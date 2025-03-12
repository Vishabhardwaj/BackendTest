import logging
from typing import List, Optional, Dict, Any
from Bio import Entrez
from dataclasses import dataclass
import re
from datetime import datetime

# Set a default email for Entrez API (required by PubMed)
Entrez.email = "your-email@example.com"

@dataclass
class Author:
    name: str
    affiliations: List[str]

@dataclass
class Paper:
    pmid: str
    title: str
    publication_date: str
    authors: List[Author]
    corresponding_email: str

def search_pubmed(query: str, retmax: int = 10000) -> List[str]:
    """Search PubMed for papers matching the query and return PMIDs."""
    try:
        handle = Entrez.esearch(db="pubmed", term=query, retmax=retmax)
        result = Entrez.read(handle)
        handle.close()
        return result["IdList"]
    except Exception as e:
        logging.error(f"Error searching PubMed: {e}")
        return []

def parse_pubmed_xml(records: List[Dict[str, Any]]) -> List[Paper]:
    """Parse PubMed XML records into Paper objects."""
    papers = []
    for record in records:
        try:
            medline = record.get("MedlineCitation", {})
            pmid = medline.get("PMID", ["Unknown"])[0]
            article = medline.get("Article", {})
            title = article.get("ArticleTitle", "No title available")
            
            # Parse publication date
            pub_date = article.get("Journal", {}).get("JournalIssue", {}).get("PubDate", {})
            date_parts = []
            for part in ["Year", "Month", "Day"]:
                date_part = pub_date.get(part, "Unknown")
                if isinstance(date_part, list):
                    date_part = date_part[0] if date_part else "Unknown"
                date_parts.append(str(date_part))
            publication_date = "-".join(date_parts)
            
            # Parse authors
            authors = []
            author_list = article.get("AuthorList", [])
            for author_entry in author_list:
                if author_entry.get("@ValidYN", "Y") == "N":
                    continue
                last_name = author_entry.get("LastName", "")
                fore_name = author_entry.get("ForeName", "")
                name = f"{fore_name} {last_name}".strip()
                affiliations = []
                for affil_info in author_entry.get("AffiliationInfo", []):
                    affiliation = affil_info.get("Affiliation", "")
                    if affiliation:
                        affiliations.append(affiliation)
                authors.append(Author(name=name, affiliations=affiliations))
            
            # Extract corresponding email
            corresponding_email = extract_corresponding_email(authors)
            
            papers.append(Paper(
                pmid=pmid,
                title=title,
                publication_date=publication_date,
                authors=authors,
                corresponding_email=corresponding_email
            ))
        except Exception as e:
            logging.error(f"Error parsing record: {e}")
    return papers

def fetch_papers(pmids: List[str]) -> List[Paper]:
    """Fetch and parse PubMed records for given PMIDs."""
    if not pmids:
        return []
    try:
        handle = Entrez.efetch(db="pubmed", id=pmids, retmode="xml")
        records = Entrez.read(handle)["PubmedArticle"]
        handle.close()
        return parse_pubmed_xml(records)
    except Exception as e:
        logging.error(f"Error fetching papers: {e}")
        return []

def extract_corresponding_email(authors: List[Author]) -> str:
    """Extract corresponding author's email from affiliations."""
    email_regex = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    emails = []
    for author in authors:
        for affiliation in author.affiliations:
            email_matches = email_regex.findall(affiliation)
            if email_matches:
                for email in email_matches:
                    if "correspond" in affiliation.lower():
                        return email
                    emails.append(email)
    return emails[0] if emails else ""
