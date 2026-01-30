"""
Annotation Guidelines & Configuration
Comprehensive guidelines for labeling data across all AI tasks
"""

import json
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)


# =============================================================================
# ANNOTATION TASK TYPES
# =============================================================================

class AnnotationTaskType(Enum):
    """Types of annotation tasks"""
    JOB_YOJANA_MATCHING = "job_yojana_matching"
    FORM_FIELD_CLASSIFICATION = "form_field_classification"
    CONTENT_SUMMARIZATION = "content_summarization"
    INTENT_CLASSIFICATION = "intent_classification"
    DOCUMENT_VALIDATION = "document_validation"
    ENTITY_EXTRACTION = "entity_extraction"


# =============================================================================
# PRIVACY & SENSITIVE DATA RULES
# =============================================================================

SENSITIVE_FIELDS = {
    # PII fields - must be masked/anonymized before annotation
    "aadhaar": {
        "pattern": r"\d{4}\s?\d{4}\s?\d{4}",
        "mask": "XXXX XXXX XXXX",
        "description_en": "Aadhaar Number",
        "description_hi": "आधार नंबर",
    },
    "pan": {
        "pattern": r"[A-Z]{5}\d{4}[A-Z]",
        "mask": "XXXXX0000X",
        "description_en": "PAN Number",
        "description_hi": "पैन नंबर",
    },
    "phone": {
        "pattern": r"(\+91[\-\s]?)?[6-9]\d{9}",
        "mask": "+91 XXXXX XXXXX",
        "description_en": "Phone Number",
        "description_hi": "फोन नंबर",
    },
    "email": {
        "pattern": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
        "mask": "user@example.com",
        "description_en": "Email Address",
        "description_hi": "ईमेल पता",
    },
    "bank_account": {
        "pattern": r"\d{9,18}",
        "mask": "XXXXXXXXXX",
        "description_en": "Bank Account Number",
        "description_hi": "बैंक खाता नंबर",
    },
    "address": {
        "pattern": None,  # Complex - manual review
        "mask": "[ADDRESS REDACTED]",
        "description_en": "Full Address",
        "description_hi": "पूरा पता",
    },
}

PRIVACY_GUIDELINES = {
    "en": """
## Privacy Guidelines for Annotators

1. **Never copy or share** any personal information from annotation tasks.
2. **Report** if you see unmasked sensitive data (Aadhaar, PAN, phone, etc.).
3. **Do not** attempt to identify individuals from the data.
4. **Skip** any example that contains clearly identifiable personal information.
5. **Use secure systems** only - do not download data to personal devices.
6. All work must be done on approved systems with audit logging.
""",
    "hi": """
## एनोटेटर्स के लिए गोपनीयता दिशानिर्देश

1. एनोटेशन कार्यों से कोई भी व्यक्तिगत जानकारी **कभी कॉपी या शेयर न करें**।
2. यदि आप बिना मास्क की गई संवेदनशील जानकारी (आधार, पैन, फोन आदि) देखते हैं तो **रिपोर्ट करें**।
3. डेटा से व्यक्तियों की पहचान करने का **प्रयास न करें**।
4. ऐसे किसी भी उदाहरण को **छोड़ दें** जिसमें स्पष्ट रूप से पहचान योग्य व्यक्तिगत जानकारी हो।
5. केवल **सुरक्षित सिस्टम** का उपयोग करें - व्यक्तिगत उपकरणों पर डेटा डाउनलोड न करें।
""",
}


# =============================================================================
# JOB/YOJANA MATCHING GUIDELINES
# =============================================================================

JOB_YOJANA_LABELS = {
    "categories": {
        "railway": {"en": "Railway Jobs", "hi": "रेलवे नौकरियां"},
        "ssc": {"en": "SSC Jobs", "hi": "एसएससी नौकरियां"},
        "bank": {"en": "Banking Jobs", "hi": "बैंकिंग नौकरियां"},
        "police": {"en": "Police/Defence", "hi": "पुलिस/रक्षा"},
        "teaching": {"en": "Teaching", "hi": "शिक्षण"},
        "healthcare": {"en": "Healthcare", "hi": "स्वास्थ्य सेवा"},
        "state_govt": {"en": "State Government", "hi": "राज्य सरकार"},
        "central_govt": {"en": "Central Government", "hi": "केंद्र सरकार"},
        "psu": {"en": "PSU Jobs", "hi": "पीएसयू नौकरियां"},
        "court": {"en": "Court/Legal", "hi": "न्यायालय/कानूनी"},
    },
    "education_levels": {
        "10th": {"en": "10th Pass", "hi": "दसवीं पास"},
        "12th": {"en": "12th Pass", "hi": "बारहवीं पास"},
        "graduate": {"en": "Graduate", "hi": "स्नातक"},
        "post_graduate": {"en": "Post Graduate", "hi": "स्नातकोत्तर"},
        "diploma": {"en": "Diploma/ITI", "hi": "डिप्लोमा/आईटीआई"},
        "professional": {"en": "Professional Degree", "hi": "प्रोफेशनल डिग्री"},
    },
    "relevance_scores": {
        "highly_relevant": {"score": 1.0, "en": "Highly Relevant", "hi": "अत्यधिक प्रासंगिक"},
        "relevant": {"score": 0.7, "en": "Relevant", "hi": "प्रासंगिक"},
        "somewhat_relevant": {"score": 0.4, "en": "Somewhat Relevant", "hi": "कुछ हद तक प्रासंगिक"},
        "not_relevant": {"score": 0.0, "en": "Not Relevant", "hi": "प्रासंगिक नहीं"},
    },
}

