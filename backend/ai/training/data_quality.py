"""
Data Quality & Analysis Module
Shared utilities for all collectors following best practices:
- Deduplication
- Class balance analysis
- Train/val/test splitting
- Inter-annotator agreement (Cohen's Kappa, Krippendorff's Alpha)
- Diversity metrics
- Data documentation
"""

import json
import hashlib
import random
import math
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from collections import Counter, defaultdict
from enum import Enum

# ============================================================================
# DEDUPLICATION
# ============================================================================

class Deduplicator:
    """
    Deduplicate records based on content hashing
    Supports exact and near-duplicate detection
    """
    
    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.duplicates_found = 0
    
    def compute_hash(self, text: str, normalize: bool = True) -> str:
        """Compute content hash"""
        if normalize:
            # Normalize: lowercase, strip whitespace, remove special chars
            text = text.lower().strip()
            text = ''.join(c for c in text if c.isalnum() or c.isspace())
            text = ' '.join(text.split())  # Normalize whitespace
        return hashlib.md5(text.encode()).hexdigest()
    
    def is_duplicate(self, text: str, normalize: bool = True) -> bool:
        """Check if text is duplicate"""
        h = self.compute_hash(text, normalize)
        if h in self.seen_hashes:
            self.duplicates_found += 1
            return True
        self.seen_hashes.add(h)
        return False
    
    def compute_simhash(self, text: str, num_bits: int = 64) -> int:
        """
        Compute SimHash for near-duplicate detection
        Similar texts will have similar hashes
        """
        tokens = text.lower().split()
        v = [0] * num_bits
        
        for token in tokens:
            token_hash = int(hashlib.md5(token.encode()).hexdigest(), 16)
            for i in range(num_bits):
                if token_hash & (1 << i):
                    v[i] += 1
                else:
                    v[i] -= 1
        
        simhash = 0
        for i in range(num_bits):
            if v[i] > 0:
                simhash |= (1 << i)
        
        return simhash
    
    def hamming_distance(self, hash1: int, hash2: int, num_bits: int = 64) -> int:
        """Compute Hamming distance between two hashes"""
        x = hash1 ^ hash2
        distance = 0
        while x:
            distance += 1
            x &= x - 1
        return distance
    
    def is_near_duplicate(self, text: str, threshold: int = 3) -> bool:
        """Check if text is a near-duplicate (SimHash within threshold)"""
        new_hash = self.compute_simhash(text)
        for existing_hash in self.seen_hashes:
            if isinstance(existing_hash, int):
                if self.hamming_distance(new_hash, existing_hash) <= threshold:
                    return True
        return False


# ============================================================================
# CLASS BALANCE ANALYSIS
# ============================================================================

class ClassBalanceAnalyzer:
    """
    Analyze class distribution and detect imbalances
    Recommends oversampling/undersampling strategies
    """
    
    def __init__(self, labels: List[str]):
        self.distribution = Counter(labels)
        self.total = len(labels)
    
    def get_distribution(self) -> Dict[str, int]:
        return dict(self.distribution)
    
    def get_percentages(self) -> Dict[str, float]:
        return {k: v / self.total * 100 for k, v in self.distribution.items()}
    
    def get_imbalance_ratio(self) -> float:
        """Ratio of majority to minority class"""
        if not self.distribution:
            return 0
        counts = list(self.distribution.values())
        return max(counts) / min(counts) if min(counts) > 0 else float('inf')
    
    def get_underrepresented_classes(self, threshold_pct: float = 10.0) -> List[str]:
        """Classes with less than threshold percentage"""
        percentages = self.get_percentages()
        return [k for k, v in percentages.items() if v < threshold_pct]
    
    def recommend_strategy(self) -> Dict[str, Any]:
        """Recommend balancing strategy"""
        ratio = self.get_imbalance_ratio()
        underrep = self.get_underrepresented_classes()
        
        if ratio <= 1.5:
            strategy = "none"
            reason = "Classes are well balanced"
        elif ratio <= 3:
            strategy = "class_weights"
            reason = "Mild imbalance - use class weights during training"
        elif ratio <= 10:
            strategy = "oversample"
            reason = "Moderate imbalance - oversample minority classes"
        else:
            strategy = "smote_or_synthetic"
            reason = "Severe imbalance - use SMOTE or generate synthetic data"
        
        return {
            "strategy": strategy,
            "reason": reason,
            "imbalance_ratio": ratio,
            "underrepresented_classes": underrep,
            "distribution": self.get_distribution(),
        }


