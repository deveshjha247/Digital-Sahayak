"""
Apply AI Engine - Pydantic Models for v1 API
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

# =============================================================================
# MATCHING MODELS
# =============================================================================

class MatchRequest(BaseModel):
    """Job/Scheme matching request"""
    user_profile: Dict[str, Any] = Field(..., description="User profile data")
    job: Optional[Dict[str, Any]] = Field(None, description="Job data")
    scheme: Optional[Dict[str, Any]] = Field(None, description="Scheme data")

class MatchResponse(BaseModel):
    """Matching response"""
    score: float = Field(..., ge=0.0, le=1.0, description="Match score")
    matched: bool = Field(..., description="Whether match threshold met")
    confidence: str = Field(..., description="Confidence level: high/medium/low")
    reasons: Dict[str, str] = Field(..., description="Match reasons in Hindi/English")
    breakdown: Dict[str, float] = Field(default_factory=dict, description="Score breakdown")

# =============================================================================
# FORM INTELLIGENCE MODELS
# =============================================================================

class ClassifyFieldRequest(BaseModel):
    """Field classification request"""
    field_label: str = Field(..., description="Form field label")
    field_value: Optional[str] = Field(None, description="Field value if available")

class ClassifyFieldResponse(BaseModel):
    """Field classification response"""
    field_label: str
    classified_type: str = Field(..., description="Detected field type")
    confidence: float = Field(..., ge=0.0, le=1.0)
    suggestions: Dict[str, str] = Field(default_factory=dict)

class ValidateFormRequest(BaseModel):
    """Form validation request"""
    form_data: Dict[str, str] = Field(..., description="Form field values")

class ValidateFormResponse(BaseModel):
    """Form validation response"""
    is_valid: bool
    error_count: int
    errors: List[Dict[str, Any]]
    severity_breakdown: Dict[str, int]

# =============================================================================
# LEARNING MODELS
# =============================================================================

class LearningFeedback(BaseModel):
    """User feedback for learning"""
    user_id: str
    job_id: str
    action: str = Field(..., description="User action: applied/ignored/saved")
    match_score: Optional[float] = Field(None, ge=0.0, le=1.0)

# =============================================================================
# API KEY MODELS
# =============================================================================

class APIKeyRequest(BaseModel):
    """API key creation request"""
    email: str = Field(..., description="Email address")
    organization: str = Field(..., description="Organization name")
    plan: str = Field(default="free", description="Plan: free/startup/business/enterprise")

class APIKeyResponse(BaseModel):
    """API key response"""
    api_key: str
    organization: str
    plan: str
    credits: int
    expires_at: Optional[str] = None
