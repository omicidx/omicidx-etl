"""
Catalog generation command for OmicIDX data catalog.
"""

import click
from pathlib import Path
import sys
import importlib.util

def load_generate_catalog():
    """Load the generate_catalog module from sqlmesh/scripts."""
    script_path = Path(__file__).parent.parent / 'sqlmesh' / 'scripts' / 'generate_catalog.py'
    
    if not script_path.exists():
        raise FileNotFoundError(f"Catalog generation script not found at {script_path}")
    
    spec = importlib.util.spec_from_file_location("generate_catalog", script_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load generate_catalog from {script_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.generate_catalog


@click.command()
@click.option(
    '--models-dir',
    type=click.Path(exists=True, file_okay=False, path_type=Path),
    default=Path(__file__).parent.parent / 'sqlmesh' / 'models',
    help='Path to SQLMesh models directory'
)
@click.option(
    '--db-path',
    type=click.Path(exists=True, file_okay=True, path_type=Path),
    default=Path(__file__).parent.parent / 'sqlmesh' / 'db.duckdb',
    help='Path to DuckDB database file'
)
@click.option(
    '--output',
    type=click.Path(path_type=Path),
    help='Output JSON file path (default: catalog-viewer/public/catalog.json)'
)
def catalog(models_dir: Path, db_path: Path, output: Path | None):
    """Generate data catalog from SQLMesh models and DuckDB."""
    generate_catalog = load_generate_catalog()
    
    if output is None:
        output = Path(__file__).parent.parent / 'catalog-viewer' / 'public' / 'catalog.json'
    
    click.echo(f"Generating catalog from models in {models_dir}")
    click.echo(f"Using database: {db_path}")
    click.echo(f"Output: {output}")
    
    try:
        catalog_data = generate_catalog(
            models_dir=models_dir,
            db_path=db_path,
            output_path=output
        )
        
        click.echo(f"✓ Catalog generated successfully!")
        click.echo(f"  - {len(catalog_data['tables'])} tables")
        click.echo(f"  - {len(catalog_data['layers'].get('raw', []))} raw tables")
        click.echo(f"  - {len(catalog_data['layers'].get('bronze', []))} bronze tables")
        click.echo(f"  - {len(catalog_data['layers'].get('geometadb', []))} geometadb tables")
        
    except Exception as e:
        click.echo(f"✗ Error generating catalog: {e}", err=True)
        raise click.Abort()
