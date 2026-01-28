"""
Advanced Web Scraper Service
Handles job scraping with scheduling, error handling, retry logic, and duplicate detection
"""

import httpx
import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import List, Dict, Optional
from difflib import SequenceMatcher
import uuid
from utils.helpers import get_current_timestamp, slugify, extract_keywords
from config.database import get_database

logger = logging.getLogger(__name__)

class RateLimiter:
    """Per-site rate limiting"""
    def __init__(self):
        self.last_request = {}
        self.request_count = {}
    
    async def check_rate_limit(self, domain: str, requests_per_hour: int = 10):
        """Check if domain can be scraped"""
        now = datetime.now()
        
        if domain not in self.last_request:
            self.last_request[domain] = now
            self.request_count[domain] = 1
            return True
        
        # Reset count if hour passed
        if (now - self.last_request[domain]).seconds > 3600:
            self.request_count[domain] = 1
            self.last_request[domain] = now
            return True
        
        # Check if limit exceeded
        if self.request_count[domain] >= requests_per_hour:
            wait_time = 3600 - (now - self.last_request[domain]).seconds
            logger.warning(f"Rate limit hit for {domain}. Wait {wait_time}s")
            return False
        
        self.request_count[domain] += 1
        return True

class DuplicateDetector:
    """Detect duplicate jobs using multiple methods"""
    
    @staticmethod
    def get_content_hash(title: str, description: str, company: str) -> str:
        """Generate hash of job content"""
        content = f"{title.lower()}{description.lower()}{company.lower()}"
        return hashlib.md5(content.encode()).hexdigest()
    
    @staticmethod
    def similarity_ratio(str1: str, str2: str) -> float:
        """Calculate similarity between two strings (0-1)"""
        return SequenceMatcher(None, str1.lower(), str2.lower()).ratio()
    
    @staticmethod
    async def is_duplicate(job: Dict, db) -> bool:
        """Check if job already exists"""
        # Exact match by hash
        job_hash = DuplicateDetector.get_content_hash(
            job["title"],
            job.get("description", ""),
            job.get("company", "")
        )
        
        existing = await db.jobs.find_one({"content_hash": job_hash})
        if existing:
            return True
        
        # Fuzzy match for similar jobs (>85% similar)
        similar = await db.jobs.find_one({
            "title": {"$regex": job["title"][:10], "$options": "i"},
            "company": job.get("company", "")
        })
        
        if similar:
            ratio = DuplicateDetector.similarity_ratio(
                job["description"],
                similar.get("description", "")
            )
            if ratio > 0.85:
                return True
        
        return False


