"""Run SQL ETL transformations using DuckDB.

This module provides a CLI and programmatic interface for running
the SQL-based ETL pipeline.

Usage (CLI):
    # Run all SQL files in order
    uv run oidx sql run

    # Run specific file(s)
    uv run oidx sql run 010_raw_to_parquet.sql 020_base_parquet_views.sql

    # List available SQL files
    uv run oidx sql list

Usage (Python):
    from omicidx_etl.sql.runner import run_sql_file, run_all

    # Run single file
    run_sql_file("010_raw_to_parquet.sql")

    # Run all files
    run_all()
"""

from datetime import datetime
from upath import UPath
from ..log import logger

import click
import duckdb

from omicidx_etl.sql import get_sql, list_sql_files


def get_connection(duckdb_name: str = "omicidx.duckdb") -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection with httpfs extension loaded."""
    con = duckdb.connect(duckdb_name)
    con.execute("INSTALL httpfs; LOAD httpfs;")
    
    logger.info(f"Created DuckDB called {duckdb_name} with httpfs extension loaded.")
    
    return con


def run_sql_file(
    name: str,
    con: duckdb.DuckDBPyConnection | None = None,
    verbose: bool = True,
) -> duckdb.DuckDBPyConnection:
    """Run a SQL file.

    Args:
        name: SQL filename (e.g., "010_raw_to_parquet.sql")
        con: Existing DuckDB connection (creates new one if None)
        verbose: Print progress messages

    Returns:
        The DuckDB connection (for chaining)
    """
    if con is None:
        con = get_connection()

    sql = get_sql(name)
    
    logger.info(f"Running SQL file: {name}")
    
    con.execute(sql)

    logger.info(f"Completed SQL file: {name}")

    return con


def run_all(
    con: duckdb.DuckDBPyConnection | None = None,
    verbose: bool = True,
) -> duckdb.DuckDBPyConnection:
    """Run all SQL files in order.

    Args:
        con: Existing DuckDB connection (creates new one if None)
        verbose: Print progress messages

    Returns:
        The DuckDB connection with all views/tables created
    """
    if con is None:
        con = get_connection()

    files = list_sql_files()

    logger.info(f"Running {len(files)} SQL files...")

    for name in files:
        run_sql_file(name, con=con, verbose=verbose)

    logger.info("All SQL files completed")
    
    # get names of all tables and views
    res = con.execute("SHOW TABLES;").fetchall()
    table_names = [row[0] for row in res]
    logger.info(f"Created tables/views: {table_names}")

    return con


def transfer_duckdb_to_s3(
    local_path: UPath = UPath('omicidx.duckdb'),
    s3_path: UPath = UPath('s3://omicidx/duckdb/omicidx.duckdb')
) -> None:
    """Transfer DuckDB database file to S3."""
    with local_path.open('rb') as local_file, s3_path.open('wb') as s3_file:
        s3_file.write(local_file.read())
    
    logger.info(f"Transferred DuckDB database to {s3_path}")
    


@click.group()
def sql():
    """Run SQL ETL transformations."""
    pass


@sql.command("list")
def list_cmd():
    """List available SQL files."""
    click.echo("Available SQL files:")
    for name in list_sql_files():
        click.echo(f"  {name}")
        

@sql.command("run")
@click.argument("files", nargs=-1)
@click.option("-q", "--quiet", is_flag=True, help="Suppress progress messages")
def run_cmd(files: tuple[str, ...], quiet: bool):
    """Run SQL files.

    If no FILES specified, runs all SQL files in order.
    """
    verbose = not quiet

    if files:
        # Run specific files
        con = get_connection()
        for name in files:
            run_sql_file(name, con=con, verbose=verbose)
    else:
        # Run all
        run_all(verbose=verbose)
        
    transfer_duckdb_to_s3()
