# Extract Path Migration Guide

This guide shows how to migrate extraction modules to use the new `PathProvider` resource.

## Overview

**Before**: Each module used ad-hoc path configuration
- `geo/extract.py` used `settings.PUBLISH_DIRECTORY / "geo"`
- `biosample/extract.py` took `output_dir` as parameter
- `sra/extract.py` took `output_dir` as parameter
- Inconsistent, duplicated logic

**After**: All modules use centralized `PathProvider`
- Single configuration point
- Consistent API
- File registration for tracking
- Easy testing

## Migration Pattern

### Step 1: Import PathProvider

```python
# At top of extract.py
from omicidx_etl.extract_config import get_path_provider
```

### Step 2: Update Module-Level Constants

**Before:**
```python
from ..config import settings
OUTPUT_PATH = UPath(settings.PUBLISH_DIRECTORY) / "geo"
OUTPUT_DIR = str(OUTPUT_PATH)
```

**After:**
```python
# Remove module-level path constants
# Paths are computed at runtime from PathProvider
```

### Step 3: Update Functions to Use PathProvider

**Before:**
```python
def extract_geo(start_date, end_date, output_path: UPath = OUTPUT_PATH):
    gse_path, gsm_path, gpl_path = get_result_paths(start_date, end_date, output_path)
    # ...
```

**After:**
```python
def extract_geo(start_date, end_date, output_dir: UPath | None = None):
    # Get provider and compute path
    provider = get_path_provider()
    if output_dir is None:
        output_dir = provider.ensure_path("geo")

    gse_path, gsm_path, gpl_path = get_result_paths(start_date, end_date, output_dir)
    # ...
```

### Step 4: Update Click Commands

**Before:**
```python
@click.command()
@click.argument('start_date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument('end_date', type=click.DateTime(formats=["%Y-%m-%d"]))
def extract(start_date, end_date):
    # Uses module-level OUTPUT_PATH
    extract_geo(start_date, end_date)
```

**After - Option A (Use Default Path):**
```python
@click.command()
@click.argument('start_date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument('end_date', type=click.DateTime(formats=["%Y-%m-%d"]))
def extract(start_date, end_date):
    # Let function use default from PathProvider
    extract_geo(start_date, end_date)
```

**After - Option B (Allow Override):**
```python
@click.command()
@click.argument('start_date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument('end_date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option('--output-dir', type=click.Path(path_type=UPath), default=None,
              help='Output directory (default: from PathProvider config)')
def extract(start_date, end_date, output_dir):
    extract_geo(start_date, end_date, output_dir=output_dir)
```

### Step 5: Optional - Register Files

Add file registration for tracking:

```python
def extract_geo(start_date, end_date, output_dir: UPath | None = None):
    provider = get_path_provider()
    if output_dir is None:
        output_dir = provider.ensure_path("geo")

    # ... extraction logic ...

    # Register created files
    provider.register_file("geo", gse_path, {
        "record_type": "series",
        "start_date": str(start_date),
        "end_date": str(end_date),
        "record_count": record_counts["GSE"]
    })
    provider.register_file("geo", gsm_path, {
        "record_type": "sample",
        "record_count": record_counts["GSM"]
    })
```

## Complete Examples

### Example 1: GEO Extract Module

**File: `omicidx_etl/geo/extract.py`**

```python
# === BEFORE ===
import anyio
from upath import UPath
from omicidx.geo import parser as gp
from ..config import settings

OUTPUT_PATH = UPath(settings.PUBLISH_DIRECTORY) / "geo"
OUTPUT_DIR = str(OUTPUT_PATH)

async def write_geo_entity_worker(
    entity_text_to_process_receive,
    start_date = date(2000, 1, 1),
    end_date = date.today(),
    output_path: UPath = OUTPUT_PATH,
):
    gse_path, gsm_path, gpl_path = get_result_paths(start_date, end_date, output_path)
    # ... extraction logic ...

@click.group()
def geo():
    """GEO extraction commands."""
    pass

@geo.command()
@click.argument('start_date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument('end_date', type=click.DateTime(formats=["%Y-%m-%d"]))
def extract(start_date, end_date):
    """Extract GEO metadata."""
    anyio.run(
        main,
        start_date.date(),
        end_date.date()
    )
```

```python
# === AFTER ===
import anyio
from upath import UPath
from omicidx.geo import parser as gp
from omicidx_etl.extract_config import get_path_provider

# No more module-level OUTPUT_PATH constant

async def write_geo_entity_worker(
    entity_text_to_process_receive,
    start_date = date(2000, 1, 1),
    end_date = date.today(),
    output_dir: UPath | None = None,
):
    # Get output directory from PathProvider if not specified
    if output_dir is None:
        provider = get_path_provider()
        output_dir = provider.ensure_path("geo")

    gse_path, gsm_path, gpl_path = get_result_paths(start_date, end_date, output_dir)
    # ... extraction logic ...

    # Optional: register files
    provider = get_path_provider()
    provider.register_file("geo", gse_path, {
        "record_type": "series",
        "start_date": str(start_date),
        "end_date": str(end_date)
    })

@click.group()
def geo():
    """GEO extraction commands."""
    pass

@geo.command()
@click.argument('start_date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.argument('end_date', type=click.DateTime(formats=["%Y-%m-%d"]))
@click.option('--output-dir', type=click.Path(path_type=UPath), default=None,
              help='Output directory (default: configured extract path)')
def extract(start_date, end_date, output_dir):
    """Extract GEO metadata."""
    anyio.run(
        main,
        start_date.date(),
        end_date.date(),
        output_dir
    )
```

