"""
DS-Search Policy Engine
========================
Decides WHEN to search and WHEN NOT to search.

Search Score Algorithm (0-1):
- Score >= 0.55 → Trigger search
- Score < 0.55 → No search needed

Positive Factors:
+0.30 if words include: "latest/new/2026/last date/result"
+0.25 if user asks a question ("kya", "kab", "link")
+0.20 if internal DB has 0 results
+0.10 if user includes a URL

Negative Factors:
-0.40 if intent is greeting/small talk
-0.30 if request is "my status / my profile"
"""

import re
import logging
from typing import Dict, Tuple, List, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SearchIntent(Enum):
    """User query intent categories"""
    GREETING = "greeting"
    SMALL_TALK = "small_talk"
    PERSONAL_STATUS = "personal_status"
    JOB_QUERY = "job_query"
    YOJANA_QUERY = "yojana_query"
    RESULT_QUERY = "result_query"
    DATE_QUERY = "date_query"
    DOCUMENT_QUERY = "document_query"
    GENERAL_INFO = "general_info"
    URL_FETCH = "url_fetch"
    BLOCKED = "blocked"
    UNKNOWN = "unknown"


@dataclass
class PolicyDecision:
    """Search policy decision result"""
    should_search: bool
    search_score: float
    intent: SearchIntent
    reason: str
    search_type: str  # "internal", "cache", "crawler", "api", "none"
    rate_limited: bool = False


