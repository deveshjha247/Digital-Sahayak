"""
Feedback Loop System
Continuously incorporates corrections, user feedback, and model errors
as new training examples for iterative improvement
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from enum import Enum
from pathlib import Path
import random

logger = logging.getLogger(__name__)


# =============================================================================
# FEEDBACK TYPES
# =============================================================================

class FeedbackType(Enum):
    """Types of feedback that can be collected"""
    USER_CORRECTION = "user_correction"          # User corrected model output
    OPERATOR_REVIEW = "operator_review"          # Operator reviewed and corrected
    MODEL_ERROR = "model_error"                  # Detected model prediction error
    IMPLICIT_POSITIVE = "implicit_positive"      # User accepted suggestion
    EXPLICIT_RATING = "explicit_rating"          # User rated response
    CONVERSATION_SUCCESS = "conversation_success"  # Successful task completion
    ESCALATION = "escalation"                    # User escalated to human


class FeedbackPriority(Enum):
    """Priority for incorporating feedback"""
    CRITICAL = 1    # Model completely wrong, high impact
    HIGH = 2        # Model wrong, needs correction
    MEDIUM = 3      # Model partially correct
    LOW = 4         # Minor improvement
    INFORMATIONAL = 5  # For analysis only


@dataclass
class FeedbackItem:
    """Represents a single piece of feedback"""
    feedback_id: str
    feedback_type: FeedbackType
    priority: FeedbackPriority
    
    # Original input/output
    input_data: Dict[str, Any]
    model_output: Any
    
    # Correction
    correct_output: Any
    correction_reason: str = ""
    
    # Metadata
    user_id: str = ""
    session_id: str = ""
    model_version: str = ""
    task_type: str = ""  # intent, job_match, form_fill, etc.
    
    # Status
    incorporated: bool = False
    incorporated_at: Optional[datetime] = None
    validated: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_training_example(self) -> Dict:
        """Convert to training example format"""
        return {
            "input": self.input_data,
            "label": self.correct_output,
            "source": f"feedback_{self.feedback_type.value}",
            "feedback_id": self.feedback_id,
            "priority": self.priority.value,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def create(
        cls,
        feedback_type: FeedbackType,
        input_data: Dict,
        model_output: Any,
        correct_output: Any,
        **kwargs
    ) -> "FeedbackItem":
        """Create new feedback item"""
        content = json.dumps({
            "input": input_data,
            "output": model_output,
            "correct": correct_output,
            "time": datetime.now().isoformat(),
        }, sort_keys=True, default=str)
        feedback_id = f"fb_{hashlib.md5(content.encode()).hexdigest()[:12]}"
        
        # Auto-determine priority
        priority = cls._determine_priority(model_output, correct_output, feedback_type)
        
        return cls(
            feedback_id=feedback_id,
            feedback_type=feedback_type,
            priority=priority,
            input_data=input_data,
            model_output=model_output,
            correct_output=correct_output,
            **kwargs,
        )
    
    @staticmethod
    def _determine_priority(
        model_output: Any,
        correct_output: Any,
        feedback_type: FeedbackType
    ) -> FeedbackPriority:
        """Automatically determine priority based on error type"""
        # Escalation always high priority
        if feedback_type == FeedbackType.ESCALATION:
            return FeedbackPriority.CRITICAL
        
        # Complete mismatch
        if model_output != correct_output:
            if feedback_type == FeedbackType.OPERATOR_REVIEW:
                return FeedbackPriority.HIGH
            return FeedbackPriority.MEDIUM
        
        return FeedbackPriority.LOW


# =============================================================================
# FEEDBACK COLLECTOR
# =============================================================================

class FeedbackCollector:
    """
    Collects and stores feedback from various sources
    """
    
    def __init__(self, storage_path: str = None):
        self.feedback_items: Dict[str, FeedbackItem] = {}
        self.storage_path = Path(storage_path) if storage_path else None
        
        # Statistics
        self.stats = defaultdict(int)
        
        if self.storage_path:
            self._load_feedback()
    
    def collect_user_correction(
        self,
        input_data: Dict,
        model_output: Any,
        user_correction: Any,
        user_id: str = "",
        reason: str = ""
    ) -> FeedbackItem:
        """Collect user correction feedback"""
        feedback = FeedbackItem.create(
            feedback_type=FeedbackType.USER_CORRECTION,
            input_data=input_data,
            model_output=model_output,
            correct_output=user_correction,
            user_id=user_id,
            correction_reason=reason,
        )
        
        self._store_feedback(feedback)
        logger.info(f"Collected user correction: {feedback.feedback_id}")
        return feedback
    
    def collect_operator_review(
        self,
        input_data: Dict,
        model_output: Any,
        correct_output: Any,
        operator_id: str,
        reason: str = ""
    ) -> FeedbackItem:
        """Collect operator review feedback"""
        feedback = FeedbackItem.create(
            feedback_type=FeedbackType.OPERATOR_REVIEW,
            input_data=input_data,
            model_output=model_output,
            correct_output=correct_output,
            user_id=operator_id,
            correction_reason=reason,
        )
        feedback.validated = True  # Operator reviews are pre-validated
        
        self._store_feedback(feedback)
        logger.info(f"Collected operator review: {feedback.feedback_id}")
        return feedback
    
    def collect_model_error(
        self,
        input_data: Dict,
        predicted_output: Any,
        actual_output: Any,
        model_version: str,
        task_type: str
    ) -> FeedbackItem:
        """Collect detected model error"""
        feedback = FeedbackItem.create(
            feedback_type=FeedbackType.MODEL_ERROR,
            input_data=input_data,
            model_output=predicted_output,
            correct_output=actual_output,
            model_version=model_version,
            task_type=task_type,
        )
        
        self._store_feedback(feedback)
        logger.info(f"Collected model error: {feedback.feedback_id}")
        return feedback
    
    def collect_implicit_positive(
        self,
        input_data: Dict,
        model_output: Any,
        user_id: str = "",
        session_id: str = ""
    ) -> FeedbackItem:
        """Collect implicit positive feedback (user accepted suggestion)"""
        feedback = FeedbackItem.create(
            feedback_type=FeedbackType.IMPLICIT_POSITIVE,
            input_data=input_data,
            model_output=model_output,
            correct_output=model_output,  # Same as model output
            user_id=user_id,
            session_id=session_id,
        )
        
        self._store_feedback(feedback)
        return feedback
    
    def collect_explicit_rating(
        self,
        input_data: Dict,
        model_output: Any,
        rating: int,  # 1-5 stars
        user_id: str = "",
        comment: str = ""
    ) -> FeedbackItem:
        """Collect explicit user rating"""
        # Rating of 4-5 is positive, 1-2 needs correction
        if rating >= 4:
            correct_output = model_output
            priority = FeedbackPriority.LOW
        elif rating <= 2:
            correct_output = None  # Needs manual correction
            priority = FeedbackPriority.HIGH
        else:
            correct_output = model_output
            priority = FeedbackPriority.MEDIUM
        
        feedback = FeedbackItem(
            feedback_id=f"fb_{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]}",
            feedback_type=FeedbackType.EXPLICIT_RATING,
            priority=priority,
            input_data=input_data,
            model_output=model_output,
            correct_output=correct_output,
            user_id=user_id,
            correction_reason=f"Rating: {rating}/5. {comment}",
        )
        
        self._store_feedback(feedback)
        return feedback
    
    def collect_escalation(
        self,
        input_data: Dict,
        model_output: Any,
        escalation_reason: str,
        user_id: str = "",
        session_id: str = ""
    ) -> FeedbackItem:
        """Collect escalation to human agent"""
        feedback = FeedbackItem.create(
            feedback_type=FeedbackType.ESCALATION,
            input_data=input_data,
            model_output=model_output,
            correct_output=None,  # Needs human resolution
            user_id=user_id,
            session_id=session_id,
            correction_reason=escalation_reason,
        )
        
        self._store_feedback(feedback)
        logger.warning(f"Escalation recorded: {feedback.feedback_id}")
        return feedback
    
    def _store_feedback(self, feedback: FeedbackItem):
        """Store feedback item"""
        self.feedback_items[feedback.feedback_id] = feedback
        self.stats[feedback.feedback_type.value] += 1
        self.stats["total"] += 1
        
        if self.storage_path:
            self._save_feedback()
    
    def _load_feedback(self):
        """Load feedback from storage"""
        feedback_file = self.storage_path / "feedback.json"
        if feedback_file.exists():
            with open(feedback_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item_data in data.get("items", []):
                    # Reconstruct FeedbackItem
                    item = FeedbackItem(
                        feedback_id=item_data["feedback_id"],
                        feedback_type=FeedbackType(item_data["feedback_type"]),
                        priority=FeedbackPriority(item_data["priority"]),
                        input_data=item_data["input_data"],
                        model_output=item_data["model_output"],
                        correct_output=item_data["correct_output"],
                        correction_reason=item_data.get("correction_reason", ""),
                        user_id=item_data.get("user_id", ""),
                        incorporated=item_data.get("incorporated", False),
                        validated=item_data.get("validated", False),
                    )
                    self.feedback_items[item.feedback_id] = item
    
    def _save_feedback(self):
        """Save feedback to storage"""
        self.storage_path.mkdir(parents=True, exist_ok=True)
        feedback_file = self.storage_path / "feedback.json"
        
        data = {
            "items": [
                {
                    "feedback_id": item.feedback_id,
                    "feedback_type": item.feedback_type.value,
                    "priority": item.priority.value,
                    "input_data": item.input_data,
                    "model_output": item.model_output,
                    "correct_output": item.correct_output,
                    "correction_reason": item.correction_reason,
                    "user_id": item.user_id,
                    "incorporated": item.incorporated,
                    "validated": item.validated,
                    "created_at": item.created_at.isoformat(),
                }
                for item in self.feedback_items.values()
            ],
            "stats": dict(self.stats),
            "saved_at": datetime.now().isoformat(),
        }
        
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, default=str, ensure_ascii=False)
    
    def get_pending_feedback(
        self,
        min_priority: FeedbackPriority = FeedbackPriority.MEDIUM,
        task_type: str = None,
        limit: int = None
    ) -> List[FeedbackItem]:
        """Get feedback items pending incorporation"""
        pending = [
            item for item in self.feedback_items.values()
            if not item.incorporated
            and item.priority.value <= min_priority.value
            and item.correct_output is not None
            and (task_type is None or item.task_type == task_type)
        ]
        
        # Sort by priority
        pending.sort(key=lambda x: (x.priority.value, x.created_at))
        
        if limit:
            pending = pending[:limit]
        
        return pending
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get feedback statistics"""
        by_type = defaultdict(int)
        by_priority = defaultdict(int)
        incorporated = 0
        pending = 0
        
        for item in self.feedback_items.values():
            by_type[item.feedback_type.value] += 1
            by_priority[item.priority.name] += 1
            if item.incorporated:
                incorporated += 1
            else:
                pending += 1
        
        return {
            "total": len(self.feedback_items),
            "incorporated": incorporated,
            "pending": pending,
            "by_type": dict(by_type),
            "by_priority": dict(by_priority),
        }


