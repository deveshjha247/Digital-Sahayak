"""
Job Recommender AI Module
Ranks jobs/schemes based on user profile (education, age, state, preferences)

Architecture (LambdaMART + Two-Tower):
1. Feature Extraction: Categorical features + text embeddings
2. Two-Tower Retrieval: Embed users and jobs separately for fast candidate generation
3. LambdaMART Re-ranker: Gradient-boosted ranking for fine-grained scoring
4. Rule-based fallback: Works without ML models for cold-start

Language Support:
- Primary: English
- Secondary: Hindi
- All reasons/messages in both languages

Dependencies (optional for ML mode):
- lightgbm (for LambdaMART)
- sentence-transformers (for embeddings)
"""

import os
import json
import pickle
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from difflib import SequenceMatcher

logger = logging.getLogger(__name__)

# Import language helper
try:
    from .language_helper import get_language_helper, EDUCATION_BILINGUAL, CATEGORY_BILINGUAL, STATE_BILINGUAL
    lang_helper = get_language_helper()
except ImportError:
    lang_helper = None
    EDUCATION_BILINGUAL = {}
    CATEGORY_BILINGUAL = {}
    STATE_BILINGUAL = {}


class JobRecommender:
    """
    Recommendation engine for jobs and government schemes
    
    Scoring approach:
    1. Rule-based: Education match, age range, location
    2. Heuristic: Category preference, salary expectation
    3. Learning: User interaction history (clicks, applies, ignores)
    4. Confidence scoring with Hindi/English explanations
    """
    
    # Category mapping for normalization
    EDUCATION_HIERARCHY = {
        "10th Pass": 1,
        "12th Pass": 2,
        "Diploma": 3,
        "Graduate": 4,
        "Post-Graduate": 5,
        "Doctorate": 6,
        "Any": 0,  # Matches all
    }
    
    # Category keywords for auto-detection
    CATEGORY_KEYWORDS = {
        "Railway": ["railway", "rrb", "tc", "group d"],
        "SSC": ["ssc", "staff selection", "clerk", "constable"],
        "UPSC": ["upsc", "ias", "ips", "civil service"],
        "Bank": ["bank", "banking", "po", "clerk"],
        "PSC": ["psc", "state service", "assistant", "examination"],
        "IT": ["software", "developer", "engineer", "programmer"],
        "Teaching": ["teacher", "lecturer", "professor", "education"],
        "Government": ["government", "ministry", "department"],
    }
    
    def __init__(self):
        self.rule_weights = {
            "education": 0.25,
            "age": 0.20,
            "location": 0.20,
            "category": 0.20,
            "salary": 0.15,
        }
    
    def get_recommendations(
        self,
        user_profile: Dict,
        jobs: List[Dict],
        top_k: int = 10,
        include_reasoning: bool = True
    ) -> List[Dict]:
        """
        Get ranked job recommendations for a user
        
        Args:
            user_profile: {
                "education": "Graduate",
                "age": 25,
                "state": "Bihar",
                "preferred_categories": ["Railway", "SSC"],
                "salary_expectation": 30000,
                "interaction_history": {...}  # Optional
            }
            jobs: List of job documents
            top_k: Return top K recommendations
            include_reasoning: Include Hindi/English explanations
        
        Returns:
            List of recommendations with scores and reasons
        """
        if not jobs:
            return []
        
        recommendations = []
        
        for job in jobs:
            try:
                score_breakdown = {}
                
                # 1. Rule-based matching
                score_breakdown["education"] = self._score_education(
                    user_profile.get("education"),
                    job.get("education_required")
                )
                
                score_breakdown["age"] = self._score_age(
                    user_profile.get("age"),
                    job.get("min_age"),
                    job.get("max_age")
                )
                
                score_breakdown["location"] = self._score_location(
                    user_profile.get("state"),
                    job.get("location")
                )
                
                score_breakdown["category"] = self._score_category(
                    user_profile.get("preferred_categories", []),
                    job.get("category", "General")
                )
                
                score_breakdown["salary"] = self._score_salary(
                    user_profile.get("salary_expectation"),
                    job.get("salary")
                )
                
                # 3. Learning-based adjustment
                learning_multiplier = self._get_learning_multiplier(
                    user_profile,
                    job
                )
                
                # Calculate weighted score
                total_score = sum(
                    score_breakdown[key] * self.rule_weights[key]
                    for key in score_breakdown
                ) * learning_multiplier
                
                # Confidence level
                confidence = self._calculate_confidence(score_breakdown)
                
                # Reasoning
                reasons = {}
                if include_reasoning:
                    reasons = self._generate_reasoning(
                        score_breakdown,
                        user_profile,
                        job
                    )
                
                recommendations.append({
                    "job_id": job.get("id"),
                    "job_title": job.get("title"),
                    "company": job.get("company"),
                    "score": round(total_score, 3),
                    "confidence": confidence,
                    "score_breakdown": score_breakdown,
                    "reasons": reasons,
                    "learning_multiplier": round(learning_multiplier, 2),
                })
            
            except Exception as e:
                logger.error(f"Error scoring job {job.get('id')}: {str(e)}")
                continue
        
        # Sort by score descending
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        
        return recommendations[:top_k]
    
    def _score_education(self, user_edu: str, job_edu: str) -> float:
        """Score education match (0-1)"""
        if not user_edu or not job_edu:
            return 0.5  # Neutral if not specified
        
        if job_edu == "Any":
            return 1.0  # Matches any education
        
        user_level = self.EDUCATION_HIERARCHY.get(user_edu, 0)
        job_level = self.EDUCATION_HIERARCHY.get(job_edu, 0)
        
        if user_level == 0:  # Unknown user education
            return 0.5
        
        if user_level >= job_level:
            return 1.0  # User meets or exceeds requirement
        else:
            # Partial score based on gap
            gap = job_level - user_level
            return max(0, 1.0 - (gap * 0.2))
    
    def _score_age(self, user_age: int, min_age: int, max_age: int) -> float:
        """Score age match (0-1)"""
        if not user_age or not min_age or not max_age:
            return 0.5
        
        if min_age <= user_age <= max_age:
            # Calculate how centered the user is
            center = (min_age + max_age) / 2
            range_width = max_age - min_age
            distance_from_center = abs(user_age - center)
            return max(0.5, 1.0 - (distance_from_center / range_width))
        else:
            # Outside range
            if user_age < min_age:
                gap = min_age - user_age
            else:
                gap = user_age - max_age
            return max(0, 0.5 - (gap * 0.05))
    
    def _score_location(self, user_state: str, job_location: str) -> float:
        """Score location match (0-1)"""
        if not user_state or not job_location:
            return 0.5
        
        # Normalize strings
        user_state_norm = user_state.lower().strip()
        location_norm = str(job_location).lower().strip()
        
        # Exact match
        if user_state_norm in location_norm or location_norm in user_state_norm:
            return 1.0
        
        # Fuzzy match
        similarity = SequenceMatcher(None, user_state_norm, location_norm).ratio()
        if similarity > 0.8:
            return similarity
        
        # Partial match (region-based)
        if any(part in location_norm for part in user_state_norm.split()):
            return 0.7
        
        # Pan-India or remote
        if "india" in location_norm or "national" in location_norm or "remote" in location_norm:
            return 0.6
        
        return 0.2  # Location mismatch
    
    def _score_category(self, user_categories: List[str], job_category: str) -> float:
        """Score category preference match (0-1)"""
        if not job_category or not user_categories:
            return 0.5
        
        if job_category in user_categories:
            return 1.0  # Exact match with preference
        
        # Check if job category is related to user preferences
        job_cat_lower = job_category.lower()
        for user_cat in user_categories:
            if user_cat.lower() in job_cat_lower or job_cat_lower in user_cat.lower():
                return 0.8  # Partial match
        
        return 0.3  # Not in preferences
    
    def _score_salary(self, user_expectation: Optional[int], job_salary: str) -> float:
        """Score salary expectation match (0-1)"""
        if not user_expectation or not job_salary:
            return 0.5
        
        # Try to parse job salary
        salary_text = str(job_salary).lower()
        
        if "not specified" in salary_text or "as per" in salary_text:
            return 0.5
        
        try:
            # Extract numbers from salary range
            import re
            numbers = re.findall(r'\d+', salary_text)
            if numbers:
                job_min = int(numbers[0]) * 1000 if int(numbers[0]) < 1000 else int(numbers[0])
                
                if job_min >= user_expectation * 0.8:
                    return min(1.0, 1.0 + (job_min - user_expectation) / user_expectation)
                else:
                    gap_ratio = (user_expectation - job_min) / user_expectation
                    return max(0.2, 1.0 - gap_ratio)
        except:
            pass
        
        return 0.5
    
    def _get_learning_multiplier(self, user_profile: Dict, job: Dict) -> float:
        """
        Adjust score based on user interaction history
        Users who apply more to similar jobs should see those jobs ranked higher
        """
        multiplier = 1.0
        
        # If user has interaction history
        history = user_profile.get("interaction_history", {})
        if not history:
            return multiplier
        
        # Category boost
        job_category = job.get("category", "")
        category_applies = history.get("applied_categories", {}).get(job_category, 0)
        if category_applies > 0:
            multiplier *= (1.0 + min(0.3, category_applies * 0.1))  # Max +30%
        
        # Company boost
        company = job.get("company", "")
        company_applies = history.get("applied_companies", {}).get(company, 0)
        if company_applies > 0:
            multiplier *= (1.0 + min(0.2, company_applies * 0.05))  # Max +20%
        
        # Negative boost for ignored jobs
        ignored_categories = history.get("ignored_categories", {}).get(job_category, 0)
        if ignored_categories > 0:
            multiplier *= (1.0 - min(0.3, ignored_categories * 0.1))  # Max -30%
        
        return max(0.5, min(1.5, multiplier))  # Clamp between 0.5 and 1.5
    
    def _calculate_confidence(self, score_breakdown: Dict) -> str:
        """Determine confidence level based on score distribution"""
        scores = list(score_breakdown.values())
        avg_score = np.mean(scores)
        std_score = np.std(scores)
        
        if avg_score > 0.75 and std_score < 0.15:
            return "high"
        elif avg_score > 0.5 and std_score < 0.3:
            return "medium"
        else:
            return "low"
    
    def _generate_reasoning(
        self,
        score_breakdown: Dict,
        user_profile: Dict,
        job: Dict
    ) -> Dict[str, str]:
        """
        Generate bilingual reasoning for the recommendation
        Primary: English, Secondary: Hindi
        """
        reasons = {
            "en": [],
            "hi": [],
            "english": [],  # Keep for backward compatibility
            "hindi": []     # Keep for backward compatibility
        }
        
        # Education reason
        edu_score = score_breakdown.get("education", 0)
        if edu_score == 1.0:
            reasons["en"].append("Your education qualifies for this position")
            reasons["hi"].append("आपकी शिक्षा इस पद के लिए योग्य है")
        elif edu_score >= 0.8:
            reasons["en"].append("Your education is suitable for this job")
            reasons["hi"].append("आपकी शिक्षा इस नौकरी के लिए उपयुक्त है")
        elif edu_score < 0.5:
            reasons["en"].append("Higher education may be required")
            reasons["hi"].append("उच्च शिक्षा आवश्यक हो सकती है")
        
        # Age reason
        age_score = score_breakdown.get("age", 0)
        if age_score >= 0.9:
            reasons["en"].append("Your age is within the eligible range")
            reasons["hi"].append("आपकी आयु पात्रता सीमा में है")
        elif age_score >= 0.7:
            reasons["en"].append("You are close to the age requirement")
            reasons["hi"].append("आप आयु मानदंड के करीब हैं")
        elif age_score < 0.5:
            reasons["en"].append("Age limit may be an issue")
            reasons["hi"].append("आयु सीमा में समस्या हो सकती है")
        
        # Location reason
        location_score = score_breakdown.get("location", 0)
        if location_score == 1.0:
            reasons["en"].append("This job is available in your state")
            reasons["hi"].append("यह नौकरी आपके राज्य में उपलब्ध है")
        elif location_score >= 0.6:
            reasons["en"].append("This is an All India level job")
            reasons["hi"].append("यह अखिल भारतीय स्तर की नौकरी है")
        
        # Category reason
        category_score = score_breakdown.get("category", 0)
        if category_score == 1.0:
            reasons["en"].append("Matches your preferred job category")
            reasons["hi"].append("आपकी पसंदीदा श्रेणी से मेल खाता है")
        elif category_score >= 0.7:
            reasons["en"].append("Related to your interests")
            reasons["hi"].append("आपकी रुचि से संबंधित है")
        
        # Salary reason
        salary_score = score_breakdown.get("salary", 0)
        if salary_score >= 0.9:
            reasons["en"].append("Salary meets your expectations")
            reasons["hi"].append("वेतन आपकी अपेक्षाओं के अनुरूप है")
        
        # Default if no reasons
        if not reasons["en"]:
            reasons["en"].append("May be suitable for your profile")
            reasons["hi"].append("आपकी प्रोफ़ाइल के लिए उपयुक्त हो सकता है")
        
        # Backward compatibility
        reasons["english"] = reasons["en"]
        reasons["hindi"] = reasons["hi"]
        
        # Combined format
        reasons["en_text"] = " | ".join(reasons["en"])
        reasons["hi_text"] = " | ".join(reasons["hi"])
        reasons["bilingual"] = f"{reasons['en_text']}\n{reasons['hi_text']}"
        
        return reasons
    
    def explain_score(self, recommendation: Dict) -> Dict:
        """
        Provide detailed explanation of a single recommendation
        """
        return {
            "job": recommendation["job_title"],
            "score": recommendation["score"],
            "confidence": recommendation["confidence"],
            "breakdown": recommendation["score_breakdown"],
            "reasons": recommendation["reasons"],
            "details": {
                "education_match": f"{recommendation['score_breakdown']['education']:.2f}/1.0",
                "age_match": f"{recommendation['score_breakdown']['age']:.2f}/1.0",
                "location_match": f"{recommendation['score_breakdown']['location']:.2f}/1.0",
                "category_match": f"{recommendation['score_breakdown']['category']:.2f}/1.0",
                "salary_match": f"{recommendation['score_breakdown']['salary']:.2f}/1.0",
                "learning_boost": f"{recommendation['learning_multiplier']:.2f}x",
            }
        }


