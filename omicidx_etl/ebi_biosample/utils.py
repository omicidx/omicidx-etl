"""Utility functions for EBI BioSample extraction."""

from datetime import datetime, timedelta, date
from typing import Iterable


def get_filename(
    start_date: date,
    end_date: date,
    tmp: bool = True,
    output_directory: str = ''
) -> str:
    """Get the filename for a given date range.

    The final filename looks like
    `biosamples-2021-01-01--2021-01-01--daily.parquet`, for example.
    """
    base = f"year={start_date.year}/month={start_date.month:02d}/day={start_date.day:02d}/data_0.parquet"
    if tmp:
        base += ".tmp"
    return base


def get_date_ranges(start_date_str: str, end_date_str: str) -> Iterable[tuple]:
    """Get date ranges for a given start and end date.

    Given a start and end date, returns a list of tuples representing daily date ranges.

    :param start_date_str: The start date in 'YYYY-MM-DD' format
    :param end_date_str: The end date in 'YYYY-MM-DD' format
    :return: Iterator of tuples, each containing a single day (same date for start and end)
    """
    # Convert strings to datetime objects
    start_date = datetime.strptime(start_date_str, "%Y-%m-%d")
    end_date = datetime.strptime(end_date_str, "%Y-%m-%d")

    current_date = start_date

    while current_date <= end_date:
        # Yield single day range (start and end are the same)
        yield (current_date.date(), current_date.date())
        # Move to next day
        current_date = current_date + timedelta(days=1)
