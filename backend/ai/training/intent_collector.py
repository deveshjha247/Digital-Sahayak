"""
Intent Classification Data Collector
Collects WhatsApp/chat messages with intent labels
For training intent classifier from scratch
"""

import json
import logging
import hashlib
import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class UserIntent(Enum):
    """Intent categories for user messages"""
    # Job related
    SEARCH_JOB = "search_job"
    APPLY_JOB = "apply_job"
    JOB_STATUS = "job_status"
    JOB_DETAILS = "job_details"
    
    # Yojana related
    SEARCH_YOJANA = "search_yojana"
    APPLY_YOJANA = "apply_yojana"
    YOJANA_STATUS = "yojana_status"
    YOJANA_ELIGIBILITY = "yojana_eligibility"
    
    # General queries
    GREETING = "greeting"
    HELP = "help"
    GOODBYE = "goodbye"
    THANKS = "thanks"
    
    # Form/document related
    FILL_FORM = "fill_form"
    UPLOAD_DOCUMENT = "upload_document"
    CHECK_DOCUMENT = "check_document"
    
    # Profile related
    UPDATE_PROFILE = "update_profile"
    VIEW_PROFILE = "view_profile"
    
    # Payment related
    MAKE_PAYMENT = "make_payment"
    PAYMENT_STATUS = "payment_status"
    
    # Complaints/feedback
    COMPLAINT = "complaint"
    FEEDBACK = "feedback"
    
    # Other
    OUT_OF_SCOPE = "out_of_scope"
    UNCLEAR = "unclear"


# Rule-based keyword patterns for initial labeling
INTENT_PATTERNS = {
    UserIntent.SEARCH_JOB: [
        r"(job|naukri|vacancy|भर्ती|नौकरी)\s*(dhundho|chahiye|batao|dikhao|ढूंढो|चाहिए|बताओ)",
        r"(koi|new|latest|sarkari)\s*(job|naukri|vacancy)",
        r"(job|naukri)\s*(hai|ho|milega)",
        r"(railway|ssc|upsc|bank)\s*(job|vacancy|bharti)",
    ],
    UserIntent.APPLY_JOB: [
        r"(apply|avedan|form|आवेदन)\s*.*(job|naukri|vacancy)",
        r"(job|naukri)\s*.*(apply|avedan|form|भरना)",
        r"(form|application)\s*(bharna|karna|submit)",
        r"(is|iss|ye|yeh)\s*(job|naukri)\s*.*(apply|avedan)",
    ],
    UserIntent.JOB_STATUS: [
        r"(mera|my|apna)\s*(job|application)\s*(status|kya hua)",
        r"(kaha|kab)\s*(tak|se)\s*(result|status)",
        r"(application|form)\s*(status|track)",
        r"(result|outcome)\s*(kya|kab)",
    ],
    UserIntent.SEARCH_YOJANA: [
        r"(yojana|scheme|योजना)\s*(dhundho|batao|dikhao|hai)",
        r"(pm|mukhyamantri|pradhan mantri)\s*(yojana|scheme)",
        r"(government|sarkari)\s*(scheme|yojana|labh)",
        r"(koi|konsi)\s*(yojana|scheme)\s*(hai|milegi)",
    ],
    UserIntent.APPLY_YOJANA: [
        r"(yojana|scheme)\s*.*(apply|avedan|registration)",
        r"(apply|avedan|register)\s*.*(yojana|scheme)",
        r"(yojana|scheme)\s*(ka|ke|ki)\s*(form|registration)",
    ],
    UserIntent.YOJANA_ELIGIBILITY: [
        r"(eligible|patr|योग्य)\s*.*(yojana|scheme)",
        r"(yojana|scheme)\s*.*(eligible|patr|yogya|mil sakti)",
        r"(kon|kaun|kisko)\s*(mil|milegi)\s*(yojana|scheme)",
        r"(mujhe|me|main)\s*(mil)\s*(sakti|sakte)",
    ],
    UserIntent.GREETING: [
        r"^(hi|hello|hey|namaste|namaskar|नमस्ते|नमस्कार)[\s!]*$",
        r"^(good\s*(morning|afternoon|evening))[\s!]*$",
        r"^(kaise\s*ho|kya\s*hal)[\s!?]*$",
    ],
    UserIntent.HELP: [
        r"(help|madad|sahayata|मदद)\s*(chahiye|karo|kijiye)",
        r"(kya|kaise)\s*(kar|karu|kare)\s*(sakta|sakti|sakte)",
        r"(guide|batao|samjhao)\s*(kaise|kya)",
        r"(confused|samajh|problem)\s*(nahi|hai)",
    ],
    UserIntent.GOODBYE: [
        r"^(bye|goodbye|alvida|tata|अलविदा)[\s!]*$",
        r"(baad|later)\s*me\s*(milte|baat)",
        r"(dhanyawad|thanks|shukriya)\s*(bye|alvida)?",
    ],
    UserIntent.THANKS: [
        r"^(thanks|thank\s*you|dhanyawad|shukriya|धन्यवाद)[\s!]*$",
        r"(bahut|bohot)\s*(accha|sahi|helpful)",
    ],
    UserIntent.FILL_FORM: [
        r"(form|फॉर्म)\s*(bharna|fill|भरना)",
        r"(help|madad)\s*.*(form|फॉर्म)",
        r"(form|फॉर्म)\s*(kaise|how)",
    ],
    UserIntent.UPLOAD_DOCUMENT: [
        r"(document|dastavej|दस्तावेज़)\s*(upload|bhejo|dena)",
        r"(upload|attach)\s*(document|file|photo)",
        r"(aadhar|pan|certificate)\s*(upload|bhejo)",
    ],
    UserIntent.UPDATE_PROFILE: [
        r"(profile|details)\s*(update|change|badlo)",
        r"(badalna|change)\s*(naam|name|number|address)",
        r"(mera|apna)\s*(profile|account)\s*(edit|update)",
    ],
    UserIntent.COMPLAINT: [
        r"(complaint|shikayat|शिकायत)\s*(karna|hai|register)",
        r"(problem|dikkat|issue)\s*(hai|ho|aayi)",
        r"(kaam|work)\s*(nahi|not)\s*(ho|hua|hora)",
    ],
    UserIntent.OUT_OF_SCOPE: [
        r"(weather|mausam|cricket|movie|song)",
        r"(joke|chutkula|mazak)",
        r"(love|pyar|girlfriend|boyfriend)",
    ],
}


