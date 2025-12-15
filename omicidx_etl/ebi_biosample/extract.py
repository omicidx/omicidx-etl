from datetime import datetime, timedelta
import tempfile
import anyio
from upath import UPath
import shutil
import click
from loguru import logger
import pyarrow as pa
import pyarrow.parquet as pq

from .schema import get_biosample_schema
from .fetcher import SampleFetcher
from .utils import get_date_ranges


async def process_by_dates(start_date, end_date, output_directory: str):
    """Process single date range.

    This function fetches samples from the EBI API for a given date range
    and writes them to a Parquet file. A semaphore file is created to indicate
    that the process is complete for the given date range.
    """
    fetcher = SampleFetcher(
        cursor="*",
        size=200,
        start_date=start_date,
        end_date=end_date,
        output_directory=output_directory,
    )
    await fetcher.process()

    output_path = UPath(output_directory)
    output_path = output_path / f"year={start_date.year}" / f"month={start_date.month:02d}" / f"day={start_date.day:02d}"
    output_file = output_path / "data_0.parquet"
    output_semaphore = output_path / "data_0.parquet.done"
    
    if output_semaphore.exists():
        logger.warning(f"Output file for {start_date} to {end_date} already exists, skipping")
        return

    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_filename = f"{tmp_dir}/data_0.parquet"
        
        if fetcher.any_samples:
            # Write samples to Parquet file
            schema = get_biosample_schema()
            table = pa.Table.from_pylist(fetcher.samples_buffer, schema=schema)
            pq.write_table(
                table,
                tmp_filename,
                compression="zstd",
                compression_level=9
            )
            

            
            with output_file.open('wb') as f, open(tmp_filename, 'rb') as src:
                shutil.copyfileobj(src, f)

            # Move temp file to final location
            #shutil.move(tmp_filename, final_filename)
            # Create .done file next to the data file
            output_semaphore.write_text(f"Processed {fetcher.processed_count} samples\n")
            logger.info(f"Finished processing {start_date} to {end_date}: {fetcher.processed_count} samples extracted")
        else:
            # No samples found - create .done with special marker
            # Create .done file to mark day as processed (even though no data)
            # This prevents re-checking empty days
            # Write metadata to indicate no samples
            output_semaphore.write_text("NO_SAMPLES\n")
            logger.info(f"Finished processing {start_date} to {end_date}: No samples found")
        UPath(tmp_filename).unlink(missing_ok=True)
    


async def limited_process(semaphore, start_date, end_date, output_directory: str=''):
    """This function is a wrapper around process_by_dates that limits the number of concurrent tasks."""
    async with semaphore:
        await process_by_dates(start_date, end_date, output_directory)


async def main(output_directory):
    start = "2021-01-01"
    # Extract up to yesterday to avoid partial day data
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    end = yesterday
    semaphore = anyio.Semaphore(20)  # Limit to 20 concurrent tasks

    logger.info(f"Starting EBI Biosample extraction from {start} to {end}")
    logger.info("Extracting up to yesterday to ensure complete days")
    logger.info(f"Output directory: {output_directory}")

    async with anyio.create_task_group() as task_group:
        for start_date, end_date in get_date_ranges(start, end):
            output_path = UPath(output_directory)
            output_path = output_path / f"year={start_date.year}" / f"month={start_date.month:02d}" / f"day={start_date.day:02d}"
            output_semaphore = output_path / "data_0.parquet.done"
            if not output_semaphore.exists(): # Only process if not already done
                logger.info(f"Scheduling processing for {start_date} to {end_date}")
                task_group.start_soon(limited_process, semaphore, start_date, end_date, str(output_directory))


@click.group()
def ebi_biosample():
    pass

@ebi_biosample.command()
@click.argument(
    "output_base",
    type=str,
)
def extract(output_base: str):
    """Extract EBI Biosample data.

    Fetches biosample data from EBI API and saves to NDJSON format,
    organized by monthly date ranges.
    """
    from omicidx_etl.path_provider import get_path_provider
    
    output_dir = get_path_provider(output_base).ensure_path('raw', 'ebi_biosample')
    

    logger.info(f"Using output directory: {output_dir}")
    anyio.run(main, output_dir)


if __name__ == "__main__":
    logger.info("Starting EBI Biosample extraction")
    extract()
