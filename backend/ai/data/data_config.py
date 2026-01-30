"""
Data Collection Configuration
Defines sources, categories, states, and collection parameters
"""

from typing import Dict, List, Any
from dataclasses import dataclass, field
from enum import Enum

# =============================================================================
# DATA SOURCES - Multiple sources for diversity
# =============================================================================

SOURCES = {
    # Government Job Portals
    "government_portals": {
        "sarkari_result": {
            "url": "https://www.sarkariresult.com",
            "type": "scraper",
            "content_types": ["jobs", "results", "admit_cards"],
            "robots_txt_compliant": True,
            "rate_limit_seconds": 2,
            "priority": 1,
        },
        "ncs_gov": {
            "url": "https://www.ncs.gov.in",
            "type": "api",
            "content_types": ["jobs", "schemes"],
            "api_key_required": False,
            "rate_limit_seconds": 1,
            "priority": 1,
        },
        "employment_news": {
            "url": "https://employmentnews.gov.in",
            "type": "scraper",
            "content_types": ["jobs"],
            "robots_txt_compliant": True,
            "rate_limit_seconds": 2,
            "priority": 2,
        },
    },
    
    # Scheme Portals
    "scheme_portals": {
        "myscheme_gov": {
            "url": "https://www.myscheme.gov.in",
            "type": "api",
            "content_types": ["schemes"],
            "api_key_required": False,
            "rate_limit_seconds": 1,
            "priority": 1,
        },
        "india_gov": {
            "url": "https://www.india.gov.in/my-government/schemes",
            "type": "scraper",
            "content_types": ["schemes"],
            "robots_txt_compliant": True,
            "rate_limit_seconds": 2,
            "priority": 2,
        },
    },
    
    # State-specific Portals (for diversity)
    "state_portals": {
        "bihar": {
            "url": "https://state.bihar.gov.in",
            "state": "Bihar",
            "content_types": ["jobs", "schemes"],
        },
        "up": {
            "url": "https://up.gov.in",
            "state": "Uttar Pradesh",
            "content_types": ["jobs", "schemes"],
        },
        "mp": {
            "url": "https://mp.gov.in",
            "state": "Madhya Pradesh",
            "content_types": ["jobs", "schemes"],
        },
        "rajasthan": {
            "url": "https://rajasthan.gov.in",
            "state": "Rajasthan",
            "content_types": ["jobs", "schemes"],
        },
        "jharkhand": {
            "url": "https://jharkhand.gov.in",
            "state": "Jharkhand",
            "content_types": ["jobs", "schemes"],
        },
    },
    
    # News & Educational Blogs
    "news_education": {
        "jagranjosh": {
            "url": "https://www.jagranjosh.com/government-jobs",
            "type": "scraper",
            "content_types": ["jobs", "syllabus", "answer_keys"],
            "language": "bilingual",
        },
        "aglasem": {
            "url": "https://aglasem.com",
            "type": "scraper",
            "content_types": ["admit_cards", "results", "syllabus"],
            "language": "english",
        },
    },
    
    # Open Datasets
    "open_datasets": {
        "data_gov_in": {
            "url": "https://data.gov.in",
            "type": "api",
            "content_types": ["statistics", "demographics"],
            "license": "open_government_license",
        },
    },
}

# =============================================================================
# JOB/SCHEME CATEGORIES - For balanced class distribution
# =============================================================================

