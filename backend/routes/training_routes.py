"""
Training Data Collection API Routes
Endpoints for collecting, labeling, and managing training datasets
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

# Import collectors
from ai.training import (
    JobMatchingCollector,
    FormFieldCollector,
    ContentRewritingCollector,
    IntentCollector,
    DocumentCollector,
    DatasetSplitter,
    ClassBalanceAnalyzer,
    DatasheetGenerator,
)

router = APIRouter(prefix="/api/training", tags=["Training Data"])

# Initialize collectors
job_collector = JobMatchingCollector()
form_collector = FormFieldCollector()
content_collector = ContentRewritingCollector()
intent_collector = IntentCollector()
document_collector = DocumentCollector()


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class JobData(BaseModel):
    title: str
    description: str
    qualification: str = ""
    category: str = ""
    state: str = ""
    district: str = ""
    salary_min: int = 0
    salary_max: int = 0
    age_min: int = 18
    age_max: int = 65
    vacancies: int = 0
    deadline: str = ""
    source_url: str = ""
    source: str = "manual"
    department: str = ""
    organization: str = ""


class UserProfileData(BaseModel):
    phone: str
    email: str = ""
    education: str = ""
    age: int = 0
    state: str = ""
    district: str = ""
    category_preferences: List[str] = []
    experience_years: int = 0
    gender: str = ""
    caste_category: str = ""


class InteractionData(BaseModel):
    user_id: str
    job_id: str
    interaction_type: str  # view, click, save, apply, reject, skip
    time_spent_seconds: int = 0
    scroll_depth: float = 0
    device: str = "unknown"
    session_id: str = ""


class MessageData(BaseModel):
    message: str
    user_id: str
    channel: str = "whatsapp"
    conversation_id: Optional[str] = None


class IntentVerification(BaseModel):
    message_id: str
    intent: str
    verifier_id: str
    notes: Optional[str] = None


class ContentData(BaseModel):
    raw_text: str
    source_url: str
    content_type: str = "job"  # job or scheme
    language: str = "en"
    title: str = ""


class SummaryData(BaseModel):
    text_id: str
    summary: str
    writer_id: str
    summary_type: str = "general"
    language: str = "en"


class FormFieldData(BaseModel):
    form_url: str
    html_content: str
    form_name: str = ""
    department: str = ""


class FieldCorrectionData(BaseModel):
    field_id: str
    original_tag: str
    corrected_tag: str
    operator_id: str
    reason: str = ""


class SplitRequest(BaseModel):
    train_ratio: float = 0.7
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    stratify: bool = True


# ============================================================================
# JOB MATCHING ENDPOINTS
# ============================================================================

@router.post("/jobs/collect")
async def collect_job(job: JobData):
    """Collect a job posting for training data"""
    job_id = job_collector.collect_job(job.dict())
    if not job_id:
        return {"status": "skipped", "reason": "duplicate"}
    return {"status": "collected", "job_id": job_id}


@router.post("/jobs/collect-batch")
async def collect_jobs_batch(jobs: List[JobData]):
    """Collect multiple jobs at once"""
    results = []
    for job in jobs:
        job_id = job_collector.collect_job(job.dict())
        results.append({
            "title": job.title[:50],
            "job_id": job_id,
            "status": "collected" if job_id else "duplicate"
        })
    return {"collected": len([r for r in results if r["status"] == "collected"]), "results": results}


@router.post("/users/collect")
async def collect_user_profile(user: UserProfileData):
    """Collect anonymized user profile"""
    user_id = job_collector.collect_user_profile(user.dict())
    return {"status": "collected", "user_id": user_id}


@router.post("/interactions/collect")
async def collect_interaction(interaction: InteractionData):
    """Collect user-job interaction"""
    result = job_collector.collect_interaction(
        user_id=interaction.user_id,
        job_id=interaction.job_id,
        interaction_type=interaction.interaction_type,
        metadata={
            "time_spent_seconds": interaction.time_spent_seconds,
            "scroll_depth": interaction.scroll_depth,
            "device": interaction.device,
            "session_id": interaction.session_id,
        }
    )
    return {"status": "collected", "interaction": result}


@router.post("/jobs/process-labels")
async def process_interaction_labels():
    """Convert interactions to training labels"""
    count = job_collector.process_interactions_to_labels()
    return {"status": "processed", "labels_created": count}


@router.get("/jobs/stats")
async def get_job_stats():
    """Get job collection statistics"""
    return job_collector.get_stats()


@router.get("/jobs/diversity")
async def get_job_diversity():
    """Get diversity analysis for collected jobs"""
    return job_collector.get_diversity_report()


@router.get("/jobs/balance")
async def get_job_class_balance():
    """Get label class balance analysis"""
    return job_collector.get_class_balance()


@router.post("/jobs/split")
async def split_job_dataset(request: SplitRequest):
    """Split job dataset into train/val/test"""
    return job_collector.split_dataset(
        train_ratio=request.train_ratio,
        val_ratio=request.val_ratio,
        test_ratio=request.test_ratio,
        stratify=request.stratify
    )


@router.post("/jobs/export")
async def export_job_training_data():
    """Export training dataset for ML model"""
    output_file = job_collector.export_training_data()
    return {"status": "exported", "file": output_file}


# ============================================================================
# INTENT CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post("/intent/collect")
async def collect_intent_message(message: MessageData):
    """Collect a chat message for intent classification"""
    result = intent_collector.collect_message(
        message=message.message,
        user_id=message.user_id,
        channel=message.channel,
        conversation_id=message.conversation_id
    )
    return {
        "status": "collected",
        "message_id": result["message_id"],
        "auto_intent": result.get("auto_intent"),
        "auto_confidence": result.get("auto_confidence"),
    }


@router.post("/intent/verify")
async def verify_intent(verification: IntentVerification):
    """Human verification of intent label"""
    from ai.training import UserIntent
    
    try:
        intent_enum = UserIntent(verification.intent)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid intent: {verification.intent}")
    
    result = intent_collector.verify_intent(
        message_id=verification.message_id,
        correct_intent=intent_enum,
        verifier_id=verification.verifier_id,
        notes=verification.notes
    )
    return {"status": "verified", "result": result}


@router.post("/intent/mark-ambiguous")
async def mark_intent_ambiguous(
    message_id: str,
    possible_intents: List[str],
    annotator_id: str,
    reason: str = None
):
    """Mark a message as ambiguous"""
    intent_collector.mark_ambiguous(message_id, possible_intents, annotator_id, reason)
    return {"status": "marked_ambiguous"}


@router.get("/intent/stats")
async def get_intent_stats():
    """Get intent collection statistics"""
    return intent_collector.get_stats()


@router.get("/intent/corrections")
async def get_intent_corrections():
    """Get correction statistics for improving rules"""
    return intent_collector.get_correction_stats()


@router.get("/intent/agreement")
async def get_intent_agreement():
    """Calculate inter-annotator agreement"""
    return intent_collector.calculate_agreement()


@router.get("/intent/balance")
async def get_intent_class_balance():
    """Get intent class balance"""
    return intent_collector.get_class_balance()


@router.get("/intent/guidelines")
async def get_intent_guidelines():
    """Get annotation guidelines for labelers"""
    return intent_collector.get_guidelines()


@router.post("/intent/split")
async def split_intent_dataset(request: SplitRequest):
    """Split intent dataset"""
    return intent_collector.split_dataset(
        train_ratio=request.train_ratio,
        val_ratio=request.val_ratio,
        test_ratio=request.test_ratio
    )


@router.post("/intent/export")
async def export_intent_training_data(min_confidence: float = 0.6, only_verified: bool = False):
    """Export intent training dataset"""
    output_file = intent_collector.export_training_data(
        min_confidence=min_confidence,
        only_verified=only_verified
    )
    return {"status": "exported", "file": output_file}


# ============================================================================
# CONTENT REWRITING ENDPOINTS
# ============================================================================

@router.post("/content/collect-raw")
async def collect_raw_content(content: ContentData):
    """Collect raw text for summarization training"""
    text_id = content_collector.collect_raw_text(
        text=content.raw_text,
        source_url=content.source_url,
        content_type=content.content_type,
        language=content.language,
        metadata={"title": content.title}
    )
    return {"status": "collected", "text_id": text_id}


@router.post("/content/add-summary")
async def add_content_summary(summary: SummaryData):
    """Add human-written summary for a text"""
    result = content_collector.add_human_summary(
        text_id=summary.text_id,
        summary=summary.summary,
        writer_id=summary.writer_id,
        summary_type=summary.summary_type,
        language=summary.language
    )
    return {"status": "added", "summary_id": result.get("summary_id")}


@router.post("/content/add-highlights")
async def add_content_highlights(
    text_id: str,
    highlights: List[str],
    writer_id: str,
    language: str = "en"
):
    """Add bullet-point highlights"""
    result = content_collector.add_highlights(text_id, highlights, writer_id, language)
    return {"status": "added", "result": result}


@router.get("/content/stats")
async def get_content_stats():
    """Get content collection statistics"""
    return content_collector.get_stats()


@router.post("/content/export")
async def export_content_training_data():
    """Export parallel corpus for summarization training"""
    output_file = content_collector.export_training_data()
    return {"status": "exported", "file": output_file}


@router.post("/content/export-highlights")
async def export_highlight_data():
    """Export highlight extraction training data"""
    output_file = content_collector.export_highlight_data()
    return {"status": "exported", "file": output_file}


# ============================================================================
# FORM FIELD CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post("/forms/collect")
async def collect_form(form: FormFieldData):
    """Collect a form for field classification"""
    form_id = form_collector.collect_form(
        form_url=form.form_url,
        html_content=form.html_content,
        metadata={
            "form_name": form.form_name,
            "department": form.department,
        }
    )
    return {"status": "collected", "form_id": form_id}


@router.post("/forms/correct-field")
async def correct_field_label(correction: FieldCorrectionData):
    """Log operator correction for a field label"""
    from ai.training import FieldSemanticTag
    
    try:
        corrected_enum = FieldSemanticTag(correction.corrected_tag)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid tag: {correction.corrected_tag}")
    
    result = form_collector.log_operator_correction(
        field_id=correction.field_id,
        original_tag=correction.original_tag,
        corrected_tag=corrected_enum,
        operator_id=correction.operator_id,
        reason=correction.reason
    )
    return {"status": "logged", "result": result}


@router.get("/forms/stats")
async def get_form_stats():
    """Get form collection statistics"""
    return form_collector.get_stats()


@router.post("/forms/export")
async def export_form_training_data():
    """Export field classification training data"""
    output_file = form_collector.export_training_data()
    return {"status": "exported", "file": output_file}


# ============================================================================
# DOCUMENT VALIDATION ENDPOINTS
# ============================================================================

@router.post("/documents/collect")
async def collect_document(
    image_path: str,
    document_type: str,
    is_sample: bool = False
):
    """Collect a document image"""
    from ai.training import DocumentType
    
    try:
        doc_type = DocumentType(document_type)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid document type: {document_type}")
    
    doc_id = document_collector.collect_document(image_path, doc_type, is_sample)
    return {"status": "collected", "doc_id": doc_id}


@router.post("/documents/add-quality-label")
async def add_document_quality(
    doc_id: str,
    quality: str,
    is_acceptable: bool = True,
    labeler_id: str = None
):
    """Add quality label for document"""
    from ai.training import QualityIssue
    
    try:
        quality_enum = QualityIssue(quality)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid quality: {quality}")
    
    result = document_collector.add_quality_label(
        doc_id=doc_id,
        quality=quality_enum,
        is_acceptable=is_acceptable,
        labeler_id=labeler_id
    )
    return {"status": "labeled", "result": result}


@router.get("/documents/stats")
async def get_document_stats():
    """Get document collection statistics"""
    return document_collector.get_stats()


@router.post("/documents/export-ocr")
async def export_ocr_training_data():
    """Export OCR training data"""
    output_file = document_collector.export_ocr_training_data()
    return {"status": "exported", "file": output_file}


@router.post("/documents/export-quality")
async def export_quality_training_data():
    """Export quality assessment training data"""
    output_file = document_collector.export_quality_training_data()
    return {"status": "exported", "file": output_file}


# ============================================================================
# GLOBAL STATS & DATASHEET
# ============================================================================

@router.get("/stats")
async def get_all_stats():
    """Get statistics for all collectors"""
    return {
        "job_matching": job_collector.get_stats(),
        "intent": intent_collector.get_stats(),
        "content": content_collector.get_stats(),
        "forms": form_collector.get_stats(),
        "documents": document_collector.get_stats(),
        "timestamp": datetime.now().isoformat(),
    }


@router.post("/generate-datasheet")
async def generate_dataset_datasheet(
    dataset_name: str,
    description: str,
    created_by: str
):
    """Generate dataset documentation (datasheet)"""
    # Gather info from all collectors
    job_stats = job_collector.get_stats()
    intent_stats = intent_collector.get_stats()
    
    datasheet = DatasheetGenerator.generate(
        name=dataset_name,
        description=description,
        data_sources=[
            "Government job portals",
            "Scheme PDFs",
            "WhatsApp conversations",
            "User interactions",
        ],
        collection_method="Automated scraping + manual annotation",
        annotation_guidelines="See /intent/guidelines endpoint",
        class_definitions={
            "job_matching": "Relevance scores from user interactions",
            "intent": "User intent categories",
            "content": "Raw text to summary pairs",
            "forms": "Field semantic types",
            "documents": "Document quality and OCR",
        },
        total_samples=sum([
            job_stats.get("jobs_collected", 0),
            intent_stats.get("messages_collected", 0),
        ]),
        class_distribution={},
        known_biases=[
            "May over-represent certain states",
            "Hindi/English mixed language bias",
        ],
        privacy_notes="All PII anonymized, DPDP compliant",
        created_by=created_by,
    )
    
    # Save datasheet
    output_path = "data/training/datasheet.json"
    DatasheetGenerator.save(datasheet, output_path)
    
    return {"status": "generated", "file": output_path, "datasheet": datasheet}
