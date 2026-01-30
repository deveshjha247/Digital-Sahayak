"""
Data Augmentation Module
Generates augmented training data for improved model robustness
Includes text augmentation, translations, and synthetic variations
"""

import logging
import random
import re
import json
from typing import Dict, List, Any, Optional, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# TEXT AUGMENTATION TECHNIQUES
# =============================================================================

class TextAugmenter:
    """
    Text augmentation techniques for NLP data
    """
    
    # Common Hindi synonyms for augmentation
    HINDI_SYNONYMS = {
        "नौकरी": ["रोजगार", "जॉब", "कार्य"],
        "आवेदन": ["अप्लाई", "अर्जी", "प्रार्थना पत्र"],
        "योजना": ["स्कीम", "कार्यक्रम", "परियोजना"],
        "सरकार": ["सरकारी", "गवर्नमेंट", "शासन"],
        "वेतन": ["सैलरी", "तनख्वाह", "पगार"],
        "शिक्षा": ["पढ़ाई", "एजुकेशन", "विद्या"],
        "परीक्षा": ["एग्जाम", "टेस्ट", "इम्तिहान"],
        "उम्र": ["आयु", "एज", "वय"],
        "पता": ["एड्रेस", "ठिकाना", "निवास"],
        "मदद": ["सहायता", "हेल्प", "सहयोग"],
        "जानकारी": ["इनफार्मेशन", "सूचना", "विवरण"],
        "भर्ती": ["रिक्रूटमेंट", "नियुक्ति", "चयन"],
    }
    
    # Common English synonyms
    ENGLISH_SYNONYMS = {
        "job": ["vacancy", "position", "employment", "opening"],
        "apply": ["register", "submit", "enroll"],
        "scheme": ["program", "initiative", "plan"],
        "government": ["govt", "state", "public sector"],
        "salary": ["pay", "compensation", "remuneration"],
        "education": ["qualification", "degree", "academic"],
        "exam": ["test", "examination", "assessment"],
        "age": ["years old", "age limit"],
        "help": ["assist", "support", "aid"],
        "information": ["details", "info", "data"],
        "recruitment": ["hiring", "selection", "bharti"],
    }
    
    # Common typos/misspellings for robustness
    COMMON_TYPOS = {
        "government": ["goverment", "governmnt", "govt"],
        "application": ["applicaton", "aplication", "applcation"],
        "recruitment": ["recritment", "recruiment", "recruitmet"],
        "examination": ["examinaton", "examiation", "examnation"],
        "certificate": ["certifcate", "certificat", "certficate"],
        "registration": ["registraton", "registation", "regestration"],
        "aadhaar": ["aadhar", "adhaar", "adhar", "aadhr"],
    }
    
    # Hinglish patterns
    HINGLISH_PATTERNS = [
        ("job", "naukri"),
        ("apply", "apply karna"),
        ("form", "form bharna"),
        ("government", "sarkari"),
        ("scheme", "yojana"),
        ("salary", "salary kitni"),
        ("eligibility", "eligibility kya hai"),
        ("last date", "last date kab hai"),
    ]
    
    def __init__(self, augmentation_factor: float = 0.3):
        """
        Args:
            augmentation_factor: Probability of applying each augmentation
        """
        self.aug_factor = augmentation_factor
    
    def augment_text(
        self,
        text: str,
        techniques: List[str] = None
    ) -> List[str]:
        """
        Apply multiple augmentation techniques to text
        
        Args:
            text: Original text
            techniques: List of techniques to apply
                Options: synonym, typo, case, hinglish, punctuation, whitespace
        
        Returns:
            List of augmented texts
        """
        if not text:
            return []
        
        techniques = techniques or ["synonym", "typo", "case", "hinglish"]
        augmented = []
        
        if "synonym" in techniques:
            aug = self._synonym_replacement(text)
            if aug and aug != text:
                augmented.append(aug)
        
        if "typo" in techniques:
            aug = self._introduce_typo(text)
            if aug and aug != text:
                augmented.append(aug)
        
        if "case" in techniques:
            aug = self._case_variation(text)
            if aug and aug != text:
                augmented.append(aug)
        
        if "hinglish" in techniques:
            aug = self._hinglish_mixing(text)
            if aug and aug != text:
                augmented.append(aug)
        
        if "punctuation" in techniques:
            aug = self._punctuation_variation(text)
            if aug and aug != text:
                augmented.append(aug)
        
        if "whitespace" in techniques:
            aug = self._whitespace_variation(text)
            if aug and aug != text:
                augmented.append(aug)
        
        return list(set(augmented))  # Remove duplicates
    
    def _synonym_replacement(self, text: str) -> str:
        """Replace words with synonyms"""
        words = text.split()
        new_words = []
        
        for word in words:
            word_lower = word.lower()
            
            # Check English synonyms
            if word_lower in self.ENGLISH_SYNONYMS and random.random() < self.aug_factor:
                replacement = random.choice(self.ENGLISH_SYNONYMS[word_lower])
                # Preserve case
                if word[0].isupper():
                    replacement = replacement.capitalize()
                new_words.append(replacement)
            # Check Hindi synonyms
            elif word in self.HINDI_SYNONYMS and random.random() < self.aug_factor:
                new_words.append(random.choice(self.HINDI_SYNONYMS[word]))
            else:
                new_words.append(word)
        
        return " ".join(new_words)
    
    def _introduce_typo(self, text: str) -> str:
        """Introduce common typos for robustness training"""
        text_lower = text.lower()
        
        for correct, typos in self.COMMON_TYPOS.items():
            if correct in text_lower and random.random() < self.aug_factor:
                typo = random.choice(typos)
                text = re.sub(correct, typo, text, flags=re.IGNORECASE, count=1)
                break
        
        return text
    
    def _case_variation(self, text: str) -> str:
        """Create case variations"""
        variation = random.choice(["lower", "upper", "title", "random"])
        
        if variation == "lower":
            return text.lower()
        elif variation == "upper":
            return text.upper()
        elif variation == "title":
            return text.title()
        else:  # random
            return "".join(
                c.upper() if random.random() > 0.5 else c.lower()
                for c in text
            )
    
    def _hinglish_mixing(self, text: str) -> str:
        """Mix Hindi and English (Hinglish)"""
        for eng, hindi in self.HINGLISH_PATTERNS:
            if eng in text.lower() and random.random() < self.aug_factor:
                text = re.sub(eng, hindi, text, flags=re.IGNORECASE, count=1)
                break
        
        return text
    
    def _punctuation_variation(self, text: str) -> str:
        """Vary punctuation"""
        # Remove punctuation
        if random.random() < 0.5:
            text = re.sub(r'[.!?]+$', '', text)
        else:
            # Add or change punctuation
            text = re.sub(r'[.!?]*$', random.choice(['', '.', '!', '?', '...']), text)
        
        return text
    
    def _whitespace_variation(self, text: str) -> str:
        """Vary whitespace"""
        if random.random() < 0.5:
            # Add extra spaces
            words = text.split()
            return "  ".join(words)
        else:
            # Remove some spaces (for common joined words)
            return text


