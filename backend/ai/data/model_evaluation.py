"""
Model Evaluation and Monitoring System
Regular evaluation on validation set with automatic dataset/guideline updates
when models fail on specific patterns
"""

import logging
import json
import hashlib
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict, Counter
from enum import Enum
from pathlib import Path
import random

logger = logging.getLogger(__name__)


# =============================================================================
# EVALUATION METRICS
# =============================================================================

class EvaluationMetrics:
    """
    Computes various evaluation metrics for classification models
    """
    
    @staticmethod
    def accuracy(y_true: List, y_pred: List) -> float:
        """Compute accuracy"""
        if len(y_true) != len(y_pred) or len(y_true) == 0:
            return 0.0
        
        correct = sum(1 for t, p in zip(y_true, y_pred) if t == p)
        return correct / len(y_true)
    
    @staticmethod
    def precision_recall_f1(
        y_true: List,
        y_pred: List,
        average: str = "macro"
    ) -> Dict[str, float]:
        """
        Compute precision, recall, and F1 score
        
        Args:
            average: 'macro' for unweighted mean, 'weighted' for weighted mean
        """
        labels = list(set(y_true) | set(y_pred))
        
        metrics_per_class = {}
        
        for label in labels:
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
            
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics_per_class[label] = {
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "support": sum(1 for t in y_true if t == label),
            }
        
        # Compute average
        if average == "macro":
            avg_precision = sum(m["precision"] for m in metrics_per_class.values()) / len(labels)
            avg_recall = sum(m["recall"] for m in metrics_per_class.values()) / len(labels)
            avg_f1 = sum(m["f1"] for m in metrics_per_class.values()) / len(labels)
        else:  # weighted
            total_support = sum(m["support"] for m in metrics_per_class.values())
            avg_precision = sum(m["precision"] * m["support"] for m in metrics_per_class.values()) / total_support
            avg_recall = sum(m["recall"] * m["support"] for m in metrics_per_class.values()) / total_support
            avg_f1 = sum(m["f1"] * m["support"] for m in metrics_per_class.values()) / total_support
        
        return {
            "precision": round(avg_precision, 4),
            "recall": round(avg_recall, 4),
            "f1": round(avg_f1, 4),
            "per_class": {k: {kk: round(vv, 4) for kk, vv in v.items()} for k, v in metrics_per_class.items()},
        }
    
    @staticmethod
    def confusion_matrix(y_true: List, y_pred: List) -> Dict[str, Dict[str, int]]:
        """Build confusion matrix"""
        labels = sorted(set(y_true) | set(y_pred))
        matrix = {label: {l: 0 for l in labels} for label in labels}
        
        for t, p in zip(y_true, y_pred):
            matrix[t][p] += 1
        
        return matrix
    
    @staticmethod
    def top_k_accuracy(
        y_true: List,
        y_pred_probs: List[Dict[str, float]],
        k: int = 3
    ) -> float:
        """
        Compute top-k accuracy (correct if true label in top k predictions)
        
        Args:
            y_pred_probs: List of {label: probability} dicts
        """
        correct = 0
        
        for true_label, probs in zip(y_true, y_pred_probs):
            top_k = sorted(probs.items(), key=lambda x: x[1], reverse=True)[:k]
            top_k_labels = [label for label, _ in top_k]
            if true_label in top_k_labels:
                correct += 1
        
        return correct / len(y_true) if y_true else 0


# =============================================================================
# FAILURE PATTERN DETECTOR
# =============================================================================

@dataclass
class FailurePattern:
    """Represents a detected failure pattern"""
    pattern_id: str
    pattern_type: str  # class_confusion, low_confidence, input_pattern, etc.
    description: str
    
    # Affected data
    affected_samples: List[Dict] = field(default_factory=list)
    frequency: int = 0
    
    # Analysis
    true_labels: List = field(default_factory=list)
    predicted_labels: List = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    # Severity
    severity: str = "medium"  # low, medium, high, critical
    
    def to_dict(self) -> Dict:
        return {
            "pattern_id": self.pattern_id,
            "pattern_type": self.pattern_type,
            "description": self.description,
            "frequency": self.frequency,
            "severity": self.severity,
            "recommendations": self.recommendations,
            "sample_count": len(self.affected_samples),
        }


