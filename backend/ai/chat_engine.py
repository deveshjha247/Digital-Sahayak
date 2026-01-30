"""
Digital Sahayak AI Chat Engine
==============================
Independent conversational AI system similar to ChatGPT/Gemini.
Works standalone without external API dependencies.

Features:
- Multi-turn conversation with memory
- Hindi + English bilingual support
- Context-aware responses about jobs, schemes, government
- Integration with project knowledge base
- Web search for real-time information (like ChatGPT/Gemini)
- Self-learning from web searches
"""

import asyncio
import re
import json
import hashlib
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field, asdict
import logging

# Web search imports
try:
    import httpx
    from bs4 import BeautifulSoup
    WEB_SEARCH_AVAILABLE = True
except ImportError:
    WEB_SEARCH_AVAILABLE = False

# Try to use duckduckgo-search library (more reliable)
try:
    from duckduckgo_search import DDGS
    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    WEB_SEARCH_AVAILABLE = False

logger = logging.getLogger(__name__)

# ===================== DATA CLASSES =====================

@dataclass
class ChatMessage:
    """Single message in conversation"""
    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }

@dataclass
class Conversation:
    """Multi-turn conversation session"""
    id: str
    user_id: str
    messages: List[ChatMessage] = field(default_factory=list)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    title: Optional[str] = None
    
    def add_message(self, role: str, content: str, metadata: Dict = None):
        msg = ChatMessage(role=role, content=content, metadata=metadata or {})
        self.messages.append(msg)
        self.updated_at = datetime.now(timezone.utc)
        
        # Auto-generate title from first user message
        if not self.title and role == 'user':
            self.title = content[:50] + ('...' if len(content) > 50 else '')
    
    def get_context(self, max_messages: int = 10) -> List[Dict]:
        """Get recent messages for context"""
        return [m.to_dict() for m in self.messages[-max_messages:]]
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "messages": [m.to_dict() for m in self.messages],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "title": self.title
        }


# ===================== KNOWLEDGE BASE =====================

