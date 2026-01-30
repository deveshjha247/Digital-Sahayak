"""
Annotation Pipeline
Handles pre-labeling, annotator assignment, and consensus
"""

import json
import logging
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)


# =============================================================================
# PRE-LABELING WITH HEURISTICS
# =============================================================================

class HeuristicPreLabeler:
    """
    Pre-labels obvious cases using heuristics
    Lets human annotators focus on complex cases
    """
    
    # Known named entities for jobs/schemes
    KNOWN_ORGANIZATIONS = {
        # Railways
        "rrb": "railway",
        "railway recruitment board": "railway",
        "indian railways": "railway",
        "northern railway": "railway",
        "southern railway": "railway",
        "central railway": "railway",
        
        # SSC
        "ssc": "ssc",
        "staff selection commission": "ssc",
        "ssc cgl": "ssc",
        "ssc chsl": "ssc",
        "ssc mts": "ssc",
        
        # Banking
        "ibps": "bank",
        "sbi": "bank",
        "state bank of india": "bank",
        "rbi": "bank",
        "reserve bank": "bank",
        "punjab national bank": "bank",
        "bank of baroda": "bank",
        
        # Police/Defence
        "crpf": "police",
        "bsf": "police",
        "cisf": "police",
        "itbp": "police",
        "ssb": "police",
        "upsc": "central_govt",
        "nda": "police",
        "cds": "police",
        
        # Teaching
        "kvs": "teaching",
        "kendriya vidyalaya": "teaching",
        "navodaya": "teaching",
        "ctet": "teaching",
        "tet": "teaching",
        
        # Healthcare
        "aiims": "healthcare",
        "esic": "healthcare",
        "nurse": "healthcare",
        "anm": "healthcare",
        "gnm": "healthcare",
    }
    
    # Known scheme keywords
    KNOWN_SCHEMES = {
        "pm kisan": "agriculture",
        "प्रधानमंत्री किसान": "agriculture",
        "pm awas": "housing",
        "प्रधानमंत्री आवास": "housing",
        "ayushman": "healthcare",
        "आयुष्मान": "healthcare",
        "ujjwala": "welfare",
        "उज्ज्वला": "welfare",
        "mudra": "employment",
        "मुद्रा": "employment",
        "scholarship": "education",
        "छात्रवृत्ति": "education",
        "pension": "pension",
        "पेंशन": "pension",
    }
    
    # Education level patterns
    EDUCATION_PATTERNS = {
        "10th": [r"10th", r"10वीं", r"matric", r"मैट्रिक", r"high school", r"हाई स्कूल"],
        "12th": [r"12th", r"12वीं", r"inter", r"इंटर", r"intermediate", r"senior secondary"],
        "graduate": [r"graduate", r"स्नातक", r"b\.?a\.?", r"b\.?sc\.?", r"b\.?com\.?", r"bachelor"],
        "post_graduate": [r"post.?graduate", r"स्नातकोत्तर", r"m\.?a\.?", r"m\.?sc\.?", r"master"],
        "diploma": [r"diploma", r"डिप्लोमा", r"iti", r"आईटीआई"],
    }
    
    # Intent patterns for messages
    INTENT_PATTERNS = {
        "greeting": [r"^(hi|hello|hey|namaste|नमस्ते|हेलो|हाय)\s*[!.,]?\s*$"],
        "job_search": [r"(job|naukri|bharti|vacancy|नौकरी|भर्ती|रिक्ति)"],
        "scheme_search": [r"(scheme|yojana|योजना|लाभ|benefit)"],
        "check_status": [r"(status|स्थिति|track|कहां पहुंचा|where.+application)"],
        "payment_issue": [r"(payment|पेमेंट|refund|रिफंड|पैसे कट|money.+deduct)"],
        "thanks": [r"^(thank|thanks|धन्यवाद|शुक्रिया|bye|अलविदा)\s*[!.,]?\s*$"],
    }
    
    def __init__(self, confidence_threshold: float = 0.8):
        self.confidence_threshold = confidence_threshold
    
    def pre_label_job(self, text: str) -> Dict[str, Any]:
        """
        Pre-label a job posting using heuristics
        """
        text_lower = text.lower()
        result = {
            "pre_labeled": False,
            "confidence": 0.0,
            "labels": {},
            "needs_review": True,
        }
        
        # Detect category from known organizations
        for org, category in self.KNOWN_ORGANIZATIONS.items():
            if org in text_lower:
                result["labels"]["category"] = category
                result["confidence"] = 0.9
                result["pre_labeled"] = True
                break
        
        # Detect education level
        for level, patterns in self.EDUCATION_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, text_lower, re.IGNORECASE):
                    result["labels"]["education_level"] = level
                    break
        
        # Extract dates (last date / deadline)
        date_match = re.search(
            r"(last\s*date|अंतिम\s*तिथि|deadline)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            text_lower
        )
        if date_match:
            result["labels"]["deadline"] = date_match.group(2)
        
        # Extract vacancies
        vacancy_match = re.search(r"(\d+)\s*(posts?|vacancies|पद|रिक्तियां)", text_lower)
        if vacancy_match:
            result["labels"]["vacancies"] = int(vacancy_match.group(1))
        
        # Determine if needs human review
        if result["confidence"] >= self.confidence_threshold and len(result["labels"]) >= 2:
            result["needs_review"] = False
        
        return result
    
    def pre_label_intent(self, message: str) -> Dict[str, Any]:
        """
        Pre-label a user message intent using heuristics
        """
        message_lower = message.lower().strip()
        result = {
            "pre_labeled": False,
            "confidence": 0.0,
            "intent": "unknown",
            "needs_review": True,
        }
        
        for intent, patterns in self.INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    result["intent"] = intent
                    result["pre_labeled"] = True
                    
                    # Higher confidence for exact matches (greetings, thanks)
                    if intent in ["greeting", "thanks"]:
                        result["confidence"] = 0.95
                        result["needs_review"] = False
                    else:
                        result["confidence"] = 0.7
                    
                    return result
        
        return result
    
    def pre_label_form_field(self, field_info: Dict) -> Dict[str, Any]:
        """
        Pre-label a form field using heuristics
        """
        label = field_info.get("label", "").lower()
        input_id = field_info.get("id", "").lower()
        placeholder = field_info.get("placeholder", "").lower()
        input_type = field_info.get("type", "text").lower()
        
        combined = f"{label} {input_id} {placeholder}"
        
        result = {
            "pre_labeled": False,
            "confidence": 0.0,
            "field_type": "unknown",
            "needs_review": True,
        }
        
        # Field detection patterns
        field_patterns = {
            "name": [r"\bname\b", r"\bनाम\b", r"candidate", r"applicant"],
            "father_name": [r"father", r"पिता", r"s/o", r"d/o"],
            "mother_name": [r"mother", r"माता"],
            "dob": [r"\bdob\b", r"birth", r"जन्म", r"d\.?o\.?b"],
            "email": [r"email", r"e-mail", r"ईमेल"],
            "phone": [r"phone", r"mobile", r"मोबाइल", r"contact", r"संपर्क"],
            "address": [r"address", r"पता"],
            "pincode": [r"pin", r"postal", r"पिन"],
            "aadhaar": [r"aadhaar", r"aadhar", r"आधार"],
            "gender": [r"gender", r"sex", r"लिंग"],
            "category": [r"category", r"caste", r"वर्ग", r"जाति"],
            "qualification": [r"qualification", r"education", r"योग्यता", r"शिक्षा"],
            "photo": [r"photo", r"photograph", r"फोटो"],
            "signature": [r"signature", r"sign", r"हस्ताक्षर"],
            "captcha": [r"captcha", r"security.?code", r"verification"],
            "password": [r"password", r"पासवर्ड"],
        }
        
        for field_type, patterns in field_patterns.items():
            for pattern in patterns:
                if re.search(pattern, combined, re.IGNORECASE):
                    result["field_type"] = field_type
                    result["pre_labeled"] = True
                    result["confidence"] = 0.85
                    
                    # High confidence for HTML type hints
                    if input_type == "email" and field_type == "email":
                        result["confidence"] = 0.95
                    elif input_type == "tel" and field_type == "phone":
                        result["confidence"] = 0.95
                    elif input_type == "date" and field_type == "dob":
                        result["confidence"] = 0.95
                    
                    if result["confidence"] >= self.confidence_threshold:
                        result["needs_review"] = False
                    
                    return result
        
        return result
    
    def batch_pre_label(
        self,
        items: List[Dict],
        task_type: str
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Pre-label a batch of items
        
        Returns:
            (auto_labeled, needs_review)
        """
        auto_labeled = []
        needs_review = []
        
        for item in items:
            if task_type == "job_yojana_matching":
                text = item.get("title", "") + " " + item.get("description", "")
                result = self.pre_label_job(text)
            elif task_type == "intent_classification":
                result = self.pre_label_intent(item.get("message", ""))
            elif task_type == "form_field_classification":
                result = self.pre_label_form_field(item)
            else:
                result = {"needs_review": True}
            
            item["_pre_label"] = result
            
            if result.get("needs_review", True):
                needs_review.append(item)
            else:
                auto_labeled.append(item)
        
        logger.info(f"Pre-labeled {len(auto_labeled)} items, {len(needs_review)} need review")
        return auto_labeled, needs_review


# =============================================================================
# ANNOTATOR CONSENSUS
# =============================================================================

@dataclass
class AnnotatorAssignment:
    """Tracks annotation assignments"""
    item_id: str
    annotator_ids: List[str]
    annotations: Dict[str, Dict] = field(default_factory=dict)
    consensus_reached: bool = False
    final_label: Optional[Dict] = None
    disagreement_notes: str = ""


class ConsensusManager:
    """
    Manages multi-annotator consensus for quality control
    """
    
    def __init__(
        self,
        min_annotators: int = 2,
        agreement_threshold: float = 0.8
    ):
        self.min_annotators = min_annotators
        self.agreement_threshold = agreement_threshold
        self.assignments: Dict[str, AnnotatorAssignment] = {}
    
    def create_assignment(
        self,
        item_id: str,
        annotator_ids: List[str]
    ) -> AnnotatorAssignment:
        """Create new annotation assignment"""
        assignment = AnnotatorAssignment(
            item_id=item_id,
            annotator_ids=annotator_ids[:self.min_annotators]
        )
        self.assignments[item_id] = assignment
        return assignment
    
    def submit_annotation(
        self,
        item_id: str,
        annotator_id: str,
        annotation: Dict
    ) -> bool:
        """
        Submit an annotation and check for consensus
        
        Returns True if consensus is reached
        """
        if item_id not in self.assignments:
            logger.warning(f"Unknown item: {item_id}")
            return False
        
        assignment = self.assignments[item_id]
        assignment.annotations[annotator_id] = annotation
        
        # Check if we have enough annotations
        if len(assignment.annotations) >= self.min_annotators:
            consensus = self._check_consensus(assignment)
            assignment.consensus_reached = consensus["reached"]
            assignment.final_label = consensus["final_label"]
            assignment.disagreement_notes = consensus.get("notes", "")
            return consensus["reached"]
        
        return False
    
    def _check_consensus(self, assignment: AnnotatorAssignment) -> Dict:
        """
        Check if annotators agree
        """
        annotations = list(assignment.annotations.values())
        
        # For categorical labels, use voting
        if all("label" in a or "intent" in a or "category" in a for a in annotations):
            # Get the primary label field
            label_field = "label" if "label" in annotations[0] else \
                          "intent" if "intent" in annotations[0] else "category"
            
            labels = [a.get(label_field) for a in annotations]
            counter = Counter(labels)
            most_common, count = counter.most_common(1)[0]
            
            agreement_ratio = count / len(labels)
            
            if agreement_ratio >= self.agreement_threshold:
                return {
                    "reached": True,
                    "final_label": {label_field: most_common},
                    "agreement_ratio": agreement_ratio,
                }
            else:
                return {
                    "reached": False,
                    "notes": f"Disagreement on {label_field}: {dict(counter)}",
                    "final_label": None,
                }
        
        # For text outputs (like summaries), require expert review
        return {
            "reached": False,
            "notes": "Text annotations require expert review",
            "final_label": None,
        }
    
    def get_disagreements(self) -> List[AnnotatorAssignment]:
        """Get all items with disagreements for expert review"""
        return [
            a for a in self.assignments.values()
            if len(a.annotations) >= self.min_annotators and not a.consensus_reached
        ]
    
    def resolve_disagreement(
        self,
        item_id: str,
        final_label: Dict,
        expert_id: str,
        notes: str = ""
    ):
        """Expert resolves a disagreement"""
        if item_id in self.assignments:
            assignment = self.assignments[item_id]
            assignment.final_label = final_label
            assignment.consensus_reached = True
            assignment.disagreement_notes = f"Resolved by {expert_id}: {notes}"
    
    def calculate_annotator_agreement(self) -> Dict[str, float]:
        """Calculate inter-annotator agreement metrics"""
        total_items = 0
        agreements = 0
        
        for assignment in self.assignments.values():
            if len(assignment.annotations) >= 2:
                total_items += 1
                if assignment.consensus_reached:
                    agreements += 1
        
        return {
            "total_items": total_items,
            "agreements": agreements,
            "agreement_rate": agreements / total_items if total_items > 0 else 0,
        }


# =============================================================================
# DEDUPLICATION FOR ANNOTATION
# =============================================================================

class AnnotationDeduplicator:
    """
    Deduplicates items before annotation to reduce redundant work
    """
    
    def __init__(self):
        self.seen_hashes: Dict[str, str] = {}  # hash -> first item id
    
    def compute_hash(self, item: Dict, fields: List[str] = None) -> str:
        """Compute content hash for an item"""
        if fields is None:
            fields = ["title", "description", "message", "text"]
        
        content = ""
        for field in fields:
            if field in item:
                content += str(item[field]).lower().strip()
        
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    def deduplicate(
        self,
        items: List[Dict],
        similarity_threshold: float = 0.95
    ) -> Tuple[List[Dict], List[Dict]]:
        """
        Deduplicate items for annotation
        
        Returns:
            (unique_items, duplicates)
        """
        unique_items = []
        duplicates = []
        
        for item in items:
            item_hash = self.compute_hash(item)
            
            if item_hash in self.seen_hashes:
                item["_duplicate_of"] = self.seen_hashes[item_hash]
                duplicates.append(item)
            else:
                item_id = item.get("id", str(len(unique_items)))
                self.seen_hashes[item_hash] = item_id
                item["_content_hash"] = item_hash
                unique_items.append(item)
        
        logger.info(f"Deduplication: {len(unique_items)} unique, {len(duplicates)} duplicates")
        return unique_items, duplicates
    
    def propagate_labels(
        self,
        labeled_items: List[Dict],
        duplicates: List[Dict]
    ) -> List[Dict]:
        """
        Propagate labels from unique items to their duplicates
        """
        # Build hash to label mapping
        hash_to_label = {}
        for item in labeled_items:
            item_hash = item.get("_content_hash")
            if item_hash and "label" in item:
                hash_to_label[item_hash] = item["label"]
        
        # Propagate to duplicates
        propagated = []
        for dup in duplicates:
            original_id = dup.get("_duplicate_of")
            if original_id in hash_to_label:
                dup["label"] = hash_to_label[original_id]
                dup["_label_propagated"] = True
                propagated.append(dup)
        
        logger.info(f"Propagated labels to {len(propagated)} duplicates")
        return propagated


# =============================================================================
# ANNOTATION QUALITY TRACKING
# =============================================================================

@dataclass
class AnnotatorStats:
    """Statistics for an individual annotator"""
    annotator_id: str
    total_annotations: int = 0
    agreements_with_consensus: int = 0
    disagreements: int = 0
    avg_time_per_item: float = 0.0
    last_active: Optional[datetime] = None
    
    @property
    def agreement_rate(self) -> float:
        if self.total_annotations == 0:
            return 0.0
        return self.agreements_with_consensus / self.total_annotations


class QualityTracker:
    """
    Tracks annotation quality for calibration
    """
    
    def __init__(self, benchmark_threshold: float = 0.9):
        self.benchmark_threshold = benchmark_threshold
        self.annotator_stats: Dict[str, AnnotatorStats] = {}
        self.benchmark_items: List[Dict] = []  # Gold standard items
    
    def add_benchmark_item(self, item: Dict, gold_label: Dict):
        """Add a benchmark item with known correct label"""
        self.benchmark_items.append({
            "item": item,
            "gold_label": gold_label,
        })
    
    def evaluate_annotator(
        self,
        annotator_id: str,
        annotations: List[Dict]
    ) -> Dict:
        """
        Evaluate annotator against benchmark items
        """
        if annotator_id not in self.annotator_stats:
            self.annotator_stats[annotator_id] = AnnotatorStats(annotator_id=annotator_id)
        
        stats = self.annotator_stats[annotator_id]
        correct = 0
        total = 0
        
        for annotation in annotations:
            item_id = annotation.get("item_id")
            
            # Find matching benchmark
            for benchmark in self.benchmark_items:
                if benchmark["item"].get("id") == item_id:
                    total += 1
                    if self._labels_match(annotation.get("label"), benchmark["gold_label"]):
                        correct += 1
                    break
        
        stats.total_annotations += total
        stats.agreements_with_consensus += correct
        stats.last_active = datetime.now()
        
        return {
            "annotator_id": annotator_id,
            "benchmark_accuracy": correct / total if total > 0 else 0,
            "passed": (correct / total) >= self.benchmark_threshold if total > 0 else False,
            "evaluated_items": total,
        }
    
    def _labels_match(self, label1: Any, label2: Any) -> bool:
        """Check if two labels match"""
        if isinstance(label1, dict) and isinstance(label2, dict):
            # Compare key fields
            for key in label2:
                if label1.get(key) != label2.get(key):
                    return False
            return True
        return label1 == label2
    
    def get_annotator_ranking(self) -> List[Dict]:
        """Get annotators ranked by quality"""
        rankings = []
        for stats in self.annotator_stats.values():
            rankings.append({
                "annotator_id": stats.annotator_id,
                "agreement_rate": stats.agreement_rate,
                "total_annotations": stats.total_annotations,
            })
        
        return sorted(rankings, key=lambda x: -x["agreement_rate"])
    
    def get_low_quality_annotators(self) -> List[str]:
        """Get annotators below quality threshold"""
        return [
            stats.annotator_id
            for stats in self.annotator_stats.values()
            if stats.agreement_rate < self.benchmark_threshold
            and stats.total_annotations >= 10  # Minimum sample size
        ]


# =============================================================================
# ANNOTATION PIPELINE ORCHESTRATOR
# =============================================================================

class AnnotationPipeline:
    """
    Orchestrates the complete annotation pipeline
    """
    
    def __init__(
        self,
        task_type: str,
        min_annotators: int = 2,
        use_pre_labeling: bool = True
    ):
        self.task_type = task_type
        self.pre_labeler = HeuristicPreLabeler() if use_pre_labeling else None
        self.deduplicator = AnnotationDeduplicator()
        self.consensus_manager = ConsensusManager(min_annotators=min_annotators)
        self.quality_tracker = QualityTracker()
    
    def prepare_for_annotation(
        self,
        items: List[Dict]
    ) -> Dict[str, List[Dict]]:
        """
        Prepare items for annotation
        
        Returns dict with:
        - auto_labeled: Items labeled by heuristics
        - for_annotation: Items needing human annotation
        - duplicates: Duplicate items (will get propagated labels)
        """
        # Step 1: Deduplicate
        unique_items, duplicates = self.deduplicator.deduplicate(items)
        
        # Step 2: Pre-label with heuristics
        if self.pre_labeler:
            auto_labeled, needs_annotation = self.pre_labeler.batch_pre_label(
                unique_items, self.task_type
            )
        else:
            auto_labeled = []
            needs_annotation = unique_items
        
        return {
            "auto_labeled": auto_labeled,
            "for_annotation": needs_annotation,
            "duplicates": duplicates,
        }
    
    def finalize_annotations(
        self,
        labeled_items: List[Dict],
        duplicates: List[Dict]
    ) -> List[Dict]:
        """
        Finalize annotations: propagate to duplicates, validate
        """
        # Propagate labels to duplicates
        propagated = self.deduplicator.propagate_labels(labeled_items, duplicates)
        
        # Combine all
        all_labeled = labeled_items + propagated
        
        return all_labeled
    
    def get_statistics(self) -> Dict:
        """Get pipeline statistics"""
        return {
            "consensus": self.consensus_manager.calculate_annotator_agreement(),
            "annotator_ranking": self.quality_tracker.get_annotator_ranking(),
            "low_quality_annotators": self.quality_tracker.get_low_quality_annotators(),
            "pending_disagreements": len(self.consensus_manager.get_disagreements()),
        }
