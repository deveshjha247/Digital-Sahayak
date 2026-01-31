"""
Scrapers Package
Web scrapers for collecting job/scheme data from various sources
"""

from .base_scraper import BaseScraper
from .ogd_india_scraper import OGDIndiaScraper, get_ogd_scraper, fetch_bihar_data

__all__ = [
    "BaseScraper",
    "OGDIndiaScraper",
    "get_ogd_scraper", 
    "fetch_bihar_data"
]
