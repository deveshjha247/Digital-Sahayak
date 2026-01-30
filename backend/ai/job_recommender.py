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
