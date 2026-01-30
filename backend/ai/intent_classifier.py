"""
WhatsApp Intent Classifier AI Module
Analyzes WhatsApp messages to understand user intent

Architecture (DistilBERT + Rule Hybrid):
1. DistilBERT: 40% smaller, 60% faster than BERT, 97% capability retention
2. Bag-of-Words Fallback: For speed and low resource usage
3. Keyword Matching: Bilingual pattern matching for reliability

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- Auto-detects: Hinglish (romanized Hindi)

Dependencies (optional for ML mode):
- transformers (for DistilBERT)
- torch (for model inference)
"""

import logging
import re
import os
import json
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .language_helper import get_language_helper, detect_lang

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
    All keywords and responses are pre-defined in language_config.json
    
    Approach:
    1. Load pre-defined keywords from config
    2. Match against intent patterns (bilingual)
    3. Calculate confidence based on keyword strength
    4. Return top intent with confidence score
    """
    
    # Pre-defined Intent patterns - All keywords in both English and Hindi
    INTENT_PATTERNS = {
        IntentType.JOB_SEARCH: {
            "keywords_en": ["job", "jobs", "vacancy", "vacancies", "opening", "recruitment", "hiring", "career", "employment", "work", "position", "latest job", "new job", "find job", "search job", "available"],
            "keywords_hi": ["नौकरी", "भर्ती", "रिक्ति", "काम", "पद", "रोजगार", "नौकरी खोज", "नई नौकरी"],
            "keywords_hinglish": ["naukri", "job chahiye", "koi job", "vacancy hai", "bharti"],
            "phrases_en": ["jobs in", "job for", "any job", "jobs available", "looking for job"],
            "phrases_hi": ["नौकरी खोज", "नौकरी चाहिए", "कोई नौकरी", "नौकरी मिलेगी"],
            "weight": 1.0,
        },
        IntentType.JOB_DETAILS: {
            "keywords_en": ["details", "info", "information", "description", "about job", "tell me", "more about", "salary", "eligibility", "age limit", "syllabus", "qualification"],
            "keywords_hi": ["विवरण", "जानकारी", "जॉब के बारे में", "वेतन", "योग्यता", "पात्रता", "आयु सीमा", "सिलेबस"],
            "keywords_hinglish": ["details batao", "kya hai", "salary kitni", "qualification kya"],
            "phrases_en": ["job details", "job information", "what about", "tell me about"],
            "phrases_hi": ["नौकरी की जानकारी", "इसके बारे में बताओ"],
            "weight": 0.9,
        },
        IntentType.JOB_APPLY: {
            "keywords_en": ["apply", "apply now", "application", "submit", "register", "enroll", "form fill", "how to apply"],
            "keywords_hi": ["आवेदन", "अभी आवेदन", "फॉर्म भरें", "आवेदन कैसे करें", "अप्लाई"],
            "keywords_hinglish": ["apply karna hai", "apply kaise kare", "form bharna hai", "apply karo"],
            "phrases_en": ["how to apply", "apply for", "let me apply", "start application", "submit application"],
            "phrases_hi": ["आवेदन कैसे करें", "आवेदन करना है", "फॉर्म भरना है"],
            "weight": 1.0,
        },
        IntentType.JOB_STATUS: {
            "keywords_en": ["status", "update", "result", "selected", "rejected", "progress", "track", "check result"],
            "keywords_hi": ["स्थिति", "परिणाम", "चयन", "रिजल्ट", "अपडेट", "कहाँ तक पहुंचा"],
            "keywords_hinglish": ["status kya hai", "result aaya", "select hua", "kya hua"],
            "phrases_en": ["application status", "job status", "check status", "my status", "result check"],
            "phrases_hi": ["आवेदन की स्थिति", "चयन परिणाम", "मेरा स्टेटस"],
            "weight": 1.0,
        },
        IntentType.SCHEME_SEARCH: {
            "keywords_en": ["scheme", "yojana", "benefits", "benefit", "program", "assistance", "welfare", "subsidy", "government scheme"],
            "keywords_hi": ["योजना", "स्कीम", "लाभ", "सुविधा", "सब्सिडी", "सहायता", "सरकारी योजना"],
            "keywords_hinglish": ["yojana batao", "scheme chahiye", "koi scheme", "benefit milega"],
            "phrases_en": ["schemes for", "any scheme", "available scheme", "which scheme"],
            "phrases_hi": ["योजना खोज", "कौन सी योजना", "योजना बताओ"],
            "weight": 1.0,
        },
        IntentType.SCHEME_DETAILS: {
            "keywords_en": ["scheme details", "scheme info", "about scheme", "scheme eligibility"],
            "keywords_hi": ["योजना विवरण", "योजना जानकारी", "योजना पात्रता"],
            "keywords_hinglish": ["scheme ke baare me", "yojana ki jaankari"],
            "phrases_en": ["scheme details", "tell me about scheme", "scheme information"],
            "phrases_hi": ["योजना की जानकारी", "योजना के बारे में बताओ"],
            "weight": 0.9,
        },
        IntentType.SCHEME_APPLY: {
            "keywords_en": ["apply scheme", "scheme application", "register scheme", "enroll scheme", "benefit apply"],
            "keywords_hi": ["योजना आवेदन", "योजना के लिए आवेदन", "लाभ लेना"],
            "keywords_hinglish": ["scheme apply karna", "yojana ke liye apply"],
            "phrases_en": ["apply for scheme", "scheme application", "register for scheme"],
            "phrases_hi": ["योजना के लिए आवेदन करें", "योजना में आवेदन"],
            "weight": 1.0,
        },
        IntentType.SCHEME_ELIGIBILITY: {
            "keywords_en": ["eligible", "eligibility", "qualify", "requirement", "criteria", "can i apply", "am i eligible"],
            "keywords_hi": ["पात्र", "पात्रता", "योग्य", "शर्त", "मैं पात्र हूं", "क्या मैं आवेदन कर सकता"],
            "keywords_hinglish": ["eligible hu", "apply kar sakta", "mujhe milega"],
            "phrases_en": ["am i eligible", "who can apply", "requirements", "check eligibility"],
            "phrases_hi": ["मैं पात्र हूं", "कौन आवेदन कर सकता है", "पात्रता जांचें"],
            "weight": 1.0,
        },
        IntentType.REGISTER: {
            "keywords_en": ["register", "signup", "sign up", "account", "create", "new user", "create account"],
            "keywords_hi": ["पंजीकरण", "खाता", "नया खाता", "खाता बनाएं", "रजिस्टर"],
            "keywords_hinglish": ["register karna", "account banana", "signup karo"],
            "phrases_en": ["create account", "new account", "sign up", "register now"],
            "phrases_hi": ["खाता बनाएं", "नया खाता बनाएं", "रजिस्टर करें"],
            "weight": 1.0,
        },
        IntentType.LOGIN: {
            "keywords_en": ["login", "log in", "sign in", "password", "username", "forgot password", "cant login"],
            "keywords_hi": ["लॉगिन", "प्रवेश", "पासवर्ड भूल गया"],
            "keywords_hinglish": ["login karo", "login nahi ho raha", "password bhul gaya"],
            "phrases_en": ["cant login", "login issue", "forgot password", "login problem"],
            "phrases_hi": ["लॉगिन नहीं हो रहा", "पासवर्ड याद नहीं"],
            "weight": 1.0,
        },
        IntentType.PROFILE_UPDATE: {
            "keywords_en": ["update", "profile", "edit", "change", "modify", "update profile", "edit profile"],
            "keywords_hi": ["प्रोफाइल", "संपादित", "बदलें", "अपडेट", "प्रोफाइल अपडेट"],
            "keywords_hinglish": ["profile update karo", "profile change karna", "edit karo"],
            "phrases_en": ["update profile", "edit profile", "change profile", "modify profile"],
            "phrases_hi": ["प्रोफाइल अपडेट करें", "प्रोफाइल बदलें", "प्रोफाइल संपादित करें"],
            "weight": 1.0,
        },
        IntentType.UPLOAD_DOCUMENT: {
            "keywords_en": ["upload", "document", "file", "certificate", "aadhar", "pan", "photo", "signature", "submit document"],
            "keywords_hi": ["अपलोड", "दस्तावेज", "फाइल", "प्रमाणपत्र", "आधार", "पैन", "फोटो", "हस्ताक्षर"],
            "keywords_hinglish": ["document upload karo", "aadhar dena hai", "photo lagana hai"],
            "phrases_en": ["upload document", "submit document", "attach file"],
            "phrases_hi": ["दस्तावेज अपलोड करें", "फाइल जमा करें"],
            "weight": 1.0,
        },
        IntentType.FILL_FORM: {
            "keywords_en": ["form", "fill", "complete", "details", "information", "fill form", "form fill"],
            "keywords_hi": ["फॉर्म", "भरें", "विवरण", "जानकारी भरें"],
            "keywords_hinglish": ["form bharna hai", "form fill karo", "details bharo"],
            "phrases_en": ["fill form", "complete form", "form details", "fill out form"],
            "phrases_hi": ["फॉर्म भरें", "फॉर्म पूरा करें"],
            "weight": 0.9,
        },
        IntentType.CHECK_STATUS: {
            "keywords_en": ["check", "status", "result", "progress", "track", "where", "update"],
            "keywords_hi": ["स्थिति", "जांच", "प्रगति", "कहां तक", "देखना"],
            "keywords_hinglish": ["status check karo", "kahan tak hua", "kya hua"],
            "phrases_en": ["check status", "track status", "see progress", "check progress"],
            "phrases_hi": ["स्थिति जांचें", "प्रगति देखें"],
            "weight": 1.0,
        },
        IntentType.HELP: {
            "keywords_en": ["help", "support", "issue", "problem", "assist", "confused", "how to", "what is", "guide"],
            "keywords_hi": ["मदद", "समस्या", "सहायता", "परेशानी", "कैसे", "क्या है", "समझ नहीं"],
            "keywords_hinglish": ["help chahiye", "problem hai", "kaise kare", "samajh nahi aaya"],
            "phrases_en": ["need help", "can you help", "what to do", "how do i", "guide me"],
            "phrases_hi": ["मुझे मदद चाहिए", "समस्या है", "क्या करूं"],
            "weight": 1.0,
        },
        IntentType.GREETING: {
            "keywords_en": ["hi", "hello", "hey", "good morning", "good evening", "good afternoon", "good night"],
            "keywords_hi": ["नमस्ते", "हेलो", "सुप्रभात", "शुभ संध्या", "शुभ रात्रि"],
            "keywords_hinglish": ["namaste", "namaskar"],
            "phrases_en": ["hello there", "how are you", "hi there"],
            "phrases_hi": ["नमस्ते कैसे हो", "कैसे हैं आप"],
            "weight": 0.8,
        },
        IntentType.FEEDBACK: {
            "keywords_en": ["feedback", "review", "rating", "like", "dislike", "good", "bad", "suggestion"],
            "keywords_hi": ["प्रतिक्रिया", "समीक्षा", "रेटिंग", "पसंद", "नापसंद", "सुझाव"],
            "keywords_hinglish": ["feedback dena hai", "review dena", "accha laga"],
            "phrases_en": ["give feedback", "review app", "my feedback", "want to review"],
            "phrases_hi": ["प्रतिक्रिया दें", "मेरी राय"],
            "weight": 0.9,
        },
        IntentType.COMPLAINT: {
            "keywords_en": ["complaint", "issue", "bug", "problem", "error", "not working", "wrong", "failed"],
            "keywords_hi": ["शिकायत", "समस्या", "त्रुटि", "गलत", "काम नहीं कर रहा", "खराब"],
            "keywords_hinglish": ["complaint karna hai", "problem hai", "kaam nahi kar raha", "galat hai"],
            "phrases_en": ["file complaint", "report issue", "something is wrong", "not working"],
            "phrases_hi": ["शिकायत दर्ज करें", "समस्या बताएं", "कुछ गलत है"],
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
    
    def _get_all_keywords(self, pattern: Dict) -> List[str]:
        """Get all keywords from pattern (en + hi + hinglish)"""
        all_keywords = []
        all_keywords.extend(pattern.get("keywords_en", []))
        all_keywords.extend(pattern.get("keywords_hi", []))
        all_keywords.extend(pattern.get("keywords_hinglish", []))
        return [kw.lower() for kw in all_keywords]
    
    def _get_all_phrases(self, pattern: Dict) -> List[str]:
        """Get all phrases from pattern (en + hi)"""
        all_phrases = []
        all_phrases.extend(pattern.get("phrases_en", []))
        all_phrases.extend(pattern.get("phrases_hi", []))
        return [p.lower() for p in all_phrases]
    
    def calculate_intent_score(self, message: str, intent: IntentType) -> float:
        """Calculate score for a specific intent using pre-defined bilingual keywords"""
        text = self.preprocess_message(message)
        keywords = self.extract_keywords(text)
        
        if not keywords:
            return 0.0
        
        pattern = self.INTENT_PATTERNS.get(intent, {})
        base_weight = pattern.get("weight", 0.5)
        
        score = 0.0
        
        # Check for phrase matches (highest priority) - bilingual
        all_phrases = self._get_all_phrases(pattern)
        phrase_match = 0
        for phrase in all_phrases:
            if phrase in text:
                phrase_match += 1
                score += 0.3  # High weight for phrase match
        
        # Check keyword matches - bilingual (en + hi + hinglish)
        all_pattern_keywords = self._get_all_keywords(pattern)
        keyword_matches = 0
        
        # Check each keyword in text (not just words)
        for pattern_kw in all_pattern_keywords:
            if pattern_kw in text:
                keyword_matches += 1
        
        # Also check word-by-word match
        for kw in keywords:
            if kw in all_pattern_keywords:
                keyword_matches += 1
        
        if keyword_matches > 0:
            # Scale score based on matches
            keyword_score = min(keyword_matches * 0.15, 0.7) * base_weight
            score += keyword_score
        
        # Normalize to 0-1
        return min(score, 1.0)
    
    def classify(self, message: str) -> Tuple[IntentType, float, Dict]:
        """
        Classify message intent (supports English, Hindi, Hinglish)
        
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
        
        # Lower threshold for intent detection
        if top_score < 0.2:
            top_intent = IntentType.UNCLEAR
            top_score = top_score / 0.2  # Adjusted score
        
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
    
    def get_suggested_response(self, intent: IntentType, lang: str = "en") -> Dict[str, str]:
        """
        Get suggested response based on intent in both languages
        
        Args:
            intent: The detected intent
            lang: Preferred language ('en' or 'hi')
        
        Returns:
            Dictionary with 'en', 'hi', and 'bilingual' keys
        """
        responses = {
            IntentType.JOB_SEARCH: {
                "en": "I can help you find jobs. What type of job are you looking for? Share your location, qualification, and preferred category.",
                "hi": "मैं आपको नौकरी खोजने में मदद कर सकता हूं। आप किस प्रकार की नौकरी खोज रहे हैं? अपना स्थान, योग्यता और पसंदीदा श्रेणी बताएं।"
            },
            IntentType.JOB_DETAILS: {
                "en": "Here are the details of the job. Do you want to apply or need more information?",
                "hi": "यहां नौकरी का विवरण है। क्या आप आवेदन करना चाहते हैं या और जानकारी चाहिए?"
            },
            IntentType.JOB_APPLY: {
                "en": "Great! I'll help you apply. Please fill in your details.",
                "hi": "बहुत अच्छा! मैं आपको आवेदन करने में मदद करूंगा। कृपया अपना विवरण भरें।"
            },
            IntentType.JOB_STATUS: {
                "en": "Let me check your application status. Please provide your application ID.",
                "hi": "मैं आपके आवेदन की स्थिति जांचता हूं। कृपया अपना आवेदन आईडी दें।"
            },
            IntentType.SCHEME_SEARCH: {
                "en": "Which scheme are you interested in? I can help you find relevant schemes based on your profile.",
                "hi": "आप किस योजना में रुचि रखते हैं? मैं आपकी प्रोफाइल के आधार पर उचित योजनाएं खोज सकता हूं।"
            },
            IntentType.SCHEME_DETAILS: {
                "en": "Here's the information about the scheme. Do you want to apply?",
                "hi": "यहां योजना की जानकारी है। क्या आप आवेदन करना चाहते हैं?"
            },
            IntentType.SCHEME_APPLY: {
                "en": "I'll help you apply for the scheme. Let's start with your basic information.",
                "hi": "मैं योजना के लिए आवेदन करने में मदद करूंगा। अपनी बुनियादी जानकारी से शुरू करें।"
            },
            IntentType.SCHEME_ELIGIBILITY: {
                "en": "Let me check your eligibility. I'll need to verify your details.",
                "hi": "मैं आपकी पात्रता जांचता हूं। मुझे आपके विवरण की पुष्टि करनी होगी।"
            },
            IntentType.REGISTER: {
                "en": "Welcome! Let's create your account. Please provide your basic details.",
                "hi": "स्वागत है! आइए आपका खाता बनाएं। कृपया अपना बुनियादी विवरण दें।"
            },
            IntentType.LOGIN: {
                "en": "Let me help you login. What's the issue you're facing?",
                "hi": "मैं आपको लॉगिन करने में मदद करता हूं। आपको क्या समस्या है?"
            },
            IntentType.PROFILE_UPDATE: {
                "en": "I can help you update your profile. What would you like to change?",
                "hi": "मैं आपकी प्रोफाइल अपडेट करने में मदद कर सकता हूं। आप क्या बदलना चाहते हैं?"
            },
            IntentType.HELP: {
                "en": "I'm here to help! What do you need assistance with?",
                "hi": "मैं मदद के लिए यहां हूं! आपको किसमें सहायता चाहिए?"
            },
            IntentType.GREETING: {
                "en": "Hello! Welcome to Digital Sahayak. How can I help you today?",
                "hi": "नमस्ते! डिजिटल सहायक में आपका स्वागत है। आज मैं आपकी कैसे मदद कर सकता हूं?"
            },
            IntentType.FEEDBACK: {
                "en": "We'd love to hear your feedback! What do you think about our service?",
                "hi": "हम आपकी प्रतिक्रिया सुनना चाहेंगे! आप हमारी सेवा के बारे में क्या सोचते हैं?"
            },
            IntentType.COMPLAINT: {
                "en": "I'm sorry to hear you're facing an issue. Please describe the problem in detail.",
                "hi": "मुझे खेद है कि आपको समस्या हो रही है। कृपया समस्या का विस्तार से वर्णन करें।"
            },
            IntentType.UPLOAD_DOCUMENT: {
                "en": "Sure, I can help you upload documents. Which document would you like to upload?",
                "hi": "ज़रूर, मैं दस्तावेज अपलोड करने में मदद कर सकता हूं। आप कौन सा दस्तावेज अपलोड करना चाहते हैं?"
            },
            IntentType.FILL_FORM: {
                "en": "Let's fill the form together. I'll guide you through each field.",
                "hi": "आइए साथ में फॉर्म भरें। मैं आपको हर फील्ड में मार्गदर्शन करूंगा।"
            },
            IntentType.CHECK_STATUS: {
                "en": "Let me check your status. Please provide your reference number.",
                "hi": "मैं आपकी स्थिति जांचता हूं। कृपया अपना संदर्भ नंबर दें।"
            },
            IntentType.UNCLEAR: {
                "en": "I'm not sure I understood correctly. Could you please rephrase your question?",
                "hi": "मुझे सही से समझ नहीं आया। क्या आप अपना सवाल दोबारा बता सकते हैं?"
            },
        }
        
        default_response = {
            "en": "How can I assist you?",
            "hi": "मैं आपकी कैसे मदद कर सकता हूं?"
        }
        
        response = responses.get(intent, default_response)
        
        return {
            "en": response["en"],
            "hi": response["hi"],
            "bilingual": f"{response['en']}\n\n{response['hi']}",
            "preferred": response.get(lang, response["en"])
        }
    
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


