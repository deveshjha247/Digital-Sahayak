"""
Server Services Module
=====================
Contains heavy services: JobScraper, AIJobMatcher, Content Rewriter

Separated from main server.py to keep files under 50KB
Size: ~45KB | Lazy loaded when needed

Garbage Collection: gc.collect() after heavy operations
Logging: Errors saved to logs/services.log
"""

import gc
import re
import json
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from pathlib import Path
import httpx
from bs4 import BeautifulSoup

# Setup logging to file
LOG_DIR = Path(__file__).parent / 'logs'
LOG_DIR.mkdir(exist_ok=True)

file_handler = logging.FileHandler(LOG_DIR / 'services.log', encoding='utf-8')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
logger.setLevel(logging.INFO)


# ===================== WEB SCRAPER SERVICE =====================

class JobScraper:
    """
    Web scraper for government job portals
    
    Features:
    - Async concurrent scraping
    - Auto category/state detection
    - Garbage collection after batch
    """
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    @staticmethod
    def clean_text(text: str) -> str:
        """Clean scraped text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    @staticmethod
    def extract_vacancies(text: str) -> int:
        """Extract number of vacancies from text"""
        matches = re.findall(r'(\d+)\s*(?:posts?|vacancies?|पद)', text.lower())
        return int(matches[0]) if matches else 0
    
    @staticmethod
    def detect_category(title: str, org: str) -> str:
        """Detect job category from title and organization"""
        text = (title + " " + org).lower()
        
        categories = {
            'railway': ['railway', 'रेलवे', 'rrb', 'ntpc'],
            'bank': ['bank', 'बैंक', 'ibps', 'sbi', 'rbi'],
            'ssc': ['ssc', 'कर्मचारी चयन', 'cgl', 'chsl', 'mts'],
            'upsc': ['upsc', 'संघ लोक सेवा', 'ias', 'ips', 'civil'],
            'police': ['police', 'पुलिस', 'constable', 'si ', 'sub inspector'],
            'defence': ['defence', 'army', 'navy', 'airforce', 'सेना'],
        }
        
        for cat, keywords in categories.items():
            if any(kw in text for kw in keywords):
                return cat
        return 'government'
    
    @staticmethod
    def detect_state(text: str) -> str:
        """Detect state from text"""
        text_lower = text.lower()
        
        state_mapping = {
            'bihar': ['bihar', 'बिहार', 'patna', 'पटना'],
            'jharkhand': ['jharkhand', 'झारखंड', 'ranchi'],
            'up': ['uttar pradesh', 'उत्तर प्रदेश', 'lucknow', 'uppsc'],
            'mp': ['madhya pradesh', 'मध्य प्रदेश', 'bhopal', 'mppsc'],
            'rajasthan': ['rajasthan', 'राजस्थान', 'jaipur', 'rpsc'],
            'maharashtra': ['maharashtra', 'महाराष्ट्र', 'mumbai', 'mpsc'],
            'wb': ['west bengal', 'पश्चिम बंगाल', 'kolkata', 'wbpsc'],
        }
        
        for state, keywords in state_mapping.items():
            if any(kw in text_lower for kw in keywords):
                return state
        return 'all'

    async def scrape_sarkari_result(self) -> List[Dict]:
        """Scrape jobs from sarkariresult.com"""
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    'https://www.sarkariresult.com/latestjob.php', 
                    headers=self.HEADERS
                )
                if response.status_code != 200:
                    logger.warning(f"Sarkari Result returned {response.status_code}")
                    return jobs
                
                soup = BeautifulSoup(response.text, 'lxml')
                job_boxes = soup.find_all('div', class_='post-box') or soup.find_all('li')
                
                for box in job_boxes[:20]:
                    try:
                        link = box.find('a')
                        if not link:
                            continue
                        
                        title = self.clean_text(link.get_text())
                        if not title or len(title) < 10:
                            continue
                        
                        href = link.get('href', '')
                        if not href.startswith('http'):
                            href = 'https://www.sarkariresult.com/' + href.lstrip('/')
                        
                        date_span = box.find('span', class_='date')
                        last_date = self.clean_text(date_span.get_text()) if date_span else "जल्द ही"
                        
                        jobs.append({
                            'title': title,
                            'title_hi': title,
                            'organization': 'Sarkari Result',
                            'organization_hi': 'सरकारी रिजल्ट',
                            'description': f"Latest job notification: {title}",
                            'description_hi': f"नवीनतम नौकरी अधिसूचना: {title}",
                            'qualification': 'विवरण के लिए आधिकारिक वेबसाइट देखें',
                            'qualification_hi': 'विवरण के लिए आधिकारिक वेबसाइट देखें',
                            'vacancies': self.extract_vacancies(title),
                            'salary': '',
                            'age_limit': '',
                            'last_date': last_date,
                            'apply_link': href,
                            'category': self.detect_category(title, ''),
                            'state': self.detect_state(title),
                            'source': 'sarkariresult.com'
                        })
                    except Exception as e:
                        logger.error(f"Error parsing job box: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Sarkari Result: {e}")
        
        return jobs
    
    async def scrape_fast_job_searchers(self) -> List[Dict]:
        """Scrape jobs from fastjobsearchers.com"""
        jobs = []
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                response = await client.get(
                    'https://www.fastjobsearchers.com/', 
                    headers=self.HEADERS
                )
                if response.status_code != 200:
                    logger.warning(f"Fast Job Searchers returned {response.status_code}")
                    return jobs
                
                soup = BeautifulSoup(response.text, 'lxml')
                articles = soup.find_all('article') or soup.find_all('div', class_='post')
                
                for article in articles[:20]:
                    try:
                        title_elem = article.find(['h2', 'h3', 'h4'])
                        if not title_elem:
                            continue
                        
                        link = title_elem.find('a') or article.find('a')
                        if not link:
                            continue
                        
                        title = self.clean_text(link.get_text())
                        if not title or len(title) < 10:
                            continue
                        
                        href = link.get('href', '')
                        summary = article.find('p')
                        desc = self.clean_text(summary.get_text()) if summary else title
                        
                        jobs.append({
                            'title': title,
                            'title_hi': title,
                            'organization': 'Fast Job Searchers',
                            'organization_hi': 'फास्ट जॉब सर्चर्स',
                            'description': desc[:500],
                            'description_hi': desc[:500],
                            'qualification': 'विवरण के लिए आधिकारिक वेबसाइट देखें',
                            'qualification_hi': 'विवरण के लिए आधिकारिक वेबसाइट देखें',
                            'vacancies': self.extract_vacancies(title + " " + desc),
                            'salary': '',
                            'age_limit': '',
                            'last_date': 'जल्द ही',
                            'apply_link': href,
                            'category': self.detect_category(title, desc),
                            'state': self.detect_state(title + " " + desc),
                            'source': 'fastjobsearchers.com'
                        })
                    except Exception as e:
                        logger.error(f"Error parsing article: {e}")
                        continue
                        
        except Exception as e:
            logger.error(f"Error scraping Fast Job Searchers: {e}")
        
        return jobs
    
    async def scrape_all(self) -> List[Dict]:
        """Scrape all configured sources with garbage collection"""
        all_jobs = []
        
        results = await asyncio.gather(
            self.scrape_sarkari_result(),
            self.scrape_fast_job_searchers(),
            return_exceptions=True
        )
        
        for result in results:
            if isinstance(result, list):
                all_jobs.extend(result)
            elif isinstance(result, Exception):
                logger.error(f"Scraper error: {result}")
        
        # Garbage collection after heavy scraping
        gc.collect()
        
        logger.info(f"Scraped {len(all_jobs)} jobs total")
        return all_jobs


# ===================== AI JOB MATCHING SERVICE =====================

class AIJobMatcher:
    """
    AI-powered job matching service
    
    Features:
    - Rule-based scoring
    - Education/Age/State matching
    - OpenAI integration (optional)
    """
    
    EDUCATION_LEVELS = {
        '10th': ['10th', 'matric', 'sslc', '10वीं', 'दसवीं', 'high school'],
        '12th': ['12th', 'intermediate', 'hsc', '12वीं', 'बारहवीं', 'higher secondary'],
        'graduate': ['graduate', 'graduation', 'bachelor', 'b.a', 'b.sc', 'b.com', 'b.tech', 'स्नातक'],
        'post_graduate': ['post graduate', 'pg', 'master', 'm.a', 'm.sc', 'm.com', 'm.tech', 'परास्नातक']
    }
    
    EDUCATION_ORDER = ['10th', '12th', 'graduate', 'post_graduate']
    
    def __init__(self, openai_client=None):
        self.openai_client = openai_client
    
    @staticmethod
    def parse_age_limit(age_limit_str: str) -> tuple:
        """Parse age limit string to get min and max age"""
        if not age_limit_str:
            return (18, 60)
        matches = re.findall(r'(\d+)', age_limit_str)
        if len(matches) >= 2:
            return (int(matches[0]), int(matches[1]))
        elif len(matches) == 1:
            return (18, int(matches[0]))
        return (18, 60)
    
    def check_education_match(self, user_education: str, job_qualification: str) -> bool:
        """Check if user's education matches job requirements"""
        if not user_education or not job_qualification:
            return True
        
        job_qual_lower = job_qualification.lower()
        
        user_level = None
        for level, keywords in self.EDUCATION_LEVELS.items():
            if any(kw in user_education.lower() for kw in keywords):
                user_level = level
                break
        
        if not user_level:
            return True
        
        required_level = None
        for level, keywords in self.EDUCATION_LEVELS.items():
            if any(kw in job_qual_lower for kw in keywords):
                required_level = level
                break
        
        if not required_level:
            return True
        
        user_idx = self.EDUCATION_ORDER.index(user_level) if user_level in self.EDUCATION_ORDER else -1
        req_idx = self.EDUCATION_ORDER.index(required_level) if required_level in self.EDUCATION_ORDER else -1
        
        return user_idx >= req_idx
    
    @staticmethod
    def check_age_match(user_age: int, age_limit_str: str) -> bool:
        """Check if user's age is within job's age limit"""
        if not user_age or not age_limit_str:
            return True
        
        min_age, max_age = AIJobMatcher.parse_age_limit(age_limit_str)
        return min_age <= user_age <= max_age
    
    @staticmethod
    def check_state_match(user_state: str, job_state: str) -> bool:
        """Check if user's state matches job's state requirement"""
        if not user_state or not job_state or job_state == 'all':
            return True
        return user_state.lower() == job_state.lower()
    
    def calculate_match_score(self, user: dict, job: dict) -> int:
        """Calculate match score between user and job (0-100)"""
        score = 50  # Base score
        
        if self.check_education_match(user.get('education_level', ''), job.get('qualification', '')):
            score += 30
        else:
            score -= 20
        
        if self.check_age_match(user.get('age'), job.get('age_limit', '')):
            score += 20
        else:
            score -= 30
        
        if self.check_state_match(user.get('state', ''), job.get('state', '')):
            score += 20
        
        preferred_cats = user.get('preferred_categories', [])
        if preferred_cats and job.get('category') in preferred_cats:
            score += 10
        
        return max(0, min(100, score))
    
    def _generate_reason(self, user: dict, job: dict, score: int) -> str:
        """Generate a simple reason for job match"""
        reasons = []
        
        if self.check_education_match(user.get('education_level', ''), job.get('qualification', '')):
            reasons.append("आपकी शिक्षा इस पद के लिए उपयुक्त है")
        
        if self.check_age_match(user.get('age'), job.get('age_limit', '')):
            reasons.append("आपकी आयु आयु सीमा में है")
        
        if self.check_state_match(user.get('state', ''), job.get('state', '')):
            reasons.append("यह नौकरी आपके राज्य में है")
        
        if user.get('preferred_categories') and job.get('category') in user.get('preferred_categories', []):
            reasons.append("यह आपकी पसंदीदा श्रेणी में है")
        
        return "; ".join(reasons) if reasons else "आपके लिए उपयुक्त हो सकती है"
    
    async def get_ai_recommendations(self, user: dict, jobs: List[dict], limit: int = 10) -> List[dict]:
        """Get AI-powered job recommendations"""
        if not self.openai_client:
            return self.get_rule_based_recommendations(user, jobs, limit)
        
        try:
            scored_jobs = []
            for job in jobs:
                score = self.calculate_match_score(user, job)
                if score >= 40:
                    scored_jobs.append({**job, 'match_score': score})
            
            scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            top_jobs = scored_jobs[:limit]
            
            if not top_jobs:
                return []
            
            # AI enhancement (optional)
            user_profile = f"""
            नाम: {user.get('name', 'उपयोगकर्ता')}
            शिक्षा: {user.get('education_level', 'अज्ञात')}
            राज्य: {user.get('state', 'भारत')}
            आयु: {user.get('age', 'अज्ञात')}
            """
            
            jobs_summary = "\n".join([
                f"- {job['title']} ({job['organization']}) - Score: {job['match_score']}%"
                for job in top_jobs[:5]
            ])
            
            prompt = f"""उपयोगकर्ता प्रोफ़ाइल:
{user_profile}

नौकरियां:
{jobs_summary}

JSON में recommendations दें।"""
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            try:
                ai_data = json.loads(ai_response)
                recommendations = ai_data.get('recommendations', [])
                
                for job in top_jobs:
                    for rec in recommendations:
                        if rec.get('job_title', '').lower() in job['title'].lower():
                            job['ai_reason'] = rec.get('reason_hi', '')
                            break
            except json.JSONDecodeError:
                pass
            
            # Garbage collection after AI call
            gc.collect()
            
            return top_jobs
            
        except Exception as e:
            logger.error(f"AI recommendation error: {e}")
            return self.get_rule_based_recommendations(user, jobs, limit)
    
    def get_rule_based_recommendations(self, user: dict, jobs: List[dict], limit: int = 10) -> List[dict]:
        """Fallback rule-based job recommendations"""
        scored_jobs = []
        
        for job in jobs:
            score = self.calculate_match_score(user, job)
            if score >= 40:
                scored_jobs.append({
                    **job,
                    'match_score': score,
                    'ai_reason': self._generate_reason(user, job, score)
                })
        
        scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        return scored_jobs[:limit]


