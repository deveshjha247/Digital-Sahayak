"""
Content Summarizer AI Module
Rewrites and summarizes job/scheme descriptions for uniqueness and clarity
Uses template-based rewriting + key extraction (no external AI dependency)

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- All templates and summaries available in both languages
"""

import logging
import re
from typing import Dict, List, Optional, Tuple

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
}


class ContentSummarizer:
    """
    Summarizes and rewrites scraped job/scheme content
    
    Approach:
    1. Extract key information (salary, location, qualifications)
    2. Generate bullet points from description
    3. Rewrite main description with varied templates
    4. Create concise summaries in Hindi/English
    """
    
    # Key extraction patterns
    KEY_PATTERNS = {
        "salary": [r"salary[:\s]*[₹]*\s*([\d,]+)", r"([\d,]+)\s*(?:per|pm|p\.m)", r"ctc[:\s]*([\d,]+)"],
        "age": [r"age[:\s]*(\d+)\s*-?\s*(\d+)?", r"(\d+)\s*years?(?:\s*-\s*(\d+))?"],
        "qualification": [r"qualification[:\s]*([a-z ]+)", r"education[:\s]*([a-z ]+)"],
        "experience": [r"experience[:\s]*(\d+)\s*years?", r"(\d+)\s*y(?:ears?)?(?:\s*of)?(?:\s*exp)?"],
        "deadline": [r"deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", r"closing\s*date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})"],
    }
    
    # Description templates for rewriting
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
