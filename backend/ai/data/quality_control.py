"""
Annotation Quality Control System
Comprehensive system for managing annotation quality
"""

import logging
from typing import Dict, List, Any, Optional, Tuple, Set
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
from enum import Enum
import json
import hashlib

from .agreement_metrics import AgreementMetrics, AgreementAnalyzer

logger = logging.getLogger(__name__)


# =============================================================================
# ANNOTATOR MANAGEMENT
# =============================================================================

class AnnotatorLevel(Enum):
    """Annotator skill levels"""
    TRAINEE = "trainee"
    JUNIOR = "junior"
    SENIOR = "senior"
    EXPERT = "expert"
    ADJUDICATOR = "adjudicator"


@dataclass
class Annotator:
    """Represents an annotator"""
    annotator_id: str
    name: str
    level: AnnotatorLevel = AnnotatorLevel.JUNIOR
    languages: List[str] = field(default_factory=lambda: ["en", "hi"])
    specializations: List[str] = field(default_factory=list)
    
    # Performance metrics
    total_annotations: int = 0
    agreement_rate: float = 0.0
    avg_time_per_item: float = 0.0
    quality_score: float = 0.0
    
    # Task assignments
    assigned_tasks: Set[str] = field(default_factory=set)
    
    def update_metrics(self, agreement: float, time_spent: float):
        """Update annotator metrics"""
        self.total_annotations += 1
        # Running average
        n = self.total_annotations
        self.agreement_rate = ((n - 1) * self.agreement_rate + agreement) / n
        self.avg_time_per_item = ((n - 1) * self.avg_time_per_item + time_spent) / n
        
        # Quality score considers agreement and speed
        self.quality_score = self.agreement_rate * 0.8 + min(1.0, 60 / max(1, self.avg_time_per_item)) * 0.2
    
    def can_adjudicate(self) -> bool:
        """Check if annotator can adjudicate disagreements"""
        return self.level in [AnnotatorLevel.EXPERT, AnnotatorLevel.ADJUDICATOR]


@dataclass
class AnnotatorPool:
    """Manages a pool of annotators"""
    annotators: Dict[str, Annotator] = field(default_factory=dict)
    
    def add_annotator(self, annotator: Annotator):
        """Add annotator to pool"""
        self.annotators[annotator.annotator_id] = annotator
    
    def get_annotator(self, annotator_id: str) -> Optional[Annotator]:
        """Get annotator by ID"""
        return self.annotators.get(annotator_id)
    
    def get_available_annotators(
        self,
        task_type: str = None,
        language: str = None,
        min_level: AnnotatorLevel = None
    ) -> List[Annotator]:
        """Get available annotators matching criteria"""
        available = []
        
        for annotator in self.annotators.values():
            # Filter by task specialization
            if task_type and task_type not in annotator.specializations:
                if annotator.specializations:  # Skip if has specializations but not this one
                    continue
            
            # Filter by language
            if language and language not in annotator.languages:
                continue
            
            # Filter by level
            if min_level:
                levels_order = list(AnnotatorLevel)
                if levels_order.index(annotator.level) < levels_order.index(min_level):
                    continue
            
            available.append(annotator)
        
        # Sort by quality score
        available.sort(key=lambda a: a.quality_score, reverse=True)
        return available
    
    def get_adjudicators(self) -> List[Annotator]:
        """Get annotators who can adjudicate"""
        return [a for a in self.annotators.values() if a.can_adjudicate()]


# =============================================================================
# ANNOTATION TASK
# =============================================================================

@dataclass
class AnnotationTask:
    """Represents an annotation task"""
    task_id: str
    task_type: str  # intent, job_category, form_field, etc.
    item: Dict[str, Any]
    item_hash: str
    
    # Annotations
    annotations: Dict[str, Any] = field(default_factory=dict)  # annotator_id -> label
    timestamps: Dict[str, datetime] = field(default_factory=dict)
    
    # Status
    status: str = "pending"  # pending, in_progress, needs_review, completed
    final_label: Optional[Any] = None
    adjudicated_by: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    @classmethod
    def create(cls, task_type: str, item: Dict) -> "AnnotationTask":
        """Create new annotation task"""
        item_str = json.dumps(item, sort_keys=True, default=str)
        item_hash = hashlib.md5(item_str.encode()).hexdigest()
        task_id = f"{task_type}_{item_hash[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        return cls(
            task_id=task_id,
            task_type=task_type,
            item=item,
            item_hash=item_hash,
        )
    
    def add_annotation(self, annotator_id: str, label: Any):
        """Add annotation from an annotator"""
        self.annotations[annotator_id] = label
        self.timestamps[annotator_id] = datetime.now()
        
        if self.status == "pending":
            self.status = "in_progress"
    
    def get_agreement(self) -> Optional[float]:
        """Get agreement ratio among annotators"""
        if len(self.annotations) < 2:
            return None
        
        labels = list(self.annotations.values())
        most_common = max(set(labels), key=labels.count)
        return labels.count(most_common) / len(labels)
    
    def needs_adjudication(self, threshold: float = 0.8) -> bool:
        """Check if task needs adjudication"""
        agreement = self.get_agreement()
        if agreement is None:
            return False
        return agreement < threshold
    
    def complete(self, final_label: Any, adjudicator_id: str = None):
        """Mark task as completed"""
        self.final_label = final_label
        self.status = "completed"
        self.completed_at = datetime.now()
        self.adjudicated_by = adjudicator_id


