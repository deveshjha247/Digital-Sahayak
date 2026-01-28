"""
Job Matching Data Collector
Collects job postings, user profiles, and interaction data for training ranking models
Labels: relevant/not_relevant based on clicks, applications, time spent

Best Practices Implemented:
- Deduplication to avoid redundant data
- Diversity tracking (state, category, education level)
- Metadata storage for RAG and validation
- Class balance analysis
- Train/val/test split support
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from collections import Counter

logger = logging.getLogger(__name__)

try:
    from .data_quality import (
        Deduplicator,
        ClassBalanceAnalyzer,
        DiversityAnalyzer,
        DatasetSplitter,
        FeedbackLoop,
    )
except ImportError:
    Deduplicator = None
    ClassBalanceAnalyzer = None
    DiversityAnalyzer = None
    DatasetSplitter = None
    FeedbackLoop = None


class JobMatchingCollector:
    """
    Collects and labels job matching training data
    
    Data Sources:
    - Job postings (title, qualification, category, state, salary, etc.)
    - User profiles (education, age, location, preferences)
    - User interactions (views, clicks, applications, time_spent)
    
    Labels:
    - Explicit: user applied = highly_relevant, user saved = relevant
    - Implicit: viewed > 30s = somewhat_relevant, skipped = not_relevant
    """
    
    LABEL_WEIGHTS = {
        "applied": 1.0,           # User applied = highly relevant
        "saved": 0.8,             # User saved/bookmarked
        "clicked": 0.6,           # User clicked to view details
        "viewed_long": 0.4,       # Viewed > 30 seconds
        "viewed_short": 0.2,      # Viewed < 30 seconds
        "skipped": 0.0,           # Shown but not interacted
        "rejected": -0.5,         # User explicitly marked not interested
    }
    
    def __init__(self, data_dir: str = "data/training/job_matching"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data files
        self.jobs_file = self.data_dir / "jobs.jsonl"
        self.users_file = self.data_dir / "users.jsonl"
        self.interactions_file = self.data_dir / "interactions.jsonl"
        self.labels_file = self.data_dir / "labeled_pairs.jsonl"
        self.metadata_file = self.data_dir / "collection_metadata.json"
        
        # Quality tools
        self.deduplicator = Deduplicator() if Deduplicator else None
        self.feedback_loop = FeedbackLoop(str(self.data_dir / "feedback")) if FeedbackLoop else None
        
        # Diversity tracking
        self.diversity_counters = {
            "states": Counter(),
            "categories": Counter(),
            "education_levels": Counter(),
            "age_groups": Counter(),
        }
        
        # Stats
        self.stats = {
            "jobs_collected": 0,
            "jobs_deduplicated": 0,
            "users_collected": 0,
            "interactions_collected": 0,
            "labeled_pairs": 0,
        }
    
    def collect_job(self, job: Dict[str, Any]) -> str:
        """
        Collect a job posting for training data
        
        Required fields:
        - title: Job title
        - description: Full description
        - qualification: Required education
        - category: Job category (Railway, Banking, etc.)
        - state: Location state
        - salary_min, salary_max: Salary range
        - age_min, age_max: Age requirements
        
        Returns: job_id or None if duplicate
        """
        # Deduplication check
        job_text = job.get("title", "") + job.get("description", "")[:500]
        if self.deduplicator and self.deduplicator.is_duplicate(job_text):
            self.stats["jobs_deduplicated"] += 1
            logger.debug(f"Duplicate job skipped: {job.get('title', '')[:50]}")
            return None
        
        job_id = self._generate_id(job.get("title", "") + job.get("source_url", ""))
        
        # Track diversity
        state = job.get("state", "unknown")
        category = job.get("category", "unknown")
        self.diversity_counters["states"][state] += 1
        self.diversity_counters["categories"][category] += 1
        
        job_record = {
            "job_id": job_id,
            "title": job.get("title", ""),
            "description": job.get("description", ""),
            "qualification": job.get("qualification", ""),
            "category": job.get("category", ""),
            "state": job.get("state", ""),
            "district": job.get("district", ""),
            "salary_min": job.get("salary_min", 0),
            "salary_max": job.get("salary_max", 0),
            "age_min": job.get("age_min", 18),
            "age_max": job.get("age_max", 65),
            "vacancies": job.get("vacancies", 0),
            "deadline": job.get("deadline", ""),
            "source_url": job.get("source_url", ""),
            "collected_at": datetime.now().isoformat(),
            
            # Metadata for RAG and validation
            "metadata": {
                "source": job.get("source", "scraper"),
                "publication_date": job.get("publication_date", ""),
                "department": job.get("department", ""),
                "organization": job.get("organization", ""),
                "language": job.get("language", "en"),
            },
            
            # Features for ML
            "features": self._extract_job_features(job),
        }
        
        self._append_jsonl(self.jobs_file, job_record)
        self.stats["jobs_collected"] += 1
        
        return job_id
    
    def collect_user_profile(self, user: Dict[str, Any]) -> str:
        """
        Collect anonymized user profile for training
        
        Required fields:
        - education: Highest qualification
        - age: User age
        - state: Location state
        - category_preferences: Preferred job categories
        """
        # Anonymize user ID
        user_id = self._generate_id(user.get("phone", "") + user.get("email", ""))
        
        user_record = {
            "user_id": user_id,
            "education": user.get("education", ""),
            "education_level": self._normalize_education(user.get("education", "")),
            "age": user.get("age", 0),
            "state": user.get("state", ""),
            "district": user.get("district", ""),
            "category_preferences": user.get("category_preferences", []),
            "experience_years": user.get("experience_years", 0),
            "gender": user.get("gender", ""),
            "caste_category": user.get("caste_category", ""),  # For reservation schemes
            "collected_at": datetime.now().isoformat(),
            
            # Features for ML
            "features": self._extract_user_features(user),
        }
        
        self._append_jsonl(self.users_file, user_record)
        self.stats["users_collected"] += 1
        
        return user_id
    
    def collect_interaction(
        self,
        user_id: str,
        job_id: str,
        interaction_type: str,
        metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Collect user-job interaction for implicit feedback
        
        interaction_type:
        - "view": User viewed job listing
        - "click": User clicked for details
        - "save": User saved/bookmarked
        - "apply": User started application
        - "complete_apply": User completed application
        - "reject": User marked not interested
        - "skip": Job shown but no interaction
        """
        interaction = {
            "user_id": user_id,
            "job_id": job_id,
            "interaction_type": interaction_type,
            "timestamp": datetime.now().isoformat(),
            "time_spent_seconds": metadata.get("time_spent_seconds", 0) if metadata else 0,
            "scroll_depth": metadata.get("scroll_depth", 0) if metadata else 0,
            "device": metadata.get("device", "unknown") if metadata else "unknown",
            "session_id": metadata.get("session_id", "") if metadata else "",
        }
        
        self._append_jsonl(self.interactions_file, interaction)
        self.stats["interactions_collected"] += 1
        
        return interaction
    
    def generate_labeled_pair(
        self,
        user_id: str,
        job_id: str,
        label: str,
        confidence: float = 1.0
    ) -> Dict:
        """
        Create a labeled (user, job) pair for supervised training
        
        label: "relevant" or "not_relevant"
        confidence: 0.0 to 1.0 (certainty of label)
        """
        labeled_pair = {
            "user_id": user_id,
            "job_id": job_id,
            "label": label,
            "label_score": self.LABEL_WEIGHTS.get(label, 0.5),
            "confidence": confidence,
            "created_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.labels_file, labeled_pair)
        self.stats["labeled_pairs"] += 1
        
        return labeled_pair
    
    def process_interactions_to_labels(self) -> int:
        """
        Convert collected interactions into labeled training pairs
        Uses implicit feedback signals to infer relevance
        """
        interactions = self._read_jsonl(self.interactions_file)
        
        # Group by (user, job)
        pair_interactions = {}
        for interaction in interactions:
            key = (interaction["user_id"], interaction["job_id"])
            if key not in pair_interactions:
                pair_interactions[key] = []
            pair_interactions[key].append(interaction)
        
        labels_created = 0
        
        for (user_id, job_id), interactions_list in pair_interactions.items():
            # Determine label from interactions
            label, confidence = self._infer_label(interactions_list)
            
            self.generate_labeled_pair(user_id, job_id, label, confidence)
            labels_created += 1
        
        return labels_created
    
    def _infer_label(self, interactions: List[Dict]) -> tuple:
        """Infer relevance label from interaction history"""
        interaction_types = [i["interaction_type"] for i in interactions]
        
        # Check for explicit signals
        if "complete_apply" in interaction_types or "apply" in interaction_types:
            return "applied", 1.0
        
        if "reject" in interaction_types:
            return "rejected", 0.9
        
        if "save" in interaction_types:
            return "saved", 0.85
        
        if "click" in interaction_types:
            # Check time spent
            total_time = sum(i.get("time_spent_seconds", 0) for i in interactions)
            if total_time > 30:
                return "viewed_long", 0.7
            else:
                return "clicked", 0.6
        
        if "view" in interaction_types:
            total_time = sum(i.get("time_spent_seconds", 0) for i in interactions)
            if total_time > 30:
                return "viewed_long", 0.5
            else:
                return "viewed_short", 0.4
        
        return "skipped", 0.3
    
    def _extract_job_features(self, job: Dict) -> Dict:
        """Extract ML features from job posting"""
        title = job.get("title", "").lower()
        desc = job.get("description", "").lower()
        
        return {
            "title_length": len(title.split()),
            "desc_length": len(desc.split()),
            "has_salary": bool(job.get("salary_min") or job.get("salary_max")),
            "has_age_limit": bool(job.get("age_min") or job.get("age_max")),
            "is_govt": any(kw in title + desc for kw in ["सरकारी", "government", "govt", "psc", "upsc"]),
            "is_railway": any(kw in title + desc for kw in ["railway", "रेलवे", "rrb"]),
            "is_banking": any(kw in title + desc for kw in ["bank", "बैंक", "ibps", "sbi"]),
            "is_ssc": any(kw in title + desc for kw in ["ssc", "staff selection"]),
            "is_defence": any(kw in title + desc for kw in ["army", "navy", "air force", "defence", "सेना"]),
        }
    
    def _extract_user_features(self, user: Dict) -> Dict:
        """Extract ML features from user profile"""
        return {
            "education_level": self._normalize_education(user.get("education", "")),
            "age_group": self._age_to_group(user.get("age", 0)),
            "has_experience": user.get("experience_years", 0) > 0,
            "num_preferences": len(user.get("category_preferences", [])),
        }
    
    def _normalize_education(self, education: str) -> int:
        """Convert education string to numeric level"""
        edu_lower = education.lower()
        
        if any(kw in edu_lower for kw in ["phd", "doctorate", "पीएचडी"]):
            return 8
        if any(kw in edu_lower for kw in ["m.tech", "mtech", "m.e", "me ", "एमटेक"]):
            return 7
        if any(kw in edu_lower for kw in ["mba", "m.sc", "msc", "m.a", "ma ", "m.com", "mcom", "masters", "pg", "post graduate", "एमबीए"]):
            return 6
        if any(kw in edu_lower for kw in ["b.tech", "btech", "b.e", "be ", "बीटेक"]):
            return 5
        if any(kw in edu_lower for kw in ["bba", "bca", "b.sc", "bsc", "b.a", "ba ", "b.com", "bcom", "bachelor", "graduate", "graduation", "स्नातक"]):
            return 4
        if any(kw in edu_lower for kw in ["12th", "12वीं", "intermediate", "hsc", "+2", "इंटरमीडिएट"]):
            return 3
        if any(kw in edu_lower for kw in ["10th", "10वीं", "matric", "ssc", "दसवीं"]):
            return 2
        if any(kw in edu_lower for kw in ["8th", "8वीं", "middle", "आठवीं"]):
            return 1
        
        return 0
    
    def _age_to_group(self, age: int) -> str:
        """Convert age to group for feature"""
        if age < 18:
            return "minor"
        if age <= 25:
            return "young"
        if age <= 35:
            return "mid"
        if age <= 45:
            return "senior"
        return "veteran"
    
    def _generate_id(self, text: str) -> str:
        """Generate unique ID from text"""
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _append_jsonl(self, filepath: Path, record: Dict):
        """Append record to JSONL file"""
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _read_jsonl(self, filepath: Path) -> List[Dict]:
        """Read all records from JSONL file"""
        if not filepath.exists():
            return []
        
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        return {
            **self.stats,
            "data_dir": str(self.data_dir),
            "files": {
                "jobs": str(self.jobs_file),
                "users": str(self.users_file),
                "interactions": str(self.interactions_file),
                "labels": str(self.labels_file),
            }
        }
    
    def get_diversity_report(self) -> Dict:
        """Get diversity analysis for collected data"""
        return {
            "state_distribution": dict(self.diversity_counters["states"].most_common(20)),
            "category_distribution": dict(self.diversity_counters["categories"].most_common(20)),
            "education_distribution": dict(self.diversity_counters["education_levels"].most_common()),
            "recommendations": self._diversity_recommendations(),
        }
    
    def _diversity_recommendations(self) -> List[str]:
        """Generate recommendations for improving diversity"""
        recs = []
        
        states = self.diversity_counters["states"]
        if len(states) < 10:
            recs.append(f"Low state diversity ({len(states)} states). Collect from more regions.")
        
        categories = self.diversity_counters["categories"]
        if categories:
            top_count = categories.most_common(1)[0][1]
            bottom_count = categories.most_common()[-1][1]
            if top_count > bottom_count * 5:
                recs.append("Category imbalance detected. Collect more from underrepresented categories.")
        
        return recs
    
    def get_class_balance(self) -> Dict:
        """Analyze label class balance"""
        labels = self._read_jsonl(self.labels_file)
        label_values = [l["label"] for l in labels]
        
        if ClassBalanceAnalyzer and label_values:
            analyzer = ClassBalanceAnalyzer(label_values)
            return analyzer.recommend_strategy()
        
        return {"distribution": Counter(label_values)}
    
    def split_dataset(
        self,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        stratify: bool = True
    ) -> Dict[str, str]:
        """
        Split dataset into train/val/test sets
        Returns paths to split files
        """
        labels = self._read_jsonl(self.labels_file)
        
        if not DatasetSplitter or not labels:
            return {"error": "No data or splitter unavailable"}
        
        if stratify:
            train, val, test = DatasetSplitter.stratified_split(
                labels, "label", train_ratio, val_ratio, test_ratio
            )
        else:
            train, val, test = DatasetSplitter.random_split(
                labels, train_ratio, val_ratio, test_ratio
            )
        
        # Save splits
        paths = {}
        for name, data in [("train", train), ("val", val), ("test", test)]:
            path = self.data_dir / f"{name}_labels.jsonl"
            with open(path, "w", encoding="utf-8") as f:
                for record in data:
                    f.write(json.dumps(record, ensure_ascii=False) + "\n")
            paths[name] = str(path)
        
        return {
            "paths": paths,
            "sizes": {"train": len(train), "val": len(val), "test": len(test)},
        }
    
    def log_operator_correction(
        self,
        user_id: str,
        job_id: str,
        original_label: str,
        corrected_label: str,
        operator_id: str
    ):
        """Log when an operator corrects a prediction"""
        if self.feedback_loop:
            self.feedback_loop.log_operator_correction(
                original_prediction=original_label,
                corrected_value=corrected_label,
                context={"user_id": user_id, "job_id": job_id},
                operator_id=operator_id
            )
    
    def export_training_data(self, output_file: str = None) -> str:
        """
        Export combined training dataset for ML model
        Format: (user_features, job_features, label)
        """
        if not output_file:
            output_file = str(self.data_dir / "training_dataset.jsonl")
        
        # Load all data
        jobs = {j["job_id"]: j for j in self._read_jsonl(self.jobs_file)}
        users = {u["user_id"]: u for u in self._read_jsonl(self.users_file)}
        labels = self._read_jsonl(self.labels_file)
        
        # Create training examples
        with open(output_file, "w", encoding="utf-8") as f:
            for label_record in labels:
                user_id = label_record["user_id"]
                job_id = label_record["job_id"]
                
                if user_id not in users or job_id not in jobs:
                    continue
                
                training_example = {
                    "user_features": users[user_id].get("features", {}),
                    "job_features": jobs[job_id].get("features", {}),
                    "user_profile": {
                        "education_level": users[user_id].get("education_level"),
                        "age": users[user_id].get("age"),
                        "state": users[user_id].get("state"),
                        "preferences": users[user_id].get("category_preferences", []),
                    },
                    "job_info": {
                        "qualification": jobs[job_id].get("qualification"),
                        "category": jobs[job_id].get("category"),
                        "state": jobs[job_id].get("state"),
                        "salary_min": jobs[job_id].get("salary_min"),
                        "salary_max": jobs[job_id].get("salary_max"),
                    },
                    "label": label_record["label"],
                    "label_score": label_record["label_score"],
                    "confidence": label_record["confidence"],
                }
                
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file
