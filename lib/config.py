from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv


@dataclass
class PubMedConfig:
    """
    Configuration settings specific to PubMed API interactions.

    Attributes:
        email (str): Email address for PubMed API identification
        tool (str): Tool name for PubMed API identification
        request_delay (float): Delay between consecutive API requests in seconds
        max_retries (int): Maximum number of retry attempts for failed requests

    Example:
        >>> config = PubMedConfig(
        ...     email="researcher@example.com",
        ...     tool="ResearchTool",
        ...     request_delay=0.34,
        ...     max_retries=3
        ... )
    """
    email: str
    tool: str
    request_delay: float
    max_retries: int


@dataclass
class Config:
    """
    Main configuration class containing all application settings.

    Combines PubMed-specific settings with general application settings like
    storage paths and request handling parameters.

    Attributes:
        pubmed_email (str): Email address for PubMed API identification
        pubmed_tool (str): Tool name for PubMed API identification
        storage_path (Path): Base path for data storage
        pdf_storage_path (Path): Specific path for PDF storage
        request_delay (float): Delay between consecutive API requests in seconds
        max_retries (int): Maximum number of retry attempts for failed requests

    Example:
        >>> config = Config(
        ...     pubmed_email="researcher@example.com",
        ...     pubmed_tool="ResearchTool",
        ...     storage_path=Path("./data"),
        ...     pdf_storage_path=Path("./data/pdfs"),
        ...     request_delay=0.34,
        ...     max_retries=3
        ... )
    """
    pubmed_email: str
    pubmed_tool: str
    storage_path: Path
    pdf_storage_path: Path
    request_delay: float
    max_retries: int

    def get_pubmed_config(self) -> PubMedConfig:
        """
        Create a PubMedConfig instance from the main configuration.

        Returns:
            PubMedConfig: Configuration object specific to PubMed operations

        Example:
            >>> config = Config(...)
            >>> pubmed_config = config.get_pubmed_config()
            >>> print(pubmed_config.email)  # researcher@example.com
        """
        return PubMedConfig(
            email=self.pubmed_email,
            tool=self.pubmed_tool,
            request_delay=self.request_delay,
            max_retries=self.max_retries
        )


def load_config() -> Config:
    """
    Load application configuration from environment variables.

    This function loads configuration settings from environment variables,
    with fallbacks to default values where appropriate. It uses python-dotenv
    to load variables from a .env file if present.

    Environment Variables:
        PUBMED_EMAIL (str): Required. Email address for PubMed API
        PUBMED_TOOL (str): Optional. Tool name for PubMed API. Default: 'PubMedTool'
        STORAGE_PATH (str): Optional. Base storage path. Default: './data'
        PDF_STORAGE_PATH (str): Optional. PDF storage path. Default: './data/pdfs'
        REQUEST_DELAY (str): Optional. API request delay in seconds. Default: '0.34'
        MAX_RETRIES (str): Optional. Maximum retry attempts. Default: '3'

    Returns:
        Config: Configuration object populated with settings

    Raises:
        ValueError: If required PUBMED_EMAIL environment variable is missing
        ValueError: If REQUEST_DELAY or MAX_RETRIES cannot be converted to proper types

    Example:
        >>> # With .env file:
        >>> # PUBMED_EMAIL=researcher@example.com
        >>> # PUBMED_TOOL=MyTool
        >>> config = load_config()
        >>> print(config.pubmed_email)  # researcher@example.com
        >>> print(config.pubmed_tool)   # MyTool

    Note:
        - Uses python-dotenv to load .env file if present
        - Provides sensible defaults for optional settings
        - Validates required email setting
        - Converts string environment variables to appropriate types
    """
    load_dotenv()

    pubmed_email = os.getenv('PUBMED_EMAIL')
    if not pubmed_email:
        raise ValueError("PUBMED_EMAIL environment variable is required")

    return Config(
        pubmed_email=pubmed_email,
        pubmed_tool=os.getenv('PUBMED_TOOL', 'PubMedTool'),
        storage_path=Path(os.getenv('STORAGE_PATH', './data')),
        pdf_storage_path=Path(os.getenv('PDF_STORAGE_PATH', './data/pdfs')),
        request_delay=float(os.getenv('REQUEST_DELAY', '0.34')),
        max_retries=int(os.getenv('MAX_RETRIES', '3'))
    )
