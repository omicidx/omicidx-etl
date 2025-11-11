# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OmicIDX is an ETL pipeline and data warehouse for comprehensive genomics and transcriptomics metadata from multiple public data sources (NCBI SRA, GEO, BioSample, BioProject, PubMed, etc.). The project combines:

1. **ETL Pipelines**: Extract metadata from various NCBI and public genomics databases
2. **DuckDB Data Warehouse**: 3-layer architecture (raw → staging → mart) with SQL-based transformations
3. **Cloud Deployment**: Export to Cloudflare R2 with remote database access

## Core Commands

### Running ETL Pipelines

```bash
# Main CLI entry point
uv run oidx [command] [subcommand]

# Individual ETL pipelines
uv run oidx sra extract --limit 1000           # SRA metadata
uv run oidx geo extract                         # GEO platforms/series/samples
uv run oidx biosample extract                   # NCBI BioSample
uv run oidx pubmed extract --start-date 2024-01-01  # PubMed metadata
uv run oidx icite extract                       # NIH iCite citations

# Complete daily pipeline (orchestrates all ETLs)
./daily_pipeline.sh
```

### Warehouse Operations

```bash
# Initialize warehouse database and schemas
uv run oidx warehouse init

# Run all transformations
uv run oidx warehouse run

# Run specific models
uv run oidx warehouse run --models stg_sra_studies --models sra_metadata

# Use custom config
uv run oidx warehouse run --config warehouse.yml

# View execution plan (dry run)
uv run oidx warehouse plan

# List all models
uv run oidx warehouse list-models

# View tables
uv run oidx warehouse tables --layer staging

# View model history
uv run oidx warehouse history --limit 20

# Show model documentation
uv run oidx warehouse describe sra_metadata
```

### Deployment to R2

```bash
# Generate catalog from schema.yml files
uv run oidx warehouse deploy catalog

# Create remote views database
uv run oidx warehouse deploy database

# Upload to R2/S3
uv run oidx warehouse deploy upload
uv run oidx warehouse deploy upload --dry-run

# Full deployment pipeline
uv run oidx warehouse deploy all
```

## Architecture

### ETL Layer

Each data source has an extraction module in `omicidx_etl/`:
- `sra/extract.py` - SRA (Studies, Experiments, Samples, Runs)
- `geo/extract.py` - GEO (Series, Samples, Platforms)
- `biosample/extract.py` - NCBI BioSample
- `etl/pubmed.py` - PubMed metadata and abstracts
- `etl/icite.py` - NIH iCite citation metrics

**Key Pattern**: ETL modules fetch data from APIs/FTP, parse XML/JSON, and output to Parquet files with enforced schemas.

**Schema Enforcement**: SRA extraction uses PyArrow schemas (defined in `get_pyarrow_schemas()`) to ensure consistent Parquet output. The `normalize_record()` function handles:
- Empty lists vs None/null
- Consistent numeric types (int64, float64)
- Required field presence

### Warehouse Layer (DuckDB)

Three-layer architecture in `omicidx_etl/transformations/`:

```
omicidx_warehouse.duckdb
├── raw/          # Views over exported parquet (no transformations)
├── staging/      # Cleaned, validated, standardized data
├── mart/         # Business logic, joins, production exports
└── meta/         # Execution tracking and lineage
```

**Model Structure**:
- SQL files in `models/{raw,staging,mart}/*.sql`
- Documentation in `models/{raw,staging,mart}/schema.yml`
- Loading operations in `models/loading/*.sql` (COPY commands)

**Important**: Recent refactoring split models into:
1. `loading/*.sql` - COPY operations that load source data to parquet
2. `raw/*.sql` - Views over the exported parquet files
3. This separation allows raw views to work with remote parquet URLs

**Key Files**:
- `transformations/warehouse.py` - Orchestration engine, dependency resolution, execution
- `transformations/config.py` - Configuration loading from warehouse.yml + env vars
- `transformations/deploy.py` - R2 deployment, catalog generation

### Daily Pipeline

`daily_pipeline.sh` orchestrates:
1. Run all ETL extractions (SRA, GEO, BioSample, PubMed, etc.)
2. Run warehouse transformations
3. Deploy to R2
4. Logs to `/data/davsean/omicidx_root/logs/`
5. Metrics to `/data/davsean/omicidx_root/metrics/`

## Configuration

### warehouse.yml

Primary configuration file:

```yaml
warehouse:
  db_path: omicidx_warehouse.duckdb
  models_dir: omicidx_etl/transformations/models
  export_dir: /data/davsean/omicidx_root/exports
  threads: 16
  memory_limit: 32GB

deployment:
  endpoint_url: https://[account_id].r2.cloudflarestorage.com
  bucket_name: your-bucket
  public_url: https://store.yourdomain.com  # Cloudflare Worker URL
  data_prefix: omicidx/data
  catalog_path: omicidx/catalog.json
```

**Environment Variable Overrides**: All config values can be overridden with `OMICIDX_*` environment variables (see `transformations/config.py`).

