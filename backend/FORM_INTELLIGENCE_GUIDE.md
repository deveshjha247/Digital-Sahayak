# Form Intelligence System - ML-based Field Classification & Error Prediction

## Overview

The Form Intelligence Engine uses ML to automatically classify form fields, predict errors, and provide smart auto-fill suggestions for government portal forms.

## Features

### 1. **Field Classification**
Automatically identifies field types using hybrid approach:
- **Rule-based**: Pattern matching for common Indian form fields
- **ML-enhanced**: OpenAI GPT for ambiguous cases

**Supported Field Types:**
- Personal: name, email, phone, age, gender
- Address: address, city, state, pincode
- Documents: aadhar, pan
- Other: education, income, caste, occupation

### 2. **Error Prediction**
Predicts potential errors before form submission:
- **Validation**: Format checks for phone, email, PAN, Aadhar, etc.
- **Pattern Detection**: Finds capitalization issues, extra spaces, unusual patterns
- **ML Analysis**: Detects inconsistencies and contextual errors

### 3. **Auto-Fill Suggestions**
Smart form filling based on user profile:
- Maps user profile data to form fields
- Classifies fields intelligently
- Suggests pre-filled values with confidence scores

### 4. **Portal Training**
Learns from historical form submissions:
- Trains on portal-specific datasets
- Learns field patterns and formats
- Improves classification accuracy over time

## API Endpoints

### Classify Single Field
```http
POST /api/forms/classify-field
```
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

### Predict Errors
```http
POST /api/forms/predict-errors
```
**Request:**
```json
{
  "form_data": {
    "name": "rajesh kumar",
    "email": "rajesh@invalid",
    "phone": "12345",
    "aadhar": "123"
  }
}
```
**Response:**
```json
{
  "has_errors": true,
  "error_count": 3,
  "errors": [
    {
      "field": "email",
      "error": "Invalid email format",
      "severity": "high",
      "suggestion": "rajesh@example.com",
      "expected_format": "Valid email format"
    },
    {
      "field": "phone",
      "error": "Invalid phone format",
      "severity": "high",
      "suggestion": "9876543210",
      "expected_format": "Starts with 6-9"
    },
    {
      "field": "aadhar",
      "error": "Invalid aadhar format",
      "severity": "high",
      "suggestion": "123456789012",
      "expected_format": "Exactly 12 digits"
    }
  ],
  "severity_breakdown": {
    "high": 3,
    "medium": 0,
    "low": 0
  }
}
```

### Auto-Fill Suggestions
```http
POST /api/forms/auto-fill
```
**Request:**
```json
{
  "form_fields": ["Name", "Email", "Mobile", "State", "Education"]
}
```
**Response:**
```json
{
  "suggestions": {
    "Name": "Rajesh Kumar",
    "Email": "rajesh@example.com",
    "Mobile": "9876543210",
    "State": "Delhi",
    "Education": "Graduate"
  },
  "confidence": 0.9
}
```

### Train from Portal Dataset
```http
POST /api/forms/train (Admin only)
```
**Request:**
```json
{
  "portal_name": "NREGA Portal",
  "form_submissions": [
    {
      "applicant_name": "Rajesh Kumar",
      "mobile_no": "9876543210",
      "aadhaar": "123456789012",
      "state": "Bihar"
    },
    {
      "applicant_name": "Priya Sharma",
      "mobile_no": "9123456789",
      "aadhaar": "987654321098",
      "state": "UP"
    }
  ]
}
```
**Response:**
```json
{
  "message": "Trained on 2 submissions from NREGA Portal",
  "fields_learned": 4,
  "patterns": {
    "applicant_name": {
      "classified_type": "name",
      "frequency": 2,
      "pattern": {"type": "alphabetic"},
      "confidence": 0.85
    },
    "mobile_no": {
      "classified_type": "phone",
      "frequency": 2,
      "pattern": {"type": "numeric", "avg_length": 10},
      "confidence": 0.95
    }
  }
}
```

### Smart Form Fill
```http
POST /api/forms/smart-form-fill
```
Combines classification, auto-fill, and error prediction in one call.

**Request:**
```json
{
  "form_fields": ["Name", "Email", "Phone", "Aadhar"],
  "partial_data": {
    "Phone": "9876543210"
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
    "Name": {"classified_type": "name", "confidence": 0.85},
    "Email": {"classified_type": "email", "confidence": 0.95}
  },
  "errors": [],
  "auto_filled_count": 2,
  "user_filled_count": 1,
  "has_errors": false
}
```

