"""
=============================================================================
SERVER_ADMIN.PY - Admin & Content Management Endpoints
=============================================================================
Extracted from server.py to keep files under 50KB
Contains: Admin stats, Content drafts, Scraper management, Document endpoints

Memory Optimization:
- Garbage Collection after heavy operations
- Lazy loading of optional dependencies
- File logging for crash debugging
=============================================================================
"""

import gc
import uuid
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Depends, Body, Query, BackgroundTasks
from logging.handlers import RotatingFileHandler

# Setup logging
logger = logging.getLogger(__name__)
if not logger.handlers:
    log_handler = RotatingFileHandler(
        'logs/admin_routes.log',
        maxBytes=5*1024*1024,  # 5MB
        backupCount=3
    )
    log_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(log_handler)
    logger.setLevel(logging.INFO)


def setup_admin_routes(
    api_router: APIRouter,
    db,
    openai_client,
    get_admin_user,
    get_current_user,
    job_scraper,
    rewrite_content_with_ai,
    generate_slug,
    get_unique_slug
):
    """
    Setup all admin and content management routes.
    
    Args:
        api_router: FastAPI router to add routes to
        db: MongoDB database connection
        openai_client: OpenAI client for AI rewriting
        get_admin_user: Dependency for admin authentication
        get_current_user: Dependency for user authentication
        job_scraper: JobScraper instance
        rewrite_content_with_ai: AI rewriting function
        generate_slug: Slug generation function
        get_unique_slug: Unique slug generation function
    """
    
    # ===================== ADMIN STATS =====================
    
    @api_router.get("/admin/stats")
    async def get_admin_stats(admin: dict = Depends(get_admin_user)):
        total_users = await db.users.count_documents({})
        total_jobs = await db.jobs.count_documents({})
        total_yojana = await db.yojana.count_documents({})
        total_applications = await db.applications.count_documents({})
        paid_applications = await db.applications.count_documents({"payment_status": "paid"})
        
        # Revenue calculation
        payments = await db.payments.find({"status": "PAID"}, {"_id": 0, "amount": 1}).to_list(1000)
        total_revenue = sum(p.get("amount", 0) for p in payments)
        
        return {
            "total_users": total_users,
            "total_jobs": total_jobs,
            "total_yojana": total_yojana,
            "total_applications": total_applications,
            "paid_applications": paid_applications,
            "total_revenue": total_revenue
        }

    @api_router.get("/admin/applications")
    async def get_all_applications(
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        admin: dict = Depends(get_admin_user)
    ):
        query = {}
        if status:
            query["application_status"] = status
        
        total = await db.applications.count_documents(query)
        apps = await db.applications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        return {"total": total, "applications": apps}

    @api_router.put("/admin/applications/{app_id}/status")
    async def update_application_status(
        app_id: str,
        status: str = Body(..., embed=True),
        admin: dict = Depends(get_admin_user)
    ):
        result = await db.applications.update_one(
            {"id": app_id},
            {"$set": {"application_status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Application not found")
        return {"message": "Status updated"}

    @api_router.post("/admin/make-admin")
    async def make_admin(phone: str = Body(..., embed=True), admin: dict = Depends(get_admin_user)):
        result = await db.users.update_one({"phone": phone}, {"$set": {"is_admin": True}})
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"message": "User is now admin"}

    # ===================== SCRAPER ENDPOINTS =====================

    @api_router.post("/admin/scrape-jobs")
    async def trigger_job_scraping(
        background_tasks: BackgroundTasks, 
        admin: dict = Depends(get_admin_user),
        save_to_draft: bool = Query(True, description="Save to draft queue for review")
    ):
        """Trigger job scraping from configured sources - saves to draft queue for review"""
        
        async def scrape_and_save():
            try:
                jobs = await job_scraper.scrape_all()
                saved_count = 0
                draft_count = 0
                
                for job_data in jobs:
                    # Check if job already exists (by title + source_url)
                    existing = await db.jobs.find_one({
                        "title": job_data["title"],
                        "apply_link": job_data["apply_link"]
                    })
                    
                    existing_draft = await db.content_drafts.find_one({
                        "title": job_data["title"],
                        "source_url": job_data.get("apply_link")
                    })
                    
                    if not existing and not existing_draft:
                        if save_to_draft:
                            # Save to draft queue for review
                            draft_id = str(uuid.uuid4())
                            base_slug = generate_slug(job_data["title"], job_data.get("state", ""))
                            
                            draft_doc = {
                                "id": draft_id,
                                "slug": base_slug,
                                **job_data,
                                "source_url": job_data.get("apply_link", ""),
                                "content_type": "job",
                                "status": "pending",
                                "is_rewritten": False,
                                "created_at": datetime.now(timezone.utc).isoformat()
                            }
                            await db.content_drafts.insert_one(draft_doc)
                            draft_count += 1
                        else:
                            # Direct save (old behavior)
                            job_id = str(uuid.uuid4())
                            base_slug = generate_slug(job_data["title"], job_data.get("state", ""))
                            slug = await get_unique_slug(base_slug, "jobs")
                            
                            job_doc = {
                                "id": job_id,
                                "slug": slug,
                                **job_data,
                                "is_active": True,
                                "is_draft": False,
                                "created_at": datetime.now(timezone.utc).isoformat(),
                                "created_by": "scraper",
                                "views": 0,
                                "applications": 0
                            }
                            await db.jobs.insert_one(job_doc)
                            saved_count += 1
                
                # Garbage collection after heavy scraping
                gc.collect()
                logger.info(f"Scraper: {draft_count} drafts, {saved_count} direct saves")
                
                await db.scrape_logs.insert_one({
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "total_scraped": len(jobs),
                    "drafts_created": draft_count,
                    "direct_saved": saved_count,
                    "status": "success"
                })
                
            except Exception as e:
                logger.error(f"Scraping error: {e}")
                await db.scrape_logs.insert_one({
                    "id": str(uuid.uuid4()),
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "error": str(e),
                    "status": "failed"
                })
        
        background_tasks.add_task(scrape_and_save)
        return {"message": "Job scraping started - content will be saved to draft queue for review", "status": "processing"}

    @api_router.get("/admin/scrape-logs")
    async def get_scrape_logs(admin: dict = Depends(get_admin_user), limit: int = 10):
        """Get recent scrape logs"""
        logs = await db.scrape_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
        return {"logs": logs}

    # ===================== CONTENT DRAFTS =====================

    @api_router.get("/admin/content-drafts")
    async def get_content_drafts(
        admin: dict = Depends(get_admin_user),
        status: str = Query("pending"),
        content_type: str = Query(None),
        skip: int = 0,
        limit: int = 20
    ):
        """Get scraped content drafts awaiting review"""
        query = {"status": status}
        if content_type:
            query["content_type"] = content_type
        
        total = await db.content_drafts.count_documents(query)
        drafts = await db.content_drafts.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
        return {"total": total, "drafts": drafts}

    @api_router.get("/admin/content-drafts/{draft_id}")
    async def get_draft_detail(draft_id: str, admin: dict = Depends(get_admin_user)):
        """Get single draft for editing"""
        draft = await db.content_drafts.find_one({"id": draft_id}, {"_id": 0})
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        return draft

    @api_router.put("/admin/content-drafts/{draft_id}")
    async def update_draft(
        draft_id: str,
        update_data: Dict[str, Any] = Body(...),
        admin: dict = Depends(get_admin_user)
    ):
        """Update draft content (for manual editing/rewriting)"""
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        update_data["updated_by"] = admin["id"]
        
        result = await db.content_drafts.update_one(
            {"id": draft_id},
            {"$set": update_data}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Draft not found")
        return {"message": "Draft updated"}

    @api_router.post("/admin/content-drafts/{draft_id}/rewrite")
    async def ai_rewrite_draft(draft_id: str, admin: dict = Depends(get_admin_user)):
        """Use AI to rewrite draft content (Copyright Safe)"""
        draft = await db.content_drafts.find_one({"id": draft_id})
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        content_type = draft.get("content_type", "job")
        rewritten = await rewrite_content_with_ai(openai_client, draft, content_type)
        
        # Update draft with rewritten content
        await db.content_drafts.update_one(
            {"id": draft_id},
            {"$set": {
                **rewritten,
                "is_rewritten": True,
                "rewritten_at": datetime.now(timezone.utc).isoformat()
            }}
        )
        
        updated_draft = await db.content_drafts.find_one({"id": draft_id}, {"_id": 0})
        return {"message": "Content rewritten by AI", "draft": updated_draft}

    @api_router.post("/admin/content-drafts/{draft_id}/publish")
    async def publish_draft(draft_id: str, admin: dict = Depends(get_admin_user)):
        """Publish approved draft as live job/yojana"""
        draft = await db.content_drafts.find_one({"id": draft_id})
        if not draft:
            raise HTTPException(status_code=404, detail="Draft not found")
        
        content_type = draft.get("content_type", "job")
        item_id = str(uuid.uuid4())
        
        # Generate unique slug
        base_slug = draft.get("slug") or generate_slug(
            draft.get("title") or draft.get("name", ""),
            draft.get("state", "")
        )
        
        if content_type == "job":
            slug = await get_unique_slug(base_slug, "jobs")
            job_doc = {
                "id": item_id,
                "slug": slug,
                "title": draft.get("title", ""),
                "title_hi": draft.get("title_hi", ""),
                "organization": draft.get("organization", ""),
                "organization_hi": draft.get("organization_hi", ""),
                "description": draft.get("description", ""),
                "description_hi": draft.get("description_hi", ""),
                "meta_description": draft.get("meta_description", ""),
                "highlights": draft.get("highlights", []),
                "qualification": draft.get("qualification", ""),
                "qualification_hi": draft.get("qualification_hi", ""),
                "vacancies": draft.get("vacancies", 0),
                "salary": draft.get("salary", ""),
                "age_limit": draft.get("age_limit", ""),
                "last_date": draft.get("last_date", ""),
                "apply_link": draft.get("apply_link", ""),
                "source_url": draft.get("source_url", ""),
                "category": draft.get("category", "government"),
                "state": draft.get("state", "all"),
                "content_type": draft.get("content_type", "job"),
                "is_active": True,
                "is_draft": False,
                "is_rewritten": draft.get("is_rewritten", False),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": admin["id"],
                "views": 0,
                "applications": 0
            }
            await db.jobs.insert_one(job_doc)
        else:
            slug = await get_unique_slug(base_slug, "yojana")
            yojana_doc = {
                "id": item_id,
                "slug": slug,
                "name": draft.get("name") or draft.get("title", ""),
                "name_hi": draft.get("name_hi") or draft.get("title_hi", ""),
                "ministry": draft.get("ministry") or draft.get("organization", ""),
                "ministry_hi": draft.get("ministry_hi", ""),
                "description": draft.get("description", ""),
                "description_hi": draft.get("description_hi", ""),
                "meta_description": draft.get("meta_description", ""),
                "highlights": draft.get("highlights", []),
                "benefits": draft.get("benefits", ""),
                "benefits_hi": draft.get("benefits_hi", ""),
                "eligibility": draft.get("eligibility", ""),
                "eligibility_hi": draft.get("eligibility_hi", ""),
                "documents_required": draft.get("documents_required", []),
                "apply_link": draft.get("apply_link", ""),
                "source_url": draft.get("source_url", ""),
                "category": draft.get("category", "welfare"),
                "state": draft.get("state", "all"),
                "govt_fee": draft.get("govt_fee", 0),
                "service_fee": draft.get("service_fee", 20),
                "is_active": True,
                "is_draft": False,
                "is_rewritten": draft.get("is_rewritten", False),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": admin["id"],
                "views": 0,
                "applications": 0
            }
            await db.yojana.insert_one(yojana_doc)
        
        # Mark draft as published
        await db.content_drafts.update_one(
            {"id": draft_id},
            {"$set": {"status": "published", "published_id": item_id, "published_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"message": "Content published successfully", "id": item_id, "slug": slug}

    @api_router.delete("/admin/content-drafts/{draft_id}")
    async def delete_draft(draft_id: str, admin: dict = Depends(get_admin_user)):
        """Delete/reject a draft"""
        result = await db.content_drafts.delete_one({"id": draft_id})
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Draft not found")
        return {"message": "Draft deleted"}

    # ===================== DOCUMENT ENDPOINTS =====================

    @api_router.post("/documents/upload")
    async def upload_document(
        doc_type: str = Body(...),
        doc_name: str = Body(...),
        doc_url: str = Body(...),
        user: dict = Depends(get_current_user)
    ):
        doc = {
            "id": str(uuid.uuid4()),
            "type": doc_type,
            "name": doc_name,
            "url": doc_url,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.update_one(
            {"id": user["id"]},
            {"$push": {"documents": doc}}
        )
        return doc

    @api_router.get("/documents")
    async def get_documents(user: dict = Depends(get_current_user)):
        return {"documents": user.get("documents", [])}

    @api_router.delete("/documents/{doc_id}")
    async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
        await db.users.update_one(
            {"id": user["id"]},
            {"$pull": {"documents": {"id": doc_id}}}
        )
        return {"message": "Document deleted"}

    logger.info("Admin routes initialized")
    return True