## Creating New Transformations

### 1. Create SQL Model

File: `models/staging/stg_new_table.sql`

```sql
-- Staging: Clean new table data

COPY (
SELECT
    accession,
    title,
    CAST(submission_date AS DATE) AS submission_date,

    -- Data quality flags
    CASE
        WHEN title IS NULL THEN FALSE
        ELSE TRUE
    END AS has_complete_metadata,

    CURRENT_TIMESTAMP AS _loaded_at

FROM src_new_table
WHERE accession IS NOT NULL
) TO '/data/davsean/omicidx_root/exports/stg_new_table.parquet'
(FORMAT parquet, COMPRESSION zstd);

CREATE OR REPLACE VIEW stg_new_table AS
SELECT * FROM read_parquet('/data/davsean/omicidx_root/exports/stg_new_table.parquet');
```

**Pattern**: Recent models use COPY to export to parquet, then create a view over it. This allows the view to later point to remote URLs.

### 2. Document in schema.yml

File: `models/staging/schema.yml`

```yaml
models:
  - name: stg_new_table
    description: |
      Cleaned and validated table data.
      - Standardized date formats
      - Quality flags added
    materialized: export_view
    export:
      enabled: true
      path: staging/stg_new_table.parquet
      compression: zstd
      row_group_size: 100000
    depends_on:
      - src_new_table
    tags:
      - staging
```

### 3. Run Model

```bash
uv run oidx warehouse run --models stg_new_table
```

## Schema Materialization Types

Defined in `schema.yml`:

- **`view`**: SQL view (no data copying, always fresh)
- **`table`**: Materialized table (faster queries, takes space)
- **`export_view`**: COPY to parquet + CREATE VIEW pattern (current standard)
- **`external_table`**: For COPY operations to parquet

## Key Patterns

### Export Directory

All parquet exports go to: `/data/davsean/omicidx_root/exports/`

This path is hardcoded in many SQL files. When working with models, maintain this pattern or update `warehouse.yml` export_dir.

### Data Quality Flags

Staging models add data quality flags:
```sql
CASE
    WHEN title IS NULL OR title = '' THEN FALSE
    WHEN description IS NULL THEN FALSE
    ELSE TRUE
END AS has_complete_metadata
```

### Audit Timestamps

Add to all staging/mart models:
```sql
CURRENT_TIMESTAMP AS _loaded_at
```

### Cross-References

Many models have cross-references between databases (e.g., SRA ↔ BioSample ↔ GEO ↔ PubMed). Track these in columns like:
- `BioProject`, `BioSample`, `GEO`, `pubmed_ids`

## GitHub Actions Workflows

Located in `.github/workflows/`:
- `ncbi_sra_etl.yaml` - SRA extraction
- `geo.yaml` - GEO extraction
- `ncbi_biosample.yaml` - BioSample extraction
- `pubmed_etl.yaml` - PubMed extraction
- `icite.yaml` - iCite extraction
- `daily.yaml` - Daily orchestration

Each workflow runs ETL + transformations + deployment on schedule or manually.

## Remote Database Pattern

For users to query data without downloading:

1. Export models write to parquet
2. `deploy.py` creates `omicidx.duckdb` with views pointing to R2 URLs
3. Users download small database file (a few MB)
4. Queries read from R2 on-demand via HTTPS

Example remote view:
```sql
CREATE VIEW mart.sra_metadata AS
SELECT * FROM read_parquet('https://store.cancerdatasci.org/omicidx/data/marts/sra_metadata.parquet');
```

## Debugging

### View warehouse execution logs

```bash
uv run oidx warehouse history --limit 50
```

### Check parquet exports

```bash
ls -lh /data/davsean/omicidx_root/exports/
```

### Inspect DuckDB directly

```bash
duckdb omicidx_warehouse.duckdb
```

```sql
-- View schemas
SELECT * FROM information_schema.tables WHERE table_schema IN ('raw', 'staging', 'mart');

-- Check execution metadata
SELECT * FROM meta.model_runs ORDER BY started_at DESC LIMIT 20;

-- View model lineage
SELECT * FROM meta.model_lineage;
```

## Data Sources

The project integrates metadata from:

- **NCBI SRA** (~30M experiments): Sequence Read Archive metadata
- **NCBI GEO** (~7M samples, ~260K series): Gene Expression Omnibus
- **NCBI BioSample** (~40M samples): Sample metadata
- **NCBI BioProject** (~800K projects): Project metadata
- **PubMed** (~40M articles): Publication metadata and abstracts
- **NIH iCite** (~37M citations): Citation metrics and influence scores

All extract to parquet with enforced schemas, then transform through the warehouse layers.

## Development Notes

- **Python version**: 3.11+ (see `.python-version`)
- **Package manager**: `uv` (replaces pip/poetry for this project)
- **Database**: DuckDB (file-based, no server needed)
- **Testing**: Limited test coverage currently; validation mostly via schema enforcement
- **Dependency management**: Uses `pyproject.toml` with uv
