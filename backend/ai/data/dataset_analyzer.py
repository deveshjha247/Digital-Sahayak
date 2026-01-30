"""
Dataset Analyzer
Comprehensive analysis of annotated datasets
Visualizations, bias detection, and quality metrics
"""

import logging
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import Counter, defaultdict
from datetime import datetime
import math

logger = logging.getLogger(__name__)


# =============================================================================
# ANALYSIS CONFIGURATION
# =============================================================================

@dataclass
class AnalysisConfig:
    """Configuration for dataset analysis"""
    label_key: str = "label"
    text_keys: List[str] = field(default_factory=lambda: ["text", "message", "title", "description"])
    categorical_keys: List[str] = field(default_factory=lambda: ["language", "state", "source", "category"])
    numeric_keys: List[str] = field(default_factory=lambda: ["salary_min", "salary_max", "age_min", "age_max"])
    
    # Thresholds
    imbalance_threshold: float = 0.1  # Class with <10% is imbalanced
    rare_class_threshold: int = 10  # Less than 10 samples is rare
    missing_threshold: float = 0.05  # >5% missing is concerning


# =============================================================================
# CLASS DISTRIBUTION ANALYZER
# =============================================================================

class ClassDistributionAnalyzer:
    """
    Analyzes class/label distribution in dataset
    """
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
    
    def analyze(
        self,
        data: List[Dict],
        label_key: str = None
    ) -> Dict[str, Any]:
        """
        Analyze class distribution
        
        Returns comprehensive distribution analysis
        """
        label_key = label_key or self.config.label_key
        
        # Count labels
        label_counts = Counter()
        missing_labels = 0
        
        for item in data:
            label = item.get(label_key)
            if label is None:
                missing_labels += 1
            else:
                label_counts[label] += 1
        
        total = len(data)
        total_labeled = total - missing_labels
        
        # Compute statistics
        distribution = {}
        imbalanced_classes = []
        rare_classes = []
        
        for label, count in label_counts.most_common():
            percentage = count / total_labeled if total_labeled > 0 else 0
            distribution[label] = {
                "count": count,
                "percentage": round(percentage * 100, 2),
            }
            
            if percentage < self.config.imbalance_threshold:
                imbalanced_classes.append(label)
            
            if count < self.config.rare_class_threshold:
                rare_classes.append(label)
        
        # Compute imbalance ratio (majority / minority)
        if label_counts:
            majority_count = label_counts.most_common(1)[0][1]
            minority_count = label_counts.most_common()[-1][1]
            imbalance_ratio = majority_count / minority_count if minority_count > 0 else float('inf')
        else:
            imbalance_ratio = 0
        
        # Entropy (measure of balance)
        entropy = self._compute_entropy(label_counts, total_labeled)
        max_entropy = math.log2(len(label_counts)) if label_counts else 0
        balance_score = entropy / max_entropy if max_entropy > 0 else 0
        
        return {
            "total_samples": total,
            "total_labeled": total_labeled,
            "missing_labels": missing_labels,
            "missing_percentage": round(missing_labels / total * 100, 2) if total > 0 else 0,
            "num_classes": len(label_counts),
            "distribution": distribution,
            "imbalance_ratio": round(imbalance_ratio, 2),
            "balance_score": round(balance_score, 4),  # 1.0 = perfectly balanced
            "imbalanced_classes": imbalanced_classes,
            "rare_classes": rare_classes,
            "is_balanced": len(imbalanced_classes) == 0 and imbalance_ratio < 3,
        }
    
    def _compute_entropy(self, counts: Counter, total: int) -> float:
        """Compute Shannon entropy"""
        if total == 0:
            return 0
        
        entropy = 0
        for count in counts.values():
            if count > 0:
                p = count / total
                entropy -= p * math.log2(p)
        
        return entropy
    
    def get_ascii_histogram(
        self,
        data: List[Dict],
        label_key: str = None,
        width: int = 40
    ) -> str:
        """
        Generate ASCII histogram for class distribution
        """
        label_key = label_key or self.config.label_key
        label_counts = Counter(item.get(label_key, "unknown") for item in data)
        
        if not label_counts:
            return "No data to visualize"
        
        max_count = max(label_counts.values())
        max_label_len = max(len(str(label)) for label in label_counts.keys())
        
        lines = ["Class Distribution:", "=" * (max_label_len + width + 15)]
        
        for label, count in label_counts.most_common():
            bar_len = int(count / max_count * width)
            bar = "█" * bar_len
            pct = count / len(data) * 100
            lines.append(f"{str(label):<{max_label_len}} | {bar:<{width}} | {count:>5} ({pct:5.1f}%)")
        
        lines.append("=" * (max_label_len + width + 15))
        lines.append(f"Total samples: {len(data)}")
        
        return "\n".join(lines)