class SearchPolicy:
    """
    Policy engine for DS-Search decisions.
    Implements smart scoring to decide when to search.
    """
    
    # Search score threshold
    SEARCH_THRESHOLD = 0.55
    
    # Rate limits
    MAX_SEARCHES_PER_USER_PER_DAY = 50
    MAX_SEARCHES_PER_MINUTE = 5
    
    # Patterns for intent detection
    GREETING_PATTERNS = [
        r'^(hi|hello|hey|namaste|namaskar|good\s*(morning|evening|night|afternoon))[\s!.]*$',
        r'^(धन्यवाद|शुक्रिया|thanks|thank\s*you|ok|okay|thik|ठीक)[\s!.]*$',
        r'^(bye|goodbye|alvida|फिर\s*मिलेंगे)[\s!.]*$',
        r'^(haan|ha|yes|no|nahi|नहीं)[\s!.]*$'
    ]
    
    PERSONAL_STATUS_PATTERNS = [
        r'(mera|my|apna)\s*(status|application|payment|profile|account)',
        r'(मेरा|अपना)\s*(स्टेटस|आवेदन|भुगतान|प्रोफाइल)',
        r'(show|check|dekho|dikhao)\s*(my|mera|apna)',
        r'(login|logout|password|otp)\s*(karo|karna|change)',
    ]
    
    BLOCKED_PATTERNS = [
        r'(hack|bypass|crack|cheat|pirate)',
        r'(otp\s*bypass|captcha\s*(bypass|break))',
        r'(password\s*crack|account\s*hack)',
        r'(free\s*recharge|unlimited\s*money)',
        r'(phishing|scam|fraud\s*kaise)'
    ]
    
    # Positive search triggers
    SEARCH_TRIGGER_PATTERNS = [
        (r'(latest|new|नया|नई|recent|fresh|2024|2025|2026)', 0.30),
        (r'(last\s*date|अंतिम\s*तिथि|deadline|cutoff|cut\s*off)', 0.30),
        (r'(result|रिजल्ट|परिणाम|merit\s*list|answer\s*key)', 0.30),
        (r'(notification|नोटिफिकेशन|admit\s*card|एडमिट)', 0.25),
        (r'(vacancy|भर्ती|recruitment|bharti|job\s*opening)', 0.25),
        (r'(kab|कब|when|date|तारीख|schedule)', 0.25),
        (r'(kya|क्या|what|kaise|कैसे|how|link|लिंक)', 0.25),
        (r'(eligibility|पात्रता|योग्यता|criteria)', 0.20),
        (r'(form|फॉर्म|apply|आवेदन|registration)', 0.20),
        (r'(salary|सैलरी|वेतन|pay\s*scale)', 0.20),
        (r'(syllabus|सिलेबस|pattern|पैटर्न)', 0.20),
        (r'https?://\S+', 0.10),  # URL in query
    ]
    
    # Job/Exam keywords
    JOB_KEYWORDS = [
        'ssc', 'upsc', 'railway', 'rrb', 'ibps', 'bank', 'police',
        'army', 'navy', 'airforce', 'nda', 'cds', 'capf', 'cisf', 'crpf',
        'bsf', 'itbp', 'ssb', 'constable', 'si', 'inspector',
        'clerk', 'po', 'so', 'assistant', 'steno', 'typist',
        'teacher', 'tet', 'ctet', 'stet', 'lecturer', 'professor',
        'engineer', 'je', 'ae', 'scientist', 'drdo', 'isro',
        'भर्ती', 'नौकरी', 'वैकेंसी', 'सरकारी'
    ]
    
    # Yojana keywords
    YOJANA_KEYWORDS = [
        'yojana', 'योजना', 'scheme', 'pm', 'cm', 'pradhan mantri',
        'mukhyamantri', 'प्रधानमंत्री', 'मुख्यमंत्री', 'subsidy', 'अनुदान',
        'pension', 'पेंशन', 'scholarship', 'छात्रवृत्ति', 'loan', 'ऋण',
        'kisan', 'किसान', 'mahila', 'महिला', 'yuva', 'युवा',
        'awas', 'आवास', 'ration', 'राशन', 'aadhar', 'आधार',
        'ayushman', 'आयुष्मान', 'ujjwala', 'उज्ज्वला', 'mudra', 'मुद्रा'
    ]
    
    # State names for context
    STATES = [
        'bihar', 'बिहार', 'up', 'uttar pradesh', 'उत्तर प्रदेश',
        'mp', 'madhya pradesh', 'मध्य प्रदेश', 'rajasthan', 'राजस्थान',
        'maharashtra', 'महाराष्ट्र', 'gujarat', 'गुजरात', 'delhi', 'दिल्ली',
        'haryana', 'हरियाणा', 'punjab', 'पंजाब', 'jharkhand', 'झारखंड',
        'chhattisgarh', 'छत्तीसगढ़', 'odisha', 'ओडिशा', 'assam', 'असम',
        'west bengal', 'पश्चिम बंगाल', 'tamil nadu', 'तमिलनाडु',
        'karnataka', 'कर्नाटक', 'kerala', 'केरल', 'telangana', 'तेलंगाना'
    ]
    
    def __init__(self, db=None):
        self.db = db
        self.user_search_counts: Dict[str, Dict] = {}  # In-memory rate limiting
    
    def detect_intent(self, query: str) -> SearchIntent:
        """
        Detect the intent of user query.
        
        Args:
            query: User's query text
            
        Returns:
            SearchIntent enum value
        """
        query_lower = query.lower().strip()
        
        # Check blocked patterns first
        for pattern in self.BLOCKED_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return SearchIntent.BLOCKED
        
        # Check greeting patterns
        for pattern in self.GREETING_PATTERNS:
            if re.match(pattern, query_lower, re.IGNORECASE):
                return SearchIntent.GREETING
        
        # Check personal status patterns
        for pattern in self.PERSONAL_STATUS_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                return SearchIntent.PERSONAL_STATUS
        
        # Check for URL fetch intent
        if re.search(r'https?://\S+', query_lower):
            if any(word in query_lower for word in ['check', 'fetch', 'summarize', 'देखो', 'बताओ']):
                return SearchIntent.URL_FETCH
        
        # Check for result query
        if re.search(r'(result|रिजल्ट|परिणाम|merit|answer\s*key)', query_lower, re.IGNORECASE):
            return SearchIntent.RESULT_QUERY
        
        # Check for job query
        if any(keyword in query_lower for keyword in self.JOB_KEYWORDS):
            return SearchIntent.JOB_QUERY
        
        # Check for yojana query
        if any(keyword in query_lower for keyword in self.YOJANA_KEYWORDS):
            return SearchIntent.YOJANA_QUERY
        
        # Check for date/time query
        if re.search(r'(kab|कब|when|date|तारीख|schedule|time)', query_lower, re.IGNORECASE):
            return SearchIntent.DATE_QUERY
        
        # Check for document query
        if re.search(r'(document|दस्तावेज|paper|form|फॉर्म|certificate)', query_lower, re.IGNORECASE):
            return SearchIntent.DOCUMENT_QUERY
        
        # Default to general info
        if len(query_lower.split()) >= 3:
            return SearchIntent.GENERAL_INFO
        
        return SearchIntent.UNKNOWN
    
    def calculate_search_score(self, query: str, intent: SearchIntent, 
                               internal_results_count: int = 0) -> float:
        """
        Calculate search score to decide if search should be triggered.
        
        Args:
            query: User's query
            intent: Detected intent
            internal_results_count: Number of results from internal DB
            
        Returns:
            Search score between 0 and 1
        """
        score = 0.0
        query_lower = query.lower()
        
        # Negative factors
        if intent == SearchIntent.GREETING:
            score -= 0.40
        elif intent == SearchIntent.SMALL_TALK:
            score -= 0.35
        elif intent == SearchIntent.PERSONAL_STATUS:
            score -= 0.30
        elif intent == SearchIntent.BLOCKED:
            score -= 1.0  # Block completely
        
        # Positive factors from patterns
        for pattern, weight in self.SEARCH_TRIGGER_PATTERNS:
            if re.search(pattern, query_lower, re.IGNORECASE):
                score += weight
        
        # Add score if internal DB has no results
        if internal_results_count == 0:
            score += 0.20
        elif internal_results_count < 3:
            score += 0.10
        
        # Intent-based bonuses
        if intent in [SearchIntent.JOB_QUERY, SearchIntent.YOJANA_QUERY, 
                      SearchIntent.RESULT_QUERY, SearchIntent.DATE_QUERY]:
            score += 0.15
        
        if intent == SearchIntent.URL_FETCH:
            score += 0.30
        
        # State mention adds relevance
        if any(state in query_lower for state in self.STATES):
            score += 0.05
        
        # Cap the score between 0 and 1
        return max(0.0, min(1.0, score))
    
    def check_rate_limit(self, user_id: str) -> Tuple[bool, str]:
        """
        Check if user has exceeded rate limits.
        
        Args:
            user_id: User's unique identifier
            
        Returns:
            Tuple of (is_allowed, reason)
        """
        import time
        current_time = time.time()
        
        if user_id not in self.user_search_counts:
            self.user_search_counts[user_id] = {
                'daily_count': 0,
                'daily_reset': current_time + 86400,  # 24 hours
                'minute_count': 0,
                'minute_reset': current_time + 60
            }
        
        user_limits = self.user_search_counts[user_id]
        
        # Reset daily counter if needed
        if current_time > user_limits['daily_reset']:
            user_limits['daily_count'] = 0
            user_limits['daily_reset'] = current_time + 86400
        
        # Reset minute counter if needed
        if current_time > user_limits['minute_reset']:
            user_limits['minute_count'] = 0
            user_limits['minute_reset'] = current_time + 60
        
        # Check daily limit
        if user_limits['daily_count'] >= self.MAX_SEARCHES_PER_USER_PER_DAY:
            return False, "Daily search limit reached. Try again tomorrow."
        
        # Check per-minute limit
        if user_limits['minute_count'] >= self.MAX_SEARCHES_PER_MINUTE:
            return False, "Too many searches. Please wait a moment."
        
        return True, "OK"
    
    def increment_search_count(self, user_id: str):
        """Increment search count for user after successful search"""
        if user_id in self.user_search_counts:
            self.user_search_counts[user_id]['daily_count'] += 1
            self.user_search_counts[user_id]['minute_count'] += 1
    
    def evaluate(self, query: str, user_id: str = None, 
                 internal_results_count: int = 0) -> PolicyDecision:
        """
        Main policy evaluation - decides whether to search.
        
        Args:
            query: User's query
            user_id: User identifier for rate limiting
            internal_results_count: Results from internal DB
            
        Returns:
            PolicyDecision with all details
        """
        # Detect intent
        intent = self.detect_intent(query)
        
        # Block harmful queries
        if intent == SearchIntent.BLOCKED:
            return PolicyDecision(
                should_search=False,
                search_score=0.0,
                intent=intent,
                reason="Query blocked by safety policy",
                search_type="none"
            )
        
        # Skip search for greetings and personal status
        if intent in [SearchIntent.GREETING, SearchIntent.SMALL_TALK]:
            return PolicyDecision(
                should_search=False,
                search_score=0.0,
                intent=intent,
                reason="Conversational query - no search needed",
                search_type="none"
            )
        
        if intent == SearchIntent.PERSONAL_STATUS:
            return PolicyDecision(
                should_search=False,
                search_score=0.0,
                intent=intent,
                reason="Personal data query - use internal DB only",
                search_type="internal"
            )
        
        # Check rate limits
        if user_id:
            is_allowed, limit_reason = self.check_rate_limit(user_id)
            if not is_allowed:
                return PolicyDecision(
                    should_search=False,
                    search_score=0.0,
                    intent=intent,
                    reason=limit_reason,
                    search_type="none",
                    rate_limited=True
                )
        
        # Calculate search score
        search_score = self.calculate_search_score(query, intent, internal_results_count)
        
        # Decide search type based on score
        if search_score >= self.SEARCH_THRESHOLD:
            search_type = "crawler"  # Default to free crawler
            reason = f"Search triggered (score: {search_score:.2f})"
        else:
            search_type = "internal"
            reason = f"Internal search only (score: {search_score:.2f})"
        
        return PolicyDecision(
            should_search=search_score >= self.SEARCH_THRESHOLD,
            search_score=search_score,
            intent=intent,
            reason=reason,
            search_type=search_type
        )
    
    def choose_crawl_plan(self, intent: SearchIntent, query: str) -> Dict:
        """
        Choose crawling strategy based on intent.
        
        Args:
            intent: Detected search intent
            query: User's query
            
        Returns:
            Crawl plan configuration
        """
        base_plan = {
            "max_pages": 5,
            "timeout": 10,
            "prefer_official": True,
            "domains": []
        }
        
        if intent == SearchIntent.JOB_QUERY:
            base_plan["domains"] = [
                "ssc.nic.in", "upsc.gov.in", "indianrailways.gov.in",
                "rrbcdg.gov.in", "ibps.in", "nta.ac.in"
            ]
            base_plan["max_pages"] = 8
        
        elif intent == SearchIntent.YOJANA_QUERY:
            base_plan["domains"] = [
                "india.gov.in", "pmjay.gov.in", "pmkisan.gov.in",
                "nrega.nic.in", "uidai.gov.in"
            ]
            base_plan["max_pages"] = 6
        
        elif intent == SearchIntent.RESULT_QUERY:
            base_plan["domains"] = [
                "ssc.nic.in", "upsc.gov.in", "nta.ac.in",
                "cbseresults.nic.in", "biharboardonline.com"
            ]
            base_plan["max_pages"] = 10
            base_plan["timeout"] = 15
        
        elif intent == SearchIntent.URL_FETCH:
            # Extract URL from query
            url_match = re.search(r'https?://\S+', query)
            if url_match:
                base_plan["specific_url"] = url_match.group()
            base_plan["max_pages"] = 1
        
        return base_plan


# Singleton instance
_policy_instance: Optional[SearchPolicy] = None

def get_policy_instance(db=None) -> SearchPolicy:
    """Get or create policy instance"""
    global _policy_instance
    if _policy_instance is None:
        _policy_instance = SearchPolicy(db)
    return _policy_instance
