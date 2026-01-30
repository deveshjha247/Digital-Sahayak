"""
AI Language Helper Module
Provides bilingual support (English primary, Hindi secondary) across all AI modules
No translation API needed - all labels pre-defined
"""

import json
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List

logger = logging.getLogger(__name__)

# Load language configuration
CONFIG_PATH = Path(__file__).parent / "language_config.json"

class LanguageHelper:
    """
    Bilingual language support for AI modules
    Primary: English, Secondary: Hindi
    
    Usage:
        lang = LanguageHelper()
        text = lang.get("labels.education.graduate")  # Returns both
        text_en = lang.get("labels.education.graduate", "en")  # English only
        text_hi = lang.get("labels.education.graduate", "hi")  # Hindi only
    """
    
    def __init__(self, config_path: str = None):
        self.config_path = Path(config_path) if config_path else CONFIG_PATH
        self.config = self._load_config()
        self.primary_lang = self.config.get("config", {}).get("primary_language", "en")
        self.secondary_lang = self.config.get("config", {}).get("secondary_language", "hi")
    
    def _load_config(self) -> Dict:
        """Load language configuration from JSON file"""
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                logger.warning(f"Language config not found at {self.config_path}")
                return {}
        except Exception as e:
            logger.error(f"Error loading language config: {e}")
            return {}
    
    def get(self, key: str, lang: str = None) -> str:
        """
        Get text by key path
        
        Args:
            key: Dot-separated path like "labels.education.graduate"
            lang: Optional language code (en/hi). If None, returns primary language.
        
        Returns:
            Text in requested language
        """
        parts = key.split(".")
        value = self.config
        
        for part in parts:
            if isinstance(value, dict) and part in value:
                value = value[part]
            else:
                return key  # Return key if not found
        
        if isinstance(value, dict):
            if lang:
                return value.get(lang, value.get(self.primary_lang, str(value)))
            return value.get(self.primary_lang, str(value))
        
        return str(value)
    
    def get_both(self, key: str) -> Tuple[str, str]:
        """
        Get text in both languages
        
        Returns:
            Tuple of (english, hindi)
        """
        return (self.get(key, "en"), self.get(key, "hi"))
    
    def get_bilingual(self, key: str, separator: str = " / ") -> str:
        """
        Get text with both languages combined
        
        Example: "Graduate / स्नातक"
        """
        en, hi = self.get_both(key)
        if en == hi:
            return en
        return f"{en}{separator}{hi}"
    
    def get_label(self, category: str, value: str, lang: str = None) -> str:
        """
        Get label from a category
        
        Args:
            category: education, categories, states, etc.
            value: The specific value like "graduate", "railway"
            lang: Optional language code
        """
        key = f"labels.{category}.{value.lower().replace(' ', '_').replace('-', '_')}"
        return self.get(key, lang)
    
    def get_intent(self, intent_type: str, lang: str = None) -> Dict:
        """Get intent configuration"""
        intent_data = self.config.get("intents", {}).get(intent_type, {})
        if lang and lang in intent_data:
            return intent_data[lang]
        return intent_data.get(self.primary_lang, {"name": intent_type, "description": ""})
    
    def get_intent_keywords(self, intent_type: str, lang: str = None) -> List[str]:
        """Get keywords for an intent in specified language"""
        intent_data = self.config.get("intents", {}).get(intent_type, {})
        keywords = intent_data.get("keywords", {})
        
        if lang:
            return keywords.get(lang, [])
        
        # Return all keywords from all languages
        all_keywords = []
        for lang_keywords in keywords.values():
            all_keywords.extend(lang_keywords)
        return all_keywords
    
    def get_all_intent_keywords(self) -> Dict[str, List[str]]:
        """Get all keywords for all intents (for classification)"""
        result = {}
        for intent_type in self.config.get("intents", {}):
            result[intent_type] = self.get_intent_keywords(intent_type)
        return result
    
    def get_form_field(self, category: str, field: str, lang: str = None) -> str:
        """Get form field label"""
        key = f"form_fields.{category}.{field}"
        return self.get(key, lang)
    
    def get_reason(self, reason_key: str, lang: str = None) -> str:
        """Get recommendation reason text"""
        key = f"recommendation_reasons.{reason_key}"
        return self.get(key, lang)
    
    def get_error(self, error_key: str, lang: str = None) -> str:
        """Get error message"""
        key = f"error_messages.{error_key}"
        return self.get(key, lang)
    
    def get_success(self, success_key: str, lang: str = None) -> str:
        """Get success message"""
        key = f"success_messages.{success_key}"
        return self.get(key, lang)
    
    def get_ui_label(self, category: str, key: str, lang: str = None) -> str:
        """Get UI label (buttons, sections, status)"""
        path = f"ui_labels.{category}.{key}"
        return self.get(path, lang)
    
    def detect_language(self, text: str) -> str:
        """
        Simple language detection based on character set
        
        Returns: 'hi' for Hindi, 'en' for English, 'hinglish' for mixed
        """
        if not text:
            return self.primary_lang
        
        # Count Hindi (Devanagari) characters
        hindi_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')
        # Count English characters
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        
        total = hindi_chars + english_chars
        if total == 0:
            return self.primary_lang
        
        hindi_ratio = hindi_chars / total
        
        if hindi_ratio > 0.7:
            return "hi"
        elif hindi_ratio > 0.2:
            return "hinglish"
        else:
            return "en"
    
    def format_response(self, text_en: str, text_hi: str, user_lang: str = None) -> str:
        """
        Format response based on user's preferred language
        If user_lang is None, returns both
        """
        if user_lang == "en":
            return text_en
        elif user_lang == "hi":
            return text_hi
        else:
            # Return both for best understanding
            return f"{text_en}\n{text_hi}"
    
    def get_education_display(self, education: str, lang: str = None) -> str:
        """Get education display text"""
        key = education.lower().replace(" ", "_").replace("-", "_")
        return self.get(f"labels.education.{key}", lang)
    
    def get_category_display(self, category: str, lang: str = None) -> str:
        """Get job category display text"""
        key = category.lower().replace(" ", "_")
        return self.get(f"labels.categories.{key}", lang)
    
    def get_state_display(self, state: str, lang: str = None) -> str:
        """Get state display text"""
        key = state.lower().replace(" ", "_")
        return self.get(f"labels.states.{key}", lang)