# =============================================================================
# QUALITY CONTROL SYSTEM
# =============================================================================

class QualityControlSystem:
    """
    Comprehensive quality control for annotations
    """
    
    def __init__(
        self,
        min_annotators: int = 2,
        agreement_threshold: float = 0.8,
        gold_sample_rate: float = 0.05,  # 5% gold standard items
    ):
        self.min_annotators = min_annotators
        self.agreement_threshold = agreement_threshold
        self.gold_sample_rate = gold_sample_rate
        
        # Task management
        self.tasks: Dict[str, AnnotationTask] = {}
        self.task_queue: List[str] = []
        
        # Annotator management
        self.annotator_pool = AnnotatorPool()
        
        # Gold standard items for quality checks
        self.gold_items: Dict[str, Dict] = {}  # item_hash -> {item, gold_label}
        
        # Statistics
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "adjudicated_tasks": 0,
            "avg_agreement": 0.0,
        }
    
    def add_gold_item(self, task_type: str, item: Dict, gold_label: Any):
        """Add gold standard item for quality control"""
        item_str = json.dumps(item, sort_keys=True, default=str)
        item_hash = hashlib.md5(item_str.encode()).hexdigest()
        
        self.gold_items[item_hash] = {
            "task_type": task_type,
            "item": item,
            "gold_label": gold_label,
        }
    
    def is_gold_item(self, item_hash: str) -> bool:
        """Check if item is a gold standard item"""
        return item_hash in self.gold_items
    
    def check_against_gold(self, item_hash: str, label: Any) -> Tuple[bool, Any]:
        """Check annotation against gold standard"""
        if item_hash not in self.gold_items:
            return (True, None)  # Not a gold item
        
        gold_label = self.gold_items[item_hash]["gold_label"]
        is_correct = label == gold_label
        return (is_correct, gold_label)
    
    def create_task(self, task_type: str, item: Dict) -> AnnotationTask:
        """Create new annotation task"""
        task = AnnotationTask.create(task_type, item)
        self.tasks[task.task_id] = task
        self.task_queue.append(task.task_id)
        self.stats["total_tasks"] += 1
        return task
    
    def create_tasks_batch(self, task_type: str, items: List[Dict]) -> List[AnnotationTask]:
        """Create tasks for a batch of items"""
        tasks = []
        for item in items:
            task = self.create_task(task_type, item)
            tasks.append(task)
        return tasks
    
    def assign_task(
        self,
        annotator_id: str,
        task_type: str = None,
        language: str = None
    ) -> Optional[AnnotationTask]:
        """
        Assign a task to an annotator
        Considers:
        - Task type preference
        - Avoiding double assignment
        - Gold item injection
        """
        annotator = self.annotator_pool.get_annotator(annotator_id)
        if not annotator:
            logger.warning(f"Unknown annotator: {annotator_id}")
            return None
        
        # Find suitable task
        for task_id in self.task_queue:
            task = self.tasks[task_id]
            
            # Check if already annotated by this annotator
            if annotator_id in task.annotations:
                continue
            
            # Check task type match
            if task_type and task.task_type != task_type:
                continue
            
            # Check if needs more annotations
            if len(task.annotations) >= self.min_annotators:
                continue
            
            return task
        
        return None  # No suitable task found
    
    def submit_annotation(
        self,
        task_id: str,
        annotator_id: str,
        label: Any,
        time_spent: float = 0.0
    ) -> Dict[str, Any]:
        """
        Submit annotation and run quality checks
        """
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.tasks[task_id]
        annotator = self.annotator_pool.get_annotator(annotator_id)
        
        # Check against gold standard
        is_gold = self.is_gold_item(task.item_hash)
        if is_gold:
            correct, gold_label = self.check_against_gold(task.item_hash, label)
            if annotator:
                annotator.update_metrics(1.0 if correct else 0.0, time_spent)
            
            if not correct:
                return {
                    "success": True,
                    "is_gold": True,
                    "gold_correct": False,
                    "message": "This was a quality check item. Your answer differs from the gold standard.",
                }
        
        # Add annotation
        task.add_annotation(annotator_id, label)
        
        # Check if we have enough annotations
        result = {"success": True, "is_gold": is_gold}
        
        if len(task.annotations) >= self.min_annotators:
            agreement = task.get_agreement()
            result["agreement"] = agreement
            
            if agreement >= self.agreement_threshold:
                # Automatic consensus
                labels = list(task.annotations.values())
                final_label = max(set(labels), key=labels.count)
                task.complete(final_label)
                self.stats["completed_tasks"] += 1
                
                # Update task queue
                if task_id in self.task_queue:
                    self.task_queue.remove(task_id)
                
                # Update annotator agreement rates
                for ann_id in task.annotations:
                    ann = self.annotator_pool.get_annotator(ann_id)
                    if ann:
                        ann_agreement = 1.0 if task.annotations[ann_id] == final_label else 0.0
                        ann.update_metrics(ann_agreement, time_spent)
                
                result["status"] = "completed"
                result["final_label"] = final_label
            else:
                # Needs adjudication
                task.status = "needs_review"
                result["status"] = "needs_review"
                result["message"] = "Disagreement detected. Task sent for adjudication."
        else:
            result["status"] = "in_progress"
            result["annotations_received"] = len(task.annotations)
            result["annotations_needed"] = self.min_annotators
        
        return result
    
    def adjudicate_task(
        self,
        task_id: str,
        adjudicator_id: str,
        final_label: Any,
        reason: str = ""
    ) -> Dict[str, Any]:
        """Adjudicate a disagreement"""
        if task_id not in self.tasks:
            return {"success": False, "error": "Task not found"}
        
        task = self.tasks[task_id]
        adjudicator = self.annotator_pool.get_annotator(adjudicator_id)
        
        if adjudicator and not adjudicator.can_adjudicate():
            return {"success": False, "error": "Annotator not authorized to adjudicate"}
        
        task.complete(final_label, adjudicator_id)
        self.stats["adjudicated_tasks"] += 1
        self.stats["completed_tasks"] += 1
        
        if task_id in self.task_queue:
            self.task_queue.remove(task_id)
        
        return {
            "success": True,
            "status": "completed",
            "final_label": final_label,
            "adjudicated_by": adjudicator_id,
        }
    
    def get_tasks_needing_review(self) -> List[AnnotationTask]:
        """Get all tasks needing adjudication"""
        return [t for t in self.tasks.values() if t.status == "needs_review"]
    
    def compute_inter_annotator_agreement(
        self,
        task_type: str = None,
        metric: str = "fleiss_kappa"
    ) -> Dict[str, Any]:
        """Compute inter-annotator agreement for completed tasks"""
        # Filter completed tasks
        completed = [
            t for t in self.tasks.values()
            if t.status == "completed"
            and (task_type is None or t.task_type == task_type)
        ]
        
        if len(completed) < 10:
            return {
                "error": "Not enough completed tasks for reliable metrics",
                "completed_count": len(completed),
            }
        
        # Get all annotator IDs
        all_annotators = set()
        for task in completed:
            all_annotators.update(task.annotations.keys())
        
        annotator_list = sorted(all_annotators)
        
        # Build annotation matrix
        # Each row is an item, each column is an annotator
        items = []
        for task in completed:
            labels = []
            for ann_id in annotator_list:
                labels.append(task.annotations.get(ann_id, None))
            items.append(labels)
        
        # Build annotations list for AgreementAnalyzer
        annotations_list = []
        for task in completed:
            annotations_list.append({
                "item_id": task.task_id,
                "annotations": task.annotations,
            })
        
        # Compute agreement
        analyzer = AgreementAnalyzer(annotations_list)
        report = analyzer.compute_full_report()
        
        return {
            "task_type": task_type,
            "completed_tasks": len(completed),
            "annotators": len(annotator_list),
            "agreement_report": report,
        }
    
    def get_annotator_performance(self) -> List[Dict]:
        """Get performance metrics for all annotators"""
        performance = []
        
        for ann_id, ann in self.annotator_pool.annotators.items():
            performance.append({
                "annotator_id": ann_id,
                "name": ann.name,
                "level": ann.level.value,
                "total_annotations": ann.total_annotations,
                "agreement_rate": round(ann.agreement_rate, 4),
                "avg_time_per_item": round(ann.avg_time_per_item, 2),
                "quality_score": round(ann.quality_score, 4),
            })
        
        # Sort by quality score
        performance.sort(key=lambda x: x["quality_score"], reverse=True)
        return performance
    
    def get_task_statistics(self) -> Dict[str, Any]:
        """Get overall task statistics"""
        task_types = defaultdict(lambda: {"total": 0, "completed": 0, "needs_review": 0})
        
        for task in self.tasks.values():
            task_types[task.task_type]["total"] += 1
            if task.status == "completed":
                task_types[task.task_type]["completed"] += 1
            elif task.status == "needs_review":
                task_types[task.task_type]["needs_review"] += 1
        
        return {
            "total_tasks": self.stats["total_tasks"],
            "completed_tasks": self.stats["completed_tasks"],
            "adjudicated_tasks": self.stats["adjudicated_tasks"],
            "pending_tasks": len(self.task_queue),
            "by_task_type": dict(task_types),
            "gold_items_count": len(self.gold_items),
        }
    
    def export_completed_annotations(
        self,
        task_type: str = None,
        format: str = "list"
    ) -> List[Dict]:
        """Export completed annotations"""
        completed = [
            t for t in self.tasks.values()
            if t.status == "completed"
            and (task_type is None or t.task_type == task_type)
        ]
        
        if format == "list":
            return [
                {
                    "item": task.item,
                    "label": task.final_label,
                    "annotators": list(task.annotations.keys()),
                    "agreement": task.get_agreement(),
                    "adjudicated": task.adjudicated_by is not None,
                }
                for task in completed
            ]
        elif format == "jsonl":
            return [
                {**task.item, "label": task.final_label}
                for task in completed
            ]
        
        return []


