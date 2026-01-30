"""
Synthetic Data Generators
Generate synthetic data for training when real data is scarce or sensitive
"""

import random
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# SYNTHETIC DATA TEMPLATES (Bilingual)
# =============================================================================

# Job titles by category
JOB_TITLES = {
    "railway": {
        "en": [
            "Junior Engineer (Civil)",
            "Assistant Loco Pilot",
            "Station Master",
            "Group D Technician",
            "Railway Ticket Collector",
            "Signal Maintainer",
            "Track Maintainer Grade-IV",
            "Senior Section Engineer",
            "Chief Commercial Inspector",
            "Assistant Station Master",
        ],
        "hi": [
            "जूनियर इंजीनियर (सिविल)",
            "सहायक लोको पायलट",
            "स्टेशन मास्टर",
            "ग्रुप डी तकनीशियन",
            "रेलवे टिकट कलेक्टर",
            "सिग्नल मेंटेनर",
            "ट्रैक मेंटेनर ग्रेड-IV",
            "वरिष्ठ सेक्शन इंजीनियर",
            "मुख्य वाणिज्यिक निरीक्षक",
            "सहायक स्टेशन मास्टर",
        ],
    },
    "ssc": {
        "en": [
            "Lower Division Clerk",
            "Upper Division Clerk",
            "Data Entry Operator",
            "Junior Statistical Assistant",
            "Stenographer Grade C",
            "Stenographer Grade D",
            "Multi Tasking Staff",
            "Junior Hindi Translator",
            "Tax Assistant",
            "Postal Assistant",
        ],
        "hi": [
            "अवर श्रेणी लिपिक",
            "उच्च श्रेणी लिपिक",
            "डाटा एंट्री ऑपरेटर",
            "कनिष्ठ सांख्यिकीय सहायक",
            "आशुलिपिक ग्रेड सी",
            "आशुलिपिक ग्रेड डी",
            "मल्टी टास्किंग स्टाफ",
            "कनिष्ठ हिंदी अनुवादक",
            "कर सहायक",
            "डाक सहायक",
        ],
    },
    "bank": {
        "en": [
            "Probationary Officer",
            "Clerk",
            "Specialist Officer (IT)",
            "Specialist Officer (HR)",
            "Assistant Manager",
            "Manager",
            "Senior Manager",
            "Chief Manager",
            "Agricultural Field Officer",
            "Marketing Officer",
        ],
        "hi": [
            "परिवीक्षाधीन अधिकारी",
            "लिपिक",
            "विशेषज्ञ अधिकारी (आईटी)",
            "विशेषज्ञ अधिकारी (मानव संसाधन)",
            "सहायक प्रबंधक",
            "प्रबंधक",
            "वरिष्ठ प्रबंधक",
            "मुख्य प्रबंधक",
            "कृषि क्षेत्र अधिकारी",
            "विपणन अधिकारी",
        ],
    },
    "police": {
        "en": [
            "Constable",
            "Head Constable",
            "Sub Inspector",
            "Inspector",
            "Assistant Sub Inspector",
            "Deputy Superintendent of Police",
            "Superintendent of Police",
            "Wireless Operator",
            "Driver Constable",
            "Home Guard",
        ],
        "hi": [
            "कांस्टेबल",
            "हेड कांस्टेबल",
            "सब इंस्पेक्टर",
            "इंस्पेक्टर",
            "सहायक सब इंस्पेक्टर",
            "पुलिस उपाधीक्षक",
            "पुलिस अधीक्षक",
            "वायरलेस ऑपरेटर",
            "ड्राइवर कांस्टेबल",
            "होम गार्ड",
        ],
    },
    "teaching": {
        "en": [
            "Primary Teacher",
            "TGT (Trained Graduate Teacher)",
            "PGT (Post Graduate Teacher)",
            "Assistant Professor",
            "Lecturer",
            "Principal",
            "Headmaster",
            "Physical Education Teacher",
            "Computer Teacher",
            "Special Educator",
        ],
        "hi": [
            "प्राथमिक शिक्षक",
            "प्रशिक्षित स्नातक शिक्षक",
            "स्नातकोत्तर शिक्षक",
            "सहायक प्रोफेसर",
            "व्याख्याता",
            "प्रधानाचार्य",
            "प्रधानाध्यापक",
            "शारीरिक शिक्षा शिक्षक",
            "कंप्यूटर शिक्षक",
            "विशेष शिक्षक",
        ],
    },
}

