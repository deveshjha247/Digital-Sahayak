"""
=============================================================================
OGD INDIA SCRAPER - Data.gov.in Integration
=============================================================================
Open Government Data (OGD) Platform India - Official Government Portal
Website: https://data.gov.in

Features:
- Fetch government schemes data
- Fetch employment/job data  
- Fetch social welfare data
- CSV/JSON dataset support
- Automatic caching to reduce API calls

API Documentation: https://data.gov.in/ogpl_apis
=============================================================================
"""

import httpx
import json
import csv
import io
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path
import asyncio

logger = logging.getLogger(__name__)

# OGD India API Configuration
OGD_CONFIG = {
    "base_url": "https://api.data.gov.in/resource",
    "catalog_url": "https://api.data.gov.in/catalog",
    
    # Important Resource IDs for Digital Sahayak
    "resources": {
        # Employment & Jobs
        "employment_exchange": "9115b89c-7a80-4f54-9b06-21086e0f0bd7",
        "skill_development": "e8394b8e-6f2b-4b5a-8c7c-fb3d9d3f8e1a",
        "rojgar_mela": "f7293c4d-5e1a-4c8b-9d6e-2a3b4c5d6e7f",
        
        # Government Schemes
        "pm_schemes": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "state_schemes": "b2c3d4e5-f6a7-8901-bcde-f12345678901",
        "welfare_schemes": "c3d4e5f6-a7b8-9012-cdef-123456789012",
        
        # Social Welfare
        "pension_schemes": "d4e5f6a7-b8c9-0123-defa-234567890123",
        "scholarship_schemes": "e5f6a7b8-c9d0-1234-efab-345678901234",
        "health_schemes": "f6a7b8c9-d0e1-2345-fabc-456789012345",
        
        # Education
        "education_stats": "a7b8c9d0-e1f2-3456-abcd-567890123456",
        "university_data": "b8c9d0e1-f2a3-4567-bcde-678901234567",
    },
    
    # Category mappings
    "categories": {
        "employment": ["employment_exchange", "skill_development", "rojgar_mela"],
        "schemes": ["pm_schemes", "state_schemes", "welfare_schemes"],
        "welfare": ["pension_schemes", "scholarship_schemes", "health_schemes"],
        "education": ["education_stats", "university_data"]
    },
    
    # Cache settings
    "cache_duration_hours": 24,
    "max_records_per_request": 100
}


