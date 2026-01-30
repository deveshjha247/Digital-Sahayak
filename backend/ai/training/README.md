# 📊 AI Training Data Guide

This folder contains dataset definitions, collectors, and sample training data for Digital Sahayak AI system.

## 🎯 Dataset Objectives

### 1. Job/Yojana Recommender Dataset

**Objective:** Train a ranking model to match jobs/schemes with user profiles based on explicit and implicit feedback.

| Label | Score | Description |
|-------|-------|-------------|
| `applied` | 1.0 | User submitted application |
| `saved` | 0.8 | User bookmarked for later |
| `clicked` | 0.6 | User viewed full details |
| `viewed_long` | 0.4 | Viewed >30 seconds |
| `skipped` | 0.1 | Shown but not interacted |
| `rejected` | 0.0 | User marked 'not interested' |

**Data Sources:**
- User application logs from database
- Click-through events from frontend
- Job listings scraped from sarkariresult.com, rojgar.com

**Files:**
- `data/job_matching/sample_jobs.jsonl` - Job postings
- `data/job_matching/sample_users.jsonl` - User profiles
- `data/job_matching/sample_interactions.jsonl` - User-job interactions

---

### 2. Form Field Classification Dataset

**Objective:** Train a model to identify semantic type of form fields from label text, enabling auto-fill functionality.

**Labels (60+ field types):**
- Personal: `applicant_name`, `father_name`, `mother_name`, `date_of_birth`, `gender`
- Identity: `aadhar_number`, `pan_number`, `voter_id`
- Contact: `mobile_number`, `email`
- Address: `village`, `district`, `state`, `pincode`
- Education: `qualification`, `university`, `percentage`
- Bank: `bank_name`, `account_number`, `ifsc_code`

**Data Sources:**
- Scrape forms from pmjay.gov.in, pmkisan.gov.in
- Bihar RTPS, Jharkhand Seva Portal
- Railway recruitment portals, SSC, UPSC forms

**Files:**
- `data/form_fields/sample_fields.jsonl` - Labeled field examples

---

### 3. Content Rewriting Dataset

**Objective:** Train model to rewrite scraped job/scheme content into unique, readable summaries with key highlights.

**Input:** Raw scraped content (title, description, dates)
**Output:**
- Rewritten title (Hindi + English)
- Unique description (100-200 words)
- Key highlights (3-5 bullet points)
- Extracted data (salary, vacancies, qualification)

**Quality Metrics:**
- Uniqueness score (plagiarism check)
- Human quality rating (0-1)

**Files:**
- `data/content_rewriting/sample_content.jsonl` - Raw + rewritten pairs

---

### 4. Intent Classification Dataset

**Objective:** Train model to understand user intents from Hindi/English mixed messages for chatbot routing.

**Intent Categories:**

| Category | Intents |
|----------|---------|
| Job | `search_job`, `apply_job`, `job_status`, `job_details` |
| Yojana | `search_yojana`, `apply_yojana`, `yojana_eligibility` |
| Form | `fill_form`, `upload_document`, `check_document` |
| General | `greeting`, `help`, `goodbye`, `thanks` |
| Other | `complaint`, `feedback`, `out_of_scope`, `unclear` |

**Language Support:** Hindi, English, Hinglish (mixed)

**Files:**
- `data/intent/sample_messages.jsonl` - Labeled messages

---

### 5. Document Validation Dataset

**Objective:** Train model to validate Indian government documents for format correctness.

**Document Types:**
- Aadhar Card (12 digits, Verhoeff checksum)
- PAN Card (5 letters + 4 digits + 1 letter)
- Voter ID (3 letters + 7 digits)
- Phone (10 digits starting with 6-9)
- Pincode (6 digits)
- IFSC (11 characters)

**Files:**
- `data/validation/rules.json` - Validation patterns and rules

---

## 🔧 Data Collection

### Using Collectors

```python
from training.job_matching_collector import JobMatchingCollector
from training.form_field_collector import FormFieldCollector
from training.intent_collector import IntentCollector

# Collect job matching data
job_collector = JobMatchingCollector(data_dir="data/training/job_matching")
job_collector.add_job(job_data)
job_collector.add_user(user_data)
job_collector.log_interaction(user_id, job_id, "applied")

# Collect form fields
field_collector = FormFieldCollector(data_dir="data/training/form_fields")
field_collector.scrape_form(url="https://pmkisan.gov.in")
field_collector.log_correction(field_id, "wrong_tag", "correct_tag")

# Collect intents
intent_collector = IntentCollector(data_dir="data/training/intent")
intent_collector.add_message("मुझे नौकरी चाहिए", intent="search_job")
```

### Quality Checks

```python
from training.data_quality import Deduplicator, ClassBalanceAnalyzer

# Deduplicate
dedup = Deduplicator()
dedup.add(text)  # Returns True if unique

# Check class balance
analyzer = ClassBalanceAnalyzer()
analyzer.add_sample("search_job")
report = analyzer.get_balance_report()
```

---

## 📈 Target Dataset Sizes

| Dataset | Target Size | Current |
|---------|-------------|---------|
| Jobs | 5,000 | 10 |
| Users | 10,000 | 10 |
| Interactions | 100,000 | 20 |
| Form Fields | 10,000 | 30 |
| Intent Messages | 20,000 | 40 |
| Content Pairs | 5,000 | 5 |

---

## 🚀 How to Contribute Data

### 1. Manual Labeling
- Use the admin panel to review and label data
- Ensure consistent labeling following guidelines

### 2. Automated Collection
- Set up scrapers for job portals
- Enable interaction logging in frontend
- Configure WhatsApp message logging

### 3. Quality Assurance
- Review random samples weekly
- Track inter-annotator agreement
- Flag ambiguous cases for discussion

---

## 📋 Annotation Guidelines

### Job Relevance
- Mark `applied` only for actual form submissions
- `saved` means user clicked bookmark/favorite
- `skipped` is automatic if shown but no interaction

### Intent Labeling
- One primary intent per message
- Mark confidence: high/medium/low
- Flag Hinglish messages with `language: hinglish`

### Form Fields
- Choose most specific tag available
- Hindi labels map to same tags as English
- Log corrections for feedback loop

---

## 📁 Directory Structure

```
training/
├── README.md                 # This file
├── dataset_definitions.json  # Complete schema definitions
├── job_matching_collector.py # Job data collector
├── form_field_collector.py   # Form field collector
├── intent_collector.py       # Intent data collector
├── content_rewriting_collector.py
├── document_collector.py
├── data_quality.py           # Quality tools
├── __init__.py
└── data/                     # Training data files
    ├── job_matching/
    │   ├── sample_jobs.jsonl
    │   ├── sample_users.jsonl
    │   └── sample_interactions.jsonl
    ├── form_fields/
    │   └── sample_fields.jsonl
    ├── content_rewriting/
    │   └── sample_content.jsonl
    ├── intent/
    │   └── sample_messages.jsonl
    └── validation/
        └── rules.json
```

---

## 🔗 References

- [Dataset Definitions](./dataset_definitions.json) - Complete JSON schema
- [Job Recommender Module](../job_recommender.py)
- [Intent Classifier Module](../intent_classifier.py)
- [Field Classifier Module](../field_classifier.py)
