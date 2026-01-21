"""
Main CLI entry point for omicidx-etl.
"""

import click
from dotenv import load_dotenv

# Load .env file early to ensure AWS credentials are available
load_dotenv()

from omicidx_etl.biosample.extract import biosample
from omicidx_etl.geo.extract import geo
from omicidx_etl.sra.cli import sra
from omicidx_etl.sql.runner import sql


@click.group()
@click.version_option()
def cli():
    """OmicIDX ETL Pipeline - Simplified data extraction tools."""
    pass


# Add subcommands
cli.add_command(biosample)
cli.add_command(sra)
cli.add_command(geo)
cli.add_command(sql)

if __name__ == "__main__":
    cli()