JOB_MATCHING_GUIDELINES = {
    "en": """
## Job/Yojana Matching Annotation Guidelines

### Task Overview
Label job postings and government schemes with attributes for matching to user profiles.

### Required Labels

1. **Category** - Select the most appropriate category:
   - Railway, SSC, Bank, Police/Defence, Teaching, Healthcare, State Govt, Central Govt, PSU, Court

2. **State** - Which state(s) is this job for?
   - Select "All India" if applicable nationwide
   - Select specific state(s) for state-level jobs

3. **Education Level** - Minimum qualification required:
   - 10th Pass, 12th Pass, Graduate, Post Graduate, Diploma/ITI, Professional

4. **Age Range** - Extract minimum and maximum age (with relaxation info if mentioned)

5. **Relevance Score** - For user segment matching:
   - Highly Relevant (1.0): Perfect match for target segment
   - Relevant (0.7): Good match with minor differences
   - Somewhat Relevant (0.4): Partial match
   - Not Relevant (0.0): No match

### Tricky Cases

- **Multiple categories**: Choose the PRIMARY category; add secondary in notes
- **Unclear education**: Default to the lowest mentioned qualification
- **Age relaxation**: Note the base age AND relaxation rules separately
- **Expired postings**: Mark as expired but still label for training data

### Skip Rules
- Skip if the text is truncated and missing key information
- Skip if it's clearly spam or unrelated content
- Skip if the language is neither Hindi nor English
""",
    "hi": """
## नौकरी/योजना मैचिंग एनोटेशन दिशानिर्देश

### कार्य अवलोकन
उपयोगकर्ता प्रोफाइल से मिलान के लिए नौकरी पोस्टिंग और सरकारी योजनाओं को विशेषताओं के साथ लेबल करें।

### आवश्यक लेबल

1. **श्रेणी** - सबसे उपयुक्त श्रेणी चुनें:
   - रेलवे, एसएससी, बैंक, पुलिस/रक्षा, शिक्षण, स्वास्थ्य सेवा, राज्य सरकार, केंद्र सरकार, पीएसयू, न्यायालय

2. **राज्य** - यह नौकरी किस राज्य के लिए है?
   - यदि राष्ट्रव्यापी लागू हो तो "अखिल भारतीय" चुनें

3. **शिक्षा स्तर** - न्यूनतम योग्यता:
   - दसवीं पास, बारहवीं पास, स्नातक, स्नातकोत्तर, डिप्लोमा/आईटीआई

4. **आयु सीमा** - न्यूनतम और अधिकतम आयु निकालें

5. **प्रासंगिकता स्कोर** - उपयोगकर्ता सेगमेंट मैचिंग के लिए
""",
}


# =============================================================================
# FORM FIELD CLASSIFICATION GUIDELINES
# =============================================================================

