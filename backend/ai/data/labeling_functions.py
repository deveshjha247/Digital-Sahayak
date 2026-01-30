"""
Labeling Functions (Programmatic Labeling)
Automates easy cases using rules and heuristics
Based on Snorkel-style weak supervision
"""

import re
import logging
from typing import Dict, List, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from enum import Enum
from collections import Counter
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# ABSTAIN CONSTANT
# =============================================================================

ABSTAIN = -1  # Label when function doesn't apply


# =============================================================================
# LABELING FUNCTION TYPES
# =============================================================================

class LFType(Enum):
    """Types of labeling functions"""
    KEYWORD = "keyword"
    REGEX = "regex"
    HEURISTIC = "heuristic"
    EXTERNAL = "external"
    ML_MODEL = "ml_model"


@dataclass
class LabelingFunctionResult:
    """Result from a labeling function"""
    label: Any  # The assigned label or ABSTAIN
    confidence: float = 1.0
    lf_name: str = ""
    metadata: Dict = field(default_factory=dict)


@dataclass 
class LabelingFunction:
    """
    A labeling function that assigns labels based on rules/heuristics
    """
    name: str
    func: Callable[[Dict], Any]
    lf_type: LFType = LFType.HEURISTIC
    description: str = ""
    label_mapping: Dict[Any, str] = field(default_factory=dict)
    weight: float = 1.0  # For weighted voting
    
    def apply(self, item: Dict) -> Any:
        """Apply the labeling function to an item"""
        try:
            return self.func(item)
        except Exception as e:
            logger.warning(f"LF {self.name} failed: {e}")
            return ABSTAIN


# =============================================================================
# INTENT CLASSIFICATION LABELING FUNCTIONS
# =============================================================================