# =============================================================================
# FEEDBACK INTEGRATOR
# =============================================================================

class FeedbackIntegrator:
    """
    Integrates collected feedback into training datasets
    """
    
    def __init__(
        self,
        collector: FeedbackCollector,
        min_confidence_threshold: float = 0.7
    ):
        self.collector = collector
        self.min_confidence = min_confidence_threshold
        
        # Integration rules
        self.validation_rules: Dict[str, Callable] = {}
    
    def add_validation_rule(self, task_type: str, rule: Callable[[FeedbackItem], bool]):
        """Add validation rule for specific task type"""
        self.validation_rules[task_type] = rule
    
    def validate_feedback(self, feedback: FeedbackItem) -> bool:
        """Validate feedback before integration"""
        # Already validated by operator
        if feedback.validated:
            return True
        
        # Check task-specific validation rules
        if feedback.task_type in self.validation_rules:
            rule = self.validation_rules[feedback.task_type]
            return rule(feedback)
        
        # Default: trust high-priority feedback
        return feedback.priority.value <= FeedbackPriority.MEDIUM.value
    
    def integrate_to_dataset(
        self,
        existing_dataset: List[Dict],
        max_feedback_ratio: float = 0.1,  # Max 10% from feedback
        deduplicate: bool = True
    ) -> tuple[List[Dict], Dict]:
        """
        Integrate validated feedback into existing dataset
        
        Returns:
            (updated_dataset, integration_report)
        """
        pending = self.collector.get_pending_feedback()
        
        # Filter to validated only
        to_integrate = []
        skipped = []
        
        for feedback in pending:
            if self.validate_feedback(feedback):
                to_integrate.append(feedback)
            else:
                skipped.append(feedback.feedback_id)
        
        # Limit by ratio
        max_items = int(len(existing_dataset) * max_feedback_ratio)
        to_integrate = to_integrate[:max_items]
        
        # Convert to training examples
        new_examples = []
        for feedback in to_integrate:
            example = feedback.to_training_example()
            
            # Deduplicate
            if deduplicate:
                example_hash = hashlib.md5(
                    json.dumps(example["input"], sort_keys=True).encode()
                ).hexdigest()
                
                # Check if already in dataset
                is_duplicate = any(
                    hashlib.md5(json.dumps(item.get("input", item), sort_keys=True, default=str).encode()).hexdigest() == example_hash
                    for item in existing_dataset
                )
                
                if is_duplicate:
                    skipped.append(feedback.feedback_id)
                    continue
            
            new_examples.append(example)
            
            # Mark as incorporated
            feedback.incorporated = True
            feedback.incorporated_at = datetime.now()
        
        # Combine datasets
        updated_dataset = existing_dataset + new_examples
        
        # Save updated feedback state
        if self.collector.storage_path:
            self.collector._save_feedback()
        
        report = {
            "original_size": len(existing_dataset),
            "feedback_pending": len(pending),
            "validated": len(to_integrate),
            "integrated": len(new_examples),
            "skipped": len(skipped),
            "final_size": len(updated_dataset),
            "feedback_ratio": len(new_examples) / len(updated_dataset) if updated_dataset else 0,
        }
        
        logger.info(f"Integrated {len(new_examples)} feedback items into dataset")
        return updated_dataset, report
    
    def create_hard_examples_dataset(
        self,
        min_priority: FeedbackPriority = FeedbackPriority.HIGH
    ) -> List[Dict]:
        """
        Create dataset of hard examples from high-priority feedback
        Useful for focused fine-tuning on difficult cases
        """
        hard_examples = []
        
        for feedback in self.collector.feedback_items.values():
            if feedback.priority.value <= min_priority.value:
                if feedback.correct_output is not None:
                    hard_examples.append(feedback.to_training_example())
        
        logger.info(f"Created hard examples dataset with {len(hard_examples)} items")
        return hard_examples


