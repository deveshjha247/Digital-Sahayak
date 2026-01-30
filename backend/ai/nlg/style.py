"""
DS-Talk Style Controller
========================
Adjusts tone and style of generated responses.
Supports formal, friendly, and concise styles.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class StyleTone(Enum):
    FORMAL = "formal"
    FRIENDLY = "friendly"
    CONCISE = "concise"


@dataclass
class StyleConfig:
    """Style configuration"""
    tone: StyleTone = StyleTone.FRIENDLY
    use_emojis: bool = True
    use_honorifics: bool = True
    max_sentences_per_section: int = 3
    include_greetings: bool = False
    include_closing: bool = True
    sentence_complexity: str = "medium"  # simple, medium, complex


# ===================== STYLE MODIFIERS =====================

STYLE_MODIFIERS = {
    StyleTone.FORMAL: {
        "hi": {
            "prefix": "",
            "suffix": "",
            "politeness": [],  # No random politeness - formal
            "closing": "",
        },
        "en": {
            "prefix": "",
            "suffix": "",
            "politeness": [],
            "closing": "",
        }
    },
    StyleTone.FRIENDLY: {
        "hi": {
            "prefix": "",
            "suffix": "",
            "politeness": [],  # No random prefixes - cleaner output
            "closing": "",
        },
        "en": {
            "prefix": "",
            "suffix": "",
            "politeness": [],
            "closing": "",
        }
    },
    StyleTone.CONCISE: {
        "hi": {
            "prefix": "",
            "suffix": "",
            "politeness": [],
            "closing": "",
        },
        "en": {
            "prefix": "",
            "suffix": "",
            "politeness": [],
            "closing": "",
        }
    }
}

# Emoji usage by tone
EMOJI_USAGE = {
    StyleTone.FORMAL: False,
    StyleTone.FRIENDLY: True,
    StyleTone.CONCISE: False,
}


# ===================== STYLE CONTROLLER =====================

class StyleController:
    """Controls response style and tone"""
    
    def __init__(self, config: Optional[StyleConfig] = None):
        self.config = config or StyleConfig()
    
    @classmethod
    def from_preferences(cls, preferences: Dict[str, Any]) -> 'StyleController':
        """Create from user preferences"""
        tone_str = preferences.get("tone", "friendly").lower()
        
        try:
            tone = StyleTone(tone_str)
        except ValueError:
            tone = StyleTone.FRIENDLY
        
        config = StyleConfig(
            tone=tone,
            use_emojis=preferences.get("use_emojis", True),
            use_honorifics=preferences.get("use_honorifics", True),
            include_closing=preferences.get("include_closing", True),
        )
        
        return cls(config)
    
    def should_use_emojis(self) -> bool:
        """Check if emojis should be used"""
        return self.config.use_emojis and EMOJI_USAGE.get(self.config.tone, True)
    
    def get_modifier(self, key: str, language: str) -> Any:
        """Get style modifier value"""
        modifiers = STYLE_MODIFIERS.get(self.config.tone, {})
        lang_modifiers = modifiers.get(language, {})
        return lang_modifiers.get(key, "")
    
    def add_politeness(self, text: str, language: str) -> str:
        """Add politeness markers if appropriate"""
        if self.config.tone == StyleTone.CONCISE:
            return text
        
        import random
        politeness = self.get_modifier("politeness", language)
        
        if politeness and random.random() > 0.7:  # 30% chance
            prefix = random.choice(politeness)
            return f"{prefix} {text}"
        
        return text
    
    def add_closing(self, text: str, language: str) -> str:
        """Add closing statement"""
        if not self.config.include_closing:
            return text
        
        closing = self.get_modifier("closing", language)
        if closing:
            return f"{text}\n\n{closing}"
        
        return text
    
    def adjust_complexity(self, text: str) -> str:
        """Adjust sentence complexity"""
        if self.config.sentence_complexity == "simple":
            # Split long sentences
            if len(text) > 100 and "," in text:
                parts = text.split(",", 1)
                if len(parts) == 2:
                    return f"{parts[0].strip()}। {parts[1].strip()}"
        
        return text
    
    def apply_style(self, text: str, language: str) -> str:
        """Apply all style modifications"""
        text = self.add_politeness(text, language)
        text = self.adjust_complexity(text)
        return text


# ===================== PREDEFINED STYLES =====================

PREDEFINED_STYLES = {
    "default": StyleConfig(
        tone=StyleTone.FRIENDLY,
        use_emojis=True,
        use_honorifics=True,
        include_closing=True,
    ),
    "formal": StyleConfig(
        tone=StyleTone.FORMAL,
        use_emojis=False,
        use_honorifics=True,
        include_closing=True,
    ),
    "quick": StyleConfig(
        tone=StyleTone.CONCISE,
        use_emojis=False,
        use_honorifics=False,
        include_closing=False,
        max_sentences_per_section=2,
    ),
    "chatbot": StyleConfig(
        tone=StyleTone.FRIENDLY,
        use_emojis=True,
        use_honorifics=False,
        include_closing=True,
        include_greetings=True,
    ),
}

def get_style(name: str) -> StyleController:
    """Get predefined style controller"""
    config = PREDEFINED_STYLES.get(name, PREDEFINED_STYLES["default"])
    return StyleController(config)