# =============================================================================
# TRANSLATION AUGMENTATION
# =============================================================================

class TranslationAugmenter:
    """
    Augments data with translations between Hindi and English
    Uses template-based translation for common patterns
    """
    
    # Template-based translations (no external API needed)
    INTENT_TRANSLATIONS = {
        # Greetings
        "hello": "नमस्ते",
        "hi": "हाय",
        "good morning": "सुप्रभात",
        "good evening": "शुभ संध्या",
        
        # Job queries
        "i want a job": "मुझे नौकरी चाहिए",
        "looking for job": "नौकरी ढूंढ रहा हूं",
        "any vacancy": "कोई वैकेंसी है",
        "government job": "सरकारी नौकरी",
        "railway job": "रेलवे में नौकरी",
        "bank job": "बैंक में नौकरी",
        
        # Scheme queries
        "what schemes are available": "कौन सी योजनाएं उपलब्ध हैं",
        "tell me about schemes": "योजनाओं के बारे में बताइए",
        "how to apply for scheme": "योजना के लिए कैसे आवेदन करें",
        
        # Application queries
        "how to apply": "कैसे आवेदन करें",
        "apply online": "ऑनलाइन आवेदन",
        "last date to apply": "आवेदन की अंतिम तिथि",
        "application status": "आवेदन की स्थिति",
        
        # Help
        "help me": "मेरी मदद करें",
        "i need help": "मुझे सहायता चाहिए",
        "thank you": "धन्यवाद",
        "bye": "अलविदा",
    }
    
    # Reverse translations
    REVERSE_TRANSLATIONS = {v: k for k, v in INTENT_TRANSLATIONS.items()}
    
    def __init__(self):
        pass
    
    def translate_to_hindi(self, text: str) -> Optional[str]:
        """Translate English text to Hindi using templates"""
        text_lower = text.lower().strip()
        
        # Direct match
        if text_lower in self.INTENT_TRANSLATIONS:
            return self.INTENT_TRANSLATIONS[text_lower]
        
        # Partial match
        for eng, hindi in self.INTENT_TRANSLATIONS.items():
            if eng in text_lower:
                return text_lower.replace(eng, hindi)
        
        return None
    
    def translate_to_english(self, text: str) -> Optional[str]:
        """Translate Hindi text to English using templates"""
        # Direct match
        if text in self.REVERSE_TRANSLATIONS:
            return self.REVERSE_TRANSLATIONS[text]
        
        # Partial match
        for hindi, eng in self.REVERSE_TRANSLATIONS.items():
            if hindi in text:
                return text.replace(hindi, eng)
        
        return None
    
    def create_bilingual_variants(self, item: Dict, text_key: str = "message") -> List[Dict]:
        """
        Create bilingual variants of an item
        
        Returns:
            List of items including translations
        """
        variants = [item]  # Original
        
        text = item.get(text_key, "")
        if not text:
            return variants
        
        # Try Hindi translation
        hindi_text = self.translate_to_hindi(text)
        if hindi_text:
            hindi_item = item.copy()
            hindi_item[text_key] = hindi_text
            hindi_item["language"] = "hi"
            hindi_item["_augmentation"] = "translation_to_hindi"
            variants.append(hindi_item)
        
        # Try English translation
        english_text = self.translate_to_english(text)
        if english_text:
            english_item = item.copy()
            english_item[text_key] = english_text
            english_item["language"] = "en"
            english_item["_augmentation"] = "translation_to_english"
            variants.append(english_item)
        
        return variants


