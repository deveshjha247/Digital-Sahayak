"""
DS-Search Trusted Sources Manager
=================================
Manages list of trusted domains for crawling.

Source Types:
- official: Government websites (highest trust)
- semi_official: Government-affiliated sites
- aggregator: News/job portals (lower trust)

Features:
- Domain whitelisting
- Source priority scoring
- Rate limiting per domain
- Blocklist for spam domains
"""

import re
import logging
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class SourceType(Enum):
    """Types of sources with trust levels"""
    OFFICIAL = "official"          # Government sites - highest trust
    SEMI_OFFICIAL = "semi_official" # Gov-affiliated sites
    AGGREGATOR = "aggregator"       # News/job portals
    EDUCATIONAL = "educational"     # Educational institutions
    BLOCKED = "blocked"             # Spam/unreliable sites


@dataclass
class TrustedSource:
    """A trusted source configuration"""
    domain: str
    source_type: SourceType
    name: str
    priority: int  # 1-10, higher is better
    enabled: bool = True
    rate_limit: float = 1.0  # Requests per second
    last_crawled: Optional[datetime] = None
    success_rate: float = 1.0
    categories: List[str] = field(default_factory=list)  # job, yojana, result, etc.
    
    def to_dict(self) -> Dict:
        return {
            "domain": self.domain,
            "source_type": self.source_type.value,
            "name": self.name,
            "priority": self.priority,
            "enabled": self.enabled,
            "rate_limit": self.rate_limit,
            "last_crawled": self.last_crawled.isoformat() if self.last_crawled else None,
            "success_rate": self.success_rate,
            "categories": self.categories
        }


