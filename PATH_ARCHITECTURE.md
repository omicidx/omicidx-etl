# Path Management Architecture

## Overview

This document describes the unified path management system for OmicIDX ETL, designed to:
1. Centralize all extraction output path configuration
2. Prepare for DuckLake migration
3. Eliminate hardcoded paths throughout the codebase
4. Enable testing with dependency injection

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                   PathProvider (Resource)                   │
│  - Single configuration: OMICIDX_EXTRACT_BASE_DIR          │
│  - Compute paths: provider.get_path("sra")                 │
│  - Register files: provider.register_file(...)              │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ provides paths to
                              ▼
         ┌──────────────────────────────────────┐
         │      Extraction Modules               │
         │  • sra/extract.py                     │
         │  • geo/extract.py                     │
         │  • biosample/extract.py               │
         │  • pubmed.py                          │
         │  • icite.py                           │
         └──────────────────────────────────────┘
                              │
                              │ writes data to
                              ▼
         ┌──────────────────────────────────────┐
         │   Extraction Output Directory         │
         │   {BASE_DIR}/                         │
         │   ├── sra/*.parquet                   │
         │   ├── geo/*.ndjson.gz                 │
         │   ├── biosample/*.parquet             │
         │   └── ...                             │
         └──────────────────────────────────────┘
                              │
                              │ imported by (future)
                              ▼
         ┌──────────────────────────────────────┐
         │       DuckLake Import Layer           │
         │   models/loading/*.sql                │
         │   COPY (...) FROM                     │
         │   '{{extract.sra}}/*.parquet'         │
         └──────────────────────────────────────┘
```

## Components

### 1. PathProvider Resource (`omicidx_etl/extract_config.py`)

**Purpose**: Single source of truth for extraction output paths

**API**:
```python
from omicidx_etl.extract_config import get_path_provider

provider = get_path_provider()

# Get paths
sra_dir = provider.get_path("sra")                    # Base asset directory
studies_dir = provider.get_path("sra", "studies")     # With subdirectories

# Ensure directories exist
output_dir = provider.ensure_path("geo")

# Register files (optional, for tracking)
provider.register_file("sra", filepath, metadata={"record_count": 100000})

# Export registry
registry = provider.export_registry()  # For auditing, DuckLake integration
```

**Configuration**:
```bash
# Environment variable
export OMICIDX_EXTRACT_BASE_DIR="/data/davsean/omicidx_root/extracts"

# Or in .env file
OMICIDX_EXTRACT_BASE_DIR=/data/davsean/omicidx_root/extracts
```

### 2. Extraction Modules

**Pattern**: Request paths from PathProvider, don't hardcode

```python
def extract_sra(output_dir: Path | None = None) -> dict:
    """
    Extract SRA metadata.

    Args:
        output_dir: Optional override. If None, uses PathProvider default.
    """
    # Get provider
    provider = get_path_provider()

    # Use default if not specified
    if output_dir is None:
        output_dir = provider.ensure_path("sra")

    # ... extraction logic ...

    # Optional: register output files
    provider.register_file("sra", output_file, {
        "record_count": count,
        "entity_type": "study"
    })

    return results
```

### 3. CLI Commands

**Pattern**: Optional `--output-dir`, defaults to PathProvider

```python
@click.command()
@click.option('--output-dir', type=click.Path(path_type=Path), default=None,
              help='Output directory (default: configured extract path)')
def extract(output_dir: Path | None):
    """Extract data."""
    extract_sra(output_dir=output_dir)
```

**Usage**:
```bash
# Use configured default
uv run oidx sra extract

# Override for testing
uv run oidx sra extract --output-dir /tmp/test_output
```

## Directory Structure

```
{OMICIDX_EXTRACT_BASE_DIR}/     # Default: /data/davsean/omicidx_root/extracts
├── sra/
│   ├── 20250101_Full-study-0001.parquet
│   ├── 20250101_Full-study-0002.parquet
│   ├── 20250101_Full-experiment-0001.parquet
│   └── ...
├── geo/
│   ├── gse-2024-01-01_2024-12-31.ndjson.gz
│   ├── gsm-2024-01-01_2024-12-31.ndjson.gz
│   └── gpl-2024-01-01_2024-12-31.ndjson.gz
├── biosample/
│   ├── biosample-000001.parquet
│   └── biosample-000002.parquet
├── bioproject/
│   └── bioproject-000001.parquet
├── pubmed/
│   └── pubmed-*.parquet
└── icite/
    └── icite-*.parquet
```

## DuckLake Integration (Future)

When migrating to DuckLake, extraction paths become the **import layer only**:

### Loading Models (`models/loading/*.sql`)

```sql
-- models/loading/load_src_sra_studies.sql
-- This is the ONLY place that references extraction paths

COPY (
    SELECT * FROM read_parquet('{{ extract_paths.sra }}/study-*.parquet')
) TO src_sra_studies;
```

### Template Rendering

```python
# In warehouse.py or new ducklake_loader.py
from omicidx_etl.extract_config import get_path_provider

def render_loading_sql(sql_template: str) -> str:
    provider = get_path_provider()

    # Simple string substitution for loading layer
    extract_paths = {
        "sra": str(provider.get_path("sra")),
        "geo": str(provider.get_path("geo")),
        "biosample": str(provider.get_path("biosample")),
        # ...
    }

    result = sql_template
    for asset, path in extract_paths.items():
        placeholder = f"{{{{ extract_paths.{asset} }}}}"
        result = result.replace(placeholder, path)

    return result
```

### All Other Models

```sql
-- models/staging/stg_sra_studies.sql
-- NO PATHS! References DuckLake tables

SELECT
    accession,
    title,
    -- transformations
FROM src_sra_studies;  -- DuckLake table, not a path
```

## Benefits

### 1. Single Configuration Point

**Before**:
```python
# In geo/extract.py
OUTPUT_PATH = UPath(settings.PUBLISH_DIRECTORY) / "geo"

# In biosample/extract.py
# output_dir passed as parameter

# In sra/extract.py
# output_dir passed as parameter

# Inconsistent, duplicated
```

**After**:
```bash
# One environment variable
export OMICIDX_EXTRACT_BASE_DIR="/data/davsean/omicidx_root/extracts"
```

### 2. Easy Testing

```python
def test_extraction():
    # Inject test provider
    test_provider = PathProvider(base_dir="/tmp/test")
    set_path_provider(test_provider)

    # All extractions now use test directory
    extract_sra()  # → writes to /tmp/test/sra/
    extract_geo()  # → writes to /tmp/test/geo/
```

### 3. File Registry / Audit Trail

```python
# After extraction
provider = get_path_provider()
registry = provider.export_registry()

# Registry contains:
{
  "base_dir": "/data/davsean/omicidx_root/extracts",
  "exported_at": "2024-11-08T12:00:00",
  "assets": {
    "sra": [
      {
        "filepath": "/data/.../sra/studies.parquet",
        "registered_at": "2024-11-08T11:30:00",
        "metadata": {
          "record_count": 500000,
          "entity_type": "study"
        }
      }
    ]
  }
}

# Use for:
# - DuckLake import validation
# - Monitoring/alerting
# - Data lineage
```

### 4. Cloud Storage Support

```bash
# Works with S3/R2/GCS via universal-pathlib
export OMICIDX_EXTRACT_BASE_DIR="s3://my-bucket/extracts"
export AWS_ACCESS_KEY_ID="..."
export AWS_SECRET_ACCESS_KEY="..."

# Extraction code unchanged!
provider.get_path("sra")  # → UPath('s3://my-bucket/extracts/sra')
```

## Migration Status

### Completed
- ✅ `PathProvider` implementation
- ✅ Migration guide
- ✅ Architecture documentation

### In Progress
- 🔄 Update extraction modules:
  - [ ] `sra/extract.py`
  - [ ] `geo/extract.py`
  - [ ] `biosample/extract.py`
  - [ ] `bioproject/extract.py` (if exists)
  - [ ] `etl/pubmed.py`
  - [ ] `etl/icite.py`
  - [ ] `etl/scimago.py`
  - [ ] `nih_reporter.py`

### Future
- ⏳ DuckLake integration
- ⏳ Loading/*.sql template rendering
- ⏳ Registry export to DuckLake metadata tables

## Code Examples

### Example 1: SRA Extraction

```python
# omicidx_etl/sra/extract.py
from omicidx_etl.extract_config import get_path_provider

def extract_sra(output_dir: Path | None = None, max_workers: int = 4) -> dict:
    provider = get_path_provider()

    if output_dir is None:
        output_dir = provider.ensure_path("sra")

    logger.info(f"Extracting SRA to {output_dir}")

    # ... extraction logic ...

    # Register files
    for url, result in results.items():
        for filename in result['filenames']:
            provider.register_file("sra", output_dir / filename, {
                "entity_type": result['entity_type'],
                "record_count": result['record_count']
            })

    return results

@click.command()
@click.option('--output-dir', type=click.Path(path_type=Path), default=None)
def extract(output_dir):
    extract_sra(output_dir=output_dir)
```

### Example 2: GEO Extraction

```python
# omicidx_etl/geo/extract.py
from omicidx_etl.extract_config import get_path_provider

async def write_geo_entity_worker(
    entity_text_to_process_receive,
    start_date,
    end_date,
    output_dir: UPath | None = None
):
    provider = get_path_provider()

    if output_dir is None:
        output_dir = provider.ensure_path("geo")

    gse_path, gsm_path, gpl_path = get_result_paths(start_date, end_date, output_dir)

    # ... extraction logic ...

    # Register files
    provider.register_file("geo", gse_path, {
        "record_type": "series",
        "date_range": f"{start_date}_{end_date}"
    })
```

## FAQ

**Q: Why not just use environment variables everywhere?**
A: PathProvider provides:
- Validation (directory exists, writable)
- Computed paths (subdirectories)
- File registry
- Testing support (injection)
- Future DuckLake integration hooks

**Q: Can I still override paths per-command?**
A: Yes! All commands accept `--output-dir` option. PathProvider is just the default.

**Q: What about warehouse export paths?**
A: Separate concern. Warehouse uses its own config (`warehouse.yml`). PathProvider is for ETL extraction only.

**Q: How does this help with DuckLake?**
A: DuckLake will manage all storage except the initial import from extraction outputs. PathProvider paths will only be used in `loading/*.sql` templates, nowhere else.

## Next Steps

1. Migrate extraction modules per [EXTRACT_MIGRATION_GUIDE.md](EXTRACT_MIGRATION_GUIDE.md)
2. Update `daily_pipeline.sh` to use new default paths
3. Test with both default and override paths
4. When ready for DuckLake:
   - Create loading/*.sql templates
   - Implement template rendering with `{{ extract_paths.* }}`
   - All downstream models reference DuckLake tables, not paths