FORM_FIELD_TYPES = {
    # Personal Information
    "name": {
        "en": "Full Name",
        "hi": "पूरा नाम",
        "examples_en": ["Name", "Candidate Name", "Applicant Name", "Full Name"],
        "examples_hi": ["नाम", "आवेदक का नाम", "पूरा नाम", "अभ्यर्थी का नाम"],
        "input_type": "text",
        "validation": r"^[a-zA-Z\s\u0900-\u097F]{2,100}$",
    },
    "father_name": {
        "en": "Father's Name",
        "hi": "पिता का नाम",
        "examples_en": ["Father's Name", "Father Name", "S/o", "D/o"],
        "examples_hi": ["पिता का नाम", "पिता नाम", "पिता/पति का नाम"],
        "input_type": "text",
        "validation": r"^[a-zA-Z\s\u0900-\u097F]{2,100}$",
    },
    "mother_name": {
        "en": "Mother's Name",
        "hi": "माता का नाम",
        "examples_en": ["Mother's Name", "Mother Name"],
        "examples_hi": ["माता का नाम", "माता नाम"],
        "input_type": "text",
        "validation": r"^[a-zA-Z\s\u0900-\u097F]{2,100}$",
    },
    "dob": {
        "en": "Date of Birth",
        "hi": "जन्म तिथि",
        "examples_en": ["Date of Birth", "DOB", "Birth Date", "D.O.B."],
        "examples_hi": ["जन्म तिथि", "जन्मतिथि", "जन्म की तारीख"],
        "input_type": "date",
        "validation": r"^\d{2}[/-]\d{2}[/-]\d{4}$",
    },
    "gender": {
        "en": "Gender",
        "hi": "लिंग",
        "examples_en": ["Gender", "Sex", "Male/Female"],
        "examples_hi": ["लिंग", "पुरुष/महिला"],
        "input_type": "select",
        "options": ["Male", "Female", "Other"],
    },
    "email": {
        "en": "Email Address",
        "hi": "ईमेल पता",
        "examples_en": ["Email", "Email ID", "E-mail Address", "Email Address"],
        "examples_hi": ["ईमेल", "ई-मेल", "ईमेल आईडी"],
        "input_type": "email",
        "validation": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
    },
    "phone": {
        "en": "Phone/Mobile Number",
        "hi": "मोबाइल नंबर",
        "examples_en": ["Mobile", "Phone", "Contact Number", "Mobile No.", "Phone Number"],
        "examples_hi": ["मोबाइल", "फोन", "संपर्क नंबर", "मोबाइल नंबर"],
        "input_type": "tel",
        "validation": r"^[6-9]\d{9}$",
    },
    "address": {
        "en": "Address",
        "hi": "पता",
        "examples_en": ["Address", "Permanent Address", "Correspondence Address", "Residential Address"],
        "examples_hi": ["पता", "स्थायी पता", "पत्राचार पता", "निवास पता"],
        "input_type": "textarea",
        "validation": None,
    },
    "state": {
        "en": "State",
        "hi": "राज्य",
        "examples_en": ["State", "State Name", "Select State"],
        "examples_hi": ["राज्य", "प्रदेश"],
        "input_type": "select",
        "options": "INDIAN_STATES",
    },
    "district": {
        "en": "District",
        "hi": "जिला",
        "examples_en": ["District", "District Name", "Select District"],
        "examples_hi": ["जिला", "जनपद"],
        "input_type": "select",
        "options": "DEPENDS_ON_STATE",
    },
    "pincode": {
        "en": "PIN Code",
        "hi": "पिन कोड",
        "examples_en": ["PIN Code", "Pincode", "PIN", "Postal Code", "Zip Code"],
        "examples_hi": ["पिन कोड", "पिनकोड"],
        "input_type": "text",
        "validation": r"^\d{6}$",
    },
    "aadhaar": {
        "en": "Aadhaar Number",
        "hi": "आधार नंबर",
        "examples_en": ["Aadhaar", "Aadhar", "Aadhaar Number", "Aadhaar No."],
        "examples_hi": ["आधार", "आधार नंबर", "आधार संख्या"],
        "input_type": "text",
        "validation": r"^\d{12}$",
        "sensitive": True,
    },
    "category": {
        "en": "Category/Caste",
        "hi": "वर्ग/जाति",
        "examples_en": ["Category", "Caste", "Reservation Category", "Social Category"],
        "examples_hi": ["वर्ग", "जाति", "आरक्षण श्रेणी"],
        "input_type": "select",
        "options": ["General", "OBC", "SC", "ST", "EWS"],
    },
    "qualification": {
        "en": "Educational Qualification",
        "hi": "शैक्षिक योग्यता",
        "examples_en": ["Qualification", "Education", "Educational Qualification", "Highest Qualification"],
        "examples_hi": ["योग्यता", "शिक्षा", "शैक्षिक योग्यता"],
        "input_type": "select",
        "options": "EDUCATION_LEVELS",
    },
    "photo": {
        "en": "Photograph",
        "hi": "फोटो",
        "examples_en": ["Photo", "Photograph", "Upload Photo", "Passport Photo"],
        "examples_hi": ["फोटो", "तस्वीर", "फोटोग्राफ"],
        "input_type": "file",
        "validation": "image/*",
    },
    "signature": {
        "en": "Signature",
        "hi": "हस्ताक्षर",
        "examples_en": ["Signature", "Sign", "Upload Signature"],
        "examples_hi": ["हस्ताक्षर", "दस्तखत", "साइन"],
        "input_type": "file",
        "validation": "image/*",
    },
    "captcha": {
        "en": "CAPTCHA",
        "hi": "कैप्चा",
        "examples_en": ["CAPTCHA", "Security Code", "Verification Code", "Enter CAPTCHA"],
        "examples_hi": ["कैप्चा", "सुरक्षा कोड"],
        "input_type": "text",
        "auto_fill": False,  # Never auto-fill
    },
    "password": {
        "en": "Password",
        "hi": "पासवर्ड",
        "examples_en": ["Password", "Create Password", "Enter Password"],
        "examples_hi": ["पासवर्ड", "कूटशब्द"],
        "input_type": "password",
        "auto_fill": False,  # Requires user input
    },
}

FORM_FIELD_GUIDELINES = {
    "en": """
## Form Field Classification Annotation Guidelines

### Task Overview
Classify form input fields to enable auto-fill functionality. Each field should be tagged with its semantic type.

### Feature Extraction
For each form field, extract these features:
1. **Label text** - The visible label near the input
2. **Input ID/Name** - HTML id and name attributes
3. **Placeholder** - Placeholder text inside the input
4. **Input type** - HTML input type (text, email, tel, date, select, etc.)
5. **Surrounding context** - Text or fields nearby

### Field Types to Label
- name, father_name, mother_name, dob, gender
- email, phone, address, state, district, pincode
- aadhaar, category, qualification
- photo, signature, captcha, password

### Annotation Rules

1. **Exact Match**: If label exactly matches a known type, use that type
2. **Semantic Match**: Use context to determine type (e.g., "Mobile" → phone)
3. **Fuzzy Match**: Handle typos and variations (e.g., "Emial" → email)
4. **Unknown**: Label as "unknown" if field type cannot be determined

### Confidence Scoring
- **High (0.9-1.0)**: Exact label match or very clear context
- **Medium (0.6-0.8)**: Semantic match with good context
- **Low (0.3-0.5)**: Fuzzy match or ambiguous context
- **Skip (<0.3)**: Cannot determine with reasonable confidence

### Tricky Cases
- **Combined fields**: "Name (as per Aadhaar)" → name
- **Repeated fields**: Label each instance with position (name_1, name_2)
- **Conditional fields**: Note the condition (e.g., "if married: spouse_name")
- **Hindi-English mix**: Use bilingual understanding

### Never Auto-fill
- CAPTCHA fields
- Password fields (unless user explicitly opts in)
- OTP fields
- File uploads (require user action)

### Recording Corrections
When an operator manually corrects an auto-fill suggestion:
1. Record the original prediction
2. Record the user's correction
3. Record the form URL and field selector
4. These corrections become training data for model improvement
""",
    "hi": """
## फॉर्म फील्ड वर्गीकरण एनोटेशन दिशानिर्देश

### कार्य अवलोकन
ऑटो-फिल कार्यक्षमता को सक्षम करने के लिए फॉर्म इनपुट फील्ड्स को वर्गीकृत करें।

### फीचर निष्कर्षण
प्रत्येक फॉर्म फील्ड के लिए ये फीचर्स निकालें:
1. **लेबल टेक्स्ट** - इनपुट के पास दिखाई देने वाला लेबल
2. **इनपुट ID/नाम** - HTML id और name एट्रिब्यूट्स
3. **प्लेसहोल्डर** - इनपुट के अंदर प्लेसहोल्डर टेक्स्ट
4. **इनपुट प्रकार** - HTML इनपुट टाइप
5. **आसपास का संदर्भ** - पास के टेक्स्ट या फील्ड्स

### लेबल करने के लिए फील्ड प्रकार
- name, father_name, mother_name, dob, gender
- email, phone, address, state, district, pincode
- aadhaar, category, qualification
""",
}


