# Backend Refactoring Guide

## New Structure

The backend has been refactored into a modular architecture for better scalability and maintainability:

```
backend/
├── server_refactored.py       # New main server file
├── server.py                   # Old monolithic server (backup)
├── ai_learning_system.py       # Self-learning AI
│
├── config/                     # Configuration
│   ├── settings.py            # Environment variables & constants
│   └── database.py            # Database connection management
│
├── models/                     # Data models
│   └── schemas.py             # All Pydantic models
│
├── routes/                     # API endpoints
│   ├── auth_routes.py         # Authentication (login, register)
│   ├── job_routes.py          # Job CRUD operations
│   ├── yojana_routes.py       # Government scheme operations
│   ├── application_routes.py  # Application management
│   ├── payment_routes.py      # Payment integration
│   ├── ai_routes.py           # AI learning endpoints
│   ├── scraper_routes.py      # Web scraping
│   ├── whatsapp_routes.py     # WhatsApp webhooks
│   └── form_routes.py         # Form intelligence (ML)
│
├── services/                   # Business logic
│   ├── hybrid_matching.py     # Hybrid Rule+ML matching engine
│   └── form_intelligence.py   # ML field classification & error prediction
│
├── middleware/                 # Middleware
│   └── auth.py                # JWT authentication
│
└── utils/                      # Utilities
    └── helpers.py             # Helper functions
```

## Key Improvements

### 1. **Separation of Concerns**
- **Config**: All settings in one place
- **Models**: Clean data validation
- **Routes**: Thin controllers, easy to test
- **Services**: Reusable business logic
- **Middleware**: Cross-cutting concerns

### 2. **Hybrid Matching System**
Located in `services/hybrid_matching.py`:
- **Rule-based matching**: Deterministic field mappings (education, age, state)
- **Heuristic scoring**: Pattern-based matching with learned weights
- **ML enhancement**: OpenAI API for semantic similarity
- **Log-based learning**: Learns from user behavior (applied, ignored, saved)

See [FORM_INTELLIGENCE_GUIDE.md](FORM_INTELLIGENCE_GUIDE.md) for detailed Form Intelligence documentation.
Form Intelligence System**
Located in `services/form_intelligence.py`:
- **Field Classification**: ML-based field type detection (name, email, phone, Aadhar, PAN, etc.)
- **Error Prediction**: Predicts form errors before submission using validation + ML
- **Auto-fill**: Smart form filling based on user profile
- **Portal Training**: Learns from portal-specific datasets to improve accuracy
- **Batch Validation**: Validate multiple forms simultaneously

### 4. **
### 3. **Modular Routes**
Each route file is focused and independent:
- Easy to add new endpoints
- Simple to test individual features
- Clear separation of authentication, resources, payments, etc.

### 4. **Database Abstraction**
`config/database.py` provides:
- Singleton pattern for connection management
- Clean startup/shutdown
- Easy to switch database implementations

### 5. **Authentication Middleware**
`middleware/auth.py` includes:
- JWT token creation/verification
- Password hashing with bcrypt
- Dependency injection for protected routes
- Admin role checking

## Migration Guide

### To use the refactored server:

1. **Update requirements.txt** (already done):
```bash
cd backend
pip install -r requirements.txt
```

2. **Run refactored server**:
```bash
python server_refactored.py
```

Or with uvicorn:
```bash
uvicorn server_refactored:app --reload
```

3. **Test endpoints**:
All endpoints remain the same (`/api/auth/login`, `/api/jobs`, etc.)

4. **Switch permanently** (optional):
```bash
# Backup old server
mv server.py server_old.py

# Use refactored as main
mv server_refactored.py server.py
```

## Adding New Features

### Add a new route:
1. Create file in `routes/` (e.g., `notification_routes.py`)
2. Define router:
```python
from fastapi import APIRouter
router = APIRouter(prefix="/notifications", tags=["Notifications"])

@router.get("")
async def get_notifications():
    return {"notifications": []}
```
3. Import in `routes/__init__.py`
4. Mount in `server_refactored.py`:
```python
from routes import notification_routes
app.include_router(notification_routes.router, prefix="/api")
```

### Add a new service:
1. Create file in `services/` (e.g., `email_service.py`)
2. Implement business logic
3. Import in routes where needed

### Add new models:
1. Add Pydantic models to `models/schemas.py`
2. Use in route handlers

## Benefits

✅ **Scalability**: Easy to add features without touching other code  
✅ **Maintainability**: Clear file organization, each <200 lines  
✅ **Testability**: Isolated components, easy to mock  
✅ **Readability**: Logical structure, self-documenting  
✅ **Collaboration**: Multiple devs can work on different routes  
✅ **Debugging**: Errors are easier to trace  

## Hybrid Matching Usage

```python
from services.hybrid_matching import HybridMatchingEngine

matcher = HybridMatchingEngine()

# Match job to user
result = await matcher.match_job_to_user(
    job=job_doc,
    user_profile=user_profile,
    use_ml=True  # Enable ML enhancement
)

# Returns:
# {
#     "score": 0.85,
#     "matched": True,
#     "reasons": {
#         "hindi": "यह नौकरी आपकी शिक्षा और उम्र के लिए उपयुक्त है",
#         "english": "This job matches your education and age requirements"
#     },
#     "breakdown": {
#         "rule_score": 0.7,
#         "heuristic_score": 0.8,
#         "ml_score": 0.9
#     }
# }
```

## AI Learning System

The self-learning AI is integrated through `ai_routes.py`:

**Endpoints:**
- `POST /api/ai/learn-from-external` - Learn from other AIs
- `POST /api/ai/generate-smart` - Generate with learnings
- `POST /api/ai/web-search` - Search web for inf

## Form Intelligence System

ML-based form assistance integrated through `form_routes.py`:

**Endpoints:**
- `POST /api/forms/classify-field` - Classify field type (name, email, Aadhar, etc.)
- `POST /api/forms/predict-errors` - Predict form errors before submission
- `POST /api/forms/auto-fill` - Get auto-fill suggestions from user profile
- `POST /api/forms/train` - Train on portal datasets (Admin)
- `POST /api/forms/smart-form-fill` - Complete form assistance in one call
- `POST /api/forms/validate-batch` - Validate multiple forms
- `GET /api/forms/training-stats` - View training statistics (Admin)

**Use Case Example:**
```python
# User filling NREGA form
form_data = {
    "applicant_name": "rajesh",
    "mobile_no": "98765",
    "aadhaar_no": "123"
}

# Predict errors
errors = await form_engine.predict_errors(form_data)
# Returns: [
#   {"field": "mobile_no", "error": "Invalid phone format", "severity": "high"},
#   {"field": "aadhaar_no", "error": "Invalid aadhar format", "severity": "high"}
# ]

# Get auto-fill suggestions
suggestions = await form_engine.auto_fill_suggestions(
    ["Name", "Email", "Mobile"],
    user_profile
)
# Pre-fills known user data
```o
- `POST /api/ai/hybrid-match` - Hybrid job matching
- `GET /api/ai/learning-stats` - View statistics

## Testing

```bash
# Test individual routes
pytest tests/test_auth_routes.py
pytest tests/test_job_routes.py

# Test services
pytest tests/test_hybrid_matching.py

# Test full API
pytest tests/test_api.py
```

## Notes

- Old `server.py` is kept as backup (1837 lines)
- New structure totals ~1500 lines across 15 files
- Average file size: ~100 lines (much more manageable)
- All functionality preserved
- No breaking changes to API endpoints
