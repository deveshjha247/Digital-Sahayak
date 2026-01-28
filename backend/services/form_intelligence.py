"""
Form Intelligence Service
ML-based field classification, auto-fill, and error prediction for portal forms
"""

from config.database import get_database
from config.settings import OPENAI_API_KEY
from utils.helpers import get_current_timestamp, extract_keywords
from openai import AsyncOpenAI
import re
from typing import Dict, List, Any, Optional
import json

client = AsyncOpenAI(api_key=OPENAI_API_KEY)

class FormIntelligenceEngine:
    """
    Intelligent form processing with ML-based field classification and error prediction
    """
    
    def __init__(self):
        self.db = get_database()
        
        # Field type patterns (rule-based classification)
        self.field_patterns = {
            "name": r"(name|नाम|naam)",
            "email": r"(email|ईमेल|e-mail)",
            "phone": r"(phone|mobile|contact|फोन|मोबाइल)",
            "address": r"(address|पता|location)",
            "age": r"(age|उम्र|dob|birth)",
            "education": r"(education|qualification|शिक्षा|degree)",
            "state": r"(state|राज्य|province)",
            "city": r"(city|शहर|district)",
            "pincode": r"(pin|postal|zip)",
            "aadhar": r"(aadhar|आधार|aadhaar)",
            "pan": r"(pan|पैन)",
            "income": r"(income|salary|आय)",
            "caste": r"(caste|category|जाति)",
            "gender": r"(gender|sex|लिंग)",
            "occupation": r"(occupation|profession|व्यवसाय)"
        }
        
        # Validation patterns
        self.validation_patterns = {
            "email": r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
            "phone": r"^[6-9]\d{9}$",
            "pincode": r"^\d{6}$",
            "aadhar": r"^\d{12}$",
            "pan": r"^[A-Z]{5}\d{4}[A-Z]$",
            "age": r"^\d{1,3}$"
        }
        
        # Common error patterns
        self.error_patterns = [
            {"pattern": r"[a-z][A-Z]", "message": "Inconsistent capitalization", "severity": "low"},
            {"pattern": r"\s{2,}", "message": "Multiple spaces detected", "severity": "low"},
            {"pattern": r"^\s|\s$", "message": "Leading/trailing spaces", "severity": "medium"},
            {"pattern": r"\d{10,}", "message": "Unusually long number", "severity": "medium"}
        ]
    
    async def classify_field(self, field_label: str, field_value: str = None) -> Dict[str, Any]:
        """
        Classify form field type using rule-based + ML approach
        """
        field_label_lower = field_label.lower()
        
        # Rule-based classification
        rule_based_type = None
        confidence = 0.0
        
        for field_type, pattern in self.field_patterns.items():
            if re.search(pattern, field_label_lower, re.IGNORECASE):
                rule_based_type = field_type
                confidence = 0.85
                break
        
        # If value provided, validate against patterns
        if field_value and rule_based_type:
            validation_pattern = self.validation_patterns.get(rule_based_type)
            if validation_pattern:
                is_valid = bool(re.match(validation_pattern, str(field_value)))
                if is_valid:
                    confidence = 0.95
        
        # ML enhancement for ambiguous cases
        ml_type = None
        if confidence < 0.8 or not rule_based_type:
            ml_type = await self._ml_classify_field(field_label, field_value)
            if ml_type:
                rule_based_type = ml_type.get("type")
                confidence = max(confidence, ml_type.get("confidence", 0.6))
        
        return {
            "field_label": field_label,
            "classified_type": rule_based_type or "unknown",
            "confidence": confidence,
            "suggestions": self._get_field_suggestions(rule_based_type or "unknown")
        }
    
    async def _ml_classify_field(self, field_label: str, field_value: str = None) -> Optional[Dict]:
        """
        Use OpenAI to classify ambiguous fields
        """
        try:
            context = f"Field label: {field_label}"
            if field_value:
                context += f"\nField value: {field_value}"
            
            prompt = f"""Classify this form field into one of these types:
name, email, phone, address, age, education, state, city, pincode, aadhar, pan, income, caste, gender, occupation, or unknown.

{context}

Respond with JSON: {{"type": "field_type", "confidence": 0.0-1.0, "reasoning": "brief explanation"}}"""
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result
        
        except Exception as e:
            print(f"ML classification error: {e}")
            return None
    
    def _get_field_suggestions(self, field_type: str) -> Dict[str, Any]:
        """
        Get input suggestions based on field type
        """
        suggestions = {
            "name": {
                "placeholder": "Enter full name",
                "validation": "Letters and spaces only",
                "example": "Rajesh Kumar"
            },
            "email": {
                "placeholder": "example@email.com",
                "validation": "Valid email format",
                "example": "rajesh@example.com"
            },
            "phone": {
                "placeholder": "10-digit mobile number",
                "validation": "Starts with 6-9",
                "example": "9876543210"
            },
            "aadhar": {
                "placeholder": "12-digit Aadhar number",
                "validation": "Exactly 12 digits",
                "example": "123456789012"
            },
            "pan": {
                "placeholder": "PAN card number",
                "validation": "Format: ABCDE1234F",
                "example": "ABCDE1234F"
            },
            "pincode": {
                "placeholder": "6-digit PIN code",
                "validation": "Exactly 6 digits",
                "example": "110001"
            },
            "age": {
                "placeholder": "Age in years",
                "validation": "Number between 1-120",
                "example": "25"
            }
        }
        
        return suggestions.get(field_type, {
            "placeholder": f"Enter {field_type}",
            "validation": "Valid input required",
            "example": ""
        })
    
    async def predict_errors(self, form_data: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Predict potential errors in form submission
        """
        errors = []
        
        for field_name, field_value in form_data.items():
            # Classify field
            classification = await self.classify_field(field_name, field_value)
            field_type = classification["classified_type"]
            
            # Validate based on type
            if field_type != "unknown":
                validation_pattern = self.validation_patterns.get(field_type)
                if validation_pattern and not re.match(validation_pattern, str(field_value)):
                    errors.append({
                        "field": field_name,
                        "error": f"Invalid {field_type} format",
                        "severity": "high",
                        "suggestion": classification["suggestions"].get("example", ""),
                        "expected_format": classification["suggestions"].get("validation", "")
                    })
            
            # Check for common patterns
            for error_pattern in self.error_patterns:
                if re.search(error_pattern["pattern"], str(field_value)):
                    errors.append({
                        "field": field_name,
                        "error": error_pattern["message"],
                        "severity": error_pattern["severity"],
                        "suggestion": "Review and correct"
                    })
        
        # ML-based error prediction
        ml_errors = await self._ml_predict_errors(form_data)
        if ml_errors:
            errors.extend(ml_errors)
        
        return errors
    
    async def _ml_predict_errors(self, form_data: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Use ML to predict subtle errors
        """
        try:
            prompt = f"""Analyze this form submission and predict potential errors or issues:

Form Data:
{json.dumps(form_data, indent=2)}

Look for:
- Inconsistent information
- Missing required context
- Unusual patterns
- Common mistakes

Respond with JSON array: [{{"field": "field_name", "error": "description", "severity": "low/medium/high", "suggestion": "fix"}}]
If no errors, return empty array []."""
            
            response = await client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return result if isinstance(result, list) else []
        
        except Exception as e:
            print(f"ML error prediction failed: {e}")
            return []
    
    async def auto_fill_suggestions(self, form_fields: List[str], user_profile: Dict) -> Dict[str, Any]:
        """
        Suggest auto-fill values based on user profile
        """
        suggestions = {}
        
        for field_label in form_fields:
            classification = await self.classify_field(field_label)
            field_type = classification["classified_type"]
            
            # Map user profile to field
            if field_type == "name":
                suggestions[field_label] = user_profile.get("name", "")
            elif field_type == "email":
                suggestions[field_label] = user_profile.get("email", "")
            elif field_type == "phone":
                suggestions[field_label] = user_profile.get("phone", "")
            elif field_type == "age":
                suggestions[field_label] = str(user_profile.get("age", ""))
            elif field_type == "education":
                suggestions[field_label] = user_profile.get("education", "")
            elif field_type == "state":
                suggestions[field_label] = user_profile.get("state", "")
            elif field_type == "city":
                suggestions[field_label] = user_profile.get("city", "")
            elif field_type == "address":
                suggestions[field_label] = user_profile.get("address", "")
            elif field_type == "gender":
                suggestions[field_label] = user_profile.get("gender", "")
        
        return {
            "suggestions": suggestions,
            "confidence": 0.9 if suggestions else 0.0
        }
    
    async def train_from_dataset(self, portal_name: str, form_submissions: List[Dict]) -> Dict[str, Any]:
        """
        Train field classification model from portal form datasets
        """
        if not form_submissions:
            return {"error": "No training data provided"}
        
        # Extract field patterns
        field_frequency = {}
        field_values = {}
        
        for submission in form_submissions:
            for field_name, field_value in submission.items():
                # Count field occurrences
                field_frequency[field_name] = field_frequency.get(field_name, 0) + 1
                
                # Collect values for pattern analysis
                if field_name not in field_values:
                    field_values[field_name] = []
                field_values[field_name].append(str(field_value))
        
        # Analyze patterns and store learning
        learned_patterns = {}
        
        for field_name, values in field_values.items():
            classification = await self.classify_field(field_name, values[0] if values else None)
            
            # Detect common patterns
            pattern_analysis = self._analyze_value_patterns(values)
            
            learned_patterns[field_name] = {
                "classified_type": classification["classified_type"],
                "frequency": field_frequency[field_name],
                "sample_values": values[:5],
                "pattern": pattern_analysis,
                "confidence": classification["confidence"]
            }
        
        # Save to database
        training_doc = {
            "portal_name": portal_name,
            "trained_at": get_current_timestamp(),
            "total_submissions": len(form_submissions),
            "learned_patterns": learned_patterns,
            "field_count": len(learned_patterns)
        }
        
        await self.db.form_training_data.insert_one(training_doc)
        
        return {
            "message": f"Trained on {len(form_submissions)} submissions from {portal_name}",
            "fields_learned": len(learned_patterns),
            "patterns": learned_patterns
        }
    
    def _analyze_value_patterns(self, values: List[str]) -> Dict[str, Any]:
        """
        Analyze patterns in field values
        """
        if not values:
            return {"type": "unknown"}
        
        # Check if all numeric
        all_numeric = all(v.isdigit() for v in values if v)
        if all_numeric:
            lengths = [len(v) for v in values if v]
            avg_length = sum(lengths) / len(lengths) if lengths else 0
            return {
                "type": "numeric",
                "avg_length": avg_length,
                "min_length": min(lengths) if lengths else 0,
                "max_length": max(lengths) if lengths else 0
            }
        
        # Check if all alphabetic
        all_alpha = all(v.replace(" ", "").isalpha() for v in values if v)
        if all_alpha:
            return {"type": "alphabetic"}
        
        # Mixed
        return {"type": "mixed"}
    
    async def get_portal_training_stats(self, portal_name: str = None) -> Dict[str, Any]:
        """
        Get training statistics for portals
        """
        query = {}
        if portal_name:
            query["portal_name"] = portal_name
        
        trainings = await self.db.form_training_data.find(query).to_list(length=100)
        
        total_submissions = sum(t.get("total_submissions", 0) for t in trainings)
        total_fields = sum(t.get("field_count", 0) for t in trainings)
        
        return {
            "portals_trained": len(trainings),
            "total_submissions": total_submissions,
            "total_fields_learned": total_fields,
            "trainings": trainings
        }
