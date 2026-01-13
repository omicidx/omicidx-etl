"""
SRA catalog management.

This module provides the SRACatalog class for managing the processing and cleanup
of SRA mirror entries.
"""
from typing import List
from datetime import datetime
import json

from upath import UPath

from ..log import get_logger, log_operation, LogProgress
from .mirror import SRAMirrorEntry
from .mirror_parquet import process_mirror_entry_to_parquet_parts


class SRACatalog:
    """
    Manages the SRA catalog: processing mirror entries and cleaning up old data.

    The catalog organizes data in a directory structure like:
        {base_dir}/{entity}/date={YYYY-MM-DD}/stage={Full|Incremental}/data_*.parquet
    """

    def __init__(self, base_dir: UPath | str):
        """
        Initialize the SRA catalog.

        Args:
            base_dir: Base directory for SRA data (e.g., 's3://omicidx/sra/raw')
        """
        self.base_dir = UPath(base_dir)
        self.log = get_logger(__name__)

    def _done_marker_path(self, mirror_entry: SRAMirrorEntry) -> UPath:
        """Return the marker path indicating this entry is processed."""
        return self.parquet_dir_for_mirror_entry(mirror_entry) / "data.done"
    
    def path_for_mirror_entry(self, mirror_entry: SRAMirrorEntry) -> UPath:
        """
        Return the legacy path where a single NDJSON file would be stored.

        This is kept for cleanup of old data but not used for new writes.

        Args:
            mirror_entry: The SRA mirror entry

        Returns:
            Path to the legacy NDJSON file
        """
        return (
            self.base_dir
            / mirror_entry.entity
            / f"date={mirror_entry.date.strftime('%Y-%m-%d')}"
            / f"stage={'Full' if mirror_entry.is_full else 'Incremental'}"
            / "data_0.ndjson.gz"
        )

    def parquet_dir_for_mirror_entry(self, mirror_entry: SRAMirrorEntry) -> UPath:
        """
        Return the directory path where parquet parts should be stored.

        Args:
            mirror_entry: The SRA mirror entry

        Returns:
            Path to the parquet directory for this entry
        """
        return (
            self.base_dir
            / mirror_entry.entity
            / f"date={mirror_entry.date.strftime('%Y-%m-%d')}"
            / f"stage={'Full' if mirror_entry.is_full else 'Incremental'}"
        )
    
    def _rm_tree(self, p: UPath) -> None:
        """
        Remove a directory/prefix recursively.
        
        Works for both local filesystems and fsspec-backed remotes like S3.
        
        Args:
            p: Path to remove recursively
        """
        if not p.exists():
            return
        
        try:
            p.fs.rm(p.path, recursive=True)
        except TypeError:
            # Some FS implementations don't accept recursive as kwarg
            p.fs.rm(p.path, True)
    
    def cleanup_one(self, mirror_entry: SRAMirrorEntry) -> None:
        """
        Remove all stored artifacts for a mirror entry (entire directory/prefix).
        
        Args:
            mirror_entry: The SRA mirror entry to clean up
        """
        log = self.log.bind(
            entity=mirror_entry.entity,
            date=str(mirror_entry.date),
            stage="Full" if mirror_entry.is_full else "Incremental",
        )
        
        out_dir = self.parquet_dir_for_mirror_entry(mirror_entry)
        
        with log_operation(log, "cleanup", url=mirror_entry.url):
            self._rm_tree(out_dir)
            
            # Optional: remove legacy single-file landing path
            legacy = self.path_for_mirror_entry(mirror_entry)
            try:
                legacy.unlink(missing_ok=True)
            except Exception:
                pass
    
    def cleanup(self, mirror_entries: List[SRAMirrorEntry]) -> None:
        """
        Clean up the catalog by removing old files.
        
        Only removes entries that are not in the current batch.
        
        Args:
            mirror_entries: List of all mirror entries
        """
        to_cleanup = [e for e in mirror_entries if not e.in_current_batch]
        
        self.log.info(
            "Starting cleanup",
            total_entries=len(mirror_entries),
            to_cleanup=len(to_cleanup),
        )
        
        progress = LogProgress(
            self.log,
            total=len(to_cleanup),
            operation="cleanup_entries",
            log_every=10,
        )
        
        for entry in to_cleanup:
            try:
                self.cleanup_one(entry)
                progress.update()
            except Exception as e:
                self.log.error(
                    "Failed to cleanup entry",
                    url=entry.url,
                    entity=entry.entity,
                    error=str(e),
                    exc_info=True,
                )
        
        progress.complete()
    
    def process_one(self, mirror_entry: SRAMirrorEntry) -> None:
        """
        Process a single mirror entry and write parquet parts.
        
        Args:
            mirror_entry: The SRA mirror entry to process
        """
        log = self.log.bind(
            entity=mirror_entry.entity,
            date=str(mirror_entry.date),
            stage="Full" if mirror_entry.is_full else "Incremental",
        )
        
        out_dir = self.parquet_dir_for_mirror_entry(mirror_entry)
        done_marker = self._done_marker_path(mirror_entry)

        if done_marker.exists():
            log.info(
                f"Skipping entry; done marker exists {done_marker}, {mirror_entry.url}, {out_dir}"
            )
            return
        
        with log_operation(log, "process_entry", url=mirror_entry.url):
            written_parts = process_mirror_entry_to_parquet_parts(
                url=mirror_entry.url,
                out_dir=out_dir,
                entity=mirror_entry.entity,
                # files will be named data_000000.parquet, data_000001.parquet, etc.
                basename = "data"
            )

            # Create completion marker with a small amount of metadata
            out_dir.mkdir(parents=True, exist_ok=True)
            marker_payload = {
                "completed_at": datetime.utcnow().isoformat() + "Z",
                "url": mirror_entry.url,
                "entity": mirror_entry.entity,
                "date": str(mirror_entry.date),
                "is_full": mirror_entry.is_full,
                "parts_written": len(written_parts),
            }
            with done_marker.open("w") as fp:
                json.dump(marker_payload, fp)
            log.info("Wrote done marker", marker=str(done_marker))
    
    def process(self, mirror_entries: List[SRAMirrorEntry]) -> None:
        """
        Process the SRA mirror entries and store them in the catalog.
        
        Only processes entries that are in the current batch.
        
        Args:
            mirror_entries: List of all mirror entries
        """
        current_batch = [e for e in mirror_entries if e.in_current_batch]
        
        self.log.info(
            "Starting batch processing",
            total_entries=len(mirror_entries),
            current_batch=len(current_batch),
        )
        
        progress = LogProgress(
            self.log,
            total=len(current_batch),
            operation="process_mirror_entries",
            log_every=1,  # Log every entry since there are typically few
        )
        
        for entry in current_batch:
            try:
                self.process_one(entry)
                progress.update()
            except Exception as e:
                self.log.error(
                    "Failed to process entry",
                    url=entry.url,
                    entity=entry.entity,
                    error=str(e),
                    exc_info=True,
                )
        
        progress.complete()
