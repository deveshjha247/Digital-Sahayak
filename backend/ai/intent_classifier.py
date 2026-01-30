"""
WhatsApp Intent Classifier AI Module
Analyzes WhatsApp messages to understand user intent
Uses keyword matching + context analysis (no external AI dependency)

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- Auto-detects: Hinglish (romanized Hindi)
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple

from .language_helper import get_language_helper, detect_language

logger = logging.getLogger(__name__)

# Initialize language helper
lang_helper = get_language_helper()


class IntentType(Enum):
    """Intent types supported by the classifier"""
    
    # Job-related intents
    JOB_SEARCH = "job_search"
    JOB_DETAILS = "job_details"
    JOB_APPLY = "job_apply"
    JOB_STATUS = "job_status"
    
    # Scheme-related intents
    SCHEME_SEARCH = "scheme_search"
    SCHEME_DETAILS = "scheme_details"
    SCHEME_APPLY = "scheme_apply"
    SCHEME_ELIGIBILITY = "scheme_eligibility"
    
    # User actions
    REGISTER = "register"
    LOGIN = "login"
    PROFILE_UPDATE = "profile_update"
    HELP = "help"
    
    # Document/form intents
    UPLOAD_DOCUMENT = "upload_document"
    FILL_FORM = "fill_form"
    CHECK_STATUS = "check_status"
    
    # General intents
    GREETING = "greeting"
    FEEDBACK = "feedback"
    COMPLAINT = "complaint"
    UNCLEAR = "unclear"


class IntentClassifier:
    """
    Classifies WhatsApp messages to determine user intent
    
    Approach:
    1. Extract keywords from message
    2. Match against intent patterns
    3. Calculate confidence based on keyword strength
    4. Return top intent with confidence score
    """
    
    # Intent patterns - maps keywords to intents
    INTENT_PATTERNS = {
        IntentType.JOB_SEARCH: {
            "keywords": ["job", "naukri", "काम", "नौकरी", "खोज", "find job", "search job", "available", "latest", "new job"],
            "phrases": ["jobs in", "job for", "any job", "jobs available", "नौकरी खोज"],
            "weight": 1.0,
        },
        IntentType.JOB_DETAILS: {
            "keywords": ["details", "info", "information", "description", "विवरण", "जानकारी", "about job", "tell me", "more about"],
            "phrases": ["job details", "job information", "what about", "tell me about", "जॉब के बारे में"],
            "weight": 0.9,
        },
        IntentType.JOB_APPLY: {
            "keywords": ["apply", "apply now", "application", "आवेदन", "अभी आवेदन", "submit", "register", "enroll"],
            "phrases": ["how to apply", "apply for", "let me apply", "start application", "आवेदन कैसे करें"],
            "weight": 1.0,
        },
        IntentType.JOB_STATUS: {
            "keywords": ["status", "update", "result", "selected", "rejected", "स्थिति", "परिणाम", "चयन", "rejected"],
            "phrases": ["application status", "job status", "check status", "my status", "चयन परिणाम"],
            "weight": 1.0,
        },
        IntentType.SCHEME_SEARCH: {
            "keywords": ["scheme", "yojana", "योजना", "benefits", "सुविधा", "benefit", "program", "assistance"],
            "phrases": ["schemes for", "any scheme", "available scheme", "योजना खोज", "कौन सी योजना"],
            "weight": 1.0,
        },
        IntentType.SCHEME_DETAILS: {
            "keywords": ["scheme", "yojana", "योजना", "details", "information", "eligibility", "पात्रता"],
            "phrases": ["scheme details", "tell me about scheme", "योजना की जानकारी"],
            "weight": 0.9,
        },
        IntentType.SCHEME_APPLY: {
            "keywords": ["apply", "scheme", "yojana", "आवेदन", "register", "enroll"],
            "phrases": ["apply for scheme", "scheme application", "योजना के लिए आवेदन"],
            "weight": 1.0,
        },
        IntentType.SCHEME_ELIGIBILITY: {
            "keywords": ["eligible", "qualification", "eligible", "पात्र", "योग्यता", "requirement"],
            "phrases": ["am i eligible", "who can apply", "requirements", "मैं पात्र हूं", "कौन आवेदन कर सकता है"],
            "weight": 1.0,
        },
        IntentType.REGISTER: {
            "keywords": ["register", "signup", "account", "create", "new user", "पंजीकरण", "खाता", "नया खाता"],
            "phrases": ["create account", "new account", "sign up", "खाता बनाएं", "नया खाता बनाएं"],
            "weight": 1.0,
        },
        IntentType.LOGIN: {
            "keywords": ["login", "sign in", "password", "username", "लॉगिन", "प्रवेश", "खाता"],
            "phrases": ["cant login", "login issue", "forgot password", "लॉगिन नहीं हो रहा"],
            "weight": 1.0,
        },
        IntentType.PROFILE_UPDATE: {
            "keywords": ["update", "profile", "edit", "change", "modify", "प्रोफाइल", "संपादित", "बदलें"],
            "phrases": ["update profile", "edit profile", "change profile", "प्रोफाइल अपडेट", "प्रोफाइल बदलें"],
            "weight": 1.0,
        },
        IntentType.UPLOAD_DOCUMENT: {
            "keywords": ["upload", "document", "file", "certificate", "aadhar", "pan", "दस्तावेज", "अपलोड", "आधार", "पैन"],
            "phrases": ["upload document", "submit document", "दस्तावेज अपलोड करें"],
            "weight": 1.0,
        },
        IntentType.FILL_FORM: {
            "keywords": ["form", "fill", "फॉर्म", "भरें", "details", "information"],
            "phrases": ["fill form", "complete form", "form details", "फॉर्म भरें"],
            "weight": 0.9,
        },
        IntentType.CHECK_STATUS: {
            "keywords": ["check", "status", "result", "progress", "स्थिति", "जांच", "प्रगति"],
            "phrases": ["check status", "track status", "see progress", "स्थिति जांचें"],
            "weight": 1.0,
        },
        IntentType.HELP: {
            "keywords": ["help", "support", "issue", "problem", "मदद", "समस्या", "सहायता", "परेशानी"],
            "phrases": ["need help", "can you help", "what to do", "मुझे मदद चाहिए", "समस्या है"],
            "weight": 1.0,
        },
        IntentType.GREETING: {
            "keywords": ["hi", "hello", "hey", "नमस्ते", "हेलो", "सुप्रभात"],
            "phrases": ["hello there", "how are you", "नमस्ते कैसे हो"],
            "weight": 0.8,
        },
        IntentType.FEEDBACK: {
            "keywords": ["feedback", "review", "rating", "like", "dislike", "प्रतिक्रिया", "समीक्षा", "रेटिंग"],
            "phrases": ["give feedback", "review app", "my feedback", "प्रतिक्रिया दें"],
            "weight": 0.9,
        },
        IntentType.COMPLAINT: {
            "keywords": ["complaint", "issue", "bug", "problem", "error", "शिकायत", "समस्या", "त्रुटि"],
            "phrases": ["file complaint", "report issue", "something is wrong", "शिकायत दर्ज करें"],
            "weight": 1.0,
        },
    }
    
    def __init__(self):
        self.min_confidence = 0.5  # Minimum confidence threshold
    
    def preprocess_message(self, message: str) -> str:
        """Preprocess message for analysis"""
        if not message:
            return ""
        
        # Convert to lowercase
        text = message.lower()
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove common punctuation but keep hyphens and apostrophes
        text = re.sub(r'[?!,;:\.\*\-\_\(\)\[\]{}]', ' ', text)
        
        return text
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extract keywords from message"""
        if not text:
            return []
        
        # Split into words
        words = text.split()
        
        # Filter short words (less than 2 characters)
        keywords = [w for w in words if len(w) >= 2]
        
        return keywords
    
    def calculate_intent_score(self, message: str, intent: IntentType) -> float:
        """Calculate score for a specific intent"""
        text = self.preprocess_message(message)
        keywords = self.extract_keywords(text)
        
        if not keywords:
            return 0.0
        
        pattern = self.INTENT_PATTERNS.get(intent, {})
        base_weight = pattern.get("weight", 0.5)
        
        score = 0.0
        
        # Check for phrase matches (highest priority)
        phrases = pattern.get("phrases", [])
        phrase_match = 0
        for phrase in phrases:
            if phrase.lower() in text:
                phrase_match += 1
        
        if phrase_match > 0:
            score += phrase_match * base_weight * 0.4  # 40% from phrase match
        
        # Check keyword matches
        pattern_keywords = pattern.get("keywords", [])
        keyword_matches = sum(1 for kw in keywords if kw in pattern_keywords)
        
        if keyword_matches > 0:
            keyword_score = min(keyword_matches / len(pattern_keywords), 1.0) * 0.6 * base_weight
            score += keyword_score
        
        # Normalize to 0-1
        return min(score, 1.0)
    
    def classify(self, message: str) -> Tuple[IntentType, float, Dict]:
        """
        Classify message intent
        
        Returns:
            (top_intent, confidence_score, details_dict)
        """
        if not message or not message.strip():
            return IntentType.UNCLEAR, 0.0, {"error": "Empty message"}
        
        # Calculate scores for all intents
        scores = {}
        for intent in IntentType:
            score = self.calculate_intent_score(message, intent)
            scores[intent] = score
        
        # Get top intent
        top_intent = max(scores, key=scores.get)
        top_score = scores[top_intent]
        
        # If confidence too low, mark as unclear
        if top_score < self.min_confidence:
            top_intent = IntentType.UNCLEAR
            top_score = top_score / self.min_confidence  # Adjusted score
        
        # Get runner-ups for context
        sorted_intents = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        runner_ups = [(intent.value, score) for intent, score in sorted_intents[1:4] if score > 0]
        
        details = {
            "original_message": message,
            "top_intent": top_intent.value,
            "confidence": round(top_score, 3),
            "runner_ups": runner_ups,
            "all_scores": {intent.value: round(score, 3) for intent, score in sorted_intents},
        }
        
        return top_intent, top_score, details
    
    def classify_batch(self, messages: List[str]) -> List[Tuple[IntentType, float, Dict]]:
        """Classify multiple messages"""
        return [self.classify(msg) for msg in messages]
    
    def get_suggested_response(self, intent: IntentType) -> str:
        """Get suggested response based on intent"""
        responses = {
            IntentType.JOB_SEARCH: "I can help you find jobs. What type of job are you looking for? Share your location, qualification, and preferred category.",
            IntentType.JOB_DETAILS: "Here are the details of the job. Do you want to apply or need more information?",
            IntentType.JOB_APPLY: "Great! I'll help you apply. Please fill in your details.",
            IntentType.JOB_STATUS: "Let me check your application status. Please provide your application ID.",
            IntentType.SCHEME_SEARCH: "Which scheme are you interested in? I can help you find relevant schemes based on your profile.",
            IntentType.SCHEME_DETAILS: "Here's the information about the scheme. Do you want to apply?",
            IntentType.SCHEME_APPLY: "I'll help you apply for the scheme. Let's start with your basic information.",
            IntentType.SCHEME_ELIGIBILITY: "Let me check your eligibility. I'll need to verify your details.",
            IntentType.REGISTER: "Welcome! Let's create your account. Please provide your basic details.",
            IntentType.LOGIN: "Let me help you login. What's the issue you're facing?",
            IntentType.PROFILE_UPDATE: "I can help you update your profile. What would you like to change?",
            IntentType.HELP: "I'm here to help! What do you need assistance with?",
            IntentType.GREETING: "Hello! Welcome to Digital Sahayak. How can I help you today?",
            IntentType.FEEDBACK: "We'd love to hear your feedback! What do you think about our service?",
            IntentType.COMPLAINT: "I'm sorry to hear you're facing an issue. Please describe the problem in detail.",
            IntentType.UPLOAD_DOCUMENT: "Sure, I can help you upload documents. Which document would you like to upload?",
            IntentType.FILL_FORM: "Let's fill the form together. I'll guide you through each field.",
            IntentType.CHECK_STATUS: "Let me check your status. Please provide your reference number.",
            IntentType.UNCLEAR: "I'm not sure I understood correctly. Could you please rephrase your question?",
        }
        
        return responses.get(intent, "How can I assist you?")
    
    def extract_entities(self, message: str) -> Dict:
        """Extract entities from message (location, job type, etc.)"""
        text = message.lower()
        entities = {}
        
        # Extract location (simplified)
        location_keywords = ["delhi", "mumbai", "bangalore", "hyderabad", "pune", "दिल्ली", "मुंबई", "बेंगलुरु"]
        for loc in location_keywords:
            if loc in text:
                entities["location"] = loc
                break
        
        # Extract job type keywords
        job_keywords = ["engineer", "developer", "teacher", "nurse", "driver", "इंजीनियर", "शिक्षक"]
        for job in job_keywords:
            if job in text:
                entities["job_type"] = job
                break
        
        return entities