# ===================== AI CONTENT REWRITER =====================

async def rewrite_content_with_ai(
    openai_client, 
    original_content: dict, 
    content_type: str = "job"
) -> dict:
    """
    Use AI to rewrite scraped content - Copyright Safe
    
    Args:
        openai_client: OpenAI client instance
        original_content: Original scraped content
        content_type: 'job' or 'yojana'
    
    Returns:
        Rewritten content dict
    """
    if not openai_client:
        return original_content
    
    try:
        if content_type == "job":
            prompt = f"""आप एक सरकारी नौकरी पोर्टल के content writer हैं। 
मूल जानकारी:
- Title: {original_content.get('title', '')}
- Organization: {original_content.get('organization', '')}
- Description: {original_content.get('description', '')[:300]}

JSON format में unique content लिखें:
{{"title": "...", "title_hi": "...", "description": "...", "description_hi": "...", "meta_description": "...", "highlights": ["...", "..."]}}"""
        else:
            prompt = f"""आप एक सरकारी योजना पोर्टल के content writer हैं।
मूल जानकारी:
- Name: {original_content.get('name', '')}
- Ministry: {original_content.get('ministry', '')}
- Description: {original_content.get('description', '')[:300]}

JSON format में unique content लिखें।"""

        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.7
        )
        
        ai_response = response.choices[0].message.content
        
        try:
            rewritten = json.loads(ai_response)
            return {**original_content, **rewritten, "is_rewritten": True}
        except json.JSONDecodeError:
            return original_content
            
    except Exception as e:
        logger.error(f"AI rewrite error: {e}")
        return original_content
    finally:
        gc.collect()


