import json
from datetime import datetime
import logging
from typing import Dict, Any, Optional

from ..fetchers.entrez.pubmed.client import PubMedClient
from ..fetchers.entrez.pubmed.models import PubMedArticle
from ..storage.local import LocalStorage

logger = logging.getLogger(__name__)

class ArticleProcessor:
    """
    A processor class for searching, fetching, and storing PubMed articles with their associated metadata.

    This class handles the complete workflow of searching for articles, processing their content,
    and storing various formats (XML, PDF, metadata) to local storage. It includes comprehensive
    error handling and logging throughout the process.

    Attributes:
        client (PubMedClient): Client for interacting with PubMed API
        storage (LocalStorage): Storage system for saving article data and metadata

    Example:
        >>> client = PubMedClient(config)
        >>> storage = LocalStorage(base_path="/data")
        >>> processor = ArticleProcessor(client, storage)
        >>> results = await processor.search_and_process("cancer therapy", max_results=10)
    """
    def __init__(self, client: PubMedClient, storage: LocalStorage):
        """
        Initialize the ArticleProcessor with PubMed client and storage system.

        Args:
            client (PubMedClient): Initialized PubMed client for API interactions
            storage (LocalStorage): Storage system for saving retrieved data
        """
        self.client = client
        self.storage = storage

    async def search_and_process(self, query: str, max_results: int = 10) -> Dict[str, Any]:
        """
        Search for articles matching the query and process their content comprehensively.

        This method performs a complete workflow:
        1. Searches for articles matching the query
        2. Saves search metadata
        3. For each article:
           - Fetches and saves XML content
           - Fetches and saves summary data
           - Attempts to download and save PDF
        4. Creates and saves a summary of the entire process

        Args:
            query (str): Search query string
            max_results (int, optional): Maximum number of results to process. Defaults to 10.

        Returns:
            Dict[str, Any]: Processing summary containing:
                - search_id: Unique identifier for this search
                - query: Original search query
                - processed_time: Timestamp of processing
                - total_articles_found: Number of articles found
                - successfully_processed: Number of articles processed successfully
                - failed_processing: Number of articles that failed processing
                - failed_pmids: List of PMIDs that failed processing
                - articles: List of processed article metadata
                - error: Error message (if an error occurred)

        Raises:
            Exception: Logs any errors during processing but returns error summary instead of raising

        Example:
            >>> results = await processor.search_and_process("cancer immunotherapy")
            >>> print(f"Found {results['total_articles_found']} articles")
            >>> print(f"Successfully processed: {results['successfully_processed']}")
        """
        logger.info(f"\nSearching for: {query}")
        try:
            articles = await self.client.search(query, max_results=max_results)
            logger.info(f"Found {len(articles)} articles matching the query")

            search_id = datetime.now().strftime('%Y%m%d_%H%M%S')
            search_metadata = {
                "search_id": search_id,
                "query": query,
                "timestamp": datetime.now().isoformat(),
                "max_results": max_results,
                "results_found": len(articles),
                "pmids": [article.pmid for article in articles]
            }

            await self.storage.save_file(
                content=json.dumps(search_metadata, indent=2).encode('utf-8'),
                relative_path=f"metadata/searches/{search_id}.json",
                metadata={"type": "search_results"}
            )

            results = []
            failed_pmids = []

            for article in articles:
                pmid = article.pmid
                logger.info(f"\nProcessing search result PMID: {pmid}")

                try:
                    xml_content = await self.client.fetch_xml(pmid)
                    if xml_content:
                        full_article = await self.client.fetch_by_id(pmid)
                        if full_article:
                            self._log_article_details(full_article, query) 
                            metadata = full_article.to_dict()

                            if await self._save_metadata(metadata, pmid, "xml"):
                                logger.info(
                                    f"XML metadata saved for PMID {pmid}")

                            try:
                                summary_data = await self.client.fetch_summary(pmid)
                                if summary_data:
                                    await self._save_metadata(summary_data, pmid, "summary")
                                    logger.info(
                                        f"Summary metadata saved for PMID {pmid}")
                            except Exception as e:
                                logger.warning(
                                    f"Failed to fetch summary data: {e}")

                            pdf_content = await self.client.fetch_pdf(pmid)
                            if pdf_content:
                                if await self._save_pdf(pdf_content, pmid, query):
                                    logger.info(f"PDF saved for PMID {pmid}")
                                else:
                                    logger.warning(
                                        f"Failed to save PDF for PMID {pmid}")

                            results.append(metadata)
                            continue

                    failed_pmids.append(pmid)
                    logger.warning(f"Failed to process PMID {pmid}")

                except Exception as e:
                    failed_pmids.append(pmid)
                    logger.error(f"Error processing PMID {pmid}: {e}")

            summary = {
                "search_id": search_id,
                "query": query,
                "processed_time": datetime.now().isoformat(),
                "total_articles_found": len(articles),
                "successfully_processed": len(results),
                "failed_processing": len(failed_pmids),
                "failed_pmids": failed_pmids,
                "articles": results
            }

            await self.storage.save_file(
                content=json.dumps(summary, indent=2,
                                   ensure_ascii=False).encode('utf-8'),
                relative_path=f"metadata/searches/{search_id}_summary.json",
            )

            return summary

        except Exception as e:
            logger.error(f"Error in search_and_process: {str(e)}")
            return {
                "error": str(e),
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

    async def _save_metadata(self, metadata: Dict[str, Any], pmid: str, metadata_type: str = "xml") -> bool:
        """
        Save article metadata to storage with enhanced information.

        Args:
            metadata (Dict[str, Any]): Article metadata to save
            pmid (str): PubMed ID of the article
            metadata_type (str, optional): Type of metadata ('xml' or 'summary'). Defaults to "xml".

        Returns:
            bool: True if save was successful, False otherwise

        Note:
            - Enhances original metadata with timestamp and type information
            - Saves as JSON with UTF-8 encoding
            - Creates metadata directory structure: metadata/{metadata_type}/{pmid}.json

        Example:
            >>> success = await processor._save_metadata(
            ...     metadata={"title": "Example Article"},
            ...     pmid="12345678",
            ...     metadata_type="summary"
            ... )
        """
        try:
            metadata_path = f"metadata/{metadata_type}/{pmid}.json"
            enhanced_metadata = {
                **metadata,
                "saved_at": datetime.now().isoformat(),
                "metadata_type": metadata_type
            }

            content = json.dumps(enhanced_metadata, indent=2,
                                 ensure_ascii=False).encode('utf-8')
            return await self.storage.save_file(
                content=content,
                relative_path=metadata_path,
            )
        except Exception as e:
            logger.error(f"Error saving {
                         metadata_type} metadata for PMID {pmid}: {e}")
            return False

    def _log_article_details(self, article: 'PubMedArticle', query: str):
        """
        Log detailed information about a processed article.

        Logs various aspects of the article including:
        - Title and basic metadata
        - Number of authors and their affiliations
        - Keywords and MeSH headings
        - Reference count
        - Search context (query that found this article)

        Args:
            article (PubMedArticle): Article to log details for
            query (str): Search query that found this article

        Note:
            Uses the logging module to output information at INFO level
        """
        logger.info("Article details:")
        logger.info(f"Found by query: '{query}'")
        logger.info(f"Title: {article.title}")
        logger.info(f"DOI: {article.doi}")
        logger.info(f"Journal: {article.journal}")
        logger.info(f"Authors: {len(article.authors)} contributors")
        logger.info(f"Keywords: {', '.join(
            article.keywords) if article.keywords else 'None'}")

        if hasattr(article, 'author_details') and article.author_details:
            logger.info("Author affiliations available")

        if hasattr(article, 'mesh_headings') and article.mesh_headings:
            logger.info(f"MeSH Headings: {len(article.mesh_headings)}")

        if hasattr(article, 'references') and article.references:
            logger.info(f"References: {len(article.references)} citations")

    async def _save_pdf(self, pdf_content: bytes, pmid: str, query: str) -> bool:
        """
        Save PDF content to storage with associated metadata.

        Args:
            pdf_content (bytes): Binary PDF content
            pmid (str): PubMed ID of the article
            query (str): Search query that found this article

        Returns:
            bool: True if save was successful, False otherwise

        Note:
            - Saves PDF in 'pdfs' directory with PMID as filename
            - Includes metadata about file size, save time, and search context
            - Creates standard path structure: pdfs/{pmid}.pdf

        Example:
            >>> pdf_content = await client.fetch_pdf("12345678")
            >>> if pdf_content:
            ...     success = await processor._save_pdf(
            ...         pdf_content,
            ...         pmid="12345678",
            ...         query="cancer research"
            ...     )
        """
        try:
            pdf_path = f"pdfs/{pmid}.pdf"
            pdf_metadata = {
                "pmid": pmid,
                "saved_at": datetime.now().isoformat(),
                "file_size": len(pdf_content),
                "search_context": {
                    "query": query
                }
            }
            return await self.storage.save_file(
                content=pdf_content,
                relative_path=pdf_path,
                metadata=pdf_metadata
            )
        except Exception as e:
            logger.error(f"Error saving PDF for PMID {pmid}: {e}")
            return False