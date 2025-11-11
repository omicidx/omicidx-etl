import polars as pl
import re
from pathlib import Path
import click
from loguru import logger
from upath import UPath


SCIMAGO_URL = "https://www.scimagojr.com/journalrank.php?out=xls"


def fetch_and_save_scimago(output_path: UPath) -> None:
    """Fetch Scimago Journal Impact Factors and save to Parquet format.

    Args:
        output_path: Directory where the output file will be saved
    """
    logger.info("Fetching Scimago Journal Impact Factors")

    # Fetch the data
    scimago = pl.read_csv(SCIMAGO_URL, separator=";")

    # Clean column names
    scimago = scimago.rename(
        {col: re.sub(r"[^\w\d_]+", "_", col.lower()).strip("_") for col in scimago.columns}
    )

    logger.info(f"Fetched {len(scimago)} journal records")

    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)

    # Save to Parquet format
    output_file = output_path / "scimago.parquet"
    scimago.write_parquet(output_file)

    logger.info(f"Saved Scimago Journal Impact Factors to {output_file}")


@click.group()
def scimago():
    """OmicIDX ETL Pipeline - Scimago journal impact factors."""
    pass


@scimago.command()
@click.argument("output_dir", type=UPath)
def extract(output_dir: UPath):
    """Extract Scimago journal impact factors.

    Args:
        output_dir: Directory where the output file will be saved
    """
    logger.info(f"Starting Scimago extraction to {output_dir}")
    fetch_and_save_scimago(output_dir)


if __name__ == "__main__":
    scimago()