# =============================================================================
# INTENT CLASSIFICATION GUIDELINES
# =============================================================================

INTENT_LABELS = {
    # Primary intents
    "greeting": {
        "en": "Greeting",
        "hi": "अभिवादन",
        "examples_en": ["Hi", "Hello", "Good morning", "Hey there"],
        "examples_hi": ["नमस्ते", "हेलो", "हाय", "सुप्रभात"],
        "examples_hinglish": ["Hi bhai", "Hello ji", "Namaste"],
    },
    "job_search": {
        "en": "Job Search",
        "hi": "नौकरी खोज",
        "examples_en": ["I want a job", "Show me government jobs", "Railway vacancies"],
        "examples_hi": ["मुझे नौकरी चाहिए", "सरकारी नौकरी दिखाओ", "रेलवे में भर्ती"],
        "examples_hinglish": ["Job chahiye", "Sarkari naukri batao", "Railway bharti hai kya"],
    },
    "scheme_search": {
        "en": "Scheme Search",
        "hi": "योजना खोज",
        "examples_en": ["Tell me about PM Kisan", "Government schemes for farmers", "Student scholarships"],
        "examples_hi": ["पीएम किसान के बारे में बताओ", "किसानों के लिए योजना", "छात्रवृत्ति"],
        "examples_hinglish": ["PM Kisan scheme kya hai", "Farmer ke liye yojana", "Scholarship milegi kya"],
    },
    "apply_job": {
        "en": "Apply for Job",
        "hi": "नौकरी के लिए आवेदन",
        "examples_en": ["Apply for this job", "How to apply", "Start application"],
        "examples_hi": ["इस नौकरी के लिए आवेदन करें", "आवेदन कैसे करें", "फॉर्म भरना है"],
        "examples_hinglish": ["Apply karna hai", "Form kaise bhare", "Application submit karo"],
    },
    "apply_scheme": {
        "en": "Apply for Scheme",
        "hi": "योजना के लिए आवेदन",
        "examples_en": ["Apply for this scheme", "Register for PM Kisan", "How to get benefits"],
        "examples_hi": ["इस योजना के लिए आवेदन", "पीएम किसान में रजिस्टर करें", "लाभ कैसे मिलेगा"],
        "examples_hinglish": ["Scheme me apply karna hai", "Registration kaise hoga"],
    },
    "check_status": {
        "en": "Check Application Status",
        "hi": "आवेदन स्थिति जांचें",
        "examples_en": ["Check my application", "Application status", "Where is my form"],
        "examples_hi": ["मेरा आवेदन चेक करो", "आवेदन की स्थिति", "फॉर्म कहां पहुंचा"],
        "examples_hinglish": ["Application status batao", "Mera form kahan hai"],
    },
    "payment_issue": {
        "en": "Payment Issue",
        "hi": "भुगतान समस्या",
        "examples_en": ["Payment failed", "Money deducted", "Refund request", "Transaction problem"],
        "examples_hi": ["पेमेंट फेल हो गया", "पैसे कट गए", "रिफंड चाहिए"],
        "examples_hinglish": ["Payment nahi hua", "Paise kat gaye", "Refund kab milega"],
    },
    "profile_update": {
        "en": "Update Profile",
        "hi": "प्रोफाइल अपडेट",
        "examples_en": ["Update my details", "Change phone number", "Edit profile"],
        "examples_hi": ["मेरी जानकारी अपडेट करो", "फोन नंबर बदलना है", "प्रोफाइल एडिट करें"],
        "examples_hinglish": ["Profile update karna hai", "Details change karo"],
    },
    "eligibility_check": {
        "en": "Check Eligibility",
        "hi": "पात्रता जांच",
        "examples_en": ["Am I eligible?", "Can I apply?", "What are the requirements?"],
        "examples_hi": ["क्या मैं पात्र हूं?", "क्या मैं आवेदन कर सकता हूं?", "योग्यता क्या है?"],
        "examples_hinglish": ["Kya main eligible hun", "Apply kar sakta hun kya"],
    },
    "document_help": {
        "en": "Document Help",
        "hi": "दस्तावेज़ सहायता",
        "examples_en": ["What documents needed?", "Where to upload photo?", "Certificate format"],
        "examples_hi": ["कौन से दस्तावेज़ चाहिए?", "फोटो कहां अपलोड करें?", "प्रमाणपत्र फॉर्मेट"],
        "examples_hinglish": ["Documents kya chahiye", "Photo kaise upload kare"],
    },
    "deadline_query": {
        "en": "Deadline Query",
        "hi": "अंतिम तिथि पूछताछ",
        "examples_en": ["Last date to apply?", "When is the deadline?", "Form last date"],
        "examples_hi": ["आवेदन की अंतिम तिथि?", "डेडलाइन कब है?", "फॉर्म कब तक भर सकते हैं?"],
        "examples_hinglish": ["Last date kya hai", "Deadline kab tak hai"],
    },
    "human_agent": {
        "en": "Talk to Human",
        "hi": "मानव एजेंट से बात",
        "examples_en": ["Talk to human", "Connect to agent", "I need help from a person"],
        "examples_hi": ["इंसान से बात करनी है", "एजेंट से कनेक्ट करो", "किसी व्यक्ति से मदद चाहिए"],
        "examples_hinglish": ["Human se baat karna hai", "Kisi insaan se connect karo"],
    },
    "feedback": {
        "en": "Feedback/Complaint",
        "hi": "फीडबैक/शिकायत",
        "examples_en": ["I have a complaint", "Want to give feedback", "Service was bad"],
        "examples_hi": ["शिकायत करनी है", "फीडबैक देना है", "सेवा खराब थी"],
        "examples_hinglish": ["Complaint karna hai", "Feedback dena hai"],
    },
    "thanks": {
        "en": "Thanks/Bye",
        "hi": "धन्यवाद/अलविदा",
        "examples_en": ["Thank you", "Thanks", "Bye", "That's all"],
        "examples_hi": ["धन्यवाद", "शुक्रिया", "अलविदा", "बस इतना ही"],
        "examples_hinglish": ["Thank you bhai", "Shukriya", "Bye bye"],
    },
    "unknown": {
        "en": "Unknown/Other",
        "hi": "अज्ञात/अन्य",
        "examples_en": ["Random text", "Unclear intent"],
        "examples_hi": ["असंबंधित टेक्स्ट"],
        "examples_hinglish": [],
    },
}

