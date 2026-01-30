"""
AI Package - Central AI/ML inference hub
Houses all AI tasks: recommendations, field classification, summarization, intent detection, validation
This package is designed to be portable and reusable in other projects.

Modules:
- job_recommender: Job/Scheme recommendation based on user profile
- field_classifier: Form field type detection and mapping  
- summarizer: Content rewriting and summarization
- intent_classifier: WhatsApp message intent detection
- validator: Document and field validation
- learning_system: Self-learning AI with OpenAI integration (optional)
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
    from .learning_system import SelfLearningAI
    
    logger.info("All AI modules loaded successfully")
except Exception as e:
    logger.warning(f"Some AI modules could not be loaded: {e}")

__all__ = [
    "JobRecommender",
    "FieldClassifier",
    "ContentSummarizer",
    "IntentClassifier",
    "IntentType",
    "DocumentValidator",
    "DocumentType",
    "ValidationStatus",
    "SelfLearningAI",
]
