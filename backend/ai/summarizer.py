"""
Content Summarizer AI Module
Rewrites and summarizes job/scheme descriptions for uniqueness and clarity

Architecture (T5/mT5 Sequence-to-Sequence):
1. Task Formulation: Summarization as text-to-text problem
2. Model Choice: T5/mT5 for multilingual Hindi/English output
3. Abstractive Generation: Generate new sentences for copyright-safe rewrites
4. Template Fallback: Rule-based templates when ML unavailable

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- All templates and summaries available in both languages

Dependencies (optional for ML mode):
- transformers (for T5/mT5)
- torch (for model inference)
"""

import logging
import re
import os
from typing import Dict, List, Optional, Any
from pathlib import Path

from .language_helper import get_language_helper

logger = logging.getLogger(__name__)

# Initialize language helper
lang_helper = get_language_helper()


# Bilingual key labels
KEY_LABELS = {
    "salary": {"en": "Salary", "hi": "वेतन"},
    "age": {"en": "Age", "hi": "आयु"},
    "qualification": {"en": "Qualification", "hi": "योग्यता"},
    "experience": {"en": "Experience", "hi": "अनुभव"},
    "deadline": {"en": "Deadline", "hi": "अंतिम तारीख"},
    "details": {"en": "Details", "hi": "विवरण"},
    "location": {"en": "Location", "hi": "स्थान"},
    "vacancies": {"en": "Vacancies", "hi": "रिक्तियां"},
    "category": {"en": "Category", "hi": "श्रेणी"},
    "department": {"en": "Department", "hi": "विभाग"},
    "posts": {"en": "Posts", "hi": "पद"},
    "apply_link": {"en": "Apply Link", "hi": "आवेदन लिंक"},
    "important_dates": {"en": "Important Dates", "hi": "महत्वपूर्ण तिथियां"},
    "application_fee": {"en": "Application Fee", "hi": "आवेदन शुल्क"},
    "selection_process": {"en": "Selection Process", "hi": "चयन प्रक्रिया"},
}

# Pre-defined bilingual rewrite templates
REWRITE_TEMPLATES_BILINGUAL = {
    "opening": {
        "en": [
            "Great opportunity for {role}.",
            "We are seeking a talented {role}.",
            "{role} position available.",
        ],
        "hi": [
            "{role} के लिए बेहतरीन अवसर।",
            "प्रतिभाशाली {role} की तलाश है।",
            "{role} पद उपलब्ध है।",
        ]
    },
    "apply_cta": {
        "en": [
            "Apply Now! Don't miss this opportunity.",
            "Submit your application before the deadline.",
        ],
        "hi": [
            "अभी आवेदन करें! इस अवसर को न चूकें।",
            "समय सीमा से पहले अपना आवेदन जमा करें।",
        ]
    },
    "deadline_warning": {
        "en": ["Last Date: {deadline}. Apply soon!"],
        "hi": ["अंतिम तिथि: {deadline}। जल्द आवेदन करें!"],
    }
}


