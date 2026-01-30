"""
Data Balancer
Handles class imbalance using oversampling, SMOTE, and weighted sampling
"""

import logging
import random
import json
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class DataBalancer:
    """
    Balances dataset across classes (states, categories, etc.)
    Implements multiple balancing strategies:
    1. Random oversampling
    2. SMOTE-like augmentation
    3. Weighted sampling
    4. Undersampling
    """
    
    def __init__(self, target_ratio: float = 0.7):
        """
        Args:
            target_ratio: Minimum ratio between smallest and largest class (0-1)
        """
        self.target_ratio = target_ratio
    
    def analyze_distribution(
        self,
        data: List[Dict],
        key: str
    ) -> Dict[str, Any]:
        """
        Analyze class distribution for a specific key
        
        Args:
            data: List of data items
            key: Field to analyze (e.g., "category", "state")
        
        Returns:
            Distribution statistics
        """
        values = [item.get(key, "unknown") for item in data]
        counter = Counter(values)
        
        total = len(values)
        stats = {
            "total_samples": total,
            "num_classes": len(counter),
            "distribution": dict(counter),
            "percentages": {k: round(v / total * 100, 2) for k, v in counter.items()},
            "min_class": min(counter.items(), key=lambda x: x[1]) if counter else ("unknown", 0),
            "max_class": max(counter.items(), key=lambda x: x[1]) if counter else ("unknown", 0),
            "imbalance_ratio": 0,
        }
        
        if stats["max_class"][1] > 0:
            stats["imbalance_ratio"] = round(
                stats["min_class"][1] / stats["max_class"][1], 3
            )
        
        return stats
    
    def oversample(
        self,
        data: List[Dict],
        key: str,
        target_count: int = None
    ) -> List[Dict]:
        """
        Oversample minority classes by duplicating samples
        
        Args:
            data: Original data
            key: Field to balance on
            target_count: Target count for each class (None = max class count)
        
        Returns:
            Balanced data list
        """
        distribution = self.analyze_distribution(data, key)
        
        if target_count is None:
            target_count = distribution["max_class"][1]
        
        # Group by class
        by_class: Dict[str, List[Dict]] = {}
        for item in data:
            cls = item.get(key, "unknown")
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(item)
        
        # Oversample each class
        balanced_data = []
        for cls, items in by_class.items():
            current_count = len(items)
            
            if current_count >= target_count:
                # Undersample if needed
                balanced_data.extend(random.sample(items, target_count))
            else:
                # Add all original items
                balanced_data.extend(items)
                
                # Add duplicates to reach target
                needed = target_count - current_count
                duplicates = random.choices(items, k=needed)
                
                # Mark as oversampled
                for dup in duplicates:
                    new_item = dup.copy()
                    new_item["_oversampled"] = True
                    balanced_data.append(new_item)
        
        random.shuffle(balanced_data)
        logger.info(f"Oversampled {len(data)} -> {len(balanced_data)} items")
        return balanced_data
    
    def smote_like_augment(
        self,
        data: List[Dict],
        key: str,
        text_fields: List[str] = None,
        target_ratio: float = None
    ) -> List[Dict]:
        """
        SMOTE-like augmentation for text data
        Creates synthetic samples by interpolating between existing ones
        
        Args:
            data: Original data
            key: Field to balance on
            text_fields: Fields to augment
            target_ratio: Target balance ratio
        
        Returns:
            Augmented data
        """
        if text_fields is None:
            text_fields = ["title", "description"]
        
        if target_ratio is None:
            target_ratio = self.target_ratio
        
        distribution = self.analyze_distribution(data, key)
        target_count = int(distribution["max_class"][1] * target_ratio)
        
        # Group by class
        by_class: Dict[str, List[Dict]] = {}
        for item in data:
            cls = item.get(key, "unknown")
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(item)
        
        # Augment minority classes
        augmented_data = list(data)
        
        for cls, items in by_class.items():
            if len(items) >= target_count:
                continue
            
            needed = target_count - len(items)
            
            for _ in range(needed):
                # Pick two random samples from same class
                if len(items) >= 2:
                    sample1, sample2 = random.sample(items, 2)
                else:
                    sample1 = sample2 = items[0]
                
                # Create synthetic sample
                synthetic = self._create_synthetic_sample(
                    sample1, sample2, text_fields
                )
                synthetic["_synthetic"] = True
                synthetic["_source_class"] = cls
                augmented_data.append(synthetic)
        
        random.shuffle(augmented_data)
        logger.info(f"SMOTE augmented {len(data)} -> {len(augmented_data)} items")
        return augmented_data
    
    def _create_synthetic_sample(
        self,
        sample1: Dict,
        sample2: Dict,
        text_fields: List[str]
    ) -> Dict:
        """Create synthetic sample by combining two samples"""
        synthetic = sample1.copy()
        
        for field in text_fields:
            text1 = sample1.get(field, "")
            text2 = sample2.get(field, "")
            
            if text1 and text2:
                # Simple interpolation: random sentence mixing
                sentences1 = self._split_sentences(text1)
                sentences2 = self._split_sentences(text2)
                
                # Mix sentences
                combined = []
                max_len = max(len(sentences1), len(sentences2))
                
                for i in range(max_len):
                    if random.random() > 0.5 and i < len(sentences1):
                        combined.append(sentences1[i])
                    elif i < len(sentences2):
                        combined.append(sentences2[i])
                    elif i < len(sentences1):
                        combined.append(sentences1[i])
                
                synthetic[field] = " ".join(combined)
        
        return synthetic
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        import re
        # Handle both English and Hindi sentence endings
        sentences = re.split(r'[।.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def weighted_sample(
        self,
        data: List[Dict],
        key: str,
        sample_size: int,
        inverse_weight: bool = True
    ) -> List[Dict]:
        """
        Sample data with class weights
        
        Args:
            data: Original data
            key: Field to weight by
            sample_size: Number of samples to return
            inverse_weight: If True, minority classes get higher weight
        
        Returns:
            Weighted sampled data
        """
        distribution = self.analyze_distribution(data, key)
        
        # Calculate weights
        weights = []
        for item in data:
            cls = item.get(key, "unknown")
            cls_count = distribution["distribution"].get(cls, 1)
            
            if inverse_weight:
                # Minority classes get higher weight
                weight = 1.0 / cls_count
            else:
                weight = cls_count / distribution["total_samples"]
            
            weights.append(weight)
        
        # Normalize weights
        total_weight = sum(weights)
        weights = [w / total_weight for w in weights]
        
        # Sample
        indices = list(range(len(data)))
        sampled_indices = random.choices(indices, weights=weights, k=sample_size)
        
        sampled_data = [data[i] for i in sampled_indices]
        logger.info(f"Weighted sampled {sample_size} items from {len(data)}")
        return sampled_data
    
    def stratified_split(
        self,
        data: List[Dict],
        key: str,
        train_ratio: float = 0.8,
        val_ratio: float = 0.1,
        test_ratio: float = 0.1
    ) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """
        Stratified train/val/test split maintaining class distribution
        
        Returns:
            (train_data, val_data, test_data)
        """
        assert abs(train_ratio + val_ratio + test_ratio - 1.0) < 0.001
        
        # Group by class
        by_class: Dict[str, List[Dict]] = {}
        for item in data:
            cls = item.get(key, "unknown")
            if cls not in by_class:
                by_class[cls] = []
            by_class[cls].append(item)
        
        train_data, val_data, test_data = [], [], []
        
        for cls, items in by_class.items():
            random.shuffle(items)
            n = len(items)
            
            train_end = int(n * train_ratio)
            val_end = train_end + int(n * val_ratio)
            
            train_data.extend(items[:train_end])
            val_data.extend(items[train_end:val_end])
            test_data.extend(items[val_end:])
        
        # Shuffle each split
        random.shuffle(train_data)
        random.shuffle(val_data)
        random.shuffle(test_data)
        
        logger.info(f"Stratified split: train={len(train_data)}, val={len(val_data)}, test={len(test_data)}")
        return train_data, val_data, test_data
    
    def balance_multiple_keys(
        self,
        data: List[Dict],
        keys: List[str],
        strategy: str = "oversample"
    ) -> List[Dict]:
        """
        Balance data across multiple keys sequentially
        
        Args:
            data: Original data
            keys: List of keys to balance (e.g., ["category", "state"])
            strategy: "oversample", "smote", or "weighted"
        
        Returns:
            Balanced data
        """
        balanced = data
        
        for key in keys:
            if strategy == "oversample":
                balanced = self.oversample(balanced, key)
            elif strategy == "smote":
                balanced = self.smote_like_augment(balanced, key)
            elif strategy == "weighted":
                balanced = self.weighted_sample(balanced, key, len(balanced))
        
        return balanced
    
    def generate_balance_report(
        self,
        data: List[Dict],
        keys: List[str]
    ) -> Dict:
        """
        Generate comprehensive balance report
        """
        report = {
            "total_samples": len(data),
            "distributions": {},
            "recommendations": [],
        }
        
        for key in keys:
            dist = self.analyze_distribution(data, key)
            report["distributions"][key] = dist
            
            if dist["imbalance_ratio"] < self.target_ratio:
                report["recommendations"].append({
                    "key": key,
                    "current_ratio": dist["imbalance_ratio"],
                    "target_ratio": self.target_ratio,
                    "action": f"Balance '{key}' using oversampling or SMOTE",
                    "min_class": dist["min_class"],
                    "max_class": dist["max_class"],
                })
        
        return report
