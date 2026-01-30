"""
DS-Search Main Orchestrator
===========================
Central orchestrator that coordinates all DS-Search components.

Flow:
1. Receive user query
2. Policy check (should we search?)
3. Check cache (hit → return)
4. Generate optimized queries
5. Execute search (crawler first, API optional)
6. Extract facts (Evidence Extractor)
7. Rank results
8. Generate natural response (DS-Talk)
9. Cache and return

Priority Order (Free-First):
1. Local DB / internal index
2. Cached search results
3. Trusted Crawler (FREE)
4. Search API (PAID - disabled by default)
"""

import logging
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime, timezone

from .policy import SearchPolicy, PolicyDecision, SearchIntent, get_policy_instance
from .querygen import QueryGenerator, GeneratedQuery, get_querygen_instance
from .sources import TrustedSources, get_sources_instance
from .crawler import DSCrawler, CrawlPlan, CrawlResult, get_crawler_instance
from .search_api import SearchAPIManager, get_api_manager
from .ranker import ResultRanker, RankedResult, get_ranker_instance
from .cache import SearchCache, get_cache_instance

# Evidence Extractor and DS-Talk integration
try:
    from ai.evidence import EvidenceExtractor, Facts, extract_facts
    EVIDENCE_AVAILABLE = True
except ImportError:
    EVIDENCE_AVAILABLE = False

try:
    from ai.nlg import DSTalk, compose_answer
    NLG_AVAILABLE = True
except ImportError:
    NLG_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class SearchResponse:
    """Response from DS-Search"""
    success: bool
    query: str
    results: List[RankedResult]
    formatted_response: str
    source: str  # "cache", "crawler", "api", "internal", "none"
    search_score: float
    intent: str
    metadata: Dict
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "query": self.query,
            "results": [r.to_dict() for r in self.results],
            "formatted_response": self.formatted_response,
            "source": self.source,
            "search_score": self.search_score,
            "intent": self.intent,
            "metadata": self.metadata
        }