# =============================================================================
# CONSISTENCY CHECKER
# =============================================================================

class ConsistencyChecker:
    """
    Checks for consistency issues in annotations
    """
    
    def __init__(self, qc_system: QualityControlSystem):
        self.qc = qc_system
    
    def find_similar_items_with_different_labels(
        self,
        similarity_threshold: float = 0.9
    ) -> List[Dict]:
        """Find similar items that have been labeled differently"""
        from difflib import SequenceMatcher
        
        completed = [t for t in self.qc.tasks.values() if t.status == "completed"]
        inconsistencies = []
        
        # Compare pairs
        for i, task1 in enumerate(completed):
            for task2 in completed[i+1:]:
                if task1.task_type != task2.task_type:
                    continue
                
                # Simple text similarity
                text1 = json.dumps(task1.item, sort_keys=True)
                text2 = json.dumps(task2.item, sort_keys=True)
                
                similarity = SequenceMatcher(None, text1, text2).ratio()
                
                if similarity >= similarity_threshold and task1.final_label != task2.final_label:
                    inconsistencies.append({
                        "task1_id": task1.task_id,
                        "task1_item": task1.item,
                        "task1_label": task1.final_label,
                        "task2_id": task2.task_id,
                        "task2_item": task2.item,
                        "task2_label": task2.final_label,
                        "similarity": round(similarity, 4),
                    })
        
        return inconsistencies
    
    def find_annotator_drift(
        self,
        annotator_id: str,
        window_size: int = 50
    ) -> Dict[str, Any]:
        """
        Detect if annotator's labeling patterns have drifted over time
        """
        # Get annotator's tasks in chronological order
        annotator_tasks = [
            (t.timestamps.get(annotator_id), t.annotations.get(annotator_id), t.final_label)
            for t in self.qc.tasks.values()
            if annotator_id in t.annotations and t.status == "completed"
        ]
        
        if len(annotator_tasks) < window_size * 2:
            return {"error": "Not enough data for drift detection"}
        
        # Sort by timestamp
        annotator_tasks.sort(key=lambda x: x[0] if x[0] else datetime.min)
        
        # Compare early vs late agreement
        early_tasks = annotator_tasks[:window_size]
        late_tasks = annotator_tasks[-window_size:]
        
        early_agreement = sum(1 for _, label, final in early_tasks if label == final) / window_size
        late_agreement = sum(1 for _, label, final in late_tasks if label == final) / window_size
        
        drift = late_agreement - early_agreement
        
        return {
            "annotator_id": annotator_id,
            "early_agreement": round(early_agreement, 4),
            "late_agreement": round(late_agreement, 4),
            "drift": round(drift, 4),
            "drift_detected": abs(drift) > 0.1,  # 10% change threshold
        }
    
    def get_label_distribution(self, task_type: str = None) -> Dict[str, Dict]:
        """Get label distribution statistics"""
        distributions = defaultdict(lambda: defaultdict(int))
        
        for task in self.qc.tasks.values():
            if task.status != "completed":
                continue
            if task_type and task.task_type != task_type:
                continue
            
            distributions[task.task_type][task.final_label] += 1
        
        result = {}
        for tt, labels in distributions.items():
            total = sum(labels.values())
            result[tt] = {
                "counts": dict(labels),
                "percentages": {
                    label: round(count / total * 100, 2)
                    for label, count in labels.items()
                },
                "total": total,
            }
        
        return result


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_quality_control_system(
    min_annotators: int = 2,
    agreement_threshold: float = 0.8
) -> QualityControlSystem:
    """Create pre-configured quality control system"""
    return QualityControlSystem(
        min_annotators=min_annotators,
        agreement_threshold=agreement_threshold,
    )
