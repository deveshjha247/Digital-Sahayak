"""
Field Classifier AI Module
Identifies form field types and maps user data to form fields

Architecture (CNN + Transformer + Rules):
1. Field Detection (CNN): Detect form fields on scanned PDFs using CNN
2. Label Understanding (Transformer): Process field labels with BERT/RoBERTa
3. Data Mapping (Rules): Match user profile keys to form fields

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- All field labels and validation messages are pre-defined bilingually

Dependencies (optional for ML mode):
- transformers (for BERT label understanding)
- torch/tensorflow (for CNN field detection)
- Pillow (for image processing)
"""

import logging
import re
import os
import json
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
from pathlib import Path

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
        
        # Generate helpful error message (bilingual)
        error_messages = {
            FieldType.EMAIL: {
                "en": "Invalid email format",
                "hi": "गलत ईमेल प्रारूप"
            },
            FieldType.PHONE: {
                "en": "Invalid phone number",
                "hi": "गलत फोन नंबर"
            },
            FieldType.MOBILE: {
                "en": "Mobile should be 10 digits starting with 6-9",
                "hi": "मोबाइल 10 अंकों का होना चाहिए (6-9 से शुरू)"
            },
            FieldType.AADHAR: {
                "en": "Aadhar should be 12 digits",
                "hi": "आधार 12 अंकों का होना चाहिए"
            },
            FieldType.PAN: {
                "en": "PAN format: 5 letters + 4 digits + 1 letter",
                "hi": "पैन प्रारूप: 5 अक्षर + 4 अंक + 1 अक्षर"
            },
            FieldType.PINCODE: {
                "en": "Pincode should be 6 digits",
                "hi": "पिनकोड 6 अंकों का होना चाहिए"
            },
            FieldType.DOB: {
                "en": "Date format: DD/MM/YYYY or YYYY-MM-DD",
                "hi": "तारीख प्रारूप: DD/MM/YYYY या YYYY-MM-DD"
            },
        }
        
        error_data = error_messages.get(field_type, {
            "en": f"Invalid {field_type}",
            "hi": f"अमान्य {field_type}"
        })
        
        # Return bilingual error message
        return False, {
            "en": error_data["en"],
            "hi": error_data["hi"],
            "bilingual": f"{error_data['en']} / {error_data['hi']}"
        }


# ==============================================================================
# Advanced ML Components (CNN + Transformer)
# ==============================================================================

