"""
PathProvider resource for ETL extraction outputs.

This module provides a centralized PathProvider that extraction modules use to:
1. Compute output paths from base directory + asset name
2. Register files and track metadata
3. Ensure directories exist
4. Validate paths

Design Pattern: Resource Provider
----------------------------------
Rather than hardcoding paths, each extraction module:
1. Gets the global PathProvider instance
2. Requests paths for its asset: provider.get_path("sra")
3. Optionally registers files: provider.register_file("sra", filepath, metadata)

This enables:
- Single configuration point
- Path tracking and auditing
- Easy testing (inject mock PathProvider)
- Future DuckLake integration

Usage Example:
--------------
    # In sra/extract.py
    from omicidx_etl.extract_config import get_path_provider

    def extract_sra():
        provider = get_path_provider()
        output_dir = provider.get_path("sra")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Do extraction...
        output_file = output_dir / "studies.parquet"

        # Optional: register for tracking
        provider.register_file("sra", output_file, {
            "record_type": "study",
            "record_count": 100000
        })

Configuration:
--------------
    export OMICIDX_EXTRACT_BASE_DIR="/data/davsean/omicidx_root/extracts"
"""

import os
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from upath import UPath
from loguru import logger


class PathProviderConfig(BaseSettings):
    """Configuration for PathProvider resource."""

    model_config = SettingsConfigDict(
        env_prefix="OMICIDX_EXTRACT_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="allow",
    )

    BASE_DIR: str = Field(
        default="/data/davsean/omicidx_root/extracts",
        description="Base directory for all extraction outputs"
    )


class PathProvider:
    """
    Resource provider for extraction output paths.

    This class is the single source of truth for where extraction outputs go.
    Extraction modules request paths from this provider rather than hardcoding them.

    Attributes:
        base_dir: Root directory for all extractions
        _registry: Internal registry of files and metadata
    """

    def __init__(self, base_dir: str | Path | UPath | None = None):
        """
        Initialize PathProvider.

        Args:
            base_dir: Base directory for extractions. If None, loads from config.
        """
        logger.debug(f"Initializing PathProvider with base_dir: {base_dir}")
        if base_dir is None:
            config = PathProviderConfig()
            base_dir = config.BASE_DIR
            logger.debug(f"Loaded base_dir from config: {base_dir}")

        self.base_dir = UPath(base_dir)
        self._registry: Dict[str, list] = {}
        logger.debug(f"PathProvider initialized with base_dir: {self.base_dir}")

    def get_path(self, asset: str, *subdirs: str) -> UPath:
        """
        Get path for an asset, optionally with subdirectories.

        Args:
            asset: Asset name (e.g., "sra", "geo", "biosample")
            *subdirs: Optional subdirectories under asset dir

        Returns:
            UPath for the asset

        Examples:
            >>> provider.get_path("sra")
            UPath('/data/.../extracts/sra')

            >>> provider.get_path("sra", "studies")
            UPath('/data/.../extracts/sra/studies')

            >>> provider.get_path("geo", "series", "2024")
            UPath('/data/.../extracts/geo/series/2024')
        """
        path = self.base_dir / asset
        for subdir in subdirs:
            path = path / subdir
        return path

    def ensure_path(self, asset: str, *subdirs: str) -> UPath:
        """
        Get path for an asset and ensure it exists.

        Args:
            asset: Asset name
            *subdirs: Optional subdirectories

        Returns:
            UPath for the asset (guaranteed to exist)
        """
        path = self.get_path(asset, *subdirs)
        path.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured path exists: {path}")
        return path

    def register_file(
        self,
        asset: str,
        filepath: str | Path | UPath,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Register a file in the provider's registry.

        This is optional but useful for tracking what files have been created,
        audit trails, and future warehouse integration.

        Args:
            asset: Asset name
            filepath: Path to the file
            metadata: Optional metadata dict (record_count, schema_version, etc.)
        """
        if asset not in self._registry:
            self._registry[asset] = []

        entry = {
            "filepath": str(filepath),
            "registered_at": datetime.now().isoformat(),
            "metadata": metadata or {}
        }

        self._registry[asset].append(entry)
        logger.debug(f"Registered file for asset '{asset}': {filepath}")

    def get_registered_files(self, asset: str) -> list[Dict[str, Any]]:
        """
        Get all registered files for an asset.

        Args:
            asset: Asset name

        Returns:
            List of file registry entries
        """
        return self._registry.get(asset, [])

    def list_assets(self) -> list[str]:
        """
        List all assets that have registered files.

        Returns:
            List of asset names
        """
        return list(self._registry.keys())

    def clear_registry(self, asset: Optional[str] = None) -> None:
        """
        Clear the file registry.

        Args:
            asset: If provided, clear only this asset's registry.
                  If None, clear entire registry.
        """
        if asset is None:
            self._registry.clear()
            logger.debug("Cleared entire file registry")
        else:
            self._registry.pop(asset, None)
            logger.debug(f"Cleared registry for asset: {asset}")

    def export_registry(self) -> Dict[str, Any]:
        """
        Export the file registry as a dict.

        Useful for serialization, logging, or warehouse integration.

        Returns:
            Dict with registry data and metadata
        """
        return {
            "base_dir": str(self.base_dir),
            "exported_at": datetime.now().isoformat(),
            "assets": self._registry
        }

    def __repr__(self) -> str:
        return f"PathProvider(base_dir={self.base_dir}, assets={len(self._registry)})"


# Global singleton instance
_path_provider: Optional[PathProvider] = None


def get_path_provider(base_dir: Optional[str | Path | UPath] = None) -> PathProvider:
    """
    Get the global PathProvider instance.

    Args:
        base_dir: Optional base directory. If provided on first call, sets global instance.

    Returns:
        Global PathProvider instance
    """
    return PathProvider(base_dir)
    
    global _path_provider

    if _path_provider is None:
        _path_provider = PathProvider(base_dir)

    return _path_provider


def set_path_provider(provider: PathProvider) -> None:
    """
    Set a custom PathProvider instance.

    Useful for testing or custom configurations.

    Args:
        provider: PathProvider instance to set as global
    """
    global _path_provider
    _path_provider = provider

