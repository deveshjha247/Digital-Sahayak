"""
AI Package - Central AI/ML inference hub
Houses all AI tasks: recommendations, field classification, summarization, intent detection, validation
"""

import logging

logger = logging.getLogger(__name__)

# Version
__version__ = "1.0.0"

# Import AI modules for easy access
try:
    from .job_recommender import JobRecommender
    from .field_classifier import FieldClassifier
    from .summarizer import ContentSummarizer
    from .intent_classifier import IntentClassifier, IntentType
    from .validator import DocumentValidator, DocumentType, ValidationStatus
    
    logger.info("All AI modules loaded successfully")
except Exception as e:
    logger.warning(f"Some AI modules could not be loaded: {e}")

__all__ = [
    "JobRecommender",
    "FieldClassifier",
    "ContentSummarizer",
    "IntentClassifier",
    "DocumentValidator",
]
