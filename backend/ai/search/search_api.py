"""
DS-Search API Integration (Optional)
====================================
Optional paid search API integration.
DISABLED BY DEFAULT - Free crawler is preferred.

Supported APIs (when enabled):
- Google Custom Search API
- Bing Search API
- SerpAPI

To enable: Admin must explicitly turn on via admin panel
and provide API credentials.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


@dataclass
class SearchAPIConfig:
    """Configuration for search API"""
    enabled: bool = False  # DISABLED BY DEFAULT
    api_type: str = "none"  # google, bing, serpapi, none
    api_key: str = ""
    daily_limit: int = 100
    cost_per_query: float = 0.0
    current_usage: int = 0


class SearchAPIProvider(ABC):
    """Abstract base class for search API providers"""
    
    @abstractmethod
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Execute a search query"""
        pass
    
    @abstractmethod
    def get_remaining_quota(self) -> int:
        """Get remaining daily quota"""
        pass


class DisabledSearchAPI(SearchAPIProvider):
    """
    Placeholder for disabled search API.
    Always returns empty results and logs that API is disabled.
    """
    
    def __init__(self):
        logger.info("Search API is DISABLED (free mode)")
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Returns empty - API is disabled"""
        logger.debug(f"Search API disabled - skipping query: {query[:50]}...")
        return []
    
    def get_remaining_quota(self) -> int:
        return 0


class GoogleSearchAPI(SearchAPIProvider):
    """
    Google Custom Search API integration.
    Requires: API Key + Custom Search Engine ID
    Cost: ~$5 per 1000 queries
    """
    
    def __init__(self, api_key: str, cx: str, daily_limit: int = 100):
        self.api_key = api_key
        self.cx = cx  # Custom Search Engine ID
        self.daily_limit = daily_limit
        self.queries_today = 0
        logger.info("Google Search API initialized")
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Execute Google Custom Search"""
        if self.queries_today >= self.daily_limit:
            logger.warning("Google API daily limit reached")
            return []
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://www.googleapis.com/customsearch/v1",
                    params={
                        "key": self.api_key,
                        "cx": self.cx,
                        "q": query,
                        "num": min(num_results, 10)
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Google API error: {response.status_code}")
                    return []
                
                data = response.json()
                self.queries_today += 1
                
                results = []
                for item in data.get('items', []):
                    results.append({
                        "title": item.get('title', ''),
                        "url": item.get('link', ''),
                        "snippet": item.get('snippet', ''),
                        "source": "google_api"
                    })
                
                logger.info(f"Google API returned {len(results)} results")
                return results
                
        except ImportError:
            logger.error("httpx not installed for Google API")
            return []
        except Exception as e:
            logger.error(f"Google API error: {e}")
            return []
    
    def get_remaining_quota(self) -> int:
        return max(0, self.daily_limit - self.queries_today)


class BingSearchAPI(SearchAPIProvider):
    """
    Bing Web Search API integration.
    Requires: API Key
    Cost: ~$3 per 1000 queries (free tier available)
    """
    
    def __init__(self, api_key: str, daily_limit: int = 1000):
        self.api_key = api_key
        self.daily_limit = daily_limit
        self.queries_today = 0
        logger.info("Bing Search API initialized")
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Execute Bing Web Search"""
        if self.queries_today >= self.daily_limit:
            logger.warning("Bing API daily limit reached")
            return []
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    "https://api.bing.microsoft.com/v7.0/search",
                    headers={"Ocp-Apim-Subscription-Key": self.api_key},
                    params={
                        "q": query,
                        "count": min(num_results, 50),
                        "mkt": "en-IN"  # India market
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"Bing API error: {response.status_code}")
                    return []
                
                data = response.json()
                self.queries_today += 1
                
                results = []
                for page in data.get('webPages', {}).get('value', []):
                    results.append({
                        "title": page.get('name', ''),
                        "url": page.get('url', ''),
                        "snippet": page.get('snippet', ''),
                        "source": "bing_api"
                    })
                
                logger.info(f"Bing API returned {len(results)} results")
                return results
                
        except ImportError:
            logger.error("httpx not installed for Bing API")
            return []
        except Exception as e:
            logger.error(f"Bing API error: {e}")
            return []
    
    def get_remaining_quota(self) -> int:
        return max(0, self.daily_limit - self.queries_today)


class SerpAPIProvider(SearchAPIProvider):
    """
    SerpAPI integration (Google results scraper).
    Requires: API Key
    Cost: ~$50 per 5000 queries
    """
    
    def __init__(self, api_key: str, daily_limit: int = 100):
        self.api_key = api_key
        self.daily_limit = daily_limit
        self.queries_today = 0
        logger.info("SerpAPI initialized")
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Execute SerpAPI search"""
        if self.queries_today >= self.daily_limit:
            logger.warning("SerpAPI daily limit reached")
            return []
        
        try:
            import httpx
            
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(
                    "https://serpapi.com/search",
                    params={
                        "api_key": self.api_key,
                        "q": query,
                        "num": min(num_results, 10),
                        "gl": "in",  # India
                        "hl": "hi"   # Hindi
                    }
                )
                
                if response.status_code != 200:
                    logger.error(f"SerpAPI error: {response.status_code}")
                    return []
                
                data = response.json()
                self.queries_today += 1
                
                results = []
                for item in data.get('organic_results', []):
                    results.append({
                        "title": item.get('title', ''),
                        "url": item.get('link', ''),
                        "snippet": item.get('snippet', ''),
                        "source": "serpapi"
                    })
                
                logger.info(f"SerpAPI returned {len(results)} results")
                return results
                
        except ImportError:
            logger.error("httpx not installed for SerpAPI")
            return []
        except Exception as e:
            logger.error(f"SerpAPI error: {e}")
            return []
    
    def get_remaining_quota(self) -> int:
        return max(0, self.daily_limit - self.queries_today)


class SearchAPIManager:
    """
    Manager for search API providers.
    Handles configuration, selection, and usage tracking.
    """
    
    def __init__(self, config: SearchAPIConfig = None):
        self.config = config or SearchAPIConfig()
        self.provider: SearchAPIProvider = DisabledSearchAPI()
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize the configured provider"""
        if not self.config.enabled:
            self.provider = DisabledSearchAPI()
            return
        
        if self.config.api_type == "google" and self.config.api_key:
            # Would need CX (Custom Search Engine ID) as well
            self.provider = DisabledSearchAPI()  # Placeholder
            logger.warning("Google API needs CX parameter")
        
        elif self.config.api_type == "bing" and self.config.api_key:
            self.provider = BingSearchAPI(
                api_key=self.config.api_key,
                daily_limit=self.config.daily_limit
            )
        
        elif self.config.api_type == "serpapi" and self.config.api_key:
            self.provider = SerpAPIProvider(
                api_key=self.config.api_key,
                daily_limit=self.config.daily_limit
            )
        
        else:
            self.provider = DisabledSearchAPI()
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """Execute search using configured provider"""
        return await self.provider.search(query, num_results)
    
    def is_enabled(self) -> bool:
        """Check if API is enabled"""
        return self.config.enabled
    
    def get_remaining_quota(self) -> int:
        """Get remaining daily quota"""
        return self.provider.get_remaining_quota()
    
    def get_status(self) -> Dict:
        """Get API status information"""
        return {
            "enabled": self.config.enabled,
            "api_type": self.config.api_type,
            "remaining_quota": self.get_remaining_quota(),
            "daily_limit": self.config.daily_limit
        }
    
    def enable(self, api_type: str, api_key: str, daily_limit: int = 100):
        """Enable search API (admin only)"""
        self.config.enabled = True
        self.config.api_type = api_type
        self.config.api_key = api_key
        self.config.daily_limit = daily_limit
        self._initialize_provider()
        logger.info(f"Search API enabled: {api_type}")
    
    def disable(self):
        """Disable search API"""
        self.config.enabled = False
        self.provider = DisabledSearchAPI()
        logger.info("Search API disabled")


# Singleton instance - DISABLED by default
_api_manager: Optional[SearchAPIManager] = None

def get_api_manager() -> SearchAPIManager:
    """Get or create API manager (disabled by default)"""
    global _api_manager
    if _api_manager is None:
        _api_manager = SearchAPIManager()  # Disabled by default
    return _api_manager
