"""
Web Scraper Routes
Scrape job portals and government websites
"""

from fastapi import APIRouter, HTTPException, Depends
from middleware.auth import get_current_admin
from config.database import get_database
from utils.helpers import get_current_timestamp, slugify, extract_keywords
import httpx
from bs4 import BeautifulSoup
import uuid

router = APIRouter(prefix="/scraper", tags=["Scraper"])

@router.post("/scrape-jobs")
async def scrape_jobs(
    url: str,
    current_user: dict = Depends(get_current_admin)
):
    """
    Scrape jobs from URL (Admin only)
    Generic scraper - adjust selectors based on target site
    """
    db = get_database()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Generic job extraction (customize based on site)
    jobs_found = []
    
    # Example: Look for common job listing patterns
    job_cards = soup.find_all(['article', 'div'], class_=lambda x: x and ('job' in x.lower() or 'card' in x.lower()))
    
    for card in job_cards[:20]:  # Limit to 20
        try:
            # Extract title
            title_elem = card.find(['h2', 'h3', 'h4', 'a'], class_=lambda x: x and 'title' in x.lower())
            if not title_elem:
                title_elem = card.find(['h2', 'h3', 'h4'])
            
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Extract company
            company_elem = card.find(class_=lambda x: x and 'company' in x.lower())
            company = company_elem.get_text(strip=True) if company_elem else "Unknown"
            
            # Extract location
            location_elem = card.find(class_=lambda x: x and 'location' in x.lower())
            location = location_elem.get_text(strip=True) if location_elem else "Not specified"
            
            # Extract description
            desc_elem = card.find(['p', 'div'], class_=lambda x: x and ('desc' in x.lower() or 'summary' in x.lower()))
            description = desc_elem.get_text(strip=True) if desc_elem else title
            
            # Create job document
            job_doc = {
                "id": str(uuid.uuid4()),
                "title": title,
                "company": company,
                "location": location,
                "description": description,
                "category": "General",
                "education_required": "Any",
                "salary": "Not specified",
                "slug": slugify(title),
                "keywords": extract_keywords(description),
                "source": "scraped",
                "source_url": url,
                "created_at": get_current_timestamp(),
                "created_by": current_user["id"]
            }
            
            # Check if already exists
            existing = await db.jobs.find_one({"title": title, "company": company})
            if not existing:
                await db.jobs.insert_one(job_doc)
                jobs_found.append(job_doc)
        
        except Exception as e:
            continue
    
    return {
        "message": f"Scraped {len(jobs_found)} jobs",
        "jobs": jobs_found
    }

@router.post("/scrape-yojana")
async def scrape_yojana(
    url: str,
    current_user: dict = Depends(get_current_admin)
):
    """
    Scrape government schemes from URL (Admin only)
    """
    db = get_database()
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    yojanas_found = []
    
    # Generic scheme extraction
    scheme_cards = soup.find_all(['article', 'div'], class_=lambda x: x and ('scheme' in x.lower() or 'yojana' in x.lower() or 'card' in x.lower()))
    
    for card in scheme_cards[:20]:  # Limit to 20
        try:
            # Extract title
            title_elem = card.find(['h2', 'h3', 'h4', 'a'])
            if not title_elem:
                continue
            
            title = title_elem.get_text(strip=True)
            
            # Extract description
            desc_elem = card.find(['p', 'div'])
            description = desc_elem.get_text(strip=True) if desc_elem else title
            
            # Extract ministry
            ministry_elem = card.find(class_=lambda x: x and 'ministry' in x.lower())
            ministry = ministry_elem.get_text(strip=True) if ministry_elem else "Government of India"
            
            # Create yojana document
            yojana_doc = {
                "id": str(uuid.uuid4()),
                "title": title,
                "description": description,
                "ministry": ministry,
                "category": "General",
                "applicable_states": "All India",
                "education_required": "Any",
                "benefits": "As per scheme guidelines",
                "how_to_apply": "Visit official website",
                "slug": slugify(title),
                "keywords": extract_keywords(description),
                "source": "scraped",
                "source_url": url,
                "created_at": get_current_timestamp(),
                "created_by": current_user["id"]
            }
            
            # Check if already exists
            existing = await db.yojana.find_one({"title": title})
            if not existing:
                await db.yojana.insert_one(yojana_doc)
                yojanas_found.append(yojana_doc)
        
        except Exception as e:
            continue
    
    return {
        "message": f"Scraped {len(yojanas_found)} schemes",
        "yojanas": yojanas_found
    }

@router.get("/test-scrape")
async def test_scrape(
    url: str,
    current_user: dict = Depends(get_current_admin)
):
    """
    Test scraping - returns raw HTML structure
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, timeout=30.0)
            response.raise_for_status()
    except Exception as e:
        raise HTTPException(500, f"Failed to fetch URL: {str(e)}")
    
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Extract structure info
    structure = {
        "title": soup.title.string if soup.title else "No title",
        "headings": [h.get_text(strip=True) for h in soup.find_all(['h1', 'h2', 'h3'])[:10]],
        "links": [a.get('href') for a in soup.find_all('a', href=True)[:20]],
        "classes": list(set([cls for elem in soup.find_all(class_=True) for cls in elem.get('class', [])]))[:50]
    }
    
    return structure
