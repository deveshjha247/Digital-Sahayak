"""
Form Field Data Collector
Scrapes HTML forms from government sites and labels input fields with semantic tags
Logs operator corrections for continuous improvement
"""

import json
import logging
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class FieldSemanticTag(Enum):
    """Semantic tags for form fields (Indian government forms)"""
    
    # Personal Info
    APPLICANT_NAME = "applicant_name"
    FATHER_NAME = "father_name"
    MOTHER_NAME = "mother_name"
    SPOUSE_NAME = "spouse_name"
    DATE_OF_BIRTH = "date_of_birth"
    AGE = "age"
    GENDER = "gender"
    MARITAL_STATUS = "marital_status"
    NATIONALITY = "nationality"
    RELIGION = "religion"
    
    # Caste & Category
    CASTE = "caste"
    CASTE_CATEGORY = "caste_category"  # SC/ST/OBC/General
    SUB_CASTE = "sub_caste"
    
    # Identity Documents
    AADHAR_NUMBER = "aadhar_number"
    PAN_NUMBER = "pan_number"
    VOTER_ID = "voter_id"
    DRIVING_LICENSE = "driving_license"
    PASSPORT_NUMBER = "passport_number"
    RATION_CARD = "ration_card"
    
    # Contact Info
    MOBILE_NUMBER = "mobile_number"
    ALTERNATE_MOBILE = "alternate_mobile"
    EMAIL = "email"
    
    # Address - Permanent
    ADDRESS_LINE1 = "address_line1"
    ADDRESS_LINE2 = "address_line2"
    VILLAGE = "village"
    POST_OFFICE = "post_office"
    POLICE_STATION = "police_station"
    TEHSIL = "tehsil"
    DISTRICT = "district"
    STATE = "state"
    PINCODE = "pincode"
    
    # Address - Current/Correspondence
    CURRENT_ADDRESS = "current_address"
    CURRENT_DISTRICT = "current_district"
    CURRENT_STATE = "current_state"
    CURRENT_PINCODE = "current_pincode"
    
    # Education
    QUALIFICATION = "qualification"
    DEGREE = "degree"
    UNIVERSITY = "university"
    BOARD = "board"
    PASSING_YEAR = "passing_year"
    PERCENTAGE = "percentage"
    CGPA = "cgpa"
    ROLL_NUMBER = "roll_number"
    SPECIALIZATION = "specialization"
    
    # Employment
    OCCUPATION = "occupation"
    EMPLOYER_NAME = "employer_name"
    DESIGNATION = "designation"
    EXPERIENCE_YEARS = "experience_years"
    SALARY = "salary"
    EMPLOYEE_ID = "employee_id"
    
    # Bank Details
    BANK_NAME = "bank_name"
    BRANCH_NAME = "branch_name"
    ACCOUNT_NUMBER = "account_number"
    IFSC_CODE = "ifsc_code"
    ACCOUNT_TYPE = "account_type"
    
    # Income & Economic
    ANNUAL_INCOME = "annual_income"
    FAMILY_INCOME = "family_income"
    BPL_STATUS = "bpl_status"
    LAND_HOLDING = "land_holding"
    
    # Physical Details
    HEIGHT = "height"
    WEIGHT = "weight"
    BLOOD_GROUP = "blood_group"
    DISABILITY_TYPE = "disability_type"
    DISABILITY_PERCENTAGE = "disability_percentage"
    
    # Photo & Signature
    PHOTO = "photo"
    SIGNATURE = "signature"
    THUMB_IMPRESSION = "thumb_impression"
    
    # Documents
    CERTIFICATE_NUMBER = "certificate_number"
    ISSUE_DATE = "issue_date"
    VALID_UNTIL = "valid_until"
    ISSUING_AUTHORITY = "issuing_authority"
    
    # Application Specific
    APPLICATION_NUMBER = "application_number"
    REGISTRATION_NUMBER = "registration_number"
    EXAM_CENTER = "exam_center"
    PREFERRED_LANGUAGE = "preferred_language"
    
    # Other
    CAPTCHA = "captcha"
    OTP = "otp"
    PASSWORD = "password"
    CONFIRM_PASSWORD = "confirm_password"
    REMARKS = "remarks"
    DECLARATION = "declaration"
    UNKNOWN = "unknown"


