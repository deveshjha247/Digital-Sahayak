"""
Data Pipeline
Orchestrates end-to-end data collection, processing, and balancing
"""

import asyncio
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any

from .data_config import DataConfig, SOURCES, CATEGORIES, STATES
from .collector import DataCollector
from .metadata import MetadataManager
from .balancer import DataBalancer
from .preprocessor import DataPreprocessor
from .synthetic import generate_training_dataset

logger = logging.getLogger(__name__)


class DataPipeline:
    """
    End-to-end data pipeline for training data preparation
    
    Steps:
    1. Collect data from multiple sources
    2. Validate and deduplicate
    3. Store metadata for RAG
    4. Balance across classes
    5. Generate synthetic data if needed
    6. Export for training
    """
    
    def __init__(
        self,
        output_dir: str = None,
        min_samples_per_class: int = 100,
        balance_keys: List[str] = None
    ):
        self.output_dir = Path(output_dir) if output_dir else Path(__file__).parent / "processed"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.min_samples_per_class = min_samples_per_class
        self.balance_keys = balance_keys or ["category", "state"]
        
        # Components
        self.collector = DataCollector()
        self.preprocessor = DataPreprocessor(required_fields=["title"])
        self.metadata_manager = MetadataManager()
        self.balancer = DataBalancer(target_ratio=0.5)
        
        # Pipeline state
        self.collected_data: List[Dict] = []
        self.processed_data: List[Dict] = []
        self.synthetic_data: List[Dict] = []
        self.final_data: List[Dict] = []
        
        # Statistics
        self.stats = {
            "collected": 0,
            "preprocessed": 0,
            "validated": 0,
            "deduplicated": 0,
            "synthetic_added": 0,
            "final": 0,
        }
    
    async def run(
        self,
        collect: bool = True,
        balance: bool = True,
        generate_synthetic: bool = True,
        export: bool = True
    ) -> Dict:
        """
        Run complete data pipeline
        
        Args:
            collect: Whether to collect from sources
            balance: Whether to balance data
            generate_synthetic: Whether to generate synthetic data
            export: Whether to export final dataset
        
        Returns:
            Pipeline statistics and output paths
        """
        logger.info("Starting data pipeline...")
        start_time = datetime.now()
        
        # Step 1: Collect data
        if collect:
            await self._collect_step()
        
        # Step 2: Preprocess and clean
        self._preprocess_step()
        
        # Step 3: Validate and deduplicate (now handled by preprocessor)
        self._validate_step()
        
        # Step 3: Store metadata
        self._metadata_step()
        
        # Step 4: Balance data
        if balance:
            self._balance_step()
        
        # Step 5: Generate synthetic data
        if generate_synthetic:
            self._synthetic_step()
        
        # Step 6: Export
        output_paths = {}
        if export:
            output_paths = self._export_step()
        
        # Summary
        duration = (datetime.now() - start_time).total_seconds()
        
        result = {
            "status": "success",
            "duration_seconds": duration,
            "statistics": self.stats,
            "output_paths": output_paths,
            "balance_report": self.balancer.generate_balance_report(
                self.final_data, self.balance_keys
            ),
        }
        
        logger.info(f"Pipeline completed in {duration:.1f}s")
        return result
    
    async def _collect_step(self):
        """Collect data from all sources"""
        logger.info("Step 1: Collecting data...")
        
        # Collect all data
        all_data = await self.collector.collect_all()
        
        self.collected_data = all_data
        self.stats["collected"] = len(all_data)
        
        logger.info(f"Collected {len(all_data)} items from sources")
    
    def _preprocess_step(self):
        """Preprocess and clean data"""
        logger.info("Step 2: Preprocessing data...")
        
        # Run full preprocessing pipeline
        cleaned_data = self.preprocessor.process(self.collected_data)
        preprocessing_stats = self.preprocessor.get_stats()
        
        self.collected_data = cleaned_data
        self.stats["preprocessed"] = len(cleaned_data)
        self.stats["preprocessing_details"] = preprocessing_stats
        
        logger.info(f"Preprocessed: {len(cleaned_data)} items")
        logger.info(f"  - Duplicates removed: {preprocessing_stats['duplicates_removed']}")
        logger.info(f"  - Fields normalized: {preprocessing_stats['fields_normalized']}")
        logger.info(f"  - Dates standardized: {preprocessing_stats['dates_standardized']}")
        logger.info(f"  - Text cleaned: {preprocessing_stats['text_cleaned']}")
    
    def _validate_step(self):
        """Additional validation after preprocessing"""
        logger.info("Step 3: Final validation...")
        
        validated = []
        
        for item in self.collected_data:
            # Skip items without description (title already checked by preprocessor)
            if not item.get("description"):
                continue
            
            # Skip items marked as having too many missing fields
            if item.get("_too_many_missing"):
                continue
            
            validated.append(item)
        
        self.processed_data = validated
        self.stats["validated"] = len(validated)
        
        logger.info(f"Validated: {len(validated)} items")
    
    def _metadata_step(self):
        """Store metadata for RAG"""
        logger.info("Step 4: Storing metadata...")
        
        for item in self.processed_data:
            self.metadata_manager.add_metadata(item)
        
        # Get diversity report
        report = self.metadata_manager.get_diversity_report()
        logger.info(f"Metadata stored. States: {len(report.get('by_state', {}))}, "
                   f"Categories: {len(report.get('by_category', {}))}")
    
    def _balance_step(self):
        """Balance data across classes"""
        logger.info("Step 4: Balancing data...")
        
        # Analyze current distribution
        initial_report = self.balancer.generate_balance_report(
            self.processed_data, self.balance_keys
        )
        
        # Apply SMOTE-like augmentation for text data
        balanced_data = self.processed_data.copy()
        
        for key in self.balance_keys:
            dist = self.balancer.analyze_distribution(balanced_data, key)
            
            if dist["imbalance_ratio"] < 0.5:
                logger.info(f"Balancing by '{key}' (ratio: {dist['imbalance_ratio']})")
                balanced_data = self.balancer.smote_like_augment(
                    balanced_data, key,
                    text_fields=["title", "description"],
                    target_ratio=0.5
                )
        
        self.processed_data = balanced_data
        logger.info(f"After balancing: {len(balanced_data)} items")
    
    def _synthetic_step(self):
        """Generate synthetic data for underrepresented classes"""
        logger.info("Step 5: Generating synthetic data...")
        
        # Check if synthetic data is needed
        current_count = len(self.processed_data)
        
        # Calculate needed synthetic data per category
        category_counts = {}
        for item in self.processed_data:
            cat = item.get("category", "unknown")
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        # Generate synthetic data for categories below threshold
        from .synthetic import SyntheticJobGenerator
        
        generator = SyntheticJobGenerator(language="bilingual")
        synthetic_data = []
        
        for category in CATEGORIES.get("jobs", {}).keys():
            current = category_counts.get(category, 0)
            
            if current < self.min_samples_per_class:
                needed = self.min_samples_per_class - current
                logger.info(f"Generating {needed} synthetic items for category: {category}")
                
                for _ in range(needed):
                    synthetic_item = generator.generate_job(category=category)
                    synthetic_data.append(synthetic_item)
        
        self.synthetic_data = synthetic_data
        self.stats["synthetic_added"] = len(synthetic_data)
        
        # Combine with processed data
        self.final_data = self.processed_data + synthetic_data
        self.stats["final"] = len(self.final_data)
        
        logger.info(f"Added {len(synthetic_data)} synthetic items. Total: {len(self.final_data)}")
    
    def _export_step(self) -> Dict[str, str]:
        """Export final dataset"""
        logger.info("Step 6: Exporting data...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        paths = {}
        
        # Export full dataset
        full_path = self.output_dir / f"training_data_{timestamp}.jsonl"
        with open(full_path, 'w', encoding='utf-8') as f:
            for item in self.final_data:
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
        paths["full_dataset"] = str(full_path)
        
        # Stratified split
        train, val, test = self.balancer.stratified_split(
            self.final_data, "category",
            train_ratio=0.8, val_ratio=0.1, test_ratio=0.1
        )
        
        # Export splits
        train_path = self.output_dir / f"train_{timestamp}.jsonl"
        val_path = self.output_dir / f"val_{timestamp}.jsonl"
        test_path = self.output_dir / f"test_{timestamp}.jsonl"
        
        for data, path in [(train, train_path), (val, val_path), (test, test_path)]:
            with open(path, 'w', encoding='utf-8') as f:
                for item in data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
        
        paths["train"] = str(train_path)
        paths["val"] = str(val_path)
        paths["test"] = str(test_path)
        
        # Export metadata
        metadata_path = self.output_dir / f"metadata_{timestamp}.json"
        metadata = self.metadata_manager.export_for_training()
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        paths["metadata"] = str(metadata_path)
        
        # Export statistics
        stats_path = self.output_dir / f"stats_{timestamp}.json"
        with open(stats_path, 'w', encoding='utf-8') as f:
            json.dump({
                "pipeline_stats": self.stats,
                "balance_report": self.balancer.generate_balance_report(
                    self.final_data, self.balance_keys
                ),
                "splits": {
                    "train": len(train),
                    "val": len(val),
                    "test": len(test),
                }
            }, f, ensure_ascii=False, indent=2)
        paths["statistics"] = str(stats_path)
        
        logger.info(f"Exported to: {self.output_dir}")
        return paths
    
    def load_existing_data(self, path: str) -> int:
        """Load existing collected data"""
        data_path = Path(path)
        
        if not data_path.exists():
            return 0
        
        loaded = []
        with open(data_path, 'r', encoding='utf-8') as f:
            for line in f:
                loaded.append(json.loads(line))
        
        self.collected_data = loaded
        self.stats["collected"] = len(loaded)
        
        logger.info(f"Loaded {len(loaded)} items from {path}")
        return len(loaded)


async def run_pipeline(
    output_dir: str = None,
    collect_new: bool = True,
    min_samples: int = 100
) -> Dict:
    """
    Convenience function to run complete data pipeline
    """
    pipeline = DataPipeline(
        output_dir=output_dir,
        min_samples_per_class=min_samples
    )
    
    return await pipeline.run(
        collect=collect_new,
        balance=True,
        generate_synthetic=True,
        export=True
    )
