from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Request, Query, Body, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
from passlib.context import CryptContext
from jose import JWTError, jwt
import httpx
import json
import hashlib
import hmac
import asyncio
import re
from bs4 import BeautifulSoup
from openai import OpenAI

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
SECRET_KEY = os.environ.get('JWT_SECRET', 'digital-sahayak-super-secret-key-2025')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_DAYS = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Cashfree Configuration
CASHFREE_APP_ID = os.environ.get('CASHFREE_APP_ID', '')
CASHFREE_SECRET_KEY = os.environ.get('CASHFREE_SECRET_KEY', '')
CASHFREE_ENV = os.environ.get('CASHFREE_ENV', 'PRODUCTION')

# WhatsApp Configuration (MOCK for now)
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID', '')
WHATSAPP_ACCESS_TOKEN = os.environ.get('WHATSAPP_ACCESS_TOKEN', '')
WHATSAPP_VERIFY_TOKEN = os.environ.get('WHATSAPP_VERIFY_TOKEN', 'digital_sahayak_verify_token')

# OpenAI Configuration (Emergent LLM Key)
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY', '')
openai_client = OpenAI(api_key=EMERGENT_LLM_KEY) if EMERGENT_LLM_KEY else None

app = FastAPI(title="Digital Sahayak API", version="1.0.0")
api_router = APIRouter(prefix="/api")
security = HTTPBearer(auto_error=False)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ===================== MODELS =====================

class UserCreate(BaseModel):
    name: str
    email: Optional[EmailStr] = None
    phone: str
    password: str
    language: str = "hi"
    # New fields for AI matching
    education_level: Optional[str] = None  # 10th, 12th, graduate, post_graduate
    state: Optional[str] = None
    age: Optional[int] = None
    preferred_categories: List[str] = []

class UserLogin(BaseModel):
    phone: str
    password: str