class KnowledgeBase:
    """
    Built-in knowledge about Digital Sahayak domain.
    No external API needed - works completely offline.
    """
    
    # Government schemes knowledge
    SCHEMES_KNOWLEDGE = {
        "pm_kisan": {
            "name": "PM-KISAN",
            "full_name": "Pradhan Mantri Kisan Samman Nidhi",
            "hindi": "प्रधानमंत्री किसान सम्मान निधि",
            "benefit": "₹6,000 per year in 3 installments",
            "eligibility": ["Small and marginal farmers", "Land holding requirement"],
            "documents": ["Aadhar Card", "Land Records", "Bank Account"]
        },
        "ayushman_bharat": {
            "name": "Ayushman Bharat",
            "hindi": "आयुष्मान भारत",
            "benefit": "₹5 Lakh health coverage per family",
            "eligibility": ["BPL families", "SECC database listed"],
            "documents": ["Aadhar Card", "Ration Card", "Income Certificate"]
        },
        "ujjwala": {
            "name": "PM Ujjwala Yojana",
            "hindi": "प्रधानमंत्री उज्ज्वला योजना",
            "benefit": "Free LPG connection",
            "eligibility": ["BPL women", "No existing LPG connection"],
            "documents": ["Aadhar Card", "BPL Card", "Bank Account"]
        },
        "mudra": {
            "name": "PM MUDRA Yojana",
            "hindi": "प्रधानमंत्री मुद्रा योजना",
            "benefit": "Loans up to ₹10 Lakh for small businesses",
            "categories": ["Shishu (up to ₹50,000)", "Kishore (₹50,000-5 Lakh)", "Tarun (5-10 Lakh)"],
            "eligibility": ["Small business owners", "Non-farm income generating activities"]
        }
    }
    
    # Job categories knowledge
    JOB_CATEGORIES = {
        "sarkari_naukri": {
            "name": "Government Jobs",
            "hindi": "सरकारी नौकरी",
            "types": ["SSC", "UPSC", "Railway", "Bank", "State PSC", "Defence"],
            "benefits": ["Job security", "Pension", "Medical benefits", "DA/HRA"]
        },
        "private_jobs": {
            "name": "Private Sector Jobs",
            "hindi": "प्राइवेट नौकरी",
            "sectors": ["IT", "Banking", "Healthcare", "Manufacturing", "Retail"]
        },
        "apprenticeship": {
            "name": "Apprenticeship",
            "hindi": "अप्रेंटिसशिप",
            "portal": "apprenticeshipindia.gov.in",
            "stipend": "As per NAPS guidelines"
        }
    }
    
    # Document types
    DOCUMENTS = {
        "aadhar": {"name": "Aadhar Card", "hindi": "आधार कार्ड", "pattern": r"\d{4}\s?\d{4}\s?\d{4}"},
        "pan": {"name": "PAN Card", "hindi": "पैन कार्ड", "pattern": r"[A-Z]{5}\d{4}[A-Z]"},
        "voter_id": {"name": "Voter ID", "hindi": "वोटर आईडी", "pattern": r"[A-Z]{3}\d{7}"},
        "ration_card": {"name": "Ration Card", "hindi": "राशन कार्ड"},
        "income_certificate": {"name": "Income Certificate", "hindi": "आय प्रमाण पत्र"},
        "caste_certificate": {"name": "Caste Certificate", "hindi": "जाति प्रमाण पत्र"},
        "domicile": {"name": "Domicile Certificate", "hindi": "मूल निवास प्रमाण पत्र"}
    }
    
    # Common intents and responses
    INTENT_RESPONSES = {
        "greeting": {
            "patterns": ["hello", "hi", "namaste", "नमस्ते", "हेलो", "hey"],
            "responses": [
                "नमस्ते! 🙏 मैं Digital Sahayak AI हूं। मैं आपकी सरकारी योजनाओं और नौकरियों में मदद कर सकता हूं। कैसे मदद करूं?",
                "Hello! 🙏 I'm Digital Sahayak AI. I can help you with government schemes, jobs, and applications. How can I assist you today?"
            ]
        },
        "scheme_inquiry": {
            "patterns": ["yojana", "scheme", "योजना", "benefit", "subsidy", "सब्सिडी"],
            "responses": [
                "मैं आपको सरकारी योजनाओं के बारे में जानकारी दे सकता हूं। किस योजना के बारे में जानना चाहते हैं?\n\n📋 Popular Schemes:\n• PM-KISAN (किसान सम्मान निधि)\n• Ayushman Bharat (आयुष्मान भारत)\n• PM Ujjwala Yojana\n• MUDRA Yojana"
            ]
        },
        "job_search": {
            "patterns": ["job", "naukri", "नौकरी", "vacancy", "recruitment", "भर्ती"],
            "responses": [
                "मैं आपको नौकरियां ढूंढने में मदद कर सकता हूं! 💼\n\n🔍 Available Categories:\n• सरकारी नौकरी (Government)\n• प्राइवेट जॉब्स (Private)\n• Apprenticeship\n\nआप किस तरह की नौकरी ढूंढ रहे हैं? अपनी qualification और location बताएं।"
            ]
        },
        "document_help": {
            "patterns": ["document", "दस्तावेज़", "aadhar", "आधार", "pan", "पैन", "certificate"],
            "responses": [
                "Documents के बारे में मदद चाहिए? 📄\n\nमैं इन documents में help कर सकता हूं:\n• Aadhar Card (आधार कार्ड)\n• PAN Card (पैन कार्ड)\n• Income Certificate (आय प्रमाण पत्र)\n• Caste Certificate (जाति प्रमाण पत्र)\n• Domicile (मूल निवास)\n\nकौन सा document चाहिए?"
            ]
        },
        "application_status": {
            "patterns": ["status", "स्टेटस", "track", "application", "आवेदन"],
            "responses": [
                "Application status check करने के लिए:\n\n1️⃣ Dashboard पर जाएं\n2️⃣ 'My Applications' section देखें\n3️⃣ Application ID से track करें\n\nक्या आप किसी specific application का status जानना चाहते हैं?"
            ]
        },
        "eligibility": {
            "patterns": ["eligible", "eligibility", "पात्र", "पात्रता", "qualify", "criteria"],
            "responses": [
                "Eligibility check करने के लिए मुझे कुछ जानकारी चाहिए:\n\n📝 Please share:\n• आपकी उम्र (Age)\n• शिक्षा (Education)\n• राज्य (State)\n• Annual Income\n\nइससे मैं सही योजनाएं suggest कर पाऊंगा।"
            ]
        },
        "thanks": {
            "patterns": ["thanks", "thank you", "धन्यवाद", "शुक्रिया", "shukriya"],
            "responses": [
                "आपका स्वागत है! 🙏 और कोई मदद चाहिए तो बताइए।",
                "You're welcome! Feel free to ask if you need any more help. 😊"
            ]
        },
        "bye": {
            "patterns": ["bye", "goodbye", "alvida", "अलविदा", "बाय"],
            "responses": [
                "अलविदा! 👋 Digital Sahayak पर आने के लिए धन्यवाद। जब भी ज़रूरत हो, वापस आइए!",
                "Goodbye! Thank you for using Digital Sahayak. Come back anytime you need help! 🙏"
            ]
        }
    }
    
    @classmethod
    def get_scheme_info(cls, scheme_key: str) -> Optional[Dict]:
        """Get information about a specific scheme"""
        return cls.SCHEMES_KNOWLEDGE.get(scheme_key.lower().replace(" ", "_").replace("-", "_"))
    
    @classmethod
    def search_schemes(cls, query: str) -> List[Dict]:
        """Search schemes by keyword"""
        query_lower = query.lower()
        results = []
        for key, scheme in cls.SCHEMES_KNOWLEDGE.items():
            if (query_lower in key or 
                query_lower in scheme.get('name', '').lower() or
                query_lower in scheme.get('hindi', '').lower()):
                results.append(scheme)
        return results
    
    @classmethod
    def detect_intent(cls, text: str) -> tuple:
        """Detect user intent from text"""
        text_lower = text.lower()
        
        for intent, data in cls.INTENT_RESPONSES.items():
            for pattern in data['patterns']:
                if pattern in text_lower:
                    return intent, data['responses']
        
        return 'general', None