# Organizations by category
ORGANIZATIONS = {
    "railway": ["Indian Railways", "RRB", "Railway Recruitment Board", "Northern Railway", "Southern Railway", "Central Railway", "Western Railway", "Eastern Railway"],
    "ssc": ["Staff Selection Commission", "SSC", "Central Government", "Ministry of Finance", "Ministry of Home Affairs", "Ministry of Defence"],
    "bank": ["State Bank of India", "Punjab National Bank", "Bank of Baroda", "IBPS", "RBI", "Canara Bank", "Union Bank", "Indian Bank"],
    "police": ["State Police", "Central Reserve Police Force", "Border Security Force", "CISF", "ITBP", "SSB", "Railway Protection Force"],
    "teaching": ["Kendriya Vidyalaya Sangathan", "Navodaya Vidyalaya Samiti", "State Education Department", "CBSE", "ICSE", "State Board"],
}

# Education requirements
EDUCATION_OPTIONS = {
    "10th_pass": {"en": "10th Pass / Matriculation", "hi": "दसवीं पास / मैट्रिकुलेशन"},
    "12th_pass": {"en": "12th Pass / Intermediate", "hi": "बारहवीं पास / इंटरमीडिएट"},
    "graduate": {"en": "Graduate in any discipline", "hi": "किसी भी विषय में स्नातक"},
    "post_graduate": {"en": "Post Graduate", "hi": "स्नातकोत्तर"},
    "diploma": {"en": "Diploma in relevant field", "hi": "संबंधित क्षेत्र में डिप्लोमा"},
    "iti": {"en": "ITI in relevant trade", "hi": "संबंधित ट्रेड में आईटीआई"},
    "b_tech": {"en": "B.Tech / B.E.", "hi": "बी.टेक / बी.ई."},
    "b_ed": {"en": "B.Ed", "hi": "बी.एड"},
}

# Salary ranges by category (monthly in INR)
SALARY_RANGES = {
    "railway": [(18000, 56900), (25000, 81100), (35400, 112400)],
    "ssc": [(18000, 56900), (25000, 81100), (35400, 112400)],
    "bank": [(23000, 42000), (36000, 63000), (50000, 90000)],
    "police": [(21700, 69100), (25500, 81100), (35400, 112400)],
    "teaching": [(35000, 60000), (47600, 91000), (57700, 182200)],
}

# Indian states
INDIAN_STATES = [
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "All India"
]