class ContentSummarizer:
    """
    Summarizes and rewrites scraped job/scheme content
    All templates are pre-defined in both English and Hindi
    
    Approach:
    1. Extract key information (salary, location, qualifications)
    2. Generate bullet points from description
    3. Rewrite main description with varied templates
    4. Create concise summaries in Hindi/English
    """
    
    # Key extraction patterns (regex - supports Hindi patterns too)
    KEY_PATTERNS = {
        "salary": [r"salary[:\s]*[₹]*\s*([\d,]+)", r"([\d,]+)\s*(?:per|pm|p\.m)", r"ctc[:\s]*([\d,]+)", r"वेतन[:\s]*([\d,]+)"],
        "age": [r"age[:\s]*(\d+)\s*-?\s*(\d+)?", r"(\d+)\s*years?(?:\s*-\s*(\d+))?", r"आयु[:\s]*(\d+)"],
        "qualification": [r"qualification[:\s]*([a-z ]+)", r"education[:\s]*([a-z ]+)", r"योग्यता[:\s]*(.+)"],
        "experience": [r"experience[:\s]*(\d+)\s*years?", r"(\d+)\s*y(?:ears?)?(?:\s*of)?(?:\s*exp)?", r"अनुभव[:\s]*(\d+)"],
        "deadline": [r"deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", r"closing\s*date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", r"अंतिम\s*तिथि[:\s]*(.+)"],
        "vacancies": [r"(\d+)\s*(?:vacancies|posts|पद)", r"total\s*posts?[:\s]*(\d+)", r"रिक्तियां[:\s]*(\d+)"],
    }
    
    # Description templates for rewriting (backward compatible)
    REWRITE_TEMPLATES = {
        "opening": [
            "We are seeking a talented {role} to join our {company} team.",
            "Join {company} as a {role} and make an impact.",
            "{company} is looking for a skilled {role}.",
            "Be part of {company}'s growing team as a {role}.",
        ],
        "qualification": [
            "Candidates should have {qualification}.",
            "{qualification} is required for this position.",
            "A {qualification} is essential for success in this role.",
            "This role requires {qualification}.",
        ],
        "responsibility": [
            "In this role, you will {responsibility}.",
            "Your responsibilities will include {responsibility}.",
            "You will be responsible for {responsibility}.",
            "Key duties include {responsibility}.",
        ],
        "benefit": [
            "We offer competitive {benefit}.",
            "Enjoy excellent {benefit} and growth opportunities.",
            "This position provides {benefit}.",
            "You'll receive {benefit} as part of our compensation.",
        ],
    }
    
    def __init__(self):
        self.min_summary_length = 30  # minimum characters
        self.max_summary_length = 200  # maximum characters
    
    def extract_key_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract key information from job description"""
        if not text:
            return {}
        
        text_lower = text.lower()
        extracted = {}
        
        # Extract each key type
        for key_type, patterns in self.KEY_PATTERNS.items():
            for pattern in patterns:
                match = re.search(pattern, text_lower, re.IGNORECASE)
                if match:
                    extracted[key_type] = match.group(1)
                    break
        
        return extracted
    
    def extract_bullet_points(self, text: str, max_points: int = 5) -> List[str]:
        """
        Extract or generate bullet points from description
        """
        if not text:
            return []
        
        bullets = []
        
        # Split by common delimiters
        sentences = re.split(r'[\.;]+', text)
        
        # Filter meaningful sentences
        for sentence in sentences:
            sentence = sentence.strip()
            
            # Skip if too short or too long
            if len(sentence) < 10 or len(sentence) > 300:
                continue
            
            # Skip if looks like header/navigation
            if any(skip in sentence.lower() for skip in ["click here", "apply now", "job alert"]):
                continue
            
            bullets.append(sentence)
        
        # Limit to max points
        return bullets[:max_points]
    
    def generate_concise_summary(self, text: str, max_length: int = 150) -> str:
        """Generate a concise summary of the text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # If already short, return as-is
        if len(text) <= max_length:
            return text
        
        # Try to break at sentence boundary
        sentences = re.split(r'[\.!?]+', text)
        summary = ""
        
        for sentence in sentences:
            test_summary = summary + sentence.strip() + "."
            if len(test_summary) <= max_length:
                summary = test_summary
            else:
                break
        
        if not summary:
            # Fallback: truncate at word boundary
            words = text[:max_length].rsplit(' ', 1)[0]
            summary = words + "..."
        
        return summary.strip()
    
    def rewrite_description(self, original: str, style: str = "professional") -> str:
        """
        Rewrite description in different style to avoid plagiarism
        
        Args:
            original: Original description text
            style: 'professional', 'casual', 'concise'
        """
        if not original:
            return ""
        
        # Extract key information
        key_info = self.extract_key_info(original)
        
        # Extract bullet points
        bullets = self.extract_bullet_points(original)
        
        # Build rewritten version
        rewritten_parts = []
        
        # Opening
        if style == "professional":
            rewritten_parts.append("We are seeking qualified candidates for an exciting opportunity.")
        elif style == "casual":
            rewritten_parts.append("Join our team for this great opportunity!")
        else:  # concise
            rewritten_parts.append("We're hiring!")
        
        # Key information
        if key_info.get("qualification"):
            rewritten_parts.append(f"Required qualification: {key_info['qualification']}")
        
        if key_info.get("experience"):
            rewritten_parts.append(f"Experience needed: {key_info['experience']}")
        
        # Responsibilities
        if bullets:
            rewritten_parts.append("Responsibilities:")
            for bullet in bullets[:3]:
                rewritten_parts.append(f"• {bullet}")
        
        return "\n".join(rewritten_parts)
    
    def generate_hindi_summary(self, text: str, job_title: str = "") -> str:
        """Generate Hindi summary of job description"""
        if not text:
            return ""
        
        # Extract key info
        key_info = self.extract_key_info(text)
        
        # Build Hindi summary
        parts = []
        
        if job_title:
            parts.append(f"📌 {job_title}")
        
        if key_info.get("qualification"):
            parts.append(f"योग्यता: {key_info['qualification']}")
        
        if key_info.get("salary"):
            parts.append(f"वेतन: ₹{key_info['salary']}")
        
        if key_info.get("experience"):
            parts.append(f"अनुभव: {key_info['experience']}")
        
        if key_info.get("age"):
            parts.append(f"आयु: {key_info['age']}")
        
        if key_info.get("deadline"):
            parts.append(f"अंतिम तारीख: {key_info['deadline']}")
        
        # Add brief summary
        summary = self.generate_concise_summary(text, 100)
        if summary:
            parts.append(f"विवरण: {summary}")
        
        return "\n".join(parts)
    
    def generate_english_summary(self, text: str, job_title: str = "") -> str:
        """Generate English summary of job description"""
        if not text:
            return ""
        
        # Extract key info
        key_info = self.extract_key_info(text)
        
        # Build English summary
        parts = []
        
        if job_title:
            parts.append(f"📌 {job_title}")
        
        if key_info.get("qualification"):
            parts.append(f"Qualification: {key_info['qualification']}")
        
        if key_info.get("salary"):
            parts.append(f"Salary: ₹{key_info['salary']}")
        
        if key_info.get("experience"):
            parts.append(f"Experience: {key_info['experience']}")
        
        if key_info.get("age"):
            parts.append(f"Age: {key_info['age']}")
        
        if key_info.get("deadline"):
            parts.append(f"Deadline: {key_info['deadline']}")
        
        # Add brief summary
        summary = self.generate_concise_summary(text, 100)
        if summary:
            parts.append(f"Details: {summary}")
        
        return "\n".join(parts)
    
    def process_job_description(self, job: Dict) -> Dict:
        """
        Process complete job description and return enriched content
        Returns bilingual summaries (English primary, Hindi secondary)
        """
        original_desc = job.get("description", "")
        title = job.get("title", "Job")
        
        english_summary = self.generate_english_summary(original_desc, title)
        hindi_summary = self.generate_hindi_summary(original_desc, title)
        
        return {
            "title": title,
            "original_description": original_desc,
            
            # English summaries (primary)
            "summary_english": english_summary,
            "summary_en": english_summary,  # Alias
            
            # Hindi summaries (secondary)
            "summary_hindi": hindi_summary,
            "summary_hi": hindi_summary,  # Alias
            
            # Bilingual combined
            "summary_bilingual": f"**English:**\n{english_summary}\n\n**हिंदी:**\n{hindi_summary}",
            
            # Rewritten versions
            "rewritten_professional": self.rewrite_description(original_desc, "professional"),
            "rewritten_casual": self.rewrite_description(original_desc, "casual"),
            "rewritten_concise": self.rewrite_description(original_desc, "concise"),
            
            # Key information (bilingual)
            "key_info": self._get_bilingual_key_info(original_desc),
            "bullet_points": self.extract_bullet_points(original_desc),
            "uniqueness_score": 0.75,
        }
    
    def _get_bilingual_key_info(self, text: str) -> Dict:
        """Extract key info with bilingual labels"""
        key_info = self.extract_key_info(text)
        
        bilingual_info = {}
        for key, value in key_info.items():
            if value and key in KEY_LABELS:
                bilingual_info[key] = {
                    "value": value,
                    "label_en": KEY_LABELS[key]["en"],
                    "label_hi": KEY_LABELS[key]["hi"],
                    "formatted_en": f"{KEY_LABELS[key]['en']}: {value}",
                    "formatted_hi": f"{KEY_LABELS[key]['hi']}: {value}"
                }
        
        return bilingual_info


