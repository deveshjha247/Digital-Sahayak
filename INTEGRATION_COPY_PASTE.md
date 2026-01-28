# 🔗 Server Integration Code - Copy & Paste Ready

## Quick Integration

### Step 1: Add to `backend/server.py` (Top Section)

```python
# Add these imports at the top of server.py
from backend.routes.ai_routes_v2 import router as ai_router
```

### Step 2: Include Router (After app creation)

```python
# After: app = FastAPI()
# Add this line:
app.include_router(ai_router)

# If you have other routers, include them all:
# app.include_router(scraper_router)
# app.include_router(auth_router)
# etc.
```

### Step 3: That's it! Server is ready

```bash
python backend/server.py
```

---

## Complete Minimal Example

```python
# backend/server.py

from fastapi import FastAPI
from backend.routes.ai_routes_v2 import router as ai_router

# Create app
app = FastAPI(
    title="Digital Sahayak API",
    version="2.0.0"
)

# Include AI routes
app.include_router(ai_router)

# Root endpoint
@app.get("/")
async def root():
    return {"status": "ok", "ai": "/api/v2/ai/health"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

---

## Testing After Integration

### 1. Health Check
```bash
curl http://localhost:8000/api/v2/ai/health
```

### 2. Job Recommendations
```bash
curl -X POST http://localhost:8000/api/v2/ai/recommendations/jobs \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {
      "education": "B.Tech",
      "age": 25,
      "state": "Bihar",
      "category": "Railway",
      "preferred_salary": 50000
    },
    "jobs": [
      {"id": 1, "title": "Senior Engineer", "salary": 60000, "location": "Delhi"},
      {"id": 2, "title": "Manager", "salary": 75000, "location": "Bihar"}
    ],
    "top_k": 5
  }'
```

### 3. Field Classification
```bash
curl -X POST http://localhost:8000/api/v2/ai/classify/field \
  -H "Content-Type: application/json" \
  -d '{
    "field_label": "आधार संख्या",
    "field_value": "123456789012"
  }'
```

### 4. Intent Classification
```bash
curl -X POST http://localhost:8000/api/v2/ai/intent/classify \
  -H "Content-Type: application/json" \
  -d '{"message": "मुझे नौकरी खोजनी है"}'
```

### 5. Document Validation
```bash
curl -X POST http://localhost:8000/api/v2/ai/validate/form \
  -H "Content-Type: application/json" \
  -d '{
    "fields": {
      "aadhar": "123456789012",
      "pan": "ABCDE1234F",
      "email": "user@example.com"
    }
  }'
```

---

## Python Usage Examples

### Example 1: Using AI in Route Handlers

```python
from fastapi import APIRouter, HTTPException
from backend.ai import JobRecommender

router = APIRouter()
recommender = JobRecommender()

@router.get("/api/jobs/{user_id}")
async def get_personalized_jobs(user_id: str):
    try:
        # Fetch user from database
        user = await db.get_user(user_id)
        
        # Fetch available jobs
        jobs = await db.get_jobs()
        
        # Get AI recommendations
        recommendations = recommender.get_recommendations(
            user_profile=user,
            jobs=jobs,
            top_k=10
        )
        
        return {"success": True, "recommendations": recommendations}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Example 2: Using AI in Services

```python
from backend.ai import IntentClassifier, FieldClassifier

class FormService:
    def __init__(self):
        self.classifier = FieldClassifier()
    
    async def submit_job_application(self, form_data: dict, user_id: str):
        # Get user profile
        user = await db.get_user(user_id)
        
        # Extract form field labels
        form_fields = list(form_data.keys())
        
        # Auto-fill with user data
        auto_filled = self.classifier.map_user_to_fields(
            user_profile=user,
            form_fields=form_fields
        )
        
        # Merge with submitted data
        final_data = {**auto_filled, **form_data}
        
        # Save to database
        await db.save_application(final_data)
        
        return {"status": "success"}
```

### Example 3: WhatsApp Bot Integration

```python
from fastapi import APIRouter
from backend.ai import IntentClassifier

router = APIRouter()
classifier = IntentClassifier()

@router.post("/api/whatsapp/message")
async def handle_whatsapp_message(message: str, user_id: str):
    # Classify message intent
    intent, confidence, details = classifier.classify(message)
    
    # Get suggested response
    response = classifier.get_suggested_response(intent)
    
    # Route to appropriate handler
    if intent.value == "job_search":
        # Handle job search
        return {"reply": response, "action": "show_jobs"}
    
    elif intent.value == "job_apply":
        # Handle application
        return {"reply": response, "action": "show_form"}
    
    elif intent.value == "help":
        # Show help
        return {"reply": response, "action": "show_help"}
    
    else:
        # Default response
        return {"reply": response, "action": "continue_chat"}
```

### Example 4: Document Upload Handler

