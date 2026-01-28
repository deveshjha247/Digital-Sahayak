"""
Advanced Scraper Routes
Web scraping with scheduling, error handling, and multiple portals
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from middleware.auth import get_current_admin
from config.database import get_database
from services.advanced_scraper import scrape_all_portals, AdvancedScraper, PORTAL_CONFIGS, get_scraper_status
from services.scheduler import get_scheduler
from utils.helpers import get_current_timestamp
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/scraper", tags=["Scraper"])

# ============================================================================
# Scheduler Management Endpoints
# ============================================================================

@router.post("/scheduler/start")
async def start_scheduler(current_user: dict = Depends(get_current_admin)):
    """
    Start automatic scraper scheduler
    Admin only
    """
    try:
        scheduler = get_scheduler()
        if scheduler.is_running:
            return {"message": "Scheduler already running"}
        
        await scheduler.start()
        
        jobs = scheduler.get_jobs()
        return {
            "status": "started",
            "message": "Scraper scheduler started",
            "scheduled_jobs": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
        raise HTTPException(500, f"Failed to start scheduler: {str(e)}")

@router.post("/scheduler/stop")
async def stop_scheduler(current_user: dict = Depends(get_current_admin)):
    """
    Stop automatic scraper scheduler
    Admin only
    """
    try:
        scheduler = get_scheduler()
        await scheduler.stop()
        
        return {
            "status": "stopped",
            "message": "Scraper scheduler stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping scheduler: {str(e)}")
        raise HTTPException(500, f"Failed to stop scheduler: {str(e)}")

@router.get("/scheduler/status")
async def get_scheduler_status(current_user: dict = Depends(get_current_admin)):
    """
    Get scheduler status and next run times
    Admin only
    """
    try:
        scheduler = get_scheduler()
        jobs = scheduler.get_jobs()
        
        db = get_database()
        scraper_status = await get_scraper_status(db)
        
        return {
            "scheduler_running": scheduler.is_running,
            "scheduled_jobs": jobs,
            "portal_status": scraper_status
        }
    except Exception as e:
        logger.error(f"Error getting scheduler status: {str(e)}")
        raise HTTPException(500, str(e))

@router.post("/scheduler/job/{job_id}/trigger")
async def trigger_scheduled_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_admin)
):
    """
    Manually trigger a scheduled scraper job
    Admin only
    """
    try:
        scheduler = get_scheduler()
        
        # Run in background
        background_tasks.add_task(scheduler.trigger_job, job_id)
        
        return {
            "status": "triggered",
            "message": f"Job {job_id} triggered in background",
            "job_id": job_id
        }
    except Exception as e:
        logger.error(f"Error triggering job: {str(e)}")
        raise HTTPException(500, str(e))

# ============================================================================
# Manual Scraping Endpoints
# ============================================================================

@router.post("/scrape-all")
async def scrape_all_portals_endpoint(
    background_tasks: BackgroundTasks,
    portal_names: list = None,
    current_user: dict = Depends(get_current_admin)
):
    """
    Manually trigger scraping of all or specific portals
    Admin only
    
    Example: /scraper/scrape-all?portal_names=SSC Official&portal_names=Railway Jobs
    """
    db = get_database()
    
    async def perform_scrape():
        try:
            results = await scrape_all_portals(portal_names)
            
            # Save results to database
            await db.scraper_reports.insert_one({
                "timestamp": get_current_timestamp(),
                "type": "manual",
                "triggered_by": current_user["id"],
                "results": results
            })
            
            logger.info(f"Scraping completed: {results}")
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            await db.scraper_reports.insert_one({
                "timestamp": get_current_timestamp(),
                "type": "manual",
                "triggered_by": current_user["id"],
                "status": "failed",
                "error": str(e)
            })
    
    background_tasks.add_task(perform_scrape)
    
    portals = portal_names or [c["name"] for c in PORTAL_CONFIGS if c["enabled"]]
    
    return {
        "status": "scraping_started",
        "message": "Scraping job started in background",
        "portals": portals,
        "timestamp": get_current_timestamp()
    }

@router.post("/scrape-portal")
async def scrape_single_portal(
    portal_name: str,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_admin)
):
    """
    Manually scrape a specific portal
    Admin only
    """
    db = get_database()
    
    # Find portal config
    portal_config = None
    for config in PORTAL_CONFIGS:
        if config["name"] == portal_name:
            portal_config = config
            break
    
    if not portal_config:
        raise HTTPException(404, f"Portal '{portal_name}' not found")
    
    async def perform_scrape():
        try:
            scraper = AdvancedScraper()
            jobs = await scraper.scrape_job_portal(portal_config)
            
            if jobs:
                await db.jobs.insert_many(jobs)
            
            await db.scraper_reports.insert_one({
                "timestamp": get_current_timestamp(),
                "type": "manual_single",
                "portal": portal_name,
                "triggered_by": current_user["id"],
                "jobs_found": len(jobs),
                "status": "success"
            })
            
            logger.info(f"Scraped {len(jobs)} jobs from {portal_name}")
        except Exception as e:
            logger.error(f"Error scraping {portal_name}: {str(e)}")
            await db.scraper_reports.insert_one({
                "timestamp": get_current_timestamp(),
                "type": "manual_single",
                "portal": portal_name,
                "triggered_by": current_user["id"],
                "status": "failed",
                "error": str(e)
            })
    
    background_tasks.add_task(perform_scrape)
    
    return {
        "status": "scraping_started",
        "portal": portal_name,
        "message": f"Scraping {portal_name} in background",
        "timestamp": get_current_timestamp()
    }

# ============================================================================
# Portal Management Endpoints
# ============================================================================

@router.get("/portals")
async def get_portals(current_user: dict = Depends(get_current_admin)):
    """
    Get list of available scraper portals and their configurations
    Admin only
    """
    return {
        "portals": [
            {
                "name": config["name"],
                "url": config["url"],
                "enabled": config["enabled"],
                "frequency_hours": config.get("frequency_hours", 6),
                "selectors": {k: v for k, v in config["selectors"].items() if k != "password"}
            }
            for config in PORTAL_CONFIGS
        ]
    }

@router.post("/portals/{portal_name}/enable")
async def enable_portal(
    portal_name: str,
    current_user: dict = Depends(get_current_admin)
):
    """
    Enable a portal for scraping
    Admin only
    """
    for config in PORTAL_CONFIGS:
        if config["name"] == portal_name:
            config["enabled"] = True
            db = get_database()
            await db.portal_settings.update_one(
                {"name": portal_name},
                {"$set": {"enabled": True, "updated_at": get_current_timestamp()}},
                upsert=True
            )
            return {"status": "enabled", "portal": portal_name}
    
    raise HTTPException(404, f"Portal '{portal_name}' not found")

@router.post("/portals/{portal_name}/disable")
async def disable_portal(
    portal_name: str,
    current_user: dict = Depends(get_current_admin)
):
    """
    Disable a portal from scraping
    Admin only
    """
    for config in PORTAL_CONFIGS:
        if config["name"] == portal_name:
            config["enabled"] = False
            db = get_database()
            await db.portal_settings.update_one(
                {"name": portal_name},
                {"$set": {"enabled": False, "updated_at": get_current_timestamp()}},
                upsert=True
            )
            return {"status": "disabled", "portal": portal_name}
    
    raise HTTPException(404, f"Portal '{portal_name}' not found")

# ============================================================================
# Reporting Endpoints
# ============================================================================

@router.get("/reports")
async def get_scraper_reports(
    limit: int = 20,
    current_user: dict = Depends(get_current_admin)
):
    """
    Get recent scraper reports and logs
    Admin only
    """
    db = get_database()
    
    reports = await db.scraper_reports.find(
        {},
        sort=[("timestamp", -1)],
        limit=limit
    ).to_list(limit)
    
    return {
        "reports": reports,
        "total": len(reports)
    }

@router.get("/status")
async def get_scraper_status_endpoint(current_user: dict = Depends(get_current_admin)):
    """
    Get detailed scraper status including portal statistics
    Admin only
    """
    db = get_database()
    
    try:
        scraper_status = await get_scraper_status(db)
        
        # Add scheduler info
        scheduler = get_scheduler()
        scraper_status["scheduler_running"] = scheduler.is_running
        scraper_status["scheduled_jobs"] = scheduler.get_jobs()
        
        return scraper_status
    except Exception as e:
        logger.error(f"Error getting status: {str(e)}")
        raise HTTPException(500, str(e))

@router.get("/stats/summary")
async def get_scraper_summary(current_user: dict = Depends(get_current_admin)):
    """
    Get summary statistics about scraping activity
    Admin only
    """
    db = get_database()
    
    try:
        # Count jobs by portal
        portal_stats = await db.jobs.aggregate([
            {"$match": {"source": "scraped"}},
            {"$group": {
                "_id": "$source_portal",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}}
        ]).to_list(None)
        
        # Count by status
        status_stats = await db.jobs.aggregate([
            {"$match": {"source": "scraped"}},
            {"$group": {
                "_id": "$status",
                "count": {"$sum": 1}
            }}
        ]).to_list(None)
        
        # Recent activity
        recent_reports = await db.scraper_reports.find(
            {},
            sort=[("timestamp", -1)],
            limit=5
        ).to_list(5)
        
        return {
            "jobs_by_portal": portal_stats,
            "jobs_by_status": status_stats,
            "recent_activity": recent_reports,
            "total_scraped_jobs": await db.jobs.count_documents({"source": "scraped"}),
            "total_draft_jobs": await db.jobs.count_documents({"source": "scraped", "status": "draft"}),
            "total_published_jobs": await db.jobs.count_documents({"source": "scraped", "status": "published"})
        }
    except Exception as e:
        logger.error(f"Error getting summary: {str(e)}")
        raise HTTPException(500, str(e))

# ============================================================================
# Duplicate Detection Endpoints
# ============================================================================

@router.post("/duplicates/check")
async def check_duplicates(current_user: dict = Depends(get_current_admin)):
    """
    Check for duplicate jobs and merge them
    Admin only
    """
    db = get_database()
    scraper = AdvancedScraper()
    
    try:
        jobs = await db.jobs.find({"source": "scraped"}).to_list(None)
        
        duplicates_found = []
        jobs_to_delete = []
        
        for i, job in enumerate(jobs):
            for other_job in jobs[i+1:]:
                if await scraper.duplicate_detector.is_duplicate(job, db):
                    duplicates_found.append({
                        "job1": job["id"],
                        "job2": other_job["id"],
                        "title": job["title"]
                    })
                    jobs_to_delete.append(other_job["id"])
        
        # Delete duplicates
        if jobs_to_delete:
            result = await db.jobs.delete_many({"id": {"$in": jobs_to_delete}})
        
        return {
            "duplicates_found": len(duplicates_found),
            "duplicates_deleted": len(jobs_to_delete),
            "duplicates": duplicates_found[:10]  # Show first 10
        }
    except Exception as e:
        logger.error(f"Error checking duplicates: {str(e)}")
        raise HTTPException(500, str(e))

# ============================================================================
# Configuration Endpoints
# ============================================================================

@router.post("/config/update")
async def update_scraper_config(
    portal_name: str,
    frequency_hours: int = None,
    enabled: bool = None,
    current_user: dict = Depends(get_current_admin)
):
    """
    Update portal scraper configuration
    Admin only
    """
    for config in PORTAL_CONFIGS:
        if config["name"] == portal_name:
            if frequency_hours:
                config["frequency_hours"] = frequency_hours
            if enabled is not None:
                config["enabled"] = enabled
            
            db = get_database()
            await db.portal_settings.update_one(
                {"name": portal_name},
                {
                    "$set": {
                        "frequency_hours": config.get("frequency_hours"),
                        "enabled": config.get("enabled"),
                        "updated_at": get_current_timestamp()
                    }
                },
                upsert=True
            )
            
            return {
                "status": "updated",
                "portal": portal_name,
                "config": {
                    "frequency_hours": config.get("frequency_hours"),
                    "enabled": config["enabled"]
                }
            }
    
    raise HTTPException(404, f"Portal '{portal_name}' not found")