# =============================================================================
# ERROR PATTERN ANALYZER
# =============================================================================

class ErrorPatternAnalyzer:
    """
    Analyzes feedback to identify systematic error patterns
    """
    
    def __init__(self, collector: FeedbackCollector):
        self.collector = collector
    
    def analyze_error_patterns(
        self,
        task_type: str = None,
        min_occurrences: int = 3
    ) -> Dict[str, Any]:
        """
        Identify recurring error patterns
        """
        # Group errors by predicted vs actual
        error_patterns = defaultdict(list)
        
        for feedback in self.collector.feedback_items.values():
            if feedback.feedback_type not in [
                FeedbackType.USER_CORRECTION,
                FeedbackType.OPERATOR_REVIEW,
                FeedbackType.MODEL_ERROR,
            ]:
                continue
            
            if task_type and feedback.task_type != task_type:
                continue
            
            # Create pattern key
            pattern_key = f"{feedback.model_output} -> {feedback.correct_output}"
            error_patterns[pattern_key].append(feedback)
        
        # Find recurring patterns
        recurring = {
            pattern: {
                "count": len(items),
                "predicted": items[0].model_output,
                "correct": items[0].correct_output,
                "sample_inputs": [i.input_data for i in items[:3]],
                "reasons": [i.correction_reason for i in items if i.correction_reason],
            }
            for pattern, items in error_patterns.items()
            if len(items) >= min_occurrences
        }
        
        # Sort by frequency
        sorted_patterns = dict(
            sorted(recurring.items(), key=lambda x: x[1]["count"], reverse=True)
        )
        
        return {
            "total_errors": sum(len(items) for items in error_patterns.values()),
            "unique_patterns": len(error_patterns),
            "recurring_patterns": len(sorted_patterns),
            "patterns": sorted_patterns,
        }
    
    def suggest_guideline_updates(
        self,
        patterns: Dict[str, Any]
    ) -> List[Dict]:
        """
        Suggest annotation guideline updates based on error patterns
        """
        suggestions = []
        
        for pattern_key, pattern_data in patterns.get("patterns", {}).items():
            if pattern_data["count"] >= 5:
                suggestion = {
                    "type": "high_frequency_error",
                    "pattern": pattern_key,
                    "frequency": pattern_data["count"],
                    "suggestion": f"Add explicit guideline to clarify: "
                                 f"'{pattern_data['predicted']}' should be labeled as "
                                 f"'{pattern_data['correct']}'",
                    "examples": pattern_data["sample_inputs"],
                }
                suggestions.append(suggestion)
        
        return suggestions
    
    def identify_ambiguous_categories(self) -> List[Dict]:
        """
        Identify categories that are frequently confused
        """
        confusion_matrix = defaultdict(lambda: defaultdict(int))
        
        for feedback in self.collector.feedback_items.values():
            if feedback.model_output and feedback.correct_output:
                if feedback.model_output != feedback.correct_output:
                    confusion_matrix[feedback.model_output][feedback.correct_output] += 1
        
        ambiguous = []
        for predicted, corrections in confusion_matrix.items():
            for correct, count in corrections.items():
                if count >= 3:
                    ambiguous.append({
                        "predicted_category": predicted,
                        "correct_category": correct,
                        "confusion_count": count,
                        "recommendation": f"Clarify distinction between '{predicted}' and '{correct}' in guidelines",
                    })
        
        # Sort by confusion count
        ambiguous.sort(key=lambda x: x["confusion_count"], reverse=True)
        
        return ambiguous