class FailurePatternDetector:
    """
    Detects systematic failure patterns in model predictions
    """
    
    def __init__(
        self,
        confusion_threshold: int = 5,  # Min confusions to flag
        low_class_f1_threshold: float = 0.5,  # F1 below this is concerning
    ):
        self.confusion_threshold = confusion_threshold
        self.low_class_f1_threshold = low_class_f1_threshold
    
    def detect_patterns(
        self,
        evaluation_results: List[Dict],
        predictions: List[Dict]
    ) -> List[FailurePattern]:
        """
        Detect failure patterns from evaluation results
        
        Args:
            evaluation_results: List of {input, true_label, predicted_label, confidence}
            predictions: Raw prediction outputs
        """
        patterns = []
        
        # 1. Detect class confusion patterns
        confusion_patterns = self._detect_class_confusion(evaluation_results)
        patterns.extend(confusion_patterns)
        
        # 2. Detect low-confidence failures
        low_conf_patterns = self._detect_low_confidence_failures(evaluation_results)
        patterns.extend(low_conf_patterns)
        
        # 3. Detect input-based patterns
        input_patterns = self._detect_input_patterns(evaluation_results)
        patterns.extend(input_patterns)
        
        # 4. Detect class-specific issues
        class_patterns = self._detect_class_issues(evaluation_results)
        patterns.extend(class_patterns)
        
        return patterns
    
    def _detect_class_confusion(
        self,
        results: List[Dict]
    ) -> List[FailurePattern]:
        """Detect frequently confused class pairs"""
        patterns = []
        confusion_counts = defaultdict(list)
        
        for result in results:
            true_label = result.get("true_label")
            pred_label = result.get("predicted_label")
            
            if true_label != pred_label:
                key = f"{true_label} -> {pred_label}"
                confusion_counts[key].append(result)
        
        for confusion_key, samples in confusion_counts.items():
            if len(samples) >= self.confusion_threshold:
                true_label, pred_label = confusion_key.split(" -> ")
                
                pattern = FailurePattern(
                    pattern_id=f"confusion_{hashlib.md5(confusion_key.encode()).hexdigest()[:8]}",
                    pattern_type="class_confusion",
                    description=f"Model frequently confuses '{true_label}' with '{pred_label}'",
                    affected_samples=samples,
                    frequency=len(samples),
                    true_labels=[true_label] * len(samples),
                    predicted_labels=[pred_label] * len(samples),
                    severity="high" if len(samples) >= self.confusion_threshold * 2 else "medium",
                    recommendations=[
                        f"Add more training examples for '{true_label}'",
                        f"Clarify distinction between '{true_label}' and '{pred_label}' in guidelines",
                        f"Consider creating disambiguation examples",
                    ],
                )
                patterns.append(pattern)
        
        return patterns
    
    def _detect_low_confidence_failures(
        self,
        results: List[Dict]
    ) -> List[FailurePattern]:
        """Detect failures on low-confidence predictions"""
        patterns = []
        low_conf_failures = []
        
        for result in results:
            confidence = result.get("confidence", 1.0)
            true_label = result.get("true_label")
            pred_label = result.get("predicted_label")
            
            if true_label != pred_label and confidence < 0.6:
                low_conf_failures.append(result)
        
        if len(low_conf_failures) >= 3:
            pattern = FailurePattern(
                pattern_id="low_confidence_failures",
                pattern_type="low_confidence",
                description="Model fails on low-confidence predictions",
                affected_samples=low_conf_failures,
                frequency=len(low_conf_failures),
                severity="medium",
                recommendations=[
                    "Consider adding confidence threshold for predictions",
                    "Route low-confidence cases to human review",
                    "Add more training data for ambiguous cases",
                ],
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_input_patterns(
        self,
        results: List[Dict]
    ) -> List[FailurePattern]:
        """Detect patterns in failed inputs"""
        patterns = []
        failures = [r for r in results if r.get("true_label") != r.get("predicted_label")]
        
        if not failures:
            return patterns
        
        # Check for language patterns
        hindi_failures = [f for f in failures if self._contains_hindi(f.get("input", {}).get("message", ""))]
        english_failures = [f for f in failures if not self._contains_hindi(f.get("input", {}).get("message", ""))]
        
        total_failures = len(failures)
        
        if len(hindi_failures) > total_failures * 0.7:
            pattern = FailurePattern(
                pattern_id="hindi_input_failures",
                pattern_type="input_pattern",
                description="Model performs poorly on Hindi inputs",
                affected_samples=hindi_failures,
                frequency=len(hindi_failures),
                severity="high",
                recommendations=[
                    "Add more Hindi training examples",
                    "Balance Hindi/English ratio in training data",
                    "Consider Hindi-specific preprocessing",
                ],
            )
            patterns.append(pattern)
        
        # Check for short input failures
        short_failures = [f for f in failures if len(f.get("input", {}).get("message", "")) < 20]
        if len(short_failures) > total_failures * 0.5:
            pattern = FailurePattern(
                pattern_id="short_input_failures",
                pattern_type="input_pattern",
                description="Model performs poorly on short inputs",
                affected_samples=short_failures,
                frequency=len(short_failures),
                severity="medium",
                recommendations=[
                    "Add more short-form training examples",
                    "Consider character-level features for short texts",
                ],
            )
            patterns.append(pattern)
        
        return patterns
    
    def _detect_class_issues(
        self,
        results: List[Dict]
    ) -> List[FailurePattern]:
        """Detect classes with poor performance"""
        patterns = []
        
        # Group by true label
        by_class = defaultdict(list)
        for result in results:
            by_class[result.get("true_label")].append(result)
        
        for class_label, class_results in by_class.items():
            correct = sum(1 for r in class_results if r.get("true_label") == r.get("predicted_label"))
            accuracy = correct / len(class_results) if class_results else 0
            
            if accuracy < 0.6 and len(class_results) >= 5:
                pattern = FailurePattern(
                    pattern_id=f"poor_class_{class_label}",
                    pattern_type="class_performance",
                    description=f"Class '{class_label}' has low accuracy ({accuracy:.1%})",
                    affected_samples=[r for r in class_results if r.get("true_label") != r.get("predicted_label")],
                    frequency=len(class_results) - correct,
                    severity="high" if accuracy < 0.4 else "medium",
                    recommendations=[
                        f"Add more training examples for '{class_label}'",
                        f"Review annotation quality for '{class_label}'",
                        f"Consider if '{class_label}' needs to be split or merged",
                    ],
                )
                patterns.append(pattern)
        
        return patterns
    
    def _contains_hindi(self, text: str) -> bool:
        """Check if text contains Hindi characters"""
        hindi_range = range(0x0900, 0x097F)
        return any(ord(char) in hindi_range for char in text)


# =============================================================================
# MODEL EVALUATOR
# =============================================================================

@dataclass
class EvaluationRun:
    """Represents a single evaluation run"""
    run_id: str
    model_version: str
    dataset_version: str
    timestamp: datetime
    
    # Metrics
    accuracy: float
    precision: float
    recall: float
    f1: float
    
    # Detailed results
    per_class_metrics: Dict[str, Dict] = field(default_factory=dict)
    confusion_matrix: Dict = field(default_factory=dict)
    
    # Failure analysis
    failure_patterns: List[FailurePattern] = field(default_factory=list)
    
    # Metadata
    sample_count: int = 0
    evaluation_duration: float = 0.0


class ModelEvaluator:
    """
    Evaluates models and tracks performance over time
    """
    
    def __init__(
        self,
        evaluation_history_path: str = None,
        performance_threshold: float = 0.8,  # Minimum acceptable F1
        degradation_threshold: float = 0.05,  # Alert if F1 drops by this much
    ):
        self.history_path = Path(evaluation_history_path) if evaluation_history_path else None
        self.performance_threshold = performance_threshold
        self.degradation_threshold = degradation_threshold
        
        self.evaluation_history: List[EvaluationRun] = []
        self.pattern_detector = FailurePatternDetector()
        
        if self.history_path:
            self._load_history()
    
    def evaluate(
        self,
        validation_data: List[Dict],
        predict_fn: Callable[[Dict], Tuple[Any, float]],
        model_version: str,
        dataset_version: str,
        text_key: str = "message",
        label_key: str = "label"
    ) -> EvaluationRun:
        """
        Run evaluation on validation dataset
        
        Args:
            validation_data: List of {input, label} items
            predict_fn: Function that takes input and returns (prediction, confidence)
            model_version: Version identifier for the model
            dataset_version: Version identifier for the dataset
        
        Returns:
            EvaluationRun with all metrics and analysis
        """
        start_time = datetime.now()
        
        y_true = []
        y_pred = []
        evaluation_results = []
        
        for item in validation_data:
            true_label = item.get(label_key)
            input_data = {k: v for k, v in item.items() if k != label_key}
            
            try:
                predicted_label, confidence = predict_fn(input_data)
            except Exception as e:
                logger.warning(f"Prediction failed: {e}")
                predicted_label = None
                confidence = 0.0
            
            y_true.append(true_label)
            y_pred.append(predicted_label)
            
            evaluation_results.append({
                "input": input_data,
                "true_label": true_label,
                "predicted_label": predicted_label,
                "confidence": confidence,
                "correct": true_label == predicted_label,
            })
        
        # Compute metrics
        accuracy = EvaluationMetrics.accuracy(y_true, y_pred)
        prf = EvaluationMetrics.precision_recall_f1(y_true, y_pred)
        cm = EvaluationMetrics.confusion_matrix(y_true, y_pred)
        
        # Detect failure patterns
        patterns = self.pattern_detector.detect_patterns(evaluation_results, y_pred)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Create evaluation run
        run = EvaluationRun(
            run_id=f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            model_version=model_version,
            dataset_version=dataset_version,
            timestamp=datetime.now(),
            accuracy=round(accuracy, 4),
            precision=prf["precision"],
            recall=prf["recall"],
            f1=prf["f1"],
            per_class_metrics=prf["per_class"],
            confusion_matrix=cm,
            failure_patterns=patterns,
            sample_count=len(validation_data),
            evaluation_duration=duration,
        )
        
        # Store in history
        self.evaluation_history.append(run)
        if self.history_path:
            self._save_history()
        
        logger.info(
            f"Evaluation complete: accuracy={accuracy:.2%}, F1={prf['f1']:.4f}, "
            f"patterns={len(patterns)}"
        )
        
        return run
    
    def check_performance_alerts(
        self,
        current_run: EvaluationRun
    ) -> List[Dict]:
        """
        Check for performance issues and generate alerts
        """
        alerts = []
        
        # Check absolute threshold
        if current_run.f1 < self.performance_threshold:
            alerts.append({
                "type": "below_threshold",
                "severity": "high",
                "message": f"F1 score ({current_run.f1:.4f}) below threshold ({self.performance_threshold})",
                "recommendation": "Review training data and model configuration",
            })
        
        # Check for degradation
        if len(self.evaluation_history) >= 2:
            prev_run = self.evaluation_history[-2]
            f1_drop = prev_run.f1 - current_run.f1
            
            if f1_drop > self.degradation_threshold:
                alerts.append({
                    "type": "performance_degradation",
                    "severity": "high",
                    "message": f"F1 dropped by {f1_drop:.4f} from previous evaluation",
                    "previous_f1": prev_run.f1,
                    "current_f1": current_run.f1,
                    "recommendation": "Investigate recent changes to data or model",
                })
        
        # Check failure patterns
        critical_patterns = [p for p in current_run.failure_patterns if p.severity in ["high", "critical"]]
        if critical_patterns:
            alerts.append({
                "type": "critical_failure_patterns",
                "severity": "high",
                "message": f"Found {len(critical_patterns)} critical failure patterns",
                "patterns": [p.to_dict() for p in critical_patterns],
                "recommendation": "Address failure patterns before deployment",
            })
        
        return alerts
    
    def get_improvement_recommendations(
        self,
        evaluation_run: EvaluationRun
    ) -> Dict[str, Any]:
        """
        Generate specific recommendations for improvement
        """
        recommendations = {
            "dataset_updates": [],
            "guideline_updates": [],
            "model_updates": [],
            "priority_actions": [],
        }
        
        # From failure patterns
        for pattern in evaluation_run.failure_patterns:
            for rec in pattern.recommendations:
                if "training example" in rec.lower() or "data" in rec.lower():
                    recommendations["dataset_updates"].append(rec)
                elif "guideline" in rec.lower():
                    recommendations["guideline_updates"].append(rec)
                else:
                    recommendations["model_updates"].append(rec)
        
        # From per-class metrics
        for class_label, metrics in evaluation_run.per_class_metrics.items():
            if metrics["f1"] < 0.6:
                recommendations["priority_actions"].append(
                    f"Improve class '{class_label}' (F1={metrics['f1']:.2f})"
                )
        
        # Deduplicate
        for key in recommendations:
            recommendations[key] = list(set(recommendations[key]))
        
        return recommendations
    
    def generate_evaluation_report(
        self,
        run: EvaluationRun
    ) -> str:
        """Generate human-readable evaluation report"""
        alerts = self.check_performance_alerts(run)
        recommendations = self.get_improvement_recommendations(run)
        
        lines = [
            "=" * 60,
            "MODEL EVALUATION REPORT",
            "=" * 60,
            "",
            f"Run ID: {run.run_id}",
            f"Model Version: {run.model_version}",
            f"Dataset Version: {run.dataset_version}",
            f"Timestamp: {run.timestamp.isoformat()}",
            f"Samples Evaluated: {run.sample_count}",
            f"Duration: {run.evaluation_duration:.2f}s",
            "",
            "--- OVERALL METRICS ---",
            f"Accuracy: {run.accuracy:.2%}",
            f"Precision: {run.precision:.4f}",
            f"Recall: {run.recall:.4f}",
            f"F1 Score: {run.f1:.4f}",
            "",
            "--- PER-CLASS PERFORMANCE ---",
        ]
        
        for class_label, metrics in sorted(run.per_class_metrics.items()):
            lines.append(
                f"  {class_label}: P={metrics['precision']:.2f}, "
                f"R={metrics['recall']:.2f}, F1={metrics['f1']:.2f} "
                f"(n={metrics['support']})"
            )
        
        if alerts:
            lines.extend([
                "",
                "--- ALERTS ---",
            ])
            for alert in alerts:
                lines.append(f"  [{alert['severity'].upper()}] {alert['message']}")
        
        if run.failure_patterns:
            lines.extend([
                "",
                "--- FAILURE PATTERNS ---",
            ])
            for pattern in run.failure_patterns[:5]:
                lines.append(f"  [{pattern.severity.upper()}] {pattern.description} (n={pattern.frequency})")
        
        if any(recommendations.values()):
            lines.extend([
                "",
                "--- RECOMMENDATIONS ---",
            ])
            for rec in recommendations.get("priority_actions", [])[:3]:
                lines.append(f"  [PRIORITY] {rec}")
            for rec in recommendations.get("dataset_updates", [])[:3]:
                lines.append(f"  [DATA] {rec}")
            for rec in recommendations.get("guideline_updates", [])[:2]:
                lines.append(f"  [GUIDELINES] {rec}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def _load_history(self):
        """Load evaluation history from file"""
        history_file = self.history_path / "evaluation_history.json"
        if history_file.exists():
            # Load basic history (without full runs for now)
            pass
    
    def _save_history(self):
        """Save evaluation history to file"""
        if not self.history_path:
            return
        
        self.history_path.mkdir(parents=True, exist_ok=True)
        history_file = self.history_path / "evaluation_history.json"
        
        history_data = [
            {
                "run_id": run.run_id,
                "model_version": run.model_version,
                "dataset_version": run.dataset_version,
                "timestamp": run.timestamp.isoformat(),
                "accuracy": run.accuracy,
                "f1": run.f1,
                "sample_count": run.sample_count,
            }
            for run in self.evaluation_history
        ]
        
        with open(history_file, "w") as f:
            json.dump(history_data, f, indent=2)


# =============================================================================
# CONTINUOUS EVALUATION SCHEDULER
# =============================================================================

class ContinuousEvaluationScheduler:
    """
    Schedules and manages regular evaluations
    """
    
    def __init__(
        self,
        evaluator: ModelEvaluator,
        evaluation_interval_hours: int = 24,
        auto_update_dataset: bool = True,
        auto_update_guidelines: bool = False
    ):
        self.evaluator = evaluator
        self.interval_hours = evaluation_interval_hours
        self.auto_update_dataset = auto_update_dataset
        self.auto_update_guidelines = auto_update_guidelines
        
        self.last_evaluation: Optional[datetime] = None
        
        # Callbacks
        self.on_evaluation_complete: Optional[Callable] = None
        self.on_alert_triggered: Optional[Callable] = None
        self.on_update_needed: Optional[Callable] = None
    
    def should_evaluate(self) -> bool:
        """Check if evaluation is due"""
        if self.last_evaluation is None:
            return True
        
        elapsed = datetime.now() - self.last_evaluation
        return elapsed >= timedelta(hours=self.interval_hours)
    
    def run_scheduled_evaluation(
        self,
        validation_data: List[Dict],
        predict_fn: Callable,
        model_version: str,
        dataset_version: str
    ) -> Optional[EvaluationRun]:
        """
        Run evaluation if scheduled
        """
        if not self.should_evaluate():
            logger.info("Evaluation not due yet")
            return None
        
        logger.info("Running scheduled evaluation...")
        
        run = self.evaluator.evaluate(
            validation_data,
            predict_fn,
            model_version,
            dataset_version
        )
        
        self.last_evaluation = datetime.now()
        
        # Check alerts
        alerts = self.evaluator.check_performance_alerts(run)
        if alerts and self.on_alert_triggered:
            self.on_alert_triggered(alerts)
        
        # Get recommendations
        recommendations = self.evaluator.get_improvement_recommendations(run)
        
        # Auto-update dataset if needed
        if self.auto_update_dataset and recommendations.get("dataset_updates"):
            if self.on_update_needed:
                self.on_update_needed("dataset", recommendations["dataset_updates"])
        
        # Auto-update guidelines if needed
        if self.auto_update_guidelines and recommendations.get("guideline_updates"):
            if self.on_update_needed:
                self.on_update_needed("guidelines", recommendations["guideline_updates"])
        
        # Callback
        if self.on_evaluation_complete:
            self.on_evaluation_complete(run)
        
        return run


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def evaluate_model(
    validation_data: List[Dict],
    predict_fn: Callable,
    model_version: str = "1.0.0"
) -> EvaluationRun:
    """Quick model evaluation"""
    evaluator = ModelEvaluator()
    return evaluator.evaluate(
        validation_data,
        predict_fn,
        model_version,
        dataset_version="1.0.0"
    )


def create_evaluation_scheduler(
    history_path: str,
    interval_hours: int = 24
) -> ContinuousEvaluationScheduler:
    """Create configured evaluation scheduler"""
    evaluator = ModelEvaluator(evaluation_history_path=history_path)
    return ContinuousEvaluationScheduler(
        evaluator,
        evaluation_interval_hours=interval_hours
    )