# ============================================================================
# TRAIN/VAL/TEST SPLITTING
# ============================================================================

class DatasetSplitter:
    """
    Split dataset into train/validation/test sets
    Ensures stratified sampling for balanced splits
    """
    
    @staticmethod
    def random_split(
        data: List[Any],
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42
    ) -> Tuple[List[Any], List[Any], List[Any]]:
        """Simple random split"""
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.01
        
        random.seed(seed)
        shuffled = data.copy()
        random.shuffle(shuffled)
        
        n = len(shuffled)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        return (
            shuffled[:train_end],
            shuffled[train_end:val_end],
            shuffled[val_end:]
        )
    
    @staticmethod
    def stratified_split(
        data: List[Dict],
        label_key: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Stratified split - maintains class distribution in each split
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.01
        
        random.seed(seed)
        
        # Group by label
        by_label = defaultdict(list)
        for item in data:
            label = item.get(label_key, "unknown")
            by_label[label].append(item)
        
        train, val, test = [], [], []
        
        for label, items in by_label.items():
            random.shuffle(items)
            n = len(items)
            train_end = int(n * train_ratio)
            val_end = train_end + int(n * val_ratio)
            
            train.extend(items[:train_end])
            val.extend(items[train_end:val_end])
            test.extend(items[val_end:])
        
        # Shuffle final sets
        random.shuffle(train)
        random.shuffle(val)
        random.shuffle(test)
        
        return train, val, test
    
    @staticmethod
    def temporal_split(
        data: List[Dict],
        date_key: str,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Temporal split - older data for training, newer for val/test
        Prevents data leakage in time-series scenarios
        """
        sorted_data = sorted(data, key=lambda x: x.get(date_key, ""))
        
        n = len(sorted_data)
        train_end = int(n * train_ratio)
        val_end = train_end + int(n * val_ratio)
        
        return (
            sorted_data[:train_end],
            sorted_data[train_end:val_end],
            sorted_data[val_end:]
        )


# ============================================================================
# INTER-ANNOTATOR AGREEMENT
# ============================================================================

class AnnotatorAgreement:
    """
    Calculate inter-annotator agreement metrics
    - Cohen's Kappa (2 annotators)
    - Fleiss' Kappa (multiple annotators)
    - Krippendorff's Alpha
    """
    
    @staticmethod
    def cohens_kappa(
        annotations1: List[str],
        annotations2: List[str]
    ) -> float:
        """
        Cohen's Kappa for 2 annotators
        κ = (p_o - p_e) / (1 - p_e)
        """
        assert len(annotations1) == len(annotations2)
        n = len(annotations1)
        
        if n == 0:
            return 0.0
        
        # Observed agreement
        p_o = sum(1 for a, b in zip(annotations1, annotations2) if a == b) / n
        
        # Expected agreement by chance
        labels = set(annotations1) | set(annotations2)
        p_e = 0.0
        for label in labels:
            p1 = annotations1.count(label) / n
            p2 = annotations2.count(label) / n
            p_e += p1 * p2
        
        if p_e == 1.0:
            return 1.0 if p_o == 1.0 else 0.0
        
        return (p_o - p_e) / (1 - p_e)
    
    @staticmethod
    def interpret_kappa(kappa: float) -> str:
        """Interpret Kappa value"""
        if kappa < 0:
            return "Poor (less than chance)"
        elif kappa < 0.20:
            return "Slight agreement"
        elif kappa < 0.40:
            return "Fair agreement"
        elif kappa < 0.60:
            return "Moderate agreement"
        elif kappa < 0.80:
            return "Substantial agreement"
        else:
            return "Almost perfect agreement"
    
    @staticmethod
    def fleiss_kappa(
        annotations: List[List[str]],
        categories: List[str]
    ) -> float:
        """
        Fleiss' Kappa for multiple annotators
        annotations[i] = list of labels from all annotators for item i
        """
        n_items = len(annotations)
        n_raters = len(annotations[0]) if annotations else 0
        n_categories = len(categories)
        
        if n_items == 0 or n_raters == 0:
            return 0.0
        
        # Count assignments per category per item
        cat_to_idx = {c: i for i, c in enumerate(categories)}
        
        # P_j: proportion of all assignments to category j
        total_assignments = n_items * n_raters
        p_j = []
        for cat in categories:
            count = sum(item_anns.count(cat) for item_anns in annotations)
            p_j.append(count / total_assignments)
        
        # P_i: extent of agreement for item i
        p_i = []
        for item_anns in annotations:
            cat_counts = Counter(item_anns)
            sum_sq = sum(c * c for c in cat_counts.values())
            p_i.append((sum_sq - n_raters) / (n_raters * (n_raters - 1)))
        
        # P_bar: mean of P_i
        p_bar = sum(p_i) / n_items if n_items > 0 else 0
        
        # P_e_bar: expected agreement by chance
        p_e_bar = sum(p * p for p in p_j)
        
        if p_e_bar == 1.0:
            return 1.0 if p_bar == 1.0 else 0.0
        
        return (p_bar - p_e_bar) / (1 - p_e_bar)
    
    @staticmethod
    def krippendorff_alpha_nominal(
        annotations: List[Dict[str, str]]
    ) -> float:
        """
        Krippendorff's Alpha for nominal data
        annotations: list of {annotator_id: label} dicts
        """
        # Build reliability matrix
        annotators = set()
        for item in annotations:
            annotators.update(item.keys())
        
        annotators = list(annotators)
        categories = set()
        for item in annotations:
            categories.update(item.values())
        categories = list(categories)
        
        n_items = len(annotations)
        if n_items < 2:
            return 0.0
        
        # Observed disagreement
        d_o = 0.0
        total_pairs = 0
        
        for item in annotations:
            values = list(item.values())
            n = len(values)
            for i in range(n):
                for j in range(i + 1, n):
                    total_pairs += 1
                    if values[i] != values[j]:
                        d_o += 1
        
        d_o = d_o / total_pairs if total_pairs > 0 else 0
        
        # Expected disagreement
        all_values = []
        for item in annotations:
            all_values.extend(item.values())
        
        value_counts = Counter(all_values)
        total = len(all_values)
        
        d_e = 0.0
        for cat1 in categories:
            for cat2 in categories:
                if cat1 != cat2:
                    d_e += value_counts[cat1] * value_counts[cat2]
        
        d_e = d_e / (total * (total - 1)) if total > 1 else 0
        
        if d_e == 0:
            return 1.0 if d_o == 0 else 0.0
        
        return 1 - (d_o / d_e)


# ============================================================================
# DIVERSITY METRICS
# ============================================================================

class DiversityAnalyzer:
    """
    Analyze dataset diversity across different dimensions
    """
    
    def __init__(self, data: List[Dict]):
        self.data = data
    
    def analyze_dimension(self, key: str) -> Dict[str, Any]:
        """Analyze diversity for a specific dimension"""
        values = [item.get(key) for item in self.data if item.get(key)]
        
        distribution = Counter(values)
        unique_count = len(distribution)
        total = len(values)
        
        # Shannon entropy (higher = more diverse)
        entropy = 0.0
        for count in distribution.values():
            p = count / total
            if p > 0:
                entropy -= p * math.log2(p)
        
        # Normalized entropy (0-1)
        max_entropy = math.log2(unique_count) if unique_count > 1 else 1
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0
        
        return {
            "dimension": key,
            "unique_values": unique_count,
            "total_samples": total,
            "entropy": entropy,
            "normalized_entropy": normalized_entropy,
            "diversity_score": normalized_entropy,  # 0 = no diversity, 1 = max diversity
            "distribution": dict(distribution.most_common(20)),
        }
    
    def analyze_all(self, dimensions: List[str]) -> Dict[str, Any]:
        """Analyze diversity across all dimensions"""
        results = {}
        for dim in dimensions:
            results[dim] = self.analyze_dimension(dim)
        
        # Overall diversity score
        scores = [r["diversity_score"] for r in results.values()]
        overall = sum(scores) / len(scores) if scores else 0
        
        return {
            "dimensions": results,
            "overall_diversity_score": overall,
            "recommendations": self._get_recommendations(results),
        }
    
    def _get_recommendations(self, results: Dict) -> List[str]:
        """Generate diversity improvement recommendations"""
        recs = []
        for dim, analysis in results.items():
            if analysis["diversity_score"] < 0.5:
                recs.append(
                    f"Low diversity in '{dim}' (score: {analysis['diversity_score']:.2f}). "
                    f"Consider collecting more varied examples."
                )
            if analysis["unique_values"] < 3:
                recs.append(
                    f"'{dim}' has only {analysis['unique_values']} unique values. "
                    f"Add more categories if applicable."
                )
        return recs


# ============================================================================
# DATASET DOCUMENTATION (DATASHEET)
# ============================================================================

class DatasheetGenerator:
    """
    Generate dataset documentation following Datasheets for Datasets format
    """
    
    @staticmethod
    def generate(
        name: str,
        description: str,
        data_sources: List[str],
        collection_method: str,
        annotation_guidelines: str,
        class_definitions: Dict[str, str],
        total_samples: int,
        class_distribution: Dict[str, int],
        known_biases: List[str],
        privacy_notes: str,
        created_by: str,
        version: str = "1.0"
    ) -> Dict:
        """Generate comprehensive datasheet"""
        return {
            "metadata": {
                "name": name,
                "version": version,
                "created_at": datetime.now().isoformat(),
                "created_by": created_by,
            },
            "motivation": {
                "description": description,
                "intended_use": f"Training AI models for {name}",
            },
            "composition": {
                "total_samples": total_samples,
                "class_distribution": class_distribution,
                "class_definitions": class_definitions,
            },
            "collection_process": {
                "data_sources": data_sources,
                "collection_method": collection_method,
                "annotation_guidelines": annotation_guidelines,
            },
            "preprocessing": {
                "cleaning_steps": [
                    "Deduplication",
                    "Text normalization",
                    "Missing value handling",
                ],
            },
            "uses": {
                "intended_uses": [
                    "Training classification/ranking models",
                    "Model evaluation and benchmarking",
                ],
                "not_intended_for": [
                    "Production without further validation",
                    "Tasks outside the defined scope",
                ],
            },
            "distribution": {
                "license": "Internal use only",
                "access_control": "Restricted",
            },
            "maintenance": {
                "update_frequency": "Continuous with feedback loop",
                "contact": created_by,
            },
            "known_issues": {
                "biases": known_biases,
                "limitations": [
                    "May not cover all edge cases",
                    "Class imbalance may affect model performance",
                ],
            },
            "privacy": {
                "notes": privacy_notes,
                "pii_handling": "Anonymized or masked",
                "compliance": "DPDP compliant",
            },
        }
    
    @staticmethod
    def save(datasheet: Dict, filepath: str):
        """Save datasheet to JSON file"""
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(datasheet, f, indent=2, ensure_ascii=False)


# ============================================================================
# TEXT NORMALIZATION
# ============================================================================

class TextNormalizer:
    """
    Normalize text for consistent processing
    """
    
    @staticmethod
    def normalize(text: str, options: Dict = None) -> str:
        """Apply normalization steps"""
        options = options or {}
        
        result = text
        
        # Remove HTML tags
        if options.get("remove_html", True):
            import re
            result = re.sub(r'<[^>]+>', ' ', result)
        
        # Normalize whitespace
        if options.get("normalize_whitespace", True):
            result = ' '.join(result.split())
        
        # Lowercase
        if options.get("lowercase", False):
            result = result.lower()
        
        # Remove special characters (keep Hindi/Devanagari)
        if options.get("remove_special", False):
            import re
            # Keep alphanumeric, Hindi characters, and basic punctuation
            result = re.sub(r'[^\w\s\u0900-\u097F.,!?-]', '', result)
        
        # Normalize numbers
        if options.get("normalize_numbers", False):
            import re
            result = re.sub(r'\d+', '[NUM]', result)
        
        return result.strip()
    
    @staticmethod
    def normalize_field_name(field_name: str) -> str:
        """
        Normalize form field names to consistent format
        "Candidate's Name" -> "candidate_name"
        "Father/Guardian Name" -> "father_guardian_name"
        """
        import re
        
        # Lowercase
        result = field_name.lower()
        
        # Replace special characters with underscore
        result = re.sub(r"['`]s?\s*", "_", result)  # Possessives
        result = re.sub(r'[/\\]', '_', result)  # Slashes
        result = re.sub(r'[^a-z0-9_\s]', '', result)  # Other special chars
        
        # Replace spaces with underscore
        result = re.sub(r'\s+', '_', result)
        
        # Remove multiple underscores
        result = re.sub(r'_+', '_', result)
        
        # Strip leading/trailing underscores
        result = result.strip('_')
        
        return result


# ============================================================================
# FEEDBACK LOOP
# ============================================================================

class FeedbackLoop:
    """
    Manage feedback loop for continuous dataset improvement
    Incorporates operator corrections, user feedback, and model errors
    """
    
    def __init__(self, data_dir: str):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.corrections_file = self.data_dir / "corrections.jsonl"
        self.model_errors_file = self.data_dir / "model_errors.jsonl"
        self.user_feedback_file = self.data_dir / "user_feedback.jsonl"
    
    def log_operator_correction(
        self,
        original_prediction: Any,
        corrected_value: Any,
        context: Dict,
        operator_id: str
    ):
        """Log when an operator corrects a model prediction"""
        record = {
            "type": "operator_correction",
            "original": original_prediction,
            "corrected": corrected_value,
            "context": context,
            "operator_id": operator_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._append(self.corrections_file, record)
    
    def log_model_error(
        self,
        input_data: Any,
        predicted: Any,
        expected: Any,
        model_version: str,
        error_type: str = None
    ):
        """Log model prediction errors for retraining"""
        record = {
            "type": "model_error",
            "input": input_data,
            "predicted": predicted,
            "expected": expected,
            "model_version": model_version,
            "error_type": error_type,
            "timestamp": datetime.now().isoformat(),
        }
        self._append(self.model_errors_file, record)
    
    def log_user_feedback(
        self,
        item_id: str,
        feedback_type: str,  # "positive", "negative", "correction"
        details: str = None,
        user_id: str = None
    ):
        """Log user feedback on recommendations/predictions"""
        record = {
            "type": "user_feedback",
            "item_id": item_id,
            "feedback_type": feedback_type,
            "details": details,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
        }
        self._append(self.user_feedback_file, record)
    
    def get_correction_samples(self, min_count: int = 5) -> List[Dict]:
        """
        Get frequently corrected patterns for retraining
        Returns patterns that were corrected multiple times
        """
        corrections = self._read(self.corrections_file)
        
        # Group by (original, corrected) pattern
        patterns = defaultdict(list)
        for c in corrections:
            key = (str(c.get("original")), str(c.get("corrected")))
            patterns[key].append(c)
        
        # Filter by minimum count
        frequent = [
            {
                "original": k[0],
                "corrected": k[1],
                "count": len(v),
                "examples": v[:3],
            }
            for k, v in patterns.items()
            if len(v) >= min_count
        ]
        
        return sorted(frequent, key=lambda x: -x["count"])
    
    def _append(self, filepath: Path, record: Dict):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _read(self, filepath: Path) -> List[Dict]:
        if not filepath.exists():
            return []
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
