"""
Base Scraper Class
Template for creating source-specific scrapers
"""

import asyncio
import aiohttp
import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from urllib.parse import urlparse, urljoin
import time

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """
    Base class for all scrapers
    Implements robots.txt compliance, rate limiting, and error handling
    """
    
    def __init__(
        self,
        base_url: str,
        rate_limit: float = 2.0,
        max_retries: int = 3,
        user_agent: str = "DigitalSahayakBot/1.0"
    ):
        self.base_url = base_url
        self.domain = urlparse(base_url).netloc
        self.rate_limit = rate_limit
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.last_request_time = 0
        self.session: Optional[aiohttp.ClientSession] = None
        
        # Robots.txt cache
        self._robots_rules: Optional[Dict] = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9",
                "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
            }
        )
        await self._load_robots_txt()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def _load_robots_txt(self):
        """Load and parse robots.txt"""
        robots_url = urljoin(self.base_url, "/robots.txt")
        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    text = await response.text()
                    self._robots_rules = self._parse_robots_txt(text)
                    logger.info(f"Loaded robots.txt from {self.domain}")
        except Exception as e:
            logger.warning(f"Could not load robots.txt: {e}")
            self._robots_rules = {}
    
    def _parse_robots_txt(self, content: str) -> Dict:
        """Parse robots.txt content"""
        rules = {
            "disallow": [],
            "allow": [],
            "crawl_delay": self.rate_limit,
        }
        
        current_agent = None
        
        for line in content.split("\n"):
            line = line.strip().lower()
            
            if line.startswith("user-agent:"):
                agent = line.split(":", 1)[1].strip()
                if agent == "*" or "digitalsahayak" in agent:
                    current_agent = agent
            
            elif current_agent and line.startswith("disallow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    rules["disallow"].append(path)
            
            elif current_agent and line.startswith("allow:"):
                path = line.split(":", 1)[1].strip()
                if path:
                    rules["allow"].append(path)
            
            elif current_agent and line.startswith("crawl-delay:"):
                try:
                    delay = float(line.split(":", 1)[1].strip())
                    rules["crawl_delay"] = max(delay, self.rate_limit)
                except ValueError:
                    pass
        
        return rules
    
    def can_fetch(self, path: str) -> bool:
        """Check if path is allowed by robots.txt"""
        if not self._robots_rules:
            return True
        
        # Check allowed paths first
        for allowed in self._robots_rules.get("allow", []):
            if path.startswith(allowed):
                return True
        
        # Check disallowed paths
        for disallowed in self._robots_rules.get("disallow", []):
            if path.startswith(disallowed):
                return False
        
        return True
    
    async def wait_rate_limit(self):
        """Wait to respect rate limit"""
        delay = self._robots_rules.get("crawl_delay", self.rate_limit) if self._robots_rules else self.rate_limit
        
        elapsed = time.time() - self.last_request_time
        if elapsed < delay:
            await asyncio.sleep(delay - elapsed)
        
        self.last_request_time = time.time()
    
    async def fetch(self, url: str, retry: int = 0) -> Optional[str]:
        """
        Fetch URL with rate limiting and retry logic
        """
        path = urlparse(url).path
        
        if not self.can_fetch(path):
            logger.warning(f"URL blocked by robots.txt: {url}")
            return None
        
        await self.wait_rate_limit()
        
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    return await response.text()
                elif response.status == 429:  # Too Many Requests
                    if retry < self.max_retries:
                        wait_time = int(response.headers.get("Retry-After", 60))
                        logger.warning(f"Rate limited. Waiting {wait_time}s")
                        await asyncio.sleep(wait_time)
                        return await self.fetch(url, retry + 1)
                else:
                    logger.warning(f"HTTP {response.status} for {url}")
                    return None
        
        except aiohttp.ClientError as e:
            if retry < self.max_retries:
                logger.warning(f"Request failed, retrying: {e}")
                await asyncio.sleep(5 * (retry + 1))
                return await self.fetch(url, retry + 1)
            logger.error(f"Request failed after retries: {e}")
            return None
    
    @abstractmethod
    async def scrape(self) -> List[Dict]:
        """
        Scrape data from source
        Must be implemented by subclasses
        """
        pass
    
    @abstractmethod
    def parse_item(self, html: str) -> Optional[Dict]:
        """
        Parse a single item from HTML
        Must be implemented by subclasses
        """
        pass
