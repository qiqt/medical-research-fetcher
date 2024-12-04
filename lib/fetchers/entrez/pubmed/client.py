import re
import logging
from typing import List, Optional, Dict, Any
from Bio import Entrez
import asyncio
import aiohttp

from lib.config import PubMedConfig

from ....fetchers.entrez.base import BaseFetcher
from .models import PubMedArticle
from ....utils.rate_limit import rate_limit

try:
    from pymed import PubMed
except ImportError:
    print("Please install pymed using: pip install pymed")
    raise

logger = logging.getLogger(__name__)


class PubMedClient(BaseFetcher):
    """
    A client for interacting with the PubMed/NCBI E-utilities API to fetch scientific articles and metadata.

    This client provides methods to search PubMed, fetch articles by ID, download PDFs, and retrieve article
    metadata in various formats (XML, JSON). It implements rate limiting and error handling for robust
    interaction with the PubMed API.

    Attributes:
        BASE_URL (str): Base URL for NCBI E-utilities API
        tool (str): Name of the tool making the request (required by NCBI)
        email (str): Email address for API access (required by NCBI)
        pubmed (PubMed): PubMed client instance from pymed library
        request_delay (float): Delay between consecutive requests for rate limiting

    Examples:
        >>> config = PubMedConfig(tool="my_tool", email="researcher@example.com")
        >>> client = PubMedClient(config)
        >>> articles = await client.search("cancer therapy", max_results=10)
    """
    BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils"

    def __init__(self, config: PubMedConfig):
        """
        Initialize the PubMedClient with the given configuration.

        Args:
            config (PubMedConfig): Configuration object containing tool name, email, and other settings
        """
        self.tool = config.tool
        self.email = config.email

        self.pubmed = PubMed(
            tool=self.tool,
            email=self.email,
        )

        self.request_delay = config.request_delay
        logger.debug(f"PubMedClient initialized with request_delay: {
                     self.request_delay}")

        Entrez.email = config.email

    def _get_base_params(config) -> Dict[str, str]:
        """
        Get base parameters required for PubMed API requests.

        Args:
            config: Configuration object containing tool and email information

        Returns:
            Dict[str, str]: Dictionary containing base parameters for API requests
        """
        return {
            'tool': config.tool,
            'email': config.email
        }

    @staticmethod
    def clean_html_tags(text: str) -> str:
        """
        Remove HTML tags from the given text.

        Args:
            text (str): Text containing HTML tags

        Returns:
            str: Clean text with HTML tags removed
        """
        return re.sub(r"<.*?>", "", text) if text else ""

    @rate_limit()
    async def search(self, query: str, max_results: Optional[int] = None) -> List[PubMedArticle]:
        """
        Search PubMed database with the given query.

        Args:
            query (str): Search query string following PubMed query syntax
            max_results (Optional[int]): Maximum number of results to return. If None, returns all results

        Returns:
            List[PubMedArticle]: List of PubMedArticle objects matching the search criteria

        Raises:
            Exception: If there's an error during the search process

        Examples:
            >>> articles = await client.search("cancer AND therapy", max_results=100)
            >>> for article in articles:
            ...     print(article.title)
        """
        try:
            raw_results = self.pubmed.query(query, max_results=max_results)
            results = []

            for article in raw_results:
                try:
                    pubmed_article = PubMedArticle.from_pymed_article(article)
                    results.append(pubmed_article)
                except Exception as e:
                    logger.error(f"Error processing article: {e}")
                    continue

            return results

        except Exception as e:
            logger.error(f"Error during PubMed search: {e}")
            return []

    @rate_limit()
    async def fetch_by_id(self, article_id: str) -> Optional[PubMedArticle]:
        """
        Fetch a specific article by its PubMed ID (PMID).

        This method first attempts to fetch the article using XML format, and if that fails,
        falls back to using the PyMed library.

        Args:
            article_id (str): PubMed ID (PMID) of the article

        Returns:
            Optional[PubMedArticle]: PubMedArticle object if found, None otherwise

        Raises:
            Exception: If there's an error fetching or parsing the article

        Examples:
            >>> article = await client.fetch_by_id("12345678")
            >>> if article:
            ...     print(f"Title: {article.title}")
        """
        try:
            xml_content = await self.fetch_xml(article_id)
            if xml_content:
                try:
                    return PubMedArticle.from_xml(xml_content)
                except Exception as e:
                    logger.error(f"Error parsing XML for {article_id}: {e}")

            results = await self.search(f"{article_id}[pmid]", max_results=1)
            return results[0] if results else None
        except Exception as e:
            logger.error(f"Error fetching article {article_id}: {e}")
            return None

    @rate_limit(delay=0.01)
    async def fetch_pdf(self, article_id: str) -> Optional[bytes]:
        """
        Attempt to fetch the PDF version of an article from PubMed Central (PMC).

        This method first checks if the article is available in PMC, then attempts to
        download the PDF if available.

        Args:
            article_id (str): PubMed ID (PMID) of the article

        Returns:
            Optional[bytes]: PDF content as bytes if available, None otherwise

        Raises:
            Exception: If there's an error during PDF retrieval

        Examples:
            >>> pdf_content = await client.fetch_pdf("12345678")
            >>> if pdf_content:
            ...     with open("article.pdf", "wb") as f:
            ...         f.write(pdf_content)
        """
        try:
            handle = Entrez.elink(dbfrom="pubmed", db="pmc",
                                  id=article_id, linkname="pubmed_pmc")
            records = Entrez.read(handle)
            handle.close()

            if not records[0].get("LinkSetDb"):
                logger.info(f"No PMC record found for PMID {article_id}")
                return None

            pmc_links = records[0]["LinkSetDb"][0].get("Link", [])
            if not pmc_links:
                return None

            pmc_id = pmc_links[0]["Id"]
            pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmc_id}/pdf/"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.93 Safari/537.36",
                "Accept": "application/pdf",
            }

            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(pdf_url) as response:
                    if response.status == 200:
                        return await response.read()
                    elif response.status in {301, 302}:
                        logger.warning(
                            f"Redirect encountered. Final URL: {response.url}")
                        return await response.read()
                    else:
                        logger.warning(
                            f"Unexpected response for {pdf_url}: {response.status}")
                        return None

        except Exception as e:
            logger.error(f"Error fetching PDF for PMID {article_id}: {e}")
            return None

    @rate_limit()
    async def fetch_xml(self, pmid: str) -> Optional[str]:
        """
        Fetch the XML representation of an article from PubMed.

        Args:
            pmid (str): PubMed ID (PMID) of the article

        Returns:
            Optional[str]: XML content as string if successful, None otherwise

        Raises:
            Exception: If there's an error fetching the XML

        Examples:
            >>> xml_content = await client.fetch_xml("12345678")
            >>> if xml_content:
            ...     print("XML length:", len(xml_content))
        """
        url = f"{self.BASE_URL}/efetch.fcgi"
        params = {
            **self._get_base_params(),
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'xml',
            'rettype': 'full'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.text()
                    else:
                        logger.error(f"Failed to fetch XML for PMID {
                                     pmid}. Status: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Error fetching XML for PMID {pmid}: {e}")
                return None

    async def batch_fetch_pdfs(self, article_ids: List[str]) -> Dict[str, Optional[bytes]]:
        """
        Fetch PDFs for multiple articles concurrently.

        Args:
            article_ids (List[str]): List of PubMed IDs (PMIDs)

        Returns:
            Dict[str, Optional[bytes]]: Dictionary mapping PMIDs to their PDF content (or None if unavailable)

        Examples:
            >>> pdfs = await client.batch_fetch_pdfs(["12345678", "87654321"])
            >>> for pmid, content in pdfs.items():
            ...     if content:
            ...         with open(f"{pmid}.pdf", "wb") as f:
            ...             f.write(content)
        """
        tasks = [self.fetch_pdf(pmid) for pmid in article_ids]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return dict(zip(article_ids, results))

    @rate_limit()
    async def fetch_summary(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a summary of an article in JSON format.

        Args:
            pmid (str): PubMed ID (PMID) of the article

        Returns:
            Optional[Dict[str, Any]]: Article summary as a dictionary if successful, None otherwise

        Raises:
            Exception: If there's an error fetching the summary

        Examples:
            >>> summary = await client.fetch_summary("12345678")
            >>> if summary:
            ...     print("Title:", summary.get("title"))
        """
        url = f"{self.BASE_URL}/esummary.fcgi"
        params = {
            **self._get_base_params(),
            'db': 'pubmed',
            'id': pmid,
            'retmode': 'json'
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Failed to fetch summary for PMID {
                                     pmid}. Status: {response.status}")
                        return None
            except Exception as e:
                logger.error(f"Error fetching summary for PMID {pmid}: {e}")
                return None