class SyntheticJobGenerator:
    """
    Generates synthetic job data for training
    Uses templates and randomization to create diverse samples
    """
    
    def __init__(self, language: str = "bilingual"):
        """
        Args:
            language: "en", "hi", or "bilingual"
        """
        self.language = language
    
    def generate_job(
        self,
        category: str = None,
        state: str = None,
        education: str = None
    ) -> Dict:
        """
        Generate a single synthetic job posting
        """
        # Random selections
        if category is None:
            category = random.choice(list(JOB_TITLES.keys()))
        
        if state is None:
            state = random.choice(INDIAN_STATES)
        
        if education is None:
            education = random.choice(list(EDUCATION_OPTIONS.keys()))
        
        # Get title
        titles = JOB_TITLES.get(category, JOB_TITLES["ssc"])
        title_idx = random.randint(0, len(titles["en"]) - 1)
        
        if self.language == "en":
            title = titles["en"][title_idx]
        elif self.language == "hi":
            title = titles["hi"][title_idx]
        else:
            title = f"{titles['en'][title_idx]} / {titles['hi'][title_idx]}"
        
        # Get organization
        org = random.choice(ORGANIZATIONS.get(category, ORGANIZATIONS["ssc"]))
        
        # Get salary
        salary_range = random.choice(SALARY_RANGES.get(category, SALARY_RANGES["ssc"]))
        salary = f"₹{salary_range[0]:,} - ₹{salary_range[1]:,}"
        
        # Get education requirement
        edu = EDUCATION_OPTIONS.get(education, EDUCATION_OPTIONS["graduate"])
        edu_text = edu["en"] if self.language == "en" else edu["hi"] if self.language == "hi" else f"{edu['en']} / {edu['hi']}"
        
        # Age limit
        min_age = random.choice([18, 20, 21])
        max_age = random.choice([27, 30, 35, 40])
        
        # Vacancies
        vacancies = random.randint(50, 5000)
        
        # Dates
        post_date = datetime.now() - timedelta(days=random.randint(1, 30))
        deadline = post_date + timedelta(days=random.randint(15, 60))
        
        # Generate description
        description = self._generate_description(
            title, org, edu_text, salary, min_age, max_age, vacancies, state, category
        )
        
        return {
            "title": title,
            "organization": org,
            "category": category,
            "state": state,
            "education_required": education,
            "education_text": edu_text,
            "salary": salary,
            "salary_min": salary_range[0],
            "salary_max": salary_range[1],
            "min_age": min_age,
            "max_age": max_age,
            "vacancies": vacancies,
            "post_date": post_date.strftime("%Y-%m-%d"),
            "deadline": deadline.strftime("%Y-%m-%d"),
            "description": description,
            "source": "synthetic",
            "language": self.language,
            "_synthetic": True,
        }
    
    def _generate_description(
        self,
        title: str,
        org: str,
        education: str,
        salary: str,
        min_age: int,
        max_age: int,
        vacancies: int,
        state: str,
        category: str
    ) -> str:
        """Generate job description text"""
        
        if self.language == "hi":
            templates = [
                f"{org} ने {title} के {vacancies} पदों के लिए भर्ती अधिसूचना जारी की है।",
                f"शैक्षिक योग्यता: {education}",
                f"आयु सीमा: {min_age} से {max_age} वर्ष",
                f"वेतनमान: {salary} प्रति माह",
                f"पद का स्थान: {state}",
                "इच्छुक और योग्य उम्मीदवार अंतिम तिथि से पहले ऑनलाइन आवेदन करें।",
            ]
        elif self.language == "en":
            templates = [
                f"{org} has released recruitment notification for {vacancies} posts of {title}.",
                f"Educational Qualification: {education}",
                f"Age Limit: {min_age} to {max_age} years",
                f"Pay Scale: {salary} per month",
                f"Job Location: {state}",
                "Interested and eligible candidates should apply online before the last date.",
            ]
        else:
            templates = [
                f"{org} has released recruitment notification for {vacancies} posts of {title}.",
                f"{org} ने {title} के {vacancies} पदों के लिए भर्ती अधिसूचना जारी की है।",
                f"Educational Qualification / शैक्षिक योग्यता: {education}",
                f"Age Limit / आयु सीमा: {min_age} to {max_age} years / {min_age} से {max_age} वर्ष",
                f"Pay Scale / वेतनमान: {salary}",
                f"Job Location / पद का स्थान: {state}",
            ]
        
        return "\n".join(templates)
    
    def generate_batch(
        self,
        count: int,
        balanced_by: str = None,
        categories: List[str] = None,
        states: List[str] = None
    ) -> List[Dict]:
        """
        Generate batch of synthetic jobs
        
        Args:
            count: Number of jobs to generate
            balanced_by: "category", "state", or None
            categories: List of categories to include
            states: List of states to include
        """
        jobs = []
        
        if categories is None:
            categories = list(JOB_TITLES.keys())
        
        if states is None:
            states = INDIAN_STATES
        
        if balanced_by == "category":
            # Equal distribution across categories
            per_category = count // len(categories)
            for category in categories:
                for _ in range(per_category):
                    jobs.append(self.generate_job(category=category))
        
        elif balanced_by == "state":
            # Equal distribution across states
            per_state = count // len(states)
            for state in states:
                for _ in range(per_state):
                    jobs.append(self.generate_job(state=state))
        
        else:
            # Random generation
            for _ in range(count):
                jobs.append(self.generate_job())
        
        random.shuffle(jobs)
        logger.info(f"Generated {len(jobs)} synthetic jobs")
        return jobs


