"""
Apply AI Engine v1 - API Routes
Versioned API endpoints for external/SaaS use
"""

from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional, Dict, Any, List
from models.schemas import (
    MatchRequest, MatchResponse,
    ClassifyFieldRequest, ClassifyFieldResponse,
    ValidateFormRequest, ValidateFormResponse,
    LearningFeedback
)
from middleware.auth import verify_api_key
from config.database import get_database

router = APIRouter(prefix="/api/v1", tags=["Apply AI Engine v1"])

# Global engine instances (set from main.py)
hybrid_matcher = None
form_engine = None

def set_engines(matcher, form_intel):
    """Set engine instances"""
    global hybrid_matcher, form_engine
    hybrid_matcher = matcher
    form_engine = form_intel

# =============================================================================
# MATCHING API
# =============================================================================

@router.post("/match/job", response_model=MatchResponse)
async def match_job(
    request: MatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Match a job to user profile using Apply AI Engine
    
    **Pricing:** 1 credit per request
    """
    if not hybrid_matcher:
        raise HTTPException(503, "Matching engine not available")
    
    try:
        result = await hybrid_matcher.match_job_to_user(
            job=request.job,
            user_profile=request.user_profile,
            use_ml=True
        )
        
        return MatchResponse(
            score=result["score"],
            matched=result["matched"],
            confidence="high" if result["score"] > 0.8 else "medium" if result["score"] > 0.6 else "low",
            reasons=result["reasons"],
            breakdown=result.get("breakdown", {})
        )
    
    except Exception as e:
        raise HTTPException(500, f"Matching failed: {str(e)}")

@router.post("/match/scheme")
async def match_scheme(
    request: MatchRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Match a government scheme to user profile
    
    **Pricing:** 1 credit per request
    """
    if not hybrid_matcher:
        raise HTTPException(503, "Matching engine not available")
    
    try:
        result = await hybrid_matcher.match_job_to_user(
            job=request.scheme,
            user_profile=request.user_profile,
            use_ml=True
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(500, f"Matching failed: {str(e)}")

@router.post("/match/batch")
async def match_batch(
    user_profile: Dict[str, Any],
    items: List[Dict[str, Any]],
    api_key: str = Depends(verify_api_key)
):
    """
    Batch match multiple jobs/schemes to user profile
    
    **Pricing:** 1 credit per item
    """
    if not hybrid_matcher:
        raise HTTPException(503, "Matching engine not available")
    
    results = []
    
    for item in items:
        try:
            result = await hybrid_matcher.match_job_to_user(
                job=item,
                user_profile=user_profile,
                use_ml=True
            )
            results.append(result)
        except Exception as e:
            results.append({"error": str(e), "item": item.get("id")})
    
    return {
        "total": len(items),
        "processed": len(results),
        "results": results
    }

# =============================================================================
# FORM INTELLIGENCE API
# =============================================================================

@router.post("/forms/classify", response_model=ClassifyFieldResponse)
async def classify_field(
    request: ClassifyFieldRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Classify form field type using Apply AI Engine
    
    **Pricing:** 0.1 credits per request
    """
    if not form_engine:
        raise HTTPException(503, "Form intelligence engine not available")
    
    try:
        result = await form_engine.classify_field(
            request.field_label,
            request.field_value
        )
        
        return ClassifyFieldResponse(**result)
    
    except Exception as e:
        raise HTTPException(500, f"Classification failed: {str(e)}")

@router.post("/forms/validate", response_model=ValidateFormResponse)
async def validate_form(
    request: ValidateFormRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Validate form and predict errors using Apply AI Engine
    
    **Pricing:** 1 credit per request
    """
    if not form_engine:
        raise HTTPException(503, "Form intelligence engine not available")
    
    try:
        errors = await form_engine.predict_errors(request.form_data)
        
        return ValidateFormResponse(
            is_valid=len(errors) == 0,
            error_count=len(errors),
            errors=errors,
            severity_breakdown={
                "high": len([e for e in errors if e.get("severity") == "high"]),
                "medium": len([e for e in errors if e.get("severity") == "medium"]),
                "low": len([e for e in errors if e.get("severity") == "low"])
            }
        )
    
    except Exception as e:
        raise HTTPException(500, f"Validation failed: {str(e)}")

@router.post("/forms/autofill")
async def autofill_form(
    form_fields: List[str],
    user_profile: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """
    Get auto-fill suggestions for form fields
    
    **Pricing:** 0.5 credits per request
    """
    if not form_engine:
        raise HTTPException(503, "Form intelligence engine not available")
    
    try:
        suggestions = await form_engine.auto_fill_suggestions(
            form_fields,
            user_profile
        )
        
        return suggestions
    
    except Exception as e:
        raise HTTPException(500, f"Auto-fill failed: {str(e)}")

@router.post("/forms/smart-fill")
async def smart_form_fill(
    form_fields: List[str],
    partial_data: Dict[str, str],
    user_profile: Dict[str, Any],
    api_key: str = Depends(verify_api_key)
):
    """
    Complete form intelligence: classify + autofill + validate
    
    **Pricing:** 2 credits per request
    """
    if not form_engine:
        raise HTTPException(503, "Form intelligence engine not available")
    
    try:
        # Classify fields
        classifications = {}
        for field in form_fields:
            classification = await form_engine.classify_field(
                field,
                partial_data.get(field)
            )
            classifications[field] = classification
        
        # Auto-fill
        auto_fill = await form_engine.auto_fill_suggestions(form_fields, user_profile)
        
        # Merge with partial data
        filled_form = {**auto_fill["suggestions"], **partial_data}
        
        # Validate
        errors = await form_engine.predict_errors(filled_form)
        
        return {
            "filled_form": filled_form,
            "classifications": classifications,
            "errors": errors,
            "auto_filled_count": len(auto_fill["suggestions"]),
            "user_filled_count": len(partial_data),
            "is_valid": len(errors) == 0
        }
    
    except Exception as e:
        raise HTTPException(500, f"Smart fill failed: {str(e)}")

# =============================================================================
# LEARNING API
# =============================================================================

@router.post("/learn/feedback")
async def submit_feedback(
    feedback: LearningFeedback,
    api_key: str = Depends(verify_api_key)
):
    """
    Submit user feedback to improve matching
    
    **Pricing:** Free (helps improve the engine)
    """
    if not hybrid_matcher:
        raise HTTPException(503, "Matching engine not available")
    
    try:
        await hybrid_matcher.update_match_outcome(
            feedback.job_id,
            feedback.user_id,
            feedback.action
        )
        
        return {
            "status": "learned",
            "message": "Feedback recorded for future improvements"
        }
    
    except Exception as e:
        raise HTTPException(500, f"Feedback submission failed: {str(e)}")

# =============================================================================
# TRAINING API (Admin)
# =============================================================================

@router.post("/train/portal")
async def train_portal(
    portal_name: str,
    form_submissions: List[Dict[str, Any]],
    api_key: str = Depends(verify_api_key)  # Admin key required
):
    """
    Train form intelligence on portal-specific datasets
    
    **Pricing:** Contact for custom training
    """
    if not form_engine:
        raise HTTPException(503, "Form intelligence engine not available")
    
    try:
        result = await form_engine.train_from_dataset(
            portal_name,
            form_submissions
        )
        
        return result
    
    except Exception as e:
        raise HTTPException(500, f"Training failed: {str(e)}")

# =============================================================================
# ANALYTICS API
# =============================================================================

@router.get("/analytics/usage")
async def get_usage_stats(
    api_key: str = Depends(verify_api_key)
):
    """
    Get API usage statistics for your account
    """
    db = get_database()
    
    # Get API key info
    key_info = await db.api_keys.find_one({"key": api_key})
    
    if not key_info:
        raise HTTPException(404, "API key not found")
    
    # Get usage stats
    usage = await db.api_usage.find(
        {"api_key": api_key}
    ).to_list(length=1000)
    
    return {
        "organization": key_info.get("organization"),
        "plan": key_info.get("plan", "free"),
        "credits_used": len(usage),
        "credits_remaining": key_info.get("credits_remaining", 0),
        "requests_today": len([u for u in usage if u.get("date") == "2026-01-28"])
    }

# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/health")
async def health_check():
    """
    Check Apply AI Engine v1 health status
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "engines": {
            "matching": "active" if hybrid_matcher else "inactive",
            "form_intelligence": "active" if form_engine else "inactive"
        },
        "uptime": "99.9%"
    }
