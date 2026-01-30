# 🤖 Digital Sahayak AI Module

A portable, reusable AI package for job/scheme recommendations, intent detection, document validation, and more.

## �️ Architecture Overview

### Advanced ML Models (v2.0)

| Task | Model | Architecture | Fallback |
|------|-------|--------------|----------|
| **Job Recommendation** | LambdaMART | Gradient-boosted ranking + Two-Tower retrieval | Rule-based scoring |
| **Form Field Classification** | BERT + CNN | Transformer (labels) + CNN (field detection) | Regex patterns |
| **Content Summarization** | T5/mT5 | Seq2Seq abstractive summarization | Template-based |
| **Intent Classification** | DistilBERT | 40% smaller, 60% faster than BERT | Keywords + BoW |
| **Document Validation** | CNN + OCR | ResNet (doc type) + Tesseract/EasyOCR | Pattern matching |

### Why These Models?

- **LambdaMART**: "Considered state-of-the-art for learning-to-rank on tabular data" - widely used in search/recommendations
- **DistilBERT**: "40% smaller, 60% faster while retaining 97% of BERT's capabilities" - ideal for real-time intent detection
- **T5/mT5**: "Particularly well-suited for summarization" - generates new sentences for copyright-safe rewrites
- **CNN + Transformer**: Industrial best practice for form processing - CNNs capture visual layout, transformers understand semantics

## 🌐 Language Support

**Primary Language:** English (en)  
**Secondary Language:** Hindi (hi)

All labels, messages, intents, and responses are pre-defined in both languages - **no translation API needed**.

```python
from ai import t, t_both, t_bi, detect_lang

# Get text in specific language
text_en = t("labels.education.graduate", "en")  # "Graduate"
text_hi = t("labels.education.graduate", "hi")  # "स्नातक"

# Get both languages
en, hi = t_both("labels.education.graduate")  # ("Graduate", "स्नातक")

# Get bilingual text
text = t_bi("labels.education.graduate")  # "Graduate / स्नातक"

# Detect language
lang = detect_lang("मुझे नौकरी चाहिए")  # "hi"
lang = detect_lang("I want a job")  # "en"
lang = detect_lang("mujhe job chahiye")  # "hinglish"
```

## 📦 Features

| Module | Description | ML Available | OpenAI Required |
|--------|-------------|--------------|-----------------|
| `job_recommender.py` | Job/Scheme recommendations | ✅ LambdaMART | ❌ No |
| `field_classifier.py` | Form field detection/mapping | ✅ CNN+BERT | ❌ No |
| `summarizer.py` | Content rewriting/summarization | ✅ T5/mT5 | ❌ No |
| `intent_classifier.py` | WhatsApp intent detection | ✅ DistilBERT | ❌ No |
| `validator.py` | Document validation | ✅ OCR+CNN | ❌ No |
| `learning_system.py` | Self-learning with feedback | N/A | ✅ Optional |

## 🚀 Quick Start

### Installation

```bash
# Basic (rule-based only)
pip install numpy pillow

# With ML models (optional)
pip install lightgbm transformers torch sentence-transformers
pip install pytesseract easyocr torchvision
```

### Basic Usage (Rule-Based)

```python
from ai import JobRecommender, FieldClassifier, IntentClassifier

# 1. Job Recommendations
recommender = JobRecommender()
user_profile = {
    "education": "Graduate",
    "age": 25,
    "state": "Bihar",
    "preferred_categories": ["Railway", "SSC"]
}
jobs = [...]  # List of job documents
recommendations = recommender.get_recommendations(user_profile, jobs, top_k=5)

# 2. Form Field Classification
classifier = FieldClassifier()
field_type = classifier.classify_field("Father's Name")  # Returns FieldType.FATHER_NAME

# 3. WhatsApp Intent Detection
intent_classifier = IntentClassifier()
result = intent_classifier.classify("मुझे रेलवे की नौकरी चाहिए")
# Returns: IntentType.JOB_SEARCH with confidence score
```

### Advanced Usage (ML-Based)