def create_intent_labeling_functions() -> List[LabelingFunction]:
    """Create labeling functions for intent classification"""
    
    lfs = []
    
    # LF: Greeting keywords
    def lf_greeting(item: Dict) -> int:
        text = item.get("message", "").lower().strip()
        greeting_patterns = [
            r"^(hi|hello|hey|namaste|नमस्ते|हेलो|हाय)\s*[!.,]?\s*$",
            r"^good\s+(morning|afternoon|evening)",
            r"^(सुप्रभात|शुभ\s*(प्रभात|संध्या))",
        ]
        for pattern in greeting_patterns:
            if re.search(pattern, text):
                return 0  # greeting intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_greeting",
        func=lf_greeting,
        lf_type=LFType.REGEX,
        description="Detects greeting messages",
        label_mapping={0: "greeting"},
        weight=1.5,  # High confidence for greetings
    ))
    
    # LF: Job search keywords
    def lf_job_search(item: Dict) -> int:
        text = item.get("message", "").lower()
        keywords = [
            "job", "vacancy", "bharti", "naukri", "recruitment",
            "नौकरी", "भर्ती", "रिक्ति", "वैकेंसी",
        ]
        for kw in keywords:
            if kw in text:
                return 1  # job_search intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_job_search",
        func=lf_job_search,
        lf_type=LFType.KEYWORD,
        description="Detects job search queries",
        label_mapping={1: "job_search"},
    ))
    
    # LF: Scheme search keywords
    def lf_scheme_search(item: Dict) -> int:
        text = item.get("message", "").lower()
        keywords = [
            "scheme", "yojana", "योजना", "subsidy", "benefit",
            "सब्सिडी", "लाभ", "pm kisan", "ayushman",
        ]
        for kw in keywords:
            if kw in text:
                return 2  # scheme_search intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_scheme_search",
        func=lf_scheme_search,
        lf_type=LFType.KEYWORD,
        description="Detects scheme search queries",
        label_mapping={2: "scheme_search"},
    ))
    
    # LF: Apply intent
    def lf_apply(item: Dict) -> int:
        text = item.get("message", "").lower()
        patterns = [
            r"(apply|आवेदन|अप्लाई|register|रजिस्टर)",
            r"(form\s+bhar|फॉर्म\s+भर)",
            r"how\s+to\s+(apply|register)",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 3  # apply intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_apply",
        func=lf_apply,
        lf_type=LFType.REGEX,
        description="Detects apply/register intent",
        label_mapping={3: "apply"},
    ))
    
    # LF: Status check
    def lf_status_check(item: Dict) -> int:
        text = item.get("message", "").lower()
        patterns = [
            r"(status|स्थिति|track|ट्रैक)",
            r"(kahan\s+pahuncha|कहां\s+पहुंचा)",
            r"(application|आवेदन).*(status|स्थिति)",
            r"mera\s+(form|application)",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 4  # check_status intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_status_check",
        func=lf_status_check,
        lf_type=LFType.REGEX,
        description="Detects status check queries",
        label_mapping={4: "check_status"},
    ))
    
    # LF: Payment issues
    def lf_payment_issue(item: Dict) -> int:
        text = item.get("message", "").lower()
        keywords = [
            "payment", "पेमेंट", "refund", "रिफंड",
            "paise", "पैसे", "money", "deduct", "कट",
            "transaction", "failed",
        ]
        count = sum(1 for kw in keywords if kw in text)
        if count >= 1:
            return 5  # payment_issue intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_payment_issue",
        func=lf_payment_issue,
        lf_type=LFType.KEYWORD,
        description="Detects payment related issues",
        label_mapping={5: "payment_issue"},
    ))
    
    # LF: Thanks/Bye
    def lf_thanks(item: Dict) -> int:
        text = item.get("message", "").lower().strip()
        patterns = [
            r"^(thank|thanks|धन्यवाद|शुक्रिया)\s*[!.,]?\s*",
            r"^(bye|goodbye|अलविदा|बाय)\s*[!.,]?\s*$",
            r"^(ok|okay|ठीक|अच्छा)\s*[!.,]?\s*$",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 6  # thanks intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_thanks",
        func=lf_thanks,
        lf_type=LFType.REGEX,
        description="Detects thanks/goodbye messages",
        label_mapping={6: "thanks"},
        weight=1.5,
    ))
    
    # LF: Help/Human agent
    def lf_human_agent(item: Dict) -> int:
        text = item.get("message", "").lower()
        patterns = [
            r"(talk|speak|connect).*(human|person|agent)",
            r"(इंसान|व्यक्ति|एजेंट).*(बात|कनेक्ट)",
            r"customer\s*(care|support|service)",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 7  # human_agent intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_human_agent",
        func=lf_human_agent,
        lf_type=LFType.REGEX,
        description="Detects requests for human agent",
        label_mapping={7: "human_agent"},
    ))
    
    # LF: Deadline query
    def lf_deadline(item: Dict) -> int:
        text = item.get("message", "").lower()
        patterns = [
            r"(last\s*date|deadline|अंतिम\s*तिथि)",
            r"(kab\s*tak|कब\s*तक)",
            r"(when|कब).*(close|बंद)",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 8  # deadline_query intent
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_deadline",
        func=lf_deadline,
        lf_type=LFType.REGEX,
        description="Detects deadline queries",
        label_mapping={8: "deadline_query"},
    ))
    
    return lfs


# =============================================================================
# JOB CATEGORY LABELING FUNCTIONS
# =============================================================================

