# 🤖 Digital Sahayak AI Module

A portable, reusable AI package for job/scheme recommendations, intent detection, document validation, and more.

## 📦 Features

| Module | Description | OpenAI Required |
|--------|-------------|-----------------|
| `job_recommender.py` | Job/Scheme recommendations based on user profile | ❌ No |
| `field_classifier.py` | Form field type detection and mapping | ❌ No |
| `summarizer.py` | Content rewriting and summarization | ❌ No |
| `intent_classifier.py` | WhatsApp message intent detection | ❌ No |
| `validator.py` | Document and field validation (Aadhar, PAN, etc.) | ❌ No |
| `learning_system.py` | Self-learning AI with OpenAI integration | ✅ Optional |

## 🚀 Quick Start

### Installation

```bash
# Copy the ai folder to your project
cp -r backend/ai /path/to/your/project/

# Install dependencies
pip install numpy
pip install openai  # Only if using learning_system.py
```

### Basic Usage

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