# ===================== WEB SEARCH ENGINE =====================

class WebSearchEngine:
    """
    Web search capability for real-time information.
    Uses DuckDuckGo (no API key required) - just like ChatGPT/Gemini.
    """
    
    def __init__(self, db=None):
        self.db = db
        self.cache_duration = timedelta(hours=6)  # Cache results for 6 hours
    
    async def search(self, query: str, num_results: int = 5) -> List[Dict]:
        """
        Search the web using DuckDuckGo.
        
        Args:
            query: Search query
            num_results: Number of results to return
            
        Returns:
            List of search results with title, url, snippet
        """
        if not WEB_SEARCH_AVAILABLE:
            logger.warning("Web search not available - httpx/bs4 not installed")
            return []
        
        # Check cache first
        cached = await self._get_cached_results(query)
        if cached:
            logger.info(f"Using cached search results for: {query}")
            return cached
        
        try:
            # DuckDuckGo HTML search (no API needed) - Use POST method
            search_url = "https://html.duckduckgo.com/html/"
            
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                # POST with form data
                response = await client.post(
                    search_url,
                    data={"q": query},
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                        "Accept-Language": "en-US,en;q=0.5",
                        "Referer": "https://html.duckduckgo.com/"
                    }
                )
                
                if response.status_code not in [200, 202]:
                    logger.error(f"Search failed with status {response.status_code}")
                    return []
                
                # Parse results
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Try multiple selector patterns for DuckDuckGo
                result_elements = soup.select('.result') or soup.select('.web-result') or soup.select('.results_links')
                
                for result in result_elements[:num_results]:
                    title_elem = result.select_one('.result__title') or result.select_one('.result__a') or result.select_one('a.result__url')
                    snippet_elem = result.select_one('.result__snippet') or result.select_one('.result__body')
                    url_elem = result.select_one('.result__url') or result.select_one('.result__extras__url')
                    
                    title = ""
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    
                    # Also try to get link text
                    if not title:
                        link = result.find('a')
                        if link:
                            title = link.get_text(strip=True)
                    
                    if title:
                        results.append({
                            "title": title,
                            "url": url_elem.get_text(strip=True) if url_elem else "",
                            "snippet": snippet_elem.get_text(strip=True) if snippet_elem else ""
                        })
                
                # If no results from selectors, try alternative parsing
                if not results:
                    # Find all links with result data
                    for link in soup.find_all('a', {'class': lambda x: x and 'result' in x.lower() if x else False}):
                        title = link.get_text(strip=True)
                        href = link.get('href', '')
                        if title and len(title) > 10:
                            results.append({
                                "title": title[:100],
                                "url": href[:100] if href else "",
                                "snippet": ""
                            })
                        if len(results) >= num_results:
                            break
                
                # Cache results
                if results:
                    await self._cache_results(query, results)
                
                logger.info(f"Web search found {len(results)} results for: {query}")
                return results
                
        except Exception as e:
            logger.error(f"Web search error: {e}")
            return []
    
    async def fetch_page_content(self, url: str, max_length: int = 5000) -> str:
        """
        Fetch and extract main content from a webpage.
        
        Args:
            url: URL to fetch
            max_length: Maximum content length to return
            
        Returns:
            Extracted text content
        """
        if not WEB_SEARCH_AVAILABLE:
            return ""
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url,
                    headers={
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                    },
                    follow_redirects=True
                )
                
                if response.status_code != 200:
                    return ""
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove script and style elements
                for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                    element.decompose()
                
                # Extract text
                text = soup.get_text(separator=' ', strip=True)
                
                # Clean up
                text = re.sub(r'\s+', ' ', text)
                
                return text[:max_length]
                
        except Exception as e:
            logger.error(f"Page fetch error: {e}")
            return ""
    
    async def _get_cached_results(self, query: str) -> Optional[List[Dict]]:
        """Get cached search results if available and not expired"""
        if self.db is None:
            return None
        
        try:
            cache_key = hashlib.md5(query.lower().encode()).hexdigest()
            cached = await self.db.ai_search_cache.find_one({"cache_key": cache_key})
            
            if cached:
                cached_time = cached.get('timestamp')
                if isinstance(cached_time, str):
                    cached_time = datetime.fromisoformat(cached_time)
                
                if datetime.now(timezone.utc) - cached_time.replace(tzinfo=timezone.utc) < self.cache_duration:
                    return cached.get('results', [])
            
            return None
        except Exception as e:
            logger.error(f"Cache read error: {e}")
            return None
    
    async def _cache_results(self, query: str, results: List[Dict]):
        """Cache search results"""
        if self.db is None:
            return
        
        try:
            cache_key = hashlib.md5(query.lower().encode()).hexdigest()
            await self.db.ai_search_cache.update_one(
                {"cache_key": cache_key},
                {
                    "$set": {
                        "query": query,
                        "results": results,
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    }
                },
                upsert=True
            )
        except Exception as e:
            logger.error(f"Cache write error: {e}")


