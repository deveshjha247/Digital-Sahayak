"""
AI Package - Central AI/ML inference hub
Houses all AI tasks: recommendations, field classification, summarization, intent detection, validation
This package is designed to be portable and reusable in other projects.

Architecture Overview:
- Job Recommender: LambdaMART (gradient-boosted ranking) + Two-Tower retrieval
- Field Classifier: CNN (field detection) + Transformer (label understanding) + Rules
- Summarizer: T5/mT5 (abstractive summarization) + Templates
- Intent Classifier: DistilBERT + Bag-of-Words + Keywords
- Validator: OCR (Tesseract/EasyOCR) + CNN (document classification) + Rules

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- All labels, messages, intents support both languages without translation API

Modules:
- job_recommender: Job/Scheme recommendation based on user profile (LambdaMART)
- field_classifier: Form field type detection and mapping (CNN + Transformer)
- summarizer: Content rewriting and summarization (T5/mT5)
- intent_classifier: WhatsApp message intent detection (DistilBERT)
- validator: Document and field validation (OCR + CNN)
- learning_system: Self-learning AI with OpenAI integration (optional)
- language_helper: Bilingual support (English + Hindi)
"""

import logging

logger = logging.getLogger(__name__)

# Version
__version__ = "2.0.0"

# Language config
PRIMARY_LANGUAGE = "en"
SECONDARY_LANGUAGE = "hi"

# Import AI modules for easy access
try:
    # Core rule-based modules
    from .job_recommender import JobRecommender
    from .field_classifier import FieldClassifier
    from .summarizer import ContentSummarizer
    from .intent_classifier import IntentClassifier, IntentType
    from .validator import DocumentValidator, DocumentType, ValidationStatus
    from .learning_system import SelfLearningAI
    
    # Advanced ML modules
    from .job_recommender import (
        AdvancedJobRecommender,
        FeatureExtractor,
        TwoTowerRetriever,
        LambdaMARTRanker,
        get_recommendations
    )
    from .field_classifier import (
        AdvancedFieldClassifier,
        TransformerLabelUnderstanding,
        CNNFieldDetector,
        classify_field,
        auto_fill_form
    )
    from .summarizer import (
        AdvancedSummarizer,
        T5Summarizer,
        TranslationAugmenter,
        rewrite,
        summarize
    )
    from .intent_classifier import (
        AdvancedIntentClassifier,
        DistilBERTIntentClassifier,
        BagOfWordsClassifier,
        predict_intent
    )
    from .validator import (
        AdvancedDocumentValidator,
        TesseractOCR,
        EasyOCRExtractor,
        CNNDocumentClassifier,
        extract_document_text,
        validate_document,
        check_document_quality
    )
    
    # Language helper
    from .language_helper import (
        LanguageHelper, 
        get_language_helper,
        t, t_both, t_bi, detect_lang,
        EDUCATION_BILINGUAL,
        CATEGORY_BILINGUAL,
        STATE_BILINGUAL
    )
    
    logger.info("All AI modules loaded successfully")
except Exception as e:
    logger.warning(f"Some AI modules could not be loaded: {e}")

__all__ = [
    # ========== Core Rule-Based Modules ==========
    "JobRecommender",
    "FieldClassifier", 
    "ContentSummarizer",
    "IntentClassifier",
    "IntentType",
    "DocumentValidator",
    "DocumentType",
    "ValidationStatus",
    "SelfLearningAI",
    
    # ========== Advanced ML Modules ==========
    # Job Recommender (LambdaMART + Two-Tower)
    "AdvancedJobRecommender",
    "FeatureExtractor",
    "TwoTowerRetriever",
    "LambdaMARTRanker",
    "get_recommendations",
    
    # Field Classifier (CNN + Transformer)
    "AdvancedFieldClassifier",
    "TransformerLabelUnderstanding",
    "CNNFieldDetector",
    "classify_field",
    "auto_fill_form",
    
    # Summarizer (T5/mT5)
    "AdvancedSummarizer",
    "T5Summarizer",
    "TranslationAugmenter",
    "rewrite",
    "summarize",
    
    # Intent Classifier (DistilBERT)
    "AdvancedIntentClassifier",
    "DistilBERTIntentClassifier",
    "BagOfWordsClassifier",
    "predict_intent",
    
    # Document Validator (OCR + CNN)
    "AdvancedDocumentValidator",
    "TesseractOCR",
    "EasyOCRExtractor",
    "CNNDocumentClassifier",
    "extract_document_text",
    "validate_document",
    "check_document_quality",
    
    # ========== Language Support ==========
    "LanguageHelper",
    "get_language_helper",
    "t",  # translate shorthand
    "t_both",  # get both languages
    "t_bi",  # bilingual text
    "detect_lang",  # detect language
    "EDUCATION_BILINGUAL",
    "CATEGORY_BILINGUAL",
    "STATE_BILINGUAL",
    
    # ========== Config ==========
    "PRIMARY_LANGUAGE",
    "SECONDARY_LANGUAGE",
]