class AdvancedScraper:
    """Advanced scraper with retry logic, error handling, and multiple sources"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.duplicate_detector = DuplicateDetector()
        self.max_retries = 3
        self.timeout = 30.0
    
    async def fetch_with_retry(self, url: str, max_retries: int = None) -> Optional[str]:
        """Fetch URL with exponential backoff retry logic"""
        if max_retries is None:
            max_retries = self.max_retries
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(follow_redirects=True) as client:
                    response = await client.get(
                        url,
                        timeout=self.timeout,
                        headers={
                            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                        }
                    )
                    response.raise_for_status()
                    return response.text
            except httpx.HTTPError as e:
                wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                logger.warning(f"Attempt {attempt + 1} failed for {url}: {str(e)}. Retry in {wait_time}s")
                
                if attempt < max_retries - 1:
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"Failed to fetch {url} after {max_retries} attempts")
                    return None
    
    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        from urllib.parse import urlparse
        return urlparse(url).netloc
    
    async def scrape_job_portal(self, portal_config: Dict) -> List[Dict]:
        """Scrape a job portal based on configuration"""
        portal_name = portal_config["name"]
        url = portal_config["url"]
        selectors = portal_config["selectors"]
        
        logger.info(f"Scraping {portal_name} from {url}")
        
        # Check rate limit
        domain = self.extract_domain(url)
        if not await self.rate_limiter.check_rate_limit(domain):
            logger.warning(f"Rate limit exceeded for {domain}")
            return []
        
        # Fetch page
        html = await self.fetch_with_retry(url)
        if not html:
            return []
        
        soup = BeautifulSoup(html, 'html.parser')
        jobs = []
        db = get_database()
        
        try:
            # Find job containers
            job_containers = soup.select(selectors["job_container"])
            logger.info(f"Found {len(job_containers)} job containers on {portal_name}")
            
            for container in job_containers[:50]:  # Limit to 50
                try:
                    job = self._extract_job_data(container, selectors, portal_name, url)
                    
                    if not job:
                        continue
                    
                    # Check for duplicates
                    if await self.duplicate_detector.is_duplicate(job, db):
                        logger.info(f"Duplicate job skipped: {job['title']}")
                        continue
                    
                    jobs.append(job)
                except Exception as e:
                    logger.error(f"Error extracting job from {portal_name}: {str(e)}")
                    continue
        
        except Exception as e:
            logger.error(f"Error parsing {portal_name}: {str(e)}")
        
        return jobs
    
    def _extract_job_data(self, container, selectors: Dict, portal_name: str, url: str) -> Optional[Dict]:
        """Extract job data from HTML container"""
        try:
            # Extract fields
            title_elem = container.select_one(selectors["title"])
            title = title_elem.get_text(strip=True) if title_elem else None
            
            if not title or len(title) < 3:
                return None
            
            company_elem = container.select_one(selectors.get("company", ""))
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            location_elem = container.select_one(selectors.get("location", ""))
            location = location_elem.get_text(strip=True) if location_elem else "Not specified"
            
            description_elem = container.select_one(selectors.get("description", ""))
            description = description_elem.get_text(strip=True) if description_elem else title
            
            salary_elem = container.select_one(selectors.get("salary", ""))
            salary = salary_elem.get_text(strip=True) if salary_elem else "Not specified"
            
            job_link_elem = container.select_one(selectors.get("link", "a"))
            job_link = job_link_elem.get("href", "") if job_link_elem else ""
            
            # Ensure absolute URL
            if job_link and not job_link.startswith("http"):
                from urllib.parse import urljoin
                job_link = urljoin(url, job_link)
            
            # Create job document
            job_hash = self.duplicate_detector.get_content_hash(title, description, company)
            
            job_doc = {
                "id": str(uuid.uuid4()),
                "title": title,
                "company": company,
                "location": location,
                "description": description[:500],  # Limit description
                "salary": salary,
                "category": self._categorize_job(title, description),
                "education_required": self._extract_education(description),
                "slug": slugify(title),
                "keywords": extract_keywords(description),
                "source": "scraped",
                "source_portal": portal_name,
                "source_url": job_link or url,
                "content_hash": job_hash,
                "scraped_at": get_current_timestamp(),
                "status": "draft",  # New jobs go to draft queue
                "created_at": get_current_timestamp()
            }
            
            return job_doc
        
        except Exception as e:
            logger.error(f"Error extracting job data: {str(e)}")
            return None
    
    def _categorize_job(self, title: str, description: str) -> str:
        """Auto-categorize job"""
        text = (title + " " + description).lower()
        
        categories = {
            "Railway": ["railway", "rrb", "rti"],
            "SSC": ["ssc", "staff selection"],
            "UPSC": ["upsc", "ias", "ips", "civil service"],
            "Bank": ["bank", "banking", "po", "clerk"],
            "PSC": ["psc", "state service", "assistant"],
            "IT": ["software", "developer", "engineer", "python", "java"],
            "Teaching": ["teacher", "lecturer", "professor", "education"],
            "Government": ["government", "ministry", "department"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "General"
    
    def _extract_education(self, description: str) -> str:
        """Extract education requirement"""
        text = description.lower()
        
        if "graduate" in text or "bachelor" in text or "b.tech" in text or "b.a" in text:
            return "Graduate"
        elif "12th" in text or "senior secondary" in text or "hsc" in text:
            return "12th Pass"
        elif "10th" in text or "secondary" in text or "ssc" in text:
            return "10th Pass"
        elif "phd" in text or "doctorate" in text:
            return "Doctorate"
        elif "diploma" in text:
            return "Diploma"
        
        return "Any"


# Portal Configurations
PORTAL_CONFIGS = [
    {
        "name": "IndiaJobs",
        "url": "https://www.indiajobs.com/",
        "enabled": True,
        "frequency_hours": 4,
        "selectors": {
            "job_container": ".job-card, article.job",
            "title": ".job-title, h2.title",
            "company": ".company-name, .employer",
            "location": ".location, .job-location",
            "description": ".job-desc, .summary, p",
            "salary": ".salary, .price",
            "link": "a.job-link, a[href*='job']"
        }
    },
    {
        "name": "Naukri Government",
        "url": "https://www.naukri.com/government-jobs",
        "enabled": True,
        "frequency_hours": 6,
        "selectors": {
            "job_container": ".jobTuple, .srp-jobtuple-wrapper",
            "title": ".jobTitle, a[data-ga-action='job title']",
            "company": ".company, .n-company-name",
            "location": ".location, .jobType",
            "description": ".jobDescription, .job-desc",
            "salary": ".salary, .n-salary",
            "link": "a.jobTitle"
        }
    },
    {
        "name": "SSC Official",
        "url": "https://ssc.nic.in/",
        "enabled": True,
        "frequency_hours": 8,
        "selectors": {
            "job_container": "tr, .vacancy-row",
            "title": "td:nth-child(2), .post-name",
            "company": "SSC",  # Static
            "location": "td:nth-child(3), .location",
            "description": "td:nth-child(4), .vacancy-details",
            "salary": "td:nth-child(5), .salary",
            "link": "a"
        }
    },
    {
        "name": "Railway Jobs (RRB)",
        "url": "https://indianrailways.gov.in/",
        "enabled": True,
        "frequency_hours": 8,
        "selectors": {
            "job_container": ".notification, .vacancy-item",
            "title": ".notif-title, h3",
            "company": "Railway",  # Static
            "location": ".location, .region",
            "description": ".notif-desc, p",
            "salary": ".salary, .grade-pay",
            "link": "a.notif-link, a"
        }
    },
    {
        "name": "UPSC Portal",
        "url": "https://www.upsc.gov.in/",
        "enabled": True,
        "frequency_hours": 8,
        "selectors": {
            "job_container": ".exam-item, .vacancy",
            "title": ".exam-name, h3",
            "company": "UPSC",  # Static
            "location": ".location, .region",
            "description": ".exam-desc, p",
            "salary": ".salary, .scale",
            "link": "a"
        }
    }
]


async def scrape_all_portals(portal_names: Optional[List[str]] = None) -> Dict:
    """Scrape all enabled portals"""
    db = get_database()
    scraper = AdvancedScraper()
    
    results = {
        "timestamp": get_current_timestamp(),
        "portals": [],
        "total_jobs": 0,
        "total_errors": 0
    }
    
    for config in PORTAL_CONFIGS:
        if not config["enabled"]:
            continue
        
        if portal_names and config["name"] not in portal_names:
            continue
        
        portal_result = {
            "name": config["name"],
            "status": "pending",
            "jobs_found": 0,
            "jobs_saved": 0,
            "errors": []
        }
        
        try:
            jobs = await scraper.scrape_job_portal(config)
            portal_result["jobs_found"] = len(jobs)
            
            # Save to database
            if jobs:
                inserted = await db.jobs.insert_many(jobs)
                portal_result["jobs_saved"] = len(inserted.inserted_ids)
                
                # Log scraping activity
                await db.scraper_logs.insert_one({
                    "portal": config["name"],
                    "jobs_found": len(jobs),
                    "jobs_saved": portal_result["jobs_saved"],
                    "timestamp": get_current_timestamp(),
                    "status": "success"
                })
            
            portal_result["status"] = "success"
            results["total_jobs"] += portal_result["jobs_saved"]
        
        except Exception as e:
            logger.error(f"Error scraping {config['name']}: {str(e)}")
            portal_result["status"] = "failed"
            portal_result["errors"].append(str(e))
            results["total_errors"] += 1
            
            # Log error
            await db.scraper_logs.insert_one({
                "portal": config["name"],
                "status": "failed",
                "error": str(e),
                "timestamp": get_current_timestamp()
            })
        
        results["portals"].append(portal_result)
    
    return results


async def get_scraper_status(db) -> Dict:
    """Get scraper status and statistics"""
    # Get recent scraping logs
    logs = await db.scraper_logs.find(
        {},
        sort=[("timestamp", -1)],
        limit=10
    ).to_list(10)
    
    # Get portal statistics
    stats = []
    for config in PORTAL_CONFIGS:
        if not config["enabled"]:
            continue
        
        portal_logs = await db.scraper_logs.find(
            {"portal": config["name"]},
            sort=[("timestamp", -1)],
            limit=5
        ).to_list(5)
        
        total_jobs = sum(log.get("jobs_saved", 0) for log in portal_logs)
        success_count = sum(1 for log in portal_logs if log.get("status") == "success")
        
        stats.append({
            "portal": config["name"],
            "total_jobs_scraped": total_jobs,
            "recent_runs": len(portal_logs),
            "success_rate": f"{(success_count / len(portal_logs) * 100):.1f}%" if portal_logs else "N/A",
            "last_run": portal_logs[0].get("timestamp") if portal_logs else None
        })
    
    return {
        "status": "operational",
        "portals": stats,
        "recent_logs": logs
    }
