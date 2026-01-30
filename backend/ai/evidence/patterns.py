"""
Regex Patterns for Evidence Extraction
======================================
Patterns to extract dates, fees, eligibility, documents from text.
Supports both Hindi and English content.
"""

import re
from typing import List, Dict, Tuple, Optional

# ===================== DATE PATTERNS =====================

DATE_PATTERNS = [
    # DD/MM/YYYY or DD-MM-YYYY
    r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    # DD Month YYYY (English)
    r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
    # DD Mon YYYY
    r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
    # Month DD, YYYY
    r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
    # Hindi dates
    r'(\d{1,2}\s+(?:जनवरी|फरवरी|मार्च|अप्रैल|मई|जून|जुलाई|अगस्त|सितंबर|अक्टूबर|नवंबर|दिसंबर)\s+\d{4})',
    # YYYY-MM-DD (ISO format)
    r'(\d{4}-\d{2}-\d{2})',
]

# Last date specific patterns
LAST_DATE_PATTERNS = [
    # English
    r'last\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'last\s+date[:\s]*(\d{1,2}\s+\w+\s+\d{4})',
    r'closing\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'deadline[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'apply\s+before[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'last\s+date\s+(?:to|of|for)\s+(?:apply|application|submission)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    # Hindi
    r'अंतिम\s+तिथि[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'आखिरी\s+तारीख[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'अंतिम\s+तारीख[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'आवेदन\s+की\s+अंतिम\s+तिथि[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
]

# Start date patterns
START_DATE_PATTERNS = [
    r'start(?:ing)?\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'application\s+start[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'form\s+(?:available|starts?)\s+(?:from)?[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'आवेदन\s+शुरू[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'प्रारंभ\s+तिथि[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
]

# Exam date patterns
EXAM_DATE_PATTERNS = [
    r'exam\s+date[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'examination\s+(?:on|date)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
    r'परीक्षा\s+(?:तिथि|तारीख)[:\s]*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
]

# ===================== FEE PATTERNS =====================

FEE_PATTERNS = [
    # Rs/INR amounts
    r'(?:Rs\.?|₹|INR)\s*(\d{1,6}(?:,\d{3})*(?:\.\d{2})?)',
    r'(\d{1,6}(?:,\d{3})*)\s*(?:Rs\.?|₹|INR|rupees?)',
    # Fee specific
    r'(?:application\s+)?fee[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    r'(?:examination\s+)?fee[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    # Hindi
    r'शुल्क[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    r'फीस[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    r'आवेदन\s+शुल्क[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
]

# Category-wise fee patterns
CATEGORY_FEE_PATTERNS = {
    'general': [
        r'(?:general|ur|unreserved)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
        r'(?:सामान्य|जनरल)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    ],
    'obc': [
        r'(?:obc|other\s+backward)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
        r'(?:ओबीसी|अन्य\s+पिछड़ा)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    ],
    'sc_st': [
        r'(?:sc|st|sc/st)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
        r'(?:अनुसूचित\s+जाति|अनुसूचित\s+जनजाति)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    ],
    'ews': [
        r'(?:ews|economically\s+weaker)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    ],
    'female': [
        r'(?:female|women|mahila)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
        r'(?:महिला)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    ],
    'pwd': [
        r'(?:pwd|ph|divyang)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
        r'(?:दिव्यांग)[:\s]*(?:Rs\.?|₹)?\s*(\d+)',
    ],
}

# ===================== ELIGIBILITY PATTERNS =====================

AGE_PATTERNS = [
    # Age range
    r'age[:\s]*(\d{2})\s*(?:to|-)\s*(\d{2})\s*years?',
    r'(\d{2})\s*(?:to|-)\s*(\d{2})\s*years?\s+(?:of\s+)?age',
    r'minimum\s+age[:\s]*(\d{2})',
    r'maximum\s+age[:\s]*(\d{2})',
    # Hindi
    r'आयु[:\s]*(\d{2})\s*(?:से|-)\s*(\d{2})\s*(?:वर्ष|साल)',
    r'न्यूनतम\s+आयु[:\s]*(\d{2})',
    r'अधिकतम\s+आयु[:\s]*(\d{2})',
    r'उम्र[:\s]*(\d{2})\s*(?:से|-)\s*(\d{2})',
]

QUALIFICATION_PATTERNS = [
    # Degree patterns
    r'(?:graduation|graduate|bachelor)',
    r'(?:post\s*graduation|post\s*graduate|master)',
    r'(?:10th|tenth|matric|matriculation)',
    r'(?:12th|twelfth|intermediate|higher\s+secondary)',
    r'(?:diploma)',
    r'(?:b\.?tech|b\.?e\.?|engineering)',
    r'(?:m\.?tech|m\.?e\.?)',
    r'(?:b\.?sc|m\.?sc)',
    r'(?:b\.?a\.?|m\.?a\.?)',
    r'(?:b\.?com|m\.?com)',
    r'(?:mbbs|md|bds)',
    r'(?:llb|ll\.?b)',
    r'(?:iti|polytechnic)',
    # Hindi
    r'(?:स्नातक|ग्रेजुएट)',
    r'(?:परास्नातक|पोस्ट\s*ग्रेजुएट)',
    r'(?:10वीं|दसवीं|मैट्रिक)',
    r'(?:12वीं|बारहवीं|इंटर)',
]

ELIGIBILITY_KEYWORDS = {
    'en': [
        'eligible', 'eligibility', 'qualification', 'must have', 'should have',
        'required', 'essential', 'candidate must', 'applicant should',
        'educational qualification', 'age limit', 'experience'
    ],
    'hi': [
        'पात्रता', 'योग्यता', 'आवश्यक', 'अनिवार्य', 'शैक्षिक योग्यता',
        'आयु सीमा', 'अनुभव', 'उम्मीदवार'
    ]
}

# ===================== VACANCY PATTERNS =====================

VACANCY_PATTERNS = [
    r'(?:total\s+)?(?:vacancies?|posts?|seats?)[:\s]*(\d+)',
    r'(\d+)\s+(?:vacancies?|posts?|seats?)',
    r'(?:कुल\s+)?(?:पद|रिक्ति|सीट)[:\s]*(\d+)',
    r'(\d+)\s+(?:पद|रिक्ति)',
]

# ===================== DOCUMENT PATTERNS =====================

DOCUMENT_KEYWORDS = {
    'en': [
        'aadhar', 'aadhaar', 'pan card', 'voter id', 'passport',
        'driving license', 'photograph', 'photo', 'signature',
        'caste certificate', 'domicile', 'income certificate',
        'marksheet', 'degree', 'experience certificate',
        'birth certificate', 'character certificate', 'noc'
    ],
    'hi': [
        'आधार', 'पैन कार्ड', 'वोटर आईडी', 'पासपोर्ट',
        'ड्राइविंग लाइसेंस', 'फोटो', 'हस्ताक्षर',
        'जाति प्रमाण पत्र', 'निवास प्रमाण पत्र', 'आय प्रमाण पत्र',
        'मार्कशीट', 'डिग्री', 'अनुभव प्रमाण पत्र',
        'जन्म प्रमाण पत्र', 'चरित्र प्रमाण पत्र'
    ]
}

# ===================== STATE/DEPARTMENT PATTERNS =====================

INDIAN_STATES = [
    'andhra pradesh', 'arunachal pradesh', 'assam', 'bihar', 'chhattisgarh',
    'goa', 'gujarat', 'haryana', 'himachal pradesh', 'jharkhand', 'karnataka',
    'kerala', 'madhya pradesh', 'maharashtra', 'manipur', 'meghalaya', 'mizoram',
    'nagaland', 'odisha', 'punjab', 'rajasthan', 'sikkim', 'tamil nadu',
    'telangana', 'tripura', 'uttar pradesh', 'uttarakhand', 'west bengal',
    'delhi', 'jammu and kashmir', 'ladakh'
]

DEPARTMENTS = {
    'railway': ['rrb', 'indian railways', 'रेलवे'],
    'ssc': ['ssc', 'staff selection', 'कर्मचारी चयन'],
    'upsc': ['upsc', 'union public service', 'संघ लोक सेवा'],
    'bank': ['ibps', 'sbi', 'rbi', 'banking', 'बैंक'],
    'police': ['police', 'constable', 'si', 'पुलिस'],
    'army': ['army', 'navy', 'airforce', 'defence', 'सेना'],
    'teaching': ['teacher', 'tet', 'ctet', 'शिक्षक'],
    'health': ['anm', 'gnm', 'nurse', 'doctor', 'स्वास्थ्य'],
}

# ===================== LINK PATTERNS =====================

OFFICIAL_LINK_PATTERNS = [
    r'(https?://[a-zA-Z0-9.-]+\.gov\.in[^\s<>"\']*)',
    r'(https?://[a-zA-Z0-9.-]+\.nic\.in[^\s<>"\']*)',
    r'official\s+(?:website|link|site)[:\s]*(https?://[^\s<>"\']+)',
    r'apply\s+(?:online\s+)?(?:at|on)[:\s]*(https?://[^\s<>"\']+)',
]

PDF_LINK_PATTERNS = [
    r'(https?://[^\s<>"\']+\.pdf)',
    r'notification\s+pdf[:\s]*(https?://[^\s<>"\']+)',
    r'download\s+(?:notification|pdf)[:\s]*(https?://[^\s<>"\']+)',
]

# ===================== UTILITY FUNCTIONS =====================

def find_all_matches(text: str, patterns: List[str]) -> List[str]:
    """Find all matches for a list of patterns"""
    matches = []
    for pattern in patterns:
        found = re.findall(pattern, text, re.IGNORECASE)
        matches.extend(found)
    return list(set(matches))

def find_first_match(text: str, patterns: List[str]) -> Optional[str]:
    """Find first match from list of patterns"""
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1) if match.groups() else match.group(0)
    return None

def extract_dates(text: str) -> Dict[str, Optional[str]]:
    """Extract all date types from text"""
    return {
        'last_date': find_first_match(text, LAST_DATE_PATTERNS),
        'start_date': find_first_match(text, START_DATE_PATTERNS),
        'exam_date': find_first_match(text, EXAM_DATE_PATTERNS),
        'all_dates': find_all_matches(text, DATE_PATTERNS)
    }

def extract_fees(text: str) -> Dict[str, Optional[int]]:
    """Extract fee information by category"""
    fees = {}
    
    # General fee amount
    general_fee = find_first_match(text, FEE_PATTERNS)
    if general_fee:
        try:
            fees['general'] = int(general_fee.replace(',', ''))
        except:
            pass
    
    # Category-wise fees
    for category, patterns in CATEGORY_FEE_PATTERNS.items():
        fee = find_first_match(text, patterns)
        if fee:
            try:
                fees[category] = int(fee.replace(',', ''))
            except:
                pass
    
    return fees

def extract_age_limit(text: str) -> Dict[str, Optional[int]]:
    """Extract age limits"""
    for pattern in AGE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) == 2:
                return {'min': int(groups[0]), 'max': int(groups[1])}
            elif len(groups) == 1:
                return {'value': int(groups[0])}
    return {}

def extract_vacancies(text: str) -> Optional[int]:
    """Extract total vacancies"""
    vacancy = find_first_match(text, VACANCY_PATTERNS)
    if vacancy:
        try:
            return int(vacancy.replace(',', ''))
        except:
            pass
    return None

def extract_documents(text: str) -> List[str]:
    """Extract required documents"""
    text_lower = text.lower()
    docs = []
    
    for doc in DOCUMENT_KEYWORDS['en'] + DOCUMENT_KEYWORDS['hi']:
        if doc.lower() in text_lower:
            docs.append(doc.title())
    
    return list(set(docs))

def detect_state(text: str) -> Optional[str]:
    """Detect Indian state from text"""
    text_lower = text.lower()
    for state in INDIAN_STATES:
        if state in text_lower:
            return state.title()
    return None

def detect_department(text: str) -> Optional[str]:
    """Detect government department"""
    text_lower = text.lower()
    for dept, keywords in DEPARTMENTS.items():
        for kw in keywords:
            if kw.lower() in text_lower:
                return dept.title()
    return None

def extract_official_links(text: str) -> List[str]:
    """Extract official government links"""
    links = find_all_matches(text, OFFICIAL_LINK_PATTERNS)
    # Flatten tuples if any
    flat_links = []
    for link in links:
        if isinstance(link, tuple):
            flat_links.extend([l for l in link if l])
        else:
            flat_links.append(link)
    return list(set(flat_links))

def extract_pdf_links(text: str) -> List[str]:
    """Extract PDF download links"""
    return find_all_matches(text, PDF_LINK_PATTERNS)

def extract_qualifications(text: str) -> List[str]:
    """Extract educational qualifications"""
    qualifications = []
    text_lower = text.lower()
    
    qual_map = {
        '10th': ['10th', 'tenth', 'matric', 'matriculation', '10वीं', 'दसवीं'],
        '12th': ['12th', 'twelfth', 'intermediate', 'higher secondary', '12वीं', 'बारहवीं'],
        'Graduation': ['graduation', 'graduate', 'bachelor', 'स्नातक', 'ग्रेजुएट'],
        'Post Graduation': ['post graduation', 'post graduate', 'master', 'परास्नातक'],
        'B.Tech/B.E.': ['b.tech', 'b.e.', 'btech', 'engineering degree'],
        'Diploma': ['diploma', 'polytechnic', 'डिप्लोमा'],
        'ITI': ['iti', 'industrial training', 'आईटीआई'],
        'MBBS': ['mbbs', 'md', 'medical degree'],
        'LLB': ['llb', 'll.b', 'law degree'],
    }
    
    for qual, keywords in qual_map.items():
        for kw in keywords:
            if kw in text_lower:
                qualifications.append(qual)
                break
    
    return list(set(qualifications))