INTENT_CLASSIFICATION_GUIDELINES = {
    "en": """
## Intent Classification Annotation Guidelines

### Task Overview
Classify user messages from WhatsApp conversations into intent categories.

### Intent Categories
1. **greeting** - Hello, Hi, Namaste
2. **job_search** - Looking for jobs
3. **scheme_search** - Looking for government schemes
4. **apply_job** - Wants to apply for a job
5. **apply_scheme** - Wants to apply for a scheme
6. **check_status** - Checking application status
7. **payment_issue** - Payment problems or refund requests
8. **profile_update** - Wants to update profile/details
9. **eligibility_check** - Asking about eligibility
10. **document_help** - Questions about required documents
11. **deadline_query** - Asking about deadlines/last dates
12. **human_agent** - Wants to talk to a human
13. **feedback** - Complaints or feedback
14. **thanks** - Thank you, goodbye
15. **unknown** - Cannot determine intent

### Handling Mixed Language (Hinglish)
- Many messages will mix Hindi and English
- Focus on the INTENT, not the language
- "Job chahiye" = job_search
- "Apply karna hai railway me" = apply_job

### Multi-Intent Messages
When a message contains multiple intents:
1. Label the PRIMARY intent (what they want most)
2. Note secondary intents in comments
3. Example: "Hi, I want to apply for SSC job" → Primary: apply_job (greeting is secondary)

### Ambiguous Cases
- If genuinely ambiguous, label as "unknown"
- Add a note explaining the ambiguity
- These will be reviewed by a senior annotator

### Context Awareness
- Consider conversation context if provided
- A "yes" might mean "apply_job" if preceded by "Do you want to apply?"
- Label based on the message + context together

### Skip Rules
- Skip if message is empty or just emojis
- Skip if message is in a language other than Hindi/English
- Skip if message contains only PII (flag for review)

### Quality Checks
- 10% of annotations will be reviewed
- Maintain >90% agreement with gold standard
- Discuss disagreements in weekly calibration sessions
""",
    "hi": """
## इंटेंट वर्गीकरण एनोटेशन दिशानिर्देश

### कार्य अवलोकन
व्हाट्सएप वार्तालाप से उपयोगकर्ता संदेशों को इंटेंट श्रेणियों में वर्गीकृत करें।

### इंटेंट श्रेणियां
1. **greeting** - हेलो, हाय, नमस्ते
2. **job_search** - नौकरी खोज रहे हैं
3. **scheme_search** - सरकारी योजनाएं खोज रहे हैं
4. **apply_job** - नौकरी के लिए आवेदन करना चाहते हैं
5. **apply_scheme** - योजना के लिए आवेदन करना चाहते हैं
6. **check_status** - आवेदन की स्थिति जांच रहे हैं
7. **payment_issue** - भुगतान समस्या या रिफंड
8. **profile_update** - प्रोफाइल अपडेट करना चाहते हैं
9. **eligibility_check** - पात्रता के बारे में पूछ रहे हैं
10. **document_help** - दस्तावेजों के बारे में प्रश्न
11. **deadline_query** - डेडलाइन/अंतिम तिथि पूछ रहे हैं
12. **human_agent** - इंसान से बात करना चाहते हैं
13. **feedback** - शिकायत या फीडबैक
14. **thanks** - धन्यवाद, अलविदा
15. **unknown** - इंटेंट निर्धारित नहीं कर सकते
""",
}


# =============================================================================
# CONTENT SUMMARIZATION GUIDELINES
# =============================================================================

