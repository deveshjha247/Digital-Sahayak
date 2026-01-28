"""
Job Routes
Job listing and management endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from models.schemas import JobCreate, JobUpdate, JobResponse
from middleware.auth import get_current_user, get_current_admin
from config.database import get_database
from utils.helpers import slugify, extract_keywords, get_current_timestamp
import uuid

router = APIRouter(prefix="/jobs", tags=["Jobs"])

@router.get("")
async def get_jobs(
    category: Optional[str] = None,
    location: Optional[str] = None,
    education: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Get job listings with filters"""
    db = get_database()
    
    query = {}
    if category:
        query["category"] = category
    if location:
        query["location"] = {"$regex": location, "$options": "i"}
    if education:
        query["education_required"] = education
    
    jobs = await db.jobs.find(query).skip(skip).limit(limit).to_list(length=limit)
    total = await db.jobs.count_documents(query)
    
    return {
        "jobs": jobs,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }

@router.get("/search")
async def search_jobs(q: str, skip: int = 0, limit: int = 20):
    """Search jobs by keyword"""
    db = get_database()
    
    query = {
        "$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"company": {"$regex": q, "$options": "i"}}
        ]
    }
    
    jobs = await db.jobs.find(query).skip(skip).limit(limit).to_list(length=limit)
    total = await db.jobs.count_documents(query)
    
    return {
        "jobs": jobs,
        "total": total,
        "query": q
    }

@router.get("/recommendations")
async def get_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """Get personalized job recommendations"""
    db = get_database()
    
    # Get user preferences
    education = current_user.get("education")
    age = current_user.get("age")
    state = current_user.get("state")
    categories = current_user.get("preferred_categories", [])
    
    # Build query
    query = {}
    if education:
        query["education_required"] = {"$in": [education, "Any"]}
    if age:
        query["$or"] = [
            {"min_age": {"$lte": age}, "max_age": {"$gte": age}},
            {"min_age": None, "max_age": None}
        ]
    if state:
        query["location"] = {"$regex": state, "$options": "i"}
    if categories:
        query["category"] = {"$in": categories}
    
    jobs = await db.jobs.find(query).limit(10).to_list(length=10)
    
    return {
        "jobs": jobs,
        "count": len(jobs)
    }

@router.get("/{job_id}")
async def get_job(job_id: str):
    """Get single job details"""
    db = get_database()
    
    job = await db.jobs.find_one({"id": job_id})
    if not job:
        raise HTTPException(404, "Job not found")
    
    return job

@router.post("")
async def create_job(
    job: JobCreate,
    current_user: dict = Depends(get_current_admin)
):
    """Create new job (Admin only)"""
    db = get_database()
    
    job_doc = {
        "id": str(uuid.uuid4()),
        **job.dict(),
        "slug": slugify(job.title),
        "keywords": extract_keywords(job.description),
        "created_at": get_current_timestamp(),
        "created_by": current_user["id"]
    }
    
    await db.jobs.insert_one(job_doc)
    
    return job_doc

@router.put("/{job_id}")
async def update_job(
    job_id: str,
    updates: JobUpdate,
    current_user: dict = Depends(get_current_admin)
):
    """Update job (Admin only)"""
    db = get_database()
    
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
    
    if "title" in update_data:
        update_data["slug"] = slugify(update_data["title"])
    if "description" in update_data:
        update_data["keywords"] = extract_keywords(update_data["description"])
    
    result = await db.jobs.update_one(
        {"id": job_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Job not found")
    
    updated_job = await db.jobs.find_one({"id": job_id})
    return updated_job

@router.delete("/{job_id}")
async def delete_job(
    job_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Delete job (Admin only)"""
    db = get_database()
    
    result = await db.jobs.delete_one({"id": job_id})
    
    if result.deleted_count == 0:
        raise HTTPException(404, "Job not found")
    
    return {"message": "Job deleted successfully"}