class OGDIndiaScraper:
    """
    Scraper for Data.gov.in - Open Government Data Platform
    
    Usage:
        scraper = OGDIndiaScraper(api_key="your_api_key")
        
        # Fetch employment data
        jobs = await scraper.fetch_employment_data()
        
        # Fetch schemes
        schemes = await scraper.fetch_schemes_data()
        
        # Search datasets
        results = await scraper.search_datasets("Bihar scholarship")
    """
    
    def __init__(self, api_key: Optional[str] = None, db=None):
        """
        Initialize OGD India Scraper
        
        Args:
            api_key: Data.gov.in API key (get from https://data.gov.in/ogpl_apis)
            db: MongoDB database for caching
        """
        self.api_key = api_key
        self.db = db
        self.cache_collection = db['ogd_cache'] if db else None
        self.base_url = OGD_CONFIG['base_url']
        self.catalog_url = OGD_CONFIG['catalog_url']
        
        # HTTP client with timeout
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers={
                "User-Agent": "DigitalSahayak/1.0 (Government Job Portal)",
                "Accept": "application/json"
            }
        )
        
        logger.info("OGD India Scraper initialized")
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
    
    # ===================== CORE API METHODS =====================
    
    async def fetch_resource(
        self, 
        resource_id: str, 
        format: str = "json",
        limit: int = 100,
        offset: int = 0,
        filters: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Fetch data from a specific OGD resource
        
        Args:
            resource_id: OGD resource ID
            format: Output format (json, csv, xml)
            limit: Number of records to fetch
            offset: Pagination offset
            filters: Additional filters
            
        Returns:
            Dict with records and metadata
        """
        try:
            # Check cache first
            cache_key = f"{resource_id}_{format}_{limit}_{offset}"
            cached = await self._get_cache(cache_key)
            if cached:
                logger.info(f"Cache hit for resource: {resource_id}")
                return cached
            
            # Build API URL
            params = {
                "api-key": self.api_key,
                "format": format,
                "limit": limit,
                "offset": offset
            }
            
            if filters:
                params.update(filters)
            
            url = f"{self.base_url}/{resource_id}"
            
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            
            if format == "json":
                data = response.json()
            elif format == "csv":
                data = self._parse_csv(response.text)
            else:
                data = {"raw": response.text}
            
            # Cache the result
            await self._set_cache(cache_key, data)
            
            logger.info(f"Fetched {len(data.get('records', []))} records from {resource_id}")
            return data
            
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching resource {resource_id}: {e}")
            return {"error": str(e), "records": []}
        except Exception as e:
            logger.error(f"Error fetching resource {resource_id}: {e}")
            return {"error": str(e), "records": []}
    
    async def search_datasets(
        self, 
        query: str,
        sector: Optional[str] = None,
        limit: int = 20
    ) -> List[Dict]:
        """
        Search OGD catalog for datasets
        
        Args:
            query: Search query
            sector: Filter by sector (employment, education, etc.)
            limit: Max results
            
        Returns:
            List of matching datasets
        """
        try:
            params = {
                "api-key": self.api_key,
                "format": "json",
                "q": query,
                "limit": limit
            }
            
            if sector:
                params["sector"] = sector
            
            response = await self.client.get(self.catalog_url, params=params)
            response.raise_for_status()
            
            data = response.json()
            return data.get("records", [])
            
        except Exception as e:
            logger.error(f"Error searching datasets: {e}")
            return []
    
    # ===================== EMPLOYMENT DATA =====================
    
    async def fetch_employment_data(
        self, 
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch employment/job related data
        
        Args:
            state: Filter by state (Bihar, UP, etc.)
            limit: Max records
            
        Returns:
            List of employment records
        """
        all_records = []
        
        for resource_key in OGD_CONFIG['categories']['employment']:
            resource_id = OGD_CONFIG['resources'].get(resource_key)
            if not resource_id:
                continue
            
            filters = {}
            if state:
                filters['filters[state]'] = state
            
            data = await self.fetch_resource(
                resource_id=resource_id,
                limit=limit,
                filters=filters
            )
            
            records = data.get('records', [])
            
            # Normalize records
            for record in records:
                normalized = self._normalize_employment_record(record, resource_key)
                if normalized:
                    all_records.append(normalized)
        
        logger.info(f"Fetched {len(all_records)} employment records")
        return all_records
    
    def _normalize_employment_record(self, record: Dict, source: str) -> Optional[Dict]:
        """Normalize employment record to standard format"""
        try:
            return {
                "id": record.get('id') or record.get('_id'),
                "title": record.get('title') or record.get('job_title') or record.get('post_name'),
                "organization": record.get('organization') or record.get('department') or record.get('ministry'),
                "state": record.get('state') or record.get('location'),
                "vacancies": int(record.get('vacancies') or record.get('total_posts') or 0),
                "qualification": record.get('qualification') or record.get('eligibility'),
                "last_date": record.get('last_date') or record.get('closing_date'),
                "salary": record.get('salary') or record.get('pay_scale'),
                "category": "government",
                "source": f"data.gov.in/{source}",
                "source_url": record.get('link') or record.get('apply_link'),
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing employment record: {e}")
            return None
    
    # ===================== SCHEMES DATA =====================
    
    async def fetch_schemes_data(
        self, 
        state: Optional[str] = None,
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch government schemes data
        
        Args:
            state: Filter by state
            category: Filter by category (welfare, education, health)
            limit: Max records
            
        Returns:
            List of scheme records
        """
        all_records = []
        
        resource_keys = OGD_CONFIG['categories']['schemes']
        if category and category in OGD_CONFIG['categories']:
            resource_keys = OGD_CONFIG['categories'][category]
        
        for resource_key in resource_keys:
            resource_id = OGD_CONFIG['resources'].get(resource_key)
            if not resource_id:
                continue
            
            filters = {}
            if state:
                filters['filters[state]'] = state
            
            data = await self.fetch_resource(
                resource_id=resource_id,
                limit=limit,
                filters=filters
            )
            
            records = data.get('records', [])
            
            for record in records:
                normalized = self._normalize_scheme_record(record, resource_key)
                if normalized:
                    all_records.append(normalized)
        
        logger.info(f"Fetched {len(all_records)} scheme records")
        return all_records
    
    def _normalize_scheme_record(self, record: Dict, source: str) -> Optional[Dict]:
        """Normalize scheme record to standard format"""
        try:
            return {
                "id": record.get('id') or record.get('_id'),
                "name": record.get('scheme_name') or record.get('title') or record.get('name'),
                "name_hi": record.get('scheme_name_hindi') or record.get('title_hi'),
                "ministry": record.get('ministry') or record.get('department'),
                "description": record.get('description') or record.get('objective'),
                "benefits": record.get('benefits') or record.get('assistance'),
                "eligibility": record.get('eligibility') or record.get('beneficiary'),
                "documents_required": self._parse_documents(record.get('documents')),
                "state": record.get('state') or "all",
                "category": self._determine_category(record),
                "apply_link": record.get('apply_link') or record.get('portal_link'),
                "source": f"data.gov.in/{source}",
                "source_url": record.get('source_url'),
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing scheme record: {e}")
            return None
    
    # ===================== WELFARE DATA =====================
    
    async def fetch_welfare_data(
        self, 
        welfare_type: Optional[str] = None,
        state: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch social welfare data (pension, scholarship, health)
        
        Args:
            welfare_type: Type of welfare (pension, scholarship, health)
            state: Filter by state
            limit: Max records
            
        Returns:
            List of welfare records
        """
        all_records = []
        
        resource_keys = OGD_CONFIG['categories']['welfare']
        
        if welfare_type:
            type_mapping = {
                'pension': ['pension_schemes'],
                'scholarship': ['scholarship_schemes'],
                'health': ['health_schemes']
            }
            resource_keys = type_mapping.get(welfare_type, resource_keys)
        
        for resource_key in resource_keys:
            resource_id = OGD_CONFIG['resources'].get(resource_key)
            if not resource_id:
                continue
            
            filters = {}
            if state:
                filters['filters[state]'] = state
            
            data = await self.fetch_resource(
                resource_id=resource_id,
                limit=limit,
                filters=filters
            )
            
            records = data.get('records', [])
            
            for record in records:
                normalized = self._normalize_welfare_record(record, resource_key)
                if normalized:
                    all_records.append(normalized)
        
        logger.info(f"Fetched {len(all_records)} welfare records")
        return all_records
    
    def _normalize_welfare_record(self, record: Dict, source: str) -> Optional[Dict]:
        """Normalize welfare record to standard format"""
        try:
            return {
                "id": record.get('id') or record.get('_id'),
                "name": record.get('scheme_name') or record.get('title'),
                "type": source.replace('_schemes', ''),
                "ministry": record.get('ministry') or record.get('department'),
                "description": record.get('description'),
                "benefits": record.get('benefits') or record.get('amount'),
                "eligibility": record.get('eligibility'),
                "state": record.get('state') or "all",
                "apply_link": record.get('apply_link'),
                "source": f"data.gov.in/{source}",
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing welfare record: {e}")
            return None
    
    # ===================== BULK FETCH =====================
    
    async def fetch_all_data(
        self, 
        state: Optional[str] = None
    ) -> Dict[str, List[Dict]]:
        """
        Fetch all available data (employment, schemes, welfare)
        
        Args:
            state: Filter by state
            
        Returns:
            Dict with all data categories
        """
        logger.info(f"Starting bulk fetch for state: {state or 'All India'}")
        
        # Fetch all categories in parallel
        employment_task = self.fetch_employment_data(state=state)
        schemes_task = self.fetch_schemes_data(state=state)
        welfare_task = self.fetch_welfare_data(state=state)
        
        employment, schemes, welfare = await asyncio.gather(
            employment_task,
            schemes_task,
            welfare_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(employment, Exception):
            logger.error(f"Employment fetch failed: {employment}")
            employment = []
        if isinstance(schemes, Exception):
            logger.error(f"Schemes fetch failed: {schemes}")
            schemes = []
        if isinstance(welfare, Exception):
            logger.error(f"Welfare fetch failed: {welfare}")
            welfare = []
        
        result = {
            "employment": employment,
            "schemes": schemes,
            "welfare": welfare,
            "total_records": len(employment) + len(schemes) + len(welfare),
            "fetched_at": datetime.utcnow().isoformat(),
            "state_filter": state
        }
        
        logger.info(f"Bulk fetch complete: {result['total_records']} total records")
        return result
    
    # ===================== HELPER METHODS =====================
    
    def _parse_csv(self, csv_text: str) -> Dict:
        """Parse CSV text to dict"""
        try:
            reader = csv.DictReader(io.StringIO(csv_text))
            records = list(reader)
            return {"records": records, "count": len(records)}
        except Exception as e:
            logger.error(f"Error parsing CSV: {e}")
            return {"records": [], "error": str(e)}
    
    def _parse_documents(self, docs_str: Optional[str]) -> List[str]:
        """Parse documents string to list"""
        if not docs_str:
            return []
        
        if isinstance(docs_str, list):
            return docs_str
        
        # Split by common delimiters
        for delim in [',', ';', '\n', '|']:
            if delim in docs_str:
                return [d.strip() for d in docs_str.split(delim) if d.strip()]
        
        return [docs_str]
    
    def _determine_category(self, record: Dict) -> str:
        """Determine scheme category from record"""
        name = str(record.get('scheme_name', '') or record.get('title', '')).lower()
        
        category_keywords = {
            'education': ['scholarship', 'education', 'student', 'school', 'college'],
            'health': ['health', 'medical', 'hospital', 'treatment', 'ayushman'],
            'housing': ['awas', 'housing', 'home', 'pradhan mantri awas'],
            'agriculture': ['kisan', 'farmer', 'agriculture', 'krishi', 'fasal'],
            'pension': ['pension', 'vridha', 'widow', 'divyang'],
            'women': ['mahila', 'women', 'girl', 'beti', 'matritva'],
            'employment': ['rojgar', 'employment', 'job', 'skill', 'mudra']
        }
        
        for category, keywords in category_keywords.items():
            if any(kw in name for kw in keywords):
                return category
        
        return 'welfare'
    
    # ===================== CACHING =====================
    
    async def _get_cache(self, key: str) -> Optional[Dict]:
        """Get cached data"""
        if not self.cache_collection:
            return None
        
        try:
            cached = await self.cache_collection.find_one({"key": key})
            if cached:
                # Check expiry
                cached_at = datetime.fromisoformat(cached.get('cached_at', ''))
                expiry = timedelta(hours=OGD_CONFIG['cache_duration_hours'])
                
                if datetime.utcnow() - cached_at < expiry:
                    return cached.get('data')
                else:
                    # Cache expired
                    await self.cache_collection.delete_one({"key": key})
            
            return None
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    async def _set_cache(self, key: str, data: Dict):
        """Set cache data"""
        if not self.cache_collection:
            return
        
        try:
            await self.cache_collection.update_one(
                {"key": key},
                {
                    "$set": {
                        "key": key,
                        "data": data,
                        "cached_at": datetime.utcnow().isoformat()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    async def clear_cache(self):
        """Clear all cached data"""
        if self.cache_collection:
            await self.cache_collection.delete_many({})
            logger.info("OGD cache cleared")


# ===================== CONVENIENCE FUNCTIONS =====================

async def get_ogd_scraper(api_key: str = None, db=None) -> OGDIndiaScraper:
    """Get OGD scraper instance"""
    import os
    api_key = api_key or os.getenv('OGD_API_KEY')
    return OGDIndiaScraper(api_key=api_key, db=db)


async def fetch_bihar_data(api_key: str = None, db=None) -> Dict:
    """Fetch all Bihar specific data"""
    scraper = await get_ogd_scraper(api_key, db)
    try:
        return await scraper.fetch_all_data(state="Bihar")
    finally:
        await scraper.close()


async def fetch_schemes_by_category(
    category: str, 
    state: str = None,
    api_key: str = None,
    db=None
) -> List[Dict]:
    """Fetch schemes by category"""
    scraper = await get_ogd_scraper(api_key, db)
    try:
        return await scraper.fetch_schemes_data(state=state, category=category)
    finally:
        await scraper.close()


# ===================== TEST =====================

if __name__ == "__main__":
    async def test():
        print("Testing OGD India Scraper...")
        
        # Note: You need an API key from https://data.gov.in/ogpl_apis
        scraper = OGDIndiaScraper(api_key="your_api_key_here")
        
        # Search datasets
        results = await scraper.search_datasets("Bihar employment")
        print(f"Found {len(results)} datasets")
        
        await scraper.close()
    
    asyncio.run(test())