def create_job_category_labeling_functions() -> List[LabelingFunction]:
    """Create labeling functions for job category classification"""
    
    lfs = []
    
    # LF: Railway jobs
    def lf_railway(item: Dict) -> int:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        keywords = [
            "railway", "rrb", "रेलवे", "indian railways",
            "loco pilot", "station master", "track maintainer",
            "northern railway", "southern railway", "central railway",
        ]
        for kw in keywords:
            if kw in text:
                return 0  # railway
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_railway",
        func=lf_railway,
        lf_type=LFType.KEYWORD,
        description="Detects railway jobs",
        label_mapping={0: "railway"},
    ))
    
    # LF: SSC jobs
    def lf_ssc(item: Dict) -> int:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        patterns = [
            r"\bssc\b", r"staff\s+selection", r"एसएससी",
            r"ssc\s*(cgl|chsl|mts|gd|je)",
        ]
        for pattern in patterns:
            if re.search(pattern, text):
                return 1  # ssc
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_ssc",
        func=lf_ssc,
        lf_type=LFType.REGEX,
        description="Detects SSC jobs",
        label_mapping={1: "ssc"},
    ))
    
    # LF: Banking jobs
    def lf_banking(item: Dict) -> int:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        keywords = [
            "bank", "ibps", "sbi", "rbi", "बैंक",
            "probationary officer", "clerk", "po",
            "punjab national bank", "bank of baroda",
        ]
        for kw in keywords:
            if kw in text:
                return 2  # bank
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_banking",
        func=lf_banking,
        lf_type=LFType.KEYWORD,
        description="Detects banking jobs",
        label_mapping={2: "bank"},
    ))
    
    # LF: Police/Defence
    def lf_police_defence(item: Dict) -> int:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        keywords = [
            "police", "constable", "पुलिस", "सिपाही",
            "crpf", "bsf", "cisf", "itbp", "ssb",
            "defence", "army", "navy", "air force",
            "nda", "cds", "सेना",
        ]
        for kw in keywords:
            if kw in text:
                return 3  # police
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_police_defence",
        func=lf_police_defence,
        lf_type=LFType.KEYWORD,
        description="Detects police/defence jobs",
        label_mapping={3: "police"},
    ))
    
    # LF: Teaching jobs
    def lf_teaching(item: Dict) -> int:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        keywords = [
            "teacher", "शिक्षक", "tgt", "pgt", "ctet", "tet",
            "kendriya vidyalaya", "kvs", "navodaya", "nvs",
            "lecturer", "professor", "principal",
        ]
        for kw in keywords:
            if kw in text:
                return 4  # teaching
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_teaching",
        func=lf_teaching,
        lf_type=LFType.KEYWORD,
        description="Detects teaching jobs",
        label_mapping={4: "teaching"},
    ))
    
    # LF: Healthcare jobs
    def lf_healthcare(item: Dict) -> int:
        text = (item.get("title", "") + " " + item.get("description", "")).lower()
        keywords = [
            "nurse", "anm", "gnm", "नर्स", "doctor",
            "aiims", "esic", "hospital", "medical",
            "pharmacist", "lab technician", "health worker",
        ]
        for kw in keywords:
            if kw in text:
                return 5  # healthcare
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_healthcare",
        func=lf_healthcare,
        lf_type=LFType.KEYWORD,
        description="Detects healthcare jobs",
        label_mapping={5: "healthcare"},
    ))
    
    return lfs


# =============================================================================
# FORM FIELD LABELING FUNCTIONS
# =============================================================================

