#!/usr/bin/env python3
"""
Generate a comprehensive data catalog from SQLMesh models and DuckDB.

This script:
1. Parses SQLMesh model files to extract metadata
2. Extracts dependencies from SQL queries
3. Queries DuckDB for table schemas and statistics
4. Generates a JSON catalog file
"""

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import duckdb
import sqlglot
from sqlglot import parse_one, exp


def parse_model_file(file_path: Path) -> Dict[str, Any]:
    """Parse a SQLMesh model file to extract metadata."""
    content = file_path.read_text()
    
    # Extract MODEL block
    model_match = re.search(
        r'MODEL\s*\(\s*(.*?)\s*\);',
        content,
        re.DOTALL | re.IGNORECASE
    )
    
    if not model_match:
        return {}
    
    model_block = model_match.group(1)
    
    # Extract model name
    name_match = re.search(r'name\s+([^\s,]+)', model_block, re.IGNORECASE)
    name = name_match.group(1) if name_match else None
    
    # Extract kind
    kind_match = re.search(r'kind\s+(\w+)', model_block, re.IGNORECASE)
    kind = kind_match.group(1) if kind_match else 'VIEW'
    
    # Extract grain
    grain_match = re.search(r'grain\s+(\w+)', model_block, re.IGNORECASE)
    grain = grain_match.group(1) if grain_match else None
    
    # Extract cron
    cron_match = re.search(r'cron\s+([^\s,]+)', model_block, re.IGNORECASE)
    cron = cron_match.group(1) if cron_match else None
    
    # Extract time_column if present
    time_column_match = re.search(
        r'time_column\s*\(\s*(\w+)\s*\)',
        model_block,
        re.IGNORECASE
    )
    time_column = time_column_match.group(1) if time_column_match else None
    
    # Extract description from comments
    description = None
    comment_match = re.search(r'^--\s*(.+)$', content, re.MULTILINE)
    if comment_match:
        description = comment_match.group(1).strip()
    
    # Parse schema and table name from full name
    schema = None
    table_name = None
    if name:
        parts = name.split('.')
        if len(parts) == 2:
            schema, table_name = parts
        else:
            table_name = name
    
    return {
        'name': name,
        'schema': schema,
        'table_name': table_name,
        'kind': kind,
        'grain': grain,
        'cron': cron,
        'time_column': time_column,
        'description': description,
        'file_path': str(file_path),
        'sql_content': content
    }


def extract_dependencies(sql: str, model_name: str) -> List[str]:
    """Extract table dependencies from SQL query."""
    dependencies = set()
    
    try:
        # Parse SQL to extract table references
        parsed = parse_one(sql, dialect='duckdb')
        
        if not parsed:
            return []
        
        # Find all table references
        for table in parsed.find_all(exp.Table):
            table_ref = table.sql(dialect='duckdb')
            # Remove quotes and normalize
            table_ref = table_ref.strip('"').strip("'")
            
            # Skip if it's the same as the model name
            if table_ref == model_name or table_ref.endswith(f'.{model_name.split(".")[-1]}'):
                continue
            
            # Only include if it looks like a model reference (has schema or matches pattern)
            if '.' in table_ref or table_ref.startswith(('raw.', 'bronze.', 'geometadb.')):
                dependencies.add(table_ref)
        
        # Also check for CTEs that reference tables
        for cte in parsed.find_all(exp.CTE):
            if cte.this:
                for table in cte.this.find_all(exp.Table):
                    table_ref = table.sql(dialect='duckdb').strip('"').strip("'")
                    if '.' in table_ref or table_ref.startswith(('raw.', 'bronze.', 'geometadb.')):
                        dependencies.add(table_ref)
    
    except Exception as e:
        # Fallback to regex if sqlglot fails
        # Look for FROM and JOIN clauses
        from_pattern = r'FROM\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        join_pattern = r'JOIN\s+([a-zA-Z_][a-zA-Z0-9_.]*)'
        
        for pattern in [from_pattern, join_pattern]:
            matches = re.findall(pattern, sql, re.IGNORECASE)
            for match in matches:
                match = match.strip()
                if '.' in match or match.startswith(('raw.', 'bronze.', 'geometadb.')):
                    dependencies.add(match)
    
    return sorted(list(dependencies))


