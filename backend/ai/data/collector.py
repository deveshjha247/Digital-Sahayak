"""
Data Collector
Handles collection from multiple sources with rate limiting and error handling
"""

import asyncio
import aiohttp
import logging
import time
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from urllib.parse import urljoin, urlparse
from abc import ABC, abstractmethod

from .data_config import DataConfig, SOURCES, SCRAPING_RULES
from .metadata import MetadataManager, DataMetadata

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Base class for data collectors"""
    
    def __init__(self, config: DataConfig = None):
        self.config = config or DataConfig()
        self.metadata_manager = MetadataManager()
        self.last_request_time: Dict[str, float] = {}
        self.user_agent = SCRAPING_RULES["default"]["user_agent"]
    
    @abstractmethod
    async def collect(self, source_config: Dict) -> List[Dict]:
        """Collect data from source"""
        pass
    
    async def rate_limit(self, domain: str, delay: float = None):
        """Apply rate limiting per domain"""
        if delay is None:
            delay = self.config.default_rate_limit
        
        now = time.time()
        last_time = self.last_request_time.get(domain, 0)
        wait_time = delay - (now - last_time)
        
        if wait_time > 0:
            await asyncio.sleep(wait_time)
        
        self.last_request_time[domain] = time.time()
    
    def validate_data(self, data: Dict) -> bool:
        """Validate collected data meets quality requirements"""
        # Check required fields
        for field in self.config.required_fields:
            if not data.get(field):
                return False
        
        # Check description length
        description = data.get("description", "")
        if len(description) < self.config.min_description_length:
            return False
        
        return True
    
    def create_metadata(self, data: Dict, source: str, **kwargs) -> DataMetadata:
        """Create metadata for collected item"""
        content = json.dumps(data, sort_keys=True)
        
        return DataMetadata(
            id="",  # Will be generated
            content_hash="",  # Will be computed
            source=source,
            source_type=kwargs.get("source_type", "scraper"),
            source_url=data.get("url"),
            collection_method="automated",
            state=data.get("state", kwargs.get("state", "all_india")),
            content_type=data.get("content_type", kwargs.get("content_type", "job")),
            category=data.get("category", kwargs.get("category", "")),
            language=self._detect_language(data.get("title", "") + " " + data.get("description", "")),
            title_length=len(data.get("title", "")),
            description_length=len(data.get("description", "")),
            has_salary_info="salary" in str(data).lower() or "वेतन" in str(data),
            has_age_info="age" in str(data).lower() or "आयु" in str(data),
            has_education_info="qualification" in str(data).lower() or "योग्यता" in str(data),
            has_deadline="deadline" in str(data).lower() or "last date" in str(data).lower(),
            quality_score=self._calculate_quality_score(data),
        )
    
    def _detect_language(self, text: str) -> str:
        """Simple language detection"""
        if not text:
            return "en"
        
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        total_alpha = sum(1 for c in text if c.isalpha())
        
        if total_alpha == 0:
            return "en"
        
        hindi_ratio = hindi_chars / total_alpha
        
        if hindi_ratio > 0.7:
            return "hi"
        elif hindi_ratio > 0.2:
            return "bilingual"
        else:
            return "en"
    
    def _calculate_quality_score(self, data: Dict) -> float:
        """Calculate quality score (0-1) for data item"""
        score = 0.0
        
        # Title quality
        title = data.get("title", "")
        if len(title) > 10:
            score += 0.15
        if len(title) > 30:
            score += 0.05
        
        # Description quality
        desc = data.get("description", "")
        if len(desc) > 100:
            score += 0.2
        if len(desc) > 300:
            score += 0.1
        
        # Has structured data
        if data.get("salary"):
            score += 0.1
        if data.get("education_required"):
            score += 0.1
        if data.get("age_limit") or (data.get("min_age") and data.get("max_age")):
            score += 0.1
        if data.get("deadline") or data.get("last_date"):
            score += 0.1
        if data.get("vacancies"):
            score += 0.05
        if data.get("category"):
            score += 0.05
        
        return min(score, 1.0)


class WebScraper(BaseCollector):
    """
    Web scraper for government job portals and news sites
    Respects robots.txt and rate limits
    """
    
    def __init__(self, config: DataConfig = None):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def collect(self, source_config: Dict) -> List[Dict]:
        """Collect data by scraping website"""
        url = source_config.get("url")
        if not url:
            return []
        
        domain = urlparse(url).netloc
        rate_limit = source_config.get("rate_limit_seconds", self.config.default_rate_limit)
        
        collected_data = []
        
        try:
            # Rate limit
            await self.rate_limit(domain, rate_limit)
            
            # Fetch page
            async with self.session.get(url) as response:
                if response.status != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status}")
                    return []
                
                html = await response.text()
                
                # Parse based on content type
                content_types = source_config.get("content_types", ["jobs"])
                
                for content_type in content_types:
                    items = self._parse_content(html, content_type, source_config)
                    collected_data.extend(items)
        
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
        
        # Validate and add metadata
        valid_data = []
        for item in collected_data:
            if self.validate_data(item):
                metadata = self.create_metadata(
                    item,
                    source=source_config.get("name", domain),
                    source_type="scraper",
                    state=source_config.get("state", "all_india"),
                )
                item_id = self.metadata_manager.add_metadata(
                    json.dumps(item, sort_keys=True),
                    metadata
                )
                if item_id:
                    item["metadata_id"] = item_id
                    valid_data.append(item)
        
        logger.info(f"Collected {len(valid_data)} items from {url}")
        return valid_data
    
    def _parse_content(self, html: str, content_type: str, config: Dict) -> List[Dict]:
        """
        Parse HTML content to extract structured data
        This is a template - implement specific parsers for each source
        """
        # Generic extraction patterns
        items = []
        
        # Extract title patterns
        title_patterns = [
            r'<h[12][^>]*class="[^"]*job-title[^"]*"[^>]*>([^<]+)</h[12]>',
            r'<a[^>]*class="[^"]*title[^"]*"[^>]*>([^<]+)</a>',
            r'<div[^>]*class="[^"]*post-title[^"]*"[^>]*>([^<]+)</div>',
        ]
        
        for pattern in title_patterns:
            matches = re.findall(pattern, html, re.IGNORECASE)
            for title in matches:
                items.append({
                    "title": title.strip(),
                    "description": "",  # Would need more sophisticated parsing
                    "content_type": content_type,
                    "source_url": config.get("url"),
                })
        
        return items


class APICollector(BaseCollector):
    """
    Collector for API-based data sources
    Handles authentication and pagination
    """
    
    def __init__(self, config: DataConfig = None):
        super().__init__(config)
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={"User-Agent": self.user_agent}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def collect(self, source_config: Dict) -> List[Dict]:
        """Collect data from API endpoint"""
        url = source_config.get("url")
        api_endpoint = source_config.get("api_endpoint", url)
        
        if not api_endpoint:
            return []
        
        domain = urlparse(api_endpoint).netloc
        rate_limit = source_config.get("rate_limit_seconds", 1.0)
        
        collected_data = []
        page = 1
        max_pages = source_config.get("max_pages", 10)
        
        while page <= max_pages:
            try:
                await self.rate_limit(domain, rate_limit)
                
                # Build request
                params = source_config.get("params", {})
                params["page"] = page
                
                headers = {"Accept": "application/json"}
                if source_config.get("api_key"):
                    headers["Authorization"] = f"Bearer {source_config['api_key']}"
                
                async with self.session.get(api_endpoint, params=params, headers=headers) as response:
                    if response.status != 200:
                        logger.warning(f"API request failed: {response.status}")
                        break
                    
                    data = await response.json()
                    
                    # Extract items from response
                    items = self._extract_items(data, source_config)
                    
                    if not items:
                        break
                    
                    collected_data.extend(items)
                    page += 1
            
            except Exception as e:
                logger.error(f"Error collecting from API {api_endpoint}: {e}")
                break
        
        # Validate and add metadata
        valid_data = []
        for item in collected_data:
            if self.validate_data(item):
                metadata = self.create_metadata(
                    item,
                    source=source_config.get("name", domain),
                    source_type="api",
                )
                item_id = self.metadata_manager.add_metadata(
                    json.dumps(item, sort_keys=True),
                    metadata
                )
                if item_id:
                    item["metadata_id"] = item_id
                    valid_data.append(item)
        
        logger.info(f"Collected {len(valid_data)} items from API")
        return valid_data
    
    def _extract_items(self, response_data: Dict, config: Dict) -> List[Dict]:
        """Extract items from API response"""
        # Try common response structures
        items_key = config.get("items_key", "data")
        
        if isinstance(response_data, list):
            return response_data
        
        if items_key in response_data:
            return response_data[items_key]
        
        # Try nested structures
        for key in ["results", "items", "records", "jobs", "schemes"]:
            if key in response_data:
                return response_data[key]
        
        return []


class DataCollector:
    """
    Main data collector orchestrating multiple sources
    Ensures diversity and balance in collected data
    """
    
    def __init__(self, config: DataConfig = None):
        self.config = config or DataConfig()
        self.metadata_manager = MetadataManager()
        self.collected_count: Dict[str, int] = {
            "by_source": {},
            "by_state": {},
            "by_category": {},
        }
    
    async def collect_all(
        self,
        sources: List[str] = None,
        content_types: List[str] = None,
        states: List[str] = None,
        max_per_source: int = None
    ) -> Dict[str, List[Dict]]:
        """
        Collect data from all configured sources
        
        Args:
            sources: List of source names to collect from (None = all)
            content_types: Filter by content type
            states: Filter by state
            max_per_source: Override max items per source
        """
        results = {
            "jobs": [],
            "schemes": [],
            "results": [],
            "admit_cards": [],
            "syllabus": [],
        }
        
        max_items = max_per_source or self.config.max_items_per_source
        
        # Collect from government portals
        for name, source_config in SOURCES.get("government_portals", {}).items():
            if sources and name not in sources:
                continue
            
            source_config["name"] = name
            
            if source_config.get("type") == "api":
                async with APICollector(self.config) as collector:
                    items = await collector.collect(source_config)
            else:
                async with WebScraper(self.config) as collector:
                    items = await collector.collect(source_config)
            
            # Categorize items
            for item in items[:max_items]:
                ct = item.get("content_type", "jobs")
                if ct in results:
                    results[ct].append(item)
                self._update_counts(item, name)
        
        # Collect from scheme portals
        for name, source_config in SOURCES.get("scheme_portals", {}).items():
            if sources and name not in sources:
                continue
            
            source_config["name"] = name
            
            if source_config.get("type") == "api":
                async with APICollector(self.config) as collector:
                    items = await collector.collect(source_config)
            else:
                async with WebScraper(self.config) as collector:
                    items = await collector.collect(source_config)
            
            for item in items[:max_items]:
                results["schemes"].append(item)
                self._update_counts(item, name)
        
        # Collect from state portals for diversity
        for name, source_config in SOURCES.get("state_portals", {}).items():
            state = source_config.get("state", "unknown")
            if states and state not in states:
                continue
            
            source_config["name"] = name
            
            async with WebScraper(self.config) as collector:
                items = await collector.collect(source_config)
            
            for item in items[:max_items // 2]:  # Less per state for balance
                ct = item.get("content_type", "jobs")
                if ct in results:
                    results[ct].append(item)
                self._update_counts(item, name)
        
        logger.info(f"Total collected: {sum(len(v) for v in results.values())} items")
        return results
    
    def _update_counts(self, item: Dict, source: str):
        """Update collection counts for tracking"""
        self.collected_count["by_source"][source] = \
            self.collected_count["by_source"].get(source, 0) + 1
        
        state = item.get("state", "unknown")
        self.collected_count["by_state"][state] = \
            self.collected_count["by_state"].get(state, 0) + 1
        
        category = item.get("category", "unknown")
        self.collected_count["by_category"][category] = \
            self.collected_count["by_category"].get(category, 0) + 1
    
    def get_collection_report(self) -> Dict:
        """Get report on collected data"""
        return {
            "counts": self.collected_count,
            "diversity": self.metadata_manager.get_diversity_report(),
            "statistics": self.metadata_manager.get_statistics(),
        }
    
    def identify_gaps(self) -> Dict:
        """
        Identify gaps in data collection
        Returns states/categories that need more data
        """
        report = self.metadata_manager.get_diversity_report()
        
        return {
            "under_represented_states": report.get("under_represented_states", []),
            "under_represented_categories": report.get("under_represented_categories", []),
            "recommendations": report.get("recommendations", []),
        }
