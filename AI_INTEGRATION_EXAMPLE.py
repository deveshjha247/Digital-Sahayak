"""
AI Module Integration Example
Shows how to integrate all AI modules into your FastAPI server
"""

# ============================================================================
# STEP 1: Update your FastAPI server (server.py or main.py)
# ============================================================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

# Import all existing routes
from backend.routes.scraper_routes_v2 import router as scraper_router
from backend.routes.ai_routes_v2 import router as ai_router
# from backend.routes.other_routes import router as other_router

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Digital Sahayak API",
    description="Comprehensive job and scheme portal with AI capabilities",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# STEP 2: Include all routers
# ============================================================================

# Scraper routes
app.include_router(scraper_router)

# AI routes (NEW)
app.include_router(ai_router)

# Other routes
# app.include_router(other_router)

logger.info("All routers initialized")

# ============================================================================
# STEP 3: Root endpoint
# ============================================================================

@app.get("/")
async def root():
    """Root endpoint - API overview"""
    return {
        "app": "Digital Sahayak API",
        "version": "2.0.0",
        "endpoints": {
            "scraper": "/api/v2/scraper/health",
            "ai": "/api/v2/ai/health",
            "docs": "/docs",
            "redoc": "/redoc"
        }
    }

# ============================================================================
# STEP 4: Startup event (optional)
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Called when server starts"""
    logger.info("Starting Digital Sahayak API...")
    
    # Initialize AI modules if needed
    try:
        from backend.ai import (
            JobRecommender,
            FieldClassifier,
            ContentSummarizer,
            IntentClassifier,
            DocumentValidator
        )
        
        # Instantiate modules (warmup)
        logger.info("Initializing AI modules...")
        recommender = JobRecommender()
        classifier = FieldClassifier()
        summarizer = ContentSummarizer()
        intent_classifier = IntentClassifier()
        validator = DocumentValidator()
        
        logger.info("All AI modules initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing AI modules: {e}")
        raise

# ============================================================================
# STEP 5: Shutdown event (optional)
# ============================================================================

@app.on_event("shutdown")
async def shutdown_event():
    """Called when server shuts down"""
    logger.info("Shutting down Digital Sahayak API...")

# ============================================================================
# RUNNING THE SERVER
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    # Run with: python server.py
    # Or: uvicorn server:app --reload
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )


# ============================================================================
# EXAMPLE USAGE IN YOUR APPLICATION
# ============================================================================

"""
From anywhere in your application, you can now use the AI modules:

# Example 1: In a route handler
from fastapi import APIRouter
from backend.ai import JobRecommender

router = APIRouter()
recommender = JobRecommender()

@router.get("/jobs/{user_id}")
async def get_user_jobs(user_id: str):
    # Fetch user profile from database
    user = await get_user(user_id)
    
    # Fetch available jobs
    jobs = await get_available_jobs()
    
    # Get recommendations using AI
    recommendations = recommender.get_recommendations(
        user_profile=user,
        jobs=jobs,
        top_k=10
    )
    
    return recommendations


# Example 2: In a service/business logic
from backend.ai import IntentClassifier

class ChatService:
    def __init__(self):
        self.classifier = IntentClassifier()
    
    async def process_whatsapp_message(self, message: str, user_id: str):
        # Classify message intent
        intent, confidence, details = self.classifier.classify(message)
        
        # Route based on intent
        if intent.value == "job_search":
            return await self.handle_job_search(user_id, message)
        elif intent.value == "job_apply":
            return await self.handle_job_apply(user_id, message)
        else:
            # Get suggested response
            response = self.classifier.get_suggested_response(intent)
            return response


# Example 3: In a form handler
from backend.ai import FieldClassifier

async def submit_application(form_data: dict, user_profile: dict):
    classifier = FieldClassifier()
    
    # Auto-fill form fields
    form_fields = list(form_data.keys())
    auto_filled = classifier.map_user_to_fields(user_profile, form_fields)
    
    # Validate before saving
    validation_results = classifier.validate_form_fields(auto_filled)
    
    if validation_results["is_valid"]:
        # Save to database
        await save_application(form_data)
        return {"status": "success"}
    else:
        return {
            "status": "error",
            "errors": validation_results["errors"]
        }


# Example 4: In document upload handler
from backend.ai import DocumentValidator

async def verify_document(ocr_text: str, fields: dict):
    validator = DocumentValidator()
    
    # Validate document
    validation = validator.validate_document({
        "ocr_text": ocr_text,
        "fields": fields
    })
    
    if validation["overall_status"] == "valid":
        return {"verified": True}
    else:
        return {
            "verified": False,
            "issues": validation["issues"]
        }
"""

# ============================================================================
# API ENDPOINT EXAMPLES
# ============================================================================

"""
Once server is running, test endpoints:

# 1. Health checks
curl http://localhost:8000/
curl http://localhost:8000/api/v2/ai/health
curl http://localhost:8000/api/v2/scraper/health

# 2. Job recommendations
curl -X POST http://localhost:8000/api/v2/ai/recommendations/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {"education": "B.Tech", "age": 25, "state": "Bihar"},
    "jobs": [{"id": 1, "title": "Engineer", "salary": 60000}],
    "top_k": 5
  }'

# 3. Intent classification
curl -X POST http://localhost:8000/api/v2/ai/intent/classify \
  -H "Content-Type: application/json" \
  -d '{"message": "मुझे नौकरी खोजनी है"}'

# 4. Form validation
curl -X POST http://localhost:8000/api/v2/ai/validate/form \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "aadhar": "123456789012",
      "pan": "ABCDE1234F"
    }
  }'

# 5. API documentation
# Visit: http://localhost:8000/docs (Swagger UI)
# Visit: http://localhost:8000/redoc (ReDoc)
"""

# ============================================================================
# DOCKER DEPLOYMENT
# ============================================================================

"""
To run in Docker:

# Dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "backend/server.py"]

# Build and run
docker build -t digital-sahayak .
docker run -p 8000:8000 digital-sahayak

# Or with docker-compose
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=info
"""

# ============================================================================
# MONITORING AND LOGGING
# ============================================================================

"""
For production:

# 1. Setup logging
import logging
from logging.handlers import RotatingFileHandler

logger = logging.getLogger(__name__)
handler = RotatingFileHandler(
    'logs/api.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
logger.addHandler(handler)

# 2. Add monitoring
from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter('requests_total', 'Total requests')
REQUEST_DURATION = Histogram('request_duration_seconds', 'Request duration')

# 3. Add error tracking
import sentry_sdk
sentry_sdk.init("your-sentry-dsn")
"""

# ============================================================================
# TESTING
# ============================================================================

"""
Example test file (tests/test_ai_integration.py):

import pytest
from backend.ai import JobRecommender, FieldClassifier, IntentClassifier

@pytest.fixture
def recommender():
    return JobRecommender()

@pytest.fixture
def classifier():
    return FieldClassifier()

def test_job_recommendations(recommender):
    user = {"education": "B.Tech", "age": 25}
    jobs = [{"id": 1, "title": "Engineer", "salary": 60000}]
    
    recommendations = recommender.get_recommendations(user, jobs, top_k=1)
    
    assert len(recommendations) > 0
    assert recommendations[0]["score"] > 0

def test_field_classification(classifier):
    field_type, confidence = classifier.classify_field("आधार संख्या")
    
    assert field_type is not None
    assert confidence > 0.5

def test_intent_classification():
    classifier = IntentClassifier()
    intent, confidence, details = classifier.classify("मुझे नौकरी चाहिए")
    
    assert intent is not None
    assert confidence > 0
"""
