"""
AI Data Collection Module
Handles data sourcing, scraping, synthetic generation, and balancing for AI training

Components:
- scrapers/: Web scrapers for different data sources
- synthetic/: Synthetic data generators
- raw/: Raw collected data (gitignored)
- processed/: Cleaned and processed data

Metadata Schema:
- source: Where data came from
- collection_date: When collected
- state: Indian state (for diversity)
- category: Job/scheme category
- language: en/hi/hinglish
- verified: Whether human-verified
"""

from .data_config import DataConfig, SOURCES, CATEGORIES, STATES
from .collector import DataCollector
from .balancer import DataBalancer
from .metadata import MetadataManager

__all__ = [
    "DataConfig",
    "DataCollector", 
    "DataBalancer",
    "MetadataManager",
    "SOURCES",
    "CATEGORIES",
    "STATES"
]