```python
from ai import (
    AdvancedJobRecommender, get_recommendations,
    AdvancedFieldClassifier, classify_field,
    AdvancedSummarizer, rewrite, summarize,
    AdvancedIntentClassifier, predict_intent,
    AdvancedDocumentValidator, validate_document
)

# 1. ML-based Job Recommendations (LambdaMART)
recommender = AdvancedJobRecommender(models_dir="./models")
recommendations = recommender.get_recommendations(user_profile, jobs, use_ml=True)

# Or use convenience function
recs = get_recommendations(user_profile, jobs, use_advanced=True)

# 2. ML-based Intent Classification (DistilBERT)
result = predict_intent("I want to apply for railway jobs", use_ml=True)
# Returns: {"intent": "job_apply", "confidence": 0.92, "model_used": "distilbert"}

# 3. ML-based Summarization (T5/mT5)
summary = summarize(job_description, language="hi", use_ml=True)
rewritten = rewrite(text, language="en", use_ml=True)

# 4. Document Validation (OCR + CNN)
result = validate_document("./aadhar.jpg", expected_type="aadhar")
# Returns extracted fields, validation status, and quality score
```

### With OpenAI (Learning System)

```python
from openai import OpenAI
from ai import SelfLearningAI

# Initialize with OpenAI client
openai_client = OpenAI(api_key="your-key")
db = your_mongodb_database

ai = SelfLearningAI(openai_client, db)

# Learn from external AI
result = await ai.learn_from_other_ai(
    prompt="Best jobs for 25-year-old graduate",
    other_ai_response="ChatGPT says...",
    ai_name="ChatGPT"
)

# Generate smart response
response = await ai.generate_with_learning(
    prompt="Recommend jobs for me",
    context={"education": "Graduate", "age": 25}
)
```

## 📁 File Structure

```
ai/
├── __init__.py          # Package exports
├── README.md            # This file
├── job_recommender.py   # Job/Scheme recommendations
├── field_classifier.py  # Form field detection
├── summarizer.py        # Content rewriting
├── intent_classifier.py # WhatsApp intent detection
├── validator.py         # Document validation
├── learning_system.py   # Self-learning AI (OpenAI)
└── training/            # Training data and models
```

## 🔧 Configuration

### Environment Variables

```bash
# Optional - only for learning_system.py
OPENAI_API_KEY=your-openai-key

# MongoDB (for learning_system.py)
MONGO_URL=mongodb://localhost:27017
DB_NAME=digital_sahayak
```

### Scoring Weights (job_recommender.py)

```python
rule_weights = {
    "education": 0.25,  # 25% weight
    "age": 0.20,        # 20% weight
    "location": 0.20,   # 20% weight
    "category": 0.20,   # 20% weight
    "salary": 0.15,     # 15% weight
}
```

## 📚 API Reference

### JobRecommender

```python
recommender.get_recommendations(
    user_profile: Dict,     # User's profile data
    jobs: List[Dict],       # List of jobs to rank
    top_k: int = 10,        # Number of results
    include_reasoning: bool = True  # Include Hindi explanations
) -> List[Dict]
```

### FieldClassifier

```python
classifier.classify_field(
    label: str,            # Field label text
    hint: str = None       # Optional hint/placeholder
) -> FieldType

classifier.map_profile_to_fields(
    profile: Dict,         # User profile
    fields: List[str]      # Form fields
) -> Dict[str, str]
```

### IntentClassifier

```python
classifier.classify(
    message: str,          # User message
    context: Dict = None   # Conversation context
) -> Tuple[IntentType, float, Dict]
```

### DocumentValidator

```python
validator.validate_field(
    value: str,            # Field value
    field_type: str        # "aadhar", "pan", "phone", etc.
) -> ValidationResult
```

## 🔄 Reusing in Other Projects

1. **Copy the `ai/` folder** to your project
2. **Install dependencies**: `pip install numpy`
3. **Import and use**:

```python
# In your project
from ai import JobRecommender, IntentClassifier

# That's it! No external AI needed for basic features
```

## 📝 Hindi/English Support

All modules support both Hindi and English:

```python
# Hindi intent classification
classifier.classify("मुझे सरकारी नौकरी चाहिए")  # JOB_SEARCH

# English intent classification  
classifier.classify("I want a government job")  # JOB_SEARCH

# Hindi field detection
classifier.classify_field("पिता का नाम")  # FATHER_NAME
```

## 🛠️ Development

### Adding New Modules

1. Create `your_module.py` in `ai/` folder
2. Add to `__init__.py`:
```python
from .your_module import YourClass
__all__.append("YourClass")
```

### Adding New Intent Types

Edit `intent_classifier.py`:
```python
class IntentType(Enum):
    YOUR_NEW_INTENT = "your_new_intent"

INTENT_PATTERNS[IntentType.YOUR_NEW_INTENT] = {
    "keywords": ["keyword1", "कीवर्ड2"],
    "phrases": ["your phrase"],
    "weight": 1.0,
}
```

## 📄 License

Part of Digital Sahayak Project. Free to use and modify.

---

Made with ❤️ for Indian Government Jobs and Schemes Portal
