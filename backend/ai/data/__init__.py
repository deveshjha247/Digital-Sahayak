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
from .pipeline import DataPipeline, run_pipeline
from .preprocessor import DataPreprocessor, TextNormalizer, preprocess_dataset
from .annotation_guidelines import (
    AnnotationGuidelinesManager,
    get_guidelines_manager,
    FORM_FIELD_TYPES,
    INTENT_LABELS,
    SENSITIVE_FIELDS,
)
from .annotation_pipeline import (
    HeuristicPreLabeler,
    ConsensusManager,
    AnnotationDeduplicator,
    QualityTracker,
    AnnotationPipeline,
)
from .agreement_metrics import (
    AgreementMetrics,
    AgreementAnalyzer,
    compute_agreement_report,
)
from .labeling_functions import (
    LabelingFunction,
    LabelModel,
    ABSTAIN,
    get_intent_label_model,
    get_job_category_label_model,
    get_form_field_label_model,
)
from .quality_control import (
    QualityControlSystem,
    AnnotatorPool,
    Annotator,
    AnnotatorLevel,
    AnnotationTask,
    ConsistencyChecker,
    create_quality_control_system,
)
from .synthetic import (
    SyntheticJobGenerator,
    SyntheticUserGenerator,
    SyntheticInteractionGenerator,
    generate_training_dataset,
)
from .scrapers import BaseScraper

__all__ = [
    # Config
    "DataConfig",
    "SOURCES",
    "CATEGORIES",
    "STATES",
    # Collection
    "DataCollector",
    "BaseScraper",
    # Processing
    "DataBalancer",
    "MetadataManager",
    "DataPreprocessor",
    "TextNormalizer",
    "preprocess_dataset",
    # Annotation
    "AnnotationGuidelinesManager",
    "get_guidelines_manager",
    "FORM_FIELD_TYPES",
    "INTENT_LABELS",
    "SENSITIVE_FIELDS",
    "HeuristicPreLabeler",
    "ConsensusManager",
    "AnnotationDeduplicator",
    "QualityTracker",
    "AnnotationPipeline",
    # Agreement Metrics
    "AgreementMetrics",
    "AgreementAnalyzer",
    "compute_agreement_report",
    # Labeling Functions (Programmatic Labeling)
    "LabelingFunction",
    "LabelModel",
    "ABSTAIN",
    "get_intent_label_model",
    "get_job_category_label_model",
    "get_form_field_label_model",
    # Quality Control
    "QualityControlSystem",
    "AnnotatorPool",
    "Annotator",
    "AnnotatorLevel",
    "AnnotationTask",
    "ConsistencyChecker",
    "create_quality_control_system",
    # Pipeline
    "DataPipeline",
    "run_pipeline",
    # Synthetic
    "SyntheticJobGenerator",
    "SyntheticUserGenerator",
    "SyntheticInteractionGenerator",
    "generate_training_dataset",
]
