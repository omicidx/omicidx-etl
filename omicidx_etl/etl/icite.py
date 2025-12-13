from urllib.request import urlopen
import zipfile
import tarfile
import shutil
import click
import httpx
from upath import UPath
from dotenv import load_dotenv
import os
import gzip
import tempfile
from omicidx_etl.path_provider import get_path_provider

from omicidx_etl.log import get_logger

from omicidx_etl.db import duckdb_connection

logger = get_logger(__name__)

load_dotenv(".env")
print(os.getenv("R2_ACCESS_KEY_ID"))
print(os.getenv("R2_SECRET_ACCESS_KEY"))

PROJECT_ID = "gap-som-dbmi-sd-app-fq9"
DATASET_ID = "omicidx"
ICITE_COLLECTION_ID = 4586573




def get_icite_collection_articles() -> list[dict[str, str]]:
    with httpx.Client(timeout=60) as client:
        response = client.get(
            f"https://api.figshare.com/v2/collections/{ICITE_COLLECTION_ID}/articles"
        )
        response.raise_for_status()
        logger.info("Getting latest ICITE articles from figshare")
        return response.json()



def get_icite_article_files(article_id: str):
    with httpx.Client(timeout=60) as client:
        response = client.get(
            f"https://api.figshare.com/v2/articles/{article_id}/files"
        )
        response.raise_for_status()
        logger.info("Getting latest ICITE article files from figshare")
        return response.json()


def clean_icite_output_directory(output_directory: UPath) -> None:
    if not output_directory.exists():
        return
    
    try:
        output_directory.fs.rm(output_directory.path, recursive=True)
    except TypeError:
        # Some FS implementations don't accept recursive as kwarg
        output_directory.fs.rm(output_directory.path, True)


def icite_metadata_parquet(file_json: list[dict], workpath: UPath) -> list[UPath]:
    url = list(filter(lambda x: x["name"] == "icite_metadata.csv", file_json))[0][
        "download_url"
    ]  # type: ignore
    
    sql = f"""
        COPY (SELECT * FROM read_csv_auto('{url}', null_padding=true)) TO '{workpath / "icite_metadata"}' (FORMAT PARQUET, COMPRESSION ZSTD, FILE_SIZE_BYTES '500MB')
    """
    
    logger.info(sql)
    
    with duckdb_connection() as conn:
        conn.execute(sql)
        
    return list((workpath / "icite_metadata").glob("*.parquet"))

def icite_opencitation_parquet(file_json: list[dict], workpath: UPath) -> list[UPath]:
    url = list(
        filter(lambda x: x["name"] == "open_citation_collection.csv", file_json)
    )[0]["download_url"]
    
    
    sql = f"""
        COPY (SELECT * FROM read_csv_auto('{url}', null_padding=true)) TO '{workpath / "icite_opencitation"}' (FORMAT PARQUET, COMPRESSION ZSTD, FILE_SIZE_BYTES '500MB')
    """
    
    logger.info(sql)
    
    with duckdb_connection() as conn:
        conn.execute(sql)
        
    return list((workpath / "icite_opencitation").glob("*.parquet"))


def icite_flow(output_directory: UPath) -> list[UPath]:
    """Flow to ingest icite data from figshare

    The NIH ICITE data is stored in a figshare collection. This flow
    downloads the data from figshare, extracts the tarfile, and uploads
    the json files to GCS.

    Since there are updates to the data, the flow also cleans out the
    GCS directory before uploading the new data.

    The article is "updated" monthly, so the flow must first find
    the latest version of the data using the figshare API.

    """
    articles: list[dict] = get_icite_collection_articles()  # type: ignore
    files: list[dict] = get_icite_article_files(articles[0]["id"])  # type: ignore
    
    logger.info(f"found {len(files)} files in the latest ICITE article")
    logger.info(files)
    # open a temporary directory for all this work:
    with tempfile.TemporaryDirectory() as workdir:
        workpath = UPath(workdir)
        workpath.mkdir(parents=True, exist_ok=True)
        
        # clean out the output directory
        clean_icite_output_directory(output_directory)
        
        # create parquet files from the metadata and opencitation data
        metadata_files = icite_metadata_parquet(files, output_directory)
        opencitation_files = icite_opencitation_parquet(files, output_directory)

    return metadata_files + opencitation_files


@click.group()
def icite():
    """ICITE extraction commands."""
    pass

@icite.command()
@click.argument('base_directory', type=click.Path(path_type=UPath))
def extract(base_directory: UPath):
    provider = get_path_provider(base_directory)
    output_dir = provider.ensure_path("icite", "raw")
    icite_flow(output_dir)
    
if __name__ == "__main__":
    extract()