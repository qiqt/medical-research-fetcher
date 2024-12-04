import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class LocalStorage:
    """
    A class for managing local file storage with a structured directory hierarchy.
    
    This class handles the creation and management of a standardized directory structure
    for storing various types of files (PDFs, metadata, etc.) and ensures all necessary
    directories exist before file operations.

    Directory Structure:
        base_path/
        ├── pdfs/
        ├── metadata/
        │   ├── xml/
        │   ├── summary/
        │   └── searches/

    Attributes:
        base_path (Path): Base directory path for all storage operations

    Example:
        >>> storage = LocalStorage(Path("/data/pubmed"))
        >>> success = await storage.save_file(
        ...     content=b"file content",
        ...     relative_path="metadata/xml/12345.json"
        ... )
    """
    def __init__(self, base_path: Path):
        """
        Initialize the LocalStorage with a base directory path.

        Args:
            base_path (Path): Path to the base directory for all storage operations.
                            Will be created if it doesn't exist.

        Example:
            >>> storage = LocalStorage(Path("/data/pubmed"))
        """
        self.base_path = Path(base_path)
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """
        Create the standard directory structure if it doesn't exist.

        Creates the following directory hierarchy:
        - base_path/pdfs/
        - base_path/metadata/
        - base_path/metadata/xml/
        - base_path/metadata/summary/
        - base_path/metadata/searches/

        Note:
            - Creates parent directories as needed
            - Logs creation of each directory at debug level
            - Silently handles cases where directories already exist
        """
        self.base_path.mkdir(parents=True, exist_ok=True)

        dirs = [
            "pdfs",
            "metadata",
            "metadata/xml",
            "metadata/summary",
            "metadata/searches"
        ]

        for dir_path in dirs:
            (self.base_path / dir_path).mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {self.base_path / dir_path}")

    async def save_file(self, content: bytes, relative_path: str, metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Save binary content to a file within the storage hierarchy.

        Args:
            content (bytes): Binary content to save
            relative_path (str): Path relative to base_path where the file should be saved
            metadata (Optional[Dict[str, Any]], optional): Additional metadata about the file.
                                                         Currently unused. Defaults to None.

        Returns:
            bool: True if save was successful, False if an error occurred

        Note:
            - Creates any missing parent directories
            - Logs successful saves at info level
            - Logs failures at error level
            - Paths are always resolved relative to base_path

        Example:
            >>> content = b"Hello, World!"
            >>> success = await storage.save_file(
            ...     content=content,
            ...     relative_path="metadata/test.txt",
            ...     metadata={"type": "test"}
            ... )
        
        Raises:
            No exceptions are raised, but failures are logged and return False
        """
        try:
            full_path = self.base_path / relative_path

            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, 'wb') as f:
                f.write(content)

            logger.info(f"Successfully saved file to {full_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving file {relative_path}: {e}")
            return False