# ==============================================================================
# Advanced ML Components (DistilBERT Intent Classification)
# ==============================================================================

class DistilBERTIntentClassifier:
    """
    DistilBERT-based intent classification
    40% smaller, 60% faster than BERT while retaining 97% of language understanding
    """
    
    # Intent labels for fine-tuned model
    INTENT_LABELS = [
        "job_search", "job_details", "job_apply", "job_status",
        "scheme_search", "scheme_details", "scheme_apply", "scheme_eligibility",
        "register", "login", "profile_update", "help",
        "upload_document", "fill_form", "check_status",
        "greeting", "feedback", "complaint", "unclear"
    ]
    
    def __init__(
        self,
        model_name: str = "distilbert-base-multilingual-cased",
        model_path: Optional[str] = None,
        num_labels: int = 19
    ):
        self.model_name = model_name
        self.model_path = model_path
        self.num_labels = num_labels
        self.model = None
        self.tokenizer = None
        self.label2id = {label: i for i, label in enumerate(self.INTENT_LABELS)}
        self.id2label = {i: label for i, label in enumerate(self.INTENT_LABELS)}
        self._load_model()
    
    def _load_model(self):
        """Load DistilBERT model for intent classification"""
        try:
            from transformers import DistilBertForSequenceClassification, DistilBertTokenizer
            
            if self.model_path and os.path.exists(self.model_path):
                self.model = DistilBertForSequenceClassification.from_pretrained(
                    self.model_path,
                    num_labels=self.num_labels
                )
                self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_path)
            else:
                # Load base model (would need fine-tuning for production)
                self.model = DistilBertForSequenceClassification.from_pretrained(
                    self.model_name,
                    num_labels=self.num_labels
                )
                self.tokenizer = DistilBertTokenizer.from_pretrained(self.model_name)
            
            self.model.eval()
            logger.info(f"Loaded DistilBERT model: {self.model_name}")
        except ImportError:
            logger.warning("transformers not installed, using keyword-based classification")
        except Exception as e:
            logger.warning(f"Could not load DistilBERT model: {e}")
    
    def predict(self, text: str) -> Tuple[str, float, Dict[str, float]]:
        """
        Predict intent from text
        
        Args:
            text: Input message
            
        Returns:
            (predicted_intent, confidence, all_probabilities)
        """
        if self.model is None or self.tokenizer is None:
            return "unclear", 0.5, {}
        
        try:
            import torch
            import torch.nn.functional as F
            
            inputs = self.tokenizer(
                text,
                return_tensors="pt",
                truncation=True,
                max_length=128,
                padding=True
            )
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                logits = outputs.logits
                probs = F.softmax(logits, dim=-1)
            
            # Get prediction
            pred_idx = torch.argmax(probs, dim=-1).item()
            confidence = probs[0, pred_idx].item()
            
            # Get all probabilities
            all_probs = {
                self.id2label[i]: probs[0, i].item()
                for i in range(self.num_labels)
            }
            
            return self.id2label[pred_idx], confidence, all_probs
            
        except Exception as e:
            logger.warning(f"DistilBERT prediction failed: {e}")
            return "unclear", 0.5, {}
    
    def train(self, train_data: List[Dict], val_data: Optional[List[Dict]] = None, epochs: int = 3):
        """
        Fine-tune DistilBERT on intent classification data
        
        Args:
            train_data: List of {"text": str, "intent": str}
            val_data: Optional validation data
            epochs: Number of training epochs
        """
        if self.model is None or self.tokenizer is None:
            logger.error("Model not loaded, cannot train")
            return
        
        try:
            import torch
            from torch.utils.data import DataLoader, Dataset
            from transformers import AdamW, get_linear_schedule_with_warmup
            
            class IntentDataset(Dataset):
                def __init__(self, data, tokenizer, label2id):
                    self.data = data
                    self.tokenizer = tokenizer
                    self.label2id = label2id
                
                def __len__(self):
                    return len(self.data)
                
                def __getitem__(self, idx):
                    item = self.data[idx]
                    encoding = self.tokenizer(
                        item["text"],
                        truncation=True,
                        max_length=128,
                        padding="max_length",
                        return_tensors="pt"
                    )
                    return {
                        "input_ids": encoding["input_ids"].squeeze(),
                        "attention_mask": encoding["attention_mask"].squeeze(),
                        "labels": torch.tensor(self.label2id.get(item["intent"], 0))
                    }
            
            train_dataset = IntentDataset(train_data, self.tokenizer, self.label2id)
            train_loader = DataLoader(train_dataset, batch_size=16, shuffle=True)
            
            optimizer = AdamW(self.model.parameters(), lr=2e-5)
            scheduler = get_linear_schedule_with_warmup(
                optimizer,
                num_warmup_steps=100,
                num_training_steps=len(train_loader) * epochs
            )
            
            self.model.train()
            for epoch in range(epochs):
                total_loss = 0
                for batch in train_loader:
                    optimizer.zero_grad()
                    outputs = self.model(
                        input_ids=batch["input_ids"],
                        attention_mask=batch["attention_mask"],
                        labels=batch["labels"]
                    )
                    loss = outputs.loss
                    loss.backward()
                    optimizer.step()
                    scheduler.step()
                    total_loss += loss.item()
                
                logger.info(f"Epoch {epoch+1}/{epochs}, Loss: {total_loss/len(train_loader):.4f}")
            
            self.model.eval()
            logger.info("Training complete")
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
    
    def save(self, output_dir: str):
        """Save fine-tuned model"""
        if self.model is not None and self.tokenizer is not None:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            self.model.save_pretrained(output_path)
            self.tokenizer.save_pretrained(output_path)
            logger.info(f"Saved model to {output_dir}")


