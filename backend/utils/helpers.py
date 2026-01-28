"""
Utility Functions
Helper functions used across the application
"""

import re
import unicodedata
from datetime import datetime, timezone

def normalize_text(text: str) -> str:
    """Normalize text by removing accents and special characters"""
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    return text

def slugify(text: str, state_prefix: str = None) -> str:
    """
    Generate URL-friendly slug from text
    
    Args:
        text: Input text
        state_prefix: Optional state prefix (e.g., 'br', 'up')
    
    Returns:
        URL-safe slug
    """
    # Normalize and lowercase
    text = normalize_text(text).lower()
    
    # Replace spaces and special chars with hyphens
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    
    # Remove leading/trailing hyphens
    text = text.strip('-')
    
    # Add state prefix if provided
    if state_prefix:
        text = f"{state_prefix.lower()}/{text}"
    
    return text

def get_current_timestamp() -> str:
    """Get current timestamp in ISO format"""
    return datetime.now(timezone.utc).isoformat()

def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime object"""
    try:
        return datetime.fromisoformat(date_str)
    except:
        return None

def calculate_days_remaining(target_date: str) -> int:
    """Calculate days remaining until target date"""
    try:
        target = parse_date(target_date)
        if target:
            delta = target - datetime.now(timezone.utc)
            return max(0, delta.days)
    except:
        pass
    return 0

def sanitize_phone(phone: str) -> str:
    """Sanitize phone number"""
    # Remove all non-digit characters
    phone = re.sub(r'\D', '', phone)
    
    # Ensure 10 digits
    if len(phone) > 10:
        phone = phone[-10:]
    
    return phone

def validate_education_level(education: str) -> bool:
    """Validate education level"""
    valid_levels = ['10th', '12th', 'Graduate', 'Post Graduate', 'Diploma', 'ITI']
    return education in valid_levels

def extract_keywords(text: str, max_keywords: int = 10) -> list:
    """Extract important keywords from text"""
    # Simple keyword extraction (can be enhanced with NLP)
    words = re.findall(r'\b\w{4,}\b', text.lower())
    
    # Common stopwords to filter
    stopwords = {'this', 'that', 'with', 'from', 'have', 'will', 'been',
                 'more', 'when', 'there', 'their', 'which', 'these', 'those'}
    
    keywords = [w for w in words if w not in stopwords]
    
    # Return unique keywords
    return list(dict.fromkeys(keywords))[:max_keywords]

def format_indian_number(number: int) -> str:
    """Format number in Indian numbering system"""
    s = str(number)
    if len(s) <= 3:
        return s
    
    # Indian format: 1,00,000
    last3 = s[-3:]
    rest = s[:-3]
    
    result = last3
    while rest:
        if len(rest) > 2:
            result = rest[-2:] + ',' + result
            rest = rest[:-2]
        else:
            result = rest + ',' + result
            rest = ''
    
    return result
