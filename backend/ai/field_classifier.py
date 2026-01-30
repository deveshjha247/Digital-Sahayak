"""
Field Classifier AI Module
Identifies form field types and maps user data to form fields
Uses regex patterns + semantic matching (no external AI dependency)

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- All field labels and validation messages are pre-defined bilingually
"""

import logging
import re
from typing import Dict, List, Tuple, Optional
from enum import Enum

from .language_helper import get_language_helper, EDUCATION_BILINGUAL, CATEGORY_BILINGUAL, STATE_BILINGUAL

logger = logging.getLogger(__name__)

# Initialize language helper
lang_helper = get_language_helper()


class FieldType(str, Enum):
    """Enumeration of recognized field types"""
    NAME = "name"
    FIRST_NAME = "first_name"
    LAST_NAME = "last_name"
    FATHER_NAME = "father_name"
    MOTHER_NAME = "mother_name"
    SPOUSE_NAME = "spouse_name"
    
    EMAIL = "email"
    PHONE = "phone"
    MOBILE = "mobile"
    
    DOB = "dob"  # Date of birth
    AGE = "age"
    GENDER = "gender"
    MARITAL_STATUS = "marital_status"
    
    ADDRESS = "address"
    STREET = "street"
    CITY = "city"
    DISTRICT = "district"
    STATE = "state"
    PINCODE = "pincode"
    
    AADHAR = "aadhar"
    PAN = "pan"
    VOTER_ID = "voter_id"
    LICENSE = "license"
    PASSPORT = "passport"
    
    EDUCATION = "education"
    QUALIFICATION = "qualification"
    STREAM = "stream"
    UNIVERSITY = "university"
    
    OCCUPATION = "occupation"
    DESIGNATION = "designation"
    COMPANY = "company"
    INCOME = "income"
    SALARY = "salary"
    
    CASTE = "caste"
    CATEGORY = "category"
    RELIGION = "religion"
    
    BANK_NAME = "bank_name"
    ACCOUNT_NUMBER = "account_number"
    IFSC = "ifsc"
    
    OTHER = "other"


