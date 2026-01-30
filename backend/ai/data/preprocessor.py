"""
Data Preprocessor
Handles cleaning, normalization, and standardization of raw data
"""

import re
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
import unicodedata

logger = logging.getLogger(__name__)


# =============================================================================
# FIELD NAME NORMALIZATION MAPPINGS
# =============================================================================

FIELD_NAME_MAPPINGS = {
    # Name fields
    "candidate_name": "name",
    "candidate's name": "name",
    "candidatename": "name",
    "applicant_name": "name",
    "applicant name": "name",
    "full_name": "name",
    "full name": "name",
    "fullname": "name",
    "naam": "name",  # Hindi
    "नाम": "name",
    "पूरा नाम": "name",
    
    # Father's name
    "father_name": "father_name",
    "father's name": "father_name",
    "fathername": "father_name",
    "father name": "father_name",
    "पिता का नाम": "father_name",
    "पिता नाम": "father_name",
    
    # Date of birth
    "date_of_birth": "dob",
    "date of birth": "dob",
    "dateofbirth": "dob",
    "dob": "dob",
    "birth_date": "dob",
    "birthdate": "dob",
    "जन्म तिथि": "dob",
    "जन्मतिथि": "dob",
    
    # Age
    "age": "age",
    "candidate_age": "age",
    "applicant_age": "age",
    "आयु": "age",
    "उम्र": "age",
    
    # Gender
    "gender": "gender",
    "sex": "gender",
    "लिंग": "gender",
    
    # Email
    "email": "email",
    "email_id": "email",
    "emailid": "email",
    "email_address": "email",
    "e-mail": "email",
    "ईमेल": "email",
    
    # Phone/Mobile
    "phone": "phone",
    "phone_number": "phone",
    "phonenumber": "phone",
    "mobile": "phone",
    "mobile_number": "phone",
    "mobilenumber": "phone",
    "contact": "phone",
    "contact_number": "phone",
    "मोबाइल": "phone",
    "फोन": "phone",
    "संपर्क": "phone",
    
    # Address
    "address": "address",
    "permanent_address": "address",
    "correspondence_address": "address",
    "पता": "address",
    "स्थायी पता": "permanent_address",
    
    # State
    "state": "state",
    "state_name": "state",
    "राज्य": "state",
    
    # District
    "district": "district",
    "district_name": "district",
    "जिला": "district",
    
    # Pin code
    "pincode": "pincode",
    "pin_code": "pincode",
    "pin": "pincode",
    "postal_code": "pincode",
    "zip": "pincode",
    "पिन कोड": "pincode",
    
    # Education
    "education": "education",
    "qualification": "education",
    "educational_qualification": "education",
    "highest_qualification": "education",
    "शिक्षा": "education",
    "योग्यता": "education",
    "शैक्षिक योग्यता": "education",
    
    # Category/Caste
    "category": "category",
    "caste": "category",
    "caste_category": "category",
    "reservation_category": "category",
    "वर्ग": "category",
    "जाति": "category",
    
    # Aadhaar
    "aadhaar": "aadhaar",
    "aadhar": "aadhaar",
    "aadhaar_number": "aadhaar",
    "aadhar_number": "aadhaar",
    "aadhaar_no": "aadhaar",
    "आधार": "aadhaar",
    "आधार नंबर": "aadhaar",
    
    # Income
    "income": "income",
    "annual_income": "income",
    "family_income": "income",
    "आय": "income",
    "वार्षिक आय": "income",
    
    # Bank details
    "bank_account": "bank_account",
    "account_number": "bank_account",
    "bank_account_number": "bank_account",
    "बैंक खाता": "bank_account",
    
    "ifsc": "ifsc_code",
    "ifsc_code": "ifsc_code",
    "ifsccode": "ifsc_code",
    
    # Job related
    "job_title": "job_title",
    "post": "job_title",
    "post_name": "job_title",
    "position": "job_title",
    "पद": "job_title",
    "पद का नाम": "job_title",
    
    "salary": "salary",
    "pay": "salary",
    "pay_scale": "salary",
    "वेतन": "salary",
    "वेतनमान": "salary",
    
    "vacancies": "vacancies",
    "vacancy": "vacancies",
    "no_of_posts": "vacancies",
    "number_of_posts": "vacancies",
    "रिक्तियां": "vacancies",
    
    "last_date": "deadline",
    "lastdate": "deadline",
    "deadline": "deadline",
    "last_date_to_apply": "deadline",
    "अंतिम तिथि": "deadline",
    
    # Scheme related
    "scheme_name": "scheme_name",
    "yojana": "scheme_name",
    "yojana_name": "scheme_name",
    "योजना": "scheme_name",
    "योजना का नाम": "scheme_name",
    
    "benefits": "benefits",
    "benefit": "benefits",
    "लाभ": "benefits",
    
    "eligibility": "eligibility",
    "eligibility_criteria": "eligibility",
    "पात्रता": "eligibility",
}