class BagOfWordsClassifier:
    """
    Lightweight bag-of-words intent classifier
    Fast alternative when DistilBERT is too heavy
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.word_weights: Dict[str, Dict[str, float]] = {}
        self._load_model()
    
    def _load_model(self):
        """Load pre-computed word weights"""
        if self.model_path and os.path.exists(self.model_path):
            try:
                with open(self.model_path, "r", encoding="utf-8") as f:
                    self.word_weights = json.load(f)
                logger.info("Loaded BoW classifier")
            except Exception as e:
                logger.warning(f"Could not load BoW model: {e}")
        else:
            # Use default weights based on intent patterns
            self._initialize_default_weights()
    
    def _initialize_default_weights(self):
        """Initialize default word weights from IntentClassifier patterns"""
        intent_words = {
            "job_search": ["job", "jobs", "vacancy", "naukri", "bharti", "नौकरी", "भर्ती"],
            "job_details": ["details", "salary", "eligibility", "qualification", "विवरण"],
            "job_apply": ["apply", "application", "submit", "आवेदन", "अप्लाई"],
            "job_status": ["status", "result", "selected", "स्थिति", "परिणाम"],
            "scheme_search": ["scheme", "yojana", "benefit", "योजना", "लाभ"],
            "scheme_apply": ["apply", "register", "enroll", "आवेदन"],
            "greeting": ["hello", "hi", "namaste", "नमस्ते"],
            "help": ["help", "support", "सहायता", "मदद"],
            "check_status": ["status", "check", "track", "स्थिति"],
        }
        
        for intent, words in intent_words.items():
            self.word_weights[intent] = {word: 1.0 for word in words}
    
    def predict(self, text: str) -> Tuple[str, float]:
        """
        Predict intent using bag-of-words
        
        Args:
            text: Input message
            
        Returns:
            (predicted_intent, confidence)
        """
        text_lower = text.lower()
        words = re.findall(r'\b\w+\b', text_lower)
        
        scores = {}
        for intent, weights in self.word_weights.items():
            score = sum(weights.get(word, 0) for word in words)
            if score > 0:
                scores[intent] = score
        
        if not scores:
            return "unclear", 0.3
        
        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        
        # Normalize to confidence
        total = sum(scores.values())
        confidence = max_score / total if total > 0 else 0.5
        
        return best_intent, confidence
    
    def train(self, data: List[Dict]):
        """Train BoW classifier from labeled data"""
        # Count word occurrences per intent
        word_counts: Dict[str, Dict[str, int]] = {}
        intent_counts: Dict[str, int] = {}
        
        for item in data:
            intent = item.get("intent", "unclear")
            text = item.get("text", "").lower()
            words = re.findall(r'\b\w+\b', text)
            
            if intent not in word_counts:
                word_counts[intent] = {}
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            
            for word in words:
                word_counts[intent][word] = word_counts[intent].get(word, 0) + 1
        
        # Compute TF-IDF-like weights
        for intent, counts in word_counts.items():
            self.word_weights[intent] = {}
            for word, count in counts.items():
                # Weight by frequency and inverse document frequency
                tf = count / intent_counts[intent]
                idf = len(word_counts) / sum(1 for ic in word_counts.values() if word in ic)
                self.word_weights[intent][word] = tf * idf
    
    def save(self, path: str):
        """Save word weights"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.word_weights, f, ensure_ascii=False, indent=2)