### Batch Validation
```http
POST /api/forms/validate-batch
```
Validate multiple forms at once.

### Training Statistics
```http
GET /api/forms/training-stats?portal_name=NREGA Portal (Admin only)
```
**Response:**
```json
{
  "portals_trained": 5,
  "total_submissions": 1500,
  "total_fields_learned": 45,
  "trainings": [...]
}
```

## Technical Details

### Field Classification Algorithm

1. **Rule-based Matching** (Primary)
   - Regex patterns for common field names
   - Supports Hindi and English labels
   - Fast and deterministic

2. **ML Classification** (Fallback)
   - Uses GPT-3.5-turbo for ambiguous cases
   - Context-aware understanding
   - Returns confidence scores

3. **Validation Enhancement**
   - If field value provided, validates against patterns
   - Increases confidence for valid formats
   - Provides format suggestions

### Error Prediction

**Three-layer approach:**

1. **Format Validation**
   - Regex patterns for email, phone, PAN, Aadhar, etc.
   - Indian-specific validations
   - Immediate feedback

2. **Pattern Detection**
   - Capitalization inconsistencies
   - Extra whitespace
   - Unusual number patterns

3. **ML-based Analysis**
   - Contextual error detection
   - Inconsistency identification
   - Semantic validation

### Training System

**Learning from portal datasets:**
- Extracts field frequency and patterns
- Analyzes value distributions
- Stores learned patterns in MongoDB
- Improves classification over time

**Pattern Analysis:**
- Numeric patterns (length distributions)
- Alphabetic patterns
- Mixed patterns
- Value frequency

## Use Cases

### 1. Job Application Forms
```python
# User filling job application
fields = ["Full Name", "Email ID", "Contact Number", "Highest Qualification"]
auto_fill = await form_engine.auto_fill_suggestions(fields, user_profile)
# Pre-fills known information
```

### 2. Government Scheme Applications
```python
# NREGA application form
form_data = {
    "applicant_name": "RAJESH KUMAR",
    "mobile": "9876543210",
    "aadhaar": "12345",  # Error: too short
    "bank_account": "1234567890123456"
}
errors = await form_engine.predict_errors(form_data)
# Warns about Aadhar length error before submission
```

### 3. Portal Scraping + Training
```python
# Scrape submissions from government portal
submissions = scrape_portal("https://nrega.gov.in")

# Train form intelligence
await form_engine.train_from_dataset("NREGA", submissions)
# Now knows NREGA-specific field patterns
```

### 4. Real-time Form Assistance
```javascript
// Frontend integration
const checkField = async (label, value) => {
  const result = await fetch('/api/forms/classify-field', {
    method: 'POST',
    body: JSON.stringify({ field_label: label, field_value: value })
  });
  
  // Show suggestions to user in real-time
  showSuggestions(result.suggestions);
};
```

## Benefits

✅ **Reduced Form Errors**: Catch mistakes before submission  
✅ **Faster Form Filling**: Auto-fill with user profile data  
✅ **Portal Compatibility**: Learns portal-specific patterns  
✅ **Hindi Support**: Works with Devanagari field labels  
✅ **Smart Validation**: Context-aware error detection  
✅ **Continuous Learning**: Improves with more data  

## Database Collections

### `form_training_data`
Stores learned patterns from portal datasets:
```json
{
  "portal_name": "NREGA Portal",
  "trained_at": "2026-01-28T10:30:00Z",
  "total_submissions": 500,
  "learned_patterns": {
    "applicant_name": {
      "classified_type": "name",
      "frequency": 500,
      "pattern": {"type": "alphabetic"}
    }
  }
}
```

## Integration Example

```python
from services.form_intelligence import FormIntelligenceEngine

# Initialize
engine = FormIntelligenceEngine()

# Classify field
classification = await engine.classify_field("आधार संख्या", "123456789012")
# Returns: {"classified_type": "aadhar", "confidence": 0.95}

# Predict errors
errors = await engine.predict_errors(form_data)

# Auto-fill
suggestions = await engine.auto_fill_suggestions(fields, user_profile)

# Train on dataset
await engine.train_from_dataset("Portal Name", submissions)
```

## Future Enhancements

- [ ] Support for more regional languages
- [ ] Custom validation rules per portal
- [ ] Image-based field detection (OCR)
- [ ] Form completion prediction
- [ ] Document verification integration
- [ ] Multi-step form guidance

## Notes

- Requires OpenAI API key for ML classification
- Training improves accuracy over time
- Supports both Hindi and English labels
- Optimized for Indian government forms
- Works with portal-specific terminology
