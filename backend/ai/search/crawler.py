"""
DS-Search Crawler
=================
Free web crawler for targeted information retrieval.

Features:
- Async HTTP requests with httpx
- BeautifulSoup for HTML parsing
- Respects rate limits per domain
- Extracts structured data from pages
- Handles multiple content types
- Incremental crawling support
"""

import asyncio
import re
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse
import hashlib

try:
    import httpx
    from bs4 import BeautifulSoup
    CRAWLER_AVAILABLE = True
except ImportError:
    CRAWLER_AVAILABLE = False

try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result from crawling a single page"""
    url: str
    title: str
    content: str
    snippet: str
    domain: str
    crawled_at: datetime
    success: bool
    content_type: str = "html"
    metadata: Dict = field(default_factory=dict)
    links: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "content": self.content[:2000],  # Truncate for storage
            "snippet": self.snippet,
            "domain": self.domain,
            "crawled_at": self.crawled_at.isoformat(),
            "success": self.success,
            "content_type": self.content_type,
            "metadata": self.metadata
        }


@dataclass
class CrawlPlan:
    """Configuration for a crawl operation"""
    queries: List[str]
    domains: List[str] = field(default_factory=list)
    max_pages: int = 5
    timeout: float = 10.0
    prefer_official: bool = True
    specific_url: Optional[str] = None
    follow_links: bool = False
    max_depth: int = 1


class DSCrawler:
    """
    Intelligent web crawler for DS-Search.
    Uses free methods: DuckDuckGo + direct HTTP requests.
    """
    
    # Default headers to mimic browser
    DEFAULT_HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }
    
    # Content extraction selectors (by domain patterns)
    EXTRACTION_RULES = {
        "default": {
            "title": ["h1", "title", ".page-title", "#title"],
            "content": ["article", "main", ".content", "#content", ".post-content", "body"],
            "date": [".date", ".published", "time", ".post-date"],
            "remove": ["script", "style", "nav", "header", "footer", "aside", ".sidebar", ".ads", ".advertisement"]
        },
        "gov.in": {
            "title": ["h1", ".page-title", "#page-title", "title"],
            "content": [".content-area", "#content", "main", ".main-content", "article"],
            "date": [".date", ".last-updated", "time"],
            "remove": ["script", "style", "nav", "header", "footer", ".menu", ".breadcrumb"]
        },
        "sarkariresult": {
            "title": ["h1", ".post-title"],
            "content": [".job-info", ".post-content", "article"],
            "date": [".date"],
            "remove": ["script", "style", "nav", ".sidebar", ".ads"]
        }
    }
    
    def __init__(self, sources_manager=None):
        self.sources = sources_manager
        self.domain_last_request: Dict[str, float] = {}  # Rate limiting
        self.session: Optional[httpx.AsyncClient] = None
    
    async def _get_session(self) -> httpx.AsyncClient:
        """Get or create HTTP session"""
        if self.session is None or self.session.is_closed:
            self.session = httpx.AsyncClient(
                timeout=15.0,
                follow_redirects=True,
                headers=self.DEFAULT_HEADERS
            )
        return self.session
    
    async def close(self):
        """Close the HTTP session"""
        if self.session and not self.session.is_closed:
            await self.session.aclose()
    
    async def _respect_rate_limit(self, domain: str):
        """Wait if needed to respect rate limit"""
        import time
        
        rate_limit = 1.0  # Default: 1 request per second
        if self.sources:
            rate_limit = self.sources.get_rate_limit(domain)
        
        min_interval = 1.0 / rate_limit
        
        if domain in self.domain_last_request:
            elapsed = time.time() - self.domain_last_request[domain]
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
        
        self.domain_last_request[domain] = time.time()
    
    def _get_extraction_rules(self, domain: str) -> Dict:
        """Get extraction rules for a domain"""
        domain_lower = domain.lower()
        
        if domain_lower.endswith('.gov.in') or domain_lower.endswith('.nic.in'):
            return self.EXTRACTION_RULES['gov.in']
        
        if 'sarkari' in domain_lower:
            return self.EXTRACTION_RULES['sarkariresult']
        
        return self.EXTRACTION_RULES['default']
    
    def _extract_content(self, html: str, url: str) -> Dict:
        """Extract structured content from HTML"""
        if not CRAWLER_AVAILABLE:
            return {"title": "", "content": "", "snippet": "", "links": []}
        
        soup = BeautifulSoup(html, 'html.parser')
        domain = urlparse(url).netloc
        rules = self._get_extraction_rules(domain)
        
        # Remove unwanted elements
        for selector in rules['remove']:
            for element in soup.select(selector):
                element.decompose()
        
        # Extract title
        title = ""
        for selector in rules['title']:
            elem = soup.select_one(selector)
            if elem:
                title = elem.get_text(strip=True)
                break
        
        if not title:
            title_tag = soup.find('title')
            title = title_tag.get_text(strip=True) if title_tag else ""
        
        # Extract main content
        content = ""
        for selector in rules['content']:
            elem = soup.select_one(selector)
            if elem:
                content = elem.get_text(separator=' ', strip=True)
                break
        
        if not content:
            content = soup.get_text(separator=' ', strip=True)
        
        # Clean content
        content = re.sub(r'\s+', ' ', content)
        content = content[:10000]  # Limit content size
        
        # Generate snippet
        snippet = content[:300] + "..." if len(content) > 300 else content
        
        # Extract important links
        links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.get_text(strip=True).lower()
            
            # Only keep relevant links
            if any(kw in text for kw in ['apply', 'download', 'result', 'notification', 'official', 'pdf']):
                full_url = urljoin(url, href)
                if full_url.startswith('http'):
                    links.append(full_url)
        
        # Extract metadata
        metadata = {}
        
        # Extract dates
        for selector in rules['date']:
            date_elem = soup.select_one(selector)
            if date_elem:
                metadata['date'] = date_elem.get_text(strip=True)
                break
        
        # Extract meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc:
            metadata['meta_description'] = meta_desc.get('content', '')
        
        return {
            "title": title,
            "content": content,
            "snippet": snippet,
            "links": links[:10],  # Top 10 relevant links
            "metadata": metadata
        }
    
    async def crawl_url(self, url: str) -> CrawlResult:
        """
        Crawl a single URL and extract content.
        
        Args:
            url: URL to crawl
            
        Returns:
            CrawlResult with extracted data
        """
        domain = urlparse(url).netloc
        
        # Check if blocked
        if self.sources and self.sources.is_blocked(domain):
            logger.warning(f"Blocked domain: {domain}")
            return CrawlResult(
                url=url,
                title="",
                content="",
                snippet="",
                domain=domain,
                crawled_at=datetime.now(timezone.utc),
                success=False,
                metadata={"error": "blocked_domain"}
            )
        
        # Respect rate limit
        await self._respect_rate_limit(domain)
        
        try:
            session = await self._get_session()
            response = await session.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to crawl {url}: HTTP {response.status_code}")
                return CrawlResult(
                    url=url,
                    title="",
                    content="",
                    snippet="",
                    domain=domain,
                    crawled_at=datetime.now(timezone.utc),
                    success=False,
                    metadata={"error": f"http_{response.status_code}"}
                )
            
            # Check content type
            content_type = response.headers.get('content-type', '')
            
            if 'application/pdf' in content_type:
                # PDF handling (just return URL, no extraction)
                return CrawlResult(
                    url=url,
                    title=url.split('/')[-1],
                    content="PDF Document",
                    snippet="PDF file available for download",
                    domain=domain,
                    crawled_at=datetime.now(timezone.utc),
                    success=True,
                    content_type="pdf",
                    metadata={"is_pdf": True}
                )
            
            # Extract content from HTML
            extracted = self._extract_content(response.text, url)
            
            # Update source stats
            if self.sources:
                self.sources.update_crawl_stats(domain, True)
            
            return CrawlResult(
                url=url,
                title=extracted['title'],
                content=extracted['content'],
                snippet=extracted['snippet'],
                domain=domain,
                crawled_at=datetime.now(timezone.utc),
                success=True,
                links=extracted['links'],
                metadata=extracted['metadata']
            )
            
        except Exception as e:
            logger.error(f"Crawl error for {url}: {e}")
            
            if self.sources:
                self.sources.update_crawl_stats(domain, False)
            
            return CrawlResult(
                url=url,
                title="",
                content="",
                snippet="",
                domain=domain,
                crawled_at=datetime.now(timezone.utc),
                success=False,
                metadata={"error": str(e)}
            )
    
    async def search_duckduckgo(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search using DuckDuckGo (free).
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            List of search results
        """
        if not DDGS_AVAILABLE:
            logger.warning("DuckDuckGo search not available - install duckduckgo-search")
            return []
        
        try:
            def sync_search():
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                    return results
            
            # Run in thread pool to not block
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(None, sync_search)
            
            formatted_results = []
            for r in results:
                formatted_results.append({
                    "title": r.get("title", ""),
                    "url": r.get("href", r.get("link", "")),
                    "snippet": r.get("body", r.get("snippet", "")),
                    "source": "duckduckgo"
                })
            
            logger.info(f"DuckDuckGo found {len(formatted_results)} results for: {query[:50]}...")
            return formatted_results
            
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []
    
    async def search_and_crawl(self, query: str, plan: CrawlPlan = None) -> List[CrawlResult]:
        """
        Search for query and crawl top results.
        
        Args:
            query: Search query
            plan: Crawl plan configuration
            
        Returns:
            List of CrawlResults with extracted content
        """
        if plan is None:
            plan = CrawlPlan(queries=[query])
        
        results = []
        urls_crawled: Set[str] = set()
        
        # If specific URL provided, crawl it directly
        if plan.specific_url:
            result = await self.crawl_url(plan.specific_url)
            if result.success:
                results.append(result)
            return results
        
        # Search with all queries
        all_search_results = []
        for search_query in plan.queries[:4]:  # Max 4 queries
            search_results = await self.search_duckduckgo(search_query, max_results=plan.max_pages)
            all_search_results.extend(search_results)
        
        # Deduplicate by URL
        seen_urls = set()
        unique_results = []
        for r in all_search_results:
            url = r.get('url', '')
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(r)
        
        # Filter by trusted domains if prefer_official
        if plan.prefer_official and plan.domains:
            # First add results from preferred domains
            prioritized = []
            others = []
            
            for r in unique_results:
                url = r.get('url', '')
                domain = urlparse(url).netloc.lower()
                
                # Check if domain matches any preferred domain
                is_preferred = any(
                    pref_domain in domain 
                    for pref_domain in plan.domains
                )
                
                if is_preferred:
                    prioritized.append(r)
                else:
                    others.append(r)
            
            unique_results = prioritized + others
        
        # Crawl top results
        for search_result in unique_results[:plan.max_pages]:
            url = search_result.get('url', '')
            
            if not url or url in urls_crawled:
                continue
            
            urls_crawled.add(url)
            
            crawl_result = await self.crawl_url(url)
            
            # If we got a search snippet but crawl failed, use search data
            if not crawl_result.success:
                crawl_result.title = search_result.get('title', '')
                crawl_result.snippet = search_result.get('snippet', '')
                crawl_result.content = crawl_result.snippet
            
            results.append(crawl_result)
            
            # Add small delay between requests
            await asyncio.sleep(0.5)
        
        logger.info(f"Crawled {len(results)} pages for query")
        return results
    
    async def crawl_specific_domains(self, query: str, domains: List[str], 
                                     max_per_domain: int = 2) -> List[CrawlResult]:
        """
        Crawl specific domains for a query.
        
        Args:
            query: Search query
            domains: List of domains to crawl
            max_per_domain: Max pages per domain
            
        Returns:
            List of CrawlResults
        """
        results = []
        
        for domain in domains[:5]:  # Max 5 domains
            # Create site-specific query
            site_query = f"site:{domain} {query}"
            
            search_results = await self.search_duckduckgo(site_query, max_results=max_per_domain)
            
            for sr in search_results:
                url = sr.get('url', '')
                if url:
                    result = await self.crawl_url(url)
                    if result.success:
                        results.append(result)
                    
                    await asyncio.sleep(0.5)
        
        return results
    
    async def fetch_and_summarize(self, url: str) -> Dict:
        """
        Fetch a URL and return summarized content.
        
        Args:
            url: URL to fetch
            
        Returns:
            Dict with title, summary, key_points
        """
        result = await self.crawl_url(url)
        
        if not result.success:
            return {
                "success": False,
                "error": result.metadata.get('error', 'Unknown error'),
                "url": url
            }
        
        # Extract key points (simple heuristic)
        content = result.content
        key_points = []
        
        # Look for important patterns
        patterns = [
            r'(?:last date|अंतिम तिथि)[:\s]*([^\n.]{10,100})',
            r'(?:eligibility|पात्रता)[:\s]*([^\n.]{10,150})',
            r'(?:salary|वेतन)[:\s]*([^\n.]{10,100})',
            r'(?:age limit|आयु सीमा)[:\s]*([^\n.]{10,100})',
            r'(?:apply|आवेदन)[:\s]*([^\n.]{10,100})',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            key_points.extend(matches[:2])
        
        return {
            "success": True,
            "url": url,
            "title": result.title,
            "summary": result.snippet,
            "content": result.content[:3000],
            "key_points": key_points[:5],
            "links": result.links,
            "metadata": result.metadata
        }


# Singleton instance
_crawler_instance: Optional[DSCrawler] = None

async def get_crawler_instance(sources_manager=None) -> DSCrawler:
    """Get or create crawler instance"""
    global _crawler_instance
    if _crawler_instance is None:
        _crawler_instance = DSCrawler(sources_manager)
    return _crawler_instance