class SyntheticUserGenerator:
    """
    Generates synthetic user profiles for training recommendation system
    """
    
    NAMES = {
        "first_names": [
            "Rahul", "Priya", "Amit", "Neha", "Raj", "Anjali", "Vikram", "Pooja",
            "Suresh", "Meena", "Arun", "Kavita", "Deepak", "Sunita", "Rajesh", "Anita"
        ],
        "last_names": [
            "Kumar", "Singh", "Sharma", "Verma", "Patel", "Gupta", "Yadav", "Mishra",
            "Jha", "Tiwari", "Pandey", "Dubey", "Srivastava", "Chauhan", "Thakur", "Maurya"
        ]
    }
    
    def generate_user(self) -> Dict:
        """Generate a single synthetic user profile"""
        
        # Basic info
        first_name = random.choice(self.NAMES["first_names"])
        last_name = random.choice(self.NAMES["last_names"])
        gender = random.choice(["male", "female"])
        
        # Age and education correlated
        age = random.randint(18, 40)
        
        if age < 20:
            education = random.choice(["10th_pass", "12th_pass"])
        elif age < 25:
            education = random.choice(["12th_pass", "graduate", "diploma"])
        else:
            education = random.choice(["graduate", "post_graduate", "diploma"])
        
        # Location
        state = random.choice(INDIAN_STATES[:-1])  # Exclude "All India"
        
        # Preferences
        preferred_categories = random.sample(
            list(JOB_TITLES.keys()),
            k=random.randint(1, 3)
        )
        
        # Salary expectation based on education
        salary_expectations = {
            "10th_pass": (15000, 25000),
            "12th_pass": (18000, 30000),
            "graduate": (25000, 50000),
            "post_graduate": (35000, 70000),
            "diploma": (20000, 40000),
        }
        
        exp_range = salary_expectations.get(education, (20000, 40000))
        salary_expectation = random.randint(exp_range[0], exp_range[1])
        
        return {
            "name": f"{first_name} {last_name}",
            "first_name": first_name,
            "last_name": last_name,
            "gender": gender,
            "age": age,
            "education": education,
            "state": state,
            "preferred_categories": preferred_categories,
            "salary_expectation": salary_expectation,
            "language_preference": random.choice(["en", "hi", "bilingual"]),
            "_synthetic": True,
        }
    
    def generate_batch(self, count: int) -> List[Dict]:
        """Generate batch of synthetic users"""
        users = [self.generate_user() for _ in range(count)]
        logger.info(f"Generated {len(users)} synthetic users")
        return users


