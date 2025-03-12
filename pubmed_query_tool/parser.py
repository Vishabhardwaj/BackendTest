from typing import List, Dict, Optional

ACADEMIC_KEYWORDS = {
    "university", "college", "institute", "academy", 
    "hospital", "school", "lab", "research center", "department"
}

COMPANY_KEYWORDS = {
    "pharmaceutical", "biotech", "pharma", "bio-tech", 
    "genetics", "inc.", "ltd", "company", "corporation", "plc"
}

def is_academic_affiliation(affiliation: str) -> bool:
    """Check if affiliation contains academic keywords."""
    lower_affiliation = affiliation.lower()
    return any(keyword in lower_affiliation for keyword in ACADEMIC_KEYWORDS)

def is_company_affiliation(affiliation: str) -> bool:
    """Check if affiliation contains company keywords."""
    lower_affiliation = affiliation.lower()
    return any(keyword in lower_affiliation for keyword in COMPANY_KEYWORDS)

def process_paper(paper) -> Optional[Dict]:
    """Process a Paper object to generate CSV row data."""
    # Check if paper has any company affiliations
    has_company = any(
        is_company_affiliation(affil)
        for author in paper.authors
        for affil in author.affiliations
    )
    if not has_company:
        return None
    
    # Collect non-academic authors
    non_academic_authors = []
    for author in paper.authors:
        if any(not is_academic_affiliation(affil) for affil in author.affiliations):
            non_academic_authors.append(author.name)
    
    # Collect unique company affiliations
    company_affiliations = []
    seen = set()
    for author in paper.authors:
        for affil in author.affiliations:
            if is_company_affiliation(affil) and affil not in seen:
                seen.add(affil)
                company_affiliations.append(affil)
    
    return {
        "PubmedID": paper.pmid,
        "Title": paper.title,
        "Publication Date": paper.publication_date,
        "Non-academic Author(s)": ", ".join(non_academic_authors),
        "Company Affiliation(s)": ", ".join(company_affiliations),
        "Corresponding Author Email": paper.corresponding_email,
    }
