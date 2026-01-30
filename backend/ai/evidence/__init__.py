"""
Evidence Extractor (Facts Engine)
=================================
Transforms raw search results into structured facts.
Extracts job titles, dates, eligibility, fees, and official links.
"""

from .extractor import EvidenceExtractor, Facts, extract_facts

__all__ = [
    'EvidenceExtractor',
    'Facts',
    'extract_facts'
]

__version__ = "1.0.0"
