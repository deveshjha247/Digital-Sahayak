"""
Hybrid Rule-Based + ML AI System with Log Learning
Combines deterministic rules with machine learning for robust matching
"""

from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import re

class HybridMatchingEngine:
    """
    Hybrid matching system combining:
    1. Rule-based field mapping
    2. Heuristic scoring
    3. ML-based improvements
    4. Log-based learning
    """
    
    def __init__(self, db):
        self.db = db
        self.logs_collection = db['matching_logs']
        self.rules_collection = db['matching_rules']
        self.heuristics_collection = db['matching_heuristics']
        
        # Field mapping rules
        self.field_mappings = {
            'education': {
                '10th': ['10th', 'matric', 'matriculation', 'secondary'],
                '12th': ['12th', 'intermediate', '+2', 'senior secondary'],
                'Graduate': ['graduate', 'graduation', 'bachelor', 'b.a', 'b.sc', 'b.com', 'b.tech'],
                'Post Graduate': ['post graduate', 'pg', 'masters', 'm.a', 'm.sc', 'm.com', 'm.tech']
            },
            'category': {
                'Railway': ['railway', 'rrb', 'rail', 'indian railway'],
                'SSC': ['ssc', 'staff selection', 'combined'],
                'UPSC': ['upsc', 'civil service', 'ias', 'ips'],
                'Bank': ['bank', 'ibps', 'sbi', 'banking'],
                'Police': ['police', 'constable', 'si', 'inspector'],
                'State Govt': ['state', 'psc', 'bpsc', 'uppsc']
            },
            'state': {
                'Bihar': ['bihar', 'br', 'patna'],
                'UP': ['up', 'uttar pradesh', 'lucknow'],
                'Jharkhand': ['jharkhand', 'jh', 'ranchi'],
                'Delhi': ['delhi', 'dl', 'new delhi'],
                'All India': ['all india', 'national', 'central']
            }
        }
        
        # Heuristic weights
        self.heuristic_weights = {
            'education_match': 30,
            'age_match': 20,
            'state_match': 15,
            'category_match': 15,
            'experience_match': 10,
            'skills_match': 10
        }
        
        # Learning parameters
        self.learning_rate = 0.1
        self.confidence_threshold = 0.75
    
    async def match_job_to_user(self, job: Dict, user_profile: Dict,
                                use_ml: bool = True) -> Dict:
        """
        Hybrid matching: Rules + ML + Logs
        
        Args:
            job: Job data
            user_profile: User profile
            use_ml: Whether to use ML enhancement
            
        Returns:
            Match result with score and reasoning
        """
        # Step 1: Rule-based matching
        rule_score, rule_breakdown = await self._rule_based_match(job, user_profile)
        
        # Step 2: Heuristic scoring
        heuristic_score, heuristic_breakdown = await self._heuristic_match(job, user_profile)
        
        # Step 3: Learn from past logs
        log_adjustment = await self._learn_from_logs(job, user_profile)
        
        # Step 4: Combine scores
        base_score = (rule_score * 0.4) + (heuristic_score * 0.4) + (log_adjustment * 0.2)
        
        # Step 5: ML enhancement if enabled
        if use_ml:
            ml_adjustment = await self._ml_enhance(job, user_profile, base_score)
            final_score = min(base_score + ml_adjustment, 100)
        else:
            final_score = base_score
        
        # Step 6: Log this matching for future learning
        await self._log_match(job, user_profile, final_score, {
            'rule_score': rule_score,
            'heuristic_score': heuristic_score,
            'log_adjustment': log_adjustment,
            'ml_adjustment': ml_adjustment if use_ml else 0
        })
        
        return {
            'match_score': round(final_score, 2),
            'breakdown': {
                'rule_based': round(rule_score, 2),
                'heuristic': round(heuristic_score, 2),
                'log_learning': round(log_adjustment, 2),
                'ml_enhancement': round(ml_adjustment if use_ml else 0, 2)
            },
            'reasoning': await self._generate_reasoning(
                job, user_profile, final_score, rule_breakdown, heuristic_breakdown
            ),
            'confidence': self._calculate_confidence(final_score, rule_score, heuristic_score)
        }
    
    async def _rule_based_match(self, job: Dict, user: Dict) -> Tuple[float, Dict]:
        """
        Strict rule-based matching using field mappings
        """
        score = 0
        breakdown = {}
        
        # Education matching
        job_edu = job.get('education', '').lower()
        user_edu = user.get('education', '').lower()
        
        if job_edu and user_edu:
            if self._field_matches('education', job_edu, user_edu):
                score += 30
                breakdown['education'] = 'Exact match'
            elif self._field_fuzzy_match('education', job_edu, user_edu):
                score += 20
                breakdown['education'] = 'Partial match'
            else:
                breakdown['education'] = 'No match'
        
        # Age matching
        user_age = user.get('age')
        min_age = job.get('min_age', 18)
        max_age = job.get('max_age', 40)
        
        if user_age:
            if min_age <= user_age <= max_age:
                score += 25
                breakdown['age'] = f'Within range ({min_age}-{max_age})'
            else:
                age_diff = min(abs(user_age - min_age), abs(user_age - max_age))
                if age_diff <= 2:
                    score += 15
                    breakdown['age'] = 'Close to range'
                else:
                    breakdown['age'] = 'Outside range'
        
        # State matching
        job_state = job.get('state', '').lower()
        user_state = user.get('state', '').lower()
        
        if job_state == 'all india' or job_state == '':
            score += 20
            breakdown['state'] = 'All India job'
        elif self._field_matches('state', job_state, user_state):
            score += 25
            breakdown['state'] = 'State match'
        else:
            breakdown['state'] = 'Different state'
        
        return score, breakdown
    
    async def _heuristic_match(self, job: Dict, user: Dict) -> Tuple[float, Dict]:
        """
        Heuristic-based scoring using learned patterns
        """
        score = 0
        breakdown = {}
        
        # Fetch learned heuristics
        heuristics = await self.heuristics_collection.find_one(
            {'user_profile_type': self._classify_user_profile(user)}
        )
        
        if heuristics:
            # Apply learned weights
            weights = heuristics.get('weights', self.heuristic_weights)
        else:
            weights = self.heuristic_weights
        
        # Category preference
        user_prefs = user.get('preferred_categories', [])
        job_category = job.get('category', '')
        
        if job_category in user_prefs:
            score += weights.get('category_match', 15)
            breakdown['category'] = 'User prefers this category'
        
        # Title keywords matching
        job_title = job.get('title', '').lower()
        if user_prefs:
            for pref in user_prefs:
                if pref.lower() in job_title:
                    score += 10
                    breakdown['title_match'] = f'Contains "{pref}"'
                    break
        
        # Eligibility text analysis
        eligibility = job.get('eligibility', '').lower()
        user_edu = user.get('education', '').lower()
        
        if user_edu in eligibility:
            score += 15
            breakdown['eligibility'] = 'Education mentioned in eligibility'
        
        return score, breakdown
    
    async def _learn_from_logs(self, job: Dict, user: Dict) -> float:
        """
        Learn from past matching logs to improve scoring
        """
        # Find similar past matches
        similar_matches = await self.logs_collection.find({
            'user_education': user.get('education'),
            'job_category': job.get('category'),
            'outcome': {'$exists': True}  # Only completed applications
        }).limit(10).to_list(10)
        
        if not similar_matches:
            return 0
        
        # Calculate adjustment based on success rate
        successful = [m for m in similar_matches if m.get('outcome') == 'success']
        success_rate = len(successful) / len(similar_matches)
        
        # Positive adjustment for high success patterns
        if success_rate > 0.7:
            return 15 * success_rate
        elif success_rate > 0.5:
            return 10 * success_rate
        else:
            return -5  # Penalize low success patterns
    
    async def _ml_enhance(self, job: Dict, user: Dict, base_score: float) -> float:
        """
        ML-based enhancement using pattern recognition
        """
        # Fetch patterns from ML model (simplified here)
        patterns = await self.db['ml_patterns'].find_one({
            'education': user.get('education'),
            'state': user.get('state')
        })
        
        if not patterns:
            return 0
        
        # Apply pattern-based adjustment
        confidence = patterns.get('confidence', 0.5)
        avg_success_score = patterns.get('avg_success_score', base_score)
        
        # Adjust towards successful pattern
        adjustment = (avg_success_score - base_score) * confidence * self.learning_rate
        
        return adjustment
    
    async def _log_match(self, job: Dict, user: Dict, score: float, details: Dict):
        """
        Log matching for future learning
        """
        log_entry = {
            'timestamp': datetime.now(),
            'user_id': user.get('id'),
            'user_education': user.get('education'),
            'user_age': user.get('age'),
            'user_state': user.get('state'),
            'job_id': job.get('id'),
            'job_category': job.get('category'),
            'job_state': job.get('state'),
            'match_score': score,
            'details': details,
            'outcome': None  # To be updated when user applies
        }
        
        await self.logs_collection.insert_one(log_entry)
    
    async def update_match_outcome(self, job_id: str, user_id: str, outcome: str):
        """
        Update log with actual outcome (applied/not applied)
        This enables learning from user behavior
        """
        await self.logs_collection.update_one(
            {'job_id': job_id, 'user_id': user_id},
            {'$set': {'outcome': outcome, 'outcome_timestamp': datetime.now()}}
        )
        
        # Trigger pattern learning
        await self._update_patterns_from_logs()
    
    async def _update_patterns_from_logs(self):
        """
        Analyze logs to update ML patterns and heuristics
        """
        # Group logs by user profile type
        pipeline = [
            {'$match': {'outcome': {'$exists': True}}},
            {'$group': {
                '_id': {
                    'education': '$user_education',
                    'state': '$user_state'
                },
                'avg_score': {'$avg': '$match_score'},
                'success_count': {
                    '$sum': {'$cond': [{'$eq': ['$outcome', 'applied']}, 1, 0]}
                },
                'total_count': {'$sum': 1}
            }}
        ]
        
        patterns = await self.logs_collection.aggregate(pipeline).to_list(100)
        
        # Update ML patterns collection
        for pattern in patterns:
            await self.db['ml_patterns'].update_one(
                {
                    'education': pattern['_id']['education'],
                    'state': pattern['_id']['state']
                },
                {
                    '$set': {
                        'avg_success_score': pattern['avg_score'],
                        'confidence': pattern['success_count'] / pattern['total_count'],
                        'updated_at': datetime.now()
                    }
                },
                upsert=True
            )
    
    def _field_matches(self, field_type: str, value1: str, value2: str) -> bool:
        """Check if two values match using field mappings"""
        mappings = self.field_mappings.get(field_type, {})
        
        for canonical, variants in mappings.items():
            if (value1 in variants or value1 == canonical.lower()) and \
               (value2 in variants or value2 == canonical.lower()):
                return True
        
        return value1 == value2
    
    def _field_fuzzy_match(self, field_type: str, value1: str, value2: str) -> bool:
        """Fuzzy matching for partial matches"""
        mappings = self.field_mappings.get(field_type, {})
        
        for canonical, variants in mappings.items():
            v1_match = any(v in value1 for v in variants)
            v2_match = any(v in value2 for v in variants)
            if v1_match and v2_match:
                return True
        
        return False
    
    def _classify_user_profile(self, user: Dict) -> str:
        """Classify user into profile type for heuristic lookup"""
        education = user.get('education', '')
        age = user.get('age', 0)
        
        if '10th' in education or '12th' in education:
            if age < 25:
                return 'young_school_educated'
            else:
                return 'mature_school_educated'
        elif 'graduate' in education.lower():
            if age < 27:
                return 'young_graduate'
            else:
                return 'mature_graduate'
        else:
            return 'general'
    
    async def _generate_reasoning(self, job: Dict, user: Dict, score: float,
                                  rule_breakdown: Dict, heuristic_breakdown: Dict) -> str:
        """
        Generate human-readable reasoning in Hindi
        """
        reasons = []
        
        # Education reasoning
        if 'education' in rule_breakdown:
            if rule_breakdown['education'] == 'Exact match':
                reasons.append(f"✓ आपकी शिक्षा ({user.get('education')}) इस job के लिए उपयुक्त है")
            elif rule_breakdown['education'] == 'No match':
                reasons.append(f"✗ शिक्षा योग्यता मेल नहीं खाती")
        
        # Age reasoning
        if 'age' in rule_breakdown:
            if 'Within range' in rule_breakdown['age']:
                reasons.append(f"✓ आपकी उम्र ({user.get('age')}) सीमा में है")
            else:
                reasons.append(f"✗ उम्र सीमा से बाहर है")
        
        # State reasoning
        if 'state' in rule_breakdown:
            if rule_breakdown['state'] == 'State match':
                reasons.append(f"✓ आपके राज्य ({user.get('state')}) में job है")
            elif rule_breakdown['state'] == 'All India job':
                reasons.append(f"✓ यह All India job है")
        
        # Category reasoning
        if 'category' in heuristic_breakdown:
            reasons.append(f"✓ {heuristic_breakdown['category']}")
        
        if score >= 75:
            reasons.insert(0, "🎯 बहुत अच्छा match!")
        elif score >= 50:
            reasons.insert(0, "👍 अच्छा match")
        else:
            reasons.insert(0, "⚠️ कम match")
        
        return " | ".join(reasons)
    
    def _calculate_confidence(self, final_score: float, rule_score: float,
                            heuristic_score: float) -> float:
        """
        Calculate confidence in the match
        Higher when rules and heuristics agree
        """
        agreement = 1 - abs(rule_score - heuristic_score) / 100
        score_confidence = final_score / 100
        
        return (agreement * 0.4 + score_confidence * 0.6)
