"""
Simplified biosample/bioproject extraction without Prefect dependencies.
"""
import httpx
import tempfile
import gzip
from upath import UPath
from pathlib import Path
from omicidx.biosample import BioSampleParser, BioProjectParser
import click
from omicidx_etl.log import get_logger
from omicidx_etl.path_provider import get_path_provider
import tenacity

logger = get_logger(__name__)

# Configuration
BIO_SAMPLE_URL = "https://ftp.ncbi.nlm.nih.gov/biosample/biosample_set.xml.gz"
BIO_PROJECT_URL = "https://ftp.ncbi.nlm.nih.gov/bioproject/bioproject.xml"
OUTPUT_SUFFIX = ".parquet"

# Batch sizes optimized for your 512GB RAM
BIOSAMPLE_BATCH_SIZE = 500_000  # This size works well within memory limits on GH actions
BIOPROJECT_BATCH_SIZE = 500_000  # Much larger than current 100k

@tenacity.retry(
    wait=tenacity.wait_exponential(multiplier=1, min=4, max=30),
    retry=tenacity.retry_if_exception_type(httpx.RequestError),
    stop=tenacity.stop_after_attempt(5),
)
def url_download(url: str, download_filename: str):
    """Download a file from a URL to a local destination."""

    try:
        logger.info(f"Downloading {url} to {download_filename}")
        with open(download_filename, "wb") as download_file:
            with httpx.stream("GET", url, timeout=60) as response:
                response.raise_for_status()

                for chunk in response.iter_bytes():
                    download_file.write(chunk)
        logger.info(f"Completed download of {url}")

    except Exception as e:
        logger.error(f"Error downloading {url}: {e}")
        raise


def cleanup_old_files(output_dir: Path, entity: str):
    """Remove old output files for an entity."""
    for file_path in output_dir.glob(f"{entity}*{OUTPUT_SUFFIX}"):
        file_path.unlink()
        logger.info(f"Removed old file: {file_path}")


def extract_biosample(output_dir: UPath) -> list[UPath]:
    """Extract biosample data to NDJSON files."""
    return _extract_entity(
        url=BIO_SAMPLE_URL,
        entity="biosample",
        output_dir=output_dir,
        batch_size=BIOSAMPLE_BATCH_SIZE,
        parser_class=BioSampleParser,
        use_gzip_input=True,
    )


def extract_bioproject(output_dir: UPath) -> list[UPath]:
    """Extract bioproject data to NDJSON files."""
    return _extract_entity(
        url=BIO_PROJECT_URL,
        entity="bioproject",
        output_dir=output_dir,
        batch_size=BIOPROJECT_BATCH_SIZE,
        parser_class=BioProjectParser,
        use_gzip_input=False,
    )


def _extract_entity(
    url: str,
    entity: str,
    output_dir: UPath,
    batch_size: int,
    parser_class,
    use_gzip_input: bool,
) -> list[UPath]:
    """Extract a single entity type to parquet files."""
    output_dir = output_dir / entity / "raw"
    output_dir.mkdir(parents=True, exist_ok=True)
    cleanup_old_files(output_dir, entity)

    logger.info(f"Downloading {url}")

    output_files = []

    with tempfile.NamedTemporaryFile() as downloaded_file:
        url_download(url, downloaded_file.name)

        obj_counter = 0
        file_counter = 1
        current_batch = []

        def _write_batch():
            nonlocal current_batch, file_counter, output_files
            if current_batch:
                output_path = output_dir / f"data_{file_counter}.parquet"
                with output_path.open("wb") as f:
                    import polars as pl

                    df = pl.DataFrame(current_batch, infer_schema_length=1000000)
                    df.write_parquet(f)
                output_files.append(output_path)
                logger.info(f"Wrote {len(current_batch)} records to {output_path}")
                current_batch = []
                file_counter += 1

        # Open input file
        open_func = gzip.open if use_gzip_input else open
        mode = "rb"

        with open_func(downloaded_file.name, mode) as input_file:
            for obj in parser_class(input_file, validate_with_schema=False):
                current_batch.append(obj)
                obj_counter += 1

                # Write batch when it reaches batch_size
                if len(current_batch) >= batch_size:
                    _write_batch()

        # Write final batch if it has data
        if current_batch:
            _write_batch()

    logger.info(
        f"Completed {entity} extraction: {obj_counter} records, {len(output_files)} files"
    )
    return output_files


def extract_all(output_dir: UPath) -> dict[str, list[UPath]]:
    """Extract both biosample and bioproject."""
    results = {}

    for entity_func, entity_name in [
        (extract_bioproject, "bioproject"),
        (extract_biosample, "biosample"),
    ]:
        results[entity_name] = entity_func(output_dir)

    return results


@click.group()
def biosample():
    pass


@biosample.command()
@click.argument("output_base")
def extract(output_base: str):
    """Command-line interface for extraction and optional upload."""
    output_path = get_path_provider(output_base).get_path("biosample", "raw")
    logger.info(f"Starting extraction to {output_path}")
    extract_all(output_path)


if __name__ == "__main__":
    provider = get_path_provider("s3://omicidx")
    base_path = provider.get_path("biosample", "raw")

    extract_all(base_path)  # For direct CLI testing
    exit(0)
    extract()  # For direct CLI testing
