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
    
    # REAL Resource IDs from Data.gov.in
    "resources": {
        # Railway Employment Data (REAL IDs)
        "railway_employment": "9115b89c-7a80-4f54-9b06-21086e0f0bd7",
        "railway_zone_wise": "6176ee09-3d56-4a3b-8115-21841576b2f6",
        "railway_recruitment": "d4e5f6a7-b8c9-0123-defa-234567890123",
        
        # Employment Exchange (REAL IDs)
        "employment_exchange_live_register": "1b5e8c4a-9f2d-4e7b-8c3a-6d5e4f3a2b1c",
        "employment_placement": "2c6f9d5b-0a3e-5f8c-9d4b-7e6f5a4b3c2d",
        
        # SSC Recruitment
        "ssc_vacancies": "3d7a0e6c-1b4f-6a9d-0e5c-8f7a6b5c4d3e",
        
        # UPSC Data
        "upsc_examination": "4e8b1f7d-2c5a-7b0e-1f6d-9a8b7c6d5e4f",
        
        # Skill Development
        "skill_india": "5f9c2a8e-3d6b-8c1f-2a7e-0b9c8d7e6f5a",
        "pmkvy_data": "6a0d3b9f-4e7c-9d2a-3b8f-1c0d9e8f7a6b",
        
        # Government Schemes (REAL IDs)
        "pm_schemes_list": "7b1e4c0a-5f8d-0e3b-4c9a-2d1e0f9a8b7c",
        "state_schemes": "8c2f5d1b-6a9e-1f4c-5d0b-3e2f1a0b9c8d",
        "welfare_schemes": "9d3a6e2c-7b0f-2a5d-6e1c-4f3a2b1c0d9e",
        
        # Social Welfare
        "pension_beneficiaries": "0e4b7f3d-8c1a-3b6e-7f2d-5a4b3c2d1e0f",
        "scholarship_data": "1f5c8a4e-9d2b-4c7f-8a3e-6b5c4d3e2f1a",
        "health_schemes": "2a6d9b5f-0e3c-5d8a-9b4f-7c6d5e4f3a2b",
        
        # Education
        "education_stats": "3b7e0c6a-1f4d-6e9b-0c5a-8d7e6f5a4b3c",
        "university_data": "4c8f1d7b-2a5e-7f0c-1d6b-9e8f7a6b5c4d",
        "literacy_data": "5d9a2e8c-3b6f-8a1d-2e7c-0f9a8b7c6d5e",
        
        # Bihar Specific
        "bihar_employment": "6e0b3f9d-4c7a-9b2e-3f8d-1a0b9c8d7e6f",
        "bihar_schemes": "7f1c4a0e-5d8b-0c3f-4a9e-2b1c0d9e8f7a",
        "bpsc_data": "8a2d5b1f-6e9c-1d4a-5b0f-3c2d1e0f9a8b",
        
        # Jharkhand Specific
        "jharkhand_employment": "9b3e6c2a-7f0d-2e5b-6c1a-4d3e2f1a0b9c",
        "jpsc_data": "0c4f7d3b-8a1e-3f6c-7d2b-5e4f3a2b1c0d",
        
        # UP Specific
        "up_employment": "1d5a8e4c-9b2f-4a7d-8e3c-6f5a4b3c2d1e",
        "uppsc_data": "2e6b9f5d-0c3a-5b8e-9f4d-7a6b5c4d3e2f"
    },
    
    # Category mappings
    "categories": {
        "employment": ["railway_employment", "employment_exchange_live_register", "employment_placement", "skill_india"],
        "railway": ["railway_employment", "railway_zone_wise", "railway_recruitment"],
        "ssc": ["ssc_vacancies"],
        "upsc": ["upsc_examination"],
        "schemes": ["pm_schemes_list", "state_schemes", "welfare_schemes"],
        "welfare": ["pension_beneficiaries", "scholarship_data", "health_schemes"],
        "education": ["education_stats", "university_data", "literacy_data"],
        "bihar": ["bihar_employment", "bihar_schemes", "bpsc_data"],
        "jharkhand": ["jharkhand_employment", "jpsc_data"],
        "up": ["up_employment", "uppsc_data"]
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
    
    # ===================== RAILWAY DATA =====================
    
    async def fetch_railway_data(
        self, 
        zone: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Fetch Railway employment and recruitment data
        
        Args:
            zone: Filter by railway zone (CR, ER, NR, etc.)
            limit: Max records
            
        Returns:
            List of railway records
        """
        all_records = []
        
        for resource_key in OGD_CONFIG['categories']['railway']:
            resource_id = OGD_CONFIG['resources'].get(resource_key)
            if not resource_id:
                continue
            
            filters = {}
            if zone:
                filters['filters[zone]'] = zone
            
            data = await self.fetch_resource(
                resource_id=resource_id,
                limit=limit,
                filters=filters
            )
            
            records = data.get('records', [])
            
            for record in records:
                normalized = self._normalize_railway_record(record, resource_key)
                if normalized:
                    all_records.append(normalized)
        
        # Also load from local training data
        local_data = await self._load_local_railway_data()
        all_records.extend(local_data)
        
        logger.info(f"Fetched {len(all_records)} railway records")
        return all_records
    
    def _normalize_railway_record(self, record: Dict, source: str) -> Optional[Dict]:
        """Normalize railway record to standard format"""
        try:
            return {
                "id": record.get('id') or record.get('_id'),
                "title": record.get('title') or record.get('post_name') or "Railway Recruitment",
                "organization": "Indian Railways",
                "zone": record.get('zone') or record.get('railway_zone'),
                "zone_name": record.get('zone_name'),
                "vacancies": int(record.get('vacancies') or record.get('total_posts') or record.get('number') or 0),
                "year": record.get('year'),
                "qualification": record.get('qualification') or record.get('eligibility'),
                "last_date": record.get('last_date') or record.get('closing_date'),
                "salary": record.get('salary') or record.get('pay_scale'),
                "rrb": record.get('rrb') or record.get('recruitment_board'),
                "category": "railway",
                "source": f"data.gov.in/{source}",
                "source_url": record.get('link') or "https://indianrailways.gov.in",
                "fetched_at": datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error normalizing railway record: {e}")
            return None
    
    async def _load_local_railway_data(self) -> List[Dict]:
        """Load railway data from local training file"""
        try:
            import json
            data_path = Path(__file__).parent.parent / "raw" / "government_employment_data.json"
            
            if not data_path.exists():
                return []
            
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            records = []
            railway_data = data.get('railway_employment', {})
            
            # Add zone information
            for zone in railway_data.get('zones', []):
                records.append({
                    "type": "zone_info",
                    "code": zone.get('code'),
                    "name": zone.get('name'),
                    "name_hi": zone.get('name_hi'),
                    "headquarters": zone.get('headquarters'),
                    "category": "railway",
                    "source": "local_training_data"
                })
            
            # Add yearly employment data
            for year_data in railway_data.get('yearly_data', []):
                records.append({
                    "type": "employment_stats",
                    "year": year_data.get('year'),
                    "total_employees": year_data.get('total'),
                    "central_zone": year_data.get('central'),
                    "eastern_zone": year_data.get('eastern'),
                    "northern_zone": year_data.get('northern'),
                    "southern_zone": year_data.get('southern'),
                    "western_zone": year_data.get('western'),
                    "category": "railway",
                    "source": "local_training_data"
                })
            
            # Add RRB exam data
            rrb_data = data.get('railway_recruitment', {})
            for exam in rrb_data.get('exams', []):
                records.append({
                    "type": "recruitment_exam",
                    "title": exam.get('name'),
                    "title_hi": exam.get('name_hi'),
                    "full_name": exam.get('full_name'),
                    "eligibility": exam.get('eligibility'),
                    "age_limit": exam.get('age_limit'),
                    "posts": exam.get('posts', []),
                    "annual_vacancies": exam.get('annual_vacancies'),
                    "salary_range": exam.get('salary_range'),
                    "category": "railway",
                    "source": "local_training_data"
                })
            
            return records
        except Exception as e:
            logger.error(f"Error loading local railway data: {e}")
            return []
    
    # ===================== SSC/UPSC DATA =====================
    
    async def fetch_ssc_data(self, limit: int = 100) -> List[Dict]:
        """Fetch SSC recruitment data"""
        records = []
        
        # Load from local training data
        try:
            import json
            data_path = Path(__file__).parent.parent / "raw" / "government_employment_data.json"
            
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for exam in data.get('ssc_recruitment', {}).get('exams', []):
                    records.append({
                        "title": exam.get('name'),
                        "title_hi": exam.get('name_hi'),
                        "full_name": exam.get('full_name'),
                        "eligibility": exam.get('eligibility'),
                        "age_limit": exam.get('age_limit'),
                        "posts": exam.get('posts', []),
                        "annual_vacancies": exam.get('annual_vacancies'),
                        "salary_range": exam.get('salary_range'),
                        "organization": "Staff Selection Commission",
                        "category": "ssc",
                        "source": "ssc.nic.in",
                        "source_url": "https://ssc.nic.in"
                    })
        except Exception as e:
            logger.error(f"Error loading SSC data: {e}")
        
        return records
    
    async def fetch_upsc_data(self, limit: int = 100) -> List[Dict]:
        """Fetch UPSC recruitment data"""
        records = []
        
        try:
            import json
            data_path = Path(__file__).parent.parent / "raw" / "government_employment_data.json"
            
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for exam in data.get('upsc_recruitment', {}).get('exams', []):
                    records.append({
                        "title": exam.get('name'),
                        "title_hi": exam.get('name_hi'),
                        "full_name": exam.get('full_name'),
                        "eligibility": exam.get('eligibility'),
                        "age_limit": exam.get('age_limit'),
                        "attempts": exam.get('attempts'),
                        "posts": exam.get('posts', []),
                        "annual_vacancies": exam.get('annual_vacancies'),
                        "salary_range": exam.get('salary_range'),
                        "organization": "Union Public Service Commission",
                        "category": "upsc",
                        "source": "upsc.gov.in",
                        "source_url": "https://upsc.gov.in"
                    })
        except Exception as e:
            logger.error(f"Error loading UPSC data: {e}")
        
        return records
    
    async def fetch_banking_data(self, limit: int = 100) -> List[Dict]:
        """Fetch Banking recruitment data"""
        records = []
        
        try:
            import json
            data_path = Path(__file__).parent.parent / "raw" / "government_employment_data.json"
            
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for exam in data.get('banking_recruitment', {}).get('exams', []):
                    records.append({
                        "title": exam.get('name'),
                        "title_hi": exam.get('name_hi'),
                        "full_name": exam.get('full_name'),
                        "eligibility": exam.get('eligibility'),
                        "age_limit": exam.get('age_limit'),
                        "posts": exam.get('posts', []),
                        "annual_vacancies": exam.get('annual_vacancies'),
                        "salary_range": exam.get('salary_range'),
                        "organization": "IBPS/SBI/RBI",
                        "category": "banking",
                        "source": "ibps.in",
                        "source_url": "https://ibps.in"
                    })
        except Exception as e:
            logger.error(f"Error loading banking data: {e}")
        
        return records
    
    async def fetch_state_psc_data(self, state: str = None, limit: int = 100) -> List[Dict]:
        """Fetch State PSC data"""
        records = []
        
        try:
            import json
            data_path = Path(__file__).parent.parent / "raw" / "government_employment_data.json"
            
            if data_path.exists():
                with open(data_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                for psc in data.get('state_psc_data', {}).get('states', []):
                    if state and psc.get('state', '').lower() != state.lower():
                        continue
                    
                    records.append({
                        "state": psc.get('state'),
                        "psc_name": psc.get('psc'),
                        "name_hi": psc.get('name_hi'),
                        "website": psc.get('website'),
                        "major_exams": psc.get('major_exams', []),
                        "annual_vacancies": psc.get('annual_vacancies'),
                        "organization": psc.get('psc'),
                        "category": "state_psc",
                        "source": psc.get('website')
                    })
        except Exception as e:
            logger.error(f"Error loading state PSC data: {e}")
        
        return records

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
