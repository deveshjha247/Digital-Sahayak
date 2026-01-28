"""
Application Routes
Job/Yojana application management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from models.schemas import ApplicationCreate, ApplicationUpdate
from middleware.auth import get_current_user, get_current_admin
from config.database import get_database
from utils.helpers import get_current_timestamp
import uuid

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("")
async def get_applications(
    status: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get user applications"""
    db = get_database()
    
    query = {"user_id": current_user["id"]}
    if status:
        query["status"] = status
    
    applications = await db.applications.find(query).to_list(length=100)
    
    return {
        "applications": applications,
        "count": len(applications)
    }

@router.get("/all")
async def get_all_applications(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    current_user: dict = Depends(get_current_admin)
):
    """Get all applications (Admin only)"""
    db = get_database()
    
    query = {}
    if status:
        query["status"] = status
    
    applications = await db.applications.find(query).skip(skip).limit(limit).to_list(length=limit)
    total = await db.applications.count_documents(query)
    
    return {
        "applications": applications,
        "total": total,
        "page": skip // limit + 1
    }

@router.get("/{application_id}")
async def get_application(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get single application"""
    db = get_database()
    
    application = await db.applications.find_one({"id": application_id})
    
    if not application:
        raise HTTPException(404, "Application not found")
    
    # Check ownership or admin
    if application["user_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(403, "Not authorized")
    
    return application

@router.post("")
async def create_application(
    application: ApplicationCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create new application"""
    db = get_database()
    
    # Check if already applied
    existing = await db.applications.find_one({
        "user_id": current_user["id"],
        "resource_id": application.resource_id,
        "resource_type": application.resource_type
    })
    
    if existing:
        raise HTTPException(400, "Already applied to this resource")
    
    # Verify resource exists
    collection = db.jobs if application.resource_type == "job" else db.yojana
    resource = await collection.find_one({"id": application.resource_id})
    
    if not resource:
        raise HTTPException(404, f"{application.resource_type.title()} not found")
    
    application_doc = {
        "id": str(uuid.uuid4()),
        "user_id": current_user["id"],
        "user_name": current_user["name"],
        "user_phone": current_user["phone"],
        **application.dict(),
        "status": "submitted",
        "created_at": get_current_timestamp(),
        "updated_at": get_current_timestamp()
    }
    
    await db.applications.insert_one(application_doc)
    
    return application_doc

@router.put("/{application_id}")
async def update_application(
    application_id: str,
    updates: ApplicationUpdate,
    current_user: dict = Depends(get_current_admin)
):
    """Update application status (Admin only)"""
    db = get_database()
    
    update_data = {k: v for k, v in updates.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = get_current_timestamp()
    
    result = await db.applications.update_one(
        {"id": application_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(404, "Application not found")
    
    updated_app = await db.applications.find_one({"id": application_id})
    return updated_app

@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete application"""
    db = get_database()
    
    application = await db.applications.find_one({"id": application_id})
    
    if not application:
        raise HTTPException(404, "Application not found")
    
    # Check ownership or admin
    if application["user_id"] != current_user["id"] and not current_user.get("is_admin"):
        raise HTTPException(403, "Not authorized")
    
    await db.applications.delete_one({"id": application_id})
    
    return {"message": "Application deleted successfully"}