# ===================== SLUG GENERATION =====================

def generate_slug(text: str, state: str = "") -> str:
    """Generate SEO-friendly URL slug from title"""
    if not text:
        import uuid
        return str(uuid.uuid4())[:8]
    
    text = text.lower()
    slug = re.sub(r'[^\w\s-]', '', text)
    slug = re.sub(r'[-\s]+', '-', slug).strip('-')
    
    state_prefixes = {
        'bihar': 'br', 'jharkhand': 'jh', 'up': 'up', 'mp': 'mp',
        'rajasthan': 'rj', 'maharashtra': 'mh', 'wb': 'wb', 'all': ''
    }
    
    prefix = state_prefixes.get(state.lower(), '')
    if prefix:
        slug = f"{prefix}/{slug}"
    
    if len(slug) > 100:
        slug = slug[:100].rsplit('-', 1)[0]
    
    return slug


# ===================== LAZY LOADING INSTANCES =====================

_job_scraper = None
_ai_job_matcher = None


def get_job_scraper() -> JobScraper:
    """Lazy load JobScraper instance"""
    global _job_scraper
    if _job_scraper is None:
        _job_scraper = JobScraper()
    return _job_scraper


def get_ai_job_matcher(openai_client=None) -> AIJobMatcher:
    """Lazy load AIJobMatcher instance"""
    global _ai_job_matcher
    if _ai_job_matcher is None:
        _ai_job_matcher = AIJobMatcher(openai_client)
    return _ai_job_matcher


# Export
__all__ = [
    'JobScraper', 
    'AIJobMatcher', 
    'rewrite_content_with_ai',
    'generate_slug',
    'get_job_scraper',
    'get_ai_job_matcher'
]