# =============================================================================
# DATE FORMAT PATTERNS
# =============================================================================

DATE_PATTERNS = [
    # ISO format
    (r'(\d{4})-(\d{2})-(\d{2})', '%Y-%m-%d'),
    # DD/MM/YYYY
    (r'(\d{2})/(\d{2})/(\d{4})', '%d/%m/%Y'),
    # DD-MM-YYYY
    (r'(\d{2})-(\d{2})-(\d{4})', '%d-%m-%Y'),
    # DD.MM.YYYY
    (r'(\d{2})\.(\d{2})\.(\d{4})', '%d.%m.%Y'),
    # MM/DD/YYYY (American)
    (r'(\d{2})/(\d{2})/(\d{4})', '%m/%d/%Y'),
    # YYYY/MM/DD
    (r'(\d{4})/(\d{2})/(\d{2})', '%Y/%m/%d'),
    # Written dates
    (r'(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})', '%d %b %Y'),
    (r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2}),?\s+(\d{4})', '%b %d %Y'),
]

# Hindi month names
HINDI_MONTHS = {
    'जनवरी': '01', 'फरवरी': '02', 'मार्च': '03', 'अप्रैल': '04',
    'मई': '05', 'जून': '06', 'जुलाई': '07', 'अगस्त': '08',
    'सितंबर': '09', 'अक्टूबर': '10', 'नवंबर': '11', 'दिसंबर': '12'
}


@dataclass
class CleaningStats:
    """Statistics for cleaning operations"""
    total_records: int = 0
    duplicates_removed: int = 0
    missing_values_handled: int = 0
    dates_standardized: int = 0
    numbers_standardized: int = 0
    text_cleaned: int = 0
    fields_normalized: int = 0
    invalid_records_dropped: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "total_records": self.total_records,
            "duplicates_removed": self.duplicates_removed,
            "missing_values_handled": self.missing_values_handled,
            "dates_standardized": self.dates_standardized,
            "numbers_standardized": self.numbers_standardized,
            "text_cleaned": self.text_cleaned,
            "fields_normalized": self.fields_normalized,
            "invalid_records_dropped": self.invalid_records_dropped,
            "final_records": self.total_records - self.duplicates_removed - self.invalid_records_dropped,
        }