class FieldClassifier:
    """
    Classifies form fields and maps user profile data to them
    
    Three-stage pipeline:
    1. Field detection: Extract field labels and identify type
    2. Semantic understanding: Match labels to known patterns
    3. Profile mapping: Map user data to classified fields
    """
    
    # Field detection patterns (regex)
    FIELD_PATTERNS = {
        FieldType.NAME: [
            r"^full\s*name$",
            r"^name$",
            r"^applicant\s*name$",
            r"^आपका\s*नाम$",
            r"^नाम$",
        ],
        FieldType.FIRST_NAME: [
            r"^first\s*name$",
            r"^first\s*name$",
            r"^पहला\s*नाम$",
        ],
        FieldType.LAST_NAME: [
            r"^last\s*name$",
            r"^surname$",
            r"^आखिरी\s*नाम$",
        ],
        FieldType.FATHER_NAME: [
            r"^father('?s)?\s*name$",
            r"^पिता\s*का\s*नाम$",
            r"^पिता\s*नाम$",
        ],
        FieldType.MOTHER_NAME: [
            r"^mother('?s)?\s*name$",
            r"^माता\s*का\s*नाम$",
        ],
        
        FieldType.EMAIL: [
            r"^email",
            r"^e-mail",
            r"^ईमेल$",
            r"^emailaddress$",
        ],
        FieldType.PHONE: [
            r"^phone",
            r"^telephone",
            r"^फोन$",
            r"^दूरभाष$",
        ],
        FieldType.MOBILE: [
            r"^mobile",
            r"^cell",
            r"^mobilephone",
            r"^मोबाइल$",
        ],
        
        FieldType.DOB: [
            r"^date\s*of\s*birth",
            r"^dob$",
            r"^birth\s*date",
            r"^जन्म\s*तारीख$",
            r"^जन्मदिन$",
        ],
        FieldType.AGE: [
            r"^age$",
            r"^आयु$",
            r"^उम्र$",
        ],
        FieldType.GENDER: [
            r"^gender$",
            r"^sex$",
            r"^लिंग$",
        ],
        
        FieldType.ADDRESS: [
            r"^address$",
            r"^full\s*address",
            r"^current\s*address",
            r"^पता$",
        ],
        FieldType.CITY: [
            r"^city$",
            r"^town$",
            r"^शहर$",
        ],
        FieldType.STATE: [
            r"^state$",
            r"^province$",
            r"^राज्य$",
        ],
        FieldType.PINCODE: [
            r"^pincode$",
            r"^postal\s*code",
            r"^zip",
            r"^पिनकोड$",
        ],
        
        FieldType.AADHAR: [
            r"^aadhar",
            r"^aadhaar",
            r"^uid",
            r"^आधार$",
        ],
        FieldType.PAN: [
            r"^pan$",
            r"^pancard",
            r"^tax\s*id",
            r"^पैन$",
        ],
        FieldType.VOTER_ID: [
            r"^voter\s*id",
            r"^elector",
            r"^वोटर$",
        ],
        
        FieldType.EDUCATION: [
            r"^education",
            r"^qualification$",
            r"^शिक्षा$",
            r"^योग्यता$",
        ],
        
        FieldType.OCCUPATION: [
            r"^occupation$",
            r"^profession",
            r"^व्यवसाय$",
        ],
        FieldType.COMPANY: [
            r"^company",
            r"^employer",
            r"^organization",
            r"^कंपनी$",
        ],
        FieldType.INCOME: [
            r"^income",
            r"^salary",
            r"^earnings",
            r"^आय$",
        ],
        
        FieldType.CATEGORY: [
            r"^category$",
            r"^caste$",
            r"^category",
            r"^श्रेणी$",
            r"^जाति$",
        ],
    }
    
    # Validation patterns for field values
    VALIDATION_PATTERNS = {
        FieldType.EMAIL: r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
        FieldType.PHONE: r"^[+]?[0-9\s\-()]{7,20}$",
        FieldType.MOBILE: r"^[6-9][0-9]{9}$",  # Indian mobile
        FieldType.AADHAR: r"^\d{12}$",
        FieldType.PAN: r"^[A-Z]{5}\d{4}[A-Z]$",
        FieldType.PINCODE: r"^\d{6}$",
        FieldType.DOB: r"^\d{2}/\d{2}/\d{4}$|^\d{4}-\d{2}-\d{2}$",
    }
    
    def __init__(self):
        self.confidence_threshold = 0.6
    
    def classify_field(self, field_label: str, field_id: str = "") -> Tuple[FieldType, float]:
        """
        Classify a single form field
        
        Args:
            field_label: Label text shown to user
            field_id: HTML ID of field (helpful for identification)
        
        Returns:
            (FieldType, confidence_score)
        """
        combined_text = f"{field_label} {field_id}".lower().strip()
        
        if not combined_text:
            return FieldType.OTHER, 0.0
        
        best_match = (FieldType.OTHER, 0.0)
        
        # Check each field type's patterns
        for field_type, patterns in self.FIELD_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, combined_text, re.IGNORECASE):
                    confidence = self._calculate_confidence(pattern, combined_text)
                    if confidence > best_match[1]:
                        best_match = (field_type, confidence)
        
        return best_match
    
    def classify_form_fields(self, fields: List[Dict]) -> List[Dict]:
        """
        Classify multiple form fields
        
        Args:
            fields: List of {"label": "...", "id": "...", "value": "..."} dicts
        
        Returns:
            List of {"label": "...", "id": "...", "type": "...", "confidence": 0.xx}
        """
        classified = []
        
        for field in fields:
            field_type, confidence = self.classify_field(
                field.get("label", ""),
                field.get("id", "")
            )
            
            classified.append({
                "label": field.get("label"),
                "id": field.get("id"),
                "type": field_type.value,
                "confidence": round(confidence, 2),
                "value": field.get("value", ""),
            })
        
        return classified
    
    def map_user_to_fields(
        self,
        user_profile: Dict,
        classified_fields: List[Dict]
    ) -> Dict:
        """
        Map user profile data to classified form fields
        
        Args:
            user_profile: User data {name, email, phone, dob, address, aadhar, pan, education, ...}
            classified_fields: Output from classify_form_fields()
        
        Returns:
            Mapping of field_id -> suggested_value with confidence
        """
        mapping = {}
        
        for field in classified_fields:
            field_type = field["type"]
            field_id = field["id"]
            
            # Get suggested value based on field type
            suggested_value, confidence = self._get_field_value(
                field_type,
                user_profile
            )
            
            if suggested_value:
                mapping[field_id] = {
                    "type": field_type,
                    "value": suggested_value,
                    "confidence": confidence,
                    "formatted": self._format_field_value(field_type, suggested_value),
                }
        
        return mapping
    
    def _calculate_confidence(self, pattern: str, text: str) -> float:
        """Calculate confidence score for a pattern match"""
        # Exact match = high confidence
        if re.fullmatch(pattern, text, re.IGNORECASE):
            return 1.0
        
        # Word boundary match = medium confidence
        if re.search(rf"\b{pattern}\b", text, re.IGNORECASE):
            return 0.85
        
        # Partial match = lower confidence
        return 0.6
    
    def _get_field_value(self, field_type: str, user_profile: Dict) -> Tuple[Optional[str], float]:
        """Get suggested value from user profile for a field type"""
        try:
            field_type = FieldType(field_type)
        except ValueError:
            return None, 0.0
        
        confidence = 0.9  # High confidence for direct mappings
        
        # Name fields
        if field_type == FieldType.NAME:
            value = user_profile.get("name", user_profile.get("full_name"))
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.FIRST_NAME:
            value = user_profile.get("first_name")
            if not value:
                name = user_profile.get("name", "").split()
                value = name[0] if name else None
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.LAST_NAME:
            value = user_profile.get("last_name")
            if not value:
                name = user_profile.get("name", "").split()
                value = name[-1] if len(name) > 1 else None
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.FATHER_NAME:
            value = user_profile.get("father_name")
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.MOTHER_NAME:
            value = user_profile.get("mother_name")
            return value, confidence if value else (None, 0.0)
        
        # Contact fields
        if field_type == FieldType.EMAIL:
            value = user_profile.get("email")
            return value, confidence if value else (None, 0.0)
        
        if field_type in [FieldType.PHONE, FieldType.MOBILE]:
            value = user_profile.get("phone") or user_profile.get("mobile")
            return value, confidence if value else (None, 0.0)
        
        # Personal fields
        if field_type == FieldType.DOB:
            value = user_profile.get("dob") or user_profile.get("date_of_birth")
            if value and isinstance(value, str):
                return self._format_date(value), confidence
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.AGE:
            value = user_profile.get("age")
            return str(value) if value else None, confidence if value else (None, 0.0)
        
        if field_type == FieldType.GENDER:
            value = user_profile.get("gender")
            return value, confidence if value else (None, 0.0)
        
        # Address fields
        if field_type == FieldType.ADDRESS:
            value = user_profile.get("address") or user_profile.get("full_address")
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.CITY:
            value = user_profile.get("city")
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.STATE:
            value = user_profile.get("state")
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.PINCODE:
            value = user_profile.get("pincode")
            return value, confidence if value else (None, 0.0)
        
        # Document fields
        if field_type == FieldType.AADHAR:
            value = user_profile.get("aadhar") or user_profile.get("aadhaar")
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.PAN:
            value = user_profile.get("pan")
            return value, confidence if value else (None, 0.0)
        
        if field_type == FieldType.VOTER_ID:
            value = user_profile.get("voter_id")
            return value, confidence if value else (None, 0.0)
        
        # Education/Occupation
        if field_type == FieldType.EDUCATION:
            value = user_profile.get("education") or user_profile.get("qualification")
            return value, (confidence - 0.1) if value else (None, 0.0)
        
        if field_type == FieldType.OCCUPATION:
            value = user_profile.get("occupation")
            return value, (confidence - 0.1) if value else (None, 0.0)
        
        if field_type == FieldType.COMPANY:
            value = user_profile.get("company")
            return value, (confidence - 0.1) if value else (None, 0.0)
        
        if field_type == FieldType.INCOME:
            value = user_profile.get("income") or user_profile.get("salary")
            return str(value) if value else None, (confidence - 0.2) if value else (None, 0.0)
        
        # Category
        if field_type == FieldType.CATEGORY:
            value = user_profile.get("category") or user_profile.get("caste")
            return value, (confidence - 0.1) if value else (None, 0.0)
        
        return None, 0.0
    
    def _format_field_value(self, field_type: str, value: str) -> str:
        """Format value appropriately for field type"""
        if not value:
            return ""
        
        try:
            field_type = FieldType(field_type)
        except ValueError:
            return str(value)
        
        # Email: lowercase
        if field_type == FieldType.EMAIL:
            return value.lower()
        
        # Phone/Mobile: remove spaces/dashes
        if field_type in [FieldType.PHONE, FieldType.MOBILE]:
            return re.sub(r"[^0-9+]", "", str(value))
        
        # Name fields: title case
        if field_type in [FieldType.NAME, FieldType.FIRST_NAME, FieldType.LAST_NAME,
                         FieldType.FATHER_NAME, FieldType.MOTHER_NAME]:
            return str(value).title()
        
        # AADHAR: 12 digits with spaces
        if field_type == FieldType.AADHAR:
            digits = re.sub(r"\D", "", str(value))
            return f"{digits[0:4]} {digits[4:8]} {digits[8:12]}"
        
        # PAN: uppercase
        if field_type == FieldType.PAN:
            return str(value).upper()
        
        # DOB: DD/MM/YYYY format
        if field_type == FieldType.DOB:
            return self._format_date(value)
        
        return str(value)
    
    def _format_date(self, date_str: str) -> str:
        """Format date to DD/MM/YYYY"""
        try:
            # Try various formats
            from datetime import datetime
            
            for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d-%m-%Y", "%d.%m.%Y"]:
                try:
                    dt = datetime.strptime(date_str, fmt)
                    return dt.strftime("%d/%m/%Y")
                except ValueError:
                    continue
            
            return date_str  # Return as-is if no match
        except:
            return date_str
    
    def validate_field_value(self, field_type: str, value: str) -> Tuple[bool, Optional[str]]:
        """
        Validate if a value matches the field type
        
        Returns:
            (is_valid, error_message)
        """
        if not value:
            return False, "Value cannot be empty"
        
        try:
            field_type = FieldType(field_type)
        except ValueError:
            return True, None  # Unknown type - accept
        
        pattern = self.VALIDATION_PATTERNS.get(field_type)
        if not pattern:
            return True, None  # No validation for this type
        
        if re.match(pattern, str(value)):
            return True, None
        
        # Generate helpful error message
        error_messages = {
            FieldType.EMAIL: "Invalid email format",
            FieldType.PHONE: "Invalid phone number",
            FieldType.MOBILE: "Mobile should be 10 digits starting with 6-9",
            FieldType.AADHAR: "Aadhar should be 12 digits",
            FieldType.PAN: "PAN format: 5 letters + 4 digits + 1 letter",
            FieldType.PINCODE: "Pincode should be 6 digits",
            FieldType.DOB: "Date format: DD/MM/YYYY or YYYY-MM-DD",
        }
        
        error = error_messages.get(field_type, f"Invalid {field_type}")
        return False, error