class TransformerLabelUnderstanding:
    """
    Transformer-based field label understanding
    Uses BERT/RoBERTa to process field labels and infer their semantic meaning
    """
    
    # Known field type embeddings (pre-computed for common fields)
    FIELD_SEMANTICS = {
        "name": ["full name", "applicant name", "candidate name", "your name", "नाम"],
        "first_name": ["first name", "given name", "पहला नाम"],
        "last_name": ["last name", "surname", "family name", "आखिरी नाम"],
        "father_name": ["father's name", "father name", "पिता का नाम"],
        "mother_name": ["mother's name", "mother name", "माता का नाम"],
        "dob": ["date of birth", "birth date", "dob", "जन्म तिथि", "जन्मदिन"],
        "age": ["age", "years old", "आयु", "उम्र"],
        "gender": ["gender", "sex", "male/female", "लिंग"],
        "email": ["email", "e-mail", "email address", "ईमेल"],
        "phone": ["phone", "telephone", "phone number", "फोन"],
        "mobile": ["mobile", "mobile number", "cell phone", "मोबाइल"],
        "address": ["address", "residential address", "पता"],
        "city": ["city", "town", "शहर"],
        "state": ["state", "province", "राज्य"],
        "pincode": ["pincode", "postal code", "zip code", "पिनकोड"],
        "aadhar": ["aadhar", "aadhaar", "uid", "aadhar number", "आधार"],
        "pan": ["pan", "pan card", "pan number", "पैन"],
        "education": ["education", "qualification", "शिक्षा", "योग्यता"],
        "income": ["income", "annual income", "salary", "आय"],
        "category": ["category", "caste", "sc/st/obc", "श्रेणी"],
        "bank_name": ["bank name", "bank", "बैंक का नाम"],
        "account_number": ["account number", "bank account", "खाता नंबर"],
        "ifsc": ["ifsc", "ifsc code", "आईएफएससी"],
    }
    
    def __init__(self, model_name: str = "bert-base-multilingual-cased", model_path: Optional[str] = None):
        self.model_name = model_name
        self.model_path = model_path
        self.model = None
        self.tokenizer = None
        self._embeddings_cache: Dict[str, Any] = {}
        self._load_model()
    
    def _load_model(self):
        """Load transformer model for label understanding"""
        try:
            from transformers import AutoModel, AutoTokenizer
            import torch
            
            if self.model_path and os.path.exists(self.model_path):
                self.model = AutoModel.from_pretrained(self.model_path)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_path)
            else:
                self.model = AutoModel.from_pretrained(self.model_name)
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            
            self.model.eval()
            logger.info(f"Loaded transformer model: {self.model_name}")
        except ImportError:
            logger.warning("transformers not installed, using rule-based label matching")
        except Exception as e:
            logger.warning(f"Could not load transformer model: {e}")
    
    def get_embedding(self, text: str) -> Optional[Any]:
        """Get embedding for a text string"""
        if not self.model or not self.tokenizer:
            return None
        
        if text in self._embeddings_cache:
            return self._embeddings_cache[text]
        
        try:
            import torch
            
            inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=128)
            with torch.no_grad():
                outputs = self.model(**inputs)
            embedding = outputs.last_hidden_state[:, 0, :].numpy()  # CLS token
            self._embeddings_cache[text] = embedding
            return embedding
        except Exception as e:
            logger.warning(f"Embedding failed: {e}")
            return None
    
    def infer_field_type(self, label: str) -> Tuple[str, float]:
        """
        Infer field type from label using transformer embeddings
        
        Returns:
            (field_type, confidence)
        """
        if self.model is None:
            # Fallback to rule-based matching
            return self._rule_based_match(label)
        
        label_embedding = self.get_embedding(label.lower())
        if label_embedding is None:
            return self._rule_based_match(label)
        
        best_match = "other"
        best_score = 0.0
        
        for field_type, examples in self.FIELD_SEMANTICS.items():
            for example in examples:
                example_embedding = self.get_embedding(example)
                if example_embedding is not None:
                    # Cosine similarity
                    import numpy as np
                    similarity = np.dot(label_embedding.flatten(), example_embedding.flatten()) / (
                        np.linalg.norm(label_embedding) * np.linalg.norm(example_embedding) + 1e-8
                    )
                    if similarity > best_score:
                        best_score = float(similarity)
                        best_match = field_type
        
        return best_match, best_score
    
    def _rule_based_match(self, label: str) -> Tuple[str, float]:
        """Fallback rule-based matching"""
        label_lower = label.lower().strip()
        for field_type, examples in self.FIELD_SEMANTICS.items():
            for example in examples:
                if example in label_lower or label_lower in example:
                    return field_type, 0.8
        return "other", 0.3


