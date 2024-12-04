from dataclasses import dataclass
from typing import List, Optional, Dict
from datetime import datetime


@dataclass
class PubMedGrant:
    """
    Data class representing a research grant associated with a PubMed article.

    Attributes:
        grant_id (Optional[str]): Unique identifier for the grant
        acronym (Optional[str]): Grant program acronym
        agency (Optional[str]): Funding agency name
        country (Optional[str]): Country of the funding agency

    Example:
        >>> grant = PubMedGrant(
        ...     grant_id="R01AI123456",
        ...     acronym="NIH",
        ...     agency="National Institutes of Health",
        ...     country="United States"
        ... )
    """
    grant_id: Optional[str]
    acronym: Optional[str]
    agency: Optional[str]
    country: Optional[str]


@dataclass
class PubMedReference:
    """
    Data class representing a reference citation in a PubMed article.

    Attributes:
        citation (str): Full text citation
        pmid (Optional[str]): PubMed ID of the referenced article
        doi (Optional[str]): Digital Object Identifier
        pmc_id (Optional[str]): PubMed Central ID

    Example:
        >>> reference = PubMedReference(
        ...     citation="Smith J et al. Cancer Research (2020)",
        ...     pmid="12345678",
        ...     doi="10.1234/example",
        ...     pmc_id="PMC7654321"
        ... )
    """
    citation: str
    pmid: Optional[str]
    doi: Optional[str]
    pmc_id: Optional[str]


@dataclass
class PubMedAuthor:
    """
    Data class representing an author of a PubMed article.

    Attributes:
        last_name (str): Author's last name
        fore_name (Optional[str]): Author's first name and middle names
        initials (Optional[str]): Author's initials
        affiliations (List[str]): List of institutional affiliations

    Methods:
        get_full_name() -> str: Returns formatted full name of the author

    Example:
        >>> author = PubMedAuthor(
        ...     last_name="Smith",
        ...     fore_name="John A",
        ...     initials="JA",
        ...     affiliations=["University of Example"]
        ... )
        >>> print(author.get_full_name())  # "Smith, John A"
    """
    last_name: str
    fore_name: Optional[str]
    initials: Optional[str]
    affiliations: List[str]

    def get_full_name(self) -> str:
        """
        Generate a formatted full name string for the author.

        Returns:
            str: Formatted name in the order "Last, First" or "Last, Initials"
                depending on available information

        Example:
            >>> author = PubMedAuthor("Smith", "John A", "JA", [])
            >>> author.get_full_name()
            'Smith, John A'
            >>> author = PubMedAuthor("Smith", None, "JA", [])
            >>> author.get_full_name()
            'Smith, JA'
        """

        if self.fore_name:
            return f"{self.last_name}, {self.fore_name}"
        elif self.initials:
            return f"{self.last_name}, {self.initials}"
        return self.last_name


@dataclass
class PubMedJournal:
    """
    Data class representing a journal in which a PubMed article was published.

    Attributes:
        title (str): Full journal title
        iso_abbreviation (Optional[str]): Standardized journal abbreviation
        issn (Optional[str]): International Standard Serial Number
        volume (Optional[str]): Journal volume
        issue (Optional[str]): Journal issue number

    Example:
        >>> journal = PubMedJournal(
        ...     title="Journal of Example Research",
        ...     iso_abbreviation="J Example Res",
        ...     issn="1234-5678",
        ...     volume="42",
        ...     issue="3"
        ... )
    """
    title: str
    iso_abbreviation: Optional[str]
    issn: Optional[str]
    volume: Optional[str]
    issue: Optional[str]


@dataclass
class PubMedDates:
    """
    Data class representing various dates associated with a PubMed article.

    Attributes:
        completed (Optional[datetime]): Date when the record was completed
        revised (Optional[datetime]): Date of last revision
        electronic_pub (Optional[datetime]): Electronic publication date
        pub_date (Optional[datetime]): Print publication date

    Methods:
        get_best_date() -> Optional[datetime]: Returns the most relevant available date

    Note:
        get_best_date() prioritizes dates in the following order:
        1. Publication date
        2. Electronic publication date
        3. Completion date
        4. Revision date

    Example:
        >>> dates = PubMedDates(
        ...     completed=datetime(2020, 1, 1),
        ...     revised=datetime(2020, 2, 1),
        ...     electronic_pub=datetime(2020, 3, 1),
        ...     pub_date=datetime(2020, 4, 1)
        ... )
        >>> best_date = dates.get_best_date()  # Returns pub_date
    """
    completed: Optional[datetime]
    revised: Optional[datetime]
    electronic_pub: Optional[datetime]
    pub_date: Optional[datetime]

    def get_best_date(self) -> Optional[datetime]:
        """
        Get the most relevant available date for the article.

        Returns:
            Optional[datetime]: The most appropriate date in order of preference:
                              pub_date > electronic_pub > completed > revised
                              Returns None if no dates are available

        Example:
            >>> dates = PubMedDates(None, None, datetime(2020, 1, 1), None)
            >>> print(dates.get_best_date())  # 2020-01-01
        """
        return (self.pub_date or
                self.electronic_pub or
                self.completed or
                self.revised)