class DataPreprocessor:
    """
    Comprehensive data preprocessing and cleaning
    
    Features:
    - Deduplication using content hashing
    - Missing value handling (drop/impute)
    - Date standardization to ISO format
    - Number/currency standardization
    - Text normalization (HTML, special chars, case)
    - Field name normalization
    """
    
    def __init__(
        self,
        required_fields: List[str] = None,
        drop_threshold: float = 0.5,
        output_date_format: str = "%Y-%m-%d"
    ):
        """
        Args:
            required_fields: Fields that must be present (records without dropped)
            drop_threshold: Drop record if missing > this fraction of fields
            output_date_format: Standardized date format
        """
        self.required_fields = required_fields or ["title"]
        self.drop_threshold = drop_threshold
        self.output_date_format = output_date_format
        self.stats = CleaningStats()
        
        # Track seen hashes for deduplication
        self._seen_hashes: Set[str] = set()
    
    def process(self, data: List[Dict]) -> List[Dict]:
        """
        Run complete preprocessing pipeline
        
        Args:
            data: Raw data records
        
        Returns:
            Cleaned and normalized data
        """
        self.stats = CleaningStats()
        self.stats.total_records = len(data)
        self._seen_hashes.clear()
        
        logger.info(f"Starting preprocessing of {len(data)} records")
        
        cleaned_data = []
        
        for record in data:
            # Step 1: Normalize field names
            record = self.normalize_field_names(record)
            
            # Step 2: Check required fields
            if not self._has_required_fields(record):
                self.stats.invalid_records_dropped += 1
                continue
            
            # Step 3: Handle missing values
            record = self.handle_missing_values(record)
            
            # Step 4: Deduplicate
            if self._is_duplicate(record):
                self.stats.duplicates_removed += 1
                continue
            
            # Step 5: Standardize dates
            record = self.standardize_dates(record)
            
            # Step 6: Standardize numbers
            record = self.standardize_numbers(record)
            
            # Step 7: Clean text fields
            record = self.clean_text_fields(record)
            
            cleaned_data.append(record)
        
        logger.info(f"Preprocessing complete: {len(cleaned_data)} records (removed {self.stats.duplicates_removed} duplicates)")
        return cleaned_data
    
    def normalize_field_names(self, record: Dict) -> Dict:
        """
        Normalize field names to consistent format
        """
        normalized = {}
        
        for key, value in record.items():
            # Convert to lowercase and strip
            normalized_key = key.lower().strip()
            
            # Replace common separators with underscore
            normalized_key = re.sub(r'[\s\-\.]+', '_', normalized_key)
            
            # Remove special characters except underscore
            normalized_key = re.sub(r'[^\w_]', '', normalized_key)
            
            # Check if we have a mapping
            if normalized_key in FIELD_NAME_MAPPINGS:
                normalized_key = FIELD_NAME_MAPPINGS[normalized_key]
                self.stats.fields_normalized += 1
            elif key.lower().strip() in FIELD_NAME_MAPPINGS:
                normalized_key = FIELD_NAME_MAPPINGS[key.lower().strip()]
                self.stats.fields_normalized += 1
            
            normalized[normalized_key] = value
        
        return normalized
    
    def handle_missing_values(self, record: Dict) -> Dict:
        """
        Handle missing values by imputation or marking
        """
        processed = {}
        missing_count = 0
        total_fields = len(record)
        
        for key, value in record.items():
            # Check if value is missing
            if self._is_missing(value):
                missing_count += 1
                
                # Impute with defaults based on field type
                if key in ['salary_min', 'salary_max', 'vacancies', 'age', 'min_age', 'max_age']:
                    processed[key] = self._get_default_numeric(key)
                    self.stats.missing_values_handled += 1
                elif key in ['state', 'category']:
                    processed[key] = "unknown"
                    self.stats.missing_values_handled += 1
                elif key in ['language']:
                    processed[key] = "bilingual"
                    self.stats.missing_values_handled += 1
                else:
                    processed[key] = None  # Keep as None
            else:
                processed[key] = value
        
        # Check if too many missing
        if total_fields > 0 and missing_count / total_fields > self.drop_threshold:
            processed['_too_many_missing'] = True
        
        return processed
    
    def _is_missing(self, value: Any) -> bool:
        """Check if value is considered missing"""
        if value is None:
            return True
        if isinstance(value, str):
            cleaned = value.strip().lower()
            return cleaned in ['', 'null', 'none', 'na', 'n/a', '-', 'undefined', 'nan']
        return False
    
    def _get_default_numeric(self, field: str) -> Optional[int]:
        """Get default numeric value for field"""
        defaults = {
            'salary_min': 15000,
            'salary_max': 50000,
            'vacancies': 1,
            'age': 25,
            'min_age': 18,
            'max_age': 35,
        }
        return defaults.get(field)
    
    def _has_required_fields(self, record: Dict) -> bool:
        """Check if record has required fields"""
        for field in self.required_fields:
            if field not in record or self._is_missing(record.get(field)):
                return False
        return True
    
    def _is_duplicate(self, record: Dict) -> bool:
        """Check if record is duplicate using content hash"""
        # Create hash from key fields
        hash_content = ""
        for field in ['title', 'description', 'organization', 'deadline']:
            value = record.get(field, '')
            if value:
                hash_content += str(value).lower().strip()
        
        if not hash_content:
            hash_content = str(record)
        
        content_hash = hashlib.md5(hash_content.encode('utf-8')).hexdigest()
        
        if content_hash in self._seen_hashes:
            return True
        
        self._seen_hashes.add(content_hash)
        record['_content_hash'] = content_hash
        return False
    
    def standardize_dates(self, record: Dict) -> Dict:
        """
        Standardize all date fields to ISO format
        """
        date_fields = ['dob', 'deadline', 'post_date', 'start_date', 'end_date', 
                       'last_date', 'apply_date', 'exam_date', 'result_date']
        
        for field in date_fields:
            if field in record and record[field]:
                original = record[field]
                standardized = self._parse_and_format_date(original)
                
                if standardized and standardized != original:
                    record[field] = standardized
                    self.stats.dates_standardized += 1
        
        return record
    
    def _parse_and_format_date(self, date_str: Any) -> Optional[str]:
        """Parse date string and return standardized format"""
        if not isinstance(date_str, str):
            if isinstance(date_str, datetime):
                return date_str.strftime(self.output_date_format)
            return str(date_str) if date_str else None
        
        date_str = date_str.strip()
        
        # Handle Hindi months
        for hindi_month, num in HINDI_MONTHS.items():
            if hindi_month in date_str:
                date_str = date_str.replace(hindi_month, num)
        
        # Try common date formats
        common_formats = [
            '%Y-%m-%d',
            '%d/%m/%Y',
            '%d-%m-%Y',
            '%d.%m.%Y',
            '%Y/%m/%d',
            '%d %b %Y',
            '%d %B %Y',
            '%b %d, %Y',
            '%B %d, %Y',
            '%d-%b-%Y',
            '%d/%b/%Y',
        ]
        
        for fmt in common_formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                return parsed.strftime(self.output_date_format)
            except ValueError:
                continue
        
        # Try regex patterns
        for pattern, fmt in DATE_PATTERNS:
            if re.search(pattern, date_str, re.IGNORECASE):
                try:
                    # Extract date components
                    match = re.search(pattern, date_str, re.IGNORECASE)
                    if match:
                        date_part = match.group(0)
                        parsed = datetime.strptime(date_part, fmt)
                        return parsed.strftime(self.output_date_format)
                except ValueError:
                    continue
        
        return date_str  # Return original if can't parse
    
    def standardize_numbers(self, record: Dict) -> Dict:
        """
        Standardize numbers and currency values
        """
        numeric_fields = ['salary', 'salary_min', 'salary_max', 'vacancies', 
                          'age', 'min_age', 'max_age', 'income', 'fee']
        
        for field in numeric_fields:
            if field in record and record[field]:
                original = record[field]
                standardized = self._parse_number(original)
                
                if standardized is not None and standardized != original:
                    record[field] = standardized
                    self.stats.numbers_standardized += 1
        
        # Handle salary range string
        if 'salary' in record and isinstance(record['salary'], str):
            salary_range = self._parse_salary_range(record['salary'])
            if salary_range:
                record['salary_min'] = salary_range[0]
                record['salary_max'] = salary_range[1]
        
        return record
    
    def _parse_number(self, value: Any) -> Optional[int]:
        """Parse number from various formats"""
        if isinstance(value, (int, float)):
            return int(value)
        
        if not isinstance(value, str):
            return None
        
        # Remove currency symbols and formatting
        cleaned = value.strip()
        cleaned = re.sub(r'[₹$€£,\s]', '', cleaned)
        cleaned = re.sub(r'(rs\.?|inr|rupees?)', '', cleaned, flags=re.IGNORECASE)
        
        # Handle lakhs/crores notation
        lakh_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:lakh|lac|लाख)', cleaned, re.IGNORECASE)
        if lakh_match:
            return int(float(lakh_match.group(1)) * 100000)
        
        crore_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:crore|cr|करोड़)', cleaned, re.IGNORECASE)
        if crore_match:
            return int(float(crore_match.group(1)) * 10000000)
        
        # Handle K notation (thousands)
        k_match = re.search(r'(\d+(?:\.\d+)?)\s*k', cleaned, re.IGNORECASE)
        if k_match:
            return int(float(k_match.group(1)) * 1000)
        
        # Extract plain number
        num_match = re.search(r'(\d+)', cleaned)
        if num_match:
            try:
                return int(num_match.group(1))
            except ValueError:
                return None
        
        return None
    
    def _parse_salary_range(self, salary_str: str) -> Optional[Tuple[int, int]]:
        """Parse salary range from string"""
        # Pattern: "₹15,000 - ₹25,000" or "15000-25000"
        range_match = re.search(
            r'[₹Rs.\s]*(\d[\d,\.]*)\s*[-–to]+\s*[₹Rs.\s]*(\d[\d,\.]*)',
            salary_str, re.IGNORECASE
        )
        
        if range_match:
            min_sal = self._parse_number(range_match.group(1))
            max_sal = self._parse_number(range_match.group(2))
            
            if min_sal and max_sal:
                return (min(min_sal, max_sal), max(min_sal, max_sal))
        
        return None
    
    def clean_text_fields(self, record: Dict) -> Dict:
        """
        Clean and normalize text fields
        """
        text_fields = ['title', 'description', 'organization', 'eligibility',
                       'benefits', 'requirements', 'instructions', 'name',
                       'address', 'education']
        
        for field in text_fields:
            if field in record and isinstance(record[field], str):
                original = record[field]
                cleaned = self.clean_text(original)
                
                if cleaned != original:
                    record[field] = cleaned
                    self.stats.text_cleaned += 1
        
        return record
    
    def clean_text(self, text: str) -> str:
        """
        Clean text: remove HTML, normalize whitespace, etc.
        """
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', ' ', text)
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        text = re.sub(r'&#\d+;', ' ', text)
        
        # Remove URLs
        text = re.sub(r'https?://\S+', '', text)
        text = re.sub(r'www\.\S+', '', text)
        
        # Remove email addresses (but keep for email fields)
        # text = re.sub(r'\S+@\S+\.\S+', '', text)
        
        # Normalize Unicode characters
        text = unicodedata.normalize('NFKC', text)
        
        # Replace multiple whitespace with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove leading/trailing whitespace
        text = text.strip()
        
        # Remove excessive punctuation
        text = re.sub(r'[.]{3,}', '...', text)
        text = re.sub(r'[-]{3,}', '--', text)
        text = re.sub(r'[_]{3,}', '__', text)
        
        return text
    
    def tokenize_text(self, text: str, lowercase: bool = True) -> List[str]:
        """
        Tokenize text into words
        """
        if not text:
            return []
        
        # Clean first
        text = self.clean_text(text)
        
        if lowercase:
            text = text.lower()
        
        # Split on whitespace and punctuation
        tokens = re.split(r'[\s\.,;:!?\(\)\[\]\{\}"\']+', text)
        
        # Filter empty tokens
        tokens = [t.strip() for t in tokens if t.strip()]
        
        return tokens
    
    def get_stats(self) -> Dict:
        """Get cleaning statistics"""
        return self.stats.to_dict()
    
    def reset_dedup_cache(self):
        """Reset deduplication cache for new batch"""
        self._seen_hashes.clear()