# ==============================================================================
# Advanced ML Components (T5/mT5 Summarization)
# ==============================================================================

class T5Summarizer:
    """
    T5/mT5 based abstractive summarization
    Generates new sentences for copyright-safe rewrites
    """
    
    def __init__(
        self,
        model_name: str = "google/mt5-small",  # Multilingual T5 for Hindi/English
        model_path: Optional[str] = None,
        max_length: int = 150,
        min_length: int = 30
    ):
        self.model_name = model_name
        self.model_path = model_path
        self.max_length = max_length
        self.min_length = min_length
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load T5/mT5 model for summarization"""
        try:
            from transformers import T5ForConditionalGeneration, T5Tokenizer, AutoModelForSeq2SeqLM, AutoTokenizer
            
            if self.model_path and os.path.exists(self.model_path):
                self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            else:
                # Try mT5 for multilingual support
                try:
                    self.model = AutoModelForSeq2SeqLM.from_pretrained(self.model_name)
                    self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                except:
                    # Fallback to standard T5
                    self.model = T5ForConditionalGeneration.from_pretrained("t5-small")
                    self.tokenizer = T5Tokenizer.from_pretrained("t5-small")
            
            self.model.eval()
            logger.info(f"Loaded T5 model: {self.model_name}")
        except ImportError:
            logger.warning("transformers not installed, using template-based summarization")
        except Exception as e:
            logger.warning(f"Could not load T5 model: {e}")
    
    def summarize(self, text: str, language: str = "en") -> str:
        """
        Generate abstractive summary using T5
        
        Args:
            text: Input text to summarize
            language: Output language ("en" or "hi")
            
        Returns:
            Generated summary
        """
        if self.model is None or self.tokenizer is None:
            return self._template_summarize(text, language)
        
        try:
            import torch
            
            # Prepare input with task prefix
            if "mt5" in self.model_name.lower():
                # mT5 task prefix
                prefix = "summarize: " if language == "en" else "सारांश: "
            else:
                prefix = "summarize: "
            
            input_text = prefix + text[:1024]  # Truncate long texts
            
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=self.max_length,
                    min_length=self.min_length,
                    length_penalty=2.0,
                    num_beams=4,
                    early_stopping=True
                )
            
            summary = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return summary
            
        except Exception as e:
            logger.warning(f"T5 summarization failed: {e}")
            return self._template_summarize(text, language)
    
    def _template_summarize(self, text: str, language: str) -> str:
        """Fallback template-based summarization"""
        # Extract key sentences
        sentences = re.split(r'[.।]', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        if not sentences:
            return text[:200] + "..."
        
        # Take first and most important sentences
        summary_sentences = sentences[:3]
        
        if language == "hi":
            return "। ".join(summary_sentences) + "।"
        else:
            return ". ".join(summary_sentences) + "."
    
    def rewrite(self, text: str, style: str = "professional", language: str = "en") -> str:
        """
        Rewrite text in a specific style
        
        Args:
            text: Input text
            style: Writing style ("professional", "casual", "concise")
            language: Output language
            
        Returns:
            Rewritten text
        """
        if self.model is None or self.tokenizer is None:
            return self._template_rewrite(text, style, language)
        
        try:
            import torch
            
            # Style-specific prompts
            style_prompts = {
                "professional": "rewrite professionally: ",
                "casual": "rewrite casually: ",
                "concise": "summarize concisely: "
            }
            
            prefix = style_prompts.get(style, "rewrite: ")
            input_text = prefix + text[:1024]
            
            inputs = self.tokenizer(
                input_text,
                return_tensors="pt",
                max_length=512,
                truncation=True
            )
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs.input_ids,
                    max_length=256,
                    num_beams=4,
                    early_stopping=True,
                    do_sample=True,
                    temperature=0.7
                )
            
            rewritten = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return rewritten
            
        except Exception as e:
            logger.warning(f"T5 rewriting failed: {e}")
            return self._template_rewrite(text, style, language)
    
    def _template_rewrite(self, text: str, style: str, language: str) -> str:
        """Fallback template-based rewriting"""
        # Use ContentSummarizer's template rewriting
        summarizer = ContentSummarizer()
        return summarizer.rewrite_description(text, style)


class TranslationAugmenter:
    """
    Translation-based augmentation for multilingual summaries
    """
    
    def __init__(self, model_name: str = "Helsinki-NLP/opus-mt-en-hi"):
        self.model_name = model_name
        self.model = None
        self.tokenizer = None
        self._load_model()
    
    def _load_model(self):
        """Load translation model"""
        try:
            from transformers import MarianMTModel, MarianTokenizer
            
            self.model = MarianMTModel.from_pretrained(self.model_name)
            self.tokenizer = MarianTokenizer.from_pretrained(self.model_name)
            self.model.eval()
            logger.info(f"Loaded translation model: {self.model_name}")
        except ImportError:
            logger.warning("transformers not installed, translation unavailable")
        except Exception as e:
            logger.warning(f"Could not load translation model: {e}")
    
    def translate(self, text: str, source: str = "en", target: str = "hi") -> str:
        """Translate text between languages"""
        if self.model is None:
            return self._fallback_translate(text, target)
        
        try:
            import torch
            
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=512)
            
            with torch.no_grad():
                outputs = self.model.generate(**inputs, max_length=512)
            
            translated = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return translated
            
        except Exception as e:
            logger.warning(f"Translation failed: {e}")
            return self._fallback_translate(text, target)
    
    def _fallback_translate(self, text: str, target: str) -> str:
        """Fallback: return original with note"""
        if target == "hi":
            return f"(हिंदी अनुवाद उपलब्ध नहीं) {text}"
        return text


class AdvancedSummarizer:
    """
    Advanced Content Summarization & Rewriting
    
    Combines T5/mT5 for abstractive summarization with template fallback
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        use_t5: bool = True,
        multilingual: bool = True
    ):
        self.models_dir = Path(models_dir) if models_dir else None
        
        # Initialize T5 summarizer
        if use_t5:
            model_name = "google/mt5-small" if multilingual else "t5-small"
            model_path = str(self.models_dir / "summarizer") if self.models_dir else None
            self.t5_model = T5Summarizer(model_name=model_name, model_path=model_path)
        else:
            self.t5_model = None
        
        # Initialize translator
        if multilingual:
            self.translator = TranslationAugmenter()
        else:
            self.translator = None
        
        # Template-based fallback
        self.template_summarizer = ContentSummarizer()
    
    def summarize(self, text: str, language: str = "en", max_length: int = 150) -> str:
        """
        Generate abstractive summary
        
        Args:
            text: Input text
            language: Output language ("en" or "hi")
            max_length: Maximum summary length
            
        Returns:
            Generated summary
        """
        # Try T5 first
        if self.t5_model and self.t5_model.model is not None:
            summary = self.t5_model.summarize(text, language)
            if summary and len(summary) > 20:
                return summary
        
        # Fallback to template
        template_result = self.template_summarizer.generate_summary({"description": text})
        
        if language == "hi":
            return template_result.get("summary_hi", template_result.get("summary_hindi", ""))
        return template_result.get("summary_en", template_result.get("summary_english", ""))
    
    def rewrite(self, text: str, language: str = "en", style: str = "professional") -> str:
        """
        Rewrite text for uniqueness
        
        Args:
            text: Input text
            language: Output language
            style: Writing style
            
        Returns:
            Rewritten text
        """
        # Try T5 rewriting
        if self.t5_model and self.t5_model.model is not None:
            rewritten = self.t5_model.rewrite(text, style, language)
            if rewritten and len(rewritten) > 20:
                return rewritten
        
        # Fallback to template
        return self.template_summarizer.rewrite_description(text, style)
    
    def generate_bilingual_summary(self, text: str) -> Dict[str, str]:
        """
        Generate summaries in both English and Hindi
        
        Args:
            text: Input text
            
        Returns:
            Dictionary with English and Hindi summaries
        """
        # Generate English summary
        english_summary = self.summarize(text, "en")
        
        # Generate Hindi summary
        if self.t5_model and self.t5_model.model is not None:
            hindi_summary = self.summarize(text, "hi")
        elif self.translator:
            hindi_summary = self.translator.translate(english_summary, "en", "hi")
        else:
            hindi_summary = self.template_summarizer.generate_summary({"description": text}).get("summary_hi", "")
        
        return {
            "en": english_summary,
            "hi": hindi_summary,
            "english": english_summary,
            "hindi": hindi_summary,
            "bilingual": f"**English:**\n{english_summary}\n\n**हिंदी:**\n{hindi_summary}"
        }
    
    def process_job_posting(self, job: Dict) -> Dict:
        """
        Process a job posting with full summarization
        
        Args:
            job: Job posting dictionary
            
        Returns:
            Processed result with summaries and rewrites
        """
        title = job.get("title", "")
        description = job.get("description", "")
        
        # Generate summaries
        bilingual = self.generate_bilingual_summary(description)
        
        # Generate rewrites
        rewrites = {
            "professional": self.rewrite(description, "en", "professional"),
            "casual": self.rewrite(description, "en", "casual"),
            "concise": self.rewrite(description, "en", "concise")
        }
        
        # Extract key info using template summarizer
        key_info = self.template_summarizer.extract_key_info(description)
        
        return {
            "title": title,
            "original": description,
            "summary_en": bilingual["en"],
            "summary_hi": bilingual["hi"],
            "summary_bilingual": bilingual["bilingual"],
            "rewritten": rewrites,
            "key_info": key_info,
            "bullet_points": self.template_summarizer.extract_bullet_points(description)
        }


