"""
DS-Talk Synonyms Dictionary
===========================
Hindi and English synonym mappings for natural variation.
Used to substitute common words with alternatives.
"""

# ===================== HINDI SYNONYMS =====================

SYNONYMS_HI = {
    # Application related - keeping gender-neutral replacements
    "आवेदन": ["अप्लाई", "रजिस्ट्रेशन"],
    "आवेदन करें": ["अप्लाई करें", "फॉर्म भरें"],
    "नोटिफिकेशन": ["सूचना", "नोटिस"],
    
    # Date related
    "अंतिम तिथि": ["आखिरी तारीख़", "लास्ट डेट"],
    
    # Document related
    "दस्तावेज़": ["डॉक्यूमेंट्स", "कागज़ात"],
    
    # Fee related  
    "शुल्क": ["फीस"],
    
    # Action related
    "जल्दी करें": ["शीघ्र करें"],
    
    # Eligibility related
    "पात्रता": ["योग्यता"],
    "आवेदन कर सकते हैं": ["अप्लाई कर सकते हैं"],
    "आयु": ["उम्र", "एज"],
    
    # General
    "जानकारी": ["इन्फॉर्मेशन", "विवरण", "डिटेल्स"],
    "आधिकारिक": ["ऑफिशियल", "सरकारी"],
    "उपलब्ध": ["मिल रहा", "अवेलेबल"],
    "मौका": ["अवसर", "चांस", "opportunity"],
    
    # Links
    "लिंक": ["कड़ी", "वेबसाइट", "URL"],
    "वेबसाइट": ["साइट", "पोर्टल"],
    
    # Positive words
    "खुशखबरी": ["गुड न्यूज़", "अच्छी खबर", "शुभ समाचार"],
    "बधाई": ["congratulations", "शुभकामनाएं"],
    
    # Job related
    "नौकरी": ["जॉब", "रोज़गार", "employment"],
    "पद": ["पोस्ट", "position", "vacancy"],
    "विभाग": ["डिपार्टमेंट", "department"],
    
    # Exam related
    "परीक्षा": ["एग्जाम", "टेस्ट"],
    "एडमिट कार्ड": ["हॉल टिकट", "प्रवेश पत्र"],
}

# ===================== ENGLISH SYNONYMS =====================

SYNONYMS_EN = {
    # Application related
    "apply": ["submit your form", "register", "enroll", "fill the form"],
    "application": ["form", "registration"],
    "recruitment": ["hiring", "vacancy", "job opening"],
    "notification": ["notice", "announcement", "circular"],
    
    # Date related
    "date": ["deadline", "due date"],
    "last": ["final", "closing", "end"],
    "start": ["begin", "commence", "opening"],
    
    # Document related
    "documents": ["papers", "certificates", "proofs"],
    "certificate": ["proof", "document"],
    
    # Fee related
    "fee": ["charge", "payment", "cost"],
    "government": ["official", "govt"],
    
    # Action related
    "quickly": ["soon", "immediately", "promptly"],
    "check": ["verify", "see", "look at"],
    "learn": ["know", "find out", "discover"],
    
    # Result related
    "result": ["outcome", "score", "marks"],
    "declared": ["announced", "released", "published", "out"],
    
    # Eligibility related
    "eligibility": ["qualification", "requirements"],
    "eligible": ["qualified", "suitable"],
    "age": ["years old"],
    
    # General
    "information": ["details", "info", "data"],
    "official": ["authorized", "government"],
    "available": ["accessible", "ready", "obtainable"],
    "opportunity": ["chance", "opening"],
    
    # Links
    "link": ["URL", "website", "portal"],
    "website": ["site", "portal", "page"],
    
    # Positive words
    "good news": ["great news", "exciting news"],
    "congratulations": ["best wishes", "well done"],
    
    # Job related
    "job": ["position", "post", "employment"],
    "posts": ["positions", "vacancies", "seats"],
    "department": ["ministry", "office"],
    
    # Exam related
    "exam": ["examination", "test"],
    "admit card": ["hall ticket", "entry pass"],
}

# ===================== POLITE MARKERS =====================

POLITE_MARKERS = {
    "hi": {
        "formal": ["कृपया", "आपसे अनुरोध है", "आपको सूचित किया जाता है"],
        "friendly": ["जी", "भाई/बहन", "दोस्त"],
    },
    "en": {
        "formal": ["Please", "We request you to", "You are hereby informed"],
        "friendly": ["Hey", "Just letting you know", "Quick update"],
    }
}

# ===================== EMOJI MAPPINGS =====================

EMOJI_MAP = {
    "success": "✅",
    "warning": "⚠️",
    "info": "ℹ️",
    "date": "📅",
    "fee": "💰",
    "document": "📄",
    "link": "🔗",
    "job": "💼",
    "result": "📊",
    "admit": "🎫",
    "search": "🔍",
    "tip": "💡",
    "note": "📌",
    "celebration": "🎉",
    "time": "⏰",
    "state": "📍",
}

def get_synonym(word: str, language: str = "hi") -> str:
    """Get a random synonym for a word"""
    import random
    
    synonyms_dict = SYNONYMS_HI if language == "hi" else SYNONYMS_EN
    
    if word in synonyms_dict and synonyms_dict[word]:
        return random.choice(synonyms_dict[word])
    
    return word

def get_emoji(category: str) -> str:
    """Get emoji for a category"""
    return EMOJI_MAP.get(category, "")