# =============================================================================
# CONTINUOUS LEARNING MANAGER
# =============================================================================

class ContinuousLearningManager:
    """
    Orchestrates the continuous learning feedback loop
    """
    
    def __init__(
        self,
        feedback_storage_path: str,
        retrain_threshold: int = 100,  # Retrain after N feedback items
        min_feedback_quality: float = 0.8
    ):
        self.collector = FeedbackCollector(feedback_storage_path)
        self.integrator = FeedbackIntegrator(self.collector)
        self.error_analyzer = ErrorPatternAnalyzer(self.collector)
        
        self.retrain_threshold = retrain_threshold
        self.min_feedback_quality = min_feedback_quality
        
        # Callbacks
        self.on_retrain_needed: Optional[Callable] = None
        self.on_guideline_update_needed: Optional[Callable] = None
    
    def process_feedback(
        self,
        feedback_type: str,
        input_data: Dict,
        model_output: Any,
        correct_output: Any = None,
        **kwargs
    ) -> FeedbackItem:
        """
        Process incoming feedback
        """
        feedback_type_enum = FeedbackType(feedback_type)
        
        if feedback_type_enum == FeedbackType.USER_CORRECTION:
            feedback = self.collector.collect_user_correction(
                input_data, model_output, correct_output, **kwargs
            )
        elif feedback_type_enum == FeedbackType.OPERATOR_REVIEW:
            feedback = self.collector.collect_operator_review(
                input_data, model_output, correct_output, **kwargs
            )
        elif feedback_type_enum == FeedbackType.MODEL_ERROR:
            feedback = self.collector.collect_model_error(
                input_data, model_output, correct_output, **kwargs
            )
        else:
            feedback = FeedbackItem.create(
                feedback_type_enum, input_data, model_output, correct_output, **kwargs
            )
            self.collector._store_feedback(feedback)
        
        # Check if retrain threshold reached
        self._check_retrain_trigger()
        
        return feedback
    
    def _check_retrain_trigger(self):
        """Check if retraining should be triggered"""
        stats = self.collector.get_statistics()
        pending = stats["pending"]
        
        if pending >= self.retrain_threshold:
            logger.info(f"Retrain threshold reached: {pending} pending feedback items")
            if self.on_retrain_needed:
                self.on_retrain_needed(pending)
    
    def run_improvement_cycle(
        self,
        current_dataset: List[Dict]
    ) -> Dict[str, Any]:
        """
        Run a complete improvement cycle
        
        1. Integrate feedback into dataset
        2. Analyze error patterns
        3. Suggest guideline updates
        4. Return improvement report
        """
        # 1. Integrate feedback
        updated_dataset, integration_report = self.integrator.integrate_to_dataset(
            current_dataset
        )
        
        # 2. Analyze errors
        error_patterns = self.error_analyzer.analyze_error_patterns()
        
        # 3. Get guideline suggestions
        guideline_suggestions = self.error_analyzer.suggest_guideline_updates(error_patterns)
        ambiguous_categories = self.error_analyzer.identify_ambiguous_categories()
        
        # 4. Compile report
        report = {
            "timestamp": datetime.now().isoformat(),
            "integration": integration_report,
            "error_analysis": error_patterns,
            "guideline_suggestions": guideline_suggestions,
            "ambiguous_categories": ambiguous_categories,
            "updated_dataset_size": len(updated_dataset),
            "recommendations": self._generate_recommendations(
                integration_report, error_patterns, guideline_suggestions
            ),
        }
        
        # Trigger guideline update callback if needed
        if guideline_suggestions and self.on_guideline_update_needed:
            self.on_guideline_update_needed(guideline_suggestions)
        
        return report, updated_dataset
    
    def _generate_recommendations(
        self,
        integration: Dict,
        errors: Dict,
        suggestions: List
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # High feedback volume
        if integration["feedback_pending"] > 50:
            recommendations.append(
                f"High feedback volume ({integration['feedback_pending']} pending). "
                "Consider increasing integration frequency."
            )
        
        # Recurring error patterns
        if errors["recurring_patterns"] > 5:
            recommendations.append(
                f"Found {errors['recurring_patterns']} recurring error patterns. "
                "Review and update annotation guidelines."
            )
        
        # Guideline updates needed
        if suggestions:
            recommendations.append(
                f"{len(suggestions)} guideline updates suggested. "
                "Review ambiguous category definitions."
            )
        
        if not recommendations:
            recommendations.append("No immediate actions needed. Continue monitoring.")
        
        return recommendations


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_feedback_loop(storage_path: str) -> ContinuousLearningManager:
    """Create pre-configured continuous learning manager"""
    return ContinuousLearningManager(storage_path)


def collect_user_feedback(
    collector: FeedbackCollector,
    input_data: Dict,
    model_output: Any,
    user_correction: Any,
    user_id: str = ""
) -> FeedbackItem:
    """Convenience function to collect user feedback"""
    return collector.collect_user_correction(
        input_data, model_output, user_correction, user_id
    )
