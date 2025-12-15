"""EBI BioSample API client and data fetcher."""

from datetime import date
import httpx
import tenacity
from loguru import logger


BASEURL = "https://www.ebi.ac.uk/biosamples/samples"


class SampleFetcher:
    """Manages stateful pagination through EBI BioSample API results.
    
    This class handles fetching samples from the EBI BioSample API with
    automatic pagination and date filtering.
    """
    
    def __init__(
        self,
        cursor: str = "*",
        size: int = 200,
        start_date: date = date.today(),
        end_date: date = date.today(),
        output_directory: str = ''
    ):
        """Initialize the SampleFetcher.
        
        Args:
            cursor: Pagination cursor (starts at "*")
            size: Number of samples per API request (default: 200)
            start_date: Start date for filtering samples
            end_date: End date for filtering samples
            output_directory: Base directory for output files
        """
        self.cursor = cursor
        self.size = size
        self.start_date = start_date
        self.end_date = end_date
        self.output_directory = output_directory
        self.base_url = BASEURL
        self.full_url = None
        self.any_samples = False
        self.processed_count = 0
        self.samples_buffer = []  # Buffer samples in memory for Parquet writing

    def date_filter_string(self) -> str:
        """Get the filter string for a given date range.

        The EBI API uses a custom date filter syntax. This function
        returns a string that can be used in the `filter` parameter
        of the API request.
        """
        return f"""dt:update:from={self.start_date.strftime('%Y-%m-%d')}until={self.end_date.strftime('%Y-%m-%d')}"""

    @tenacity.retry(
        stop=tenacity.stop.stop_after_attempt(10),
        wait=tenacity.wait.wait_random_exponential(multiplier=1, max=40),
        before_sleep=lambda retry_state: logger.warning(
            f"request request failed, retrying in {retry_state.upcoming_sleep} seconds (attempt {retry_state.attempt_number}/5)"
        ),
    )
    async def perform_request(self) -> dict:
        """Perform a request to the EBI API with retries."""
        filt = self.date_filter_string()

        params = {
            "cursor": self.cursor,
            "size": self.size,
            "filter": filt,
        }
        logger.debug(f"Performing request to EBI API: {self.full_url if self.full_url is not None else self.base_url} with params {params}")
        async with httpx.AsyncClient() as client:
            if self.full_url is not None:
                response = await client.get(self.full_url, timeout=40)
            else:
                response = await client.get(self.base_url, params=params, timeout=40)
            response.raise_for_status()
            return response.json()

    async def fetch_next_set(self):
        """Fetch the next set of samples from the EBI API.

        This function fetches the next set of samples from the EBI API
        and yields them one by one. It also updates the cursor for the
        next request.
        """
        while True:
            try:
                response = await self.perform_request()
                for sample in response["_embedded"]["samples"]:
                    self.any_samples = True
                    characteristics = []
                    for k, v in sample["characteristics"].items():
                        for val in v:
                            val["characteristic"] = k
                            characteristics.append(val)
                    sample["characteristics"] = characteristics
                    yield sample

                if "next" in response["_links"]:
                    self.full_url = response["_links"]["next"]["href"]
                else:
                    self.completed()
                    break
            except KeyError: # no more samples
                self.completed()
                break

    async def process(self):
        """Process the samples from the EBI API.

        This function fetches samples from the EBI API and buffers them
        in memory. It runs in a loop until there are no more samples
        to fetch.
        """
        self.processed_count = 0

        async for sample in self.fetch_next_set():
            self.samples_buffer.append(sample)
            self.processed_count += 1
            if self.processed_count % 1000 == 0:
                logger.debug(f"Fetched {self.processed_count} samples so far for date range {self.start_date} to {self.end_date}")

    def completed(self):
        """Finalize the fetching process.

        This function is called when there are no more samples to fetch.
        """
        logger.info("Completed fetching samples")
