# Apply AI Engine v1 - API Documentation

## Authentication

All API requests require Bearer token authentication:

```http
Authorization: Bearer YOUR_API_KEY
```

## Base URL

**Development:** `http://localhost:8000/api/v1`  
**Production:** `https://api.applyai.in/v1`

## Endpoints

### 1. Job Matching

**Endpoint:** `POST /match/job`

**Request:**
```json
{
  "user_profile": {
    "education": "Graduate",
    "age": 25,
    "state": "Bihar",
    "preferred_categories": ["Railway", "SSC"]
  },
  "job": {
    "id": "job123",
    "title": "Railway Clerk",
    "education_required": "Graduate",
    "min_age": 18,
    "max_age": 30,
    "location": "Bihar",
    "category": "Railway"
  }
}
```

**Response:**
```json
{
  "score": 0.95,
  "matched": true,
  "confidence": "high",
  "reasons": {
    "hindi": "यह नौकरी आपकी शिक्षा और उम्र के लिए बिल्कुल सही है",
    "english": "This job perfectly matches your education and age"
  },
  "breakdown": {
    "education_score": 0.3,
    "age_score": 0.2,
    "location_score": 0.2,
    "category_score": 0.25
  }
}
```

**Credits:** 1 credit per request

---

### 2. Field Classification

**Endpoint:** `POST /forms/classify`

**Request:**
```json
{
  "field_label": "आधार संख्या",
  "field_value": "123456789012"
}
```

**Response:**
```json
{
  "field_label": "आधार संख्या",
  "classified_type": "aadhar",
  "confidence": 0.95,
  "suggestions": {
    "placeholder": "12-digit Aadhar number",
    "validation": "Exactly 12 digits",
    "example": "123456789012"
  }
}
```

**Credits:** 0.1 credits per request

---

### 3. Form Validation

**Endpoint:** `POST /forms/validate`

**Request:**
```json
{
  "form_data": {
    "name": "Rajesh Kumar",
    "email": "rajesh@example.com",
    "phone": "9876543210",
    "aadhar": "123456789012"
  }
}
```

**Response:**
```json
{
  "is_valid": true,
  "error_count": 0,
  "errors": [],
  "severity_breakdown": {
    "high": 0,
    "medium": 0,
    "low": 0
  }
}
```

**Credits:** 1 credit per request

---

### 4. Auto-fill Suggestions

**Endpoint:** `POST /forms/autofill`

**Request:**
```json
{
  "form_fields": ["Name", "Email", "Phone", "State"],
  "user_profile": {
    "name": "Rajesh Kumar",
    "email": "rajesh@example.com",
    "phone": "9876543210",
    "state": "Bihar"
  }
}
```

**Response:**
```json
{
  "suggestions": {
    "Name": "Rajesh Kumar",
    "Email": "rajesh@example.com",
    "Phone": "9876543210",
    "State": "Bihar"
  },
  "confidence": 0.9
}
```

**Credits:** 0.5 credits per request

---

### 5. Smart Form Fill

**Endpoint:** `POST /forms/smart-fill`

**Request:**
```json
{
  "form_fields": ["Name", "Email", "Phone", "Aadhar"],
  "partial_data": {
    "Phone": "9876543210"
  },
  "user_profile": {
    "name": "Rajesh Kumar",
    "email": "rajesh@example.com"
  }
}
```

**Response:**
```json
{
  "filled_form": {
    "Name": "Rajesh Kumar",
    "Email": "rajesh@example.com",
    "Phone": "9876543210",
    "Aadhar": ""
  },
  "classifications": {
    "Name": {
      "classified_type": "name",
      "confidence": 0.85
    }
  },
  "errors": [],
  "auto_filled_count": 2,
  "user_filled_count": 1,
  "is_valid": true
}
```

**Credits:** 2 credits per request

---

### 6. Submit Feedback

**Endpoint:** `POST /learn/feedback`

**Request:**
```json
{
  "user_id": "user123",
  "job_id": "job456",
  "action": "applied",
  "match_score": 0.85
}
```

**Response:**
```json
{
  "status": "learned",
  "message": "Feedback recorded for future improvements"
}
```

**Credits:** Free

---

### 7. Batch Matching

**Endpoint:** `POST /match/batch`

**Request:**
```json
{
  "user_profile": {...},
  "items": [
    {"id": "job1", "title": "Job 1", ...},
    {"id": "job2", "title": "Job 2", ...}
  ]
}
```

**Response:**
```json
{
  "total": 2,
  "processed": 2,
  "results": [
    {"score": 0.95, "matched": true, ...},
    {"score": 0.75, "matched": true, ...}
  ]
}
```

**Credits:** 1 credit per item

---

### 8. Usage Statistics

**Endpoint:** `GET /analytics/usage`

**Response:**
```json
{
  "organization": "Your Company",
  "plan": "startup",
  "credits_used": 1250,
  "credits_remaining": 48750,
  "requests_today": 45
}
```

**Credits:** Free

---

### 9. Health Check

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "engines": {
    "matching": "active",
    "form_intelligence": "active"
  },
  "uptime": "99.9%"
}
```

**Credits:** Free

---

## Error Codes

| Code | Description |
|------|-------------|
| 200 | Success |
| 401 | Invalid API key |
| 402 | Insufficient credits |
| 403 | API key inactive/expired |
| 404 | Resource not found |
| 429 | Rate limit exceeded |
| 500 | Internal server error |
| 503 | Service unavailable |

---

## Rate Limits

| Plan | Requests/Minute | Requests/Day |
|------|-----------------|--------------|
| Free | 10 | 1,000 |
| Startup | 100 | 50,000 |
| Business | 500 | 500,000 |
| Enterprise | Unlimited | Unlimited |

---

## Code Examples

### Python
```python
import requests

API_KEY = "your_api_key"
BASE_URL = "https://api.applyai.in/v1"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# Match job
response = requests.post(
    f"{BASE_URL}/match/job",
    headers=headers,
    json={
        "user_profile": {...},
        "job": {...}
    }
)

print(response.json())
```

### JavaScript
```javascript
const API_KEY = 'your_api_key';
const BASE_URL = 'https://api.applyai.in/v1';

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

// Match job
const response = await fetch(`${BASE_URL}/match/job`, {
  method: 'POST',
  headers: headers,
  body: JSON.stringify({
    user_profile: {...},
    job: {...}
  })
});

const data = await response.json();
console.log(data);
```

### cURL
```bash
curl -X POST https://api.applyai.in/v1/match/job \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_profile": {...},
    "job": {...}
  }'
```

---

## Support

**Email:** support@applyai.in  
**Documentation:** https://docs.applyai.in  
**Status:** https://status.applyai.in