# ===================== AI RESPONSE GENERATOR =====================

class AIResponseGenerator:
    """
    Generates intelligent responses without external API.
    Uses template-based generation with smart context awareness.
    Now with web search capability for real-time information!
    """
    
    def __init__(self, db=None):
        self.kb = KnowledgeBase()
        self.web_search = WebSearchEngine(db)
        self.db = db
        
        # Patterns that indicate user needs real-time/web information
        self.web_search_triggers = [
            # Date/time related
            r"kab se|कब से|when|date|तारीख|schedule|time table",
            # Latest/current info
            r"latest|नया|new|current|अभी|recent|2024|2025|2026",
            # Result/notification related
            r"result|रिजल्ट|notification|नोटिफिकेशन|admit card|एडमिट",
            # Exam related
            r"exam|परीक्षा|board|बोर्ड|entrance|प्रवेश",
            # News/updates
            r"news|खबर|update|अपडेट|announcement|घोषणा",
            # Specific queries AI might not know
            r"salary|सैलरी|cutoff|कटऑफ|vacancy|रिक्ति|last date|अंतिम तिथि"
        ]
    
    def _needs_web_search(self, message: str) -> bool:
        """Check if the query needs web search for real-time info"""
        message_lower = message.lower()
        for pattern in self.web_search_triggers:
            if re.search(pattern, message_lower, re.IGNORECASE):
                return True
        return False
    
    async def generate_response_async(self, user_message: str, context: List[Dict] = None, 
                                      user_profile: Dict = None, language: str = "hi") -> str:
        """
        Generate AI response with web search capability (async version).
        """
        # Detect intent
        intent, preset_responses = self.kb.detect_intent(user_message)
        
        # Check for specific queries in knowledge base
        response = self._handle_specific_queries(user_message, user_profile, language)
        if response:
            return response
        
        # Use preset responses for known intents
        if preset_responses:
            import random
            return random.choice(preset_responses)
        
        # Check if web search is needed
        if self._needs_web_search(user_message):
            web_response = await self._search_and_respond(user_message, language)
            if web_response:
                return web_response
        
        # Generate contextual response
        return self._generate_contextual_response(user_message, context, user_profile, language)
    
    async def _search_and_respond(self, query: str, language: str) -> Optional[str]:
        """Search web and generate response from results"""
        try:
            # Enhance query for better results
            search_query = self._enhance_search_query(query)
            
            # Search the web
            results = await self.web_search.search(search_query, num_results=5)
            
            if not results:
                return None
            
            # Build response from search results
            response = self._build_response_from_search(query, results, language)
            
            # Store learned information
            await self._store_learned_info(query, results)
            
            return response
            
        except Exception as e:
            logger.error(f"Search and respond error: {e}")
            return None
    
    def _enhance_search_query(self, query: str) -> str:
        """Enhance user query for better search results"""
        # Add context for Indian government related queries
        query_lower = query.lower()
        
        # Board exam queries
        if "bihar board" in query_lower or "bseb" in query_lower:
            return f"{query} BSEB official 2026"
        
        # SSC queries
        if "ssc" in query_lower:
            return f"{query} ssc.nic.in official"
        
        # Railway queries
        if "railway" in query_lower or "rrb" in query_lower:
            return f"{query} indianrailways.gov.in official"
        
        # UPSC queries
        if "upsc" in query_lower:
            return f"{query} upsc.gov.in official"
        
        # Bank exams
        if "bank" in query_lower or "ibps" in query_lower:
            return f"{query} ibps.in official"
        
        # General government queries
        if any(word in query_lower for word in ["sarkari", "government", "govt", "सरकारी"]):
            return f"{query} official india.gov.in"
        
        return query
    
    def _build_response_from_search(self, original_query: str, results: List[Dict], language: str) -> str:
        """Build a helpful response from search results"""
        if not results:
            return None
        
        # Header
        if language == "hi":
            response = f"🔍 **आपके सवाल के लिए मैंने web search किया:**\n\n"
        else:
            response = f"🔍 **I searched the web for your question:**\n\n"
        
        # Add relevant information from results
        for i, result in enumerate(results[:3], 1):
            title = result.get('title', '')
            snippet = result.get('snippet', '')
            url = result.get('url', '')
            
            if title and snippet:
                response += f"**{i}. {title}**\n"
                response += f"   {snippet}\n"
                if url:
                    response += f"   🔗 Source: {url}\n"
                response += "\n"
        
        # Add helpful footer
        if language == "hi":
            response += "\n💡 *यह जानकारी web search से मिली है। Official website पर verify करें।*"
        else:
            response += "\n💡 *This information is from web search. Please verify on official website.*"
        
        return response
    
    async def _store_learned_info(self, query: str, results: List[Dict]):
        """Store learned information from web search"""
        if self.db is None:
            return
        
        try:
            await self.db.ai_learned_knowledge.insert_one({
                "query": query,
                "results": results,
                "learned_at": datetime.now(timezone.utc).isoformat(),
                "source": "web_search"
            })
            logger.info(f"Stored learned info for: {query}")
        except Exception as e:
            logger.error(f"Failed to store learned info: {e}")
    
    def generate_response(self, user_message: str, context: List[Dict] = None, 
                         user_profile: Dict = None, language: str = "hi") -> str:
        """
        Generate AI response based on user message and context.
        Sync version - for backward compatibility.
        
        Args:
            user_message: Current user message
            context: Previous conversation messages
            user_profile: User's profile data
            language: Preferred language (hi/en)
        
        Returns:
            AI generated response
        """
        # Detect intent
        intent, preset_responses = self.kb.detect_intent(user_message)
        
        # Check for specific queries
        response = self._handle_specific_queries(user_message, user_profile, language)
        if response:
            return response
        
        # Use preset responses for known intents
        if preset_responses:
            import random
            return random.choice(preset_responses)
        
        # For queries needing web search, return a message to use async version
        if self._needs_web_search(user_message):
            return "NEEDS_WEB_SEARCH"  # Signal to use async version
        
        # Generate contextual response
        return self._generate_contextual_response(user_message, context, user_profile, language)
    
    def _handle_specific_queries(self, message: str, user_profile: Dict, language: str) -> Optional[str]:
        """Handle specific types of queries"""
        message_lower = message.lower()
        
        # Scheme specific queries
        for scheme_key, scheme_data in KnowledgeBase.SCHEMES_KNOWLEDGE.items():
            if scheme_key.replace("_", " ") in message_lower or \
               scheme_data['name'].lower() in message_lower:
                return self._format_scheme_info(scheme_data, language)
        
        # Eligibility calculation
        if "eligible" in message_lower or "पात्र" in message_lower:
            if user_profile:
                return self._check_eligibility(user_profile, language)
        
        # Job specific
        if "ssc" in message_lower or "upsc" in message_lower or "railway" in message_lower:
            return self._get_job_info(message, language)
        
        # Document help
        for doc_key, doc_data in KnowledgeBase.DOCUMENTS.items():
            if doc_key in message_lower or doc_data['hindi'] in message:
                return self._format_document_info(doc_data, language)
        
        return None
    
    def _format_scheme_info(self, scheme: Dict, language: str) -> str:
        """Format scheme information"""
        if language == "hi":
            response = f"📋 **{scheme.get('hindi', scheme['name'])}**\n\n"
        else:
            response = f"📋 **{scheme['name']}**\n\n"
        
        response += f"💰 **Benefit**: {scheme.get('benefit', 'N/A')}\n\n"
        
        if 'eligibility' in scheme:
            response += "✅ **Eligibility**:\n"
            for item in scheme['eligibility']:
                response += f"  • {item}\n"
        
        if 'documents' in scheme:
            response += "\n📄 **Required Documents**:\n"
            for doc in scheme['documents']:
                response += f"  • {doc}\n"
        
        response += "\n💡 *आवेदन करने के लिए 'Apply Now' बटन पर क्लिक करें या मुझसे और जानकारी पूछें।*"
        
        return response
    
    def _format_document_info(self, doc: Dict, language: str) -> str:
        """Format document information"""
        response = f"📄 **{doc['name']}** ({doc['hindi']})\n\n"
        
        if 'pattern' in doc:
            response += f"🔢 Format: `{doc['pattern']}`\n\n"
        
        response += "📝 **कैसे बनवाएं**:\n"
        response += "1. नज़दीकी CSC (Common Service Centre) जाएं\n"
        response += "2. Online portal पर apply करें\n"
        response += "3. Required documents लेकर जाएं\n\n"
        response += "💡 *Digital Sahayak पर document upload करें for auto-verification*"
        
        return response
    
    def _check_eligibility(self, user_profile: Dict, language: str) -> str:
        """Check eligibility based on user profile"""
        eligible_schemes = []
        
        age = user_profile.get('age', 0)
        education = user_profile.get('education_level', '')
        state = user_profile.get('state', '')
        
        # Simple eligibility rules
        if age >= 18:
            eligible_schemes.append("PM-KISAN (if farmer)")
            eligible_schemes.append("Ayushman Bharat (if BPL)")
            eligible_schemes.append("MUDRA Yojana (for business)")
        
        if education in ['graduate', 'post_graduate']:
            eligible_schemes.append("SSC CGL (Graduate level)")
            eligible_schemes.append("Bank PO (Graduate level)")
        
        if education in ['12th', 'graduate', 'post_graduate']:
            eligible_schemes.append("SSC CHSL (12th pass)")
            eligible_schemes.append("Railway NTPC")
        
        if not eligible_schemes:
            return "आपकी profile अधूरी है। कृपया अपना profile complete करें ताकि मैं सही योजनाएं suggest कर सकूं। 📝"
        
        response = "📋 **आपके लिए संभावित योजनाएं/नौकरियां**:\n\n"
        for scheme in eligible_schemes:
            response += f"✅ {scheme}\n"
        
        response += "\n💡 *More accurate results के लिए अपना profile update करें।*"
        
        return response
    
    def _get_job_info(self, message: str, language: str) -> str:
        """Get job information"""
        message_lower = message.lower()
        
        if "ssc" in message_lower:
            return """📋 **SSC (Staff Selection Commission)**

🎯 **Popular Exams**:
• SSC CGL - Graduate Level (₹25,500 - ₹1,51,100)
• SSC CHSL - 12th Pass (₹25,500 - ₹81,100)
• SSC MTS - 10th Pass (₹18,000 - ₹56,900)
• SSC GD - Constable (₹21,700 - ₹69,100)

📅 **Exam Pattern**:
• Tier 1: Online (100 marks, 60 min)
• Tier 2: Online (200 marks, 120 min)
• Tier 3: Descriptive (pen & paper)

📝 **Apply**: ssc.nic.in

💡 *Latest notifications के लिए 'Jobs' section देखें।*"""

        elif "upsc" in message_lower:
            return """📋 **UPSC (Union Public Service Commission)**

🎯 **Major Exams**:
• Civil Services (IAS/IPS/IFS)
• CDS - Combined Defence Services
• NDA - National Defence Academy
• CAPF - Central Armed Police Forces

📅 **Civil Services Pattern**:
• Prelims: Objective (GS + CSAT)
• Mains: Descriptive (9 papers)
• Interview: Personality Test

📝 **Apply**: upsc.gov.in

💡 *Preparation tips के लिए मुझसे पूछें!*"""

        elif "railway" in message_lower:
            return """📋 **Railway Recruitment**

🎯 **Popular Posts**:
• RRB NTPC - Graduate Posts (₹35,400+)
• RRB Group D - 10th Pass (₹18,000+)
• RRB JE - Junior Engineer
• RRB ALP - Loco Pilot

📅 **Apply Process**:
1. RRB Zone website पर जाएं
2. One-time registration करें
3. Online form भरें
4. Admit card download करें

📝 **Websites**: rrbcdg.gov.in (zone-wise)

💡 *Railway jobs में 7th Pay Commission benefits मिलते हैं!*"""

        return "नौकरी की जानकारी के लिए 'Jobs' section देखें या specific exam का नाम बताएं। 💼"
    
    def _generate_contextual_response(self, message: str, context: List[Dict], 
                                       user_profile: Dict, language: str) -> str:
        """Generate contextual response for general queries"""
        
        # Check for question words
        question_words = ['what', 'how', 'when', 'where', 'why', 'which', 'who',
                         'क्या', 'कैसे', 'कब', 'कहाँ', 'क्यों', 'कौन', 'किसे']
        
        is_question = any(word in message.lower() for word in question_words) or message.endswith('?')
        
        if is_question:
            return self._answer_question(message, context, language)
        
        # Default helpful response
        return """मैं समझ गया! 🤔

मैं आपकी इन चीज़ों में मदद कर सकता हूं:

📋 **सरकारी योजनाएं** - PM-KISAN, Ayushman Bharat, etc.
💼 **नौकरियां** - Sarkari Naukri, Private Jobs
📄 **Documents** - Aadhar, PAN, Certificates
📝 **Application Help** - Form filling, status tracking

कृपया specific सवाल पूछें या बताएं आपको क्या जानना है। 😊"""

    def _answer_question(self, question: str, context: List[Dict], language: str) -> str:
        """Answer specific questions"""
        question_lower = question.lower()
        
        # How to apply
        if "apply" in question_lower or "आवेदन" in question_lower:
            return """📝 **Apply करने के Steps**:

1️⃣ **Scheme/Job चुनें** - Browse करें या search करें
2️⃣ **Eligibility देखें** - Requirements match करें
3️⃣ **Documents Ready करें** - List में दिए documents
4️⃣ **Form भरें** - Online या CSC के through
5️⃣ **Submit करें** - Payment (if any) और submit

💡 *Auto-fill feature से form भरना आसान होगा!*

क्या किसी specific scheme/job के लिए apply करना है?"""

        # Check status
        if "status" in question_lower or "स्थिति" in question_lower:
            return """🔍 **Application Status Check करें**:

1️⃣ Dashboard → My Applications
2️⃣ Application ID enter करें
3️⃣ Current status देखें

**Status Types**:
• 🟡 Pending - Under review
• 🟢 Approved - स्वीकृत
• 🔴 Rejected - कारण देखें
• 🔵 Processing - कार्यवाही जारी

Application ID बताएं, मैं help करता हूं।"""

        # Documents required
        if "document" in question_lower or "दस्तावेज़" in question_lower:
            return """📄 **आमतौर पर ज़रूरी Documents**:

✅ **Identity Proof**:
  • Aadhar Card (आधार कार्ड)
  • PAN Card (पैन कार्ड)
  • Voter ID (वोटर आईडी)

✅ **Address Proof**:
  • Aadhar Card
  • Utility Bills
  • Domicile Certificate

✅ **Education**:
  • Marksheets (10th, 12th)
  • Degree Certificate
  • Migration Certificate

✅ **Others**:
  • Passport Size Photo
  • Income Certificate
  • Caste Certificate (if applicable)

किस scheme/job के लिए documents चाहिए?"""

        return """अच्छा सवाल है! 🤔

मुझे थोड़ा और context चाहिए। कृपया बताएं:
• क्या यह किसी scheme के बारे में है?
• क्या यह job के बारे में है?
• क्या कोई specific document/process है?

मैं आपकी पूरी मदद करूंगा! 💪"""


