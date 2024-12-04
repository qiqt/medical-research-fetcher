from datetime import datetime
from typing import List, Optional, Dict, Any

from ....fetchers.entrez.base import BaseArticle
from .types import (
    PubMedGrant, PubMedReference, PubMedAuthor,
    PubMedJournal, PubMedDates
)
from .parsers import PubMedXMLParser


class PubMedArticle(BaseArticle):
    """
    A class representing a PubMed article with comprehensive metadata and related information.

    This class extends BaseArticle and provides additional fields and methods specific to
    PubMed articles, including author details, journal information, MeSH headings, grants,
    and references.

    Attributes:
        title (str): Article title
        abstract (str): Article abstract
        authors (List[str]): List of author names
        doi (Optional[str]): Digital Object Identifier
        pmid (str): PubMed ID
        keywords (List[str]): Article keywords
        related_dois (List[str]): Related DOIs
        published_date (datetime): Publication date
        journal (Optional[str]): Journal name
        volume (Optional[str]): Journal volume
        issue (Optional[str]): Journal issue
        pages (Optional[str]): Article pages
        pubtype (Optional[List[str]]): Publication types
        author_details (Optional[List[PubMedAuthor]]): Detailed author information
        journal_details (Optional[PubMedJournal]): Detailed journal information
        dates (Optional[PubMedDates]): Various publication dates
        mesh_headings (Optional[List[Dict[str, Any]]]): MeSH terms and qualifiers
        grants (Optional[List[PubMedGrant]]): Funding information
        references (Optional[List[PubMedReference]]): Cited references
        chemicals (Optional[List[Dict[str, str]]]): Chemical substances

    Examples:
        >>> article = PubMedArticle(
        ...     title="Example Article",
        ...     abstract="This is an abstract",
        ...     authors=["Smith, J", "Doe, J"],
        ...     doi="10.1234/example",
        ...     pmid="12345678",
        ...     keywords=["keyword1", "keyword2"],
        ...     related_dois=[],
        ...     published_date=datetime.now()
        ... )
    """
    def __init__(self,
                 title: str,
                 abstract: str,
                 authors: List[str],
                 doi: Optional[str],
                 pmid: str,
                 keywords: List[str],
                 related_dois: List[str],
                 published_date: datetime,
                 journal: Optional[str] = None,
                 volume: Optional[str] = None,
                 issue: Optional[str] = None,
                 pages: Optional[str] = None,
                 pubtype: Optional[List[str]] = None,
                 author_details: Optional[List[PubMedAuthor]] = None,
                 journal_details: Optional[PubMedJournal] = None,
                 dates: Optional[PubMedDates] = None,
                 mesh_headings: Optional[List[Dict[str, Any]]] = None,
                 grants: Optional[List[PubMedGrant]] = None,
                 references: Optional[List[PubMedReference]] = None,
                 chemicals: Optional[List[Dict[str, str]]] = None
                 ):
        """
        Initialize a PubMedArticle instance.

        Args:
            title (str): Article title
            abstract (str): Article abstract
            authors (List[str]): List of author names
            doi (Optional[str]): Digital Object Identifier
            pmid (str): PubMed ID
            keywords (List[str]): Article keywords
            related_dois (List[str]): Related DOIs
            published_date (datetime): Publication date
            journal (Optional[str], optional): Journal name. Defaults to None.
            volume (Optional[str], optional): Journal volume. Defaults to None.
            issue (Optional[str], optional): Journal issue. Defaults to None.
            pages (Optional[str], optional): Article pages. Defaults to None.
            pubtype (Optional[List[str]], optional): Publication types. Defaults to None.
            author_details (Optional[List[PubMedAuthor]], optional): Detailed author information. Defaults to None.
            journal_details (Optional[PubMedJournal], optional): Detailed journal information. Defaults to None.
            dates (Optional[PubMedDates], optional): Various publication dates. Defaults to None.
            mesh_headings (Optional[List[Dict[str, Any]]], optional): MeSH terms and qualifiers. Defaults to None.
            grants (Optional[List[PubMedGrant]], optional): Funding information. Defaults to None.
            references (Optional[List[PubMedReference]], optional): Cited references. Defaults to None.
            chemicals (Optional[List[Dict[str, str]]], optional): Chemical substances. Defaults to None.
        """
        super().__init__(
            title=title,
            abstract=abstract,
            authors=authors,
            doi=doi,
            source_id=pmid,
            source_type="pubmed",
            published_date=published_date,
        )
        self.keywords = keywords
        self.related_dois = related_dois
        self.pmid = pmid
        self.journal = journal
        self.volume = volume
        self.issue = issue
        self.pages = pages
        self.pubtype = pubtype or []

        self.author_details = author_details or []
        self.journal_details = journal_details
        self.dates = dates
        self.mesh_headings = mesh_headings or []
        self.grants = grants or []
        self.references = references or []
        self.chemicals = chemicals or []

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the PubMedArticle instance to a dictionary representation.

        Returns:
            Dict[str, Any]: Dictionary containing all article data, including:
                - Basic article information (title, abstract, authors, etc.)
                - PubMed-specific fields (keywords, PMID, journal info)
                - Extended metadata (author details, grants, references, etc.)
                All datetime objects are converted to ISO format strings.

        Example:
            >>> article_dict = article.to_dict()
            >>> print(f"Title: {article_dict['title']}")
            >>> print(f"Number of authors: {len(article_dict['authors'])}")
        """
        base_dict = super().to_dict()
        
        base_dict.update({
            'keywords': self.keywords,
            'related_dois': self.related_dois,
            'pmid': self.pmid,
            'journal': self.journal,
            'volume': self.volume,
            'issue': self.issue,
            'pages': self.pages,
            'pubtype': self.pubtype
        })

        if self.author_details:
            base_dict['author_details'] = [
                author.__dict__ for author in self.author_details
            ]
        if self.journal_details:
            base_dict['journal_details'] = self.journal_details.__dict__
        if self.dates:
            base_dict['dates'] = {
                k: v.isoformat() if v else None 
                for k, v in self.dates.__dict__.items()
            }
        if self.mesh_headings:
            base_dict['mesh_headings'] = self.mesh_headings
        if self.grants:
            base_dict['grants'] = [grant.__dict__ for grant in self.grants]
        if self.references:
            base_dict['references'] = [ref.__dict__ for ref in self.references]
        if self.chemicals:
            base_dict['chemicals'] = self.chemicals

        return base_dict

    @classmethod
    def from_esummary(cls, summary_data: Dict[str, Any]) -> 'PubMedArticle':
        """
        Create a PubMedArticle instance from PubMed E-utilities summary data.

        Args:
            summary_data (Dict[str, Any]): Article summary data from PubMed E-utilities

        Returns:
            PubMedArticle: New article instance with data from summary

        Raises:
            ValueError: If the summary data format is invalid

        Note:
            - Handles various date formats from PubMed
            - Extracts DOI from article identifiers if available
            - Uses current date as fallback if publication date parsing fails

        Example:
            >>> summary = {"result": {"123": {"title": "Example", "authors": [...]}}}
            >>> article = PubMedArticle.from_esummary(summary)
        """
        article_data = next(iter(summary_data.get('result', {}).values()))
        if not isinstance(article_data, dict):
            raise ValueError("Invalid summary data format")

        doi = None
        for id_obj in article_data.get('articleids', []):
            if id_obj.get('idtype') == 'doi':
                doi = id_obj.get('value')
                break

        try:
            pub_date_str = article_data.get('sortpubdate', '')
            published_date = datetime.strptime(pub_date_str, '%Y/%m/%d %H:%M')
        except (ValueError, TypeError):
            try:
                pub_date_str = article_data.get('pubdate', '')
                published_date = datetime.strptime(pub_date_str, '%Y %b')
            except (ValueError, TypeError):
                published_date = datetime.now()

        authors = [
            author['name'] 
            for author in article_data.get('authors', [])
            if isinstance(author, dict) and 'name' in author
        ]

        return cls(
            title=article_data.get('title', 'No title available'),
            abstract='',
            authors=authors,
            doi=doi,
            pmid=article_data.get('uid', 'No PMID available'),
            keywords=[],
            related_dois=[],
            published_date=published_date,
            journal=article_data.get('fulljournalname'),
            volume=article_data.get('volume'),
            issue=article_data.get('issue'),
            pages=article_data.get('pages'),
            pubtype=article_data.get('pubtype', [])
        )

    @classmethod
    def from_pymed_article(cls, article: Any) -> 'PubMedArticle':
        """
        Create a PubMedArticle instance from a PyMed article object.

        Args:
            article (Any): PyMed article object

        Returns:
            PubMedArticle: New article instance with data from PyMed

        Note:
            - Handles various data formats and potential missing fields
            - Processes multiple DOIs, keeping the first as primary
            - Cleans and normalizes author names
            - Uses current date as fallback for missing publication dates

        Example:
            >>> pymed_article = pubmed.query("cancer", max_results=1)[0]
            >>> article = PubMedArticle.from_pymed_article(pymed_article)
        """
        title = article.title if article.title else 'No title available'
        if isinstance(title, (list, tuple)):
            title = title[0]

        abstract = article.abstract if article.abstract else 'No abstract available'
        if isinstance(abstract, (list, tuple)):
            abstract = abstract[0]

        keywords = article.keywords if article.keywords else []
        if isinstance(keywords, (list, tuple)) and len(keywords) > 0:
            keywords = keywords[0] if isinstance(keywords[0], list) else keywords

        doi = None
        related_dois = []
        if article.doi:
            dois = article.doi.split()
            doi = dois[0] if dois else None
            related_dois = dois[1:] if len(dois) > 1 else []

        pmid = article.pubmed_id.split()[0] if article.pubmed_id else 'No PMID available'

        try:
            published_date = article.publication_date if article.publication_date else datetime.now()
        except AttributeError:
            published_date = datetime.now()

        try:
            authors = [str(author) for author in article.authors] if article.authors else []
        except AttributeError:
            authors = []

        return cls(
            title=title,
            abstract=abstract,
            authors=authors,
            doi=doi,
            pmid=pmid,
            keywords=keywords,
            related_dois=related_dois,
            published_date=published_date,
            journal=getattr(article, 'journal', None),
            volume=getattr(article, 'volume', None),
            issue=getattr(article, 'issue', None),
            pages=getattr(article, 'pages', None),
            pubtype=getattr(article, 'pubtype', [])
        )

    @classmethod
    def from_xml(cls, xml_content: str) -> 'PubMedArticle':
        """
        Create a PubMedArticle instance from PubMed XML content.

        Args:
            xml_content (str): PubMed article XML string

        Returns:
            PubMedArticle: New article instance with data parsed from XML

        Note:
            - Uses PubMedXMLParser for initial XML parsing
            - Constructs author names from components
            - Handles multiple publication date formats
            - Creates detailed objects for authors, journal, grants, and references
            - Uses current date as fallback if no valid publication date is found

        Example:
            >>> xml = '''<?xml version="1.0"?>
            ... <!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2019//EN">
            ... <PubmedArticleSet>
            ...     <PubmedArticle>
            ...         <!-- Article content -->
            ...     </PubmedArticle>
            ... </PubmedArticleSet>'''
            >>> article = PubMedArticle.from_xml(xml)
        """
        metadata = PubMedXMLParser.parse_pubmed_article(xml_content)
        
        authors = [
            f"{author['last_name']}, {author['fore_name']}"
            if author.get('fore_name')
            else author['last_name']
            for author in metadata['authors']
        ]

        dates = metadata.get('dates', {})
        date_options = [
            dates.get('pub_date'),
            dates.get('electronic_pub'),
            dates.get('completed'),
            dates.get('revised')
        ]
        published_date = None
        for date_str in date_options:
            if date_str:
                try:
                    published_date = datetime.fromisoformat(date_str)
                    break
                except ValueError:
                    continue
        if not published_date:
            published_date = datetime.now()

        return cls(
            title=metadata['title'],
            abstract=metadata['abstract'],
            authors=authors,
            doi=metadata.get('doi'),
            pmid=metadata['pmid'],
            keywords=metadata.get('keywords', []),
            related_dois=[],
            published_date=published_date,
            journal=metadata['journal']['title'],
            volume=metadata['journal']['volume'],
            issue=metadata['journal']['issue'],
            pages=metadata.get('pages'),
            pubtype=metadata.get('publication_types', []),
            author_details=[
                PubMedAuthor(**author) for author in metadata['authors']
            ],
            journal_details=PubMedJournal(**metadata['journal']),
            mesh_headings=metadata.get('mesh_headings', []),
            grants=[PubMedGrant(**grant) for grant in metadata.get('grants', [])],
            references=[
                PubMedReference(**ref) for ref in metadata.get('references', [])
            ],
            chemicals=metadata.get('chemicals', [])
        )