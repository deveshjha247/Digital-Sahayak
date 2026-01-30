"""
DS-Search: Digital Sahayak Intelligent Search System
=====================================================
Fallback intelligence layer for real-time information retrieval.

Architecture:
1. Local DB / Internal Index (first priority)
2. Cached Search Results (Redis/file cache)
3. Trusted Crawler (free - ON by default)
4. Search API (paid - OFF by default)

Key Components:
- policy.py: Search decision rules
- querygen.py: Hindi/English query generation
- sources.py: Trusted domains management
- crawler.py: Web scraping engine
- search_api.py: Optional paid search (disabled)
- ranker.py: Result scoring & ranking
- cache.py: Multi-layer caching
- ds_search.py: Main orchestrator
"""

from .ds_search import DSSearch, get_ds_search_instance
from .policy import SearchPolicy
from .querygen import QueryGenerator
from .sources import TrustedSources
from .crawler import DSCrawler
from .ranker import ResultRanker
from .cache import SearchCache

__all__ = [
    'DSSearch',
    'get_ds_search_instance',
    'SearchPolicy',
    'QueryGenerator', 
    'TrustedSources',
    'DSCrawler',
    'ResultRanker',
    'SearchCache'
]

__version__ = "1.0.0"