# ==============================================================================
# Advanced ML Components (LambdaMART + Two-Tower)
# ==============================================================================

@dataclass
class UserProfileAdvanced:
    """Extended user profile for ML recommendations"""
    user_id: str
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None
    state: Optional[str] = None
    district: Optional[str] = None
    education: Optional[str] = None
    income: Optional[float] = None
    category: Optional[str] = None  # SC/ST/OBC/General
    occupation: Optional[str] = None
    skills: List[str] = field(default_factory=list)
    interests: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=lambda: ["Hindi"])
    interaction_history: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id, "name": self.name, "age": self.age,
            "gender": self.gender, "state": self.state, "district": self.district,
            "education": self.education, "income": self.income, "category": self.category,
            "occupation": self.occupation, "skills": self.skills, "interests": self.interests,
        }


class FeatureExtractor:
    """
    Extract features from user profiles and job postings
    Combines categorical, numerical, and text embedding features
    """
    
    EDUCATION_LEVELS = {
        "below_10th": 1, "10th": 2, "10th pass": 2, "12th": 3, "12th pass": 3,
        "graduate": 4, "post_graduate": 5, "post-graduate": 5, "doctorate": 6,
        "diploma": 3.5, "iti": 2.5, "any": 0
    }
    
    STATES = [
        "Andhra Pradesh", "Bihar", "Chhattisgarh", "Delhi", "Gujarat",
        "Haryana", "Jharkhand", "Karnataka", "Kerala", "Madhya Pradesh",
        "Maharashtra", "Odisha", "Punjab", "Rajasthan", "Tamil Nadu",
        "Telangana", "Uttar Pradesh", "West Bengal"
    ]
    
    CATEGORIES = ["General", "OBC", "SC", "ST", "EWS"]
    
    def __init__(self, embedding_model: Optional[Any] = None):
        self.embedding_model = embedding_model
        self._embedding_cache: Dict[str, np.ndarray] = {}
        
    def _get_text_embedding(self, text: str, dim: int = 384) -> np.ndarray:
        """Get text embedding with caching"""
        if not text:
            return np.zeros(dim)
        cache_key = hash(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        if self.embedding_model:
            try:
                embedding = self.embedding_model.encode(text)
                self._embedding_cache[cache_key] = embedding
                return embedding
            except Exception as e:
                logger.warning(f"Embedding failed: {e}")
        # Fallback: character n-gram hashing
        features = np.zeros(dim)
        text_lower = text.lower()
        for i in range(len(text_lower) - 2):
            ngram = text_lower[i:i+3]
            idx = hash(ngram) % dim
            features[idx] += 1
        norm = np.linalg.norm(features)
        return features / norm if norm > 0 else features
    
    def _encode_education(self, education: Optional[str]) -> float:
        if not education:
            return 0.0
        return self.EDUCATION_LEVELS.get(education.lower().replace(" ", "_").replace("-", "_"), 0.0)
    
    def _encode_state(self, state: Optional[str]) -> np.ndarray:
        encoding = np.zeros(len(self.STATES))
        if state and state in self.STATES:
            encoding[self.STATES.index(state)] = 1.0
        return encoding
    
    def _encode_category(self, category: Optional[str]) -> np.ndarray:
        encoding = np.zeros(len(self.CATEGORIES))
        if category and category in self.CATEGORIES:
            encoding[self.CATEGORIES.index(category)] = 1.0
        return encoding
    
    def extract_user_features(self, user: Dict) -> np.ndarray:
        """Extract feature vector from user profile dict"""
        features = []
        features.append(user.get("age", 30) / 100.0)
        features.append(min((user.get("income") or 500000) / 1000000.0, 1.0))
        features.append(self._encode_education(user.get("education")) / 6.0)
        features.extend(self._encode_state(user.get("state")))
        features.extend(self._encode_category(user.get("category")))
        gender_map = {"male": 1.0, "female": 0.0, "other": 0.5}
        features.append(gender_map.get((user.get("gender") or "").lower(), 0.5))
        skills_text = " ".join(user.get("skills", []) + user.get("interests", []))
        skills_embedding = self._get_text_embedding(skills_text)
        features.extend(skills_embedding[:64])  # Truncate for size
        return np.array(features, dtype=np.float32)
    
    def extract_job_features(self, job: Dict) -> np.ndarray:
        """Extract feature vector from job/scheme posting"""
        features = []
        features.append(1.0 if job.get("type") == "job" else 0.0)
        features.append((job.get("min_age") or 18) / 100.0)
        features.append((job.get("max_age") or 65) / 100.0)
        features.append(self._encode_education(job.get("education_required")) / 6.0)
        days_left = 365
        if job.get("deadline"):
            try:
                deadline = datetime.fromisoformat(str(job["deadline"]).replace("Z", "+00:00"))
                days_left = max(0, (deadline - datetime.now()).days)
            except:
                pass
        features.append(min(days_left / 365.0, 1.0))
        features.extend(self._encode_state(job.get("location")))
        features.extend(self._encode_category(job.get("category")))
        text = f"{job.get('title', '')} {job.get('description', '')} {' '.join(job.get('tags', []))}"
        text_embedding = self._get_text_embedding(text)
        features.extend(text_embedding[:64])
        return np.array(features, dtype=np.float32)
    
    def extract_pair_features(self, user: Dict, job: Dict) -> np.ndarray:
        """Extract features for a user-job pair including interaction features"""
        user_features = self.extract_user_features(user)
        job_features = self.extract_job_features(job)
        
        # Interaction features
        interaction = []
        user_age = user.get("age", 30)
        age_match = 1.0
        if job.get("min_age") and user_age < job["min_age"]:
            age_match = 0.0
        elif job.get("max_age") and user_age > job["max_age"]:
            age_match = 0.0
        interaction.append(age_match)
        
        state_match = 1.0 if not job.get("location") or job.get("location") == user.get("state") else 0.5
        interaction.append(state_match)
        
        user_edu = self._encode_education(user.get("education"))
        job_edu = self._encode_education(job.get("education_required"))
        edu_match = 1.0 if user_edu >= job_edu else max(0, 1 - (job_edu - user_edu) / 3)
        interaction.append(edu_match)
        
        # Content similarity
        user_text = " ".join(user.get("skills", []) + user.get("interests", []))
        job_text = f"{job.get('title', '')} {job.get('description', '')}"
        user_emb = self._get_text_embedding(user_text)
        job_emb = self._get_text_embedding(job_text)
        similarity = np.dot(user_emb, job_emb) / (np.linalg.norm(user_emb) * np.linalg.norm(job_emb) + 1e-8)
        interaction.append(float(similarity))
        
        return np.concatenate([user_features, job_features, np.array(interaction, dtype=np.float32)])


class TwoTowerRetriever:
    """
    Two-Tower Neural Retrieval Model
    Embeds users and jobs separately for fast candidate generation
    """
    
    def __init__(self, embedding_dim: int = 64, model_path: Optional[str] = None):
        self.embedding_dim = embedding_dim
        self.model_path = model_path
        self.job_embeddings: Dict[str, np.ndarray] = {}
        self._load_model()
    
    def _load_model(self):
        if self.model_path and os.path.exists(self.model_path):
            try:
                with open(self.model_path, "rb") as f:
                    data = pickle.load(f)
                    self.job_embeddings = data.get("job_embeddings", {})
                logger.info("Loaded two-tower model")
            except Exception as e:
                logger.warning(f"Could not load two-tower model: {e}")
    
    def embed(self, features: np.ndarray) -> np.ndarray:
        """Project features to embedding space"""
        np.random.seed(42)
        proj = np.random.randn(len(features), self.embedding_dim) * 0.1
        return np.tanh(features @ proj)
    
    def index_jobs(self, jobs: List[Tuple[str, np.ndarray]]):
        """Index job embeddings for fast retrieval"""
        for job_id, features in jobs:
            self.job_embeddings[job_id] = self.embed(features)
        logger.info(f"Indexed {len(jobs)} jobs for retrieval")
    
    def retrieve_candidates(self, user_embedding: np.ndarray, top_k: int = 100) -> List[Tuple[str, float]]:
        """Retrieve top-k candidate jobs by similarity"""
        if not self.job_embeddings:
            return []
        similarities = []
        for job_id, job_emb in self.job_embeddings.items():
            sim = np.dot(user_embedding, job_emb) / (
                np.linalg.norm(user_embedding) * np.linalg.norm(job_emb) + 1e-8
            )
            similarities.append((job_id, float(sim)))
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


class LambdaMARTRanker:
    """
    LambdaMART Ranking Model using LightGBM
    Optimizes NDCG directly for learning-to-rank
    """
    
    def __init__(self, model_path: Optional[str] = None, n_estimators: int = 100):
        self.model_path = model_path
        self.model = None
        self.n_estimators = n_estimators
        self._load_model()
    
    def _load_model(self):
        if self.model_path and os.path.exists(self.model_path):
            try:
                import lightgbm as lgb
                self.model = lgb.Booster(model_file=self.model_path)
                logger.info("Loaded LambdaMART model")
            except ImportError:
                logger.warning("LightGBM not installed, using fallback ranking")
            except Exception as e:
                logger.warning(f"Could not load LambdaMART model: {e}")
    
    def train(self, features: np.ndarray, labels: np.ndarray, groups: np.ndarray):
        """Train LambdaMART model"""
        try:
            import lightgbm as lgb
            train_data = lgb.Dataset(features, label=labels, group=groups)
            params = {
                "objective": "lambdarank", "metric": "ndcg",
                "boosting_type": "gbdt", "num_leaves": 31,
                "learning_rate": 0.1, "verbose": -1,
            }
            self.model = lgb.train(params, train_data, num_boost_round=self.n_estimators)
            logger.info("Trained LambdaMART model")
        except ImportError:
            logger.warning("LightGBM not installed, using fallback ranking")
    
    def predict(self, features: np.ndarray) -> np.ndarray:
        """Predict relevance scores"""
        if self.model is not None:
            try:
                return self.model.predict(features)
            except Exception as e:
                logger.warning(f"Prediction failed: {e}")
        # Fallback: use interaction features (last 4 values)
        return features[:, -4:].mean(axis=1) if len(features.shape) > 1 else features[-4:].mean()
    
    def save(self, path: str):
        if self.model is not None:
            try:
                self.model.save_model(path)
            except Exception as e:
                logger.error(f"Could not save model: {e}")


class AdvancedJobRecommender:
    """
    Advanced Job/Yojana Recommendation System
    Combines Two-Tower retrieval with LambdaMART ranking
    Falls back to rule-based if ML models unavailable
    """
    
    def __init__(
        self,
        models_dir: Optional[str] = None,
        embedding_model_name: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    ):
        self.models_dir = Path(models_dir) if models_dir else None
        self.embedding_model = self._load_embedding_model(embedding_model_name)
        self.feature_extractor = FeatureExtractor(self.embedding_model)
        
        retriever_path = str(self.models_dir / "two_tower.pkl") if self.models_dir else None
        self.retriever = TwoTowerRetriever(model_path=retriever_path)
        
        ranker_path = str(self.models_dir / "lambdamart.txt") if self.models_dir else None
        self.ranker = LambdaMARTRanker(model_path=ranker_path)
        
        self.jobs_cache: Dict[str, Dict] = {}
        self.job_features_cache: Dict[str, np.ndarray] = {}
        self.rule_based = JobRecommender()  # Fallback
    
    def _load_embedding_model(self, model_name: str):
        try:
            from sentence_transformers import SentenceTransformer
            return SentenceTransformer(model_name)
        except ImportError:
            logger.warning("sentence-transformers not installed, using fallback embeddings")
            return None
        except Exception as e:
            logger.warning(f"Could not load embedding model: {e}")
            return None
    
    def index_jobs(self, jobs: List[Dict]):
        """Index jobs for fast retrieval"""
        job_features_list = []
        for job in jobs:
            job_id = job.get("id", job.get("_id", str(hash(job.get("title", "")))))
            features = self.feature_extractor.extract_job_features(job)
            self.jobs_cache[job_id] = job
            self.job_features_cache[job_id] = features
            job_features_list.append((job_id, features))
        self.retriever.index_jobs(job_features_list)
    
    def get_recommendations(
        self,
        user_profile: Dict,
        jobs: List[Dict],
        top_k: int = 10,
        use_ml: bool = True
    ) -> List[Dict]:
        """
        Get ranked recommendations combining ML and rule-based approaches
        
        Args:
            user_profile: User profile dictionary
            jobs: List of job/scheme postings
            top_k: Number of recommendations to return
            use_ml: Whether to use ML ranking (falls back to rules if unavailable)
        """
        if not use_ml or self.ranker.model is None:
            # Fall back to rule-based recommendations
            return self.rule_based.get_recommendations(user_profile, jobs, top_k)
        
        # Index jobs if not already cached
        if not self.jobs_cache:
            self.index_jobs(jobs)
        
        recommendations = []
        for job in jobs:
            job_id = job.get("id", job.get("_id", str(hash(job.get("title", "")))))
            
            # Get pair features
            pair_features = self.feature_extractor.extract_pair_features(user_profile, job)
            
            # Get ML score
            ml_score = float(self.ranker.predict(pair_features.reshape(1, -1))[0])
            
            # Get rule-based score for reasoning
            rule_rec = self.rule_based.get_recommendations(user_profile, [job], 1)
            rule_score = rule_rec[0]["score"] if rule_rec else 0.5
            reasons = rule_rec[0]["reasons"] if rule_rec else {"en": [], "hi": []}
            
            # Combine scores (70% ML, 30% rule-based for interpretability)
            combined_score = 0.7 * ml_score + 0.3 * rule_score
            
            recommendations.append({
                "job_id": job_id,
                "job_title": job.get("title"),
                "company": job.get("company"),
                "score": round(combined_score, 3),
                "ml_score": round(ml_score, 3),
                "rule_score": round(rule_score, 3),
                "confidence": "high" if combined_score > 0.7 else "medium" if combined_score > 0.4 else "low",
                "reasons": reasons,
            })
        
        recommendations.sort(key=lambda x: x["score"], reverse=True)
        return recommendations[:top_k]
    
    def train(self, users: List[Dict], jobs: List[Dict], interactions: List[Dict]):
        """Train the ML models from interaction data"""
        features_list, labels_list, groups_list = [], [], []
        
        # Group interactions by user
        user_interactions = {}
        for interaction in interactions:
            user_id = interaction["user_id"]
            if user_id not in user_interactions:
                user_interactions[user_id] = []
            user_interactions[user_id].append(interaction)
        
        user_lookup = {u.get("user_id", u.get("id")): u for u in users}
        job_lookup = {j.get("id", j.get("_id")): j for j in jobs}
        
        relevance_map = {"apply": 4.0, "save": 3.0, "click": 2.0, "view": 1.0, "skip": 0.0}
        
        for user_id, user_ints in user_interactions.items():
            if user_id not in user_lookup:
                continue
            user = user_lookup[user_id]
            group_size = 0
            
            for interaction in user_ints:
                posting_id = interaction["posting_id"]
                if posting_id not in job_lookup:
                    continue
                job = job_lookup[posting_id]
                pair_features = self.feature_extractor.extract_pair_features(user, job)
                relevance = relevance_map.get(interaction.get("interaction_type"), 1.0)
                features_list.append(pair_features)
                labels_list.append(relevance)
                group_size += 1
            
            if group_size > 0:
                groups_list.append(group_size)
        
        if features_list:
            self.ranker.train(
                np.array(features_list),
                np.array(labels_list),
                np.array(groups_list)
            )
            self.index_jobs(jobs)
    
    def save(self, output_dir: str):
        """Save all models"""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        self.ranker.save(str(output_path / "lambdamart.txt"))
        with open(output_path / "two_tower.pkl", "wb") as f:
            pickle.dump({"job_embeddings": self.retriever.job_embeddings}, f)


# Convenience function for API integration
def get_recommendations(
    user_profile: Dict,
    job_list: List[Dict],
    top_k: int = 10,
    use_advanced: bool = False,
    models_dir: Optional[str] = None
) -> List[Dict]:
    """
    Get job/yojana recommendations for a user
    
    Args:
        user_profile: User profile dictionary
        job_list: List of job posting dictionaries
        top_k: Number of recommendations
        use_advanced: Use ML-based recommendations (requires trained models)
        models_dir: Directory with trained models
        
    Returns:
        List of recommendation dictionaries with scores and explanations
    """
    if use_advanced:
        recommender = AdvancedJobRecommender(models_dir=models_dir)
        return recommender.get_recommendations(user_profile, job_list, top_k)
    else:
        recommender = JobRecommender()
        return recommender.get_recommendations(user_profile, job_list, top_k)