# Global instance for easy import
_helper = None

def get_language_helper() -> LanguageHelper:
    """Get singleton language helper instance"""
    global _helper
    if _helper is None:
        _helper = LanguageHelper()
    return _helper


# Convenience functions
def t(key: str, lang: str = None) -> str:
    """Shorthand for translation: t("labels.education.graduate", "hi")"""
    return get_language_helper().get(key, lang)

def t_both(key: str) -> Tuple[str, str]:
    """Get both languages: (english, hindi)"""
    return get_language_helper().get_both(key)

def t_bi(key: str) -> str:
    """Get bilingual text: 'English / हिंदी'"""
    return get_language_helper().get_bilingual(key)

def detect_lang(text: str) -> str:
    """Detect language of text"""
    return get_language_helper().detect_language(text)


# Education mapping with bilingual support
EDUCATION_BILINGUAL = {
    "10th Pass": ("10th Pass", "दसवीं पास"),
    "12th Pass": ("12th Pass", "बारहवीं पास"),
    "Diploma": ("Diploma", "डिप्लोमा"),
    "Graduate": ("Graduate", "स्नातक"),
    "Post-Graduate": ("Post-Graduate", "स्नातकोत्तर"),
    "Doctorate": ("Doctorate", "डॉक्टरेट"),
    "Any": ("Any", "कोई भी"),
}

# Category mapping with bilingual support
CATEGORY_BILINGUAL = {
    "Railway": ("Railway", "रेलवे"),
    "SSC": ("SSC", "एसएससी"),
    "UPSC": ("UPSC", "यूपीएससी"),
    "Bank": ("Bank", "बैंक"),
    "Police": ("Police", "पुलिस"),
    "Teaching": ("Teaching", "शिक्षण"),
    "Defence": ("Defence", "रक्षा"),
    "PSC": ("State PSC", "राज्य पीएससी"),
    "Court": ("Court", "न्यायालय"),
    "Government": ("Government", "सरकारी"),
}

# State mapping with bilingual support
STATE_BILINGUAL = {
    "Bihar": ("Bihar", "बिहार"),
    "Jharkhand": ("Jharkhand", "झारखंड"),
    "Uttar Pradesh": ("Uttar Pradesh", "उत्तर प्रदेश"),
    "Madhya Pradesh": ("Madhya Pradesh", "मध्य प्रदेश"),
    "Rajasthan": ("Rajasthan", "राजस्थान"),
    "Delhi": ("Delhi", "दिल्ली"),
    "Maharashtra": ("Maharashtra", "महाराष्ट्र"),
    "West Bengal": ("West Bengal", "पश्चिम बंगाल"),
    "All India": ("All India", "अखिल भारतीय"),
}