class FormFieldCollector:
    """
    Collects and labels form fields from government websites
    
    Features:
    - Extracts field metadata (label, id, name, type, placeholder)
    - Maps to semantic tags
    - Logs operator corrections for ground truth
    - Supports Hindi and English labels
    """
    
    # Pattern to tag mapping
    FIELD_PATTERNS = {
        # Name fields
        r"(applicant|candidate|your)\s*(name|नाम)": FieldSemanticTag.APPLICANT_NAME,
        r"(father|पिता)\s*(name|नाम|का नाम)": FieldSemanticTag.FATHER_NAME,
        r"(mother|माता)\s*(name|नाम|का नाम)": FieldSemanticTag.MOTHER_NAME,
        r"(spouse|husband|wife|पति|पत्नी)\s*(name|नाम)": FieldSemanticTag.SPOUSE_NAME,
        
        # DOB & Age
        r"(date\s*of\s*birth|dob|जन्म\s*तिथि|जन्मतिथि)": FieldSemanticTag.DATE_OF_BIRTH,
        r"^age$|^आयु$|^उम्र$": FieldSemanticTag.AGE,
        
        # Gender
        r"(gender|sex|लिंग)": FieldSemanticTag.GENDER,
        
        # Category
        r"(caste|जाति)\s*(category|वर्ग)?": FieldSemanticTag.CASTE_CATEGORY,
        r"(category|वर्ग)\s*(sc|st|obc|general)?": FieldSemanticTag.CASTE_CATEGORY,
        
        # Identity
        r"(aadhar|aadhaar|आधार)\s*(number|no|संख्या|नंबर)?": FieldSemanticTag.AADHAR_NUMBER,
        r"(pan)\s*(number|no|card)?": FieldSemanticTag.PAN_NUMBER,
        r"(voter|epic)\s*(id|number)?": FieldSemanticTag.VOTER_ID,
        
        # Contact
        r"(mobile|phone|मोबाइल|फोन)\s*(number|no|नंबर)?": FieldSemanticTag.MOBILE_NUMBER,
        r"(email|ईमेल|e-mail)": FieldSemanticTag.EMAIL,
        
        # Address
        r"(address|पता)\s*(line)?\s*1?": FieldSemanticTag.ADDRESS_LINE1,
        r"(village|गांव|ग्राम)": FieldSemanticTag.VILLAGE,
        r"(district|जिला)": FieldSemanticTag.DISTRICT,
        r"(state|राज्य|प्रदेश)": FieldSemanticTag.STATE,
        r"(pin\s*code|pincode|पिन\s*कोड)": FieldSemanticTag.PINCODE,
        
        # Education
        r"(qualification|योग्यता|शैक्षिक)": FieldSemanticTag.QUALIFICATION,
        r"(university|विश्वविद्यालय)": FieldSemanticTag.UNIVERSITY,
        r"(passing\s*year|उत्तीर्ण\s*वर्ष)": FieldSemanticTag.PASSING_YEAR,
        r"(percentage|प्रतिशत|%|marks)": FieldSemanticTag.PERCENTAGE,
        
        # Bank
        r"(bank)\s*(name|नाम)?": FieldSemanticTag.BANK_NAME,
        r"(account)\s*(number|no|नंबर)": FieldSemanticTag.ACCOUNT_NUMBER,
        r"(ifsc)\s*(code)?": FieldSemanticTag.IFSC_CODE,
        
        # Income
        r"(annual|yearly|वार्षिक)\s*(income|आय)": FieldSemanticTag.ANNUAL_INCOME,
        r"(family)\s*(income|आय)": FieldSemanticTag.FAMILY_INCOME,
        
        # Photo/Signature
        r"(photo|photograph|फोटो|चित्र)": FieldSemanticTag.PHOTO,
        r"(signature|हस्ताक्षर)": FieldSemanticTag.SIGNATURE,
        
        # Security
        r"(captcha|कैप्चा)": FieldSemanticTag.CAPTCHA,
        r"(otp|ओटीपी)": FieldSemanticTag.OTP,
        r"(password|पासवर्ड)": FieldSemanticTag.PASSWORD,
    }
    
    def __init__(self, data_dir: str = "data/training/form_fields"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data files
        self.forms_file = self.data_dir / "forms.jsonl"
        self.fields_file = self.data_dir / "fields.jsonl"
        self.corrections_file = self.data_dir / "corrections.jsonl"
        self.labels_file = self.data_dir / "labeled_fields.jsonl"
        
        self.stats = {
            "forms_collected": 0,
            "fields_collected": 0,
            "corrections_logged": 0,
            "auto_labeled": 0,
        }
    
    def collect_form(
        self,
        url: str,
        html_content: str,
        form_name: str = "",
        department: str = ""
    ) -> str:
        """
        Collect a form from government website
        Parses HTML and extracts all input fields
        """
        form_id = self._generate_id(url)
        
        # Extract fields from HTML
        fields = self._parse_html_fields(html_content)
        
        form_record = {
            "form_id": form_id,
            "url": url,
            "form_name": form_name,
            "department": department,
            "total_fields": len(fields),
            "collected_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.forms_file, form_record)
        self.stats["forms_collected"] += 1
        
        # Store each field
        for field in fields:
            self.collect_field(form_id, field)
        
        return form_id
    
    def collect_field(self, form_id: str, field_data: Dict) -> str:
        """
        Collect a single form field with its metadata
        """
        field_id = self._generate_id(
            form_id + field_data.get("name", "") + field_data.get("id", "")
        )
        
        # Auto-label based on patterns
        auto_tag, confidence = self._auto_label_field(field_data)
        
        field_record = {
            "field_id": field_id,
            "form_id": form_id,
            
            # HTML attributes
            "tag": field_data.get("tag", "input"),
            "type": field_data.get("type", "text"),
            "name": field_data.get("name", ""),
            "id": field_data.get("id", ""),
            "class": field_data.get("class", ""),
            "placeholder": field_data.get("placeholder", ""),
            "label_text": field_data.get("label_text", ""),
            "surrounding_text": field_data.get("surrounding_text", ""),
            
            # Validation attributes
            "required": field_data.get("required", False),
            "maxlength": field_data.get("maxlength"),
            "minlength": field_data.get("minlength"),
            "pattern": field_data.get("pattern"),
            
            # Auto-labeling
            "auto_tag": auto_tag.value if auto_tag else None,
            "auto_confidence": confidence,
            
            # Will be filled by operator
            "manual_tag": None,
            "verified": False,
            
            "collected_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.fields_file, field_record)
        self.stats["fields_collected"] += 1
        
        if auto_tag:
            self.stats["auto_labeled"] += 1
        
        return field_id
    
    def log_operator_correction(
        self,
        field_id: str,
        original_tag: str,
        corrected_tag: str,
        operator_id: str,
        notes: str = ""
    ):
        """
        Log when an operator corrects an auto-labeled field
        This is GOLD DATA for improving the model
        """
        correction = {
            "field_id": field_id,
            "original_tag": original_tag,
            "corrected_tag": corrected_tag,
            "operator_id": operator_id,
            "notes": notes,
            "timestamp": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.corrections_file, correction)
        self.stats["corrections_logged"] += 1
        
        logger.info(f"Correction logged: {original_tag} -> {corrected_tag}")
        
        return correction
    
    def verify_field_label(
        self,
        field_id: str,
        semantic_tag: str,
        operator_id: str
    ):
        """
        Operator verifies a field label (confirms auto-label or provides correct one)
        """
        labeled_field = {
            "field_id": field_id,
            "semantic_tag": semantic_tag,
            "verified_by": operator_id,
            "verified_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.labels_file, labeled_field)
        
        return labeled_field
    
    def _parse_html_fields(self, html_content: str) -> List[Dict]:
        """
        Parse HTML and extract form fields
        Note: In production, use BeautifulSoup
        """
        fields = []
        
        # Simple regex patterns for demo
        # In production, use proper HTML parser
        
        # Find input fields
        input_pattern = r'<input([^>]*)>'
        for match in re.finditer(input_pattern, html_content, re.IGNORECASE):
            attrs = match.group(1)
            field = self._parse_attributes(attrs)
            field["tag"] = "input"
            fields.append(field)
        
        # Find textarea
        textarea_pattern = r'<textarea([^>]*)>'
        for match in re.finditer(textarea_pattern, html_content, re.IGNORECASE):
            attrs = match.group(1)
            field = self._parse_attributes(attrs)
            field["tag"] = "textarea"
            fields.append(field)
        
        # Find select
        select_pattern = r'<select([^>]*)>'
        for match in re.finditer(select_pattern, html_content, re.IGNORECASE):
            attrs = match.group(1)
            field = self._parse_attributes(attrs)
            field["tag"] = "select"
            fields.append(field)
        
        return fields
    
    def _parse_attributes(self, attr_string: str) -> Dict:
        """Parse HTML attributes from string"""
        field = {}
        
        # Parse common attributes
        patterns = {
            "type": r'type\s*=\s*["\']([^"\']*)["\']',
            "name": r'name\s*=\s*["\']([^"\']*)["\']',
            "id": r'id\s*=\s*["\']([^"\']*)["\']',
            "class": r'class\s*=\s*["\']([^"\']*)["\']',
            "placeholder": r'placeholder\s*=\s*["\']([^"\']*)["\']',
            "maxlength": r'maxlength\s*=\s*["\']?(\d+)["\']?',
            "minlength": r'minlength\s*=\s*["\']?(\d+)["\']?',
            "pattern": r'pattern\s*=\s*["\']([^"\']*)["\']',
        }
        
        for key, pattern in patterns.items():
            match = re.search(pattern, attr_string, re.IGNORECASE)
            if match:
                field[key] = match.group(1)
        
        # Check for required attribute
        field["required"] = "required" in attr_string.lower()
        
        return field
    
    def _auto_label_field(self, field: Dict) -> Tuple[Optional[FieldSemanticTag], float]:
        """
        Auto-label field based on patterns
        Returns (tag, confidence)
        """
        # Combine all text sources
        text_sources = [
            field.get("name", ""),
            field.get("id", ""),
            field.get("placeholder", ""),
            field.get("label_text", ""),
            field.get("surrounding_text", ""),
        ]
        
        combined_text = " ".join(text_sources).lower()
        
        if not combined_text.strip():
            return None, 0.0
        
        # Check against patterns
        best_match = None
        best_confidence = 0.0
        
        for pattern, tag in self.FIELD_PATTERNS.items():
            if re.search(pattern, combined_text, re.IGNORECASE):
                # Calculate confidence based on match quality
                confidence = 0.7  # Base confidence for pattern match
                
                # Boost if multiple attributes match
                match_count = sum(
                    1 for src in text_sources 
                    if src and re.search(pattern, src, re.IGNORECASE)
                )
                confidence += match_count * 0.1
                
                if confidence > best_confidence:
                    best_match = tag
                    best_confidence = min(confidence, 1.0)
        
        return best_match, best_confidence
    
    def _generate_id(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _append_jsonl(self, filepath: Path, record: Dict):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _read_jsonl(self, filepath: Path) -> List[Dict]:
        if not filepath.exists():
            return []
        
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
    
    def get_stats(self) -> Dict:
        return self.stats
    
    def export_training_data(self, output_file: str = None) -> str:
        """
        Export labeled fields for training field classifier model
        Format: (field_features, semantic_tag)
        """
        if not output_file:
            output_file = str(self.data_dir / "training_dataset.jsonl")
        
        fields = self._read_jsonl(self.fields_file)
        labels = {l["field_id"]: l["semantic_tag"] for l in self._read_jsonl(self.labels_file)}
        
        with open(output_file, "w", encoding="utf-8") as f:
            for field in fields:
                field_id = field["field_id"]
                
                # Use verified label if available, otherwise auto_tag
                semantic_tag = labels.get(field_id) or field.get("auto_tag")
                
                if not semantic_tag:
                    continue
                
                training_example = {
                    "features": {
                        "name": field.get("name", ""),
                        "id": field.get("id", ""),
                        "placeholder": field.get("placeholder", ""),
                        "label_text": field.get("label_text", ""),
                        "type": field.get("type", "text"),
                        "required": field.get("required", False),
                        "maxlength": field.get("maxlength"),
                    },
                    "semantic_tag": semantic_tag,
                    "verified": field_id in labels,
                }
                
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file