class DSSearch:
    """
    Main DS-Search orchestrator.
    Coordinates policy, query generation, crawling, ranking, and caching.
    """
    
    VERSION = "1.0.0"
    
    def __init__(self, db=None):
        self.db = db
        
        # Components (will be initialized lazily)
        self._policy: Optional[SearchPolicy] = None
        self._querygen: Optional[QueryGenerator] = None
        self._sources: Optional[TrustedSources] = None
        self._crawler: Optional[DSCrawler] = None
        self._api_manager: Optional[SearchAPIManager] = None
        self._ranker: Optional[ResultRanker] = None
        self._cache: Optional[SearchCache] = None
        
        self._initialized = False
        
        # Search logs (for analytics)
        self.search_logs: List[Dict] = []
        
        logger.info(f"DS-Search v{self.VERSION} created")
    
    async def initialize(self, db=None):
        """Initialize all components"""
        if self._initialized:
            return
        
        if db:
            self.db = db
        
        # Initialize components
        self._policy = get_policy_instance(self.db)
        self._querygen = get_querygen_instance()
        self._sources = await get_sources_instance(self.db)
        self._crawler = await get_crawler_instance(self._sources)
        self._api_manager = get_api_manager()
        self._ranker = get_ranker_instance(self._sources)
        self._cache = await get_cache_instance(self.db)
        
        self._initialized = True
        logger.info(f"DS-Search v{self.VERSION} initialized")
    
    async def search(self, query: str, user_id: str = None, 
                     user_context: Dict = None, language: str = "hi") -> SearchResponse:
        """
        Main search method - handles user query end-to-end.
        
        Args:
            query: User's search query
            user_id: User identifier for rate limiting
            user_context: Additional context (profile, preferences)
            language: Response language (hi/en)
            
        Returns:
            SearchResponse with results and formatted response
        """
        await self.initialize()
        
        start_time = datetime.now(timezone.utc)
        
        # Step 1: Policy check
        policy_decision = self._policy.evaluate(
            query=query,
            user_id=user_id,
            internal_results_count=0  # Will be updated if we check internal DB
        )
        
        # Log search attempt
        log_entry = {
            "query": query,
            "user_id": user_id,
            "timestamp": start_time.isoformat(),
            "intent": policy_decision.intent.value,
            "search_score": policy_decision.search_score
        }
        
        # Check if search should be blocked
        if not policy_decision.should_search:
            log_entry["action"] = "blocked"
            log_entry["reason"] = policy_decision.reason
            self._log_search(log_entry)
            
            return SearchResponse(
                success=False,
                query=query,
                results=[],
                formatted_response=self._get_no_search_response(policy_decision, language),
                source="none",
                search_score=policy_decision.search_score,
                intent=policy_decision.intent.value,
                metadata={"reason": policy_decision.reason}
            )
        
        # Step 2: Check cache
        cached_results = await self._cache.get(query)
        if cached_results:
            log_entry["action"] = "cache_hit"
            self._log_search(log_entry)
            
            # Re-rank cached results
            ranked = self._ranker.rank(cached_results, query)
            top_results = self._ranker.get_top_results(ranked)
            
            return SearchResponse(
                success=True,
                query=query,
                results=top_results,
                formatted_response=self._ranker.format_for_response(top_results, language),
                source="cache",
                search_score=policy_decision.search_score,
                intent=policy_decision.intent.value,
                metadata={"cache_hit": True}
            )
        
        # Step 3: Generate optimized queries
        query_type = self._get_query_type_from_intent(policy_decision.intent)
        generated_queries = self._querygen.generate(query, query_type)
        
        # Step 4: Get crawl plan
        crawl_plan = self._policy.choose_crawl_plan(policy_decision.intent, query)
        crawl_plan_obj = CrawlPlan(
            queries=[gq.text for gq in generated_queries[:3]],
            domains=crawl_plan.get('domains', []),
            max_pages=crawl_plan.get('max_pages', 5),
            timeout=crawl_plan.get('timeout', 10),
            prefer_official=crawl_plan.get('prefer_official', True),
            specific_url=crawl_plan.get('specific_url')
        )
        
        # Step 5: Execute crawler (FREE)
        crawl_results = await self._crawler.search_and_crawl(
            query=generated_queries[0].text if generated_queries else query,
            plan=crawl_plan_obj
        )
        
        results_source = "crawler"
        
        # Step 6: If crawler fails and API is enabled, try API
        if not crawl_results and self._api_manager.is_enabled():
            api_results = await self._api_manager.search(
                generated_queries[0].text if generated_queries else query,
                num_results=5
            )
            if api_results:
                crawl_results = [
                    CrawlResult(
                        url=r['url'],
                        title=r['title'],
                        content=r.get('snippet', ''),
                        snippet=r.get('snippet', ''),
                        domain='',
                        crawled_at=datetime.now(timezone.utc),
                        success=True
                    )
                    for r in api_results
                ]
                results_source = "api"
        
        # Step 7: Rank results
        query_keywords = [gq.text.split()[0] for gq in generated_queries if gq.text]
        ranked_results = self._ranker.rank(
            [r.to_dict() for r in crawl_results],
            query,
            query_keywords
        )
        
        # Get top results
        top_results = self._ranker.get_top_results(ranked_results, min_score=0.40)
        
        # Step 8: Cache results
        if top_results:
            await self._cache.put(
                query=query,
                results=[r.to_dict() for r in top_results],
                source=results_source
            )
        
        # Update rate limit
        if user_id:
            self._policy.increment_search_count(user_id)
        
        # Log success
        log_entry["action"] = "search_complete"
        log_entry["source"] = results_source
        log_entry["results_count"] = len(top_results)
        log_entry["duration_ms"] = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
        self._log_search(log_entry)
        
        # Format response
        if top_results:
            formatted = self._ranker.format_for_response(top_results, language)
        else:
            formatted = self._get_not_found_response(query, language)
        
        return SearchResponse(
            success=len(top_results) > 0,
            query=query,
            results=top_results,
            formatted_response=formatted,
            source=results_source,
            search_score=policy_decision.search_score,
            intent=policy_decision.intent.value,
            metadata={
                "queries_generated": len(generated_queries),
                "crawl_results": len(crawl_results),
                "ranked_results": len(ranked_results),
                "duration_ms": log_entry.get("duration_ms", 0)
            }
        )
    
    async def fetch_url(self, url: str, user_id: str = None) -> Dict:
        """
        Fetch and summarize a specific URL.
        
        Args:
            url: URL to fetch
            user_id: User identifier
            
        Returns:
            Dict with extracted content
        """
        await self.initialize()
        
        result = await self._crawler.fetch_and_summarize(url)
        
        # Log
        self._log_search({
            "query": url,
            "user_id": user_id,
            "action": "url_fetch",
            "success": result.get('success', False)
        })
        
        return result
    
    async def ask(self, query: str, user_id: str = None, 
                  user_context: Dict = None, language: str = "hi") -> str:
        """
        Simplified interface - returns just the formatted response string.
        Perfect for integration with chat AI.
        
        Args:
            query: User's question
            user_id: User identifier
            user_context: Additional context
            language: Response language
            
        Returns:
            Formatted response string
        """
        response = await self.search(query, user_id, user_context, language)
        return response.formatted_response
    
    def _get_query_type_from_intent(self, intent: SearchIntent) -> Optional[str]:
        """Map intent to query type"""
        mapping = {
            SearchIntent.JOB_QUERY: "job",
            SearchIntent.YOJANA_QUERY: "yojana",
            SearchIntent.RESULT_QUERY: "result",
            SearchIntent.DATE_QUERY: "general",
            SearchIntent.DOCUMENT_QUERY: "general"
        }
        return mapping.get(intent)
    
    def _get_no_search_response(self, decision: PolicyDecision, language: str) -> str:
        """Get response when search is not triggered"""
        if decision.intent == SearchIntent.GREETING:
            if language == "hi":
                return "नमस्ते! मैं Digital Sahayak हूं। कैसे मदद कर सकता हूं?"
            return "Hello! I'm Digital Sahayak. How can I help you?"
        
        if decision.intent == SearchIntent.PERSONAL_STATUS:
            if language == "hi":
                return "आपके व्यक्तिगत डेटा के लिए, कृपया 'My Applications' या 'Profile' section देखें।"
            return "For your personal data, please check the 'My Applications' or 'Profile' section."
        
        if decision.intent == SearchIntent.BLOCKED:
            if language == "hi":
                return "यह जानकारी प्रदान करना संभव नहीं है।"
            return "I cannot provide this information."
        
        if decision.rate_limited:
            if language == "hi":
                return f"⚠️ {decision.reason}"
            return f"⚠️ {decision.reason}"
        
        # Default
        if language == "hi":
            return "कृपया अपना सवाल स्पष्ट रूप से पूछें।"
        return "Please ask your question clearly."
    
    def _get_not_found_response(self, query: str, language: str) -> str:
        """Get response when no results found"""
        if language == "hi":
            return f"""🔍 **"{query[:30]}..." के लिए कोई प्रासंगिक जानकारी नहीं मिली।**

💡 **सुझाव:**
• कृपया योजना/नौकरी का official नाम use करें
• अपने सवाल में state का नाम add करें
• Official website का link provide करें

📝 *उदाहरण: "PM Kisan योजना Bihar", "SSC CGL 2026 result"*"""
        
        return f"""🔍 **No relevant information found for "{query[:30]}..."**

💡 **Suggestions:**
• Use the official scheme/job name
• Add state name to your query
• Provide official website link

📝 *Example: "PM Kisan scheme Bihar", "SSC CGL 2026 result"*"""
    
    def _log_search(self, log_entry: Dict):
        """Log search for analytics"""
        log_entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        self.search_logs.append(log_entry)
        
        # Keep only recent logs in memory
        if len(self.search_logs) > 1000:
            self.search_logs = self.search_logs[-500:]
        
        # Log to database (async, fire-and-forget)
        if self.db is not None:
            import asyncio
            asyncio.create_task(self._save_log_to_db(log_entry))
    
    async def _save_log_to_db(self, log_entry: Dict):
        """Save log entry to database"""
        try:
            await self.db.search_logs.insert_one(log_entry)
        except Exception as e:
            logger.warning(f"Failed to save search log: {e}")
    
    # ============== Admin Methods ==============
    
    async def get_cache_status(self) -> Dict:
        """Get cache status (admin)"""
        await self.initialize()
        return self._cache.get_stats()
    
    async def clear_cache(self) -> Dict:
        """Clear all caches (admin)"""
        await self.initialize()
        await self._cache.clear_all()
        return {"status": "cleared"}
    
    async def add_trusted_source(self, domain: str, name: str, 
                                 source_type: str, priority: int = 5,
                                 categories: List[str] = None) -> bool:
        """Add a trusted source (admin)"""
        await self.initialize()
        return await self._sources.add_source(domain, name, source_type, priority, categories)
    
    async def block_domain(self, domain: str, reason: str = "") -> bool:
        """Block a domain (admin)"""
        await self.initialize()
        return await self._sources.block_domain(domain, reason)
    
    async def get_sources_list(self) -> List[Dict]:
        """Get all trusted sources (admin)"""
        await self.initialize()
        return self._sources.get_all_sources()
    
    async def get_search_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent search logs (admin)"""
        if self.db is None:
            return self.search_logs[-limit:]
        
        try:
            cursor = self.db.search_logs.find().sort("timestamp", -1).limit(limit)
            logs = []
            async for doc in cursor:
                doc.pop('_id', None)
                logs.append(doc)
            return logs
        except Exception:
            return self.search_logs[-limit:]
    
    def enable_search_api(self, api_type: str, api_key: str, daily_limit: int = 100):
        """Enable paid search API (admin only)"""
        self._api_manager.enable(api_type, api_key, daily_limit)
        logger.warning(f"Search API enabled: {api_type}")
    
    def disable_search_api(self):
        """Disable paid search API"""
        self._api_manager.disable()
        logger.info("Search API disabled")
    
    def get_api_status(self) -> Dict:
        """Get API status"""
        return self._api_manager.get_status()


# ============== Singleton Instance ==============

_ds_search_instance: Optional[DSSearch] = None

async def get_ds_search_instance(db=None) -> DSSearch:
    """Get or create DS-Search instance"""
    global _ds_search_instance
    
    if _ds_search_instance is None:
        _ds_search_instance = DSSearch(db)
    
    if db is not None and not _ds_search_instance._initialized:
        await _ds_search_instance.initialize(db)
    
    return _ds_search_instance