class TextNormalizer:
    """
    Specialized text normalization for search and matching
    """
    
    # Common stopwords (English + Hindi)
    STOPWORDS_EN = {
        'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
        'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
        'could', 'should', 'may', 'might', 'must', 'shall', 'can', 'need',
        'this', 'that', 'these', 'those', 'it', 'its', 'as', 'if', 'when',
        'than', 'so', 'no', 'not', 'only', 'same', 'also', 'very', 'just',
    }
    
    STOPWORDS_HI = {
        'का', 'की', 'के', 'को', 'में', 'से', 'है', 'हैं', 'था', 'थी', 'थे',
        'और', 'या', 'पर', 'इस', 'उस', 'एक', 'यह', 'वह', 'जो', 'कि', 'भी',
        'तो', 'ने', 'हो', 'होता', 'होती', 'होते', 'करता', 'करती', 'करते',
        'लिए', 'साथ', 'अपने', 'कर', 'जा', 'आ', 'ले', 'दे', 'रहा', 'रही',
    }
    
    def __init__(self, remove_stopwords: bool = False):
        self.remove_stopwords = remove_stopwords
        self.stopwords = self.STOPWORDS_EN | self.STOPWORDS_HI
    
    def normalize(self, text: str) -> str:
        """Full text normalization pipeline"""
        if not text:
            return ""
        
        # Step 1: Clean
        text = self._remove_html(text)
        text = self._remove_special_chars(text)
        
        # Step 2: Normalize
        text = text.lower()
        text = unicodedata.normalize('NFKC', text)
        
        # Step 3: Whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Step 4: Optionally remove stopwords
        if self.remove_stopwords:
            words = text.split()
            words = [w for w in words if w not in self.stopwords]
            text = ' '.join(words)
        
        return text
    
    def _remove_html(self, text: str) -> str:
        """Remove HTML tags and entities"""
        text = re.sub(r'<[^>]+>', ' ', text)
        text = re.sub(r'&[a-zA-Z]+;', ' ', text)
        text = re.sub(r'&#\d+;', ' ', text)
        return text
    
    def _remove_special_chars(self, text: str) -> str:
        """Remove special characters but keep Hindi and basic punctuation"""
        # Keep alphanumeric, Hindi characters, and basic punctuation
        text = re.sub(r'[^\w\s\u0900-\u097F.,!?;:\-]', ' ', text)
        return text
    
    def normalize_for_search(self, text: str) -> str:
        """Normalize text for search indexing"""
        normalized = self.normalize(text)
        # Remove all punctuation for search
        normalized = re.sub(r'[^\w\s\u0900-\u097F]', '', normalized)
        return normalized
    
    def get_ngrams(self, text: str, n: int = 2) -> List[str]:
        """Get character n-grams for fuzzy matching"""
        normalized = self.normalize_for_search(text)
        normalized = normalized.replace(' ', '')
        
        if len(normalized) < n:
            return [normalized]
        
        return [normalized[i:i+n] for i in range(len(normalized) - n + 1)]


def preprocess_dataset(
    data: List[Dict],
    required_fields: List[str] = None,
    output_path: str = None
) -> Tuple[List[Dict], Dict]:
    """
    Convenience function to preprocess a dataset
    
    Args:
        data: Raw data records
        required_fields: Fields that must be present
        output_path: Optional path to save cleaned data
    
    Returns:
        (cleaned_data, statistics)
    """
    preprocessor = DataPreprocessor(required_fields=required_fields)
    cleaned = preprocessor.process(data)
    stats = preprocessor.get_stats()
    
    if output_path:
        import json
        from pathlib import Path
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            for record in cleaned:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        
        logger.info(f"Saved cleaned data to {output_path}")
    
    return cleaned, stats
