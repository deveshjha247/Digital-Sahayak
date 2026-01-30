"""
Inter-Annotator Agreement Metrics
Computes Cohen's Kappa, Krippendorff's Alpha, and other agreement metrics
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
import math

logger = logging.getLogger(__name__)


class AgreementMetrics:
    """
    Computes inter-annotator agreement metrics for quality control
    
    Supported metrics:
    - Cohen's Kappa (2 annotators, categorical)
    - Fleiss' Kappa (multiple annotators, categorical)
    - Krippendorff's Alpha (multiple annotators, various scales)
    - Percent Agreement (simple)
    - Scott's Pi
    """
    
    @staticmethod
    def percent_agreement(
        annotations1: List[Any],
        annotations2: List[Any]
    ) -> float:
        """
        Simple percent agreement between two annotators
        
        Args:
            annotations1: Labels from annotator 1
            annotations2: Labels from annotator 2
        
        Returns:
            Agreement ratio (0-1)
        """
        if len(annotations1) != len(annotations2):
            raise ValueError("Annotation lists must have same length")
        
        if len(annotations1) == 0:
            return 0.0
        
        agreements = sum(1 for a, b in zip(annotations1, annotations2) if a == b)
        return agreements / len(annotations1)
    
    @staticmethod
    def cohens_kappa(
        annotations1: List[Any],
        annotations2: List[Any]
    ) -> Dict[str, float]:
        """
        Cohen's Kappa for two annotators
        Accounts for chance agreement
        
        κ = (Po - Pe) / (1 - Pe)
        where:
        - Po = observed agreement
        - Pe = expected agreement by chance
        
        Interpretation:
        - < 0: Less than chance agreement
        - 0.01-0.20: Slight agreement
        - 0.21-0.40: Fair agreement
        - 0.41-0.60: Moderate agreement
        - 0.61-0.80: Substantial agreement
        - 0.81-1.00: Almost perfect agreement
        
        Returns:
            Dict with kappa, observed_agreement, expected_agreement
        """
        if len(annotations1) != len(annotations2):
            raise ValueError("Annotation lists must have same length")
        
        n = len(annotations1)
        if n == 0:
            return {"kappa": 0.0, "observed_agreement": 0.0, "expected_agreement": 0.0}
        
        # Get all unique labels
        all_labels = set(annotations1) | set(annotations2)
        
        # Count occurrences
        count1 = Counter(annotations1)
        count2 = Counter(annotations2)
        
        # Observed agreement (Po)
        observed = sum(1 for a, b in zip(annotations1, annotations2) if a == b) / n
        
        # Expected agreement by chance (Pe)
        expected = sum(
            (count1.get(label, 0) / n) * (count2.get(label, 0) / n)
            for label in all_labels
        )
        
        # Cohen's Kappa
        if expected == 1.0:
            kappa = 1.0 if observed == 1.0 else 0.0
        else:
            kappa = (observed - expected) / (1 - expected)
        
        return {
            "kappa": round(kappa, 4),
            "observed_agreement": round(observed, 4),
            "expected_agreement": round(expected, 4),
            "interpretation": AgreementMetrics._interpret_kappa(kappa),
            "n_items": n,
            "n_categories": len(all_labels),
        }
    
    @staticmethod
    def _interpret_kappa(kappa: float) -> str:
        """Interpret kappa value"""
        if kappa < 0:
            return "poor (less than chance)"
        elif kappa <= 0.20:
            return "slight"
        elif kappa <= 0.40:
            return "fair"
        elif kappa <= 0.60:
            return "moderate"
        elif kappa <= 0.80:
            return "substantial"
        else:
            return "almost perfect"
    
    @staticmethod
    def fleiss_kappa(
        annotations_matrix: List[List[int]]
    ) -> Dict[str, float]:
        """
        Fleiss' Kappa for multiple annotators
        
        Args:
            annotations_matrix: Matrix where each row is an item,
                               and each column is the count of annotators
                               who assigned that category
                               [[count_cat1, count_cat2, ...], ...]
        
        Returns:
            Dict with kappa and related statistics
        """
        if not annotations_matrix:
            return {"kappa": 0.0}
        
        n_items = len(annotations_matrix)
        n_categories = len(annotations_matrix[0])
        n_annotators = sum(annotations_matrix[0])  # Assuming same for all items
        
        # Calculate proportion of assignments to each category
        p_j = []
        for j in range(n_categories):
            total_j = sum(row[j] for row in annotations_matrix)
            p_j.append(total_j / (n_items * n_annotators))
        
        # Calculate P_i for each item (extent of agreement)
        P_i = []
        for row in annotations_matrix:
            sum_squared = sum(n_ij ** 2 for n_ij in row)
            P_i_val = (sum_squared - n_annotators) / (n_annotators * (n_annotators - 1))
            P_i.append(P_i_val)
        
        # Mean observed agreement
        P_bar = sum(P_i) / n_items
        
        # Expected agreement by chance
        P_e = sum(p ** 2 for p in p_j)
        
        # Fleiss' Kappa
        if P_e == 1.0:
            kappa = 1.0 if P_bar == 1.0 else 0.0
        else:
            kappa = (P_bar - P_e) / (1 - P_e)
        
        return {
            "kappa": round(kappa, 4),
            "observed_agreement": round(P_bar, 4),
            "expected_agreement": round(P_e, 4),
            "interpretation": AgreementMetrics._interpret_kappa(kappa),
            "n_items": n_items,
            "n_categories": n_categories,
            "n_annotators": n_annotators,
        }
    
    @staticmethod
    def krippendorff_alpha(
        annotations: Dict[str, Dict[str, Any]],
        level: str = "nominal"
    ) -> Dict[str, float]:
        """
        Krippendorff's Alpha for multiple annotators
        Handles missing data and various measurement levels
        
        Args:
            annotations: Dict mapping annotator_id to {item_id: label}
            level: "nominal", "ordinal", "interval", or "ratio"
        
        Returns:
            Dict with alpha and related statistics
        """
        # Build reliability data matrix
        annotators = list(annotations.keys())
        all_items = set()
        for ann_data in annotations.values():
            all_items.update(ann_data.keys())
        items = sorted(all_items)
        
        # Build units (items) with their values
        units = {}
        for item in items:
            values = []
            for annotator in annotators:
                if item in annotations[annotator]:
                    values.append(annotations[annotator][item])
            if len(values) >= 2:  # Need at least 2 annotations
                units[item] = values
        
        if not units:
            return {"alpha": 0.0, "interpretation": "insufficient data"}
        
        # Get all unique values
        all_values = set()
        for values in units.values():
            all_values.update(values)
        
        # For nominal data, use simple disagreement
        if level == "nominal":
            # Calculate observed disagreement
            total_pairs = 0
            disagreements = 0
            
            for values in units.values():
                n = len(values)
                for i in range(n):
                    for j in range(i + 1, n):
                        total_pairs += 1
                        if values[i] != values[j]:
                            disagreements += 1
            
            D_o = disagreements / total_pairs if total_pairs > 0 else 0
            
            # Calculate expected disagreement
            value_counts = Counter()
            total_values = 0
            for values in units.values():
                value_counts.update(values)
                total_values += len(values)
            
            D_e = 0
            for v1 in all_values:
                for v2 in all_values:
                    if v1 != v2:
                        n1 = value_counts[v1]
                        n2 = value_counts[v2]
                        D_e += n1 * n2
            
            D_e = D_e / (total_values * (total_values - 1)) if total_values > 1 else 0
            
            # Krippendorff's Alpha
            alpha = 1 - (D_o / D_e) if D_e > 0 else 1.0
        
        else:
            # For ordinal/interval/ratio, use appropriate distance function
            # Simplified implementation for ordinal
            alpha = AgreementMetrics._ordinal_alpha(units, all_values)
        
        return {
            "alpha": round(alpha, 4),
            "interpretation": AgreementMetrics._interpret_alpha(alpha),
            "n_items": len(units),
            "n_annotators": len(annotators),
            "n_categories": len(all_values),
            "level": level,
        }
    
    @staticmethod
    def _ordinal_alpha(units: Dict, all_values: set) -> float:
        """Calculate alpha for ordinal data"""
        # Sort values and assign ranks
        sorted_values = sorted(all_values)
        value_to_rank = {v: i for i, v in enumerate(sorted_values)}
        
        # Calculate observed disagreement with ordinal distance
        total_pairs = 0
        weighted_disagreements = 0
        
        for values in units.values():
            n = len(values)
            for i in range(n):
                for j in range(i + 1, n):
                    total_pairs += 1
                    rank_diff = abs(value_to_rank[values[i]] - value_to_rank[values[j]])
                    weighted_disagreements += rank_diff ** 2
        
        D_o = weighted_disagreements / total_pairs if total_pairs > 0 else 0
        
        # Expected disagreement (simplified)
        max_distance = (len(sorted_values) - 1) ** 2
        D_e = max_distance / 3  # Approximate expected value
        
        alpha = 1 - (D_o / D_e) if D_e > 0 else 1.0
        return max(-1, min(1, alpha))  # Clamp to [-1, 1]
    
    @staticmethod
    def _interpret_alpha(alpha: float) -> str:
        """Interpret Krippendorff's alpha"""
        if alpha < 0:
            return "systematic disagreement"
        elif alpha < 0.667:
            return "low reliability (discard)"
        elif alpha < 0.8:
            return "acceptable for tentative conclusions"
        else:
            return "good reliability"
    
    @staticmethod
    def scotts_pi(
        annotations1: List[Any],
        annotations2: List[Any]
    ) -> Dict[str, float]:
        """
        Scott's Pi - similar to Kappa but uses joint distribution
        Better when annotators have different marginal distributions
        """
        if len(annotations1) != len(annotations2):
            raise ValueError("Annotation lists must have same length")
        
        n = len(annotations1)
        if n == 0:
            return {"pi": 0.0}
        
        # Get all unique labels
        all_labels = set(annotations1) | set(annotations2)
        
        # Joint proportions
        joint_counts = Counter(zip(annotations1, annotations2))
        
        # Marginal proportions (averaged)
        count1 = Counter(annotations1)
        count2 = Counter(annotations2)
        
        # Observed agreement
        observed = sum(1 for a, b in zip(annotations1, annotations2) if a == b) / n
        
        # Expected agreement using averaged marginals
        expected = sum(
            ((count1.get(label, 0) + count2.get(label, 0)) / (2 * n)) ** 2
            for label in all_labels
        )
        
        # Scott's Pi
        if expected == 1.0:
            pi = 1.0 if observed == 1.0 else 0.0
        else:
            pi = (observed - expected) / (1 - expected)
        
        return {
            "pi": round(pi, 4),
            "observed_agreement": round(observed, 4),
            "expected_agreement": round(expected, 4),
        }
    
    @staticmethod
    def confusion_matrix(
        annotations1: List[Any],
        annotations2: List[Any],
        labels: List[Any] = None
    ) -> Dict[str, Any]:
        """
        Build confusion matrix between two annotators
        """
        if labels is None:
            labels = sorted(set(annotations1) | set(annotations2))
        
        label_to_idx = {label: i for i, label in enumerate(labels)}
        n_labels = len(labels)
        
        # Initialize matrix
        matrix = [[0] * n_labels for _ in range(n_labels)]
        
        for a1, a2 in zip(annotations1, annotations2):
            if a1 in label_to_idx and a2 in label_to_idx:
                i = label_to_idx[a1]
                j = label_to_idx[a2]
                matrix[i][j] += 1
        
        return {
            "matrix": matrix,
            "labels": labels,
            "annotator1_totals": [sum(row) for row in matrix],
            "annotator2_totals": [sum(matrix[i][j] for i in range(n_labels)) for j in range(n_labels)],
        }
    
    @staticmethod
    def category_agreement(
        annotations1: List[Any],
        annotations2: List[Any]
    ) -> Dict[str, Dict[str, float]]:
        """
        Per-category agreement analysis
        """
        all_labels = sorted(set(annotations1) | set(annotations2))
        results = {}
        
        for label in all_labels:
            # True positives: both annotators assigned this label
            tp = sum(1 for a, b in zip(annotations1, annotations2) if a == label and b == label)
            # False positives: annotator1 assigned, annotator2 didn't
            fp = sum(1 for a, b in zip(annotations1, annotations2) if a == label and b != label)
            # False negatives: annotator2 assigned, annotator1 didn't
            fn = sum(1 for a, b in zip(annotations1, annotations2) if a != label and b == label)
            # True negatives
            tn = sum(1 for a, b in zip(annotations1, annotations2) if a != label and b != label)
            
            # Precision, Recall, F1
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            results[label] = {
                "precision": round(precision, 4),
                "recall": round(recall, 4),
                "f1": round(f1, 4),
                "support": tp + fn,  # Total for annotator2
            }
        
        return results


