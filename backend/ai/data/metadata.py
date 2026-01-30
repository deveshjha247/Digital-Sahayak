"""
Metadata Manager
Stores and manages metadata for all collected data
Supports retrieval-augmented generation (RAG) and validation
"""

import json
import hashlib
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class DataMetadata:
    """Metadata schema for collected data items"""
    
    # Identification
    id: str
    content_hash: str  # SHA256 of content for deduplication
    
    # Source information
    source: str  # e.g., "sarkari_result", "ncs_gov"
    source_type: str  # "scraper", "api", "synthetic", "manual"
    source_url: Optional[str] = None
    
    # Collection info
    collection_date: str = ""
    collection_method: str = ""  # "automated", "manual", "synthetic"
    
    # Geographic diversity
    state: str = "all_india"
    district: Optional[str] = None
    region: str = "all_india"  # north, south, east, west, northeast, central
    
    # Content classification
    content_type: str = ""  # "job", "scheme", "result", "admit_card", "syllabus"
    category: str = ""  # "railway", "ssc", "bank", etc.
    sub_category: Optional[str] = None
    
    # Language
    language: str = "en"  # "en", "hi", "hinglish", "bilingual"
    
    # Quality indicators
    verified: bool = False
    verification_date: Optional[str] = None
    quality_score: float = 0.0  # 0-1 score
    
    # Content characteristics
    title_length: int = 0
    description_length: int = 0
    has_salary_info: bool = False
    has_age_info: bool = False
    has_education_info: bool = False
    has_deadline: bool = False
    
    # For training
    used_in_training: bool = False
    training_split: Optional[str] = None  # "train", "validation", "test"
    
    # Additional metadata
    tags: List[str] = None
    extra: Dict[str, Any] = None
    
    def __post_init__(self):
        if not self.collection_date:
            self.collection_date = datetime.now().isoformat()
        if self.tags is None:
            self.tags = []
        if self.extra is None:
            self.extra = {}