# ===================== MAIN CHAT ENGINE =====================

class DigitalSahayakAI:
    """
    Main AI Chat Engine for Digital Sahayak.
    Provides ChatGPT/Gemini-like conversational experience.
    Now with web search capability for real-time information!
    """
    
    def __init__(self, db=None):
        self.db = db
        self.generator = AIResponseGenerator(db)  # Pass db for web search
        self.conversations: Dict[str, Conversation] = {}  # In-memory cache
        self.version = "2.1.0"  # Updated version with web search
    
    async def initialize(self, db):
        """Initialize with database connection"""
        self.db = db
        self.generator = AIResponseGenerator(db)  # Re-initialize with db
        logger.info(f"Digital Sahayak AI v{self.version} initialized with web search")
    
    def _generate_conversation_id(self, user_id: str) -> str:
        """Generate unique conversation ID"""
        timestamp = datetime.now(timezone.utc).isoformat()
        unique = hashlib.md5(f"{user_id}:{timestamp}".encode()).hexdigest()[:12]
        return f"conv_{unique}"
    
    async def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation"""
        conv_id = self._generate_conversation_id(user_id)
        conv = Conversation(id=conv_id, user_id=user_id)
        self.conversations[conv_id] = conv
        
        # Save to DB
        if self.db is not None:
            await self.db.ai_conversations.insert_one(conv.to_dict())
        
        return conv
    
    async def get_conversation(self, conv_id: str, user_id: str) -> Optional[Conversation]:
        """Get existing conversation"""
        # Check cache first
        if conv_id in self.conversations:
            conv = self.conversations[conv_id]
            if conv.user_id == user_id:
                return conv
        
        # Load from DB
        if self.db is not None:
            data = await self.db.ai_conversations.find_one({"id": conv_id, "user_id": user_id})
            if data:
                conv = Conversation(
                    id=data['id'],
                    user_id=data['user_id'],
                    created_at=datetime.fromisoformat(data['created_at']) if isinstance(data['created_at'], str) else data['created_at'],
                    title=data.get('title')
                )
                for msg_data in data.get('messages', []):
                    conv.messages.append(ChatMessage(
                        role=msg_data['role'],
                        content=msg_data['content'],
                        timestamp=datetime.fromisoformat(msg_data['timestamp']) if isinstance(msg_data['timestamp'], str) else datetime.now(timezone.utc),
                        metadata=msg_data.get('metadata', {})
                    ))
                self.conversations[conv_id] = conv
                return conv
        
        return None
    
    async def get_user_conversations(self, user_id: str, limit: int = 20) -> List[Dict]:
        """Get all conversations for a user"""
        if self.db is None:
            return []
        
        cursor = self.db.ai_conversations.find(
            {"user_id": user_id}
        ).sort("updated_at", -1).limit(limit)
        
        conversations = []
        async for doc in cursor:
            conversations.append({
                "id": doc['id'],
                "title": doc.get('title', 'New Chat'),
                "created_at": doc['created_at'],
                "updated_at": doc.get('updated_at', doc['created_at']),
                "message_count": len(doc.get('messages', []))
            })
        
        return conversations
    
    async def chat(self, user_id: str, message: str, conv_id: str = None,
                   user_profile: Dict = None, language: str = "hi") -> Dict:
        """
        Main chat method - processes user message and returns AI response.
        Now with web search capability for real-time information!
        
        Args:
            user_id: User's ID
            message: User's message
            conv_id: Existing conversation ID (optional)
            user_profile: User's profile for personalization
            language: Preferred language
        
        Returns:
            Dict with response, conversation_id, etc.
        """
        # Get or create conversation
        if conv_id:
            conversation = await self.get_conversation(conv_id, user_id)
        else:
            conversation = None
        
        if not conversation:
            conversation = await self.create_conversation(user_id)
        
        # Add user message
        conversation.add_message('user', message)
        
        # Get conversation context
        context = conversation.get_context(max_messages=8)
        
        # First try sync response (for known queries)
        ai_response = self.generator.generate_response(
            user_message=message,
            context=context,
            user_profile=user_profile,
            language=language
        )
        
        # If web search is needed, use async version
        used_web_search = False
        if ai_response == "NEEDS_WEB_SEARCH":
            ai_response = await self.generator.generate_response_async(
                user_message=message,
                context=context,
                user_profile=user_profile,
                language=language
            )
            used_web_search = True
        
        # Add AI response
        conversation.add_message('assistant', ai_response, metadata={
            "model": "digital-sahayak-ai",
            "version": self.version,
            "used_web_search": used_web_search
        })
        
        # Update in DB
        if self.db is not None:
            await self.db.ai_conversations.update_one(
                {"id": conversation.id},
                {"$set": conversation.to_dict()},
                upsert=True
            )
        
        return {
            "success": True,
            "conversation_id": conversation.id,
            "message": ai_response,
            "title": conversation.title,
            "model": "digital-sahayak-ai",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    async def delete_conversation(self, conv_id: str, user_id: str) -> bool:
        """Delete a conversation"""
        if conv_id in self.conversations:
            del self.conversations[conv_id]
        
        if self.db is not None:
            result = await self.db.ai_conversations.delete_one({
                "id": conv_id,
                "user_id": user_id
            })
            return result.deleted_count > 0
        
        return False
    
    async def clear_user_history(self, user_id: str) -> int:
        """Clear all conversations for a user"""
        # Clear from cache
        to_delete = [k for k, v in self.conversations.items() if v.user_id == user_id]
        for k in to_delete:
            del self.conversations[k]
        
        # Clear from DB
        if self.db is not None:
            result = await self.db.ai_conversations.delete_many({"user_id": user_id})
            return result.deleted_count
        
        return len(to_delete)


# ===================== SINGLETON INSTANCE =====================

# Global AI instance
digital_sahayak_ai = DigitalSahayakAI()


async def get_ai_instance(db=None) -> DigitalSahayakAI:
    """Get or initialize AI instance"""
    global digital_sahayak_ai
    if db is not None and digital_sahayak_ai.db is None:
        await digital_sahayak_ai.initialize(db)
    return digital_sahayak_ai
