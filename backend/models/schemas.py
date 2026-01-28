"""
Pydantic Models for Data Validation
All request/response models organized here
"""

from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

# ==================== User Models ====================

class UserBase(BaseModel):
    name: str
    phone: str
    email: Optional[EmailStr] = None
    language: str = "hi"

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    language: Optional[str] = None
    education: Optional[str] = None
    age: Optional[int] = None
    state: Optional[str] = None
    preferred_categories: Optional[List[str]] = None

class UserResponse(UserBase):
    id: str
    is_admin: bool = False
    is_operator: bool = False
    education: Optional[str] = None
    age: Optional[int] = None
    state: Optional[str] = None
    preferred_categories: Optional[List[str]] = []

# ==================== Job Models ====================

class JobBase(BaseModel):
    title: str
    organization: str
    category: str
    description: str
    eligibility: str
    last_date: Optional[str] = None
    apply_link: Optional[str] = None
    state: Optional[str] = None
    education: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None

class JobCreate(JobBase):
    pass

class JobUpdate(BaseModel):
    title: Optional[str] = None
    organization: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    eligibility: Optional[str] = None
    last_date: Optional[str] = None
    apply_link: Optional[str] = None
    state: Optional[str] = None
    education: Optional[str] = None
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    slug: Optional[str] = None
    meta_description: Optional[str] = None

class JobResponse(JobBase):
    id: str
    slug: Optional[str] = None
    created_at: str

# ==================== Yojana Models ====================

class YojanaBase(BaseModel):
    title: str
    category: str
    description: str
    eligibility: str
    benefits: str
    how_to_apply: str
    state: Optional[str] = None

class YojanaCreate(YojanaBase):
    pass

class YojanaUpdate(BaseModel):
    title: Optional[str] = None
    category: Optional[str] = None
    description: Optional[str] = None
    eligibility: Optional[str] = None
    benefits: Optional[str] = None
    how_to_apply: Optional[str] = None
    state: Optional[str] = None

class YojanaResponse(YojanaBase):
    id: str
    slug: Optional[str] = None
    created_at: str

# ==================== Application Models ====================

class ApplicationCreate(BaseModel):
    job_id: Optional[str] = None
    yojana_id: Optional[str] = None
    documents: Optional[List[str]] = []

class ApplicationResponse(BaseModel):
    id: str
    user_id: str
    job_id: Optional[str] = None
    yojana_id: Optional[str] = None
    status: str
    payment_status: str
    created_at: str

# ==================== Payment Models ====================

class PaymentCreate(BaseModel):
    amount: float
    application_id: str
    user_details: Dict[str, Any]

class PaymentResponse(BaseModel):
    order_id: str
    payment_session_id: str
    amount: float
    status: str

# ==================== Content Draft Models ====================

class ContentDraft(BaseModel):
    title: str
    content_type: str = "job"
    source_url: Optional[str] = None
    raw_content: Dict[str, Any]
    status: str = "pending"
    slug: Optional[str] = None
    meta_description: Optional[str] = None
    is_rewritten: bool = False

# ==================== AI Learning Models ====================

class AILearnRequest(BaseModel):
    prompt: str
    other_ai_response: str
    ai_name: str = "External AI"
    use_web_search: bool = False

class AIGenerateRequest(BaseModel):
    prompt: str
    context: str = ""
    use_web_search: bool = False

class WebSearchRequest(BaseModel):
    query: str
    max_results: int = 3

class BatchCompareRequest(BaseModel):
    comparisons: List[Dict[str, Any]]

class JobMatchRequest(BaseModel):
    job_id: str
    external_suggestions: Optional[Dict[str, Any]] = None
    use_web_search: bool = False
