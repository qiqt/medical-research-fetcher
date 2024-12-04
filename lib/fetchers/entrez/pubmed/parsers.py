import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Optional, List, Dict, Any

from .types import (
    PubMedGrant, PubMedReference, PubMedAuthor,
    PubMedJournal, PubMedDates
)


class PubMedXMLParser:
    """
    A utility class for parsing PubMed XML data into structured Python objects.

    This parser handles the complex XML structure of PubMed articles and extracts various
    components including metadata, authors, references, grants, and MeSH headings. It provides
    methods to parse individual components as well as complete articles.

    The parser uses ElementTree for XML processing and returns typed data structures
    defined in the .types module.
    """
    @staticmethod
    def _get_text(element: Optional[ET.Element], xpath: str, default: str = "") -> str:
        """
        Safely extract text content from an XML element using an XPath expression.

        Args:
            element (Optional[ET.Element]): The XML element to search within
            xpath (str): XPath expression to locate the desired element
            default (str): Value to return if element or text is not found. Defaults to empty string

        Returns:
            str: Text content of the matching element or default value if not found
        """
        if element is None:
            return default
        found = element.find(xpath)
        return found.text if found is not None and found.text else default

    @staticmethod
    def _parse_date(date_elem: Optional[ET.Element]) -> Optional[datetime]:
        """
        Parse a PubMed date element into a Python datetime object.

        Args:
            date_elem (Optional[ET.Element]): XML element containing Year, Month, and Day elements

        Returns:
            Optional[datetime]: Parsed datetime object, or None if parsing fails

        Note:
            - If month is missing, defaults to January (1)
            - If day is missing, defaults to 1st of the month
            - Returns None if year is missing or invalid
        """
        if date_elem is None:
            return None

        year = date_elem.find('Year')
        month = date_elem.find('Month')
        day = date_elem.find('Day')

        if year is None:
            return None

        try:
            year_val = int(year.text)
            month_val = int(
                month.text) if month is not None and month.text.isdigit() else 1
            day_val = int(
                day.text) if day is not None and day.text.isdigit() else 1
            return datetime(year_val, month_val, day_val)
        except (ValueError, AttributeError):
            return None

    @classmethod
    def parse_grants(cls, article_elem: ET.Element) -> List[PubMedGrant]:
        """
        Parse grant information from a PubMed article XML element.

        Args:
            article_elem (ET.Element): XML element containing the article data

        Returns:
            List[PubMedGrant]: List of PubMedGrant objects containing grant information

        Example:
            >>> grants = PubMedXMLParser.parse_grants(article_element)
            >>> for grant in grants:
            ...     print(f"ID: {grant.grant_id}, Agency: {grant.agency}")
        """
        grants = []
        grant_list = article_elem.find('.//GrantList')

        if grant_list is not None:
            for grant_elem in grant_list.findall('Grant'):
                grant = PubMedGrant(
                    grant_id=cls._get_text(grant_elem, 'GrantID'),
                    acronym=cls._get_text(grant_elem, 'Acronym'),
                    agency=cls._get_text(grant_elem, 'Agency'),
                    country=cls._get_text(grant_elem, 'Country')
                )
                grants.append(grant)

        return grants

    @classmethod
    def parse_references(cls, article_elem: ET.Element) -> List[PubMedReference]:
        """
        Parse reference citations from a PubMed article XML element.

        Args:
            article_elem (ET.Element): XML element containing the article data

        Returns:
            List[PubMedReference]: List of PubMedReference objects containing citation information
                                 and identifiers (PMID, DOI, PMC ID)

        Example:
            >>> references = PubMedXMLParser.parse_references(article_element)
            >>> for ref in references:
            ...     print(f"Citation: {ref.citation}, DOI: {ref.doi}")
        """
        references = []
        ref_list = article_elem.find('.//ReferenceList')

        if ref_list is not None:
            for ref_elem in ref_list.findall('Reference'):
                citation = cls._get_text(ref_elem, 'Citation')
                article_ids = ref_elem.find('ArticleIdList')

                pmid = None
                doi = None
                pmc_id = None

                if article_ids is not None:
                    for id_elem in article_ids.findall('ArticleId'):
                        id_type = id_elem.get('IdType', '')
                        if id_type == 'pubmed':
                            pmid = id_elem.text
                        elif id_type == 'doi':
                            doi = id_elem.text
                        elif id_type == 'pmc':
                            pmc_id = id_elem.text

                reference = PubMedReference(
                    citation=citation,
                    pmid=pmid,
                    doi=doi,
                    pmc_id=pmc_id
                )
                references.append(reference)

        return references

    @classmethod
    def parse_authors(cls, article_elem: ET.Element) -> List[PubMedAuthor]:
        """
        Parse author information from a PubMed article XML element.

        Args:
            article_elem (ET.Element): XML element containing the article data

        Returns:
            List[PubMedAuthor]: List of PubMedAuthor objects containing author details
                               including names and affiliations

        Example:
            >>> authors = PubMedXMLParser.parse_authors(article_element)
            >>> for author in authors:
            ...     print(f"{author.last_name}, {author.fore_name}")
            ...     print(f"Affiliations: {', '.join(author.affiliations)}")
        """
        authors = []
        author_list = article_elem.find('.//AuthorList')

        if author_list is not None:
            for author_elem in author_list.findall('Author'):
                affiliations = [
                    aff.text for aff in author_elem.findall('.//Affiliation')
                    if aff.text
                ]

                author = PubMedAuthor(
                    last_name=cls._get_text(author_elem, 'LastName'),
                    fore_name=cls._get_text(author_elem, 'ForeName') or None,
                    initials=cls._get_text(author_elem, 'Initials') or None,
                    affiliations=affiliations
                )
                authors.append(author)

        return authors

    @classmethod
    def parse_journal(cls, article_elem: ET.Element) -> PubMedJournal:
        """
        Parse journal metadata from a PubMed article XML element.

        Args:
            article_elem (ET.Element): XML element containing the article data

        Returns:
            PubMedJournal: Object containing journal metadata including title,
                          abbreviation, ISSN, volume, and issue

        Example:
            >>> journal = PubMedXMLParser.parse_journal(article_element)
            >>> print(f"{journal.title} ({journal.iso_abbreviation})")
            >>> print(f"Volume {journal.volume}, Issue {journal.issue}")
        """
        journal_elem = article_elem.find('.//Journal')
        if journal_elem is None:
            return PubMedJournal("Unknown Journal", None, None, None, None)

        return PubMedJournal(
            title=cls._get_text(journal_elem, 'Title'),
            iso_abbreviation=cls._get_text(
                journal_elem, 'ISOAbbreviation') or None,
            issn=cls._get_text(journal_elem, 'ISSN') or None,
            volume=cls._get_text(journal_elem, './/Volume') or None,
            issue=cls._get_text(journal_elem, './/Issue') or None
        )

    @classmethod
    def parse_dates(cls, article_elem: ET.Element) -> PubMedDates:
        """
        Parse publication dates from a PubMed article XML element.

        Args:
            article_elem (ET.Element): XML element containing the article data

        Returns:
            PubMedDates: Object containing various publication dates (completed,
                        revised, electronic publication, and print publication)

        Note:
            Returns None for any date that cannot be parsed or is missing required elements
        """
        return PubMedDates(
            completed=cls._parse_date(article_elem.find('.//DateCompleted')),
            revised=cls._parse_date(article_elem.find('.//DateRevised')),
            electronic_pub=cls._parse_date(
                article_elem.find('.//ArticleDate[@DateType="Electronic"]')
            ),
            pub_date=cls._parse_date(article_elem.find('.//PubDate'))
        )

    @classmethod
    def parse_pubmed_article(cls, xml_content: str) -> Dict[str, Any]:
        """
        Parse a complete PubMed article XML into a structured dictionary.

        This method extracts all available information from a PubMed article XML
        including metadata, authors, dates, references, MeSH headings, and chemical
        substances.

        Args:
            xml_content (str): Complete PubMed article XML string

        Returns:
            Dict[str, Any]: Dictionary containing all parsed article data with the following keys:
                - pmid: PubMed ID
                - title: Article title
                - abstract: Article abstract
                - journal: Journal metadata
                - authors: List of authors with affiliations
                - dates: Publication dates
                - publication_types: List of publication types
                - keywords: List of keywords
                - mesh_headings: List of MeSH terms with qualifiers
                - grants: List of funding grants
                - references: List of cited references
                - chemicals: List of chemical substances

        Raises:
            ValueError: If the XML doesn't contain a PubmedArticle element
            xml.etree.ElementTree.ParseError: If the XML is malformed

        Example:
            >>> xml_content = '''<?xml version="1.0"?>
            ... <!DOCTYPE PubmedArticleSet PUBLIC "-//NLM//DTD PubMedArticle, 1st January 2019//EN" "https://dtd.nlm.nih.gov/ncbi/pubmed/out/pubmed_190101.dtd">
            ... <PubmedArticleSet>
            ...     <PubmedArticle>
            ...         <!-- Article content -->
            ...     </PubmedArticle>
            ... </PubmedArticleSet>'''
            >>> article_data = PubMedXMLParser.parse_pubmed_article(xml_content)
            >>> print(f"Title: {article_data['title']}")
            >>> print(f"Authors: {len(article_data['authors'])}")
        """
        root = ET.fromstring(xml_content)
        article_set = root.find('.//PubmedArticle')

        if article_set is None:
            raise ValueError("No PubmedArticle element found in XML")

        medline_citation = article_set.find('MedlineCitation')
        article = medline_citation.find('Article')

        journal = cls.parse_journal(article)
        authors = cls.parse_authors(article)
        dates = cls.parse_dates(article_set)
        grants = cls.parse_grants(article)
        references = cls.parse_references(article_set)

        return {
            'pmid': cls._get_text(medline_citation, 'PMID'),
            'title': cls._get_text(article, 'ArticleTitle'),
            'abstract': cls._get_text(article, './/Abstract/AbstractText'),
            'journal': journal.__dict__,
            'authors': [author.__dict__ for author in authors],
            'dates': {k: v.isoformat() if v else None
                      for k, v in dates.__dict__.items()},
            'publication_types': [
                pt.text for pt in article.findall('.//PublicationType')
            ],
            'keywords': [
                kw.text for kw in medline_citation.findall('.//Keyword')
            ],
            'mesh_headings': [
                {
                    'descriptor': desc.text,
                    'major_topic': desc.get('MajorTopicYN', 'N') == 'Y',
                    'qualifiers': [
                        {
                            'name': qual.text,
                            'major_topic': qual.get('MajorTopicYN', 'N') == 'Y'
                        }
                        for qual in mh.findall('QualifierName')
                    ]
                }
                for mh in medline_citation.findall('.//MeshHeading')
                if (desc := mh.find('DescriptorName')) is not None
            ],
            'grants': [grant.__dict__ for grant in grants],
            'references': [ref.__dict__ for ref in references],
            'chemicals': [
                {
                    'registry_number': cls._get_text(chem, 'RegistryNumber'),
                    'substance_name': cls._get_text(chem, 'NameOfSubstance')
                }
                for chem in medline_citation.findall('.//Chemical')
            ]
        }