# =============================================================================
# SYNTHETIC VARIATION GENERATOR
# =============================================================================

class SyntheticVariationGenerator:
    """
    Generates synthetic variations of existing data
    """
    
    # Templates for intent variations
    INTENT_TEMPLATES = {
        "job_search": [
            "I want a {job_type} job",
            "Show me {job_type} jobs",
            "Any {job_type} vacancy?",
            "{job_type} में नौकरी चाहिए",
            "{job_type} job dikhao",
            "Looking for {job_type} position",
        ],
        "scheme_search": [
            "Tell me about {scheme_type} scheme",
            "{scheme_type} योजना के बारे में बताओ",
            "What is {scheme_type} yojana?",
            "How to get {scheme_type} benefit?",
            "{scheme_type} का लाभ कैसे मिलेगा?",
        ],
        "apply": [
            "How to apply for {target}?",
            "{target} के लिए कैसे apply करें?",
            "I want to apply for {target}",
            "{target} का form kaise bhare?",
            "Apply online for {target}",
        ],
        "check_status": [
            "What is my {target} status?",
            "{target} की status kya hai?",
            "Track my {target} application",
            "Mera {target} kahan pahuncha?",
        ],
        "deadline": [
            "What is the last date for {target}?",
            "{target} की last date kya hai?",
            "When does {target} close?",
            "{target} कब तक है?",
        ],
    }
    
    # Slot fillers
    JOB_TYPES = [
        "railway", "bank", "ssc", "police", "teacher", "clerk",
        "रेलवे", "बैंक", "पुलिस", "शिक्षक", "क्लर्क",
    ]
    
    SCHEME_TYPES = [
        "PM Kisan", "Ayushman", "pension", "housing", "education",
        "पीएम किसान", "आयुष्मान", "पेंशन", "आवास", "छात्रवृत्ति",
    ]
    
    TARGETS = [
        "SSC CGL", "RRB NTPC", "IBPS PO", "UP Police", "Railway Group D",
        "PM Kisan", "Ayushman Bharat", "scholarship", "pension",
    ]
    
    def __init__(self, variation_count: int = 3):
        self.variation_count = variation_count
    
    def generate_intent_variations(
        self,
        intent: str,
        count: int = None
    ) -> List[Dict]:
        """Generate synthetic variations for an intent"""
        count = count or self.variation_count
        variations = []
        
        templates = self.INTENT_TEMPLATES.get(intent, [])
        if not templates:
            return variations
        
        for _ in range(count):
            template = random.choice(templates)
            
            # Fill slots
            if "{job_type}" in template:
                filled = template.format(job_type=random.choice(self.JOB_TYPES))
            elif "{scheme_type}" in template:
                filled = template.format(scheme_type=random.choice(self.SCHEME_TYPES))
            elif "{target}" in template:
                filled = template.format(target=random.choice(self.TARGETS))
            else:
                filled = template
            
            variations.append({
                "message": filled,
                "label": intent,
                "_augmentation": "synthetic_variation",
                "_template": template,
            })
        
        return variations
    
    def generate_form_field_variations(
        self,
        field_type: str,
        count: int = None
    ) -> List[Dict]:
        """Generate variations of form field labels"""
        count = count or self.variation_count
        
        field_variations = {
            "name": [
                {"label": "Full Name", "id": "fullname"},
                {"label": "पूरा नाम", "id": "full_name"},
                {"label": "Applicant Name", "id": "applicant_name"},
                {"label": "Candidate Name", "id": "candidate"},
                {"label": "आवेदक का नाम", "id": "naam"},
            ],
            "email": [
                {"label": "Email ID", "id": "email"},
                {"label": "ईमेल", "id": "email_id"},
                {"label": "Email Address", "id": "emailaddress"},
                {"label": "E-mail", "id": "e_mail"},
            ],
            "phone": [
                {"label": "Mobile Number", "id": "mobile"},
                {"label": "मोबाइल नंबर", "id": "mobile_no"},
                {"label": "Phone", "id": "phone"},
                {"label": "Contact Number", "id": "contact"},
                {"label": "संपर्क नंबर", "id": "contact_no"},
            ],
            "dob": [
                {"label": "Date of Birth", "id": "dob"},
                {"label": "जन्म तिथि", "id": "birth_date"},
                {"label": "D.O.B", "id": "date_of_birth"},
                {"label": "Birth Date", "id": "birthdate"},
            ],
            "aadhaar": [
                {"label": "Aadhaar Number", "id": "aadhaar"},
                {"label": "आधार नंबर", "id": "aadhar"},
                {"label": "Aadhaar No.", "id": "aadhaar_no"},
                {"label": "UIDAI Number", "id": "uid"},
            ],
        }
        
        variations = field_variations.get(field_type, [])
        selected = random.sample(variations, min(count, len(variations)))
        
        return [
            {**var, "field_type": field_type, "_augmentation": "form_field_variation"}
            for var in selected
        ]