class AgreementAnalyzer:
    """
    Analyzes annotation agreement across multiple annotators and items
    """
    
    def __init__(self):
        self.annotations: Dict[str, Dict[str, Any]] = {}  # item_id -> {annotator_id: label}
        self.annotator_pairs: List[Tuple[str, str]] = []
    
    def add_annotation(
        self,
        item_id: str,
        annotator_id: str,
        label: Any
    ):
        """Add a single annotation"""
        if item_id not in self.annotations:
            self.annotations[item_id] = {}
        self.annotations[item_id][annotator_id] = label
    
    def add_batch(
        self,
        annotations: List[Dict]
    ):
        """
        Add batch of annotations
        Each dict should have: item_id, annotator_id, label
        """
        for ann in annotations:
            self.add_annotation(
                ann["item_id"],
                ann["annotator_id"],
                ann["label"]
            )
    
    def get_pairwise_annotations(
        self,
        annotator1: str,
        annotator2: str
    ) -> Tuple[List[Any], List[Any]]:
        """Get aligned annotations for two annotators"""
        labels1 = []
        labels2 = []
        
        for item_id, item_annotations in self.annotations.items():
            if annotator1 in item_annotations and annotator2 in item_annotations:
                labels1.append(item_annotations[annotator1])
                labels2.append(item_annotations[annotator2])
        
        return labels1, labels2
    
    def compute_all_metrics(self) -> Dict[str, Any]:
        """Compute comprehensive agreement metrics"""
        results = {
            "pairwise": {},
            "overall": {},
            "per_category": {},
            "recommendations": [],
        }
        
        # Get all annotators
        annotators = set()
        for item_annotations in self.annotations.values():
            annotators.update(item_annotations.keys())
        annotators = sorted(annotators)
        
        if len(annotators) < 2:
            return {"error": "Need at least 2 annotators"}
        
        # Pairwise metrics
        for i, ann1 in enumerate(annotators):
            for ann2 in annotators[i + 1:]:
                labels1, labels2 = self.get_pairwise_annotations(ann1, ann2)
                
                if len(labels1) > 0:
                    pair_key = f"{ann1}_vs_{ann2}"
                    results["pairwise"][pair_key] = {
                        "cohens_kappa": AgreementMetrics.cohens_kappa(labels1, labels2),
                        "percent_agreement": AgreementMetrics.percent_agreement(labels1, labels2),
                        "n_items": len(labels1),
                    }
        
        # Overall Krippendorff's Alpha
        kripp_format = {ann: {} for ann in annotators}
        for item_id, item_annotations in self.annotations.items():
            for ann_id, label in item_annotations.items():
                kripp_format[ann_id][item_id] = label
        
        results["overall"]["krippendorff_alpha"] = AgreementMetrics.krippendorff_alpha(
            kripp_format, level="nominal"
        )
        
        # Average pairwise kappa
        kappas = [
            pair_data["cohens_kappa"]["kappa"]
            for pair_data in results["pairwise"].values()
        ]
        if kappas:
            results["overall"]["average_kappa"] = round(sum(kappas) / len(kappas), 4)
        
        # Per-category analysis (using first pair)
        if annotators and len(annotators) >= 2:
            labels1, labels2 = self.get_pairwise_annotations(annotators[0], annotators[1])
            if labels1:
                results["per_category"] = AgreementMetrics.category_agreement(labels1, labels2)
        
        # Recommendations
        avg_kappa = results["overall"].get("average_kappa", 0)
        alpha = results["overall"]["krippendorff_alpha"].get("alpha", 0)
        
        if avg_kappa < 0.6:
            results["recommendations"].append(
                "Low agreement (κ < 0.6). Review guidelines and retrain annotators."
            )
        if alpha < 0.667:
            results["recommendations"].append(
                "Krippendorff's α < 0.667. Data reliability is questionable."
            )
        
        # Check for problematic categories
        for cat, metrics in results.get("per_category", {}).items():
            if metrics["f1"] < 0.5:
                results["recommendations"].append(
                    f"Category '{cat}' has low agreement (F1={metrics['f1']}). "
                    "Clarify definition in guidelines."
                )
        
        return results
    
    def get_disagreements(self) -> List[Dict]:
        """Get all items where annotators disagreed"""
        disagreements = []
        
        for item_id, item_annotations in self.annotations.items():
            labels = list(item_annotations.values())
            
            if len(set(labels)) > 1:  # Disagreement exists
                disagreements.append({
                    "item_id": item_id,
                    "annotations": item_annotations,
                    "labels": list(set(labels)),
                })
        
        return disagreements
    
    def get_annotator_statistics(self) -> Dict[str, Dict]:
        """Get statistics per annotator"""
        stats = defaultdict(lambda: {
            "total_annotations": 0,
            "agreements": 0,
            "disagreements": 0,
        })
        
        for item_annotations in self.annotations.values():
            annotators = list(item_annotations.keys())
            labels = list(item_annotations.values())
            
            # Check if there's consensus
            is_agreement = len(set(labels)) == 1
            
            for ann_id in annotators:
                stats[ann_id]["total_annotations"] += 1
                if is_agreement:
                    stats[ann_id]["agreements"] += 1
                else:
                    stats[ann_id]["disagreements"] += 1
        
        # Calculate agreement rates
        for ann_id in stats:
            total = stats[ann_id]["total_annotations"]
            if total > 0:
                stats[ann_id]["agreement_rate"] = round(
                    stats[ann_id]["agreements"] / total, 4
                )
        
        return dict(stats)


def compute_agreement_report(
    annotations: List[Dict],
    output_path: str = None
) -> Dict:
    """
    Convenience function to compute full agreement report
    
    Args:
        annotations: List of {item_id, annotator_id, label}
        output_path: Optional path to save report
    
    Returns:
        Complete agreement analysis
    """
    analyzer = AgreementAnalyzer()
    analyzer.add_batch(annotations)
    
    report = analyzer.compute_all_metrics()
    report["disagreements"] = analyzer.get_disagreements()
    report["annotator_stats"] = analyzer.get_annotator_statistics()
    
    if output_path:
        import json
        from pathlib import Path
        
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Agreement report saved to {output_path}")
    
    return report
