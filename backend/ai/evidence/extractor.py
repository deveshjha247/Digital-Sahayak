"""
Evidence Extractor - Main Module
================================
Transforms raw search results into structured facts.
Uses trust scoring, content extraction, and pattern matching.
"""

import asyncio
import re
import logging
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from urllib.parse import urlparse

try:
    import httpx
    from bs4 import BeautifulSoup
    SCRAPING_AVAILABLE = True
except ImportError:
    SCRAPING_AVAILABLE = False

from .patterns import (
    extract_dates, extract_fees, extract_age_limit,
    extract_vacancies, extract_documents, detect_state,
    detect_department, extract_official_links, extract_pdf_links,
    extract_qualifications, ELIGIBILITY_KEYWORDS
)

logger = logging.getLogger(__name__)

# ===================== DATA CLASSES =====================

@dataclass
class Facts:
    """Structured facts extracted from search results"""
    type: str  # 'job', 'scheme', 'result', 'admit_card', 'answer_key'
    title: str
    state: Optional[str] = None
    department: Optional[str] = None
    organization: Optional[str] = None
    
    # Dates
    last_date: Optional[str] = None
    start_date: Optional[str] = None
    exam_date: Optional[str] = None
    result_date: Optional[str] = None
    
    # Eligibility
    eligibility: List[str] = field(default_factory=list)
    age_limit: Dict[str, int] = field(default_factory=dict)
    qualifications: List[str] = field(default_factory=list)
    
    # Details
    vacancies: Optional[int] = None
    documents: List[str] = field(default_factory=list)
    
    # Fees
    fees: Dict[str, Any] = field(default_factory=dict)
    
    # Links
    links: List[str] = field(default_factory=list)
    pdf_links: List[str] = field(default_factory=list)
    apply_link: Optional[str] = None
    
    # Metadata
    source_url: Optional[str] = None
    source_trust: float = 0.0
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    confidence: float = 0.0
    raw_snippet: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def is_valid(self) -> bool:
        """Check if facts have minimum required info"""
        return bool(self.title and (self.last_date or self.links or self.eligibility))


@dataclass 
class SearchResult:
    """Single search result input"""
    title: str
    url: str
    snippet: str
    source_type: str = "unknown"
    domain: str = ""
    
    def __post_init__(self):
        if not self.domain and self.url:
            try:
                self.domain = urlparse(self.url).netloc.lower()
            except:
                pass


# ===================== TRUST SCORING =====================

class TrustScorer:
    """Assigns trust scores to sources"""
    
    # Domain trust scores
    TRUST_SCORES = {
        # Official government (1.0)
        '.gov.in': 1.0,
        '.nic.in': 1.0,
        'india.gov.in': 1.0,
        
        # Semi-official (0.85)
        '.ac.in': 0.85,
        '.edu.in': 0.85,
        
        # Trusted aggregators (0.7)
        'sarkariresult.com': 0.7,
        'freejobalert.com': 0.7,
        'sarkariexam.com': 0.7,
        'employmentnews.gov.in': 0.9,
        'ncs.gov.in': 0.9,
        
        # News sites (0.6)
        'hindustantimes.com': 0.6,
        'timesofindia.com': 0.6,
        'ndtv.com': 0.6,
        'aajtak.in': 0.6,
        
        # Default (0.3)
        'default': 0.3
    }
    
    @classmethod
    def get_trust_score(cls, url: str) -> float:
        """Calculate trust score for a URL"""
        try:
            domain = urlparse(url).netloc.lower()
        except:
            return 0.3
        
        # Check exact domain match first
        for pattern, score in cls.TRUST_SCORES.items():
            if pattern in domain:
                return score
        
        return cls.TRUST_SCORES['default']
    
    @classmethod
    def calculate_keyword_match(cls, text: str, query: str) -> float:
        """Calculate keyword match score (0-1)"""
        if not text or not query:
            return 0.0
        
        text_lower = text.lower()
        query_words = query.lower().split()
        
        if not query_words:
            return 0.0
        
        matched = sum(1 for word in query_words if word in text_lower)
        return matched / len(query_words)
    
    @classmethod
    def rank_results(cls, results: List[SearchResult], query: str) -> List[SearchResult]:
        """Rank results by trust × keyword match"""
        scored = []
        for result in results:
            trust = cls.get_trust_score(result.url)
            keyword_match = cls.calculate_keyword_match(
                f"{result.title} {result.snippet}", query
            )
            # Combined score: 60% trust + 40% keyword match
            score = (trust * 0.6) + (keyword_match * 0.4)
            scored.append((result, score, trust))
        
        # Sort by combined score (descending)
        scored.sort(key=lambda x: x[1], reverse=True)
        
        # Add trust info to results
        ranked = []
        for result, score, trust in scored:
            result.source_type = cls._get_source_type(trust)
            ranked.append(result)
        
        return ranked
    
    @staticmethod
    def _get_source_type(trust: float) -> str:
        if trust >= 0.9:
            return "official"
        elif trust >= 0.7:
            return "semi_official"
        elif trust >= 0.5:
            return "aggregator"
        else:
            return "unknown"