SUMMARIZATION_GUIDELINES = {
    "en": """
## Content Summarization Annotation Guidelines

### Task Overview
Create concise summaries of job postings and government scheme announcements in both Hindi and English.

### Summary Requirements

1. **Length**: 50-150 words (adjust based on original content)
2. **Languages**: Create summaries in BOTH Hindi and English
3. **Key Information**: Must include:
   - Job/Scheme name
   - Organization
   - Key eligibility (education, age)
   - Benefits/Salary
   - Important dates
   - How to apply (brief)

### Writing Style

- Use simple, clear language
- Avoid jargon unless necessary
- Write in third person
- Use bullet points for clarity
- DO NOT copy sentences verbatim from source (copyright)

### Summary Template

**English:**
```
[Organization] has announced [Job/Scheme name] for [target group].
- Eligibility: [education], [age range]
- Benefits: [salary/benefits]
- Last Date: [deadline]
- Apply: [brief instruction]
```

**Hindi:**
```
[संगठन] ने [नौकरी/योजना का नाम] की घोषणा की है।
- पात्रता: [शिक्षा], [आयु सीमा]
- लाभ: [वेतन/लाभ]
- अंतिम तिथि: [डेडलाइन]
- आवेदन: [संक्षिप्त निर्देश]
```

### Quality Criteria

- **Accuracy**: All facts must match the source
- **Completeness**: All key information included
- **Clarity**: Easy to understand for rural users
- **Brevity**: No unnecessary words
- **Neutrality**: No opinions or recommendations

### Diversity in Summaries
- If multiple annotators summarize the same content, encourage different phrasings
- This helps train models to generate diverse outputs

### Skip Rules
- Skip if source is incomplete or truncated
- Skip if source is not a job/scheme announcement
- Skip if source is in a language you don't understand well
""",
    "hi": """
## सामग्री सारांश एनोटेशन दिशानिर्देश

### कार्य अवलोकन
नौकरी पोस्टिंग और सरकारी योजना घोषणाओं का हिंदी और अंग्रेजी दोनों में संक्षिप्त सारांश बनाएं।

### सारांश आवश्यकताएं

1. **लंबाई**: 50-150 शब्द
2. **भाषाएं**: हिंदी और अंग्रेजी दोनों में सारांश बनाएं
3. **मुख्य जानकारी**:
   - नौकरी/योजना का नाम
   - संगठन
   - पात्रता (शिक्षा, आयु)
   - लाभ/वेतन
   - महत्वपूर्ण तिथियां
   - आवेदन कैसे करें

### लेखन शैली

- सरल, स्पष्ट भाषा का उपयोग करें
- अनावश्यक शब्दजाल से बचें
- तीसरे व्यक्ति में लिखें
- स्पष्टता के लिए बुलेट पॉइंट्स का उपयोग करें
- स्रोत से वाक्यों की शब्दशः नकल न करें
""",
}


# =============================================================================
# DOCUMENT VALIDATION GUIDELINES
# =============================================================================

DOCUMENT_TYPES = {
    "aadhaar_card": {
        "en": "Aadhaar Card",
        "hi": "आधार कार्ड",
        "required_fields": ["name", "aadhaar_number", "dob", "gender", "address"],
        "format_checks": {
            "aadhaar_number": r"^\d{12}$",
        },
    },
    "pan_card": {
        "en": "PAN Card",
        "hi": "पैन कार्ड",
        "required_fields": ["name", "pan_number", "dob", "father_name"],
        "format_checks": {
            "pan_number": r"^[A-Z]{5}\d{4}[A-Z]$",
        },
    },
    "voter_id": {
        "en": "Voter ID",
        "hi": "मतदाता पहचान पत्र",
        "required_fields": ["name", "voter_id_number", "father_name", "address"],
        "format_checks": {
            "voter_id_number": r"^[A-Z]{3}\d{7}$",
        },
    },
    "driving_license": {
        "en": "Driving License",
        "hi": "ड्राइविंग लाइसेंस",
        "required_fields": ["name", "license_number", "dob", "validity"],
    },
    "passport": {
        "en": "Passport",
        "hi": "पासपोर्ट",
        "required_fields": ["name", "passport_number", "dob", "validity"],
        "format_checks": {
            "passport_number": r"^[A-Z]\d{7}$",
        },
    },
    "marksheet": {
        "en": "Marksheet/Certificate",
        "hi": "अंकपत्र/प्रमाणपत्र",
        "required_fields": ["name", "roll_number", "year", "percentage_or_grade"],
    },
    "caste_certificate": {
        "en": "Caste Certificate",
        "hi": "जाति प्रमाणपत्र",
        "required_fields": ["name", "caste", "issuing_authority", "certificate_number"],
    },
    "income_certificate": {
        "en": "Income Certificate",
        "hi": "आय प्रमाणपत्र",
        "required_fields": ["name", "annual_income", "issuing_authority", "validity"],
    },
    "domicile_certificate": {
        "en": "Domicile Certificate",
        "hi": "मूल निवास प्रमाणपत्र",
        "required_fields": ["name", "state", "issuing_authority"],
    },
    "photo": {
        "en": "Passport Photo",
        "hi": "पासपोर्ट फोटो",
        "required_fields": [],
        "quality_checks": ["face_visible", "proper_background", "recent"],
    },
    "signature": {
        "en": "Signature",
        "hi": "हस्ताक्षर",
        "required_fields": [],
        "quality_checks": ["legible", "proper_background"],
    },
}

