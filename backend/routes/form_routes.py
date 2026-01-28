"""
Form Intelligence Routes
ML-based field classification and error prediction for portal forms
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Any
from middleware.auth import get_current_user, get_current_admin
from config.database import get_database

router = APIRouter(prefix="/forms", tags=["Form Intelligence"])

# Global form intelligence engine (initialized in main.py)
form_engine = None

def set_form_engine(engine_instance):
    """Set form engine instance (called from main.py)"""
    global form_engine
    form_engine = engine_instance

@router.post("/classify-field")
async def classify_field(
    field_label: str,
    field_value: str = None,
    current_user: dict = Depends(get_current_user)
):
    """
    Classify form field type using ML
    """
    if not form_engine:
        raise HTTPException(503, "Form Intelligence Engine not available")
    
    result = await form_engine.classify_field(field_label, field_value)
    return result

@router.post("/predict-errors")
async def predict_errors(
    form_data: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """
    Predict potential errors in form submission
    """
    if not form_engine:
        raise HTTPException(503, "Form Intelligence Engine not available")
    
    errors = await form_engine.predict_errors(form_data)
    
    return {
        "has_errors": len(errors) > 0,
        "error_count": len(errors),
        "errors": errors,
        "severity_breakdown": {
            "high": len([e for e in errors if e.get("severity") == "high"]),
            "medium": len([e for e in errors if e.get("severity") == "medium"]),
            "low": len([e for e in errors if e.get("severity") == "low"])
        }
    }

@router.post("/auto-fill")
async def get_auto_fill_suggestions(
    form_fields: List[str],
    current_user: dict = Depends(get_current_user)
):
    """
    Get auto-fill suggestions based on user profile
    """
    if not form_engine:
        raise HTTPException(503, "Form Intelligence Engine not available")
    
    suggestions = await form_engine.auto_fill_suggestions(form_fields, current_user)
    
    return suggestions

@router.post("/train")
async def train_from_portal_data(
    portal_name: str,
    form_submissions: List[Dict[str, Any]],
    current_user: dict = Depends(get_current_admin)
):
    """
    Train field classification model from portal datasets (Admin only)
    """
    if not form_engine:
        raise HTTPException(503, "Form Intelligence Engine not available")
    
    if not form_submissions:
        raise HTTPException(400, "No training data provided")
    
    result = await form_engine.train_from_dataset(portal_name, form_submissions)
    
    return result

@router.get("/training-stats")
async def get_training_stats(
    portal_name: str = None,
    current_user: dict = Depends(get_current_admin)
):
    """
    Get training statistics (Admin only)
    """
    if not form_engine:
        raise HTTPException(503, "Form Intelligence Engine not available")
    
    stats = await form_engine.get_portal_training_stats(portal_name)
    
    return stats

@router.post("/validate-batch")
async def validate_form_batch(
    forms: List[Dict[str, str]],
    current_user: dict = Depends(get_current_user)
):
    """
    Validate multiple forms in batch
    """
    if not form_engine:
        raise HTTPException(503, "Form Intelligence Engine not available")
    
    results = []
    
    for idx, form_data in enumerate(forms):
        errors = await form_engine.predict_errors(form_data)
        results.append({
            "form_index": idx,
            "is_valid": len(errors) == 0,
            "errors": errors
        })
    
    total_valid = sum(1 for r in results if r["is_valid"])
    
    return {
        "total_forms": len(forms),
        "valid_forms": total_valid,
        "invalid_forms": len(forms) - total_valid,
        "results": results
    }

@router.post("/smart-form-fill")
async def smart_form_fill(
    form_fields: List[str],
    partial_data: Dict[str, str],
    current_user: dict = Depends(get_current_user)
):
    """
    Intelligent form filling with classification and auto-fill
    """
    if not form_engine:
        raise HTTPException(503, "Form Intelligence Engine not available")
    
    # Classify all fields
    classifications = {}
    for field in form_fields:
        classification = await form_engine.classify_field(
            field, 
            partial_data.get(field)
        )
        classifications[field] = classification
    
    # Get auto-fill suggestions
    auto_fill = await form_engine.auto_fill_suggestions(form_fields, current_user)
    
    # Merge with partial data (partial data takes priority)
    filled_form = {**auto_fill["suggestions"], **partial_data}
    
    # Predict errors on filled form
    errors = await form_engine.predict_errors(filled_form)
    
    return {
        "filled_form": filled_form,
        "classifications": classifications,
        "errors": errors,
        "auto_filled_count": len(auto_fill["suggestions"]),
        "user_filled_count": len(partial_data),
        "has_errors": len(errors) > 0
    }
