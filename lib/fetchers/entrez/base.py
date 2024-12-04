from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

@dataclass
class BaseArticle:
    """
    Base class for representing scientific articles from various sources.

    This class provides a common structure for article metadata, regardless of the source
    (e.g., PubMed, ArXiv, etc.). It includes essential metadata fields and serialization
    capabilities.

    Attributes:
        title (str): Article title
        abstract (str): Article abstract or summary
        authors (List[str]): List of author names
        doi (Optional[str]): Digital Object Identifier
        source_id (str): Identifier specific to the source system (e.g., PMID for PubMed)
        source_type (str): Identifier for the source system (e.g., "pubmed", "arxiv")
        published_date (datetime): Publication date

    Example:
        >>> article = BaseArticle(
        ...     title="Example Article",
        ...     abstract="This is an example abstract",
        ...     authors=["Smith, J", "Doe, J"],
        ...     doi="10.1234/example",
        ...     source_id="12345678",
        ...     source_type="pubmed",
        ...     published_date=datetime.now()
        ... )
    """
    title: str
    abstract: str
    authors: List[str]
    doi: Optional[str]
    source_id: str
    source_type: str
    published_date: datetime

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the article to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary containing all article fields, with
                           published_date converted to ISO format string

        Example:
            >>> article = BaseArticle(...)
            >>> article_dict = article.to_dict()
            >>> print(article_dict['title'])
            >>> print(article_dict['published_date'])  # ISO format string
        """
        return {
            'title': self.title,
            'abstract': self.abstract,
            'authors': self.authors,
            'doi': self.doi,
            'source_id': self.source_id,
            'source_type': self.source_type,
            'published_date': self.published_date.isoformat(),
        }

class BaseFetcher(ABC):
    """
    Abstract base class for article fetchers from different sources.

    This class defines the interface for fetching articles and their metadata
    from various scientific article sources. Implementations should handle
    source-specific API interactions and data formatting.

    Attributes:
        config (Dict[str, Any]): Configuration parameters for the fetcher

    Example:
        >>> class PubMedFetcher(BaseFetcher):
        ...     async def search(self, query: str, max_results: Optional[int] = None):
        ...         # Implementation for PubMed search
        ...         pass
    """
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the fetcher with configuration parameters.

        Args:
            config (Dict[str, Any]): Configuration dictionary containing
                                   source-specific settings
        """
        self.config = config
    
    @abstractmethod
    async def search(self, query: str, max_results: Optional[int] = None) -> List[BaseArticle]:
        """
        Search for articles matching the query.

        Args:
            query (str): Search query string
            max_results (Optional[int], optional): Maximum number of results to return.
                                                 Defaults to None.

        Returns:
            List[BaseArticle]: List of articles matching the search criteria

        Note:
            This is an abstract method that must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def fetch_by_id(self, article_id: str) -> Optional[BaseArticle]:
        """
        Fetch a specific article by its identifier.

        Args:
            article_id (str): Source-specific article identifier

        Returns:
            Optional[BaseArticle]: Article if found, None otherwise

        Note:
            This is an abstract method that must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    async def fetch_pdf(self, article_id: str) -> Optional[bytes]:
        """
        Fetch the PDF content of an article.

        Args:
            article_id (str): Source-specific article identifier

        Returns:
            Optional[bytes]: PDF content as bytes if available, None otherwise

        Note:
            This is an abstract method that must be implemented by subclasses
        """
        pass
    
    async def batch_fetch(self, article_ids: List[str]) -> Dict[str, Optional[BaseArticle]]:
        """
        Fetch multiple articles by their identifiers.

        This is a default implementation that fetches articles sequentially.
        Subclasses may override this with more efficient batch operations.

        Args:
            article_ids (List[str]): List of article identifiers

        Returns:
            Dict[str, Optional[BaseArticle]]: Dictionary mapping article IDs to
                                            their corresponding articles (or None if not found)

        Example:
            >>> fetcher = MyFetcher(config)
            >>> articles = await fetcher.batch_fetch(["123", "456", "789"])
            >>> for article_id, article in articles.items():
            ...     if article:
            ...         print(f"{article_id}: {article.title}")
        """
        results = {}
        for article_id in article_ids:
            results[article_id] = await self.fetch_by_id(article_id)
        return results