def create_form_field_labeling_functions() -> List[LabelingFunction]:
    """Create labeling functions for form field classification"""
    
    lfs = []
    
    # LF: Name field
    def lf_name_field(item: Dict) -> int:
        label = item.get("label", "").lower()
        input_id = item.get("id", "").lower()
        placeholder = item.get("placeholder", "").lower()
        combined = f"{label} {input_id} {placeholder}"
        
        patterns = [
            r"\bname\b", r"\bनाम\b", r"candidate", r"applicant",
            r"full\s*name", r"पूरा\s*नाम",
        ]
        
        # Exclude father/mother name
        if re.search(r"(father|mother|पिता|माता)", combined):
            return ABSTAIN
        
        for pattern in patterns:
            if re.search(pattern, combined):
                return 0  # name
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_name_field",
        func=lf_name_field,
        lf_type=LFType.REGEX,
        description="Detects name input fields",
        label_mapping={0: "name"},
    ))
    
    # LF: Email field
    def lf_email_field(item: Dict) -> int:
        label = item.get("label", "").lower()
        input_id = item.get("id", "").lower()
        input_type = item.get("type", "").lower()
        combined = f"{label} {input_id}"
        
        if input_type == "email":
            return 1  # email
        
        if re.search(r"(email|e-mail|ईमेल)", combined):
            return 1
        
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_email_field",
        func=lf_email_field,
        lf_type=LFType.HEURISTIC,
        description="Detects email input fields",
        label_mapping={1: "email"},
        weight=1.5,  # High confidence when input type is email
    ))
    
    # LF: Phone field
    def lf_phone_field(item: Dict) -> int:
        label = item.get("label", "").lower()
        input_id = item.get("id", "").lower()
        input_type = item.get("type", "").lower()
        combined = f"{label} {input_id}"
        
        if input_type == "tel":
            return 2  # phone
        
        if re.search(r"(phone|mobile|मोबाइल|फोन|contact|संपर्क)", combined):
            return 2
        
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_phone_field",
        func=lf_phone_field,
        lf_type=LFType.HEURISTIC,
        description="Detects phone input fields",
        label_mapping={2: "phone"},
        weight=1.5,
    ))
    
    # LF: DOB field
    def lf_dob_field(item: Dict) -> int:
        label = item.get("label", "").lower()
        input_id = item.get("id", "").lower()
        input_type = item.get("type", "").lower()
        combined = f"{label} {input_id}"
        
        if input_type == "date" and re.search(r"(birth|dob|जन्म)", combined):
            return 3  # dob
        
        if re.search(r"(date\s*of\s*birth|dob|d\.?o\.?b|जन्म\s*तिथि)", combined):
            return 3
        
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_dob_field",
        func=lf_dob_field,
        lf_type=LFType.HEURISTIC,
        description="Detects date of birth fields",
        label_mapping={3: "dob"},
    ))
    
    # LF: Aadhaar field
    def lf_aadhaar_field(item: Dict) -> int:
        label = item.get("label", "").lower()
        input_id = item.get("id", "").lower()
        combined = f"{label} {input_id}"
        
        if re.search(r"(aadhaar|aadhar|आधार)", combined):
            return 4  # aadhaar
        
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_aadhaar_field",
        func=lf_aadhaar_field,
        lf_type=LFType.REGEX,
        description="Detects Aadhaar number fields",
        label_mapping={4: "aadhaar"},
    ))
    
    # LF: CAPTCHA field (never auto-fill)
    def lf_captcha_field(item: Dict) -> int:
        label = item.get("label", "").lower()
        input_id = item.get("id", "").lower()
        combined = f"{label} {input_id}"
        
        if re.search(r"(captcha|security\s*code|verification)", combined):
            return 5  # captcha
        
        return ABSTAIN
    
    lfs.append(LabelingFunction(
        name="lf_captcha_field",
        func=lf_captcha_field,
        lf_type=LFType.REGEX,
        description="Detects CAPTCHA fields",
        label_mapping={5: "captcha"},
        weight=2.0,  # Very high confidence
    ))
    
    return lfs


# =============================================================================
# LABEL MODEL (COMBINES LABELING FUNCTIONS)
# =============================================================================

