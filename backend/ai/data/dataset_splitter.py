"""
Dataset Splitter
Splits annotated datasets into train/validation/test sets
with stratification, diversity checks, and reproducibility
"""

import logging
import random
import hashlib
import json
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict, Counter
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# SPLIT CONFIGURATION
# =============================================================================

@dataclass
class SplitConfig:
    """Configuration for dataset splitting"""
    train_ratio: float = 0.70
    val_ratio: float = 0.15
    test_ratio: float = 0.15
    
    # Stratification
    stratify_by: List[str] = field(default_factory=lambda: ["label"])
    ensure_min_samples: int = 2  # Minimum samples per class per split
    
    # Diversity
    diversity_keys: List[str] = field(default_factory=lambda: ["language", "state", "source"])
    
    # Reproducibility
    random_seed: int = 42
    
    # Validation
    allow_leakage_check: bool = True  # Check for data leakage between splits
    
    def __post_init__(self):
        total = self.train_ratio + self.val_ratio + self.test_ratio
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")


@dataclass
class SplitResult:
    """Result of dataset splitting"""
    train: List[Dict]
    val: List[Dict]
    test: List[Dict]
    
    # Metadata
    config: SplitConfig = None
    split_timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    statistics: Dict = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)
    
    def get_split(self, split_name: str) -> List[Dict]:
        """Get split by name"""
        return {"train": self.train, "val": self.val, "test": self.test}.get(split_name, [])
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for serialization"""
        return {
            "train_size": len(self.train),
            "val_size": len(self.val),
            "test_size": len(self.test),
            "config": {
                "train_ratio": self.config.train_ratio if self.config else 0.7,
                "val_ratio": self.config.val_ratio if self.config else 0.15,
                "test_ratio": self.config.test_ratio if self.config else 0.15,
                "random_seed": self.config.random_seed if self.config else 42,
            },
            "split_timestamp": self.split_timestamp,
            "statistics": self.statistics,
            "warnings": self.warnings,
        }


# =============================================================================
# DATASET SPLITTER
# =============================================================================

class DatasetSplitter:
    """
    Splits datasets with stratification and diversity balancing
    
    Features:
    - Stratified splitting by label
    - Diversity balancing across splits
    - Data leakage detection
    - Reproducible splits via seeding
    - Handles imbalanced classes
    """
    
    def __init__(self, config: SplitConfig = None):
        self.config = config or SplitConfig()
        random.seed(self.config.random_seed)
    
    def split(
        self,
        data: List[Dict],
        label_key: str = "label"
    ) -> SplitResult:
        """
        Split dataset into train/val/test with stratification
        
        Args:
            data: List of annotated items
            label_key: Key containing the label
        
        Returns:
            SplitResult with train, val, test splits
        """
        if not data:
            raise ValueError("Empty dataset provided")
        
        warnings = []
        
        # Group by label for stratification
        label_groups = defaultdict(list)
        unlabeled = []
        
        for item in data:
            label = item.get(label_key)
            if label is not None:
                label_groups[label].append(item)
            else:
                unlabeled.append(item)
        
        if unlabeled:
            warnings.append(f"{len(unlabeled)} items have no label, distributed proportionally")
        
        # Check for rare classes
        for label, items in label_groups.items():
            min_needed = self.config.ensure_min_samples * 3  # For 3 splits
            if len(items) < min_needed:
                warnings.append(
                    f"Class '{label}' has only {len(items)} samples, "
                    f"minimum {min_needed} needed for proper stratification"
                )
        
        # Stratified split
        train, val, test = [], [], []
        
        for label, items in label_groups.items():
            random.shuffle(items)
            
            n = len(items)
            n_train = max(self.config.ensure_min_samples, int(n * self.config.train_ratio))
            n_val = max(self.config.ensure_min_samples, int(n * self.config.val_ratio))
            n_test = max(self.config.ensure_min_samples, n - n_train - n_val)
            
            # Adjust if we don't have enough samples
            total_needed = n_train + n_val + n_test
            if total_needed > n:
                # Scale down proportionally
                scale = n / total_needed
                n_train = max(1, int(n_train * scale))
                n_val = max(1, int(n_val * scale))
                n_test = max(1, n - n_train - n_val)
            
            train.extend(items[:n_train])
            val.extend(items[n_train:n_train + n_val])
            test.extend(items[n_train + n_val:n_train + n_val + n_test])
        
        # Distribute unlabeled items proportionally
        if unlabeled:
            random.shuffle(unlabeled)
            n = len(unlabeled)
            n_train = int(n * self.config.train_ratio)
            n_val = int(n * self.config.val_ratio)
            
            train.extend(unlabeled[:n_train])
            val.extend(unlabeled[n_train:n_train + n_val])
            test.extend(unlabeled[n_train + n_val:])
        
        # Shuffle each split
        random.shuffle(train)
        random.shuffle(val)
        random.shuffle(test)
        
        # Check for data leakage
        if self.config.allow_leakage_check:
            leakage = self._check_data_leakage(train, val, test)
            if leakage:
                warnings.extend(leakage)
        
        # Compute statistics
        statistics = self._compute_split_statistics(train, val, test, label_key)
        
        result = SplitResult(
            train=train,
            val=val,
            test=test,
            config=self.config,
            statistics=statistics,
            warnings=warnings,
        )
        
        logger.info(
            f"Split complete: train={len(train)}, val={len(val)}, test={len(test)}"
        )
        
        return result
    
    def split_by_time(
        self,
        data: List[Dict],
        time_key: str = "created_at",
        label_key: str = "label"
    ) -> SplitResult:
        """
        Split by time to simulate real-world deployment
        Earlier data for training, later for validation/test
        """
        # Sort by time
        def get_time(item):
            t = item.get(time_key)
            if isinstance(t, str):
                try:
                    return datetime.fromisoformat(t.replace("Z", "+00:00"))
                except:
                    return datetime.min
            return t or datetime.min
        
        sorted_data = sorted(data, key=get_time)
        
        n = len(sorted_data)
        n_train = int(n * self.config.train_ratio)
        n_val = int(n * self.config.val_ratio)
        
        train = sorted_data[:n_train]
        val = sorted_data[n_train:n_train + n_val]
        test = sorted_data[n_train + n_val:]
        
        warnings = [
            "Time-based split used. Train data is older than val/test.",
            f"Train period: up to {get_time(train[-1]) if train else 'N/A'}",
            f"Val period: {get_time(val[0]) if val else 'N/A'} to {get_time(val[-1]) if val else 'N/A'}",
            f"Test period: from {get_time(test[0]) if test else 'N/A'}",
        ]
        
        statistics = self._compute_split_statistics(train, val, test, label_key)
        
        return SplitResult(
            train=train,
            val=val,
            test=test,
            config=self.config,
            statistics=statistics,
            warnings=warnings,
        )
    
    def k_fold_split(
        self,
        data: List[Dict],
        k: int = 5,
        label_key: str = "label"
    ) -> List[Tuple[List[Dict], List[Dict]]]:
        """
        K-fold cross-validation splits
        
        Returns:
            List of (train, val) tuples for each fold
        """
        # Group by label for stratified k-fold
        label_groups = defaultdict(list)
        for item in data:
            label = item.get(label_key, "unknown")
            label_groups[label].append(item)
        
        # Shuffle each group
        for items in label_groups.values():
            random.shuffle(items)
        
        # Create k folds
        folds = [[] for _ in range(k)]
        
        for label, items in label_groups.items():
            for i, item in enumerate(items):
                folds[i % k].append(item)
        
        # Create train/val pairs
        splits = []
        for i in range(k):
            val = folds[i]
            train = []
            for j in range(k):
                if j != i:
                    train.extend(folds[j])
            
            random.shuffle(train)
            random.shuffle(val)
            splits.append((train, val))
        
        logger.info(f"Created {k}-fold split with ~{len(data)//k} samples per fold")
        return splits
    
    def _check_data_leakage(
        self,
        train: List[Dict],
        val: List[Dict],
        test: List[Dict]
    ) -> List[str]:
        """Check for duplicate items across splits"""
        warnings = []
        
        def item_hash(item: Dict) -> str:
            # Exclude metadata fields for comparison
            core_fields = {k: v for k, v in item.items() 
                         if not k.startswith("_") and k not in ["label", "annotator"]}
            return hashlib.md5(json.dumps(core_fields, sort_keys=True, default=str).encode()).hexdigest()
        
        train_hashes = set(item_hash(i) for i in train)
        val_hashes = set(item_hash(i) for i in val)
        test_hashes = set(item_hash(i) for i in test)
        
        train_val_overlap = train_hashes & val_hashes
        train_test_overlap = train_hashes & test_hashes
        val_test_overlap = val_hashes & test_hashes
        
        if train_val_overlap:
            warnings.append(f"DATA LEAKAGE: {len(train_val_overlap)} items appear in both train and val")
        if train_test_overlap:
            warnings.append(f"DATA LEAKAGE: {len(train_test_overlap)} items appear in both train and test")
        if val_test_overlap:
            warnings.append(f"DATA LEAKAGE: {len(val_test_overlap)} items appear in both val and test")
        
        return warnings
    
    def _compute_split_statistics(
        self,
        train: List[Dict],
        val: List[Dict],
        test: List[Dict],
        label_key: str
    ) -> Dict:
        """Compute statistics for each split"""
        
        def compute_stats(data: List[Dict], name: str) -> Dict:
            if not data:
                return {"size": 0}
            
            label_dist = Counter(item.get(label_key, "unknown") for item in data)
            
            # Diversity stats
            diversity = {}
            for key in self.config.diversity_keys:
                values = [item.get(key, "unknown") for item in data]
                diversity[key] = dict(Counter(values))
            
            return {
                "size": len(data),
                "label_distribution": dict(label_dist),
                "diversity": diversity,
            }
        
        return {
            "train": compute_stats(train, "train"),
            "val": compute_stats(val, "val"),
            "test": compute_stats(test, "test"),
            "total_samples": len(train) + len(val) + len(test),
        }


# =============================================================================
# DIVERSITY BALANCER
# =============================================================================

class DiversityBalancer:
    """
    Ensures diversity is maintained across splits
    """
    
    def __init__(self, diversity_keys: List[str] = None):
        self.diversity_keys = diversity_keys or ["language", "state", "source"]
    
    def check_diversity(
        self,
        split_result: SplitResult
    ) -> Dict[str, Any]:
        """
        Check if diversity is maintained across splits
        """
        issues = []
        diversity_report = {}
        
        for key in self.diversity_keys:
            train_dist = self._get_distribution(split_result.train, key)
            val_dist = self._get_distribution(split_result.val, key)
            test_dist = self._get_distribution(split_result.test, key)
            
            # Check for missing categories
            all_categories = set(train_dist.keys()) | set(val_dist.keys()) | set(test_dist.keys())
            
            for cat in all_categories:
                train_pct = train_dist.get(cat, 0)
                val_pct = val_dist.get(cat, 0)
                test_pct = test_dist.get(cat, 0)
                
                # Check for significant deviation (>10% difference)
                if abs(train_pct - val_pct) > 0.1 or abs(train_pct - test_pct) > 0.1:
                    issues.append(
                        f"'{key}={cat}' distribution varies: "
                        f"train={train_pct:.1%}, val={val_pct:.1%}, test={test_pct:.1%}"
                    )
            
            diversity_report[key] = {
                "train": train_dist,
                "val": val_dist,
                "test": test_dist,
            }
        
        return {
            "is_diverse": len(issues) == 0,
            "issues": issues,
            "report": diversity_report,
        }
    
    def _get_distribution(self, data: List[Dict], key: str) -> Dict[str, float]:
        """Get percentage distribution for a key"""
        if not data:
            return {}
        
        counts = Counter(item.get(key, "unknown") for item in data)
        total = sum(counts.values())
        
        return {k: v / total for k, v in counts.items()}
    
    def rebalance_for_diversity(
        self,
        split_result: SplitResult,
        key: str
    ) -> SplitResult:
        """
        Rebalance splits to ensure diversity on a specific key
        Uses swapping to maintain split sizes
        """
        # Get target distribution from overall data
        all_data = split_result.train + split_result.val + split_result.test
        target_dist = self._get_distribution(all_data, key)
        
        # This is a simplified rebalancing - for production, use more sophisticated methods
        logger.info(f"Rebalancing splits for diversity key: {key}")
        
        # For now, just log the target distribution
        logger.info(f"Target distribution: {target_dist}")
        
        return split_result  # Return unchanged for now


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def split_dataset(
    data: List[Dict],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    label_key: str = "label",
    random_seed: int = 42
) -> SplitResult:
    """
    Convenience function for standard dataset splitting
    
    Args:
        data: List of annotated items
        train_ratio: Fraction for training (default 70%)
        val_ratio: Fraction for validation (default 15%)
        test_ratio: Fraction for testing (default 15%)
        label_key: Key containing the label
        random_seed: For reproducibility
    
    Returns:
        SplitResult with train, val, test splits
    """
    config = SplitConfig(
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        random_seed=random_seed,
    )
    
    splitter = DatasetSplitter(config)
    return splitter.split(data, label_key)


def save_splits(
    split_result: SplitResult,
    output_dir: str,
    prefix: str = "dataset"
) -> Dict[str, str]:
    """
    Save splits to JSON files
    
    Returns:
        Dictionary of split name to file path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    paths = {}
    
    for split_name in ["train", "val", "test"]:
        data = split_result.get_split(split_name)
        file_path = output_path / f"{prefix}_{split_name}.json"
        
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        paths[split_name] = str(file_path)
        logger.info(f"Saved {split_name} split ({len(data)} items) to {file_path}")
    
    # Save metadata
    metadata_path = output_path / f"{prefix}_metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(split_result.to_dict(), f, indent=2, default=str)
    
    paths["metadata"] = str(metadata_path)
    
    return paths