def get_table_schema(conn: duckdb.DuckDBPyConnection, schema: str, table: str) -> Optional[Dict[str, Any]]:
    """Get table schema information from DuckDB."""
    try:
        # Try DESCRIBE first (DuckDB native)
        try:
            desc_query = f'DESCRIBE "{schema}"."{table}"'
            result = conn.execute(desc_query).fetchall()
            
            columns = []
            for row in result:
                # DESCRIBE returns: column_name, column_type, null, key, default, extra
                col_name = row[0]
                col_type = row[1]
                nullable = row[2] if len(row) > 2 else True
                
                columns.append({
                    'name': col_name,
                    'type': col_type,
                    'nullable': nullable if isinstance(nullable, bool) else True
                })
            
            return {'columns': columns} if columns else None
        except Exception:
            # Fallback to information_schema if DESCRIBE fails
            query = f"""
            SELECT 
                column_name,
                data_type,
                is_nullable
            FROM information_schema.columns
            WHERE table_schema = '{schema}' AND table_name = '{table}'
            ORDER BY ordinal_position
            """
            result = conn.execute(query).fetchall()
            
            columns = []
            for row in result:
                columns.append({
                    'name': row[0],
                    'type': row[1],
                    'nullable': row[2] == 'YES' if row[2] else True
                })
            
            return {'columns': columns} if columns else None
    
    except Exception:
        return None