# =============================================================================
# DATA AUGMENTATION PIPELINE
# =============================================================================

class DataAugmentationPipeline:
    """
    Complete data augmentation pipeline
    """
    
    def __init__(
        self,
        augmentation_ratio: float = 0.5,  # 50% more data through augmentation
        enable_text_aug: bool = True,
        enable_translation: bool = True,
        enable_synthetic: bool = True
    ):
        self.augmentation_ratio = augmentation_ratio
        
        self.text_augmenter = TextAugmenter() if enable_text_aug else None
        self.translation_augmenter = TranslationAugmenter() if enable_translation else None
        self.synthetic_generator = SyntheticVariationGenerator() if enable_synthetic else None
        
        # Statistics
        self.stats = defaultdict(int)
    
    def augment_dataset(
        self,
        data: List[Dict],
        text_key: str = "message",
        label_key: str = "label",
        preserve_distribution: bool = True
    ) -> Tuple[List[Dict], Dict]:
        """
        Augment entire dataset
        
        Args:
            data: Original dataset
            text_key: Key containing text to augment
            label_key: Key containing label
            preserve_distribution: If True, augment rare classes more
        
        Returns:
            (augmented_dataset, augmentation_report)
        """
        augmented = list(data)  # Start with original
        self.stats = defaultdict(int)
        
        # Calculate target augmentation per class
        if preserve_distribution:
            class_counts = defaultdict(int)
            for item in data:
                class_counts[item.get(label_key, "unknown")] += 1
            
            max_count = max(class_counts.values()) if class_counts else 1
            augmentation_targets = {
                label: int((max_count - count) * self.augmentation_ratio)
                for label, count in class_counts.items()
            }
        else:
            augmentation_targets = defaultdict(lambda: int(len(data) * self.augmentation_ratio / len(set(item.get(label_key) for item in data))))
        
        # Track generated hashes to avoid duplicates
        existing_hashes = set()
        for item in data:
            text = item.get(text_key, "")
            existing_hashes.add(hashlib.md5(text.encode()).hexdigest())
        
        # Augment each class
        for item in data:
            label = item.get(label_key)
            text = item.get(text_key, "")
            
            if not text or augmentation_targets.get(label, 0) <= 0:
                continue
            
            generated = []
            
            # Text augmentation
            if self.text_augmenter:
                aug_texts = self.text_augmenter.augment_text(text)
                for aug_text in aug_texts:
                    aug_hash = hashlib.md5(aug_text.encode()).hexdigest()
                    if aug_hash not in existing_hashes:
                        aug_item = item.copy()
                        aug_item[text_key] = aug_text
                        aug_item["_augmentation"] = "text_augmentation"
                        generated.append(aug_item)
                        existing_hashes.add(aug_hash)
                        self.stats["text_augmentation"] += 1
            
            # Translation augmentation
            if self.translation_augmenter:
                variants = self.translation_augmenter.create_bilingual_variants(item, text_key)
                for variant in variants[1:]:  # Skip original
                    var_text = variant.get(text_key, "")
                    var_hash = hashlib.md5(var_text.encode()).hexdigest()
                    if var_hash not in existing_hashes:
                        generated.append(variant)
                        existing_hashes.add(var_hash)
                        self.stats["translation"] += 1
            
            # Add generated items (up to target)
            target = augmentation_targets.get(label, 0)
            for gen_item in generated[:target]:
                augmented.append(gen_item)
                augmentation_targets[label] = augmentation_targets.get(label, 0) - 1
        
        # Synthetic variations for underrepresented intents
        if self.synthetic_generator:
            for label, remaining in augmentation_targets.items():
                if remaining > 0:
                    synthetic = self.synthetic_generator.generate_intent_variations(
                        label, count=remaining
                    )
                    augmented.extend(synthetic)
                    self.stats["synthetic"] += len(synthetic)
        
        # Shuffle
        random.shuffle(augmented)
        
        report = {
            "original_size": len(data),
            "augmented_size": len(augmented),
            "increase_ratio": len(augmented) / len(data) if data else 0,
            "augmentation_counts": dict(self.stats),
            "timestamp": datetime.now().isoformat(),
        }
        
        logger.info(
            f"Augmented dataset: {len(data)} -> {len(augmented)} "
            f"(+{len(augmented) - len(data)} items)"
        )
        
        return augmented, report
    
    def augment_for_robustness(
        self,
        data: List[Dict],
        text_key: str = "message"
    ) -> List[Dict]:
        """
        Create robustness-focused augmentations
        (typos, case variations, whitespace issues)
        """
        augmented = list(data)
        
        for item in data:
            text = item.get(text_key, "")
            if not text:
                continue
            
            # Typo variation
            if self.text_augmenter:
                typo_text = self.text_augmenter._introduce_typo(text)
                if typo_text != text:
                    typo_item = item.copy()
                    typo_item[text_key] = typo_text
                    typo_item["_augmentation"] = "robustness_typo"
                    augmented.append(typo_item)
                
                # Case variation
                case_text = self.text_augmenter._case_variation(text)
                if case_text != text:
                    case_item = item.copy()
                    case_item[text_key] = case_text
                    case_item["_augmentation"] = "robustness_case"
                    augmented.append(case_item)
        
        return augmented


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def augment_dataset(
    data: List[Dict],
    augmentation_ratio: float = 0.5,
    text_key: str = "message"
) -> Tuple[List[Dict], Dict]:
    """Quick dataset augmentation"""
    pipeline = DataAugmentationPipeline(augmentation_ratio=augmentation_ratio)
    return pipeline.augment_dataset(data, text_key=text_key)


def create_bilingual_dataset(
    data: List[Dict],
    text_key: str = "message"
) -> List[Dict]:
    """Create bilingual (Hindi-English) versions of dataset"""
    translator = TranslationAugmenter()
    bilingual = []
    
    for item in data:
        variants = translator.create_bilingual_variants(item, text_key)
        bilingual.extend(variants)
    
    return bilingual
