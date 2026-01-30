"""
DS-Search Query Generator
=========================
Generates optimized search queries in Hindi and English.

For each user query, generates 2-4 search queries:
1. Hindi version
2. English version
3. "Official only" version
4. "site:gov.in" version

Handles:
- Job queries
- Yojana queries
- Result queries
- General queries
"""

import re
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class GeneratedQuery:
    """A generated search query"""
    text: str
    language: str  # 'hi', 'en', 'gov'
    query_type: str  # 'job', 'yojana', 'result', 'general'
    priority: int  # 1-4, 1 being highest


class QueryGenerator:
    """
    Intelligent query generator for DS-Search.
    Generates multiple optimized queries from user input.
    """
    
    # Filler words to remove
    FILLER_WORDS_HI = [
        'bhai', 'भाई', 'yaar', 'यार', 'please', 'प्लीज', 
        'batao', 'बताओ', 'bata', 'बता', 'do', 'दो',
        'kya', 'क्या', 'hai', 'है', 'hain', 'हैं',
        'mujhe', 'मुझे', 'humko', 'हमको', 'hamein', 'हमें',
        'chahiye', 'चाहिए', 'chahie', 'dikhao', 'दिखाओ',
        'na', 'ना', 'ji', 'जी', 'sir', 'सर', 'madam', 'मैडम'
    ]
    
    FILLER_WORDS_EN = [
        'please', 'kindly', 'can', 'you', 'tell', 'me', 'about',
        'what', 'is', 'are', 'the', 'a', 'an', 'show', 'give',
        'i', 'want', 'need', 'looking', 'for', 'find', 'help'
    ]
    
    # Query templates by type
    JOB_TEMPLATES = {
        'hi': "{keyword} भर्ती {state} {year} अंतिम तिथि आधिकारिक वेबसाइट",
        'en': "{keyword} recruitment {state} {year} last date official notification",
        'gov': 'site:gov.in {keyword} recruitment {state} notification {year}'
    }
    
    YOJANA_TEMPLATES = {
        'hi': "{yojana_name} योजना पात्रता दस्तावेज आवेदन लिंक आधिकारिक",
        'en': "{yojana_name} scheme eligibility documents apply link official",
        'gov': 'site:gov.in "{yojana_name}" apply eligibility documents'
    }
    
    RESULT_TEMPLATES = {
        'hi': "{exam_name} रिजल्ट {year} लिंक आधिकारिक",
        'en': "{exam_name} result {year} official link direct",
        'gov': 'site:gov.in "{exam_name}" result {year}'
    }
    
    ADMIT_CARD_TEMPLATES = {
        'hi': "{exam_name} एडमिट कार्ड {year} डाउनलोड लिंक",
        'en': "{exam_name} admit card {year} download link official",
        'gov': 'site:gov.in "{exam_name}" admit card download {year}'
    }
    
    CUTOFF_TEMPLATES = {
        'hi': "{exam_name} कटऑफ {year} श्रेणीवार",
        'en': "{exam_name} cutoff {year} category wise expected",
        'gov': 'site:gov.in "{exam_name}" cutoff marks {year}'
    }
    
    SYLLABUS_TEMPLATES = {
        'hi': "{exam_name} सिलेबस {year} परीक्षा पैटर्न",
        'en': "{exam_name} syllabus {year} exam pattern topics",
        'gov': 'site:gov.in "{exam_name}" syllabus exam pattern'
    }
    
    # Entity extraction patterns
    EXAM_PATTERNS = [
        r'(ssc\s*(cgl|chsl|mts|gd|stenographer|je))',
        r'(upsc\s*(cse|ias|ips|nda|cds|capf|epfo))',
        r'(rrb\s*(ntpc|alp|je|group\s*d))',
        r'(ibps\s*(po|clerk|so|rrb))',
        r'(neet|jee\s*(main|advanced)?|gate|cat|mat)',
        r'(ctet|stet|tet|net|set)',
        r'(bihar\s*board|bseb|cbse|icse)',
        r'(police\s*(constable|si)|army|navy|airforce)',
    ]
    
    STATE_MAPPING = {
        'bihar': 'Bihar', 'बिहार': 'Bihar',
        'up': 'Uttar Pradesh', 'uttar pradesh': 'Uttar Pradesh', 'उत्तर प्रदेश': 'Uttar Pradesh',
        'mp': 'Madhya Pradesh', 'madhya pradesh': 'Madhya Pradesh', 'मध्य प्रदेश': 'Madhya Pradesh',
        'rajasthan': 'Rajasthan', 'राजस्थान': 'Rajasthan',
        'maharashtra': 'Maharashtra', 'महाराष्ट्र': 'Maharashtra',
        'gujarat': 'Gujarat', 'गुजरात': 'Gujarat',
        'delhi': 'Delhi', 'दिल्ली': 'Delhi',
        'haryana': 'Haryana', 'हरियाणा': 'Haryana',
        'punjab': 'Punjab', 'पंजाब': 'Punjab',
        'jharkhand': 'Jharkhand', 'झारखंड': 'Jharkhand',
        'chhattisgarh': 'Chhattisgarh', 'छत्तीसगढ़': 'Chhattisgarh',
        'odisha': 'Odisha', 'ओडिशा': 'Odisha',
        'west bengal': 'West Bengal', 'पश्चिम बंगाल': 'West Bengal',
        'tamil nadu': 'Tamil Nadu', 'तमिलनाडु': 'Tamil Nadu',
        'karnataka': 'Karnataka', 'कर्नाटक': 'Karnataka',
        'kerala': 'Kerala', 'केरल': 'Kerala',
        'telangana': 'Telangana', 'तेलंगाना': 'Telangana',
        'andhra pradesh': 'Andhra Pradesh', 'आंध्र प्रदेश': 'Andhra Pradesh',
        'assam': 'Assam', 'असम': 'Assam',
    }
    
    YOJANA_MAPPING = {
        'pm kisan': 'PM Kisan Samman Nidhi',
        'पीएम किसान': 'PM Kisan Samman Nidhi',
        'pmkisan': 'PM Kisan Samman Nidhi',
        'ayushman': 'Ayushman Bharat',
        'आयुष्मान': 'Ayushman Bharat',
        'ujjwala': 'PM Ujjwala Yojana',
        'उज्ज्वला': 'PM Ujjwala Yojana',
        'mudra': 'PM MUDRA Yojana',
        'मुद्रा': 'PM MUDRA Yojana',
        'awas': 'PM Awas Yojana',
        'आवास': 'PM Awas Yojana',
        'jan dhan': 'Jan Dhan Yojana',
        'जन धन': 'Jan Dhan Yojana',
        'sukanya': 'Sukanya Samriddhi Yojana',
        'सुकन्या': 'Sukanya Samriddhi Yojana',
        'kaushal vikas': 'PM Kaushal Vikas Yojana',
        'कौशल विकास': 'PM Kaushal Vikas Yojana',
        'fasal bima': 'PM Fasal Bima Yojana',
        'फसल बीमा': 'PM Fasal Bima Yojana',
    }
    
    def __init__(self):
        self.current_year = datetime.now().year
    
    def clean_query(self, query: str) -> str:
        """
        Remove filler words and clean the query.
        
        Args:
            query: Raw user query
            
        Returns:
            Cleaned query
        """
        query_lower = query.lower()
        
        # Remove filler words
        words = query_lower.split()
        cleaned_words = []
        
        for word in words:
            word_clean = word.strip('?!.,')
            if word_clean not in self.FILLER_WORDS_HI and word_clean not in self.FILLER_WORDS_EN:
                cleaned_words.append(word_clean)
        
        return ' '.join(cleaned_words)
    
    def extract_entities(self, query: str) -> Dict[str, Optional[str]]:
        """
        Extract key entities from query (exam, state, year, yojana).
        
        Args:
            query: User query
            
        Returns:
            Dict with extracted entities
        """
        query_lower = query.lower()
        entities = {
            'exam': None,
            'state': None,
            'year': None,
            'yojana': None,
            'keyword': None
        }
        
        # Extract exam name
        for pattern in self.EXAM_PATTERNS:
            match = re.search(pattern, query_lower, re.IGNORECASE)
            if match:
                entities['exam'] = match.group().upper().replace('  ', ' ')
                break
        
        # Extract state
        for state_key, state_value in self.STATE_MAPPING.items():
            if state_key in query_lower:
                entities['state'] = state_value
                break
        
        # Extract year
        year_match = re.search(r'(202[4-9]|203[0-5])', query)
        if year_match:
            entities['year'] = year_match.group()
        else:
            entities['year'] = str(self.current_year)
        
        # Extract yojana
        for yojana_key, yojana_value in self.YOJANA_MAPPING.items():
            if yojana_key in query_lower:
                entities['yojana'] = yojana_value
                break
        
        # Extract main keyword (first significant noun)
        cleaned = self.clean_query(query)
        if cleaned:
            entities['keyword'] = cleaned.split()[0] if cleaned.split() else query[:20]
        
        return entities
    
    def detect_query_type(self, query: str) -> str:
        """
        Detect the type of query.
        
        Args:
            query: User query
            
        Returns:
            Query type string
        """
        query_lower = query.lower()
        
        # Result query
        if re.search(r'(result|रिजल्ट|परिणाम|merit|answer\s*key)', query_lower):
            return 'result'
        
        # Admit card query
        if re.search(r'(admit\s*card|एडमिट\s*कार्ड|hall\s*ticket)', query_lower):
            return 'admit_card'
        
        # Cutoff query
        if re.search(r'(cutoff|cut\s*off|कटऑफ|cut\s*off\s*marks)', query_lower):
            return 'cutoff'
        
        # Syllabus query
        if re.search(r'(syllabus|सिलेबस|pattern|पैटर्न|topics)', query_lower):
            return 'syllabus'
        
        # Yojana query
        if re.search(r'(yojana|योजना|scheme|subsidy|pension)', query_lower):
            return 'yojana'
        
        # Job/recruitment query
        if re.search(r'(vacancy|भर्ती|recruitment|job|नौकरी|bharti)', query_lower):
            return 'job'
        
        return 'general'
    
    def generate(self, query: str, query_type: str = None) -> List[GeneratedQuery]:
        """
        Generate multiple search queries from user input.
        
        Args:
            query: User's original query
            query_type: Optional query type override
            
        Returns:
            List of GeneratedQuery objects
        """
        # Clean and extract entities
        entities = self.extract_entities(query)
        
        # Detect query type if not provided
        if not query_type:
            query_type = self.detect_query_type(query)
        
        generated = []
        
        # Select templates based on query type
        if query_type == 'job':
            generated.extend(self._generate_job_queries(entities))
        elif query_type == 'yojana':
            generated.extend(self._generate_yojana_queries(entities))
        elif query_type == 'result':
            generated.extend(self._generate_result_queries(entities))
        elif query_type == 'admit_card':
            generated.extend(self._generate_admit_queries(entities))
        elif query_type == 'cutoff':
            generated.extend(self._generate_cutoff_queries(entities))
        elif query_type == 'syllabus':
            generated.extend(self._generate_syllabus_queries(entities))
        else:
            generated.extend(self._generate_general_queries(query, entities))
        
        # Always add a cleaned version of original query
        cleaned = self.clean_query(query)
        if cleaned and not any(g.text.lower() == cleaned.lower() for g in generated):
            generated.append(GeneratedQuery(
                text=cleaned,
                language='mixed',
                query_type=query_type,
                priority=4
            ))
        
        logger.info(f"Generated {len(generated)} queries for: {query[:50]}...")
        return generated
    
    def _generate_job_queries(self, entities: Dict) -> List[GeneratedQuery]:
        """Generate job-related queries"""
        queries = []
        
        keyword = entities.get('exam') or entities.get('keyword') or 'government'
        state = entities.get('state') or ''
        year = entities.get('year') or str(self.current_year)
        
        # Hindi query
        queries.append(GeneratedQuery(
            text=self.JOB_TEMPLATES['hi'].format(
                keyword=keyword, state=state, year=year
            ).strip(),
            language='hi',
            query_type='job',
            priority=1
        ))
        
        # English query
        queries.append(GeneratedQuery(
            text=self.JOB_TEMPLATES['en'].format(
                keyword=keyword, state=state, year=year
            ).strip(),
            language='en',
            query_type='job',
            priority=2
        ))
        
        # Government site only
        queries.append(GeneratedQuery(
            text=self.JOB_TEMPLATES['gov'].format(
                keyword=keyword, state=state, year=year
            ).strip(),
            language='gov',
            query_type='job',
            priority=3
        ))
        
        return queries
    
    def _generate_yojana_queries(self, entities: Dict) -> List[GeneratedQuery]:
        """Generate yojana-related queries"""
        queries = []
        
        yojana_name = entities.get('yojana') or entities.get('keyword') or 'government scheme'
        
        # Hindi query
        queries.append(GeneratedQuery(
            text=self.YOJANA_TEMPLATES['hi'].format(yojana_name=yojana_name).strip(),
            language='hi',
            query_type='yojana',
            priority=1
        ))
        
        # English query
        queries.append(GeneratedQuery(
            text=self.YOJANA_TEMPLATES['en'].format(yojana_name=yojana_name).strip(),
            language='en',
            query_type='yojana',
            priority=2
        ))
        
        # Government site only
        queries.append(GeneratedQuery(
            text=self.YOJANA_TEMPLATES['gov'].format(yojana_name=yojana_name).strip(),
            language='gov',
            query_type='yojana',
            priority=3
        ))
        
        return queries
    
    def _generate_result_queries(self, entities: Dict) -> List[GeneratedQuery]:
        """Generate result-related queries"""
        queries = []
        
        exam_name = entities.get('exam') or entities.get('keyword') or 'exam'
        year = entities.get('year') or str(self.current_year)
        
        # Hindi query
        queries.append(GeneratedQuery(
            text=self.RESULT_TEMPLATES['hi'].format(exam_name=exam_name, year=year).strip(),
            language='hi',
            query_type='result',
            priority=1
        ))
        
        # English query
        queries.append(GeneratedQuery(
            text=self.RESULT_TEMPLATES['en'].format(exam_name=exam_name, year=year).strip(),
            language='en',
            query_type='result',
            priority=2
        ))
        
        # Government site only
        queries.append(GeneratedQuery(
            text=self.RESULT_TEMPLATES['gov'].format(exam_name=exam_name, year=year).strip(),
            language='gov',
            query_type='result',
            priority=3
        ))
        
        return queries
    
    def _generate_admit_queries(self, entities: Dict) -> List[GeneratedQuery]:
        """Generate admit card queries"""
        queries = []
        
        exam_name = entities.get('exam') or entities.get('keyword') or 'exam'
        year = entities.get('year') or str(self.current_year)
        
        for lang, template in self.ADMIT_CARD_TEMPLATES.items():
            queries.append(GeneratedQuery(
                text=template.format(exam_name=exam_name, year=year).strip(),
                language=lang,
                query_type='admit_card',
                priority=1 if lang == 'hi' else (2 if lang == 'en' else 3)
            ))
        
        return queries
    
    def _generate_cutoff_queries(self, entities: Dict) -> List[GeneratedQuery]:
        """Generate cutoff queries"""
        queries = []
        
        exam_name = entities.get('exam') or entities.get('keyword') or 'exam'
        year = entities.get('year') or str(self.current_year)
        
        for lang, template in self.CUTOFF_TEMPLATES.items():
            queries.append(GeneratedQuery(
                text=template.format(exam_name=exam_name, year=year).strip(),
                language=lang,
                query_type='cutoff',
                priority=1 if lang == 'hi' else (2 if lang == 'en' else 3)
            ))
        
        return queries
    
    def _generate_syllabus_queries(self, entities: Dict) -> List[GeneratedQuery]:
        """Generate syllabus queries"""
        queries = []
        
        exam_name = entities.get('exam') or entities.get('keyword') or 'exam'
        year = entities.get('year') or str(self.current_year)
        
        for lang, template in self.SYLLABUS_TEMPLATES.items():
            queries.append(GeneratedQuery(
                text=template.format(exam_name=exam_name, year=year).strip(),
                language=lang,
                query_type='syllabus',
                priority=1 if lang == 'hi' else (2 if lang == 'en' else 3)
            ))
        
        return queries
    
    def _generate_general_queries(self, original: str, entities: Dict) -> List[GeneratedQuery]:
        """Generate general queries when type is unknown"""
        queries = []
        cleaned = self.clean_query(original)
        
        # Original cleaned
        queries.append(GeneratedQuery(
            text=cleaned,
            language='mixed',
            query_type='general',
            priority=1
        ))
        
        # With "official" suffix
        queries.append(GeneratedQuery(
            text=f"{cleaned} official website",
            language='en',
            query_type='general',
            priority=2
        ))
        
        # Gov.in only
        queries.append(GeneratedQuery(
            text=f"site:gov.in {cleaned}",
            language='gov',
            query_type='general',
            priority=3
        ))
        
        return queries


# Singleton instance
_querygen_instance: Optional[QueryGenerator] = None

def get_querygen_instance() -> QueryGenerator:
    """Get or create query generator instance"""
    global _querygen_instance
    if _querygen_instance is None:
        _querygen_instance = QueryGenerator()
    return _querygen_instance