class CNNFieldDetector:
    """
    CNN-based field detection for scanned PDFs
    Detects form fields (text boxes, checkboxes, etc.) from images
    """
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self._load_model()
    
    def _load_model(self):
        """Load CNN model for field detection"""
        if self.model_path and os.path.exists(self.model_path):
            try:
                import torch
                self.model = torch.load(self.model_path)
                self.model.eval()
                logger.info("Loaded CNN field detector")
            except ImportError:
                logger.warning("PyTorch not installed, field detection unavailable")
            except Exception as e:
                logger.warning(f"Could not load CNN model: {e}")
    
    def detect_fields(self, image_path: str) -> List[Dict]:
        """
        Detect form fields in an image
        
        Returns:
            List of detected fields with bounding boxes and types
        """
        if self.model is None:
            # Fallback: use basic image processing
            return self._basic_field_detection(image_path)
        
        try:
            import torch
            from PIL import Image
            import torchvision.transforms as transforms
            
            transform = transforms.Compose([
                transforms.Resize((800, 600)),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
            ])
            
            image = Image.open(image_path).convert("RGB")
            image_tensor = transform(image).unsqueeze(0)
            
            with torch.no_grad():
                predictions = self.model(image_tensor)
            
            fields = []
            for pred in predictions:
                fields.append({
                    "bbox": pred["box"].tolist(),
                    "field_type": pred["label"],
                    "confidence": float(pred["score"])
                })
            
            return fields
        except Exception as e:
            logger.warning(f"Field detection failed: {e}")
            return self._basic_field_detection(image_path)
    
    def _basic_field_detection(self, image_path: str) -> List[Dict]:
        """Basic field detection using image processing"""
        try:
            from PIL import Image
            import numpy as np
            
            image = Image.open(image_path).convert("L")
            img_array = np.array(image)
            
            # Simple edge detection for form fields
            # This is a placeholder - real implementation would use OpenCV
            fields = []
            
            # Detect horizontal lines (potential text fields)
            height, width = img_array.shape
            for y in range(0, height, 50):
                for x in range(0, width, 100):
                    fields.append({
                        "bbox": [x, y, x + 200, y + 30],
                        "field_type": "text_field",
                        "confidence": 0.5
                    })
            
            return fields[:20]  # Limit to 20 fields
        except Exception as e:
            logger.warning(f"Basic field detection failed: {e}")
            return []


