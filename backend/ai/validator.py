"""
Document & Field Validator AI Module
Validates documents, form fields, and user data

Architecture (OCR + CNN + Rules):
1. OCR: Tesseract/EasyOCR for text extraction from documents
2. CNN: Lightweight Vision model for document type/quality detection
3. Rules: Domain-specific validation (Aadhar, PAN, dates, etc.)

Language Support:
- Primary: English (en)
- Secondary: Hindi (hi)
- All validation messages are pre-defined bilingually

Dependencies (optional for ML mode):
- pytesseract/easyocr (for OCR)
- torch/torchvision (for CNN document classification)
- Pillow (for image processing)
"""

import logging
import re
import os
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

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


# ==============================================================================
# Advanced ML Components (OCR + CNN Document Validation)
# ==============================================================================

class TesseractOCR:
    """
    Tesseract OCR for text extraction from documents
    Supports Hindi and English text extraction
    """
    
    def __init__(self, lang: str = "hin+eng"):
        self.lang = lang
        self.tesseract_available = self._check_tesseract()
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract is installed"""
        try:
            import pytesseract
            pytesseract.get_tesseract_version()
            return True
        except ImportError:
            logger.warning("pytesseract not installed")
            return False
        except Exception as e:
            logger.warning(f"Tesseract not found: {e}")
            return False
    
    def extract_text(self, image_path: str) -> str:
        """
        Extract text from image using Tesseract
        
        Args:
            image_path: Path to image file
            
        Returns:
            Extracted text
        """
        if not self.tesseract_available:
            return self._fallback_extraction(image_path)
        
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            text = pytesseract.image_to_string(image, lang=self.lang)
            return text.strip()
            
        except Exception as e:
            logger.warning(f"OCR failed: {e}")
            return self._fallback_extraction(image_path)
    
    def extract_structured(self, image_path: str) -> Dict:
        """
        Extract structured text with bounding boxes
        
        Returns:
            Dictionary with text blocks and positions
        """
        if not self.tesseract_available:
            return {"text": self._fallback_extraction(image_path), "blocks": []}
        
        try:
            import pytesseract
            from PIL import Image
            
            image = Image.open(image_path)
            
            # Get detailed OCR data
            data = pytesseract.image_to_data(image, lang=self.lang, output_type=pytesseract.Output.DICT)
            
            blocks = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    blocks.append({
                        "text": data["text"][i],
                        "bbox": [
                            data["left"][i],
                            data["top"][i],
                            data["left"][i] + data["width"][i],
                            data["top"][i] + data["height"][i]
                        ],
                        "confidence": data["conf"][i]
                    })
            
            full_text = " ".join(b["text"] for b in blocks)
            return {"text": full_text, "blocks": blocks}
            
        except Exception as e:
            logger.warning(f"Structured OCR failed: {e}")
            return {"text": "", "blocks": []}
    
    def _fallback_extraction(self, image_path: str) -> str:
        """Fallback when Tesseract unavailable"""
        # Return empty - in production you'd use an alternative
        return ""


class EasyOCRExtractor:
    """
    EasyOCR alternative for text extraction
    Better multilingual support than Tesseract
    """
    
    def __init__(self, languages: List[str] = ["en", "hi"]):
        self.languages = languages
        self.reader = None
        self._load_model()
    
    def _load_model(self):
        """Load EasyOCR reader"""
        try:
            import easyocr
            self.reader = easyocr.Reader(self.languages, gpu=False)
            logger.info("Loaded EasyOCR reader")
        except ImportError:
            logger.warning("easyocr not installed")
        except Exception as e:
            logger.warning(f"Could not load EasyOCR: {e}")
    
    def extract_text(self, image_path: str) -> str:
        """Extract text from image"""
        if self.reader is None:
            return ""
        
        try:
            results = self.reader.readtext(image_path)
            text = " ".join(r[1] for r in results)
            return text.strip()
        except Exception as e:
            logger.warning(f"EasyOCR extraction failed: {e}")
            return ""
    
    def extract_structured(self, image_path: str) -> Dict:
        """Extract text with bounding boxes"""
        if self.reader is None:
            return {"text": "", "blocks": []}
        
        try:
            results = self.reader.readtext(image_path)
            
            blocks = []
            for bbox, text, confidence in results:
                blocks.append({
                    "text": text,
                    "bbox": [
                        int(bbox[0][0]), int(bbox[0][1]),
                        int(bbox[2][0]), int(bbox[2][1])
                    ],
                    "confidence": confidence
                })
            
            full_text = " ".join(b["text"] for b in blocks)
            return {"text": full_text, "blocks": blocks}
            
        except Exception as e:
            logger.warning(f"EasyOCR structured extraction failed: {e}")
            return {"text": "", "blocks": []}


class CNNDocumentClassifier:
    """
    CNN-based document type and quality classification
    Distinguishes between Aadhar, PAN, marksheets, etc.
    """
    
    DOCUMENT_CLASSES = [
        "aadhar", "pan", "voter_id", "driving_license",
        "passport", "marksheet", "income_certificate",
        "caste_certificate", "bank_statement", "other"
    ]
    
    def __init__(self, model_path: Optional[str] = None):
        self.model_path = model_path
        self.model = None
        self.transform = None
        self._load_model()
    
    def _load_model(self):
        """Load CNN classifier model"""
        try:
            import torch
            import torchvision.transforms as transforms
            import torchvision.models as models
            
            if self.model_path and os.path.exists(self.model_path):
                self.model = torch.load(self.model_path)
            else:
                # Use pre-trained ResNet18 as backbone
                self.model = models.resnet18(pretrained=True)
                # Replace final layer for document classification
                self.model.fc = torch.nn.Linear(512, len(self.DOCUMENT_CLASSES))
            
            self.model.eval()
            
            self.transform = transforms.Compose([
                transforms.Resize((224, 224)),
                transforms.ToTensor(),
                transforms.Normalize(
                    mean=[0.485, 0.456, 0.406],
                    std=[0.229, 0.224, 0.225]
                )
            ])
            
            logger.info("Loaded CNN document classifier")
        except ImportError:
            logger.warning("PyTorch not installed, document classification unavailable")
        except Exception as e:
            logger.warning(f"Could not load CNN model: {e}")
    
    def classify(self, image_path: str) -> Tuple[str, float]:
        """
        Classify document type from image
        
        Args:
            image_path: Path to document image
            
        Returns:
            (document_type, confidence)
        """
        if self.model is None:
            return self._rule_based_classify(image_path)
        
        try:
            import torch
            from PIL import Image
            
            image = Image.open(image_path).convert("RGB")
            image_tensor = self.transform(image).unsqueeze(0)
            
            with torch.no_grad():
                outputs = self.model(image_tensor)
                probs = torch.nn.functional.softmax(outputs, dim=1)
                confidence, pred_idx = torch.max(probs, 1)
            
            return self.DOCUMENT_CLASSES[pred_idx.item()], confidence.item()
            
        except Exception as e:
            logger.warning(f"CNN classification failed: {e}")
            return self._rule_based_classify(image_path)
    
    def _rule_based_classify(self, image_path: str) -> Tuple[str, float]:
        """Fallback rule-based classification"""
        # Use filename hints if available
        filename = os.path.basename(image_path).lower()
        
        for doc_type in self.DOCUMENT_CLASSES:
            if doc_type in filename:
                return doc_type, 0.6
        
        return "other", 0.3
    
    def check_quality(self, image_path: str) -> Dict:
        """
        Check document image quality
        
        Returns:
            Quality metrics (blur, brightness, etc.)
        """
        try:
            from PIL import Image
            import numpy as np
            
            image = Image.open(image_path).convert("L")
            img_array = np.array(image)
            
            # Blur detection using Laplacian variance
            laplacian_var = np.var(np.gradient(img_array))
            is_blurry = laplacian_var < 100
            
            # Brightness check
            mean_brightness = np.mean(img_array)
            is_too_dark = mean_brightness < 50
            is_too_bright = mean_brightness > 200
            
            # Contrast check
            contrast = np.std(img_array)
            is_low_contrast = contrast < 30
            
            quality_score = 1.0
            issues = []
            
            if is_blurry:
                quality_score -= 0.3
                issues.append({"en": "Image is blurry", "hi": "छवि धुंधली है"})
            if is_too_dark:
                quality_score -= 0.2
                issues.append({"en": "Image is too dark", "hi": "छवि बहुत गहरी है"})
            if is_too_bright:
                quality_score -= 0.2
                issues.append({"en": "Image is overexposed", "hi": "छवि अधिक उज्ज्वल है"})
            if is_low_contrast:
                quality_score -= 0.2
                issues.append({"en": "Low contrast", "hi": "कम कंट्रास्ट"})
            
            return {
                "quality_score": max(0, quality_score),
                "is_acceptable": quality_score > 0.5,
                "metrics": {
                    "blur_variance": float(laplacian_var),
                    "brightness": float(mean_brightness),
                    "contrast": float(contrast)
                },
                "issues": issues
            }
            
        except Exception as e:
            logger.warning(f"Quality check failed: {e}")
            return {
                "quality_score": 0.5,
                "is_acceptable": True,
                "metrics": {},
                "issues": []
            }


class AdvancedDocumentValidator:
    """
    Advanced Document Validation Pipeline
    
    Combines OCR, CNN classification, and rule-based validation
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        use_tesseract: bool = True,
        use_easyocr: bool = False,
        use_cnn: bool = True
    ):
        self.models_dir = Path(models_dir) if models_dir else None
        
        # Initialize OCR
        if use_tesseract:
            self.ocr = TesseractOCR()
        elif use_easyocr:
            self.ocr = EasyOCRExtractor()
        else:
            self.ocr = None
        
        # Initialize CNN classifier
        if use_cnn:
            cnn_path = str(self.models_dir / "doc_classifier.pt") if self.models_dir else None
            self.cnn_classifier = CNNDocumentClassifier(model_path=cnn_path)
        else:
            self.cnn_classifier = None
        
        # Rule-based validator
        self.rule_validator = DocumentValidator()
    
    def extract_text(self, image_path: str) -> Dict:
        """
        Extract text from document image
        
        Args:
            image_path: Path to document image
            
        Returns:
            Extraction result with text and blocks
        """
        if self.ocr:
            return self.ocr.extract_structured(image_path)
        return {"text": "", "blocks": []}
    
    def classify_document(self, image_path: str) -> Dict:
        """
        Classify document type and check quality
        
        Args:
            image_path: Path to document image
            
        Returns:
            Classification result with type and quality
        """
        result = {
            "document_type": "unknown",
            "type_confidence": 0.0,
            "quality": {}
        }
        
        if self.cnn_classifier:
            doc_type, confidence = self.cnn_classifier.classify(image_path)
            result["document_type"] = doc_type
            result["type_confidence"] = confidence
            result["quality"] = self.cnn_classifier.check_quality(image_path)
        
        return result
    
    def extract_document_fields(self, text: str, document_type: str) -> Dict:
        """
        Extract specific fields based on document type
        
        Args:
            text: OCR extracted text
            document_type: Type of document
            
        Returns:
            Extracted field values
        """
        fields = {}
        
        if document_type == "aadhar":
            # Extract Aadhar number (12 digits, possibly with spaces)
            aadhar_match = re.search(r'\b(\d{4}\s?\d{4}\s?\d{4})\b', text)
            if aadhar_match:
                fields["aadhar_number"] = aadhar_match.group(1).replace(" ", "")
            
            # Extract name
            name_match = re.search(r'(?:Name|नाम)[:\s]*([A-Za-z\s]+)', text, re.IGNORECASE)
            if name_match:
                fields["name"] = name_match.group(1).strip()
            
            # Extract DOB
            dob_match = re.search(r'(?:DOB|जन्म\s*तिथि)[:\s]*(\d{2}/\d{2}/\d{4})', text, re.IGNORECASE)
            if dob_match:
                fields["dob"] = dob_match.group(1)
        
        elif document_type == "pan":
            # Extract PAN number (5 letters + 4 digits + 1 letter)
            pan_match = re.search(r'\b([A-Z]{5}[0-9]{4}[A-Z])\b', text)
            if pan_match:
                fields["pan_number"] = pan_match.group(1)
            
            # Extract name
            name_match = re.search(r'(?:Name|नाम)[:\s]*([A-Za-z\s]+)', text, re.IGNORECASE)
            if name_match:
                fields["name"] = name_match.group(1).strip()
        
        elif document_type == "voter_id":
            # Extract Voter ID (3 letters + 7 digits)
            voter_match = re.search(r'\b([A-Z]{3}[0-9]{7})\b', text)
            if voter_match:
                fields["voter_id"] = voter_match.group(1)
        
        elif document_type == "driving_license":
            # Extract DL number
            dl_match = re.search(r'\b([A-Z]{2}[0-9]{13})\b', text)
            if dl_match:
                fields["dl_number"] = dl_match.group(1)
        
        # Generic field extraction
        # Phone number
        phone_match = re.search(r'\b([6-9]\d{9})\b', text)
        if phone_match:
            fields["phone"] = phone_match.group(1)
        
        # Email
        email_match = re.search(r'\b[\w.-]+@[\w.-]+\.\w+\b', text)
        if email_match:
            fields["email"] = email_match.group(0)
        
        # Address
        if "address" not in fields:
            # Try to find address block
            address_patterns = [
                r'(?:Address|पता)[:\s]*([A-Za-z0-9\s,.-]+)',
                r'(?:Residence|निवास)[:\s]*([A-Za-z0-9\s,.-]+)'
            ]
            for pattern in address_patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    fields["address"] = match.group(1).strip()[:200]
                    break
        
        return fields
    
    def validate_document(self, image_path: str) -> Dict:
        """
        Complete document validation pipeline
        
        Args:
            image_path: Path to document image
            
        Returns:
            Comprehensive validation result
        """
        result = {
            "status": "unknown",
            "document_type": "unknown",
            "type_confidence": 0.0,
            "quality": {},
            "extracted_text": "",
            "extracted_fields": {},
            "field_validation": {},
            "issues": [],
            "recommendations": []
        }
        
        # Step 1: Classify document and check quality
        classification = self.classify_document(image_path)
        result["document_type"] = classification["document_type"]
        result["type_confidence"] = classification["type_confidence"]
        result["quality"] = classification["quality"]
        
        # Check quality issues
        if classification.get("quality", {}).get("quality_score", 1) < 0.5:
            result["issues"].extend(classification["quality"].get("issues", []))
            result["recommendations"].append({
                "en": "Please upload a clearer image",
                "hi": "कृपया एक स्पष्ट छवि अपलोड करें"
            })
        
        # Step 2: Extract text
        ocr_result = self.extract_text(image_path)
        result["extracted_text"] = ocr_result.get("text", "")
        
        if not result["extracted_text"]:
            result["issues"].append({
                "en": "Could not extract text from document",
                "hi": "दस्तावेज़ से टेक्स्ट नहीं निकाल सका"
            })
            result["status"] = "failed"
            return result
        
        # Step 3: Extract fields based on document type
        result["extracted_fields"] = self.extract_document_fields(
            result["extracted_text"],
            result["document_type"]
        )
        
        # Step 4: Validate extracted fields
        if result["extracted_fields"]:
            validation = self.rule_validator.validate_form_fields(result["extracted_fields"])
            result["field_validation"] = validation
            
            if validation.get("is_valid"):
                result["status"] = "valid"
            else:
                result["status"] = "invalid"
                for error in validation.get("errors", []):
                    result["issues"].append(error)
        else:
            result["status"] = "partial"
            result["recommendations"].append({
                "en": "Could not extract all required fields",
                "hi": "सभी आवश्यक फ़ील्ड नहीं निकाल सके"
            })
        
        return result
    
    def validate_multiple(self, documents: List[Dict]) -> Dict:
        """
        Validate multiple documents
        
        Args:
            documents: List of {"path": str, "expected_type": str}
            
        Returns:
            Validation results for all documents
        """
        results = []
        all_valid = True
        
        for doc in documents:
            result = self.validate_document(doc["path"])
            
            # Check if type matches expected
            if doc.get("expected_type"):
                if result["document_type"] != doc["expected_type"]:
                    result["issues"].append({
                        "en": f"Expected {doc['expected_type']}, got {result['document_type']}",
                        "hi": f"अपेक्षित {doc['expected_type']}, मिला {result['document_type']}"
                    })
                    result["status"] = "invalid"
            
            if result["status"] != "valid":
                all_valid = False
            
            results.append({
                "path": doc["path"],
                "result": result
            })
        
        return {
            "all_valid": all_valid,
            "valid_count": sum(1 for r in results if r["result"]["status"] == "valid"),
            "total_count": len(results),
            "documents": results
        }