class UserProfile(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: str
    language: str = "hi"
    is_admin: bool = False
    is_operator: bool = False
    documents: List[Dict] = []
    whatsapp_connected: bool = False
    created_at: datetime
    # New fields for AI matching
    education_level: Optional[str] = None
    state: Optional[str] = None
    age: Optional[int] = None
    preferred_categories: List[str] = []

class UserProfileUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    education_level: Optional[str] = None
    state: Optional[str] = None
    age: Optional[int] = None
    preferred_categories: Optional[List[str]] = None

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserProfile

class JobAlertCreate(BaseModel):
    title: str
    title_hi: Optional[str] = None
    organization: str
    organization_hi: Optional[str] = None
    description: str
    description_hi: Optional[str] = None
    vacancies: int = 0
    qualification: str
    qualification_hi: Optional[str] = None
    age_limit: str = ""
    salary: str = ""
    last_date: str
    apply_link: str
    category: str = "government"
    state: str = "all"
    is_active: bool = True

class YojanaCreate(BaseModel):
    name: str
    name_hi: Optional[str] = None
    ministry: str
    ministry_hi: Optional[str] = None
    description: str
    description_hi: Optional[str] = None
    benefits: str
    benefits_hi: Optional[str] = None
    eligibility: str
    eligibility_hi: Optional[str] = None
    documents_required: List[str] = []
    apply_link: str
    category: str = "welfare"
    state: str = "all"
    govt_fee: float = 0
    service_fee: float = 20
    is_active: bool = True

class ApplicationCreate(BaseModel):
    item_type: str  # "job" or "yojana"
    item_id: str
    user_details: Dict[str, Any]
    documents: List[str] = []

class PaymentCreate(BaseModel):
    application_id: str
    amount: float
    return_url: str

class WhatsAppMessage(BaseModel):
    phone: str
    message: str
    template: Optional[str] = None

# ===================== HELPER FUNCTIONS =====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = await db.users.find_one({"id": user_id}, {"_id": 0, "password": 0})
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_admin_user(user: dict = Depends(get_current_user)):
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user

# ===================== WEB SCRAPER SERVICE =====================

class JobScraper:
    """Web scraper for government job portals"""
    
    HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
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
        if matches:
            return int(matches[0])
        return 0
    
    @staticmethod
    def detect_category(title: str, org: str) -> str:
        """Detect job category from title and organization"""
        text = (title + " " + org).lower()
        if any(word in text for word in ['railway', 'रेलवे', 'rrb', 'ntpc']):
            return 'railway'
        elif any(word in text for word in ['bank', 'बैंक', 'ibps', 'sbi', 'rbi']):
            return 'bank'
        elif any(word in text for word in ['ssc', 'कर्मचारी चयन', 'cgl', 'chsl', 'mts']):
            return 'ssc'
        elif any(word in text for word in ['upsc', 'संघ लोक सेवा', 'ias', 'ips', 'civil']):
            return 'upsc'
        elif any(word in text for word in ['police', 'पुलिस', 'constable', 'si ', 'sub inspector']):
            return 'police'
        elif any(word in text for word in ['defence', 'army', 'navy', 'airforce', 'सेना']):
            return 'defence'
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
                response = await client.get('https://www.sarkariresult.com/latestjob.php', headers=self.HEADERS)
                if response.status_code != 200:
                    logger.warning(f"Sarkari Result returned {response.status_code}")
                    return jobs
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find job listings
                job_boxes = soup.find_all('div', class_='post-box')
                if not job_boxes:
                    job_boxes = soup.find_all('li')
                
                for box in job_boxes[:20]:  # Limit to 20 jobs
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
                        
                        # Extract date if available
                        date_span = box.find('span', class_='date')
                        last_date = self.clean_text(date_span.get_text()) if date_span else "जल्द ही"
                        
                        jobs.append({
                            'title': title,
                            'title_hi': title,  # Many titles are already in Hindi
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
                response = await client.get('https://www.fastjobsearchers.com/', headers=self.HEADERS)
                if response.status_code != 200:
                    logger.warning(f"Fast Job Searchers returned {response.status_code}")
                    return jobs
                
                soup = BeautifulSoup(response.text, 'lxml')
                
                # Find job listings
                articles = soup.find_all('article')
                if not articles:
                    articles = soup.find_all('div', class_='post')
                
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
                        
                        # Extract summary
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
        """Scrape all configured sources"""
        all_jobs = []
        
        # Run scrapers concurrently
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
        
        logger.info(f"Scraped {len(all_jobs)} jobs total")
        return all_jobs

job_scraper = JobScraper()

# ===================== AI JOB MATCHING SERVICE =====================

class AIJobMatcher:
    """AI-powered job matching service using OpenAI"""
    
    EDUCATION_LEVELS = {
        '10th': ['10th', 'matric', 'sslc', '10वीं', 'दसवीं', 'high school'],
        '12th': ['12th', 'intermediate', 'hsc', '12वीं', 'बारहवीं', 'higher secondary'],
        'graduate': ['graduate', 'graduation', 'bachelor', 'b.a', 'b.sc', 'b.com', 'b.tech', 'स्नातक'],
        'post_graduate': ['post graduate', 'pg', 'master', 'm.a', 'm.sc', 'm.com', 'm.tech', 'परास्नातक']
    }
    
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
    
    @staticmethod
    def check_education_match(user_education: str, job_qualification: str) -> bool:
        """Check if user's education matches job requirements"""
        if not user_education or not job_qualification:
            return True
        
        job_qual_lower = job_qualification.lower()
        
        # Education hierarchy: 10th < 12th < graduate < post_graduate
        education_order = ['10th', '12th', 'graduate', 'post_graduate']
        
        user_level = None
        for level, keywords in AIJobMatcher.EDUCATION_LEVELS.items():
            if any(kw in user_education.lower() for kw in keywords):
                user_level = level
                break
        
        if not user_level:
            return True  # Can't determine, show job
        
        # Check what the job requires
        required_level = None
        for level, keywords in AIJobMatcher.EDUCATION_LEVELS.items():
            if any(kw in job_qual_lower for kw in keywords):
                required_level = level
                break
        
        if not required_level:
            return True
        
        # User should have equal or higher education
        user_idx = education_order.index(user_level) if user_level in education_order else -1
        req_idx = education_order.index(required_level) if required_level in education_order else -1
        
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
    
    @staticmethod
    def calculate_match_score(user: dict, job: dict) -> int:
        """Calculate match score between user and job (0-100)"""
        score = 50  # Base score
        
        # Education match (+30)
        if AIJobMatcher.check_education_match(
            user.get('education_level', ''),
            job.get('qualification', '')
        ):
            score += 30
        else:
            score -= 20
        
        # Age match (+20)
        if AIJobMatcher.check_age_match(
            user.get('age'),
            job.get('age_limit', '')
        ):
            score += 20
        else:
            score -= 30
        
        # State match (+20)
        if AIJobMatcher.check_state_match(
            user.get('state', ''),
            job.get('state', '')
        ):
            score += 20
        
        # Category preference (+10)
        preferred_cats = user.get('preferred_categories', [])
        if preferred_cats and job.get('category') in preferred_cats:
            score += 10
        
        return max(0, min(100, score))
    
    async def get_ai_recommendations(self, user: dict, jobs: List[dict], limit: int = 10) -> List[dict]:
        """Get AI-powered job recommendations"""
        if not openai_client:
            # Fallback to rule-based matching
            return self.get_rule_based_recommendations(user, jobs, limit)
        
        try:
            # Calculate scores for all jobs
            scored_jobs = []
            for job in jobs:
                score = self.calculate_match_score(user, job)
                if score >= 40:  # Minimum threshold
                    scored_jobs.append({
                        **job,
                        'match_score': score
                    })
            
            # Sort by score
            scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
            top_jobs = scored_jobs[:limit]
            
            if not top_jobs:
                return []
            
            # Use AI to generate personalized recommendations
            user_profile = f"""
            नाम: {user.get('name', 'उपयोगकर्ता')}
            शिक्षा: {user.get('education_level', 'अज्ञात')}
            राज्य: {user.get('state', 'भारत')}
            आयु: {user.get('age', 'अज्ञात')}
            पसंदीदा श्रेणियां: {', '.join(user.get('preferred_categories', [])) or 'सभी'}
            """
            
            jobs_summary = "\n".join([
                f"- {job['title']} ({job['organization']}) - Score: {job['match_score']}%"
                for job in top_jobs[:5]
            ])
            
            prompt = f"""आप एक नौकरी सलाहकार हैं। इस उपयोगकर्ता प्रोफ़ाइल के आधार पर, नीचे दी गई नौकरियों में से सबसे उपयुक्त नौकरियों की सिफारिश करें।

उपयोगकर्ता प्रोफ़ाइल:
{user_profile}

उपलब्ध नौकरियां:
{jobs_summary}

कृपया JSON format में जवाब दें:
{{"recommendations": [{{"job_title": "...", "reason_hi": "इस नौकरी के लिए आप उपयुक्त हैं क्योंकि..."}}]}}
"""
            
            response = openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=500,
                temperature=0.7
            )
            
            ai_response = response.choices[0].message.content
            
            # Parse AI response and merge with scored jobs
            try:
                ai_data = json.loads(ai_response)
                recommendations = ai_data.get('recommendations', [])
                
                # Merge AI reasons with scored jobs
                for job in top_jobs:
                    for rec in recommendations:
                        if rec.get('job_title', '').lower() in job['title'].lower():
                            job['ai_reason'] = rec.get('reason_hi', '')
                            break
            except json.JSONDecodeError:
                pass  # Use jobs without AI reasons
            
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

ai_job_matcher = AIJobMatcher()

# ===================== AUTH ENDPOINTS =====================

@api_router.post("/auth/register", response_model=TokenResponse)
async def register(user_data: UserCreate):
    existing = await db.users.find_one({"phone": user_data.phone})
    if existing:
        raise HTTPException(status_code=400, detail="Phone number already registered")
    
    user_id = str(uuid.uuid4())
    user_doc = {
        "id": user_id,
        "name": user_data.name,
        "email": user_data.email,
        "phone": user_data.phone,
        "password": get_password_hash(user_data.password),
        "language": user_data.language,
        "is_admin": False,
        "is_operator": False,
        "documents": [],
        "whatsapp_connected": False,
        "education_level": user_data.education_level,
        "state": user_data.state,
        "age": user_data.age,
        "preferred_categories": user_data.preferred_categories,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.users.insert_one(user_doc)
    
    token = create_access_token({"sub": user_id})
    user_doc.pop("password")
    user_doc.pop("_id", None)
    user_doc["created_at"] = datetime.fromisoformat(user_doc["created_at"])
    
    return TokenResponse(access_token=token, user=UserProfile(**user_doc))

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    user = await db.users.find_one({"phone": credentials.phone})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token({"sub": user["id"]})
    user.pop("password")
    user.pop("_id", None)
    if isinstance(user["created_at"], str):
        user["created_at"] = datetime.fromisoformat(user["created_at"])
    
    return TokenResponse(access_token=token, user=UserProfile(**user))

@api_router.get("/auth/me", response_model=UserProfile)
async def get_me(user: dict = Depends(get_current_user)):
    if isinstance(user["created_at"], str):
        user["created_at"] = datetime.fromisoformat(user["created_at"])
    return UserProfile(**user)

# ===================== JOB ALERTS ENDPOINTS =====================

@api_router.post("/jobs", status_code=201)
async def create_job(job: JobAlertCreate, admin: dict = Depends(get_admin_user)):
    job_id = str(uuid.uuid4())
    job_doc = {
        "id": job_id,
        **job.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin["id"],
        "views": 0,
        "applications": 0
    }
    await db.jobs.insert_one(job_doc)
    job_doc.pop("_id", None)
    return job_doc

@api_router.get("/jobs")
async def get_jobs(
    category: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    query = {"is_active": True}
    if category:
        query["category"] = category
    if state and state != "all":
        query["state"] = {"$in": [state, "all"]}
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"title_hi": {"$regex": search, "$options": "i"}},
            {"organization": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.jobs.count_documents(query)
    jobs = await db.jobs.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "jobs": jobs}

@api_router.get("/jobs/{job_id}")
async def get_job(job_id: str):
    job = await db.jobs.find_one({"id": job_id}, {"_id": 0})
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    await db.jobs.update_one({"id": job_id}, {"$inc": {"views": 1}})
    return job

@api_router.put("/jobs/{job_id}")
async def update_job(job_id: str, job: JobAlertCreate, admin: dict = Depends(get_admin_user)):
    result = await db.jobs.update_one({"id": job_id}, {"$set": job.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job updated"}

@api_router.delete("/jobs/{job_id}")
async def delete_job(job_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.jobs.delete_one({"id": job_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"message": "Job deleted"}

# ===================== YOJANA ENDPOINTS =====================

@api_router.post("/yojana", status_code=201)
async def create_yojana(yojana: YojanaCreate, admin: dict = Depends(get_admin_user)):
    yojana_id = str(uuid.uuid4())
    yojana_doc = {
        "id": yojana_id,
        **yojana.model_dump(),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "created_by": admin["id"],
        "views": 0,
        "applications": 0
    }
    await db.yojana.insert_one(yojana_doc)
    yojana_doc.pop("_id", None)
    return yojana_doc

@api_router.get("/yojana")
async def get_yojana_list(
    category: Optional[str] = None,
    state: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    query = {"is_active": True}
    if category:
        query["category"] = category
    if state and state != "all":
        query["state"] = {"$in": [state, "all"]}
    if search:
        query["$or"] = [
            {"name": {"$regex": search, "$options": "i"}},
            {"name_hi": {"$regex": search, "$options": "i"}},
            {"ministry": {"$regex": search, "$options": "i"}}
        ]
    
    total = await db.yojana.count_documents(query)
    yojanas = await db.yojana.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "yojanas": yojanas}

@api_router.get("/yojana/{yojana_id}")
async def get_yojana(yojana_id: str):
    yojana = await db.yojana.find_one({"id": yojana_id}, {"_id": 0})
    if not yojana:
        raise HTTPException(status_code=404, detail="Yojana not found")
    await db.yojana.update_one({"id": yojana_id}, {"$inc": {"views": 1}})
    return yojana

@api_router.put("/yojana/{yojana_id}")
async def update_yojana(yojana_id: str, yojana: YojanaCreate, admin: dict = Depends(get_admin_user)):
    result = await db.yojana.update_one({"id": yojana_id}, {"$set": yojana.model_dump()})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Yojana not found")
    return {"message": "Yojana updated"}

@api_router.delete("/yojana/{yojana_id}")
async def delete_yojana(yojana_id: str, admin: dict = Depends(get_admin_user)):
    result = await db.yojana.delete_one({"id": yojana_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Yojana not found")
    return {"message": "Yojana deleted"}

# ===================== APPLICATION ENDPOINTS =====================

@api_router.post("/applications", status_code=201)
async def create_application(app_data: ApplicationCreate, user: dict = Depends(get_current_user)):
    app_id = str(uuid.uuid4())
    
    # Get item details
    if app_data.item_type == "job":
        item = await db.jobs.find_one({"id": app_data.item_id}, {"_id": 0})
        service_fee = 20
        govt_fee = 0
    else:
        item = await db.yojana.find_one({"id": app_data.item_id}, {"_id": 0})
        service_fee = item.get("service_fee", 20) if item else 20
        govt_fee = item.get("govt_fee", 0) if item else 0
    
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    total_fee = service_fee + govt_fee
    
    application_doc = {
        "id": app_id,
        "user_id": user["id"],
        "item_type": app_data.item_type,
        "item_id": app_data.item_id,
        "item_title": item.get("title") or item.get("name"),
        "user_details": app_data.user_details,
        "documents": app_data.documents,
        "service_fee": service_fee,
        "govt_fee": govt_fee,
        "total_fee": total_fee,
        "payment_status": "pending",
        "application_status": "pending",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.applications.insert_one(application_doc)
    
    # Update item application count
    collection = db.jobs if app_data.item_type == "job" else db.yojana
    await collection.update_one({"id": app_data.item_id}, {"$inc": {"applications": 1}})
    
    application_doc.pop("_id", None)
    return application_doc

@api_router.get("/applications")
async def get_user_applications(user: dict = Depends(get_current_user)):
    apps = await db.applications.find({"user_id": user["id"]}, {"_id": 0}).sort("created_at", -1).to_list(100)
    return {"applications": apps}

@api_router.get("/applications/{app_id}")
async def get_application(app_id: str, user: dict = Depends(get_current_user)):
    app = await db.applications.find_one({"id": app_id, "user_id": user["id"]}, {"_id": 0})
    if not app:
        raise HTTPException(status_code=404, detail="Application not found")
    return app

# ===================== PAYMENT ENDPOINTS (Cashfree) =====================

@api_router.post("/payments/create-order")
async def create_payment_order(payment: PaymentCreate, user: dict = Depends(get_current_user)):
    application = await db.applications.find_one({"id": payment.application_id, "user_id": user["id"]})
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    
    order_id = f"order_{uuid.uuid4().hex[:12]}"
    
    # Cashfree API call
    cashfree_url = "https://api.cashfree.com/pg/orders" if CASHFREE_ENV == "PRODUCTION" else "https://sandbox.cashfree.com/pg/orders"
    
    headers = {
        "x-api-version": "2023-08-01",
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY,
        "Content-Type": "application/json"
    }
    
    payload = {
        "order_id": order_id,
        "order_amount": payment.amount,
        "order_currency": "INR",
        "customer_details": {
            "customer_id": user["id"][:20],
            "customer_name": user["name"],
            "customer_phone": user["phone"],
            "customer_email": user.get("email") or f"{user['phone']}@digitalsahayak.com"
        },
        "order_meta": {
            "return_url": payment.return_url + f"?order_id={order_id}",
            "notify_url": f"{os.environ.get('BACKEND_URL', '')}/api/payments/webhook"
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(cashfree_url, json=payload, headers=headers)
            cf_response = response.json()
            
            if response.status_code in [200, 201]:
                # Store payment record
                payment_doc = {
                    "id": str(uuid.uuid4()),
                    "order_id": order_id,
                    "cf_order_id": cf_response.get("cf_order_id"),
                    "application_id": payment.application_id,
                    "user_id": user["id"],
                    "amount": payment.amount,
                    "status": "PENDING",
                    "payment_session_id": cf_response.get("payment_session_id"),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                await db.payments.insert_one(payment_doc)
                
                return {
                    "order_id": order_id,
                    "payment_session_id": cf_response.get("payment_session_id"),
                    "order_status": cf_response.get("order_status")
                }
            else:
                logger.error(f"Cashfree error: {cf_response}")
                raise HTTPException(status_code=400, detail=cf_response.get("message", "Payment creation failed"))
    except httpx.HTTPError as e:
        logger.error(f"Payment API error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")

@api_router.get("/payments/verify/{order_id}")
async def verify_payment(order_id: str, user: dict = Depends(get_current_user)):
    payment = await db.payments.find_one({"order_id": order_id, "user_id": user["id"]}, {"_id": 0})
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    
    # Verify with Cashfree
    cashfree_url = f"https://api.cashfree.com/pg/orders/{order_id}" if CASHFREE_ENV == "PRODUCTION" else f"https://sandbox.cashfree.com/pg/orders/{order_id}"
    
    headers = {
        "x-api-version": "2023-08-01",
        "x-client-id": CASHFREE_APP_ID,
        "x-client-secret": CASHFREE_SECRET_KEY
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(cashfree_url, headers=headers)
            cf_response = response.json()
            
            if response.status_code == 200:
                order_status = cf_response.get("order_status")
                
                # Update payment status
                await db.payments.update_one(
                    {"order_id": order_id},
                    {"$set": {"status": order_status, "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                
                # If paid, update application
                if order_status == "PAID":
                    await db.applications.update_one(
                        {"id": payment["application_id"]},
                        {"$set": {"payment_status": "paid", "application_status": "processing"}}
                    )
                
                return {"order_id": order_id, "status": order_status, "amount": cf_response.get("order_amount")}
            else:
                raise HTTPException(status_code=400, detail="Failed to verify payment")
    except httpx.HTTPError as e:
        logger.error(f"Payment verify error: {str(e)}")
        raise HTTPException(status_code=500, detail="Payment service unavailable")

@api_router.post("/payments/webhook")
async def payment_webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("x-webhook-signature")
    
    # Verify webhook signature (simplified)
    logger.info(f"Payment webhook received")
    
    try:
        payload = json.loads(body)
        event_type = payload.get("type")
        data = payload.get("data", {})
        
        if event_type == "PAYMENT_SUCCESS":
            order_id = data.get("order", {}).get("order_id")
            if order_id:
                await db.payments.update_one(
                    {"order_id": order_id},
                    {"$set": {"status": "PAID", "updated_at": datetime.now(timezone.utc).isoformat()}}
                )
                payment = await db.payments.find_one({"order_id": order_id})
                if payment:
                    await db.applications.update_one(
                        {"id": payment["application_id"]},
                        {"$set": {"payment_status": "paid", "application_status": "processing"}}
                    )
        
        return {"status": "ok"}
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return {"status": "error"}

# ===================== WHATSAPP ENDPOINTS (MOCK) =====================

@api_router.get("/whatsapp/webhook")
async def whatsapp_verify(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
    hub_verify_token: str = Query(None, alias="hub.verify_token")
):
    if hub_verify_token == WHATSAPP_VERIFY_TOKEN and hub_mode == "subscribe":
        return int(hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@api_router.post("/whatsapp/webhook")
async def whatsapp_webhook(request: Request):
    body = await request.json()
    logger.info(f"WhatsApp webhook: {json.dumps(body, indent=2)}")
    
    # Process incoming messages (MOCK)
    try:
        if body.get("entry"):
            for entry in body["entry"]:
                changes = entry.get("changes", [])
                for change in changes:
                    value = change.get("value", {})
                    messages = value.get("messages", [])
                    for msg in messages:
                        sender = msg.get("from")
                        text = msg.get("text", {}).get("body", "")
                        logger.info(f"WhatsApp message from {sender}: {text}")
                        
                        # Store message
                        await db.whatsapp_messages.insert_one({
                            "id": str(uuid.uuid4()),
                            "from": sender,
                            "text": text,
                            "direction": "inbound",
                            "created_at": datetime.now(timezone.utc).isoformat()
                        })
    except Exception as e:
        logger.error(f"WhatsApp webhook error: {str(e)}")
    
    return {"status": "ok"}

@api_router.post("/whatsapp/send")
async def send_whatsapp(msg: WhatsAppMessage, admin: dict = Depends(get_admin_user)):
    # MOCK implementation - logs the message
    logger.info(f"[MOCK] WhatsApp send to {msg.phone}: {msg.message}")
    
    message_doc = {
        "id": str(uuid.uuid4()),
        "to": msg.phone,
        "text": msg.message,
        "template": msg.template,
        "direction": "outbound",
        "status": "sent",
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    await db.whatsapp_messages.insert_one(message_doc)
    message_doc.pop("_id", None)
    
    return {"status": "sent", "message_id": message_doc["id"]}

@api_router.post("/whatsapp/connect")
async def connect_whatsapp(phone: str = Body(..., embed=True), user: dict = Depends(get_current_user)):
    # Update user's WhatsApp connection status
    await db.users.update_one(
        {"id": user["id"]},
        {"$set": {"whatsapp_connected": True, "whatsapp_phone": phone}}
    )
    return {"status": "connected", "message": "WhatsApp connected successfully"}

# ===================== ADMIN ENDPOINTS =====================

@api_router.get("/admin/stats")
async def get_admin_stats(admin: dict = Depends(get_admin_user)):
    total_users = await db.users.count_documents({})
    total_jobs = await db.jobs.count_documents({})
    total_yojana = await db.yojana.count_documents({})
    total_applications = await db.applications.count_documents({})
    paid_applications = await db.applications.count_documents({"payment_status": "paid"})
    
    # Revenue calculation
    payments = await db.payments.find({"status": "PAID"}, {"_id": 0, "amount": 1}).to_list(1000)
    total_revenue = sum(p.get("amount", 0) for p in payments)
    
    return {
        "total_users": total_users,
        "total_jobs": total_jobs,
        "total_yojana": total_yojana,
        "total_applications": total_applications,
        "paid_applications": paid_applications,
        "total_revenue": total_revenue
    }

@api_router.get("/admin/applications")
async def get_all_applications(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    admin: dict = Depends(get_admin_user)
):
    query = {}
    if status:
        query["application_status"] = status
    
    total = await db.applications.count_documents(query)
    apps = await db.applications.find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(limit).to_list(limit)
    return {"total": total, "applications": apps}

@api_router.put("/admin/applications/{app_id}/status")
async def update_application_status(
    app_id: str,
    status: str = Body(..., embed=True),
    admin: dict = Depends(get_admin_user)
):
    result = await db.applications.update_one(
        {"id": app_id},
        {"$set": {"application_status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Application not found")
    return {"message": "Status updated"}

@api_router.post("/admin/make-admin")
async def make_admin(phone: str = Body(..., embed=True), admin: dict = Depends(get_admin_user)):
    result = await db.users.update_one({"phone": phone}, {"$set": {"is_admin": True}})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User is now admin"}

# ===================== SCRAPER ENDPOINTS =====================

@api_router.post("/admin/scrape-jobs")
async def trigger_job_scraping(background_tasks: BackgroundTasks, admin: dict = Depends(get_admin_user)):
    """Trigger job scraping from configured sources"""
    
    async def scrape_and_save():
        try:
            jobs = await job_scraper.scrape_all()
            saved_count = 0
            
            for job_data in jobs:
                # Check if job already exists (by title + apply_link)
                existing = await db.jobs.find_one({
                    "title": job_data["title"],
                    "apply_link": job_data["apply_link"]
                })
                
                if not existing:
                    job_id = str(uuid.uuid4())
                    job_doc = {
                        "id": job_id,
                        **job_data,
                        "is_active": True,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                        "created_by": "scraper",
                        "views": 0,
                        "applications": 0
                    }
                    await db.jobs.insert_one(job_doc)
                    saved_count += 1
            
            logger.info(f"Scraper saved {saved_count} new jobs")
            
            # Log scrape result
            await db.scrape_logs.insert_one({
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "total_scraped": len(jobs),
                "new_saved": saved_count,
                "status": "success"
            })
            
        except Exception as e:
            logger.error(f"Scraping error: {e}")
            await db.scrape_logs.insert_one({
                "id": str(uuid.uuid4()),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "error": str(e),
                "status": "failed"
            })
    
    background_tasks.add_task(scrape_and_save)
    return {"message": "Job scraping started in background", "status": "processing"}

@api_router.get("/admin/scrape-logs")
async def get_scrape_logs(admin: dict = Depends(get_admin_user), limit: int = 10):
    """Get recent scrape logs"""
    logs = await db.scrape_logs.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit).to_list(limit)
    return {"logs": logs}

# ===================== AI JOB RECOMMENDATIONS =====================

@api_router.get("/recommendations")
async def get_job_recommendations(user: dict = Depends(get_current_user), limit: int = 10):
    """Get AI-powered job recommendations based on user profile"""
    
    # Fetch all active jobs
    jobs = await db.jobs.find({"is_active": True}, {"_id": 0}).to_list(100)
    
    if not jobs:
        return {"recommendations": [], "message": "No jobs available"}
    
    # Get AI recommendations
    recommendations = await ai_job_matcher.get_ai_recommendations(user, jobs, limit)
    
    return {
        "recommendations": recommendations,
        "total": len(recommendations),
        "user_profile": {
            "education_level": user.get("education_level"),
            "state": user.get("state"),
            "age": user.get("age"),
            "preferred_categories": user.get("preferred_categories", [])
        }
    }

@api_router.put("/profile/preferences")
async def update_user_preferences(
    preferences: UserProfileUpdate,
    user: dict = Depends(get_current_user)
):
    """Update user profile preferences for better job matching"""
    update_data = {}
    
    if preferences.name:
        update_data["name"] = preferences.name
    if preferences.email:
        update_data["email"] = preferences.email
    if preferences.education_level:
        update_data["education_level"] = preferences.education_level
    if preferences.state:
        update_data["state"] = preferences.state
    if preferences.age is not None:
        update_data["age"] = preferences.age
    if preferences.preferred_categories is not None:
        update_data["preferred_categories"] = preferences.preferred_categories
    
    if update_data:
        await db.users.update_one(
            {"id": user["id"]},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one({"id": user["id"]}, {"_id": 0, "password": 0})
    return {"message": "Profile updated", "user": updated_user}

@api_router.get("/jobs/matching")
async def get_matching_jobs(
    user: dict = Depends(get_current_user),
    category: Optional[str] = None,
    state: Optional[str] = None,
    skip: int = 0,
    limit: int = 20
):
    """Get jobs matching user's profile with scores"""
    
    # Build query
    query = {"is_active": True}
    if category:
        query["category"] = category
    if state and state != "all":
        query["state"] = {"$in": [state, "all"]}
    
    # Fetch jobs
    jobs = await db.jobs.find(query, {"_id": 0}).to_list(100)
    
    # Calculate match scores
    scored_jobs = []
    for job in jobs:
        score = ai_job_matcher.calculate_match_score(user, job)
        job["match_score"] = score
        job["match_reason"] = ai_job_matcher._generate_reason(user, job, score)
        scored_jobs.append(job)
    
    # Sort by match score
    scored_jobs.sort(key=lambda x: x["match_score"], reverse=True)
    
    # Paginate
    total = len(scored_jobs)
    paginated = scored_jobs[skip:skip + limit]
    
    return {
        "total": total,
        "jobs": paginated,
        "user_profile_complete": bool(user.get("education_level") and user.get("state") and user.get("age"))
    }

# ===================== DOCUMENT ENDPOINTS =====================

@api_router.post("/documents/upload")
async def upload_document(
    doc_type: str = Body(...),
    doc_name: str = Body(...),
    doc_url: str = Body(...),
    user: dict = Depends(get_current_user)
):
    doc = {
        "id": str(uuid.uuid4()),
        "type": doc_type,
        "name": doc_name,
        "url": doc_url,
        "uploaded_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.update_one(
        {"id": user["id"]},
        {"$push": {"documents": doc}}
    )
    return doc

@api_router.get("/documents")
async def get_documents(user: dict = Depends(get_current_user)):
    return {"documents": user.get("documents", [])}

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str, user: dict = Depends(get_current_user)):
    await db.users.update_one(
        {"id": user["id"]},
        {"$pull": {"documents": {"id": doc_id}}}
    )
    return {"message": "Document deleted"}

# ===================== PUBLIC ENDPOINTS =====================

@api_router.get("/")
async def root():
    return {"message": "Digital Sahayak API v1.0", "status": "online"}

@api_router.get("/categories")
async def get_categories():
    return {
        "job_categories": [
            {"id": "government", "name": "Government Jobs", "name_hi": "सरकारी नौकरी"},
            {"id": "railway", "name": "Railway Jobs", "name_hi": "रेलवे नौकरी"},
            {"id": "bank", "name": "Bank Jobs", "name_hi": "बैंक नौकरी"},
            {"id": "ssc", "name": "SSC Jobs", "name_hi": "SSC नौकरी"},
            {"id": "upsc", "name": "UPSC Jobs", "name_hi": "UPSC नौकरी"},
            {"id": "state", "name": "State Jobs", "name_hi": "राज्य नौकरी"},
            {"id": "defence", "name": "Defence Jobs", "name_hi": "रक्षा नौकरी"},
            {"id": "police", "name": "Police Jobs", "name_hi": "पुलिस नौकरी"}
        ],
        "yojana_categories": [
            {"id": "welfare", "name": "Welfare Schemes", "name_hi": "कल्याण योजना"},
            {"id": "education", "name": "Education", "name_hi": "शिक्षा योजना"},
            {"id": "agriculture", "name": "Agriculture", "name_hi": "कृषि योजना"},
            {"id": "housing", "name": "Housing", "name_hi": "आवास योजना"},
            {"id": "health", "name": "Health", "name_hi": "स्वास्थ्य योजना"},
            {"id": "women", "name": "Women & Child", "name_hi": "महिला एवं बाल"},
            {"id": "pension", "name": "Pension", "name_hi": "पेंशन योजना"},
            {"id": "employment", "name": "Employment", "name_hi": "रोजगार योजना"}
        ],
        "states": [
            {"id": "all", "name": "All India", "name_hi": "संपूर्ण भारत"},
            {"id": "bihar", "name": "Bihar", "name_hi": "बिहार"},
            {"id": "jharkhand", "name": "Jharkhand", "name_hi": "झारखंड"},
            {"id": "up", "name": "Uttar Pradesh", "name_hi": "उत्तर प्रदेश"},
            {"id": "mp", "name": "Madhya Pradesh", "name_hi": "मध्य प्रदेश"},
            {"id": "rajasthan", "name": "Rajasthan", "name_hi": "राजस्थान"},
            {"id": "maharashtra", "name": "Maharashtra", "name_hi": "महाराष्ट्र"},
            {"id": "wb", "name": "West Bengal", "name_hi": "पश्चिम बंगाल"}
        ]
    }

# Include router
app.include_router(api_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup():
    # Create indexes
    await db.users.create_index("phone", unique=True)
    await db.users.create_index("id", unique=True)
    await db.jobs.create_index("id", unique=True)
    await db.jobs.create_index([("created_at", -1)])
    await db.yojana.create_index("id", unique=True)
    await db.yojana.create_index([("created_at", -1)])
    await db.applications.create_index("id", unique=True)
    await db.applications.create_index("user_id")
    await db.payments.create_index("order_id", unique=True)
    
    # Create default admin if not exists
    admin = await db.users.find_one({"phone": "6200184827"})
    if not admin:
        admin_doc = {
            "id": str(uuid.uuid4()),
            "name": "Admin",
            "email": "admin@digitalsahayak.com",
            "phone": "6200184827",
            "password": get_password_hash("admin123"),
            "language": "hi",
            "is_admin": True,
            "is_operator": True,
            "documents": [],
            "whatsapp_connected": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(admin_doc)
        logger.info("Default admin created")
    else:
        # Ensure existing user is admin
        await db.users.update_one({"phone": "6200184827"}, {"$set": {"is_admin": True, "is_operator": True}})
    
    logger.info("Digital Sahayak API started")

@app.on_event("shutdown")
async def shutdown():
    client.close()