CATEGORIES = {
    "job_categories": {
        "railway": {"en": "Railway", "hi": "रेलवे", "weight": 1.0},
        "ssc": {"en": "SSC", "hi": "एसएससी", "weight": 1.0},
        "upsc": {"en": "UPSC", "hi": "यूपीएससी", "weight": 0.8},
        "bank": {"en": "Bank", "hi": "बैंक", "weight": 1.0},
        "police": {"en": "Police", "hi": "पुलिस", "weight": 1.0},
        "teaching": {"en": "Teaching", "hi": "शिक्षण", "weight": 1.0},
        "defence": {"en": "Defence", "hi": "रक्षा", "weight": 0.9},
        "psc": {"en": "State PSC", "hi": "राज्य पीएससी", "weight": 1.0},
        "court": {"en": "Court", "hi": "न्यायालय", "weight": 0.7},
        "healthcare": {"en": "Healthcare", "hi": "स्वास्थ्य", "weight": 0.9},
        "engineering": {"en": "Engineering", "hi": "इंजीनियरिंग", "weight": 0.8},
        "agriculture": {"en": "Agriculture", "hi": "कृषि", "weight": 0.7},
    },
    
    "scheme_categories": {
        "education": {"en": "Education", "hi": "शिक्षा", "weight": 1.0},
        "employment": {"en": "Employment", "hi": "रोजगार", "weight": 1.0},
        "health": {"en": "Health", "hi": "स्वास्थ्य", "weight": 1.0},
        "agriculture": {"en": "Agriculture", "hi": "कृषि", "weight": 0.9},
        "housing": {"en": "Housing", "hi": "आवास", "weight": 0.8},
        "women_welfare": {"en": "Women Welfare", "hi": "महिला कल्याण", "weight": 0.9},
        "social_security": {"en": "Social Security", "hi": "सामाजिक सुरक्षा", "weight": 1.0},
        "skill_development": {"en": "Skill Development", "hi": "कौशल विकास", "weight": 1.0},
        "financial_inclusion": {"en": "Financial Inclusion", "hi": "वित्तीय समावेशन", "weight": 0.8},
    },
}

# =============================================================================
# INDIAN STATES - For geographic diversity
# =============================================================================

STATES = {
    # Large states (higher sampling weight)
    "uttar_pradesh": {"en": "Uttar Pradesh", "hi": "उत्तर प्रदेश", "weight": 1.2, "population_rank": 1},
    "maharashtra": {"en": "Maharashtra", "hi": "महाराष्ट्र", "weight": 1.1, "population_rank": 2},
    "bihar": {"en": "Bihar", "hi": "बिहार", "weight": 1.1, "population_rank": 3},
    "west_bengal": {"en": "West Bengal", "hi": "पश्चिम बंगाल", "weight": 1.0, "population_rank": 4},
    "madhya_pradesh": {"en": "Madhya Pradesh", "hi": "मध्य प्रदेश", "weight": 1.0, "population_rank": 5},
    
    # Medium states
    "tamil_nadu": {"en": "Tamil Nadu", "hi": "तमिलनाडु", "weight": 0.9, "population_rank": 6},
    "rajasthan": {"en": "Rajasthan", "hi": "राजस्थान", "weight": 1.0, "population_rank": 7},
    "karnataka": {"en": "Karnataka", "hi": "कर्नाटक", "weight": 0.9, "population_rank": 8},
    "gujarat": {"en": "Gujarat", "hi": "गुजरात", "weight": 0.9, "population_rank": 9},
    "andhra_pradesh": {"en": "Andhra Pradesh", "hi": "आंध्र प्रदेश", "weight": 0.8, "population_rank": 10},
    
    # Smaller states (ensure representation)
    "jharkhand": {"en": "Jharkhand", "hi": "झारखंड", "weight": 0.9, "population_rank": 14},
    "odisha": {"en": "Odisha", "hi": "ओडिशा", "weight": 0.8, "population_rank": 11},
    "kerala": {"en": "Kerala", "hi": "केरल", "weight": 0.7, "population_rank": 13},
    "chhattisgarh": {"en": "Chhattisgarh", "hi": "छत्तीसगढ़", "weight": 0.8, "population_rank": 17},
    "punjab": {"en": "Punjab", "hi": "पंजाब", "weight": 0.7, "population_rank": 16},
    "haryana": {"en": "Haryana", "hi": "हरियाणा", "weight": 0.7, "population_rank": 18},
    "uttarakhand": {"en": "Uttarakhand", "hi": "उत्तराखंड", "weight": 0.6, "population_rank": 20},
    "himachal_pradesh": {"en": "Himachal Pradesh", "hi": "हिमाचल प्रदेश", "weight": 0.5, "population_rank": 21},
    
    # Union Territories
    "delhi": {"en": "Delhi", "hi": "दिल्ली", "weight": 0.8, "population_rank": 19},
    "chandigarh": {"en": "Chandigarh", "hi": "चंडीगढ़", "weight": 0.4, "population_rank": 30},
    
    # Northeast (ensure representation for diversity)
    "assam": {"en": "Assam", "hi": "असम", "weight": 0.6, "population_rank": 15},
    "tripura": {"en": "Tripura", "hi": "त्रिपुरा", "weight": 0.4, "population_rank": 22},
    "meghalaya": {"en": "Meghalaya", "hi": "मेघालय", "weight": 0.4, "population_rank": 23},
    "manipur": {"en": "Manipur", "hi": "मणिपुर", "weight": 0.4, "population_rank": 24},
    "nagaland": {"en": "Nagaland", "hi": "नागालैंड", "weight": 0.3, "population_rank": 25},
    "arunachal_pradesh": {"en": "Arunachal Pradesh", "hi": "अरुणाचल प्रदेश", "weight": 0.3, "population_rank": 28},
    
    # All India
    "all_india": {"en": "All India", "hi": "अखिल भारतीय", "weight": 1.5, "population_rank": 0},
}