# Convenience functions for API integration
def extract_document_text(image_path: str, use_easyocr: bool = False) -> str:
    """
    Extract text from document image
    
    Args:
        image_path: Path to document image
        use_easyocr: Use EasyOCR instead of Tesseract
        
    Returns:
        Extracted text
    """
    validator = AdvancedDocumentValidator(use_tesseract=not use_easyocr, use_easyocr=use_easyocr)
    result = validator.extract_text(image_path)
    return result.get("text", "")


def validate_document(image_path: str, expected_type: Optional[str] = None, models_dir: Optional[str] = None) -> Dict:
    """
    Validate a document image
    
    Args:
        image_path: Path to document image
        expected_type: Expected document type (aadhar, pan, etc.)
        models_dir: Directory with trained models
        
    Returns:
        Validation result
    """
    validator = AdvancedDocumentValidator(models_dir=models_dir)
    result = validator.validate_document(image_path)
    
    if expected_type and result["document_type"] != expected_type:
        result["issues"].append({
            "en": f"Document type mismatch: expected {expected_type}",
            "hi": f"दस्तावेज़ प्रकार मेल नहीं खाता: अपेक्षित {expected_type}"
        })
        result["status"] = "invalid"
    
    return result


def check_document_quality(image_path: str) -> Dict:
    """
    Check document image quality
    
    Args:
        image_path: Path to document image
        
    Returns:
        Quality assessment
    """
    classifier = CNNDocumentClassifier()
    return classifier.check_quality(image_path)