# ===================== CONTENT SCRAPER =====================

class ContentScraper:
    """Scrapes and extracts content from URLs"""
    
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36"
        self.timeout = 15.0
    
    async def scrape_url(self, url: str) -> Optional[str]:
        """Scrape content from a URL"""
        if not SCRAPING_AVAILABLE:
            logger.warning("Scraping not available - httpx/beautifulsoup not installed")
            return None
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(
                    url,
                    headers={"User-Agent": self.user_agent},
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: {response.status_code}")
                    return None
                
                return self._extract_text(response.text)
                
        except Exception as e:
            logger.error(f"Scraping error for {url}: {e}")
            return None
    
    def _extract_text(self, html: str) -> str:
        """Extract clean text from HTML"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            element.decompose()
        
        # Get text
        text = soup.get_text(separator=' ', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text[:10000]  # Limit to 10k chars


# ===================== EVIDENCE EXTRACTOR =====================

class EvidenceExtractor:
    """Main class to extract structured facts from search results"""
    
    def __init__(self):
        self.scraper = ContentScraper()
        self.trust_scorer = TrustScorer()
    
    async def extract(
        self,
        results: List[Dict],
        query: str,
        scrape_top_n: int = 2
    ) -> Optional[Facts]:
        """
        Extract facts from search results.
        
        Args:
            results: List of search results (title, url, snippet)
            query: Original search query
            scrape_top_n: Number of top results to scrape for details
            
        Returns:
            Structured Facts object or None if extraction fails
        """
        if not results:
            return None
        
        # Convert to SearchResult objects
        search_results = [
            SearchResult(
                title=r.get('title', ''),
                url=r.get('url', ''),
                snippet=r.get('snippet', '')
            ) for r in results if r.get('url')
        ]
        
        if not search_results:
            return None
        
        # Rank by trust and keyword match
        ranked = self.trust_scorer.rank_results(search_results, query)
        
        # Detect content type from query
        content_type = self._detect_content_type(query)
        
        # Start with basic facts from snippets
        facts = self._extract_from_snippets(ranked, content_type, query)
        
        # Try to scrape top official sources for more details
        official_results = [r for r in ranked if r.source_type == "official"][:scrape_top_n]
        
        if not official_results:
            # Fallback to semi-official
            official_results = [r for r in ranked if r.source_type in ("official", "semi_official")][:scrape_top_n]
        
        if not official_results:
            # Last resort: use top ranked results
            official_results = ranked[:scrape_top_n]
        
        # Scrape and enhance facts
        for result in official_results:
            try:
                scraped_text = await self.scraper.scrape_url(result.url)
                if scraped_text:
                    self._enhance_facts_from_text(facts, scraped_text, result)
            except Exception as e:
                logger.error(f"Error scraping {result.url}: {e}")
        
        # Calculate confidence
        facts.confidence = self._calculate_confidence(facts)
        
        return facts if facts.is_valid() else None
    
    def _detect_content_type(self, query: str) -> str:
        """Detect type of content from query"""
        query_lower = query.lower()
        
        if any(kw in query_lower for kw in ['result', 'रिजल्ट', 'merit']):
            return 'result'
        elif any(kw in query_lower for kw in ['admit card', 'hall ticket', 'एडमिट']):
            return 'admit_card'
        elif any(kw in query_lower for kw in ['answer key', 'उत्तर कुंजी']):
            return 'answer_key'
        elif any(kw in query_lower for kw in ['scheme', 'yojana', 'योजना', 'pension', 'subsidy']):
            return 'scheme'
        else:
            return 'job'
    
    def _extract_from_snippets(
        self, 
        results: List[SearchResult],
        content_type: str,
        query: str
    ) -> Facts:
        """Extract basic facts from snippets"""
        # Combine all snippets
        combined_text = ' '.join([
            f"{r.title} {r.snippet}" for r in results
        ])
        
        # Get best title
        title = results[0].title if results else query
        
        # Extract dates
        dates = extract_dates(combined_text)
        
        # Extract other info
        fees = extract_fees(combined_text)
        age_limit = extract_age_limit(combined_text)
        vacancies = extract_vacancies(combined_text)
        documents = extract_documents(combined_text)
        state = detect_state(combined_text)
        department = detect_department(combined_text)
        qualifications = extract_qualifications(combined_text)
        
        # Extract links
        official_links = []
        pdf_links = []
        for r in results:
            if '.gov.in' in r.url or '.nic.in' in r.url:
                official_links.append(r.url)
        
        # Build eligibility list
        eligibility = []
        if age_limit:
            if 'min' in age_limit and 'max' in age_limit:
                eligibility.append(f"Age: {age_limit['min']}-{age_limit['max']} years")
            elif 'value' in age_limit:
                eligibility.append(f"Age limit: {age_limit['value']} years")
        
        if qualifications:
            eligibility.append(f"Education: {', '.join(qualifications)}")
        
        # Calculate fees with service charge
        fees_with_service = {}
        if fees:
            base_fee = fees.get('general', 0)
            fees_with_service = {
                'govt_fee': base_fee,
                'service_fee': 20,  # Digital Sahayak service fee
                'total': base_fee + 20,
                'category_wise': fees
            }
        
        return Facts(
            type=content_type,
            title=title,
            state=state,
            department=department,
            last_date=dates.get('last_date'),
            start_date=dates.get('start_date'),
            exam_date=dates.get('exam_date'),
            eligibility=eligibility,
            age_limit=age_limit,
            qualifications=qualifications,
            vacancies=vacancies,
            documents=documents,
            fees=fees_with_service,
            links=official_links[:5],
            pdf_links=pdf_links[:3],
            source_url=results[0].url if results else None,
            source_trust=self.trust_scorer.get_trust_score(results[0].url) if results else 0,
            raw_snippet=results[0].snippet if results else None
        )
    
    def _enhance_facts_from_text(
        self, 
        facts: Facts, 
        text: str, 
        source: SearchResult
    ):
        """Enhance facts with scraped content"""
        # Update dates if not found
        if not facts.last_date:
            dates = extract_dates(text)
            facts.last_date = dates.get('last_date')
            facts.start_date = dates.get('start_date') or facts.start_date
            facts.exam_date = dates.get('exam_date') or facts.exam_date
        
        # Update fees
        if not facts.fees:
            fees = extract_fees(text)
            if fees:
                base_fee = fees.get('general', 0)
                facts.fees = {
                    'govt_fee': base_fee,
                    'service_fee': 20,
                    'total': base_fee + 20,
                    'category_wise': fees
                }
        
        # Update vacancies
        if not facts.vacancies:
            facts.vacancies = extract_vacancies(text)
        
        # Add more documents
        new_docs = extract_documents(text)
        facts.documents = list(set(facts.documents + new_docs))
        
        # Add more qualifications to eligibility
        new_quals = extract_qualifications(text)
        for qual in new_quals:
            if qual not in facts.qualifications:
                facts.qualifications.append(qual)
        
        # Extract links
        official_links = extract_official_links(text)
        facts.links = list(set(facts.links + official_links))[:5]
        
        pdf_links = extract_pdf_links(text)
        facts.pdf_links = list(set(facts.pdf_links + pdf_links))[:3]
        
        # Update trust if this source is better
        source_trust = self.trust_scorer.get_trust_score(source.url)
        if source_trust > facts.source_trust:
            facts.source_trust = source_trust
            facts.source_url = source.url
    
    def _calculate_confidence(self, facts: Facts) -> float:
        """Calculate confidence score for extracted facts"""
        score = 0.0
        
        # Title present
        if facts.title:
            score += 0.15
        
        # Source trust
        score += facts.source_trust * 0.25
        
        # Key fields present
        if facts.last_date:
            score += 0.15
        if facts.eligibility:
            score += 0.10
        if facts.fees:
            score += 0.10
        if facts.links:
            score += 0.15
        if facts.vacancies:
            score += 0.05
        if facts.documents:
            score += 0.05
        
        return min(score, 1.0)


# ===================== FACTORY FUNCTION =====================

async def extract_facts(
    results: List[Dict],
    query: str,
    scrape_top_n: int = 2
) -> Optional[Facts]:
    """
    Factory function to extract facts from search results.
    
    Args:
        results: List of search results with title, url, snippet
        query: Original query
        scrape_top_n: How many top results to scrape
        
    Returns:
        Structured Facts or None
    """
    extractor = EvidenceExtractor()
    return await extractor.extract(results, query, scrape_top_n)