class SyntheticInteractionGenerator:
    """
    Generates synthetic user-job interactions for training
    """
    
    def generate_interactions(
        self,
        users: List[Dict],
        jobs: List[Dict],
        interactions_per_user: int = 10
    ) -> List[Dict]:
        """
        Generate realistic interactions between users and jobs
        """
        interactions = []
        
        for user in users:
            # Filter relevant jobs for this user
            relevant_jobs = [
                job for job in jobs
                if job.get("category") in user.get("preferred_categories", [])
                or job.get("state") == user.get("state")
                or job.get("state") == "All India"
            ]
            
            if not relevant_jobs:
                relevant_jobs = jobs
            
            # Generate interactions
            num_interactions = min(interactions_per_user, len(relevant_jobs))
            sampled_jobs = random.sample(relevant_jobs, num_interactions)
            
            for job in sampled_jobs:
                # Determine interaction type based on relevance
                relevance_score = self._calculate_relevance(user, job)
                
                if relevance_score > 0.7:
                    action = random.choices(
                        ["applied", "saved", "clicked"],
                        weights=[0.4, 0.3, 0.3]
                    )[0]
                elif relevance_score > 0.4:
                    action = random.choices(
                        ["clicked", "saved", "skipped"],
                        weights=[0.4, 0.3, 0.3]
                    )[0]
                else:
                    action = random.choices(
                        ["skipped", "clicked", "rejected"],
                        weights=[0.5, 0.3, 0.2]
                    )[0]
                
                interactions.append({
                    "user_id": user.get("id", id(user)),
                    "job_id": job.get("id", id(job)),
                    "action": action,
                    "relevance_score": relevance_score,
                    "timestamp": datetime.now().isoformat(),
                    "_synthetic": True,
                })
        
        logger.info(f"Generated {len(interactions)} synthetic interactions")
        return interactions
    
    def _calculate_relevance(self, user: Dict, job: Dict) -> float:
        """Calculate relevance score between user and job"""
        score = 0.0
        
        # Category match
        if job.get("category") in user.get("preferred_categories", []):
            score += 0.3
        
        # State match
        if job.get("state") == user.get("state") or job.get("state") == "All India":
            score += 0.2
        
        # Education match
        edu_order = {"10th_pass": 1, "12th_pass": 2, "diploma": 3, "graduate": 4, "post_graduate": 5}
        user_edu = edu_order.get(user.get("education", "graduate"), 4)
        job_edu = edu_order.get(job.get("education_required", "graduate"), 4)
        
        if user_edu >= job_edu:
            score += 0.2
        
        # Age match
        user_age = user.get("age", 25)
        min_age = job.get("min_age", 18)
        max_age = job.get("max_age", 35)
        
        if min_age <= user_age <= max_age:
            score += 0.2
        
        # Salary match
        user_salary = user.get("salary_expectation", 30000)
        job_salary = job.get("salary_min", 25000)
        
        if job_salary >= user_salary * 0.8:
            score += 0.1
        
        return min(score, 1.0)


def generate_training_dataset(
    num_jobs: int = 1000,
    num_users: int = 500,
    output_dir: str = None
) -> Dict[str, str]:
    """
    Generate complete synthetic training dataset
    
    Returns paths to generated files
    """
    if output_dir is None:
        output_dir = Path(__file__).parent / "generated"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate data
    job_gen = SyntheticJobGenerator(language="bilingual")
    user_gen = SyntheticUserGenerator()
    interaction_gen = SyntheticInteractionGenerator()
    
    jobs = job_gen.generate_batch(num_jobs, balanced_by="category")
    users = user_gen.generate_batch(num_users)
    interactions = interaction_gen.generate_interactions(users, jobs)
    
    # Save to files
    paths = {}
    
    jobs_path = output_dir / "synthetic_jobs.jsonl"
    with open(jobs_path, 'w', encoding='utf-8') as f:
        for job in jobs:
            f.write(json.dumps(job, ensure_ascii=False) + "\n")
    paths["jobs"] = str(jobs_path)
    
    users_path = output_dir / "synthetic_users.jsonl"
    with open(users_path, 'w', encoding='utf-8') as f:
        for user in users:
            f.write(json.dumps(user, ensure_ascii=False) + "\n")
    paths["users"] = str(users_path)
    
    interactions_path = output_dir / "synthetic_interactions.jsonl"
    with open(interactions_path, 'w', encoding='utf-8') as f:
        for interaction in interactions:
            f.write(json.dumps(interaction, ensure_ascii=False) + "\n")
    paths["interactions"] = str(interactions_path)
    
    logger.info(f"Generated training dataset: {paths}")
    return paths
