"""
AI Routes - FastAPI endpoints for AI modules
Exposes all AI functionality through REST API
"""

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from typing import List, Dict, Optional, Any
import logging
import json

from backend.ai import (
    JobRecommender,
    FieldClassifier,
    ContentSummarizer,
    IntentClassifier,
    DocumentValidator,
    IntentType,
    ValidationStatus,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v2/ai", tags=["AI"])

# Initialize AI modules (singleton pattern)
job_recommender = JobRecommender()
field_classifier = FieldClassifier()
content_summarizer = ContentSummarizer()
intent_classifier = IntentClassifier()
document_validator = DocumentValidator()


# ============================================================================
# JOB RECOMMENDATION ENDPOINTS
# ============================================================================

@router.post("/recommendations/jobs")
async def get_job_recommendations(
    user_profile: Dict[str, Any],
    jobs: List[Dict[str, Any]],
    top_k: Optional[int] = 10,
    language: Optional[str] = "en"
):
    """
    Get personalized job recommendations for a user
    
    Request body:
    {
        "user_profile": {
            "education": "B.Tech",
            "age": 25,
            "state": "Bihar",
            "category": "Railway",
            "preferred_salary": 50000
        },
        "jobs": [
            {"id": 1, "title": "...", "salary": 60000, ...},
            ...
        ],
        "top_k": 10,
        "language": "en"
    }
    """
    try:
        recommendations = job_recommender.get_recommendations(
            user_profile=user_profile,
            jobs=jobs,
            top_k=top_k
        )
        
        # Format response
        response = {
            "success": True,
            "count": len(recommendations),
            "recommendations": recommendations,
            "metadata": {
                "language": language,
                "top_k_requested": top_k,
            }
        }
        
        return response
    
    except Exception as e:
        logger.error(f"Error in job recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/recommendations/schemes")
async def get_scheme_recommendations(
    user_profile: Dict[str, Any],
    schemes: List[Dict[str, Any]],
    top_k: Optional[int] = 5,
):
    """
    Get personalized scheme recommendations for a user
    Similar to job recommendations but for govt schemes
    """
    try:
        # Use same recommender logic
        recommendations = job_recommender.get_recommendations(
            user_profile=user_profile,
            jobs=schemes,  # schemes follow same structure
            top_k=top_k
        )
        
        return {
            "success": True,
            "count": len(recommendations),
            "recommendations": recommendations,
        }
    
    except Exception as e:
        logger.error(f"Error in scheme recommendations: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recommendations/explain/{job_id}")
async def explain_job_score(
    job_id: str,
    user_profile: Dict[str, Any],
    job: Dict[str, Any],
    language: Optional[str] = "en"
):
    """
    Get detailed explanation of how a job was scored
    """
    try:
        explanation = job_recommender.explain_score(
            user_profile=user_profile,
            job=job,
            language=language
        )
        
        return {
            "success": True,
            "job_id": job_id,
            "explanation": explanation,
        }
    
    except Exception as e:
        logger.error(f"Error explaining score: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FORM FIELD CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post("/classify/field")
async def classify_form_field(
    field_label: str,
    field_value: Optional[str] = None,
):
    """
    Classify a single form field
    
    Request body:
    {
        "field_label": "आधार संख्या",
        "field_value": "123456789012"
    }
    
    Response:
    {
        "field_label": "आधार संख्या",
        "field_type": "aadhar",
        "confidence": 0.98,
        "value": "123456789012",
        "formatted_value": "1234 5678 9012",
        "valid": true
    }
    """
    try:
        field_type, confidence = field_classifier.classify_field(field_label)
        
        response = {
            "success": True,
            "field_label": field_label,
            "field_type": field_type.value if field_type else None,
            "confidence": round(confidence, 3),
        }
        
        if field_value:
            formatted_value = field_classifier.format_field_value(field_type, field_value)
            response["value"] = field_value
            response["formatted_value"] = formatted_value
            
            # Validate
            is_valid = field_classifier.validate_field_value(field_type, field_value)
            response["valid"] = is_valid
        
        return response
    
    except Exception as e:
        logger.error(f"Error classifying field: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/classify/form")
async def classify_form_fields(
    fields: Dict[str, Any],
):
    """
    Classify all fields in a form
    
    Request body:
    {
        "fields": {
            "आधार संख्या": "123456789012",
            "email": "user@example.com",
            "phone": "9876543210"
        }
    }
    """
    try:
        classified = field_classifier.classify_form_fields(fields)
        
        return {
            "success": True,
            "original_fields": fields,
            "classified_fields": classified,
            "total_fields": len(fields),
        }
    
    except Exception as e:
        logger.error(f"Error classifying form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/map/user-to-form")
async def map_user_profile_to_form(
    user_profile: Dict[str, Any],
    form_fields: List[str],
):
    """
    Map user profile data to form fields automatically
    
    Request body:
    {
        "user_profile": {
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "9876543210",
            "aadhar": "123456789012"
        },
        "form_fields": ["नाम", "email", "phone", "आधार संख्या"]
    }
    """
    try:
        mapping = field_classifier.map_user_to_fields(user_profile, form_fields)
        
        return {
            "success": True,
            "mapped_fields": mapping,
            "user_profile_keys": list(user_profile.keys()),
            "form_fields_count": len(form_fields),
        }
    
    except Exception as e:
        logger.error(f"Error mapping user profile: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CONTENT SUMMARIZATION ENDPOINTS
# ============================================================================

@router.post("/summarize/job")
async def summarize_job_description(
    job: Dict[str, Any],
    language: Optional[str] = "en",
    style: Optional[str] = "professional"
):
    """
    Summarize and rewrite job description
    
    Request body:
    {
        "job": {
            "title": "Senior Engineer",
            "description": "Long description..."
        },
        "language": "en",
        "style": "professional"
    }
    """
    try:
        result = content_summarizer.process_job_description(job)
        
        if language == "hi":
            summary = result["summary_hindi"]
        else:
            summary = result["summary_english"]
        
        if style == "casual":
            rewritten = result["rewritten_casual"]
        elif style == "concise":
            rewritten = result["rewritten_concise"]
        else:
            rewritten = result["rewritten_professional"]
        
        return {
            "success": True,
            "title": job.get("title", ""),
            "summary": summary,
            "rewritten": rewritten,
            "key_info": result["key_info"],
            "bullet_points": result["bullet_points"][:3],
        }
    
    except Exception as e:
        logger.error(f"Error summarizing job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/summarize/text")
async def summarize_text(
    text: str,
    max_length: Optional[int] = 150,
):
    """
    Generate concise summary of any text
    """
    try:
        summary = content_summarizer.generate_concise_summary(text, max_length)
        
        return {
            "success": True,
            "original_length": len(text),
            "summary_length": len(summary),
            "summary": summary,
        }
    
    except Exception as e:
        logger.error(f"Error summarizing text: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# INTENT CLASSIFICATION ENDPOINTS
# ============================================================================

@router.post("/intent/classify")
async def classify_intent(
    message: str,
):
    """
    Classify WhatsApp message intent
    
    Request body:
    {
        "message": "मुझे नौकरी खोजनी है"
    }
    
    Response:
    {
        "intent": "job_search",
        "confidence": 0.95,
        "suggested_response": "I can help you find jobs..."
    }
    """
    try:
        intent, confidence, details = intent_classifier.classify(message)
        
        response = {
            "success": True,
            "message": message,
            "intent": intent.value,
            "confidence": round(confidence, 3),
            "suggested_response": intent_classifier.get_suggested_response(intent),
            "runner_ups": details.get("runner_ups", []),
        }
        
        # Extract entities (location, job type, etc.)
        entities = intent_classifier.extract_entities(message)
        if entities:
            response["extracted_entities"] = entities
        
        return response
    
    except Exception as e:
        logger.error(f"Error classifying intent: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/intent/classify-batch")
async def classify_intents_batch(
    messages: List[str],
):
    """
    Classify multiple messages
    """
    try:
        results = intent_classifier.classify_batch(messages)
        
        classifications = []
        for intent, confidence, details in results:
            classifications.append({
                "message": details.get("original_message", ""),
                "intent": intent.value,
                "confidence": round(confidence, 3),
            })
        
        return {
            "success": True,
            "total_messages": len(messages),
            "classifications": classifications,
        }
    
    except Exception as e:
        logger.error(f"Error classifying batch intents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DOCUMENT VALIDATION ENDPOINTS
# ============================================================================

@router.post("/validate/field")
async def validate_field(
    field_type: str,
    value: str,
):
    """
    Validate a single field value
    
    Request body:
    {
        "field_type": "aadhar",
        "value": "123456789012"
    }
    """
    try:
        is_valid, formatted_value, error = document_validator.validate_field(field_type, value)
        
        return {
            "success": True,
            "field_type": field_type,
            "original_value": value,
            "formatted_value": formatted_value,
            "valid": is_valid,
            "error": error,
        }
    
    except Exception as e:
        logger.error(f"Error validating field: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/form")
async def validate_form(
    fields: Dict[str, Any],
):
    """
    Validate all fields in a form
    
    Request body:
    {
        "fields": {
            "aadhar": "123456789012",
            "pan": "ABCDE1234F",
            "email": "user@example.com"
        }
    }
    """
    try:
        validation_result = document_validator.validate_form_fields(fields)
        
        return {
            "success": True,
            "is_valid": validation_result["is_valid"],
            "fields": validation_result["fields"],
            "summary": validation_result["summary"],
            "errors": validation_result.get("errors", []),
        }
    
    except Exception as e:
        logger.error(f"Error validating form: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/validate/document")
async def validate_document(
    ocr_text: str,
    fields: Optional[Dict[str, Any]] = None,
    document_type: Optional[str] = None,
):
    """
    Validate a complete document
    
    Request body:
    {
        "ocr_text": "Extracted text from document...",
        "fields": {"aadhar": "123456789012", ...},
        "document_type": "aadhar"
    }
    """
    try:
        document_data = {
            "ocr_text": ocr_text,
            "fields": fields or {},
            "document_type": document_type,
        }
        
        validation_result = document_validator.validate_document(document_data)
        
        return {
            "success": True,
            "document_type": validation_result["document_type"],
            "overall_status": validation_result["overall_status"],
            "quality_score": validation_result["quality_score"],
            "fields_validation": validation_result.get("fields_validation", {}),
            "issues": validation_result.get("issues", []),
        }
    
    except Exception as e:
        logger.error(f"Error validating document: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def ai_health_check():
    """Check AI module health"""
    return {
        "status": "healthy",
        "modules": {
            "job_recommender": "ready",
            "field_classifier": "ready",
            "content_summarizer": "ready",
            "intent_classifier": "ready",
            "document_validator": "ready",
        },
        "version": "1.0.0",
    }


# ============================================================================
# BATCH OPERATIONS
# ============================================================================

@router.post("/batch/process-jobs")
async def batch_process_jobs(
    jobs: List[Dict[str, Any]],
    operations: List[str],  # ["summarize", "classify", "validate"]
):
    """
    Process multiple jobs with various AI operations
    
    Request body:
    {
        "jobs": [...],
        "operations": ["summarize", "classify"]
    }
    """
    try:
        results = []
        
        for job in jobs:
            job_result = {"job_id": job.get("id"), "operations": {}}
            
            if "summarize" in operations:
                job_result["operations"]["summary"] = content_summarizer.process_job_description(job)
            
            results.append(job_result)
        
        return {
            "success": True,
            "total_jobs": len(jobs),
            "operations_performed": operations,
            "results": results,
        }
    
    except Exception as e:
        logger.error(f"Error in batch processing: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
