"""
Document & Field Validator AI Module
Validates documents, form fields, and user data
Includes OCR field extraction, format validation, and constraint checking

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- All validation messages are pre-defined bilingually
"""

import logging
import re
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any

from .language_helper import get_language_helper

logger = logging.getLogger(__name__)

# Initialize language helper
lang_helper = get_language_helper()


# Bilingual error messages
VALIDATION_MESSAGES = {
    "aadhar": {
        "success": {"en": "Valid Aadhar number", "hi": "वैध आधार नंबर"},
        "error": {"en": "Invalid Aadhar number. Must be 12 digits.", "hi": "अवैध आधार नंबर। 12 अंकों का होना चाहिए।"}
    },
    "pan": {
        "success": {"en": "Valid PAN number", "hi": "वैध पैन नंबर"},
        "error": {"en": "Invalid PAN format. Must be 5 letters + 4 digits + 1 letter.", "hi": "अवैध पैन प्रारूप। 5 अक्षर + 4 अंक + 1 अक्षर होना चाहिए।"}
    },
    "email": {
        "success": {"en": "Valid email address", "hi": "वैध ईमेल पता"},
        "error": {"en": "Invalid email format.", "hi": "अवैध ईमेल प्रारूप।"}
    },
    "phone": {
        "success": {"en": "Valid phone number", "hi": "वैध फोन नंबर"},
        "error": {"en": "Invalid phone number. Must be 10 digits starting with 6-9.", "hi": "अवैध फोन नंबर। 6-9 से शुरू होने वाले 10 अंक होने चाहिए।"}
    },
    "date_dob": {
        "success": {"en": "Valid date of birth", "hi": "वैध जन्म तिथि"},
        "error": {"en": "Invalid date format. Use DD/MM/YYYY.", "hi": "अवैध तारीख प्रारूप। DD/MM/YYYY का उपयोग करें।"}
    },
    "voter_id": {
        "success": {"en": "Valid Voter ID", "hi": "वैध वोटर आईडी"},
        "error": {"en": "Invalid Voter ID. Must be 3 letters + 7 digits.", "hi": "अवैध वोटर आईडी। 3 अक्षर + 7 अंक होने चाहिए।"}
    },
    "driving_license": {
        "success": {"en": "Valid Driving License", "hi": "वैध ड्राइविंग लाइसेंस"},
        "error": {"en": "Invalid DL format. Must be 2 letters + 13 digits.", "hi": "अवैध डीएल प्रारूप। 2 अक्षर + 13 अंक होने चाहिए।"}
    },
    "pincode": {
        "success": {"en": "Valid Pincode", "hi": "वैध पिनकोड"},
        "error": {"en": "Invalid Pincode. Must be 6 digits.", "hi": "अवैध पिनकोड। 6 अंक होने चाहिए।"}
    },
}


class DocumentType(Enum):
    """Supported document types"""
    AADHAR = "aadhar"
    PAN = "pan"
    VOTER_ID = "voter_id"
    DRIVING_LICENSE = "driving_license"
    PASSPORT = "passport"
    BANK_STATEMENT = "bank_statement"
    CERTIFICATE = "certificate"
    INCOME_CERTIFICATE = "income_certificate"


class ValidationStatus(Enum):
    """Validation status indicators"""
    VALID = "valid"
    INVALID = "invalid"
    PARTIAL = "partial"  # Some fields extracted but unconfirmed
    UNCLEAR = "unclear"  # Image quality issues


