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
import os
from upath import UPath
from ..log import logger

import click
import duckdb

from omicidx_etl.sql import get_sql, list_sql_files


def get_connection(duckdb_name: str = "omicidx.duckdb") -> duckdb.DuckDBPyConnection:
    """Create a DuckDB connection with httpfs extension loaded."""
    con = duckdb.connect(duckdb_name)
    con.execute("INSTALL httpfs; LOAD httpfs;")
    
    try:
        aws_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
        aws_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
        aws_endpoint_url = os.environ['AWS_ENDPOINT_URL'].replace('https://', '').split('.')[0]
        sql = f"""
create or replace secret r2 (
    TYPE r2,
    KEY_ID '{aws_access_key_id}',
    SECRET '{aws_secret_access_key}',
    ACCOUNT_ID '{aws_endpoint_url}'
);"""
        con.execute(sql)
    
        logger.info("sql secret for R2 created successfully.")
        return con
    except KeyError as e:
        logger.error(f"Missing AWS environment variable: {e}. R2 secret not created.")
        raise
        


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


def create_metadata_table(
    con: duckdb.DuckDBPyConnection,
    table_name: str = "db_creation_metadata"
) -> None:
    """Create a metadata table to track ETL runs."""
    sql = f"""create table {table_name} as select current_timestamp() as created_at;"""
    
    con.execute(sql)
    
    
def get_table_summaries(con: duckdb.DuckDBPyConnection) -> list[dict]:
    """Get summaries of all tables in the DuckDB database.

    Args:
        con: DuckDB connection
    Returns:
        List of dictionaries with table summaries
    """
    res = con.execute("SHOW TABLES;").fetchall()
    table_names = [row[0] for row in res]
    
    summaries = []
    for table in table_names:
        count_res = con.execute(f"SELECT COUNT(*) FROM {table};").fetchone()
        if count_res is not None:
            count = count_res[0]
        else:
            count = 0
        summaries.append({
            "table_name": table,
            "row_count": count
        })
    
    return summaries


def write_summary_data_json(summaries: list[dict], output_path: UPath) -> None:
    """Write summary data to a JSON file.

    Args:
        summaries: List of table summaries
        output_path: Path to output JSON file
    """
    import json

    with output_path.open('w') as f:
        json.dump(summaries, f, indent=4)
    
    logger.info(f"Wrote summary data to {output_path}")

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
    
    # get summaries of created tables/views
    summaries = get_table_summaries(con)
    for summary in summaries:
        logger.info(f"Table/View: {summary['table_name']}, Rows: {summary['row_count']}")
    # write summaries to JSON
    output_path = UPath(f"s3://omicidx/duckdb/metadata/{datetime.now().isoformat()}_metadata.json")
    write_summary_data_json(summaries, output_path)

    create_metadata_table(con)

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
            
        con.execute('DROP SECRET r2 IF EXISTS;')
    else:
        # Run all
        run_all(verbose=verbose)
        
    transfer_duckdb_to_s3()
