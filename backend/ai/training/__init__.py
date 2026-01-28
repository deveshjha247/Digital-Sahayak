"""
AI Training Data Collection Package
Collects and labels datasets for training AI models from scratch

5 Data Collectors:
1. JobMatchingCollector - Job-user interaction data for ranking models
2. FormFieldCollector - Form field labeling for auto-fill
3. ContentRewritingCollector - Raw text to summary corpus
4. IntentCollector - Chat messages with intent labels
5. DocumentCollector - Document images with annotations

Quality & Analysis Tools:
- Deduplicator - Remove duplicate entries
- ClassBalanceAnalyzer - Detect class imbalances
- DiversityAnalyzer - Track data diversity
- DatasetSplitter - Train/val/test splits
- AnnotatorAgreement - Cohen's Kappa, Fleiss' Kappa
- FeedbackLoop - Continuous improvement from operator corrections
"""

from .job_matching_collector import JobMatchingCollector
from .form_field_collector import FormFieldCollector, FieldSemanticTag
from .content_rewriting_collector import ContentRewritingCollector
from .intent_collector import IntentCollector, UserIntent, INTENT_PATTERNS
from .document_collector import (
    DocumentCollector,
    DocumentType,
    QualityIssue,
    DOCUMENT_FIELDS,
)
from .data_quality import (
    Deduplicator,
    ClassBalanceAnalyzer,
    DiversityAnalyzer,
    DatasetSplitter,
    AnnotatorAgreement,
    DatasheetGenerator,
    TextNormalizer,
    FeedbackLoop,
)

__all__ = [
    # Collectors
    "JobMatchingCollector",
    "FormFieldCollector", 
    "ContentRewritingCollector",
    "IntentCollector",
    "DocumentCollector",
    
    # Enums and constants
    "FieldSemanticTag",
    "UserIntent",
    "DocumentType",
    "QualityIssue",
    "INTENT_PATTERNS",
    "DOCUMENT_FIELDS",
    
    # Quality tools
    "Deduplicator",
    "ClassBalanceAnalyzer",
    "DiversityAnalyzer",
    "DatasetSplitter",
    "AnnotatorAgreement",
    "DatasheetGenerator",
    "TextNormalizer",
    "FeedbackLoop",
]