class TrustedSources:
    """
    Manages trusted domains for DS-Search crawling.
    """
    
    # Default trusted government domains (highest priority)
    OFFICIAL_DOMAINS = {
        # Central Government
        "india.gov.in": TrustedSource(
            domain="india.gov.in",
            source_type=SourceType.OFFICIAL,
            name="National Portal of India",
            priority=10,
            categories=["yojana", "general", "government"]
        ),
        "pib.gov.in": TrustedSource(
            domain="pib.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Press Information Bureau",
            priority=10,
            categories=["news", "announcement", "government"]
        ),
        
        # Job Portals - Government
        "ssc.nic.in": TrustedSource(
            domain="ssc.nic.in",
            source_type=SourceType.OFFICIAL,
            name="Staff Selection Commission",
            priority=10,
            categories=["job", "result", "admit_card"]
        ),
        "upsc.gov.in": TrustedSource(
            domain="upsc.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Union Public Service Commission",
            priority=10,
            categories=["job", "result", "admit_card"]
        ),
        "indianrailways.gov.in": TrustedSource(
            domain="indianrailways.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Indian Railways",
            priority=10,
            categories=["job", "general"]
        ),
        "rrbcdg.gov.in": TrustedSource(
            domain="rrbcdg.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Railway Recruitment Board",
            priority=10,
            categories=["job", "result", "admit_card"]
        ),
        "ibps.in": TrustedSource(
            domain="ibps.in",
            source_type=SourceType.OFFICIAL,
            name="Institute of Banking Personnel Selection",
            priority=10,
            categories=["job", "result", "admit_card"]
        ),
        "nta.ac.in": TrustedSource(
            domain="nta.ac.in",
            source_type=SourceType.OFFICIAL,
            name="National Testing Agency",
            priority=10,
            categories=["job", "result", "admit_card", "exam"]
        ),
        
        # Yojana Portals
        "pmkisan.gov.in": TrustedSource(
            domain="pmkisan.gov.in",
            source_type=SourceType.OFFICIAL,
            name="PM-KISAN Portal",
            priority=10,
            categories=["yojana", "kisan"]
        ),
        "pmjay.gov.in": TrustedSource(
            domain="pmjay.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Ayushman Bharat Portal",
            priority=10,
            categories=["yojana", "health"]
        ),
        "pmaymis.gov.in": TrustedSource(
            domain="pmaymis.gov.in",
            source_type=SourceType.OFFICIAL,
            name="PM Awas Yojana",
            priority=10,
            categories=["yojana", "housing"]
        ),
        "nrega.nic.in": TrustedSource(
            domain="nrega.nic.in",
            source_type=SourceType.OFFICIAL,
            name="MGNREGA Portal",
            priority=10,
            categories=["yojana", "employment"]
        ),
        "uidai.gov.in": TrustedSource(
            domain="uidai.gov.in",
            source_type=SourceType.OFFICIAL,
            name="UIDAI Aadhaar",
            priority=10,
            categories=["document", "identity"]
        ),
        "pmjdy.gov.in": TrustedSource(
            domain="pmjdy.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Jan Dhan Yojana",
            priority=10,
            categories=["yojana", "banking"]
        ),
        "mudra.org.in": TrustedSource(
            domain="mudra.org.in",
            source_type=SourceType.OFFICIAL,
            name="MUDRA Yojana",
            priority=10,
            categories=["yojana", "loan"]
        ),
        
        # Education
        "cbse.gov.in": TrustedSource(
            domain="cbse.gov.in",
            source_type=SourceType.OFFICIAL,
            name="CBSE",
            priority=10,
            categories=["education", "result", "exam"]
        ),
        "cbseresults.nic.in": TrustedSource(
            domain="cbseresults.nic.in",
            source_type=SourceType.OFFICIAL,
            name="CBSE Results",
            priority=10,
            categories=["result"]
        ),
        "ugc.ac.in": TrustedSource(
            domain="ugc.ac.in",
            source_type=SourceType.OFFICIAL,
            name="UGC",
            priority=10,
            categories=["education", "scholarship"]
        ),
        
        # State Portals
        "bihar.gov.in": TrustedSource(
            domain="bihar.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Bihar Government",
            priority=9,
            categories=["state", "yojana", "job"]
        ),
        "biharboardonline.com": TrustedSource(
            domain="biharboardonline.com",
            source_type=SourceType.SEMI_OFFICIAL,
            name="Bihar Board",
            priority=8,
            categories=["result", "education"]
        ),
        "bsebinteredu.in": TrustedSource(
            domain="bsebinteredu.in",
            source_type=SourceType.SEMI_OFFICIAL,
            name="BSEB Inter Results",
            priority=8,
            categories=["result", "education"]
        ),
        "up.gov.in": TrustedSource(
            domain="up.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Uttar Pradesh Government",
            priority=9,
            categories=["state", "yojana", "job"]
        ),
        "mp.gov.in": TrustedSource(
            domain="mp.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Madhya Pradesh Government",
            priority=9,
            categories=["state", "yojana", "job"]
        ),
        "rajasthan.gov.in": TrustedSource(
            domain="rajasthan.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Rajasthan Government",
            priority=9,
            categories=["state", "yojana", "job"]
        ),
        
        # Defense & Police
        "joinindianarmy.nic.in": TrustedSource(
            domain="joinindianarmy.nic.in",
            source_type=SourceType.OFFICIAL,
            name="Indian Army Recruitment",
            priority=10,
            categories=["job", "defense"]
        ),
        "joinindiannavy.gov.in": TrustedSource(
            domain="joinindiannavy.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Indian Navy Recruitment",
            priority=10,
            categories=["job", "defense"]
        ),
        "indianairforce.nic.in": TrustedSource(
            domain="indianairforce.nic.in",
            source_type=SourceType.OFFICIAL,
            name="Indian Air Force",
            priority=10,
            categories=["job", "defense"]
        ),
    }
    
    # Aggregator sites (lower trust, but useful for news)
    AGGREGATOR_DOMAINS = {
        "sarkariresult.com": TrustedSource(
            domain="sarkariresult.com",
            source_type=SourceType.AGGREGATOR,
            name="Sarkari Result",
            priority=5,
            categories=["job", "result", "admit_card"]
        ),
        "sarkarijobfind.com": TrustedSource(
            domain="sarkarijobfind.com",
            source_type=SourceType.AGGREGATOR,
            name="Sarkari Job Find",
            priority=4,
            categories=["job", "result"]
        ),
        "freejobalert.com": TrustedSource(
            domain="freejobalert.com",
            source_type=SourceType.AGGREGATOR,
            name="Free Job Alert",
            priority=5,
            categories=["job", "result", "admit_card"]
        ),
        "employmentnews.gov.in": TrustedSource(
            domain="employmentnews.gov.in",
            source_type=SourceType.OFFICIAL,
            name="Employment News",
            priority=9,
            categories=["job", "news"]
        ),
    }
    
    # Blocked domains (spam, unreliable, click-bait)
    BLOCKED_DOMAINS = {
        "fakesite.com",
        "scamjobs.com",
        "getrichquick.com",
        # Add more as discovered
    }
    
    def __init__(self, db=None):
        self.db = db
        self.sources: Dict[str, TrustedSource] = {}
        self.blocked_domains: Set[str] = set(self.BLOCKED_DOMAINS)
        self._initialize_sources()
    
    def _initialize_sources(self):
        """Initialize with default sources"""
        self.sources.update(self.OFFICIAL_DOMAINS)
        self.sources.update(self.AGGREGATOR_DOMAINS)
        logger.info(f"Initialized {len(self.sources)} trusted sources")
    
    async def load_from_db(self):
        """Load additional sources from database"""
        if self.db is None:
            return
        
        try:
            cursor = self.db.trusted_sources.find({"enabled": True})
            async for doc in cursor:
                source = TrustedSource(
                    domain=doc['domain'],
                    source_type=SourceType(doc['source_type']),
                    name=doc['name'],
                    priority=doc.get('priority', 5),
                    enabled=doc.get('enabled', True),
                    rate_limit=doc.get('rate_limit', 1.0),
                    categories=doc.get('categories', [])
                )
                self.sources[source.domain] = source
            
            # Load blocked domains
            blocked_cursor = self.db.trusted_sources.find({"source_type": "blocked"})
            async for doc in blocked_cursor:
                self.blocked_domains.add(doc['domain'])
            
            logger.info(f"Loaded {len(self.sources)} sources from DB")
        except Exception as e:
            logger.error(f"Error loading sources from DB: {e}")
    
    def is_trusted(self, domain: str) -> bool:
        """Check if a domain is trusted"""
        # Normalize domain
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        # Check blocked first
        if domain in self.blocked_domains:
            return False
        
        # Check if in trusted sources
        if domain in self.sources:
            return self.sources[domain].enabled
        
        # Check if it's a .gov.in domain (auto-trust)
        if domain.endswith('.gov.in') or domain.endswith('.nic.in'):
            return True
        
        return False
    
    def is_blocked(self, domain: str) -> bool:
        """Check if a domain is blocked"""
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        return domain in self.blocked_domains
    
    def get_source(self, domain: str) -> Optional[TrustedSource]:
        """Get source configuration for a domain"""
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        return self.sources.get(domain)
    
    def get_priority(self, domain: str) -> int:
        """Get priority score for a domain"""
        source = self.get_source(domain)
        if source:
            return source.priority
        
        # Default priorities based on domain type
        domain = domain.lower()
        if domain.endswith('.gov.in'):
            return 8
        elif domain.endswith('.nic.in'):
            return 8
        elif domain.endswith('.ac.in'):
            return 6
        elif domain.endswith('.edu.in'):
            return 6
        elif domain.endswith('.org.in'):
            return 5
        
        return 3  # Default for unknown domains
    
    def get_sources_by_category(self, category: str) -> List[TrustedSource]:
        """Get all sources for a specific category"""
        return [
            source for source in self.sources.values()
            if category in source.categories and source.enabled
        ]
    
    def get_official_sources(self) -> List[TrustedSource]:
        """Get all official government sources"""
        return [
            source for source in self.sources.values()
            if source.source_type == SourceType.OFFICIAL and source.enabled
        ]
    
    def get_domains_for_query_type(self, query_type: str) -> List[str]:
        """Get recommended domains for a query type"""
        category_mapping = {
            'job': ['job', 'result', 'admit_card'],
            'yojana': ['yojana', 'government'],
            'result': ['result', 'education'],
            'admit_card': ['admit_card', 'result'],
            'cutoff': ['result', 'job'],
            'syllabus': ['education', 'exam'],
            'general': ['government', 'general']
        }
        
        categories = category_mapping.get(query_type, ['general'])
        
        domains = []
        for source in self.sources.values():
            if source.enabled and any(cat in source.categories for cat in categories):
                domains.append(source.domain)
        
        # Sort by priority
        domains.sort(key=lambda d: self.get_priority(d), reverse=True)
        
        return domains[:15]  # Return top 15
    
    async def add_source(self, domain: str, name: str, source_type: str,
                        priority: int = 5, categories: List[str] = None) -> bool:
        """Add a new trusted source"""
        if self.is_blocked(domain):
            logger.warning(f"Cannot add blocked domain: {domain}")
            return False
        
        source = TrustedSource(
            domain=domain.lower().strip(),
            source_type=SourceType(source_type),
            name=name,
            priority=priority,
            categories=categories or []
        )
        
        self.sources[source.domain] = source
        
        # Save to DB
        if self.db is not None:
            try:
                await self.db.trusted_sources.update_one(
                    {"domain": source.domain},
                    {"$set": source.to_dict()},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error saving source to DB: {e}")
        
        logger.info(f"Added trusted source: {domain}")
        return True
    
    async def block_domain(self, domain: str, reason: str = "") -> bool:
        """Block a domain"""
        domain = domain.lower().strip()
        if domain.startswith('www.'):
            domain = domain[4:]
        
        self.blocked_domains.add(domain)
        
        # Remove from trusted if present
        if domain in self.sources:
            del self.sources[domain]
        
        # Save to DB
        if self.db is not None:
            try:
                await self.db.trusted_sources.update_one(
                    {"domain": domain},
                    {"$set": {
                        "domain": domain,
                        "source_type": "blocked",
                        "blocked_reason": reason,
                        "blocked_at": datetime.now(timezone.utc).isoformat()
                    }},
                    upsert=True
                )
            except Exception as e:
                logger.error(f"Error blocking domain in DB: {e}")
        
        logger.info(f"Blocked domain: {domain}")
        return True
    
    def update_crawl_stats(self, domain: str, success: bool):
        """Update crawl statistics for a domain"""
        source = self.get_source(domain)
        if source:
            source.last_crawled = datetime.now(timezone.utc)
            # Update success rate (rolling average)
            current_rate = source.success_rate
            source.success_rate = (current_rate * 0.9) + (1.0 if success else 0.0) * 0.1
    
    def get_rate_limit(self, domain: str) -> float:
        """Get rate limit for a domain"""
        source = self.get_source(domain)
        if source:
            return source.rate_limit
        return 1.0  # Default: 1 request per second
    
    def get_all_sources(self) -> List[Dict]:
        """Get all sources as list of dicts"""
        return [source.to_dict() for source in self.sources.values()]
    
    def get_stats(self) -> Dict:
        """Get statistics about sources"""
        official_count = sum(1 for s in self.sources.values() if s.source_type == SourceType.OFFICIAL)
        aggregator_count = sum(1 for s in self.sources.values() if s.source_type == SourceType.AGGREGATOR)
        
        return {
            "total_sources": len(self.sources),
            "official_sources": official_count,
            "aggregator_sources": aggregator_count,
            "blocked_domains": len(self.blocked_domains),
            "enabled_sources": sum(1 for s in self.sources.values() if s.enabled)
        }


# Singleton instance
_sources_instance: Optional[TrustedSources] = None

async def get_sources_instance(db=None) -> TrustedSources:
    """Get or create sources instance"""
    global _sources_instance
    if _sources_instance is None:
        _sources_instance = TrustedSources(db)
        if db is not None:
            await _sources_instance.load_from_db()
    return _sources_instance
