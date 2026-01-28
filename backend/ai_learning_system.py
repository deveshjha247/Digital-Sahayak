"""
Digital Sahayak - Self-Learning AI System
------------------------------------------
This AI system learns from other AIs and improves itself continuously.
Features:
- Learns from external AI responses (Copilot, ChatGPT, etc.)
- Understands project context and domain
- Web search capability for real-time information
- Context-aware response generation
"""

from openai import OpenAI
import os
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import json
from motor.motor_asyncio import AsyncIOMotorClient
import httpx
from bs4 import BeautifulSoup
import re
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

class SelfLearningAI:
    """
    A self-learning AI that:
    1. Learns from other AI systems
    2. Understands the project domain (Digital Sahayak - Jobs & Schemes)
    3. Searches web for real-time information
    4. Improves responses based on past learnings
    5. Uses Rule + ML Hybrid approach for matching
    6. Learns from interaction logs
    """
    
    def __init__(self, openai_client: OpenAI, db):
        self.openai_client = openai_client
        self.db = db
        self.learning_collection = db['ai_learning_history']
        self.improvement_collection = db['ai_improvements']
        self.project_context_collection = db['ai_project_context']
        self.web_search_cache = db['ai_web_search_cache']
        self.interaction_logs_collection = db['ai_interaction_logs']
        self.rules_collection = db['ai_matching_rules']
        
        # Initialize field mapping rules for job matching
        self.field_mapping_rules = {
            "education": {
                "10th": ["10th", "Matriculation", "High School", "10वीं"],
                "12th": ["12th", "Intermediate", "+2", "12वीं"],
                "Graduate": ["Graduate", "Graduation", "Bachelor", "BA", "BSc", "BCom", "स्नातक"],
                "Post Graduate": ["Post Graduate", "PG", "Master", "MA", "MSc", "MCom", "स्नातकोत्तर"]
            },
            "state": {
                "Bihar": ["BR", "bihar", "बिहार"],
                "Jharkhand": ["JH", "jharkhand", "झारखंड"],
                "Uttar Pradesh": ["UP", "uttar pradesh", "उत्तर प्रदेश"],
                "All India": ["All India", "National", "सभी राज्य"]
            },
            "category": {
                "Railway": ["railway", "रेलवे", "rail", "indian railway"],
                "SSC": ["ssc", "staff selection", "एसएससी"],
                "UPSC": ["upsc", "civil services", "यूपीएससी"],
                "Bank": ["bank", "बैंक", "banking"],
                "Police": ["police", "पुलिस", "constable"]
            }
        }
        
        # Heuristic scoring weights
        self.heuristic_weights = {
            "education_match": 30,
            "age_match": 20,
            "state_match": 25,
            "category_match": 15,
            "experience_match": 10
        }
        
        # Load existing rules from database
        self.custom_rules = []
        
        # Project domain knowledge
        self.project_domain = {
            "name": "Digital Sahayak",
            "purpose": "Government Jobs and Schemes (Yojana) Portal for Indian Citizens",
            "key_features": [
                "Job alerts from government sources",
                "Yojana (welfare schemes) listings",
                "AI-powered job matching based on education, age, state",
                "Payment integration with Cashfree",
                "WhatsApp notifications",
                "Content scraping and rewriting"
            ],
            "target_users": [
                "Rural/Semi-urban youth seeking government jobs",
                "Low-income families looking for welfare schemes",
                "Job seekers aged 18-40"
            ],
            "technical_stack": {
                "backend": "Python FastAPI",
                "frontend": "React.js with Tailwind CSS",
                "database": "MongoDB",
                "ai": "OpenAI GPT"
            }
        }
        
        # Initialize project understanding
        self.project_files_analyzed = False
    
    async def analyze_project_structure(self, project_root: str = None) -> Dict:
        """
        Analyze the entire project structure to understand context
        This helps AI make better decisions based on the actual codebase
        
        Args:
            project_root: Root directory of the project
            
        Returns:
            Dict with project analysis
        """
        if not project_root:
            project_root = Path(__file__).parent.parent
        
        analysis = {
            "timestamp": datetime.now(),
            "files_analyzed": [],
            "routes_found": [],
            "models_found": [],
            "key_functions": [],
            "dependencies": [],
            "insights": []
        }
        
        try:
            # Analyze backend/server.py
            server_file = Path(project_root) / "backend" / "server.py"
            if server_file.exists():
                with open(server_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # Extract API routes
                    routes = re.findall(r'@api_router\.(get|post|put|delete)\("([^"]+)"', content)
                    analysis['routes_found'] = [f"{method.upper()} {path}" for method, path in routes]
                    
                    # Extract model classes
                    models = re.findall(r'class (\w+)\(BaseModel\)', content)
                    analysis['models_found'] = models
                    
                    # Extract async functions
                    functions = re.findall(r'async def (\w+)\(', content)
                    analysis['key_functions'] = functions[:20]  # Top 20
                    
                    analysis['files_analyzed'].append('backend/server.py')
            
            # Analyze requirements.txt
            req_file = Path(project_root) / "backend" / "requirements.txt"
            if req_file.exists():
                with open(req_file, 'r', encoding='utf-8') as f:
                    deps = [line.strip() for line in f if line.strip() and not line.startswith('#')]
                    analysis['dependencies'] = deps[:15]
                    analysis['files_analyzed'].append('backend/requirements.txt')
            
            # Analyze frontend package.json
            package_file = Path(project_root) / "frontend" / "package.json"
            if package_file.exists():
                with open(package_file, 'r', encoding='utf-8') as f:
                    package_data = json.load(f)
                    if 'dependencies' in package_data:
                        analysis['dependencies'].extend(list(package_data['dependencies'].keys())[:10])
                    analysis['files_analyzed'].append('frontend/package.json')
            
            # Generate insights
            analysis['insights'] = [
                f"Found {len(analysis['routes_found'])} API endpoints",
                f"Found {len(analysis['models_found'])} data models",
                f"Using {len(analysis['dependencies'])} dependencies",
                "Project focuses on job and yojana management",
                "Has AI matching capabilities",
                "Integrated with payment and WhatsApp systems"
            ]
            
            # Save to database
            await self.project_context_collection.insert_one(dict(analysis))
            self.project_files_analyzed = True
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.now()
            }
    
    async def web_search(self, query: str, max_results: int = 3) -> List[Dict]:
        """
        Search the web for real-time information
        Uses DuckDuckGo-like approach (no API key needed)
        
        Args:
            query: Search query
            max_results: Number of results to return
            
        Returns:
            List of search results with title, url, snippet
        """
        # Check cache first
        cached = await self.web_search_cache.find_one({
            "query": query,
            "timestamp": {"$gte": datetime.now().timestamp() - 3600}  # 1 hour cache
        })
        
        if cached:
            return cached['results']
        
        results = []
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Use DuckDuckGo HTML search (no API key required)
                url = f"https://html.duckduckgo.com/html/?q={query}"
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = await client.get(url, headers=headers, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Parse search results
                    result_divs = soup.find_all('div', class_='result')[:max_results]
                    
                    for div in result_divs:
                        title_elem = div.find('a', class_='result__a')
                        snippet_elem = div.find('a', class_='result__snippet')
                        
                        if title_elem:
                            result = {
                                'title': title_elem.get_text(strip=True),
                                'url': title_elem.get('href', ''),
                                'snippet': snippet_elem.get_text(strip=True) if snippet_elem else ''
                            }
                            results.append(result)
            
            # Cache the results
            await self.web_search_cache.insert_one({
                "query": query,
                "results": results,
                "timestamp": datetime.now().timestamp()
            })
            
        except Exception as e:
            # Fallback: return a basic result
            results = [{
                "title": "Search unavailable",
                "url": "",
                "snippet": f"Web search failed: {str(e)}"
            }]
        
        return results
    
    async def extract_web_content(self, url: str) -> str:
        """
        Extract main content from a webpage
        Useful for getting detailed information from search results
        
        Args:
            url: URL to extract content from
            
        Returns:
            Extracted text content
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, follow_redirects=True)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Get text
                    text = soup.get_text()
                    
                    # Clean up
                    lines = (line.strip() for line in text.splitlines())
                    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                    text = ' '.join(chunk for chunk in chunks if chunk)
                    
                    # Limit to 2000 characters
                    return text[:2000]
    
    async def normalize_field_value(self, field: str, value: str) -> str:
        """
        Normalize field values using field mapping rules
        Handles variations, abbreviations, and Hindi translations
        
        Args:
            field: Field name (education, state, category)
            value: Raw value to normalize
            
        Returns:
            Normalized standard value
        """
        if not value or field not in self.field_mapping_rules:
            return value
        
        value_lower = value.lower().strip()
        
        # Check against mapping rules
        for standard_value, variations in self.field_mapping_rules[field].items():
            for variation in variations:
                if variation.lower() in value_lower or value_lower in variation.lower():
                    return standard_value
        
        return value  # Return original if no match
    
    async def apply_heuristic_matching(self, job_data: Dict, user_profile: Dict) -> Dict:
        """
        Apply rule-based heuristic matching for job recommendations
        Uses weighted scoring system
        
        Args:
            job_data: Job details
            user_profile: User profile
            
        Returns:
            Dict with score, breakdown, and matched fields
        """
        score_breakdown = {}
        matched_fields = []
        total_score = 0
        
        # 1. Education Match (30 points)
        job_education = await self.normalize_field_value("education", job_data.get('education', ''))
        user_education = await self.normalize_field_value("education", user_profile.get('education', ''))
        
        if job_education == user_education:
            education_score = self.heuristic_weights['education_match']
            matched_fields.append('education')
        elif self._education_qualifies(user_education, job_education):
            education_score = self.heuristic_weights['education_match'] * 0.7
            matched_fields.append('education_partial')
        else:
            education_score = 0
        
        score_breakdown['education'] = education_score
        total_score += education_score
        
        # 2. Age Match (20 points)
        user_age = user_profile.get('age', 0)
        min_age = job_data.get('min_age', 18)
        max_age = job_data.get('max_age', 40)
        
        if min_age <= user_age <= max_age:
            age_score = self.heuristic_weights['age_match']
            matched_fields.append('age')
        elif abs(user_age - min_age) <= 2 or abs(user_age - max_age) <= 2:
            age_score = self.heuristic_weights['age_match'] * 0.5
            matched_fields.append('age_close')
        else:
            age_score = 0
        
        score_breakdown['age'] = age_score
        total_score += age_score
        
        # 3. State Match (25 points)
        job_state = await self.normalize_field_value("state", job_data.get('state', ''))
        user_state = await self.normalize_field_value("state", user_profile.get('state', ''))
        
        if job_state == user_state or job_state == "All India":
            state_score = self.heuristic_weights['state_match']
            matched_fields.append('state')
        else:
            state_score = 0
        
        score_breakdown['state'] = state_score
        total_score += state_score
        
        # 4. Category Match (15 points)
        job_category = job_data.get('category', '')
        user_preferences = user_profile.get('preferred_categories', [])
        
        if job_category in user_preferences:
            category_score = self.heuristic_weights['category_match']
            matched_fields.append('category')
        else:
            category_score = 0
        
        score_breakdown['category'] = category_score
        total_score += category_score
        
        # 5. Experience Match (10 points) - if applicable
        job_experience = job_data.get('experience_required', 0)
        user_experience = user_profile.get('experience_years', 0)
        
        if user_experience >= job_experience:
            experience_score = self.heuristic_weights['experience_match']
            matched_fields.append('experience')
        else:
            experience_score = max(0, self.heuristic_weights['experience_match'] * 0.3)
        
        score_breakdown['experience'] = experience_score
        total_score += experience_score
        
        return {
            "total_score": round(total_score, 2),
            "max_score": sum(self.heuristic_weights.values()),
            "score_breakdown": score_breakdown,
            "matched_fields": matched_fields,
            "match_percentage": round((total_score / sum(self.heuristic_weights.values())) * 100, 2)
        }
    
    def _education_qualifies(self, user_education: str, required_education: str) -> bool:
        """Check if user's education qualifies for job requirement"""
        education_hierarchy = ["10th", "12th", "Graduate", "Post Graduate"]
        
        try:
            user_level = education_hierarchy.index(user_education)
            required_level = education_hierarchy.index(required_education)
            return user_level >= required_level
        except ValueError:
            return False
    
    async def hybrid_job_matching(self, job_data: Dict, user_profile: Dict, 
                                   use_ml: bool = True) -> Dict:
        """
        Hybrid approach: Combines rule-based heuristics with ML predictions
        
        Args:
            job_data: Job details
            user_profile: User profile
            use_ml: Whether to use ML enhancement
            
        Returns:
            Dict with final score, rule score, ML score, and reasoning
        """
        # Step 1: Apply rule-based heuristic matching
        heuristic_result = await self.apply_heuristic_matching(job_data, user_profile)
        
        # Step 2: Apply ML enhancement if enabled
        ml_enhancement = 0
        ml_reasoning = ""
        
        if use_ml and self.openai_client:
            ml_prompt = f"""
            Analyze this job match and provide enhancement score (-10 to +10 points).
            Consider soft factors not captured by rules.
            
            Job: {job_data.get('title', 'Unknown')}
            User: {user_profile.get('education', '?')} educated, {user_profile.get('age', '?')} years old
            
            Rule-based score: {heuristic_result['match_percentage']}%
            Matched fields: {', '.join(heuristic_result['matched_fields'])}
            
            Consider:
            1. Job description relevance to user profile
            2. Career progression alignment
            3. Geographic suitability
            4. Application deadline urgency
            
            Respond with JSON:
            {{
                "ml_score_adjustment": <-10 to +10>,
                "reasoning": "brief explanation in Hindi"
            }}
            """
            
            try:
                response = self.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": ml_prompt}],
                    temperature=0.3
                )
                
                ml_result = json.loads(response.choices[0].message.content)
                ml_enhancement = ml_result.get('ml_score_adjustment', 0)
                ml_reasoning = ml_result.get('reasoning', '')
            except Exception as e:
                logger.warning(f"ML enhancement failed: {e}")
        
        # Step 3: Combine scores
        final_score = min(100, max(0, heuristic_result['match_percentage'] + ml_enhancement))
        
        # Step 4: Log this interaction for future learning
        await self.log_interaction({
            "type": "hybrid_job_matching",
            "job_id": job_data.get('id'),
            "user_id": user_profile.get('id'),
            "heuristic_score": heuristic_result['match_percentage'],
            "ml_adjustment": ml_enhancement,
            "final_score": final_score,
            "matched_fields": heuristic_result['matched_fields'],
            "timestamp": datetime.now()
        })
        
        return {
            "final_score": final_score,
            "rule_based_score": heuristic_result['match_percentage'],
            "ml_enhancement": ml_enhancement,
            "score_breakdown": heuristic_result['score_breakdown'],
            "matched_fields": heuristic_result['matched_fields'],
            "ml_reasoning": ml_reasoning,
            "method": "hybrid",
            "confidence": 0.85 if use_ml else 0.70
        }
    
    async def log_interaction(self, interaction_data: Dict):
        """
        Log user interactions for learning from behavior patterns
        
        Args:
            interaction_data: Interaction details
        """
        try:
            await self.interaction_logs_collection.insert_one(interaction_data)
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")
    
    async def learn_from_logs(self, days: int = 7) -> Dict:
        """
        Analyze interaction logs to learn patterns and improve matching
        
        Args:
            days: Number of days of logs to analyze
            
        Returns:
            Dict with learned patterns and rule adjustments
        """
        cutoff_date = datetime.now().timestamp() - (days * 24 * 3600)
        
        # Fetch recent logs
        logs = await self.interaction_logs_collection.find({
            "timestamp": {"$gte": cutoff_date}
        }).to_list(1000)
        
        if not logs:
            return {"learned": False, "reason": "No recent logs available"}
        
        # Analyze patterns
        analysis_prompt = f"""
        Analyze these interaction logs to identify patterns and suggest improvements.
        
        Total interactions: {len(logs)}
        Sample data: {json.dumps(logs[:10], default=str, ensure_ascii=False)}
        
        Identify:
        1. Which fields are most predictive of good matches?
        2. Are current weights optimal?
        3. Are there patterns in user behavior?
        4. Should we adjust heuristic weights?
        
        Respond with JSON:
        {{
            "patterns_found": ["pattern1", "pattern2"],
            "weight_adjustments": {{"field": "new_weight"}},
            "insights": ["insight1", "insight2"],
            "recommended_rules": ["rule1", "rule2"]
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": analysis_prompt}],
                temperature=0.2
            )
            
            learned_patterns = json.loads(response.choices[0].message.content)
            
            # Apply weight adjustments if suggested
            if learned_patterns.get('weight_adjustments'):
                for field, new_weight in learned_patterns['weight_adjustments'].items():
                    if field in self.heuristic_weights:
                        old_weight = self.heuristic_weights[field]
                        self.heuristic_weights[field] = new_weight
                        logger.info(f"Adjusted weight for {field}: {old_weight} → {new_weight}")
            
            # Save learning
            await self.improvement_collection.insert_one({
                "timestamp": datetime.now(),
                "type": "log_learning",
                "logs_analyzed": len(logs),
                "patterns": learned_patterns,
                "days_analyzed": days
            })
            
            return {
                "learned": True,
                "logs_analyzed": len(logs),
                "patterns": learned_patterns,
                "weights_updated": bool(learned_patterns.get('weight_adjustments'))
            }
            
        except Exception as e:
            logger.error(f"Log learning failed: {e}")
            return {"learned": False, "error": str(e)}
    
    async def add_custom_rule(self, rule: Dict) -> bool:
        """
        Add a custom matching rule learned from patterns
        
        Args:
            rule: Rule definition with conditions and actions
            
        Returns:
            bool: Success status
        """
        try:
            rule['created_at'] = datetime.now()
            rule['active'] = True
            await self.rules_collection.insert_one(rule)
            self.custom_rules.append(rule)
            return True
        except Exception as e:
            logger.error(f"Failed to add rule: {e}")
            return False
    
    async def get_active_rules(self) -> List[Dict]:
        """Get all active custom matching rules"""
        if not self.custom_rules:
            self.custom_rules = await self.rules_collection.find(
                {"active": True}
            ).to_list(100)
        return self.custom_rules
        except:
            return ""
        
        return ""
        
    async def learn_from_other_ai(self, prompt: str, other_ai_response: str, 
                                   ai_name: str = "External AI", use_web_search: bool = False) -> Dict:
        """
        Learn from other AI's response and generate improved version
        Can optionally use web search for fact-checking and additional context
        
        Args:
            prompt: Original question/task
            other_ai_response: Response from another AI
            ai_name: Name of the external AI (Copilot, ChatGPT, etc.)
            use_web_search: Whether to search web for additional context
        
        Returns:
            Dict with improved response and learning insights
        """
        # Get project context if not already analyzed
        if not self.project_files_analyzed:
            await self.analyze_project_structure()
        
        # Web search if requested
        web_context = ""
        if use_web_search:
            search_results = await self.web_search(prompt)
            web_context = "\n\nWeb Search Results:\n"
            for idx, result in enumerate(search_results, 1):
                web_context += f"{idx}. {result['title']}: {result['snippet']}\n"
        
        # Step 1: Analyze the other AI's response with project context
        analysis_prompt = f"""
        Analyze an AI response in the context of Digital Sahayak project.
        
        Project Context:
        - Name: {self.project_domain['name']}
        - Purpose: {self.project_domain['purpose']}
        - Key Features: {', '.join(self.project_domain['key_features'])}
        - Target Users: {', '.join(self.project_domain['target_users'])}
        
        Original Prompt: {prompt}
        
        Other AI ({ai_name}) Response:
        {other_ai_response}
        
        {web_context}
        
        Analyze and provide in JSON format:
        {{
            "strengths": ["what's good in this response"],
            "weaknesses": ["what can be improved"],
            "missing_aspects": ["what's missing"],
            "project_relevance": "how relevant is this to Digital Sahayak",
            "better_approach": "detailed explanation of better approach",
            "needs_web_search": true/false
        }}
        """
        
        try:
            analysis_response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an AI expert analyzing other AI responses."},
                    {"role": "user", "content": analysis_prompt}
                ],
                temperature=0.3
            )
            
            analysis = json.loads(analysis_response.choices[0].message.content)
            
            # If analysis suggests web search is needed and we haven't done it yet
            if analysis.get('needs_web_search', False) and not use_web_search:
                return await self.learn_from_other_ai(prompt, other_ai_response, ai_name, use_web_search=True)
            
            # Step 2: Generate improved response with full context
            improved_prompt = f"""
            You are Digital Sahayak AI - specialized in Indian government jobs and welfare schemes.
            
            Project Domain:
            {json.dumps(self.project_domain, indent=2)}
            
            Original Task: {prompt}
            Other AI ({ai_name}) Response: {other_ai_response}
            
            Analysis of Other AI:
            - Strengths: {', '.join(analysis['strengths'])}
            - Weaknesses: {', '.join(analysis['weaknesses'])}
            - Missing: {', '.join(analysis['missing_aspects'])}
            - Project Relevance: {analysis.get('project_relevance', 'N/A')}
            - Better Approach: {analysis['better_approach']}
            
            {web_context}
            
            Generate an improved response that:
            1. Retains the strengths from other AI
            2. Fixes all weaknesses
            3. Adds missing aspects
            4. Is highly relevant to Digital Sahayak's mission
            5. Uses web search context if available
            6. Is practical and implementable
            
            Provide response in English/Hindi as appropriate for Indian users.
            """
            
            improved_response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are Digital Sahayak AI - a self-improving AI assistant."},
                    {"role": "user", "content": improved_prompt}
                ],
                temperature=0.7
            )
            
            improved_text = improved_response.choices[0].message.content
            
            # Step 3: Save learning with project context
            learning_record = {
                "timestamp": datetime.now(),
                "prompt": prompt,
                "other_ai_name": ai_name,
                "other_ai_response": other_ai_response,
                "analysis": analysis,
                "improved_response": improved_text,
                "used_web_search": use_web_search,
                "web_results": search_results if use_web_search else [],
                "project_context_applied": True,
                "improvement_score": await self._calculate_improvement_score(
                    other_ai_response, improved_text
                )
            }
            
            await self.learning_collection.insert_one(learning_record)
            
            return {
                "success": True,
                "original_ai": ai_name,
                "original_response": other_ai_response,
                "analysis": analysis,
                "improved_response": improved_text,
                "used_web_search": use_web_search,
                "learning_saved": True
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _calculate_improvement_score(self, original: str, improved: str) -> float:
        """
        Original और improved response को compare करके score calculate करो
        """
        prompt = f"""
        Compare these two responses and give an improvement score (0-100):
        
        Original: {original}
        Improved: {improved}
        
        Rate on: Clarity, Completeness, Accuracy, Helpfulness
        Return only a number between 0-100.
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )
            score = float(response.choices[0].message.content.strip())
            return min(max(score, 0), 100)
        except:
            return 50.0  # Default score
    
    async def generate_with_learning(self, prompt: str, context: str = "", 
                                    use_web_search: bool = False) -> Dict:
        """
        Generate response using past learnings and project context
        Can optionally search web for real-time information
        
        Args:
            prompt: User's question/task
            context: Additional context
            use_web_search: Whether to search web for current information
        
        Returns:
            Dict with response and confidence score
        """
        # Ensure project is analyzed
        if not self.project_files_analyzed:
            await self.analyze_project_structure()
        
        # Fetch similar past learnings
        past_learnings = await self.learning_collection.find(
            {"prompt": {"$regex": prompt[:30], "$options": "i"}}
        ).limit(5).to_list(5)
        
        # Compile learning insights
        learning_insights = []
        for learning in past_learnings:
            if 'analysis' in learning:
                learning_insights.append({
                    "learned_strengths": learning['analysis'].get('strengths', []),
                    "learned_weaknesses": learning['analysis'].get('weaknesses', []),
                    "better_approach": learning['analysis'].get('better_approach', '')
                })
        
        # Web search if requested
        web_context = ""
        if use_web_search:
            search_results = await self.web_search(prompt)
            web_context = "\n\nWeb Search Results:\n"
            for idx, result in enumerate(search_results, 1):
                web_context += f"{idx}. {result['title']}: {result['snippet']}\n"
        
        # Enhanced prompt with all context
        enhanced_prompt = f"""
        You are Digital Sahayak AI - Expert in Indian government jobs and welfare schemes.
        
        Project Domain:
        {json.dumps(self.project_domain, indent=2)}
        
        Task: {prompt}
        Additional Context: {context}
        
        Past Learnings from Similar Tasks:
        {json.dumps(learning_insights, ensure_ascii=False, indent=2) if learning_insights else "No past learnings yet"}
        
        {web_context}
        
        Generate the best possible response considering:
        1. Project's specific domain (Indian government jobs & schemes)
        2. Target audience (rural/semi-urban youth, low-income families)
        3. Past learnings and improvements
        4. Web search results if available
        5. Practical implementation in the Digital Sahayak system
        
        Be specific, actionable, and relevant to the Digital Sahayak mission.
        """
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are Digital Sahayak AI - continuously learning and improving."},
                {"role": "user", "content": enhanced_prompt}
            ],
            temperature=0.7
        )
        
        return {
            "response": response.choices[0].message.content,
            "learnings_applied": len(learning_insights),
            "used_web_search": use_web_search,
            "project_context_applied": True,
            "confidence": min(0.8 + (len(learning_insights) * 0.04), 0.99)  # More learnings = more confidence
        }
    
    async def compare_and_learn_batch(self, comparisons: List[Dict]) -> Dict:
        """
        Compare multiple AI responses to learn best patterns
        
        Args:
            comparisons: List of {prompt, ai_name, response}
        
        Returns:
            Learning summary with identified patterns
        """
        learning_summary = {
            "total_comparisons": len(comparisons),
            "patterns_learned": [],
            "best_practices": [],
            "project_specific_insights": []
        }
        
        # Analyze all responses together
        comparison_prompt = f"""
        Analyze multiple AI responses to identify best patterns for Digital Sahayak project.
        
        Project Context:
        - Focus: Indian government jobs and welfare schemes
        - Users: Rural youth, low-income families
        - Tech: Python FastAPI, React, MongoDB, OpenAI
        
        AI Responses to Compare:
        {json.dumps(comparisons, ensure_ascii=False, indent=2)}
        
        Identify:
        1. Common patterns in effective responses
        2. Best practices across all AIs
        3. What makes a response effective for Digital Sahayak users
        4. Project-specific insights
        5. Technical implementation patterns
        
        Return as JSON:
        {{
            "patterns_learned": ["pattern1", "pattern2"],
            "best_practices": ["practice1", "practice2"],
            "project_specific_insights": ["insight1", "insight2"],
            "recommended_approach": "detailed recommendation"
        }}
        """
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": comparison_prompt}],
                temperature=0.3
            )
            
            patterns = json.loads(response.choices[0].message.content)
            
            # Save improvements
            await self.improvement_collection.insert_one({
                "timestamp": datetime.now(),
                "type": "batch_learning",
                "patterns": patterns,
                "source_count": len(comparisons)
            })
            
            learning_summary.update(patterns)
            
        except Exception as e:
            learning_summary["error"] = str(e)
        
        return learning_summary
    
    async def get_learning_stats(self) -> Dict:
        """
        Learning statistics को fetch करो
        """
        total_learnings = await self.learning_collection.count_documents({})
        
        # Average improvement score
        pipeline = [
            {"$group": {
                "_id": None,
                "avg_improvement": {"$avg": "$improvement_score"},
                "total": {"$sum": 1}
            }}
        ]
        
        stats = await self.learning_collection.aggregate(pipeline).to_list(1)
        
        return {
            "total_learnings": total_learnings,
            "average_improvement_score": stats[0]['avg_improvement'] if stats else 0,
            "learning_rate": "Growing" if total_learnings > 10 else "Starting"
        }
    
    async def auto_improve_job_matching(self, job_data: Dict, user_profile: Dict,
                                       other_ai_suggestions: Optional[Dict] = None,
                                       use_web_search: bool = False) -> Dict:
        """
        Automatically improve job matching using AI learning
        Specific to Digital Sahayak's job recommendation system
        
        Args:
            job_data: Job details (title, education, age, state, etc.)
            user_profile: User profile (education, age, state, preferences)
            other_ai_suggestions: Optional suggestions from external AI
            use_web_search: Whether to search for job-related info
            
        Returns:
            Dict with match score and reasoning
        """
        # Calculate base match score
        base_match = await self._calculate_base_match(job_data, user_profile)
        
        # Web search for job details if requested
        web_context = ""
        if use_web_search and job_data.get('title'):
            search_query = f"{job_data['title']} eligibility criteria requirements"
            search_results = await self.web_search(search_query, max_results=2)
            web_context = "Web Info: " + "; ".join([r['snippet'] for r in search_results])
        
        # If external AI provided suggestions, learn from them
        if other_ai_suggestions:
            learning_prompt = f"""
            Job Matching Task for Digital Sahayak
            
            Job: {job_data.get('title', 'Unknown')}
            - Education: {job_data.get('education', 'Any')}
            - Age Range: {job_data.get('min_age', 18)}-{job_data.get('max_age', 40)}
            - State: {job_data.get('state', 'All India')}
            
            User Profile:
            - Education: {user_profile.get('education', 'Not specified')}
            - Age: {user_profile.get('age', 'Not specified')}
            - State: {user_profile.get('state', 'Not specified')}
            
            Base Match Score: {base_match}%
            
            {web_context}
            """
            
            improved_match = await self.learn_from_other_ai(
                prompt=learning_prompt,
                other_ai_response=str(other_ai_suggestions),
                ai_name="External Job Matcher",
                use_web_search=False  # Already searched if needed
            )
            
            return {
                "base_match": base_match,
                "improved_analysis": improved_match.get('improved_response'),
                "learned": True,
                "web_search_used": use_web_search
            }
        
        # Generate AI reasoning for the match
        reasoning_prompt = f"""
        Explain why this job matches (or doesn't match) this user profile.
        Provide reasoning in Hindi for better user understanding.
        
        Job: {job_data.get('title', 'Unknown')}
        Match Score: {base_match}%
        
        User: Age {user_profile.get('age', '?')}, {user_profile.get('education', '?')} educated, from {user_profile.get('state', '?')}
        
        {web_context}
        
        Provide brief, clear reasoning (2-3 points in Hindi).
        """
        
        reasoning_response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": reasoning_prompt}],
            temperature=0.5
        )
        
        return {
            "match_score": base_match,
            "reasoning": reasoning_response.choices[0].message.content,
            "learned": False,
            "web_search_used": use_web_search
        }
    
    async def _calculate_base_match(self, job_data: Dict, user_profile: Dict) -> float:
        """Basic matching logic"""
        score = 50.0
        
        # Education match
        if job_data.get('education') == user_profile.get('education'):
            score += 20
        
        # Age match
        user_age = user_profile.get('age', 0)
        min_age = job_data.get('min_age', 18)
        max_age = job_data.get('max_age', 40)
        if min_age <= user_age <= max_age:
            score += 15
        
        # State match
        if job_data.get('state') == user_profile.get('state'):
            score += 15
        
        return min(score, 100.0)