# Convenience function for API integration
def rewrite(text: str, language: str = "en", use_ml: bool = False, models_dir: Optional[str] = None) -> str:
    """
    Rewrite text for uniqueness
    
    Args:
        text: Input text
        language: Output language ("en" or "hi")
        use_ml: Use T5/mT5 for rewriting
        models_dir: Directory with trained models
        
    Returns:
        Rewritten text
    """
    if use_ml:
        summarizer = AdvancedSummarizer(models_dir=models_dir)
        return summarizer.rewrite(text, language)
    else:
        summarizer = ContentSummarizer()
        return summarizer.rewrite_description(text)


def summarize(text: str, language: str = "en", use_ml: bool = False, models_dir: Optional[str] = None) -> str:
    """
    Generate summary of text
    
    Args:
        text: Input text
        language: Output language
        use_ml: Use T5/mT5 for summarization
        models_dir: Directory with trained models
        
    Returns:
        Generated summary
    """
    if use_ml:
        summarizer = AdvancedSummarizer(models_dir=models_dir)
        return summarizer.summarize(text, language)
    else:
        summarizer = ContentSummarizer()
        result = summarizer.generate_summary({"description": text})
        key = f"summary_{language}" if language in ["en", "hi"] else "summary_english"
        return result.get(key, result.get("summary_english", ""))