### Example 2: BioSample Extract Module

**File: `omicidx_etl/biosample/extract.py`**

```python
# === BEFORE ===
def extract_biosample(output_dir: Path) -> list[Path]:
    """Extract biosample data to parquet files."""
    return _extract_entity(
        url=BIO_SAMPLE_URL,
        entity="biosample",
        output_dir=output_dir,
        # ...
    )

@click.group()
def biosample():
    """Biosample extraction commands."""
    pass

@biosample.command()
@click.argument('output_dir', type=click.Path(path_type=Path))
def extract(output_dir: Path):
    """Extract biosample metadata."""
    extract_biosample(output_dir)
```

```python
# === AFTER ===
from omicidx_etl.extract_config import get_path_provider

def extract_biosample(output_dir: Path | None = None) -> list[Path]:
    """Extract biosample data to parquet files."""
    # Use PathProvider if no directory specified
    if output_dir is None:
        provider = get_path_provider()
        output_dir = provider.ensure_path("biosample")

    output_files = _extract_entity(
        url=BIO_SAMPLE_URL,
        entity="biosample",
        output_dir=output_dir,
        # ...
    )

    # Register files
    provider = get_path_provider()
    for filepath in output_files:
        provider.register_file("biosample", filepath)

    return output_files

@click.group()
def biosample():
    """Biosample extraction commands."""
    pass

@biosample.command()
@click.option('--output-dir', type=click.Path(path_type=Path), default=None,
              help='Output directory (default: configured extract path)')
def extract(output_dir: Path | None):
    """Extract biosample metadata."""
    extract_biosample(output_dir)
```

### Example 3: SRA Extract Module (Already Takes output_dir)

**File: `omicidx_etl/sra/extract.py`**

```python
# === BEFORE ===
@sra.command()
@click.argument('output_dir', type=click.Path(path_type=Path))
@click.option('--format', 'output_format', ...)
def extract(output_dir: Path, output_format: str, workers: int):
    """Extract SRA data to local files."""
    results = extract_sra(output_dir, ...)
    return results
```

```python
# === AFTER ===
from omicidx_etl.extract_config import get_path_provider

@sra.command()
@click.option('--output-dir', type=click.Path(path_type=Path), default=None,
              help='Output directory (default: configured extract path)')
@click.option('--format', 'output_format', ...)
def extract(output_dir: Path | None, output_format: str, workers: int):
    """Extract SRA data to local files."""
    # Use PathProvider default if not specified
    if output_dir is None:
        provider = get_path_provider()
        output_dir = provider.ensure_path("sra")

    results = extract_sra(output_dir, ...)

    # Register files
    provider = get_path_provider()
    for entity_type, info in results.items():
        for filename in info.get('filenames', []):
            provider.register_file("sra", output_dir / filename, {
                "entity_type": entity_type,
                "record_count": info.get('record_count', 0)
            })

    return results
```

## Configuration

### Environment Variable

```bash
# Set base directory for all extractions
export OMICIDX_EXTRACT_BASE_DIR="/data/davsean/omicidx_root/extracts"
```

### In .env File

```bash
# .env
OMICIDX_EXTRACT_BASE_DIR=/data/davsean/omicidx_root/extracts
```

### Programmatic Configuration

```python
from omicidx_etl.extract_config import get_path_provider, set_path_provider, PathProvider

# For testing or custom setups
custom_provider = PathProvider(base_dir="/tmp/test_extracts")
set_path_provider(custom_provider)
```

## Benefits After Migration

1. **Single Configuration**: One place to change all extraction paths
2. **Consistent API**: All modules use same pattern
3. **Testing**: Easy to inject test paths
4. **Tracking**: Optional file registration for audit trails
5. **DuckLake Ready**: When migrating to DuckLake, these paths feed loading/*.sql

## Migration Checklist

For each extraction module:

- [ ] Import `get_path_provider` from `extract_config`
- [ ] Remove module-level path constants (OUTPUT_PATH, OUTPUT_DIR, etc.)
- [ ] Update functions to accept optional `output_dir` parameter
- [ ] Call `provider.ensure_path(asset)` when output_dir is None
- [ ] Update Click commands to use `--output-dir` option with default=None
- [ ] Optional: Add `provider.register_file()` calls for tracking
- [ ] Test with default path and custom override path

## Testing

```python
# test_extract_with_provider.py
import tempfile
from pathlib import Path
from omicidx_etl.extract_config import PathProvider, set_path_provider
from omicidx_etl.sra.extract import extract_sra

def test_sra_extract_uses_provider():
    # Create temp directory for test
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up test provider
        test_provider = PathProvider(base_dir=tmpdir)
        set_path_provider(test_provider)

        # Extract should use provider's path
        results = extract_sra(output_dir=None)  # None = use provider

        # Check files went to right place
        sra_dir = Path(tmpdir) / "sra"
        assert sra_dir.exists()
        assert len(list(sra_dir.glob("*.parquet"))) > 0
```

## Backward Compatibility

The old `settings.PUBLISH_DIRECTORY` still works but logs deprecation warning:

```python
from omicidx_etl.config import settings

# Still works, but deprecated
path = settings.publish_directory  # → Warning logged
```

Migrate to:

```python
from omicidx_etl.extract_config import get_path_provider

provider = get_path_provider()
path = provider.base_dir
```
