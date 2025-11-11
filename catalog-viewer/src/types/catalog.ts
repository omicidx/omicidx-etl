/**
 * TypeScript types for the OmicIDX Data Catalog
 * These types match the JSON schema defined in sqlmesh/scripts/catalog_schema.json
 */

export type ModelKind = 'VIEW' | 'INCREMENTAL_BY_TIME_RANGE' | 'INCREMENTAL_BY_UNIQUE_KEY' | 'FULL';
export type SchemaName = 'raw' | 'bronze' | 'geometadb';

export interface ColumnStatistics {
  null_count?: number | null;
  null_percentage?: number | null;
  distinct_count?: number | null;
  min?: number | null;
  max?: number | null;
  mean?: number | null;
  std?: number | null;
  q25?: number | null;
  q50?: number | null;
  q75?: number | null;
}

export interface Column {
  name: string;
  type: string;
  nullable?: boolean;
  description?: string;
  statistics?: ColumnStatistics;
  // Statistics can also be at the top level
  null_count?: number | null;
  null_percentage?: number | null;
  distinct_count?: number | null;
  min?: number | null;
  max?: number | null;
  mean?: number | null;
  std?: number | null;
  q25?: number | null;
  q50?: number | null;
  q75?: number | null;
}

export interface Table {
  name: string;
  schema?: SchemaName;
  table_name?: string;
  kind?: ModelKind;
  grain?: string | string[];
  cron?: string;
  time_column?: string;
  description?: string;
  file_path?: string;
  row_count?: number | null;
  size_bytes?: number | null;
  dependencies?: string[];
  dependents?: string[];
  columns?: Column[];
  sql_content?: string;
}

export interface Catalog {
  version: string;
  generated_at: string;
  database_path: string;
  tables: Table[];
  layers: {
    raw?: string[];
    bronze?: string[];
    geometadb?: string[];
  };
}

// Helper types for graph visualization
export interface GraphNode {
  id: string;
  name: string;
  schema: SchemaName | string;
  kind?: ModelKind;
  row_count?: number | null;
  dependencies?: string[];
  dependents?: string[];
}

export interface GraphLink {
  source: string;
  target: string;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