DOCUMENT_VALIDATION_LABELS = {
    "validity": {
        "acceptable": {"en": "Acceptable", "hi": "स्वीकार्य"},
        "too_blurry": {"en": "Too Blurry", "hi": "बहुत धुंधला"},
        "expired": {"en": "Expired", "hi": "एक्सपायर्ड"},
        "wrong_document": {"en": "Wrong Document Type", "hi": "गलत दस्तावेज़ प्रकार"},
        "incomplete": {"en": "Incomplete/Cropped", "hi": "अधूरा/क्रॉप किया हुआ"},
        "tampered": {"en": "Possibly Tampered", "hi": "संभवतः छेड़छाड़"},
        "unreadable": {"en": "Unreadable", "hi": "पढ़ने योग्य नहीं"},
    },
    "quality_scores": {
        "excellent": {"score": 1.0, "en": "Excellent", "hi": "उत्कृष्ट"},
        "good": {"score": 0.8, "en": "Good", "hi": "अच्छा"},
        "acceptable": {"score": 0.6, "en": "Acceptable", "hi": "स्वीकार्य"},
        "poor": {"score": 0.4, "en": "Poor", "hi": "खराब"},
        "unacceptable": {"score": 0.0, "en": "Unacceptable", "hi": "अस्वीकार्य"},
    },
}

DOCUMENT_VALIDATION_GUIDELINES = {
    "en": """
## Document Validation Annotation Guidelines

### Task Overview
Validate uploaded documents for quality, authenticity, and data extraction accuracy.

### Validation Steps

1. **Document Type Identification**
   - Identify the document type (Aadhaar, PAN, Marksheet, etc.)
   - Mark as "wrong_document" if it doesn't match expected type

2. **Quality Assessment**
   - **Excellent**: Crystal clear, all text readable
   - **Good**: Clear, minor issues that don't affect readability
   - **Acceptable**: Some blur/issues but key info readable
   - **Poor**: Significant issues, may need reupload
   - **Unacceptable**: Cannot extract required information

3. **Validity Check**
   - Check expiry date if applicable
   - Verify document appears genuine
   - Flag if tampering suspected

4. **Data Extraction Validation**
   - Verify OCR-extracted text matches the document
   - Correct any OCR errors
   - Mark fields that couldn't be extracted

5. **Cross-Validation**
   - Compare extracted data with user profile
   - Flag mismatches (e.g., DOB mismatch)

### Format Validation Rules

| Field | Format | Example |
|-------|--------|---------|
| Aadhaar | 12 digits | 123456789012 |
| PAN | AAAAA0000A | ABCDE1234F |
| Phone | 10 digits starting 6-9 | 9876543210 |
| PIN Code | 6 digits | 110001 |
| Voter ID | 3 letters + 7 digits | ABC1234567 |

### Red Flags
- Document edges appear cut/cropped artificially
- Text appears edited or misaligned
- Photo appears pasted or mismatched
- Holograms/security features missing or damaged
- Multiple documents submitted as one

### Privacy Rules
- DO NOT save copies of documents
- Work only within the annotation interface
- Report any data breaches immediately
""",
    "hi": """
## दस्तावेज़ सत्यापन एनोटेशन दिशानिर्देश

### कार्य अवलोकन
अपलोड किए गए दस्तावेज़ों को गुणवत्ता, प्रामाणिकता और डेटा निष्कर्षण सटीकता के लिए सत्यापित करें।

### सत्यापन चरण

1. **दस्तावेज़ प्रकार पहचान**
   - दस्तावेज़ प्रकार की पहचान करें (आधार, पैन, अंकपत्र, आदि)
   - यदि अपेक्षित प्रकार से मेल नहीं खाता तो "गलत दस्तावेज़" चिह्नित करें

2. **गुणवत्ता मूल्यांकन**
   - उत्कृष्ट: बिल्कुल स्पष्ट, सभी टेक्स्ट पढ़ने योग्य
   - अच्छा: स्पष्ट, मामूली समस्याएं
   - स्वीकार्य: कुछ धुंधलापन लेकिन मुख्य जानकारी पढ़ने योग्य
   - खराब: महत्वपूर्ण समस्याएं, पुनः अपलोड की आवश्यकता
   - अस्वीकार्य: आवश्यक जानकारी नहीं निकाली जा सकती

3. **वैधता जांच**
   - यदि लागू हो तो समाप्ति तिथि जांचें
   - सत्यापित करें कि दस्तावेज़ वास्तविक दिखता है
""",
}


# =============================================================================
# ANNOTATION SCHEMA CLASS
# =============================================================================

@dataclass
class AnnotationSchema:
    """Complete annotation schema for a task"""
    task_type: AnnotationTaskType
    labels: Dict[str, Any]
    guidelines: Dict[str, str]
    examples: List[Dict] = field(default_factory=list)
    skip_rules: List[str] = field(default_factory=list)
    quality_threshold: float = 0.9
    requires_review: bool = True


