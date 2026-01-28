"""
Scheduler Service
Handles automatic scheduling of scraper jobs using APScheduler
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
import logging
from datetime import datetime
from services.advanced_scraper import scrape_all_portals, PORTAL_CONFIGS
from config.database import get_database
from utils.helpers import get_current_timestamp

logger = logging.getLogger(__name__)

class ScraperScheduler:
    """Manages scheduling of scraper jobs"""
    
    def __init__(self):
        self.scheduler = None
        self.is_running = False
    
    async def start(self):
        """Start the scheduler"""
        self.scheduler = AsyncIOScheduler()
        
        # Schedule scraping for each portal based on frequency
        for config in PORTAL_CONFIGS:
            if not config["enabled"]:
                continue
            
            frequency_hours = config.get("frequency_hours", 6)
            portal_name = config["name"]
            
            job_id = f"scrape_{portal_name.lower().replace(' ', '_')}"
            
            self.scheduler.add_job(
                self._scrape_portal_job,
                IntervalTrigger(hours=frequency_hours),
                id=job_id,
                name=f"Scrape {portal_name}",
                args=[portal_name],
                replace_existing=True,
                max_instances=1,  # Prevent concurrent runs
                coalesce=True
            )
            
            logger.info(f"Scheduled {portal_name} scraping every {frequency_hours} hours")
        
        # Schedule cleanup job (daily at 2 AM)
        self.scheduler.add_job(
            self._cleanup_old_drafts,
            CronTrigger(hour=2, minute=0),
            id="cleanup_drafts",
            name="Cleanup Old Draft Jobs",
            max_instances=1
        )
        
        self.scheduler.start()
        self.is_running = True
        logger.info("Scraper scheduler started")
    
    async def stop(self):
        """Stop the scheduler"""
        if self.scheduler:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Scraper scheduler stopped")
    
    async def _scrape_portal_job(self, portal_name: str):
        """Job callback for scraping a portal"""
        db = get_database()
        
        logger.info(f"Starting scheduled scrape for {portal_name}")
        
        try:
            results = await scrape_all_portals([portal_name])
            
            # Update scheduler stats
            await db.scheduler_stats.update_one(
                {"type": "last_scrape"},
                {
                    "$set": {
                        "timestamp": get_current_timestamp(),
                        "portal": portal_name,
                        "jobs_found": results["portals"][0]["jobs_found"] if results["portals"] else 0,
                        "jobs_saved": results["portals"][0]["jobs_saved"] if results["portals"] else 0,
                        "status": results["portals"][0]["status"] if results["portals"] else "failed"
                    }
                },
                upsert=True
            )
            
            logger.info(f"Completed scrape for {portal_name}: {results}")
        
        except Exception as e:
            logger.error(f"Error in scheduled scrape for {portal_name}: {str(e)}")
            
            # Log error
            await db.scheduler_stats.insert_one({
                "type": "scrape_error",
                "portal": portal_name,
                "error": str(e),
                "timestamp": get_current_timestamp()
            })
    
    async def _cleanup_old_drafts(self):
        """Cleanup old draft jobs (older than 7 days)"""
        db = get_database()
        
        logger.info("Running cleanup of old draft jobs")
        
        try:
            from datetime import datetime, timedelta
            cutoff_date = (datetime.now() - timedelta(days=7)).isoformat()
            
            result = await db.jobs.delete_many({
                "status": "draft",
                "scraped_at": {"$lt": cutoff_date}
            })
            
            logger.info(f"Deleted {result.deleted_count} old draft jobs")
            
            await db.scheduler_stats.insert_one({
                "type": "cleanup",
                "deleted_count": result.deleted_count,
                "timestamp": get_current_timestamp(),
                "status": "success"
            })
        
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
    
    def get_jobs(self):
        """Get list of scheduled jobs"""
        if not self.scheduler:
            return []
        
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })
        
        return jobs
    
    async def trigger_job(self, job_id: str):
        """Manually trigger a scheduled job"""
        if not self.scheduler:
            raise Exception("Scheduler not running")
        
        job = self.scheduler.get_job(job_id)
        if not job:
            raise Exception(f"Job {job_id} not found")
        
        # Execute job immediately
        await job.func(*job.args, **job.kwargs)
        logger.info(f"Manually triggered job: {job_id}")

# Global scheduler instance
_scheduler = None

def get_scheduler() -> ScraperScheduler:
    """Get or create scheduler instance"""
    global _scheduler
    if _scheduler is None:
        _scheduler = ScraperScheduler()
    return _scheduler