class LabelModel:
    """
    Combines multiple labeling functions using weighted voting
    Based on Snorkel's label model approach
    """
    
    def __init__(
        self,
        labeling_functions: List[LabelingFunction],
        label_names: Dict[int, str] = None
    ):
        self.lfs = labeling_functions
        self.label_names = label_names or {}
        
        # Statistics
        self.lf_stats = {lf.name: {"applied": 0, "abstained": 0} for lf in self.lfs}
    
    def apply(self, item: Dict) -> Dict[str, Any]:
        """
        Apply all labeling functions and combine results
        """
        votes = []
        weights = []
        lf_results = {}
        
        for lf in self.lfs:
            result = lf.apply(item)
            lf_results[lf.name] = result
            
            if result != ABSTAIN:
                votes.append(result)
                weights.append(lf.weight)
                self.lf_stats[lf.name]["applied"] += 1
            else:
                self.lf_stats[lf.name]["abstained"] += 1
        
        if not votes:
            return {
                "label": ABSTAIN,
                "label_name": "abstain",
                "confidence": 0.0,
                "lf_results": lf_results,
                "needs_human_label": True,
            }
        
        # Weighted voting
        label_weights = Counter()
        for vote, weight in zip(votes, weights):
            label_weights[vote] += weight
        
        # Get winning label
        winning_label = label_weights.most_common(1)[0][0]
        total_weight = sum(weights)
        confidence = label_weights[winning_label] / total_weight
        
        # Determine if human review needed
        needs_review = (
            confidence < 0.7 or  # Low confidence
            len(set(votes)) > 1  # Conflicting LFs
        )
        
        return {
            "label": winning_label,
            "label_name": self.label_names.get(winning_label, str(winning_label)),
            "confidence": round(confidence, 4),
            "lf_results": lf_results,
            "n_lfs_voted": len(votes),
            "needs_human_label": needs_review,
        }
    
    def apply_batch(self, items: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Apply to batch and separate auto-labeled from needs-review
        
        Returns:
            (auto_labeled, needs_review)
        """
        auto_labeled = []
        needs_review = []
        
        for item in items:
            result = self.apply(item)
            item["_label_model_result"] = result
            
            if result["needs_human_label"]:
                needs_review.append(item)
            else:
                item["label"] = result["label_name"]
                item["label_confidence"] = result["confidence"]
                auto_labeled.append(item)
        
        logger.info(f"Label model: {len(auto_labeled)} auto-labeled, {len(needs_review)} need review")
        return auto_labeled, needs_review
    
    def get_lf_statistics(self) -> Dict[str, Dict]:
        """Get statistics for each labeling function"""
        stats = {}
        for lf in self.lfs:
            name = lf.name
            applied = self.lf_stats[name]["applied"]
            abstained = self.lf_stats[name]["abstained"]
            total = applied + abstained
            
            stats[name] = {
                "type": lf.lf_type.value,
                "description": lf.description,
                "weight": lf.weight,
                "applied": applied,
                "abstained": abstained,
                "coverage": round(applied / total, 4) if total > 0 else 0,
            }
        
        return stats
    
    def get_lf_conflicts(self, items: List[Dict]) -> List[Dict]:
        """Find items where labeling functions conflict"""
        conflicts = []
        
        for item in items:
            result = self.apply(item)
            
            # Get all non-abstain results
            votes = {
                lf_name: vote 
                for lf_name, vote in result["lf_results"].items() 
                if vote != ABSTAIN
            }
            
            if len(set(votes.values())) > 1:
                conflicts.append({
                    "item": item,
                    "conflicting_votes": votes,
                })
        
        return conflicts


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_intent_label_model() -> LabelModel:
    """Get pre-configured label model for intent classification"""
    lfs = create_intent_labeling_functions()
    label_names = {
        0: "greeting",
        1: "job_search",
        2: "scheme_search",
        3: "apply",
        4: "check_status",
        5: "payment_issue",
        6: "thanks",
        7: "human_agent",
        8: "deadline_query",
    }
    return LabelModel(lfs, label_names)


def get_job_category_label_model() -> LabelModel:
    """Get pre-configured label model for job category classification"""
    lfs = create_job_category_labeling_functions()
    label_names = {
        0: "railway",
        1: "ssc",
        2: "bank",
        3: "police",
        4: "teaching",
        5: "healthcare",
    }
    return LabelModel(lfs, label_names)


def get_form_field_label_model() -> LabelModel:
    """Get pre-configured label model for form field classification"""
    lfs = create_form_field_labeling_functions()
    label_names = {
        0: "name",
        1: "email",
        2: "phone",
        3: "dob",
        4: "aadhaar",
        5: "captcha",
    }
    return LabelModel(lfs, label_names)