class AdvancedFieldClassifier:
    """
    Advanced Form Field Classification & Auto-Fill
    
    Three-stage pipeline:
    1. Field Detection (CNN): Detect form fields on scanned PDFs
    2. Label Understanding (Transformer): Process field labels semantically
    3. Data Mapping (Rules): Match user profile to form fields
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        use_transformer: bool = True,
        use_cnn: bool = True
    ):
        self.models_dir = Path(models_dir) if models_dir else None
        
        # Initialize components
        if use_transformer:
            transformer_path = str(self.models_dir / "field_transformer") if self.models_dir else None
            self.label_model = TransformerLabelUnderstanding(model_path=transformer_path)
        else:
            self.label_model = None
        
        if use_cnn:
            cnn_path = str(self.models_dir / "field_cnn.pt") if self.models_dir else None
            self.field_detector = CNNFieldDetector(model_path=cnn_path)
        else:
            self.field_detector = None
        
        # Rule-based fallback
        self.rule_classifier = FieldClassifier()
    
    def classify_field(self, label: str) -> Dict:
        """
        Classify a field label using transformer + rules
        
        Returns:
            Classification result with field type and confidence
        """
        # Try transformer-based classification
        if self.label_model:
            field_type, confidence = self.label_model.infer_field_type(label)
            if confidence > 0.7:
                return {
                    "field_type": field_type,
                    "confidence": confidence,
                    "method": "transformer"
                }
        
        # Fall back to rule-based
        rule_result = self.rule_classifier.classify_field(label)
        return {
            "field_type": rule_result["type"].value if hasattr(rule_result["type"], "value") else rule_result["type"],
            "confidence": rule_result["confidence"],
            "method": "rules"
        }
    
    def detect_form_fields(self, image_path: str) -> List[Dict]:
        """
        Detect and classify fields from a form image
        
        Returns:
            List of detected fields with types and positions
        """
        if self.field_detector:
            detected = self.field_detector.detect_fields(image_path)
            
            # Classify each detected field
            for field in detected:
                if "label" in field:
                    classification = self.classify_field(field["label"])
                    field["classified_type"] = classification["field_type"]
                    field["classification_confidence"] = classification["confidence"]
            
            return detected
        
        return []
    
    def auto_fill_form(self, fields: List[Dict], user_profile: Dict) -> Dict[str, str]:
        """
        Auto-fill form fields from user profile
        
        Args:
            fields: List of field definitions with types
            user_profile: User profile data
            
        Returns:
            Mapping of field IDs to values
        """
        filled_values = {}
        
        # Profile to field type mapping
        profile_mapping = {
            "name": ["name", "full_name"],
            "first_name": ["first_name"],
            "last_name": ["last_name"],
            "father_name": ["father_name"],
            "mother_name": ["mother_name"],
            "email": ["email"],
            "phone": ["phone", "telephone"],
            "mobile": ["mobile", "phone"],
            "dob": ["dob", "date_of_birth", "birth_date"],
            "age": ["age"],
            "gender": ["gender", "sex"],
            "address": ["address", "full_address"],
            "city": ["city"],
            "state": ["state"],
            "district": ["district"],
            "pincode": ["pincode", "postal_code"],
            "aadhar": ["aadhar_number", "aadhar", "uid"],
            "pan": ["pan_number", "pan"],
            "education": ["education", "qualification"],
            "category": ["category", "caste"],
            "income": ["income", "annual_income"],
            "bank_name": ["bank_name", "bank"],
            "account_number": ["account_number", "bank_account"],
            "ifsc": ["ifsc_code", "ifsc"],
        }
        
        for field in fields:
            field_type = field.get("classified_type") or field.get("field_type", "").lower()
            field_id = field.get("id", field.get("name", ""))
            
            # Find matching profile field
            for profile_key, field_types in profile_mapping.items():
                if field_type in field_types or profile_key in field_type:
                    value = user_profile.get(profile_key)
                    if value:
                        # Format value based on field type
                        filled_values[field_id] = self._format_value(value, field_type)
                        break
        
        return filled_values
    
    def _format_value(self, value: Any, field_type: str) -> str:
        """Format value based on field type"""
        if field_type in ["phone", "mobile"]:
            # Format phone number
            digits = re.sub(r'\D', '', str(value))
            if len(digits) == 10:
                return digits
            elif len(digits) == 12 and digits.startswith("91"):
                return digits[2:]
        
        if field_type == "aadhar":
            # Format Aadhar: XXXX XXXX XXXX
            digits = re.sub(r'\D', '', str(value))
            if len(digits) == 12:
                return f"{digits[:4]} {digits[4:8]} {digits[8:]}"
        
        if field_type in ["dob", "date_of_birth"]:
            # Ensure DD/MM/YYYY format
            if isinstance(value, str):
                return value
        
        return str(value)
    
    def process_form(self, image_path: str, user_profile: Dict) -> Dict:
        """
        Complete form processing pipeline
        
        Args:
            image_path: Path to form image
            user_profile: User profile data
            
        Returns:
            Processing result with detected fields and auto-fill suggestions
        """
        # Detect fields
        fields = self.detect_form_fields(image_path)
        
        # Auto-fill
        filled = self.auto_fill_form(fields, user_profile)
        
        return {
            "detected_fields": fields,
            "auto_fill": filled,
            "unmapped_fields": [
                f for f in fields 
                if f.get("id", f.get("name")) not in filled
            ]
        }


# Convenience function for API integration
def classify_field(label: str, use_ml: bool = False, models_dir: Optional[str] = None) -> Dict:
    """
    Classify a form field label
    
    Args:
        label: Field label text
        use_ml: Use ML-based classification
        models_dir: Directory with trained models
        
    Returns:
        Classification result with field type and confidence
    """
    if use_ml:
        classifier = AdvancedFieldClassifier(models_dir=models_dir)
        return classifier.classify_field(label)
    else:
        classifier = FieldClassifier()
        result = classifier.classify_field(label)
        return {
            "field_type": result["type"].value if hasattr(result["type"], "value") else str(result["type"]),
            "confidence": result["confidence"],
            "method": "rules"
        }


def auto_fill_form(fields: List[Dict], user_profile: Dict, use_ml: bool = False) -> Dict[str, str]:
    """
    Auto-fill form fields from user profile
    
    Args:
        fields: List of field definitions
        user_profile: User profile data
        use_ml: Use ML-based field classification
        
    Returns:
        Mapping of field IDs to values
    """
    classifier = AdvancedFieldClassifier() if use_ml else FieldClassifier()
    
    if hasattr(classifier, 'auto_fill_form'):
        return classifier.auto_fill_form(fields, user_profile)
    else:
        return classifier.map_profile_to_fields(user_profile, fields)