# =============================================================================
# FEATURE ANALYZER
# =============================================================================

class FeatureAnalyzer:
    """
    Analyzes features/fields in the dataset
    """
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
    
    def analyze_missing_features(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze missing values across all features
        """
        if not data:
            return {"error": "Empty dataset"}
        
        # Get all unique keys
        all_keys = set()
        for item in data:
            all_keys.update(item.keys())
        
        total = len(data)
        missing_analysis = {}
        
        for key in all_keys:
            missing = sum(1 for item in data if key not in item or item[key] is None or item[key] == "")
            percentage = missing / total * 100
            
            missing_analysis[key] = {
                "missing_count": missing,
                "missing_percentage": round(percentage, 2),
                "is_concerning": percentage > self.config.missing_threshold * 100,
            }
        
        # Sort by missing percentage
        sorted_missing = sorted(
            missing_analysis.items(),
            key=lambda x: x[1]["missing_percentage"],
            reverse=True
        )
        
        concerning_features = [
            k for k, v in missing_analysis.items()
            if v["is_concerning"]
        ]
        
        return {
            "total_features": len(all_keys),
            "features": dict(sorted_missing),
            "concerning_features": concerning_features,
            "completeness_score": round(
                1 - sum(v["missing_percentage"] for v in missing_analysis.values()) / (len(all_keys) * 100),
                4
            ),
        }
    
    def analyze_categorical_features(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze categorical features
        """
        analysis = {}
        
        for key in self.config.categorical_keys:
            values = [item.get(key) for item in data if item.get(key) is not None]
            
            if not values:
                analysis[key] = {"present": False}
                continue
            
            counts = Counter(values)
            
            analysis[key] = {
                "present": True,
                "unique_values": len(counts),
                "top_5": dict(counts.most_common(5)),
                "coverage": round(len(values) / len(data) * 100, 2),
            }
        
        return analysis
    
    def analyze_text_features(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze text features (length, vocabulary, etc.)
        """
        analysis = {}
        
        for key in self.config.text_keys:
            texts = [item.get(key) for item in data if item.get(key) and isinstance(item.get(key), str)]
            
            if not texts:
                analysis[key] = {"present": False}
                continue
            
            lengths = [len(t) for t in texts]
            word_counts = [len(t.split()) for t in texts]
            
            analysis[key] = {
                "present": True,
                "count": len(texts),
                "coverage": round(len(texts) / len(data) * 100, 2),
                "length": {
                    "min": min(lengths),
                    "max": max(lengths),
                    "avg": round(sum(lengths) / len(lengths), 1),
                },
                "word_count": {
                    "min": min(word_counts),
                    "max": max(word_counts),
                    "avg": round(sum(word_counts) / len(word_counts), 1),
                },
                "empty_count": sum(1 for t in texts if len(t.strip()) == 0),
            }
        
        return analysis
    
    def analyze_numeric_features(self, data: List[Dict]) -> Dict[str, Any]:
        """
        Analyze numeric features
        """
        analysis = {}
        
        for key in self.config.numeric_keys:
            values = []
            for item in data:
                val = item.get(key)
                if val is not None:
                    try:
                        values.append(float(val))
                    except (ValueError, TypeError):
                        pass
            
            if not values:
                analysis[key] = {"present": False}
                continue
            
            sorted_vals = sorted(values)
            n = len(sorted_vals)
            
            analysis[key] = {
                "present": True,
                "count": n,
                "coverage": round(n / len(data) * 100, 2),
                "min": sorted_vals[0],
                "max": sorted_vals[-1],
                "mean": round(sum(values) / n, 2),
                "median": sorted_vals[n // 2],
                "std": round(self._compute_std(values), 2),
            }
        
        return analysis
    
    def _compute_std(self, values: List[float]) -> float:
        """Compute standard deviation"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / (len(values) - 1)
        return math.sqrt(variance)


# =============================================================================
# BIAS DETECTOR
# =============================================================================

class BiasDetector:
    """
    Detects potential biases in the dataset
    """
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
    
    def detect_biases(
        self,
        data: List[Dict],
        label_key: str = None,
        sensitive_keys: List[str] = None
    ) -> Dict[str, Any]:
        """
        Detect potential biases across sensitive attributes
        
        Args:
            data: Dataset
            label_key: Label column
            sensitive_keys: Attributes to check for bias (e.g., gender, state, language)
        """
        label_key = label_key or self.config.label_key
        sensitive_keys = sensitive_keys or ["language", "state", "gender", "category"]
        
        biases = []
        bias_report = {}
        
        for sensitive_key in sensitive_keys:
            # Group by sensitive attribute
            groups = defaultdict(list)
            for item in data:
                attr = item.get(sensitive_key, "unknown")
                groups[attr].append(item)
            
            if len(groups) < 2:
                continue
            
            # Analyze label distribution within each group
            group_distributions = {}
            for attr_val, items in groups.items():
                labels = Counter(item.get(label_key, "unknown") for item in items)
                total = len(items)
                group_distributions[attr_val] = {
                    label: count / total for label, count in labels.items()
                }
            
            # Check for disparities
            all_labels = set()
            for dist in group_distributions.values():
                all_labels.update(dist.keys())
            
            disparities = []
            for label in all_labels:
                rates = [
                    (attr, dist.get(label, 0))
                    for attr, dist in group_distributions.items()
                ]
                
                if len(rates) >= 2:
                    max_rate = max(r[1] for r in rates)
                    min_rate = min(r[1] for r in rates)
                    
                    # Disparate impact ratio
                    if max_rate > 0:
                        disparity_ratio = min_rate / max_rate
                        
                        # 4/5ths rule: ratio < 0.8 indicates potential bias
                        if disparity_ratio < 0.8:
                            disparities.append({
                                "label": label,
                                "disparity_ratio": round(disparity_ratio, 3),
                                "max_group": max(rates, key=lambda x: x[1])[0],
                                "min_group": min(rates, key=lambda x: x[1])[0],
                            })
            
            if disparities:
                biases.append({
                    "attribute": sensitive_key,
                    "disparities": disparities,
                })
            
            bias_report[sensitive_key] = {
                "groups": list(groups.keys()),
                "group_sizes": {k: len(v) for k, v in groups.items()},
                "distributions": group_distributions,
                "has_disparity": len(disparities) > 0,
            }
        
        return {
            "biases_detected": len(biases) > 0,
            "bias_count": len(biases),
            "biases": biases,
            "detailed_report": bias_report,
            "recommendations": self._get_bias_recommendations(biases),
        }
    
    def _get_bias_recommendations(self, biases: List[Dict]) -> List[str]:
        """Generate recommendations based on detected biases"""
        recommendations = []
        
        for bias in biases:
            attr = bias["attribute"]
            for disparity in bias["disparities"]:
                recommendations.append(
                    f"Review {attr}-based disparity for label '{disparity['label']}': "
                    f"'{disparity['min_group']}' group has {disparity['disparity_ratio']:.0%} rate "
                    f"compared to '{disparity['max_group']}' group"
                )
        
        if not biases:
            recommendations.append("No significant biases detected based on 4/5ths rule")
        
        return recommendations
    
    def detect_representation_bias(
        self,
        data: List[Dict],
        expected_distribution: Dict[str, Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Check if dataset representation matches expected population distribution
        
        Args:
            expected_distribution: Expected percentages by attribute
                e.g., {"state": {"UP": 0.16, "Maharashtra": 0.09, ...}}
        """
        if not expected_distribution:
            # Default: Indian state population distribution (approximate)
            expected_distribution = {
                "state": {
                    "UP": 0.166, "Maharashtra": 0.092, "Bihar": 0.087,
                    "West Bengal": 0.075, "Madhya Pradesh": 0.060,
                    "Tamil Nadu": 0.057, "Rajasthan": 0.056,
                    "Karnataka": 0.050, "Gujarat": 0.050,
                },
                "language": {
                    "hi": 0.44, "en": 0.30, "hinglish": 0.26,
                },
            }
        
        issues = []
        report = {}
        
        for attr, expected in expected_distribution.items():
            actual = Counter(item.get(attr) for item in data if item.get(attr))
            total = sum(actual.values())
            
            if total == 0:
                continue
            
            actual_pct = {k: v / total for k, v in actual.items()}
            
            deviations = {}
            for category, exp_pct in expected.items():
                act_pct = actual_pct.get(category, 0)
                deviation = act_pct - exp_pct
                
                if abs(deviation) > 0.05:  # >5% deviation
                    deviations[category] = {
                        "expected": round(exp_pct * 100, 1),
                        "actual": round(act_pct * 100, 1),
                        "deviation": round(deviation * 100, 1),
                    }
                    issues.append(
                        f"{attr}='{category}': expected {exp_pct:.1%}, got {act_pct:.1%}"
                    )
            
            report[attr] = {
                "expected": expected,
                "actual": {k: round(v, 3) for k, v in actual_pct.items()},
                "deviations": deviations,
            }
        
        return {
            "representation_issues": issues,
            "report": report,
        }


# =============================================================================
# DATASET ANALYZER (MAIN CLASS)
# =============================================================================

class DatasetAnalyzer:
    """
    Comprehensive dataset analyzer combining all analysis components
    """
    
    def __init__(self, config: AnalysisConfig = None):
        self.config = config or AnalysisConfig()
        self.class_analyzer = ClassDistributionAnalyzer(self.config)
        self.feature_analyzer = FeatureAnalyzer(self.config)
        self.bias_detector = BiasDetector(self.config)
    
    def analyze(
        self,
        data: List[Dict],
        include_bias_check: bool = True
    ) -> Dict[str, Any]:
        """
        Perform comprehensive dataset analysis
        """
        if not data:
            return {"error": "Empty dataset"}
        
        logger.info(f"Analyzing dataset with {len(data)} samples...")
        
        analysis = {
            "analysis_timestamp": datetime.now().isoformat(),
            "dataset_size": len(data),
        }
        
        # Class distribution
        analysis["class_distribution"] = self.class_analyzer.analyze(data)
        
        # Feature analysis
        analysis["missing_features"] = self.feature_analyzer.analyze_missing_features(data)
        analysis["categorical_features"] = self.feature_analyzer.analyze_categorical_features(data)
        analysis["text_features"] = self.feature_analyzer.analyze_text_features(data)
        analysis["numeric_features"] = self.feature_analyzer.analyze_numeric_features(data)
        
        # Bias detection
        if include_bias_check:
            analysis["bias_analysis"] = self.bias_detector.detect_biases(data)
            analysis["representation_analysis"] = self.bias_detector.detect_representation_bias(data)
        
        # Overall health score
        analysis["health_score"] = self._compute_health_score(analysis)
        
        # Recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        return analysis
    
    def _compute_health_score(self, analysis: Dict) -> Dict[str, Any]:
        """Compute overall dataset health score"""
        scores = {}
        
        # Balance score (from class distribution)
        class_dist = analysis.get("class_distribution", {})
        scores["balance"] = class_dist.get("balance_score", 0)
        
        # Completeness score (from missing features)
        missing = analysis.get("missing_features", {})
        scores["completeness"] = missing.get("completeness_score", 0)
        
        # Bias score (inverse of bias issues)
        bias = analysis.get("bias_analysis", {})
        bias_count = bias.get("bias_count", 0)
        scores["fairness"] = max(0, 1 - bias_count * 0.2)  # Penalize for each bias
        
        # Overall score (weighted average)
        weights = {"balance": 0.4, "completeness": 0.3, "fairness": 0.3}
        overall = sum(scores[k] * weights[k] for k in weights)
        
        return {
            "overall": round(overall, 4),
            "components": {k: round(v, 4) for k, v in scores.items()},
            "rating": self._score_to_rating(overall),
        }
    
    def _score_to_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 0.9:
            return "Excellent"
        elif score >= 0.8:
            return "Good"
        elif score >= 0.7:
            return "Fair"
        elif score >= 0.6:
            return "Needs Improvement"
        else:
            return "Poor"
    
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Class imbalance recommendations
        class_dist = analysis.get("class_distribution", {})
        if not class_dist.get("is_balanced", True):
            imbalanced = class_dist.get("imbalanced_classes", [])
            recommendations.append(
                f"Address class imbalance. Consider oversampling minority classes: {imbalanced}"
            )
        
        rare_classes = class_dist.get("rare_classes", [])
        if rare_classes:
            recommendations.append(
                f"Collect more data for rare classes (< {self.config.rare_class_threshold} samples): {rare_classes}"
            )
        
        # Missing features recommendations
        missing = analysis.get("missing_features", {})
        concerning = missing.get("concerning_features", [])
        if concerning:
            recommendations.append(
                f"Address high missing rates in: {concerning[:5]}"  # Top 5
            )
        
        # Bias recommendations
        bias = analysis.get("bias_analysis", {})
        if bias.get("biases_detected"):
            recommendations.extend(bias.get("recommendations", [])[:3])  # Top 3
        
        if not recommendations:
            recommendations.append("Dataset looks healthy! Ready for model training.")
        
        return recommendations
    
    def get_summary_report(self, data: List[Dict]) -> str:
        """
        Generate human-readable summary report
        """
        analysis = self.analyze(data)
        
        lines = [
            "=" * 60,
            "DATASET ANALYSIS REPORT",
            "=" * 60,
            "",
            f"Analysis Date: {analysis['analysis_timestamp']}",
            f"Dataset Size: {analysis['dataset_size']} samples",
            "",
            "--- CLASS DISTRIBUTION ---",
        ]
        
        # Add histogram
        lines.append(self.class_analyzer.get_ascii_histogram(data))
        
        class_dist = analysis.get("class_distribution", {})
        lines.extend([
            "",
            f"Number of Classes: {class_dist.get('num_classes', 0)}",
            f"Balance Score: {class_dist.get('balance_score', 0):.2%}",
            f"Imbalance Ratio: {class_dist.get('imbalance_ratio', 0):.1f}:1",
            f"Is Balanced: {'Yes' if class_dist.get('is_balanced') else 'No'}",
        ])
        
        # Health score
        health = analysis.get("health_score", {})
        lines.extend([
            "",
            "--- HEALTH SCORE ---",
            f"Overall: {health.get('overall', 0):.1%} ({health.get('rating', 'Unknown')})",
            f"  - Balance: {health.get('components', {}).get('balance', 0):.1%}",
            f"  - Completeness: {health.get('components', {}).get('completeness', 0):.1%}",
            f"  - Fairness: {health.get('components', {}).get('fairness', 0):.1%}",
        ])
        
        # Recommendations
        lines.extend([
            "",
            "--- RECOMMENDATIONS ---",
        ])
        for i, rec in enumerate(analysis.get("recommendations", []), 1):
            lines.append(f"{i}. {rec}")
        
        lines.append("")
        lines.append("=" * 60)
        
        return "\n".join(lines)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def analyze_dataset(
    data: List[Dict],
    label_key: str = "label"
) -> Dict[str, Any]:
    """
    Quick analysis of a dataset
    """
    config = AnalysisConfig(label_key=label_key)
    analyzer = DatasetAnalyzer(config)
    return analyzer.analyze(data)


def print_dataset_report(data: List[Dict], label_key: str = "label"):
    """
    Print human-readable dataset report
    """
    config = AnalysisConfig(label_key=label_key)
    analyzer = DatasetAnalyzer(config)
    print(analyzer.get_summary_report(data))
