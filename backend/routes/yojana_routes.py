"""
Yojana (Schemes) Routes
Government scheme listing and management
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional
from models.schemas import YojanaCreate, YojanaUpdate, YojanaResponse
from middleware.auth import get_current_user, get_current_admin
from config.database import get_database
from utils.helpers import slugify, extract_keywords, get_current_timestamp
import uuid

router = APIRouter(prefix="/yojana", tags=["Yojana"])

@router.get("")
async def get_yojanas(
    category: Optional[str] = None,
    state: Optional[str] = None,
    education: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Get yojana listings with filters"""
    db = get_database()
    
    query = {}
    if category:
        query["category"] = category
    if state:
        query["applicable_states"] = {"$regex": state, "$options": "i"}
    if education:
        query["education_required"] = education
    
    yojanas = await db.yojana.find(query).skip(skip).limit(limit).to_list(length=limit)
    total = await db.yojana.count_documents(query)
    
    return {
        "yojanas": yojanas,
        "total": total,
        "page": skip // limit + 1,
        "pages": (total + limit - 1) // limit
    }

@router.get("/search")
async def search_yojanas(q: str, skip: int = 0, limit: int = 20):
    """Search yojanas by keyword"""
    db = get_database()
    
    query = {
        "$or": [
            {"title": {"$regex": q, "$options": "i"}},
            {"description": {"$regex": q, "$options": "i"}},
            {"ministry": {"$regex": q, "$options": "i"}}
        ]
    }
    
    yojanas = await db.yojana.find(query).skip(skip).limit(limit).to_list(length=limit)
    total = await db.yojana.count_documents(query)
    
    return {
        "yojanas": yojanas,
        "total": total,
        "query": q
    }

@router.get("/recommendations")
async def get_recommendations(
    current_user: dict = Depends(get_current_user)
):
    """Get personalized yojana recommendations"""
    db = get_database()
    
    # Get user profile
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
        query["$or"] = [
            {"applicable_states": {"$regex": state, "$options": "i"}},
            {"applicable_states": "All India"}
        ]
    if categories:
        query["category"] = {"$in": categories}
    
    yojanas = await db.yojana.find(query).limit(10).to_list(length=10)
    
    return {
        "yojanas": yojanas,
        "count": len(yojanas)
    }

@router.get("/{yojana_id}")
async def get_yojana(yojana_id: str):
    """Get single yojana details"""
    db = get_database()
    
    yojana = await db.yojana.find_one({"id": yojana_id})
    if not yojana:
        raise HTTPException(404, "Yojana not found")
    
    return yojana

@router.post("")
async def create_yojana(
    yojana: YojanaCreate,
    current_user: dict = Depends(get_current_admin)
):
    """Create new yojana (Admin only)"""
    db = get_database()
    
    yojana_doc = {
        "id": str(uuid.uuid4()),
        **yojana.dict(),
        "slug": slugify(yojana.title),
        "keywords": extract_keywords(yojana.description),
        "created_at": get_current_timestamp(),
        "created_by": current_user["id"]
    }
    
    await db.yojana.insert_one(yojana_doc)
    
    return yojana_doc

@router.put("/{yojana_id}")
async def update_yojana(
    yojana_id: str,
    updates: YojanaUpdate,
    current_user: dict = Depends(get_current_admin)
):
    """Update yojana (Admin only)"""
    db = get_database()
    
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
    
    if "title" in update_data:
        update_data["slug"] = slugify(update_data["title"])
    if "description" in update_data:
        update_data["keywords"] = extract_keywords(update_data["description"])
    
    result = await db.yojana.update_one(
        {"id": yojana_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Yojana not found")
    
    updated_yojana = await db.yojana.find_one({"id": yojana_id})
    return updated_yojana

@router.delete("/{yojana_id}")
async def delete_yojana(
    yojana_id: str,
    current_user: dict = Depends(get_current_admin)
):
    """Delete yojana (Admin only)"""
    db = get_database()
    
    result = await db.yojana.delete_one({"id": yojana_id})
    
    if result.deleted_count == 0:
        raise HTTPException(404, "Yojana not found")
    
    return {"message": "Yojana deleted successfully"}
