"""
DS-Search Result Ranker
=======================
Scores and ranks search results for relevance and trustworthiness.

Scoring Factors:
- Source type (official > aggregator)
- Domain trust score
- Content relevance
- Freshness
- Query match quality
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timezone, timedelta

logger = logging.getLogger(__name__)


@dataclass
class RankedResult:
    """A search result with ranking scores"""
    url: str
    title: str
    snippet: str
    content: str
    domain: str
    
    # Scores
    relevance_score: float = 0.0
    trust_score: float = 0.0
    freshness_score: float = 0.0
    total_score: float = 0.0
    
    # Metadata
    source_type: str = "unknown"
    crawled_at: Optional[datetime] = None
    metadata: Dict = None
    
    def to_dict(self) -> Dict:
        return {
            "url": self.url,
            "title": self.title,
            "snippet": self.snippet,
            "content": self.content[:1000] if self.content else "",
            "domain": self.domain,
            "scores": {
                "relevance": round(self.relevance_score, 3),
                "trust": round(self.trust_score, 3),
                "freshness": round(self.freshness_score, 3),
                "total": round(self.total_score, 3)
            },
            "source_type": self.source_type,
            "crawled_at": self.crawled_at.isoformat() if self.crawled_at else None
        }


class ResultRanker:
    """
    Ranks search results based on multiple factors.
    Prefers official government sources over aggregators.
    """
    
    # Weight configuration
    WEIGHTS = {
        "relevance": 0.40,   # How well content matches query
        "trust": 0.35,       # Source trustworthiness
        "freshness": 0.15,   # How recent the content is
        "title_match": 0.10  # Title contains query keywords
    }
    
    # Trust scores by domain type
    TRUST_SCORES = {
        "official": 1.0,      # .gov.in, .nic.in
        "semi_official": 0.85,
        "educational": 0.75,   # .ac.in, .edu.in
        "aggregator": 0.50,
        "news": 0.60,
        "unknown": 0.30
    }
    
    # Domain pattern to trust mapping
    DOMAIN_TRUST_PATTERNS = {
        r'\.gov\.in$': "official",
        r'\.nic\.in$': "official",
        r'\.ac\.in$': "educational",
        r'\.edu\.in$': "educational",
        r'sarkari': "aggregator",
        r'jobalert': "aggregator",
        r'freejobalert': "aggregator",
        r'(news|times|india|daily)': "news"
    }
    
    # Important keywords that boost relevance
    IMPORTANT_KEYWORDS = [
        'official', 'आधिकारिक', 'notification', 'नोटिफिकेशन',
        'apply', 'आवेदन', 'download', 'डाउनलोड',
        'result', 'रिजल्ट', 'admit', 'एडमिट',
        'last date', 'अंतिम तिथि', 'deadline'
    ]
    
    def __init__(self, sources_manager=None):
        self.sources = sources_manager
    
    def _get_domain_type(self, domain: str) -> str:
        """Determine domain type based on patterns"""
        domain_lower = domain.lower()
        
        # Check with sources manager first
        if self.sources:
            source = self.sources.get_source(domain)
            if source:
                return source.source_type.value
        
        # Pattern matching
        for pattern, dtype in self.DOMAIN_TRUST_PATTERNS.items():
            if re.search(pattern, domain_lower):
                return dtype
        
        return "unknown"
    
    def _calculate_trust_score(self, domain: str) -> float:
        """Calculate trust score for a domain"""
        # Check sources manager
        if self.sources:
            priority = self.sources.get_priority(domain)
            return min(1.0, priority / 10.0)
        
        # Fallback to domain type
        domain_type = self._get_domain_type(domain)
        return self.TRUST_SCORES.get(domain_type, 0.30)
    
    def _calculate_relevance_score(self, result: Dict, query: str, 
                                   query_keywords: List[str]) -> float:
        """Calculate relevance score based on query match"""
        score = 0.0
        
        title = (result.get('title', '') or '').lower()
        snippet = (result.get('snippet', '') or '').lower()
        content = (result.get('content', '') or '').lower()
        
        # Combine text for matching
        all_text = f"{title} {snippet} {content}"
        
        # Query keyword matches
        query_lower = query.lower()
        query_words = query_lower.split()
        
        # Direct query match
        if query_lower in all_text:
            score += 0.30
        
        # Keyword matches
        keywords_found = 0
        for keyword in query_keywords:
            if keyword.lower() in all_text:
                keywords_found += 1
        
        if query_keywords:
            keyword_ratio = keywords_found / len(query_keywords)
            score += keyword_ratio * 0.40
        
        # Important keyword bonus
        for imp_kw in self.IMPORTANT_KEYWORDS:
            if imp_kw.lower() in all_text:
                score += 0.05
        
        # Title match bonus
        title_matches = sum(1 for w in query_words if w in title)
        if query_words:
            score += (title_matches / len(query_words)) * 0.20
        
        # Snippet quality
        if len(snippet) > 100:
            score += 0.05
        
        return min(1.0, score)
    
    def _calculate_freshness_score(self, result: Dict) -> float:
        """Calculate freshness score based on dates"""
        score = 0.5  # Default middle score
        
        # Check metadata for dates
        metadata = result.get('metadata', {})
        
        # Look for date in various formats
        date_str = metadata.get('date', '')
        
        # Check content for year mentions
        content = result.get('content', '') or ''
        snippet = result.get('snippet', '') or ''
        
        current_year = datetime.now().year
        
        # Recent year mentions boost score
        if str(current_year) in content or str(current_year) in snippet:
            score = 0.90
        elif str(current_year - 1) in content or str(current_year - 1) in snippet:
            score = 0.70
        elif str(current_year - 2) in content:
            score = 0.50
        
        # "Latest" or "New" keywords
        text_lower = f"{content} {snippet}".lower()
        if any(kw in text_lower for kw in ['latest', 'new', 'recent', 'नया', 'नई', 'ताजा']):
            score = min(1.0, score + 0.20)
        
        return score
    
    def _calculate_title_match_score(self, title: str, query_keywords: List[str]) -> float:
        """Calculate how well title matches query"""
        if not title or not query_keywords:
            return 0.0
        
        title_lower = title.lower()
        matches = sum(1 for kw in query_keywords if kw.lower() in title_lower)
        
        return matches / len(query_keywords) if query_keywords else 0.0
    
    def rank(self, results: List[Dict], query: str, 
             query_keywords: List[str] = None) -> List[RankedResult]:
        """
        Rank search results by relevance and trust.
        
        Args:
            results: List of search/crawl results
            query: Original user query
            query_keywords: Extracted keywords from query
            
        Returns:
            Sorted list of RankedResult objects
        """
        if not results:
            return []
        
        # Extract keywords if not provided
        if not query_keywords:
            query_keywords = self._extract_keywords(query)
        
        ranked_results = []
        
        for result in results:
            # Handle both dict and CrawlResult objects
            if hasattr(result, 'to_dict'):
                result_dict = result.to_dict()
            else:
                result_dict = result
            
            domain = result_dict.get('domain', '')
            if not domain:
                # Extract from URL
                from urllib.parse import urlparse
                url = result_dict.get('url', '')
                domain = urlparse(url).netloc if url else ''
            
            # Calculate individual scores
            trust_score = self._calculate_trust_score(domain)
            relevance_score = self._calculate_relevance_score(
                result_dict, query, query_keywords
            )
            freshness_score = self._calculate_freshness_score(result_dict)
            title_match = self._calculate_title_match_score(
                result_dict.get('title', ''), query_keywords
            )
            
            # Calculate weighted total score
            total_score = (
                relevance_score * self.WEIGHTS['relevance'] +
                trust_score * self.WEIGHTS['trust'] +
                freshness_score * self.WEIGHTS['freshness'] +
                title_match * self.WEIGHTS['title_match']
            )
            
            ranked_result = RankedResult(
                url=result_dict.get('url', ''),
                title=result_dict.get('title', ''),
                snippet=result_dict.get('snippet', ''),
                content=result_dict.get('content', ''),
                domain=domain,
                relevance_score=relevance_score,
                trust_score=trust_score,
                freshness_score=freshness_score,
                total_score=total_score,
                source_type=self._get_domain_type(domain),
                crawled_at=result_dict.get('crawled_at'),
                metadata=result_dict.get('metadata', {})
            )
            
            ranked_results.append(ranked_result)
        
        # Sort by total score (descending)
        ranked_results.sort(key=lambda r: r.total_score, reverse=True)
        
        logger.info(f"Ranked {len(ranked_results)} results. Top score: {ranked_results[0].total_score:.3f}" if ranked_results else "No results to rank")
        
        return ranked_results
    
    def _extract_keywords(self, query: str) -> List[str]:
        """Extract important keywords from query"""
        # Remove filler words
        filler_words = {
            'kya', 'hai', 'hain', 'ka', 'ki', 'ke', 'me', 'mein',
            'the', 'is', 'are', 'a', 'an', 'what', 'how', 'when',
            'please', 'batao', 'bataiye', 'dikhao', 'show', 'tell'
        }
        
        words = query.lower().split()
        keywords = [w for w in words if w not in filler_words and len(w) > 2]
        
        return keywords
    
    def get_top_results(self, ranked_results: List[RankedResult], 
                        min_score: float = 0.65, max_results: int = 5) -> List[RankedResult]:
        """
        Get top results above minimum score threshold.
        
        Args:
            ranked_results: List of ranked results
            min_score: Minimum total score to include
            max_results: Maximum number of results to return
            
        Returns:
            Filtered list of top results
        """
        filtered = [r for r in ranked_results if r.total_score >= min_score]
        return filtered[:max_results]
    
    def get_best_official_result(self, ranked_results: List[RankedResult]) -> Optional[RankedResult]:
        """Get the best result from official sources"""
        official_results = [
            r for r in ranked_results 
            if r.source_type in ['official', 'semi_official']
        ]
        
        if official_results:
            return official_results[0]
        return None
    
    def format_for_response(self, ranked_results: List[RankedResult], 
                           language: str = 'hi') -> str:
        """
        Format ranked results for AI response.
        
        Args:
            ranked_results: Ranked results to format
            language: Response language (hi/en)
            
        Returns:
            Formatted string for AI response
        """
        if not ranked_results:
            if language == 'hi':
                return "कोई प्रासंगिक जानकारी नहीं मिली।"
            return "No relevant information found."
        
        # Header
        if language == 'hi':
            response = "🔍 **आपके सवाल के लिए मैंने खोजा:**\n\n"
        else:
            response = "🔍 **Here's what I found:**\n\n"
        
        # Add top results
        for i, result in enumerate(ranked_results[:3], 1):
            # Trust indicator
            trust_icon = "✅" if result.source_type == "official" else "📄"
            
            response += f"{trust_icon} **{i}. {result.title}**\n"
            
            if result.snippet:
                response += f"   {result.snippet[:200]}...\n" if len(result.snippet) > 200 else f"   {result.snippet}\n"
            
            response += f"   🔗 {result.url}\n"
            
            # Score indicator for debugging
            if result.source_type == "official":
                if language == 'hi':
                    response += f"   _(आधिकारिक स्रोत)_\n"
                else:
                    response += f"   _(Official Source)_\n"
            
            response += "\n"
        
        # Footer
        if language == 'hi':
            response += "💡 *आधिकारिक वेबसाइट पर जाकर जानकारी verify करें।*"
        else:
            response += "💡 *Please verify on official website.*"
        
        return response


# Singleton instance
_ranker_instance: Optional[ResultRanker] = None

def get_ranker_instance(sources_manager=None) -> ResultRanker:
    """Get or create ranker instance"""
    global _ranker_instance
    if _ranker_instance is None:
        _ranker_instance = ResultRanker(sources_manager)
    return _ranker_instance