class IntentCollector:
    """
    Collects chat messages with intent labels for training
    
    Data Collection Strategy:
    1. Rule-based auto-labeling for initial dataset
    2. Human verification and correction
    3. Confidence scoring for quality filtering
    """
    
    def __init__(self, data_dir: str = "data/training/intent"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data files
        self.messages_file = self.data_dir / "messages.jsonl"
        self.labeled_file = self.data_dir / "labeled_messages.jsonl"
        self.corrections_file = self.data_dir / "corrections.jsonl"
        self.conversations_file = self.data_dir / "conversations.jsonl"
        
        self.stats = {
            "messages_collected": 0,
            "auto_labeled": 0,
            "human_verified": 0,
            "corrections": 0,
        }
    
    def collect_message(
        self,
        message: str,
        user_id: str,
        channel: str = "whatsapp",  # whatsapp, web, app
        conversation_id: Optional[str] = None,
        context: Optional[Dict] = None
    ) -> Dict:
        """
        Collect a user message (anonymized)
        
        Args:
            message: User's message text
            user_id: Anonymized user identifier
            channel: Communication channel
            conversation_id: ID to group messages in same conversation
            context: Previous messages, user state, etc.
        """
        message_id = self._generate_id(message + user_id + datetime.now().isoformat())
        
        # Anonymize sensitive data
        anonymized_message = self._anonymize_message(message)
        
        # Auto-label with rule-based patterns
        auto_intent, confidence = self._auto_label(anonymized_message)
        
        record = {
            "message_id": message_id,
            "message": anonymized_message,
            "original_length": len(message),
            "user_id": self._hash_user_id(user_id),
            "channel": channel,
            "conversation_id": conversation_id,
            "context": context or {},
            
            # Auto labeling
            "auto_intent": auto_intent.value if auto_intent else None,
            "auto_confidence": confidence,
            
            # Verification status
            "human_verified": False,
            "verified_intent": None,
            
            "collected_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.messages_file, record)
        self.stats["messages_collected"] += 1
        
        if auto_intent:
            self.stats["auto_labeled"] += 1
        
        return record
    
    def verify_intent(
        self,
        message_id: str,
        correct_intent: UserIntent,
        verifier_id: str,
        notes: Optional[str] = None
    ) -> Dict:
        """
        Human verification of intent label
        """
        # Find the message
        messages = {m["message_id"]: m for m in self._read_jsonl(self.messages_file)}
        
        if message_id not in messages:
            return {"error": "Message not found"}
        
        msg = messages[message_id]
        
        # Check if it's a correction
        is_correction = (
            msg.get("auto_intent") and 
            msg["auto_intent"] != correct_intent.value
        )
        
        # Create labeled record
        labeled_record = {
            "message_id": message_id,
            "message": msg["message"],
            "intent": correct_intent.value,
            "verifier_id": verifier_id,
            "verified_at": datetime.now().isoformat(),
            "was_auto_correct": msg.get("auto_intent") == correct_intent.value,
            "notes": notes,
        }
        
        self._append_jsonl(self.labeled_file, labeled_record)
        self.stats["human_verified"] += 1
        
        # Log correction if auto-label was wrong
        if is_correction:
            correction = {
                "message_id": message_id,
                "message": msg["message"],
                "auto_intent": msg["auto_intent"],
                "correct_intent": correct_intent.value,
                "verifier_id": verifier_id,
                "corrected_at": datetime.now().isoformat(),
            }
            self._append_jsonl(self.corrections_file, correction)
            self.stats["corrections"] += 1
        
        return labeled_record
    
    def collect_conversation(
        self,
        messages: List[Dict],
        user_id: str,
        channel: str = "whatsapp"
    ) -> str:
        """
        Collect a full conversation with multiple turns
        
        messages format: [
            {"role": "user", "text": "...", "intent": "..."},
            {"role": "bot", "text": "..."},
            ...
        ]
        """
        conversation_id = self._generate_id(user_id + datetime.now().isoformat())
        
        processed_messages = []
        for msg in messages:
            if msg["role"] == "user":
                # Anonymize and collect user messages
                processed = {
                    "role": "user",
                    "text": self._anonymize_message(msg["text"]),
                    "intent": msg.get("intent"),
                }
            else:
                processed = {
                    "role": msg["role"],
                    "text": msg["text"],
                }
            processed_messages.append(processed)
        
        record = {
            "conversation_id": conversation_id,
            "user_id": self._hash_user_id(user_id),
            "channel": channel,
            "messages": processed_messages,
            "num_turns": len([m for m in messages if m["role"] == "user"]),
            "collected_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.conversations_file, record)
        
        return conversation_id
    
    def _auto_label(self, message: str) -> Tuple[Optional[UserIntent], float]:
        """
        Auto-label using rule-based patterns
        Returns (intent, confidence)
        """
        message_lower = message.lower()
        
        best_intent = None
        best_confidence = 0.0
        
        for intent, patterns in INTENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    # Calculate confidence based on pattern specificity
                    confidence = 0.6 + (len(pattern) / 100)  # Longer patterns = higher confidence
                    confidence = min(confidence, 0.9)  # Cap at 0.9 (not 100% sure without human)
                    
                    if confidence > best_confidence:
                        best_intent = intent
                        best_confidence = confidence
        
        return best_intent, best_confidence
    
    def _anonymize_message(self, message: str) -> str:
        """
        Remove PII from message
        """
        anonymized = message
        
        # Replace phone numbers
        anonymized = re.sub(r'\b[6-9]\d{9}\b', '[PHONE]', anonymized)
        anonymized = re.sub(r'\+91\s*\d{10}', '[PHONE]', anonymized)
        
        # Replace Aadhar numbers
        anonymized = re.sub(r'\b\d{4}\s*\d{4}\s*\d{4}\b', '[AADHAR]', anonymized)
        
        # Replace PAN numbers
        anonymized = re.sub(r'\b[A-Z]{5}\d{4}[A-Z]\b', '[PAN]', anonymized)
        
        # Replace email
        anonymized = re.sub(r'\b[\w.-]+@[\w.-]+\.\w+\b', '[EMAIL]', anonymized)
        
        # Replace bank account numbers (8-18 digits)
        anonymized = re.sub(r'\b\d{8,18}\b', '[ACCOUNT]', anonymized)
        
        return anonymized
    
    def _hash_user_id(self, user_id: str) -> str:
        """Hash user ID for anonymization"""
        return hashlib.sha256(user_id.encode()).hexdigest()[:16]
    
    def _generate_id(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:12]
    
    def _append_jsonl(self, filepath: Path, record: Dict):
        with open(filepath, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    
    def _read_jsonl(self, filepath: Path) -> List[Dict]:
        if not filepath.exists():
            return []
        
        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
    
    def get_stats(self) -> Dict:
        return self.stats
    
    def export_training_data(
        self,
        output_file: str = None,
        min_confidence: float = 0.0,
        only_verified: bool = False
    ) -> str:
        """
        Export labeled data for training intent classifier
        
        Format: {"text": message, "label": intent}
        """
        if not output_file:
            output_file = str(self.data_dir / "training_dataset.jsonl")
        
        # Collect verified labels
        verified = {}
        for record in self._read_jsonl(self.labeled_file):
            verified[record["message_id"]] = record["intent"]
        
        # Get all messages
        messages = self._read_jsonl(self.messages_file)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for msg in messages:
                # Use verified intent if available, otherwise auto
                if msg["message_id"] in verified:
                    intent = verified[msg["message_id"]]
                    confidence = 1.0
                elif only_verified:
                    continue
                elif msg.get("auto_intent") and msg.get("auto_confidence", 0) >= min_confidence:
                    intent = msg["auto_intent"]
                    confidence = msg["auto_confidence"]
                else:
                    continue
                
                training_example = {
                    "text": msg["message"],
                    "label": intent,
                    "confidence": confidence,
                    "verified": msg["message_id"] in verified,
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file
    
    def get_correction_stats(self) -> Dict:
        """
        Analyze which intents are most often mislabeled
        Useful for improving auto-labeling rules
        """
        corrections = self._read_jsonl(self.corrections_file)
        
        confusion = {}
        for c in corrections:
            key = (c["auto_intent"], c["correct_intent"])
            confusion[key] = confusion.get(key, 0) + 1
        
        return {
            "total_corrections": len(corrections),
            "confusion_matrix": [
                {"auto": k[0], "correct": k[1], "count": v}
                for k, v in sorted(confusion.items(), key=lambda x: -x[1])
            ]
        }