class AdvancedIntentClassifier:
    """
    Advanced Intent Classification for WhatsApp/Chat
    
    Combines DistilBERT with keyword-based fallback for reliable intent detection
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        use_distilbert: bool = True,
        use_bow: bool = True
    ):
        self.models_dir = Path(models_dir) if models_dir else None
        
        # Initialize DistilBERT
        if use_distilbert:
            model_path = str(self.models_dir / "intent_model") if self.models_dir else None
            self.distilbert = DistilBERTIntentClassifier(model_path=model_path)
        else:
            self.distilbert = None
        
        # Initialize BoW classifier
        if use_bow:
            bow_path = str(self.models_dir / "bow_weights.json") if self.models_dir else None
            self.bow_classifier = BagOfWordsClassifier(model_path=bow_path)
        else:
            self.bow_classifier = None
        
        # Keyword-based fallback
        self.keyword_classifier = IntentClassifier()
    
    def predict_intent(self, text: str) -> Dict:
        """
        Predict intent using ensemble of models
        
        Args:
            text: Input message
            
        Returns:
            Prediction result with intent, confidence, and metadata
        """
        results = []
        
        # DistilBERT prediction
        if self.distilbert and self.distilbert.model is not None:
            intent, confidence, probs = self.distilbert.predict(text)
            results.append({
                "model": "distilbert",
                "intent": intent,
                "confidence": confidence,
                "weight": 0.5
            })
        
        # BoW prediction
        if self.bow_classifier:
            intent, confidence = self.bow_classifier.predict(text)
            results.append({
                "model": "bow",
                "intent": intent,
                "confidence": confidence,
                "weight": 0.2
            })
        
        # Keyword prediction (always available)
        keyword_result = self.keyword_classifier.classify_intent(text)
        results.append({
            "model": "keywords",
            "intent": keyword_result["intent"].value if hasattr(keyword_result["intent"], "value") else keyword_result["intent"],
            "confidence": keyword_result["confidence"],
            "weight": 0.3
        })
        
        # Combine results
        if results:
            # Weighted voting
            intent_scores: Dict[str, float] = {}
            for r in results:
                intent = r["intent"]
                score = r["confidence"] * r["weight"]
                intent_scores[intent] = intent_scores.get(intent, 0) + score
            
            best_intent = max(intent_scores, key=intent_scores.get)
            combined_confidence = intent_scores[best_intent] / sum(r["weight"] for r in results)
            
            # Determine which model was most influential
            best_model = max(results, key=lambda r: r["confidence"] if r["intent"] == best_intent else 0)
            
            return {
                "intent": best_intent,
                "confidence": round(combined_confidence, 3),
                "model_used": best_model["model"],
                "all_predictions": results,
                "language": detect_lang(text)
            }
        
        return {
            "intent": "unclear",
            "confidence": 0.3,
            "model_used": "none",
            "all_predictions": [],
            "language": "en"
        }
    
    def get_response(self, intent: str, language: str = "en") -> Dict:
        """Get appropriate response for intent"""
        return self.keyword_classifier.get_response(
            IntentType[intent.upper()] if intent.upper() in IntentType.__members__ else IntentType.UNCLEAR,
            language
        )
    
    def train(self, data: List[Dict], val_split: float = 0.1):
        """
        Train all classifiers
        
        Args:
            data: List of {"text": str, "intent": str}
            val_split: Validation split ratio
        """
        # Split data
        n_val = int(len(data) * val_split)
        train_data = data[:-n_val] if n_val > 0 else data
        val_data = data[-n_val:] if n_val > 0 else None
        
        # Train DistilBERT
        if self.distilbert and self.distilbert.model is not None:
            self.distilbert.train(train_data, val_data)
        
        # Train BoW
        if self.bow_classifier:
            self.bow_classifier.train(train_data)
        
        logger.info("All classifiers trained")
    
    def save(self, output_dir: str):
        """Save all models"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if self.distilbert and self.distilbert.model is not None:
            self.distilbert.save(str(output_path / "intent_model"))
        
        if self.bow_classifier:
            self.bow_classifier.save(str(output_path / "bow_weights.json"))


# Convenience function for API integration
def predict_intent(text: str, use_ml: bool = False, models_dir: Optional[str] = None) -> Dict:
    """
    Predict user intent from message
    
    Args:
        text: Input message
        use_ml: Use DistilBERT for classification
        models_dir: Directory with trained models
        
    Returns:
        Prediction result with intent and confidence
    """
    if use_ml:
        classifier = AdvancedIntentClassifier(models_dir=models_dir)
        return classifier.predict_intent(text)
    else:
        classifier = IntentClassifier()
        result = classifier.classify_intent(text)
        return {
            "intent": result["intent"].value if hasattr(result["intent"], "value") else str(result["intent"]),
            "confidence": result["confidence"],
            "model_used": "keywords",
            "language": detect_lang(text)
        }