```python
from fastapi import UploadFile, File
from backend.ai import DocumentValidator

@router.post("/api/documents/upload")
async def upload_document(
    file: UploadFile = File(...),
    document_type: str = None,
    user_id: str = None
):
    validator = DocumentValidator()
    
    # Read file content (pseudo-code, actual implementation depends on file type)
    content = await file.read()
    
    # Extract text from image (use OCR service or dummy for now)
    ocr_text = await extract_text_from_image(content)
    
    # Extract fields
    fields = validator.extract_fields_from_text(ocr_text)
    
    # Validate document
    validation_result = validator.validate_document({
        "ocr_text": ocr_text,
        "fields": fields,
        "document_type": document_type
    })
    
    if validation_result["overall_status"] == "valid":
        # Save document
        await db.save_document(user_id, file.filename, fields)
        return {"status": "verified", "document_id": "..."}
    else:
        return {
            "status": "invalid",
            "issues": validation_result["issues"],
            "quality_score": validation_result["quality_score"]
        }
```

### Example 5: Job Posting Processing

```python
from backend.ai import ContentSummarizer

class JobPostingService:
    def __init__(self):
        self.summarizer = ContentSummarizer()
    
    async def create_job_posting(self, job_data: dict):
        # Process description
        result = self.summarizer.process_job_description(job_data)
        
        # Create enhanced job posting
        enhanced_job = {
            "title": result["title"],
            "original_description": result["original_description"],
            "summary_english": result["summary_english"],
            "summary_hindi": result["summary_hindi"],
            "key_requirements": result["key_info"],
            "highlights": result["bullet_points"][:3],
            "created_at": datetime.now()
        }
        
        # Save to database
        job_id = await db.save_job(enhanced_job)
        
        return job_id
```

---

## Environment Configuration

### `.env` File (Optional)

```env
# Debug mode
DEBUG=false

# Logging
LOG_LEVEL=info
LOG_FILE=logs/api.log

# AI Configuration
AI_BATCH_SIZE=100
AI_CACHE_ENABLED=false
```

### Load in server:

```python
from dotenv import load_dotenv
import os

load_dotenv()

DEBUG = os.getenv("DEBUG", "false") == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
```

---

## Error Handling Template

```python
from fastapi import APIRouter, HTTPException
from backend.ai import JobRecommender
import logging

logger = logging.getLogger(__name__)
router = APIRouter()
recommender = JobRecommender()

@router.post("/api/v2/ai/recommendations/jobs")
async def get_recommendations(request: dict):
    try:
        # Validate request
        if not request.get("user_profile"):
            raise ValueError("user_profile is required")
        
        if not request.get("jobs"):
            raise ValueError("jobs list is required")
        
        # Call AI module
        recommendations = recommender.get_recommendations(
            user_profile=request["user_profile"],
            jobs=request["jobs"],
            top_k=request.get("top_k", 10)
        )
        
        # Return success
        return {
            "success": True,
            "data": recommendations
        }
    
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Logging Setup

```python
import logging
from logging.handlers import RotatingFileHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# File handler for production
file_handler = RotatingFileHandler(
    'logs/api.log',
    maxBytes=10485760,  # 10MB
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
))

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)
```

---

## Docker Deployment

### Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "backend/server.py"]
```

### docker-compose.yml

```yaml
version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=false
      - LOG_LEVEL=info
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped
```

### Build and Run

```bash
# Build
docker build -t digital-sahayak .

# Run
docker run -p 8000:8000 digital-sahayak

# Or with docker-compose
docker-compose up -d
```

---

## Testing Template

```python
import pytest
from fastapi.testclient import TestClient
from backend.server import app

client = TestClient(app)

class TestAIEndpoints:
    
    def test_health_check(self):
        response = client.get("/api/v2/ai/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_job_recommendations(self):
        payload = {
            "user_profile": {"education": "B.Tech", "age": 25},
            "jobs": [
                {"id": 1, "title": "Engineer", "salary": 60000},
                {"id": 2, "title": "Manager", "salary": 75000}
            ],
            "top_k": 5
        }
        
        response = client.post(
            "/api/v2/ai/recommendations/jobs",
            json=payload
        )
        
        assert response.status_code == 200
        assert response.json()["success"] == True
        assert len(response.json()["recommendations"]) > 0
    
    def test_intent_classification(self):
        response = client.post(
            "/api/v2/ai/intent/classify",
            json={"message": "नौकरी चाहिए"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] is not None
        assert 0 <= data["confidence"] <= 1
```

---

## Performance Monitoring

```python
from prometheus_client import Counter, Histogram, generate_latest
from fastapi.responses import Response
from time import time

# Metrics
REQUEST_COUNT = Counter(
    'requests_total',
    'Total requests',
    ['method', 'endpoint']
)

REQUEST_DURATION = Histogram(
    'request_duration_seconds',
    'Request duration',
    ['method', 'endpoint']
)

# Middleware to track metrics
@app.middleware("http")
async def track_metrics(request, call_next):
    start = time()
    response = await call_next(request)
    duration = time() - start
    
    REQUEST_COUNT.labels(
        method=request.method,
        endpoint=request.url.path
    ).inc()
    
    REQUEST_DURATION.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

# Metrics endpoint
@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type="text/plain"
    )
```

---

## That's it! 🎉

You now have everything ready to integrate the AI system into your server.

**Next steps**:
1. Copy the integration code
2. Add to your `server.py`
3. Restart server
4. Test endpoints
5. Done! 🚀