def get_table_stats(conn: duckdb.DuckDBPyConnection, schema: str, table: str, columns: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Get comprehensive statistics for a table."""
    stats = {
        'row_count': None,
        'size_bytes': None,
        'columns': []
    }
    
    try:
        # Get row count
        count_query = f'SELECT COUNT(*) FROM "{schema}"."{table}"'
        row_count = conn.execute(count_query).fetchone()[0]
        stats['row_count'] = int(row_count)
        
        # Get column statistics
        for col in columns:
            col_name = col['name']
            col_type = col['type'].upper()
            col_stats = {
                'name': col_name,
                'type': col_type,
                'null_count': None,
                'null_percentage': None,
                'distinct_count': None,
                'min': None,
                'max': None,
                'mean': None,
                'std': None,
                'q25': None,
                'q50': None,
                'q75': None,
            }
            
            try:
                # Get null count
                null_query = f'SELECT COUNT(*) FROM "{schema}"."{table}" WHERE "{col_name}" IS NULL'
                null_count = conn.execute(null_query).fetchone()[0]
                col_stats['null_count'] = int(null_count)
                if stats['row_count']:
                    col_stats['null_percentage'] = (null_count / stats['row_count']) * 100
                
                # Get distinct count (sample for large tables)
                try:
                    distinct_query = f'SELECT COUNT(DISTINCT "{col_name}") FROM "{schema}"."{table}"'
                    distinct_count = conn.execute(distinct_query).fetchone()[0]
                    col_stats['distinct_count'] = int(distinct_count)
                except Exception:
                    pass
                
                # Get min/max/mean for numeric types
                if any(t in col_type for t in ['INT', 'BIGINT', 'DOUBLE', 'FLOAT', 'DECIMAL', 'NUMERIC', 'REAL']):
                    try:
                        stats_query = f"""
                        SELECT 
                            MIN("{col_name}") as min_val,
                            MAX("{col_name}") as max_val,
                            AVG("{col_name}") as mean_val,
                            STDDEV("{col_name}") as std_val
                        FROM "{schema}"."{table}"
                        WHERE "{col_name}" IS NOT NULL
                        """
                        result = conn.execute(stats_query).fetchone()
                        if result:
                            col_stats['min'] = float(result[0]) if result[0] is not None else None
                            col_stats['max'] = float(result[1]) if result[1] is not None else None
                            col_stats['mean'] = float(result[2]) if result[2] is not None else None
                            col_stats['std'] = float(result[3]) if result[3] is not None else None
                    except Exception:
                        pass
                    
                    # Get percentiles (q25, q50, q75)
                    try:
                        percentile_query = f"""
                        SELECT 
                            quantile_cont("{col_name}", 0.25) as q25,
                            quantile_cont("{col_name}", 0.50) as q50,
                            quantile_cont("{col_name}", 0.75) as q75
                        FROM "{schema}"."{table}"
                        WHERE "{col_name}" IS NOT NULL
                        """
                        result = conn.execute(percentile_query).fetchone()
                        if result:
                            col_stats['q25'] = float(result[0]) if result[0] is not None else None
                            col_stats['q50'] = float(result[1]) if result[1] is not None else None
                            col_stats['q75'] = float(result[2]) if result[2] is not None else None
                    except Exception:
                        pass
                
            except Exception:
                pass
            
            stats['columns'].append(col_stats)
    
    except Exception as e:
        # Table might not exist yet or query failed
        pass
    
    return stats


def build_dependency_graph(models: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Build a graph of which models depend on which."""
    dependents = {}
    
    for model in models:
        model_name = model['name']
        if not model_name:
            continue
        
        # Initialize dependents list
        if model_name not in dependents:
            dependents[model_name] = []
        
        # Find models that depend on this one
        for other_model in models:
            if other_model['name'] == model_name:
                continue
            
            deps = other_model.get('dependencies', [])
            if model_name in deps:
                dependents[model_name].append(other_model['name'])
    
    return dependents


def generate_catalog(
    models_dir: Path,
    db_path: Path,
    output_path: Optional[Path] = None
) -> Dict[str, Any]:
    """Generate the complete catalog."""
    
    # Find all model files
    model_files = []
    for layer_dir in ['raw', 'bronze', 'geometadb']:
        layer_path = models_dir / layer_dir
        if layer_path.exists():
            model_files.extend(layer_path.glob('*.sql'))
    
    # Parse all models
    models = []
    for model_file in sorted(model_files):
        model_info = parse_model_file(model_file)
        if model_info.get('name'):
            # Extract dependencies
            sql = model_info.get('sql_content', '')
            deps = extract_dependencies(sql, model_info['name'])
            model_info['dependencies'] = deps
            models.append(model_info)
    
    # Connect to DuckDB
    conn = None
    if db_path.exists():
        conn = duckdb.connect(str(db_path))
        
        # Enrich models with database information
        for model in models:
            schema = model.get('schema')
            table = model.get('table_name')
            
            if schema and table:
                # Get schema information
                schema_info = get_table_schema(conn, schema, table)
                if schema_info:
                    model['columns'] = schema_info.get('columns', [])
                
                # Get statistics (pass columns if we have them)
                columns = model.get('columns', [])
                stats = get_table_stats(conn, schema, table, columns)
                model['row_count'] = stats.get('row_count')
                model['size_bytes'] = stats.get('size_bytes')
                
                # Merge column statistics
                if columns and stats.get('columns'):
                    # Match columns and merge stats
                    col_dict = {col['name']: col for col in columns}
                    for stat_col in stats['columns']:
                        col_name = stat_col['name']
                        if col_name in col_dict:
                            col_dict[col_name].update({
                                k: v for k, v in stat_col.items()
                                if k != 'name' and v is not None
                            })
                    model['columns'] = list(col_dict.values())
                elif stats.get('columns'):
                    # Use stats columns if we don't have schema columns
                    model['columns'] = stats['columns']
    
    # Build dependency graph
    dependents_map = build_dependency_graph(models)
    for model in models:
        model_name = model['name']
        model['dependents'] = dependents_map.get(model_name, [])
    
    # Organize by layers
    layers = {
        'raw': [],
        'bronze': [],
        'geometadb': []
    }
    
    for model in models:
        schema = model.get('schema')
        if schema in layers:
            layers[schema].append(model['name'])
    
    # Build catalog
    catalog = {
        'version': '1.0',
        'generated_at': datetime.utcnow().isoformat() + 'Z',
        'database_path': str(db_path),
        'tables': models,
        'layers': layers
    }
    
    if conn:
        conn.close()
    
    # Write to file if output path provided
    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(catalog, f, indent=2)
    
    return catalog


def main():
    parser = argparse.ArgumentParser(
        description='Generate data catalog from SQLMesh models and DuckDB'
    )
    parser.add_argument(
        '--models-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'models',
        help='Path to SQLMesh models directory'
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        default=Path(__file__).parent.parent / 'db.duckdb',
        help='Path to DuckDB database file'
    )
    parser.add_argument(
        '--output',
        type=Path,
        help='Output JSON file path (default: print to stdout)'
    )
    
    args = parser.parse_args()
    
    catalog = generate_catalog(
        models_dir=args.models_dir,
        db_path=args.db_path,
        output_path=args.output
    )
    
    if not args.output:
        print(json.dumps(catalog, indent=2))


if __name__ == '__main__':
    main()