class DocumentValidator:
    """
    Validates documents and form fields
    
    Approach:
    1. Identify document type by visual features/text
    2. Extract fields using OCR-like patterns
    3. Validate extracted data against constraints
    4. Return validation status with confidence
    5. Suggest corrections for invalid fields
    """
    
    # Validation patterns for different field types
    VALIDATION_RULES = {
        "aadhar": {
            "pattern": r"^\d{12}$",
            "format_func": lambda x: f"{x[0:4]} {x[4:8]} {x[8:12]}",
            "description": "12-digit Aadhar number",
            "constraints": {
                "length": 12,
                "numeric_only": True,
            }
        },
        "pan": {
            "pattern": r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$",
            "format_func": lambda x: x.upper(),
            "description": "10-character PAN",
            "constraints": {
                "length": 10,
                "format": "5 letters, 4 digits, 1 letter",
            }
        },
        "email": {
            "pattern": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "format_func": lambda x: x.lower().strip(),
            "description": "Valid email address",
            "constraints": {
                "max_length": 254,
            }
        },
        "phone": {
            "pattern": r"^[6-9]\d{9}$",
            "format_func": lambda x: re.sub(r"\D", "", x)[-10:],
            "description": "10-digit Indian mobile number",
            "constraints": {
                "length": 10,
                "starts_with": ["6", "7", "8", "9"],
            }
        },
        "date_dob": {
            "pattern": r"^\d{1,2}[/-]\d{1,2}[/-]\d{4}$",
            "format_func": lambda x: re.sub(r"[/-]", "-", x),
            "description": "Date in DD/MM/YYYY format",
            "constraints": {
                "min_age": 18,
                "max_age": 80,
            }
        },
        "voter_id": {
            "pattern": r"^[A-Z]{3}\d{7}$",
            "format_func": lambda x: x.upper(),
            "description": "3 letters + 7 digits",
            "constraints": {
                "length": 10,
            }
        },
        "driving_license": {
            "pattern": r"^[A-Z]{2}\d{13}$",
            "format_func": lambda x: x.upper(),
            "description": "2 letters + 13 digits",
            "constraints": {
                "length": 15,
            }
        },
    }
    
    # Document type recognition patterns
    DOCUMENT_PATTERNS = {
        DocumentType.AADHAR: {
            "keywords": ["आधार", "aadhar", "uidai", "enrollment"],
            "field_names": ["आधार संख्या", "aadhar number", "UID", "enrolment id"],
        },
        DocumentType.PAN: {
            "keywords": ["pan", "income tax", "नियंत्रक", "department of income tax"],
            "field_names": ["permanent account number", "pan number"],
        },
        DocumentType.VOTER_ID: {
            "keywords": ["voter", "electoral", "निर्वाचन", "election"],
            "field_names": ["voter id", "epic number", "roll number"],
        },
        DocumentType.DRIVING_LICENSE: {
            "keywords": ["driving license", "dl", "license number", "transport"],
            "field_names": ["license number", "registration number"],
        },
        DocumentType.PASSPORT: {
            "keywords": ["passport", "पासपोर्ट", "government of india"],
            "field_names": ["passport number", "पासपोर्ट नंबर"],
        },
        DocumentType.INCOME_CERTIFICATE: {
            "keywords": ["income", "certificate", "आय", "प्रमाणपत्र"],
            "field_names": ["annual income", "total income", "वार्षिक आय"],
        },
    }
    
    def __init__(self):
        self.confidence_threshold = 0.7
    
    def identify_document_type(self, text: str, keywords: List[str] = None) -> Tuple[Optional[DocumentType], float]:
        """
        Identify document type from OCR text
        
        Returns:
            (document_type, confidence_score)
        """
        if not text:
            return None, 0.0
        
        text_lower = text.lower()
        scores = {}
        
        for doc_type, patterns in self.DOCUMENT_PATTERNS.items():
            score = 0.0
            
            # Check keywords
            keywords_list = patterns.get("keywords", [])
            keyword_matches = sum(1 for kw in keywords_list if kw.lower() in text_lower)
            
            if keyword_matches > 0:
                score += (keyword_matches / len(keywords_list)) * 0.6
            
            # Check field names
            field_names = patterns.get("field_names", [])
            field_matches = sum(1 for fn in field_names if fn.lower() in text_lower)
            
            if field_matches > 0:
                score += (field_matches / len(field_names)) * 0.4
            
            scores[doc_type] = score
        
        if not scores:
            return None, 0.0
        
        best_doc_type = max(scores, key=scores.get)
        best_score = scores[best_doc_type]
        
        return best_doc_type, best_score
    
    def extract_fields_from_text(self, text: str, document_type: DocumentType = None) -> Dict[str, Any]:
        """
        Extract fields from document text using patterns
        """
        if not text:
            return {}
        
        extracted = {}
        
        # Extract Aadhar (12 digits in sequence)
        aadhar_match = re.search(r'\b(\d{4}\s?\d{4}\s?\d{4}|\d{12})\b', text)
        if aadhar_match:
            aadhar = re.sub(r'\s', '', aadhar_match.group(1))
            if len(aadhar) == 12:
                extracted["aadhar"] = aadhar
        
        # Extract PAN
        pan_match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z]{1})\b', text)
        if pan_match:
            extracted["pan"] = pan_match.group(1)
        
        # Extract email
        email_match = re.search(r'\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b', text)
        if email_match:
            extracted["email"] = email_match.group(0)
        
        # Extract phone
        phone_match = re.search(r'\b[6-9]\d{9}\b', text)
        if phone_match:
            extracted["phone"] = phone_match.group(0)
        
        # Extract dates (DD/MM/YYYY format)
        date_matches = re.findall(r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{4})\b', text)
        if date_matches:
            extracted["dates"] = date_matches
        
        # Extract voter ID
        voter_match = re.search(r'\b([A-Z]{3}\d{7})\b', text)
        if voter_match:
            extracted["voter_id"] = voter_match.group(1)
        
        # Extract driving license
        dl_match = re.search(r'\b([A-Z]{2}\d{13})\b', text)
        if dl_match:
            extracted["driving_license"] = dl_match.group(1)
        
        return extracted
    
    def validate_field(self, field_type: str, value: str) -> Tuple[bool, Optional[str], Dict[str, str]]:
        """
        Validate a single field
        
        Returns:
            (is_valid, formatted_value, message_dict with en/hi/bilingual)
        """
        if not value or field_type not in self.VALIDATION_RULES:
            return False, None, {
                "en": f"Unknown field type: {field_type}",
                "hi": f"अज्ञात फ़ील्ड प्रकार: {field_type}",
                "bilingual": f"Unknown field type: {field_type} / अज्ञात फ़ील्ड प्रकार: {field_type}"
            }
        
        rules = self.VALIDATION_RULES[field_type]
        pattern = rules.get("pattern", "")
        
        # Clean input
        clean_value = str(value).strip()
        
        # Get bilingual message for this field type
        msg = VALIDATION_MESSAGES.get(field_type, {
            "success": {"en": "Valid", "hi": "वैध"},
            "error": {"en": "Invalid", "hi": "अवैध"}
        })
        
        # Check pattern
        if pattern and not re.match(pattern, clean_value):
            return False, None, {
                "en": msg["error"]["en"],
                "hi": msg["error"]["hi"],
                "bilingual": f"{msg['error']['en']} / {msg['error']['hi']}"
            }
        
        # Apply format function
        formatted_value = clean_value
        if "format_func" in rules:
            try:
                formatted_value = rules["format_func"](clean_value)
            except Exception as e:
                return False, None, {
                    "en": f"Error formatting value: {str(e)}",
                    "hi": f"मान स्वरूपित करने में त्रुटि: {str(e)}",
                    "bilingual": f"Error: {str(e)} / त्रुटि: {str(e)}"
                }
        
        # Validate constraints
        constraints = rules.get("constraints", {})
        
        if "length" in constraints:
            if len(re.sub(r'\D', '', clean_value)) != constraints["length"]:
                return False, None, {
                    "en": f"Length should be {constraints['length']}",
                    "hi": f"लंबाई {constraints['length']} होनी चाहिए",
                    "bilingual": f"Length should be {constraints['length']} / लंबाई {constraints['length']} होनी चाहिए"
                }
        
        if "numeric_only" in constraints and constraints["numeric_only"]:
            if not re.match(r'^\d+$', clean_value):
                return False, None, {
                    "en": "Only digits allowed",
                    "hi": "केवल अंक अनुमत हैं",
                    "bilingual": "Only digits allowed / केवल अंक अनुमत हैं"
                }
        
        if "starts_with" in constraints:
            if not any(clean_value.startswith(prefix) for prefix in constraints["starts_with"]):
                return False, None, {
                    "en": f"Must start with {', '.join(constraints['starts_with'])}",
                    "hi": f"{', '.join(constraints['starts_with'])} से शुरू होना चाहिए",
                    "bilingual": f"Must start with {', '.join(constraints['starts_with'])} / {', '.join(constraints['starts_with'])} से शुरू होना चाहिए"
                }
        
        if "max_length" in constraints:
            if len(clean_value) > constraints["max_length"]:
                return False, None, {
                    "en": f"Maximum length is {constraints['max_length']}",
                    "hi": f"अधिकतम लंबाई {constraints['max_length']} है",
                    "bilingual": f"Maximum length is {constraints['max_length']} / अधिकतम लंबाई {constraints['max_length']} है"
                }
        
        # Success
        return True, formatted_value, {
            "en": msg["success"]["en"],
            "hi": msg["success"]["hi"],
            "bilingual": f"{msg['success']['en']} / {msg['success']['hi']}"
        }
    
    def validate_form_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate multiple form fields
        
        Returns:
            {
                "is_valid": bool,
                "fields": {
                    "field_name": {
                        "value": "...",
                        "valid": bool,
                        "error": "..."
                    }
                },
                "summary": "X valid, Y invalid"
            }
        """
        results = {
            "is_valid": True,
            "fields": {},
            "valid_count": 0,
            "invalid_count": 0,
            "errors": []
        }
        
        for field_name, value in fields.items():
            is_valid, formatted_value, error = self.validate_field(field_name, value)
            
            results["fields"][field_name] = {
                "original_value": value,
                "formatted_value": formatted_value,
                "valid": is_valid,
                "error": error,
            }
            
            if is_valid:
                results["valid_count"] += 1
            else:
                results["invalid_count"] += 1
                results["is_valid"] = False
                if error:
                    results["errors"].append(f"{field_name}: {error}")
        
        results["summary"] = f"{results['valid_count']} valid, {results['invalid_count']} invalid"
        
        return results
    
    def validate_age_from_dob(self, dob: str, min_age: int = 18, max_age: int = 80) -> Tuple[bool, Optional[int], str]:
        """
        Validate age from DOB
        
        Returns:
            (is_valid, age, message)
        """
        try:
            # Parse date
            date_parts = re.split(r'[/-]', dob)
            if len(date_parts) != 3:
                return False, None, "Invalid date format"
            
            day, month, year = int(date_parts[0]), int(date_parts[1]), int(date_parts[2])
            
            # Validate month and day
            if month < 1 or month > 12:
                return False, None, "Invalid month"
            
            if day < 1 or day > 31:
                return False, None, "Invalid day"
            
            # Calculate age (simplified)
            from datetime import datetime
            today = datetime.now()
            birth_year = int(year) if year > 1900 else 2000 + int(year)
            
            age = today.year - birth_year
            
            if age < min_age or age > max_age:
                return False, age, f"Age must be between {min_age} and {max_age}"
            
            return True, age, "Valid"
        
        except Exception as e:
            return False, None, f"Error validating age: {str(e)}"
    
    def validate_document(self, document_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate complete document
        
        document_data should contain:
        - ocr_text: Extracted text from document
        - fields: Dictionary of extracted fields
        - document_type: (Optional) Known document type
        """
        result = {
            "document_type": None,
            "type_confidence": 0.0,
            "extraction_status": ValidationStatus.UNCLEAR.value,
            "fields_validation": {},
            "overall_status": ValidationStatus.UNCLEAR.value,
            "quality_score": 0.0,
            "issues": [],
        }
        
        ocr_text = document_data.get("ocr_text", "")
        fields = document_data.get("fields", {})
        
        # Identify document type if not provided
        if not document_data.get("document_type"):
            doc_type, confidence = self.identify_document_type(ocr_text)
            result["document_type"] = doc_type.value if doc_type else None
            result["type_confidence"] = confidence
        else:
            result["document_type"] = document_data.get("document_type")
        
        # Extract fields from OCR if not provided
        if not fields:
            fields = self.extract_fields_from_text(ocr_text, result["document_type"])
        
        # Validate extracted fields
        if fields:
            validation_results = self.validate_form_fields(fields)
            result["fields_validation"] = validation_results["fields"]
            
            if validation_results["valid_count"] > 0:
                result["extraction_status"] = ValidationStatus.PARTIAL.value
            
            if validation_results["is_valid"]:
                result["overall_status"] = ValidationStatus.VALID.value
            else:
                result["issues"] = validation_results["errors"]
                result["overall_status"] = ValidationStatus.INVALID.value
        else:
            result["issues"].append("No fields extracted from document")
        
        # Calculate quality score
        quality_score = 0.0
        if result["type_confidence"] > 0.7:
            quality_score += 0.5
        if result["extraction_status"] != ValidationStatus.UNCLEAR.value:
            quality_score += 0.3
        if not result["issues"]:
            quality_score += 0.2
        
        result["quality_score"] = round(quality_score, 2)
        
        return result