# =============================================================================
# EDUCATION LEVELS
# =============================================================================

EDUCATION_LEVELS = {
    "below_10th": {"en": "Below 10th", "hi": "दसवीं से कम", "order": 0, "weight": 0.3},
    "10th_pass": {"en": "10th Pass", "hi": "दसवीं पास", "order": 1, "weight": 1.0},
    "12th_pass": {"en": "12th Pass", "hi": "बारहवीं पास", "order": 2, "weight": 1.2},
    "diploma": {"en": "Diploma", "hi": "डिप्लोमा", "order": 3, "weight": 0.8},
    "iti": {"en": "ITI", "hi": "आईटीआई", "order": 3, "weight": 0.7},
    "graduate": {"en": "Graduate", "hi": "स्नातक", "order": 4, "weight": 1.0},
    "post_graduate": {"en": "Post Graduate", "hi": "स्नातकोत्तर", "order": 5, "weight": 0.7},
    "doctorate": {"en": "Doctorate", "hi": "डॉक्टरेट", "order": 6, "weight": 0.3},
    "any": {"en": "Any", "hi": "कोई भी", "order": -1, "weight": 0.5},
}

# =============================================================================
# DATA COLLECTION CONFIG
# =============================================================================

@dataclass
class DataConfig:
    """Configuration for data collection"""
    
    # Rate limiting
    default_rate_limit: float = 2.0  # seconds between requests
    max_concurrent_requests: int = 3
    
    # Retry settings
    max_retries: int = 3
    retry_delay: float = 5.0
    
    # Data diversity targets
    min_states_coverage: int = 15  # Minimum states to cover
    min_categories_per_state: int = 5
    target_class_balance_ratio: float = 0.7  # Min ratio between smallest and largest class
    
    # Collection limits
    max_items_per_source: int = 1000
    max_items_per_category: int = 500
    
    # Quality filters
    min_description_length: int = 50
    required_fields: List[str] = field(default_factory=lambda: ["title", "description", "source"])
    
    # Storage
    raw_data_path: str = "raw/"
    processed_data_path: str = "processed/"
    
    # Metadata
    include_metadata: bool = True
    metadata_fields: List[str] = field(default_factory=lambda: [
        "source", "collection_date", "state", "category", 
        "language", "verified", "url", "content_hash"
    ])


# =============================================================================
# SCRAPING RULES (robots.txt compliance)
# =============================================================================

SCRAPING_RULES = {
    "default": {
        "respect_robots_txt": True,
        "user_agent": "DigitalSahayakBot/1.0 (Educational/Research; +https://digitalsahayak.in/bot)",
        "crawl_delay": 2,
        "max_pages_per_domain": 100,
        "allowed_content_types": ["text/html", "application/json", "application/pdf"],
    },
    
    "rate_limits": {
        "default": 2.0,  # seconds
        "government_sites": 3.0,  # More respectful to gov sites
        "news_sites": 1.5,
        "api_endpoints": 1.0,
    },
    
    "excluded_paths": [
        "/admin",
        "/login",
        "/register",
        "/private",
        "/api/internal",
    ],
}