class AnnotationGuidelinesManager:
    """
    Manages annotation guidelines and schemas for all tasks
    """
    
    def __init__(self):
        self.schemas: Dict[str, AnnotationSchema] = {}
        self._initialize_schemas()
    
    def _initialize_schemas(self):
        """Initialize all annotation schemas"""
        
        # Job/Yojana Matching
        self.schemas["job_yojana_matching"] = AnnotationSchema(
            task_type=AnnotationTaskType.JOB_YOJANA_MATCHING,
            labels=JOB_YOJANA_LABELS,
            guidelines=JOB_MATCHING_GUIDELINES,
            skip_rules=[
                "Truncated text missing key information",
                "Spam or unrelated content",
                "Language other than Hindi/English",
            ],
        )
        
        # Form Field Classification
        self.schemas["form_field_classification"] = AnnotationSchema(
            task_type=AnnotationTaskType.FORM_FIELD_CLASSIFICATION,
            labels=FORM_FIELD_TYPES,
            guidelines=FORM_FIELD_GUIDELINES,
            skip_rules=[
                "Form not loading properly",
                "Dynamic form requiring login",
                "CAPTCHA-only forms",
            ],
        )
        
        # Intent Classification
        self.schemas["intent_classification"] = AnnotationSchema(
            task_type=AnnotationTaskType.INTENT_CLASSIFICATION,
            labels=INTENT_LABELS,
            guidelines=INTENT_CLASSIFICATION_GUIDELINES,
            skip_rules=[
                "Empty or emoji-only messages",
                "Languages other than Hindi/English",
                "Messages containing only PII",
            ],
        )
        
        # Content Summarization
        self.schemas["content_summarization"] = AnnotationSchema(
            task_type=AnnotationTaskType.CONTENT_SUMMARIZATION,
            labels={},  # No fixed labels for summarization
            guidelines=SUMMARIZATION_GUIDELINES,
            skip_rules=[
                "Incomplete source content",
                "Not a job/scheme announcement",
                "Source in unknown language",
            ],
        )
        
        # Document Validation
        self.schemas["document_validation"] = AnnotationSchema(
            task_type=AnnotationTaskType.DOCUMENT_VALIDATION,
            labels={
                "document_types": DOCUMENT_TYPES,
                "validity_labels": DOCUMENT_VALIDATION_LABELS,
            },
            guidelines=DOCUMENT_VALIDATION_GUIDELINES,
            skip_rules=[
                "File corrupt or won't open",
                "Multiple documents in one image",
                "Document in foreign language",
            ],
        )
    
    def get_schema(self, task_type: str) -> Optional[AnnotationSchema]:
        """Get annotation schema for a task type"""
        return self.schemas.get(task_type)
    
    def get_guidelines(self, task_type: str, language: str = "en") -> str:
        """Get guidelines text for a task"""
        schema = self.schemas.get(task_type)
        if schema:
            return schema.guidelines.get(language, schema.guidelines.get("en", ""))
        return ""
    
    def get_labels(self, task_type: str) -> Dict:
        """Get label definitions for a task"""
        schema = self.schemas.get(task_type)
        return schema.labels if schema else {}
    
    def export_guidelines(self, output_dir: str = None) -> Dict[str, str]:
        """Export all guidelines to files"""
        if output_dir is None:
            output_dir = Path(__file__).parent / "guidelines"
        else:
            output_dir = Path(output_dir)
        
        output_dir.mkdir(parents=True, exist_ok=True)
        paths = {}
        
        for task_name, schema in self.schemas.items():
            # Export English guidelines
            en_path = output_dir / f"{task_name}_guidelines_en.md"
            with open(en_path, 'w', encoding='utf-8') as f:
                f.write(f"# {task_name.replace('_', ' ').title()} Annotation Guidelines\n\n")
                f.write(f"Generated: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write(schema.guidelines.get("en", ""))
                f.write("\n\n## Skip Rules\n")
                for rule in schema.skip_rules:
                    f.write(f"- {rule}\n")
            paths[f"{task_name}_en"] = str(en_path)
            
            # Export Hindi guidelines
            hi_path = output_dir / f"{task_name}_guidelines_hi.md"
            with open(hi_path, 'w', encoding='utf-8') as f:
                f.write(f"# {task_name.replace('_', ' ').title()} एनोटेशन दिशानिर्देश\n\n")
                f.write(f"तिथि: {datetime.now().strftime('%Y-%m-%d')}\n\n")
                f.write(schema.guidelines.get("hi", ""))
            paths[f"{task_name}_hi"] = str(hi_path)
            
            # Export labels as JSON
            labels_path = output_dir / f"{task_name}_labels.json"
            with open(labels_path, 'w', encoding='utf-8') as f:
                json.dump(schema.labels, f, ensure_ascii=False, indent=2)
            paths[f"{task_name}_labels"] = str(labels_path)
        
        # Export privacy guidelines
        privacy_path = output_dir / "privacy_guidelines.md"
        with open(privacy_path, 'w', encoding='utf-8') as f:
            f.write(PRIVACY_GUIDELINES["en"])
            f.write("\n\n---\n\n")
            f.write(PRIVACY_GUIDELINES["hi"])
        paths["privacy"] = str(privacy_path)
        
        logger.info(f"Exported guidelines to {output_dir}")
        return paths
    
    def get_all_task_types(self) -> List[str]:
        """Get list of all task types"""
        return list(self.schemas.keys())
    
    def validate_annotation(
        self,
        task_type: str,
        annotation: Dict
    ) -> Dict[str, Any]:
        """
        Validate an annotation against the schema
        
        Returns validation result with any errors
        """
        schema = self.schemas.get(task_type)
        if not schema:
            return {"valid": False, "errors": ["Unknown task type"]}
        
        errors = []
        warnings = []
        
        # Task-specific validation
        if task_type == "intent_classification":
            intent = annotation.get("intent")
            if intent not in INTENT_LABELS:
                errors.append(f"Unknown intent: {intent}")
            
            confidence = annotation.get("confidence", 0)
            if confidence < 0.3:
                warnings.append("Low confidence annotation")
        
        elif task_type == "form_field_classification":
            field_type = annotation.get("field_type")
            if field_type not in FORM_FIELD_TYPES and field_type != "unknown":
                errors.append(f"Unknown field type: {field_type}")
        
        elif task_type == "document_validation":
            validity = annotation.get("validity")
            if validity not in DOCUMENT_VALIDATION_LABELS["validity"]:
                errors.append(f"Unknown validity status: {validity}")
        
        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }


# Singleton instance
_guidelines_manager = None

def get_guidelines_manager() -> AnnotationGuidelinesManager:
    """Get singleton instance of guidelines manager"""
    global _guidelines_manager
    if _guidelines_manager is None:
        _guidelines_manager = AnnotationGuidelinesManager()
    return _guidelines_manager