class MetadataManager:
    """
    Manages metadata for all collected data
    Supports querying, filtering, and statistics
    """
    
    def __init__(self, storage_path: str = None):
        self.storage_path = Path(storage_path) if storage_path else Path(__file__).parent / "metadata"
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.index_file = self.storage_path / "index.json"
        self.index: Dict[str, Dict] = self._load_index()
    
    def _load_index(self) -> Dict:
        """Load metadata index from file"""
        if self.index_file.exists():
            try:
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading metadata index: {e}")
        return {"items": {}, "stats": {}, "last_updated": None}
    
    def _save_index(self):
        """Save metadata index to file"""
        self.index["last_updated"] = datetime.now().isoformat()
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving metadata index: {e}")
    
    @staticmethod
    def generate_id() -> str:
        """Generate unique ID for data item"""
        return str(uuid.uuid4())[:12]
    
    @staticmethod
    def compute_hash(content: str) -> str:
        """Compute SHA256 hash of content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]
    
    def add_metadata(self, content: str, metadata: DataMetadata) -> str:
        """Add metadata for a data item"""
        # Compute content hash for deduplication
        content_hash = self.compute_hash(content)
        
        # Check for duplicates
        if self._is_duplicate(content_hash):
            logger.info(f"Duplicate content detected: {content_hash}")
            return None
        
        # Generate ID if not provided
        if not metadata.id:
            metadata.id = self.generate_id()
        
        metadata.content_hash = content_hash
        
        # Store metadata
        self.index["items"][metadata.id] = asdict(metadata)
        self._save_index()
        
        return metadata.id
    
    def _is_duplicate(self, content_hash: str) -> bool:
        """Check if content already exists"""
        for item in self.index["items"].values():
            if item.get("content_hash") == content_hash:
                return True
        return False
    
    def get_metadata(self, item_id: str) -> Optional[Dict]:
        """Get metadata for a specific item"""
        return self.index["items"].get(item_id)
    
    def query(
        self,
        source: str = None,
        state: str = None,
        category: str = None,
        content_type: str = None,
        language: str = None,
        verified: bool = None,
        min_quality_score: float = None,
        limit: int = None
    ) -> List[Dict]:
        """
        Query metadata with filters
        Useful for selecting training data subsets
        """
        results = []
        
        for item_id, metadata in self.index["items"].items():
            # Apply filters
            if source and metadata.get("source") != source:
                continue
            if state and metadata.get("state") != state:
                continue
            if category and metadata.get("category") != category:
                continue
            if content_type and metadata.get("content_type") != content_type:
                continue
            if language and metadata.get("language") != language:
                continue
            if verified is not None and metadata.get("verified") != verified:
                continue
            if min_quality_score and metadata.get("quality_score", 0) < min_quality_score:
                continue
            
            results.append(metadata)
            
            if limit and len(results) >= limit:
                break
        
        return results
    
    def get_statistics(self) -> Dict:
        """
        Get statistics about collected data
        Useful for monitoring diversity and balance
        """
        stats = {
            "total_items": len(self.index["items"]),
            "by_source": {},
            "by_state": {},
            "by_category": {},
            "by_content_type": {},
            "by_language": {},
            "verified_count": 0,
            "quality_distribution": {"low": 0, "medium": 0, "high": 0},
            "collection_dates": {"oldest": None, "newest": None},
        }
        
        for metadata in self.index["items"].values():
            # By source
            source = metadata.get("source", "unknown")
            stats["by_source"][source] = stats["by_source"].get(source, 0) + 1
            
            # By state
            state = metadata.get("state", "unknown")
            stats["by_state"][state] = stats["by_state"].get(state, 0) + 1
            
            # By category
            category = metadata.get("category", "unknown")
            stats["by_category"][category] = stats["by_category"].get(category, 0) + 1
            
            # By content type
            content_type = metadata.get("content_type", "unknown")
            stats["by_content_type"][content_type] = stats["by_content_type"].get(content_type, 0) + 1
            
            # By language
            language = metadata.get("language", "unknown")
            stats["by_language"][language] = stats["by_language"].get(language, 0) + 1
            
            # Verified
            if metadata.get("verified"):
                stats["verified_count"] += 1
            
            # Quality distribution
            quality = metadata.get("quality_score", 0)
            if quality < 0.4:
                stats["quality_distribution"]["low"] += 1
            elif quality < 0.7:
                stats["quality_distribution"]["medium"] += 1
            else:
                stats["quality_distribution"]["high"] += 1
        
        return stats
    
    def get_diversity_report(self) -> Dict:
        """
        Generate diversity report for data collection
        Identifies under-represented categories/states
        """
        stats = self.get_statistics()
        
        report = {
            "total_items": stats["total_items"],
            "state_coverage": len(stats["by_state"]),
            "category_coverage": len(stats["by_category"]),
            "under_represented_states": [],
            "under_represented_categories": [],
            "class_balance_ratio": 0,
            "recommendations": [],
        }
        
        # Find under-represented states
        if stats["by_state"]:
            avg_state = sum(stats["by_state"].values()) / len(stats["by_state"])
            for state, count in stats["by_state"].items():
                if count < avg_state * 0.3:
                    report["under_represented_states"].append({
                        "state": state,
                        "count": count,
                        "target": int(avg_state)
                    })
        
        # Find under-represented categories
        if stats["by_category"]:
            avg_category = sum(stats["by_category"].values()) / len(stats["by_category"])
            for category, count in stats["by_category"].items():
                if count < avg_category * 0.3:
                    report["under_represented_categories"].append({
                        "category": category,
                        "count": count,
                        "target": int(avg_category)
                    })
        
        # Calculate class balance ratio
        if stats["by_category"]:
            min_count = min(stats["by_category"].values())
            max_count = max(stats["by_category"].values())
            report["class_balance_ratio"] = min_count / max_count if max_count > 0 else 0
        
        # Generate recommendations
        if report["under_represented_states"]:
            report["recommendations"].append(
                f"Collect more data from: {', '.join([s['state'] for s in report['under_represented_states'][:5]])}"
            )
        
        if report["under_represented_categories"]:
            report["recommendations"].append(
                f"Need more data for categories: {', '.join([c['category'] for c in report['under_represented_categories'][:5]])}"
            )
        
        if report["class_balance_ratio"] < 0.5:
            report["recommendations"].append(
                "Consider using SMOTE or oversampling to balance classes"
            )
        
        return report
    
    def mark_for_training(self, item_ids: List[str], split: str = "train"):
        """Mark items as used in training with specific split"""
        for item_id in item_ids:
            if item_id in self.index["items"]:
                self.index["items"][item_id]["used_in_training"] = True
                self.index["items"][item_id]["training_split"] = split
        self._save_index()
    
    def export_for_training(
        self,
        output_path: str,
        content_type: str = None,
        min_quality: float = 0.5,
        verified_only: bool = False
    ) -> int:
        """
        Export metadata for training data preparation
        Returns count of exported items
        """
        items = self.query(
            content_type=content_type,
            verified=verified_only if verified_only else None,
            min_quality_score=min_quality
        )
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(items, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(items)} items to {output_path}")
        return len(items)
