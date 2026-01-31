"""
DS-Talk: Main Orchestrator
==========================
Converts structured facts into natural language responses.
Coordinates planner, surface realizer, style, and safety modules.
Enhanced with regional Hindi, urgency detection, and messaging templates.
"""

import logging
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

from .planner import ResponsePlanner, plan_sections
from .surface import SurfaceRealizer, realise_section
from .style import StyleController, StyleConfig, StyleTone, get_style
from .safety import SafetyChecker, check_safety
from .synonyms import get_emoji
from .templates_enhanced import (
    get_greeting,
    get_urgency_template,
    get_urgency_level,
    get_regional_template,
    get_messaging_template,
    get_category_template,
    get_conversational_template,
    get_state_name,
    get_salary_template,
    get_qualification_text
)

logger = logging.getLogger(__name__)


# ===================== DS-TALK RESPONSE =====================

@dataclass
class DSTalkResponse:
    """Complete DS-Talk response"""
    text: str
    language: str
    sections_used: List[str]
    style: str
    safety_passed: bool
    warnings: List[str]
    
    def to_dict(self) -> Dict:
        return {
            "text": self.text,
            "language": self.language,
            "sections_used": self.sections_used,
            "style": self.style,
            "safety_passed": self.safety_passed,
            "warnings": self.warnings
        }


# ===================== DS-TALK MAIN CLASS =====================

class DSTalk:
    """
    DS-Talk Natural Language Generator
    
    Converts structured facts into human-like Hindi/English responses.
    Uses templates with variations, synonyms, and style controls.
    """
    
    def __init__(
        self,
        style: str = "default",
        use_emojis: bool = True,
        use_synonyms: bool = True,
        include_disclaimer: bool = True,
        variation_level: int = 2
    ):
        """
        Initialize DS-Talk.
        
        Args:
            style: Style preset ('default', 'formal', 'quick', 'chatbot')
            use_emojis: Whether to include emojis
            use_synonyms: Whether to vary word choice
            include_disclaimer: Include disclaimer at end
            variation_level: 1-3, how much variation in templates
        """
        self.style_controller = get_style(style)
        self.style_name = style
        
        self.planner = ResponsePlanner(include_disclaimer=include_disclaimer)
        self.realizer = SurfaceRealizer(
            use_synonyms=use_synonyms,
            use_emojis=use_emojis,
            variation_level=variation_level
        )
        self.safety_checker = SafetyChecker()
        
        self.use_emojis = use_emojis
    
    def compose(
        self,
        facts: Dict[str, Any],
        language: str = "hi",
        source_texts: List[str] = None
    ) -> DSTalkResponse:
        """
        Compose a natural language response from facts.
        
        Args:
            facts: Structured facts dictionary
            language: 'hi' for Hindi, 'en' for English
            source_texts: Original source snippets for safety check
            
        Returns:
            DSTalkResponse with composed text
        """
        if not facts:
            return self._not_found_response(language)
        
        # Plan sections
        sections = self.planner.plan(facts, language)
        
        if not sections:
            return self._not_found_response(language)
        
        # Realise each section
        parts = []
        sections_used = []
        
        for section in sections:
            text = self.realizer.realise(section.name, section.data, language)
            if text:
                # Apply style
                text = self.style_controller.apply_style(text, language)
                parts.append(text)
                sections_used.append(section.name)
        
        # Join parts
        composed = "\n\n".join(parts)
        
        # Add closing
        composed = self.style_controller.add_closing(composed, language)
        
        # Safety check
        safety_result = self.safety_checker.check(
            composed,
            source_texts=source_texts,
            facts=facts
        )
        
        return DSTalkResponse(
            text=safety_result.cleaned_text,
            language=language,
            sections_used=sections_used,
            style=self.style_name,
            safety_passed=safety_result.is_safe,
            warnings=safety_result.warnings
        )
    
    def compose_quick(
        self,
        facts: Dict[str, Any],
        language: str = "hi"
    ) -> str:
        """
        Quick compose - returns just the text.
        
        Args:
            facts: Structured facts
            language: 'hi' or 'en'
            
        Returns:
            Composed text string
        """
        response = self.compose(facts, language)
        return response.text
    
    def _not_found_response(self, language: str) -> DSTalkResponse:
        """Generate not found response"""
        from .templates import TEMPLATES
        import random
        
        templates = TEMPLATES.get(f"not_found_{language}", [])
        text = random.choice(templates) if templates else "Information not found."
        
        return DSTalkResponse(
            text=text,
            language=language,
            sections_used=["not_found"],
            style=self.style_name,
            safety_passed=True,
            warnings=[]
        )
    
    def compose_with_header(
        self,
        facts: Dict[str, Any],
        language: str = "hi",
        header: str = None
    ) -> str:
        """
        Compose with a custom header.
        
        Args:
            facts: Structured facts
            language: 'hi' or 'en'
            header: Custom header text
            
        Returns:
            Composed text with header
        """
        response = self.compose(facts, language)
        
        if header:
            return f"**{header}**\n\n{response.text}"
        
        return response.text
    
    def format_as_card(
        self,
        facts: Dict[str, Any],
        language: str = "hi"
    ) -> Dict[str, Any]:
        """
        Format response as a card structure for UI.
        
        Args:
            facts: Structured facts
            language: 'hi' or 'en'
            
        Returns:
            Dictionary with card fields
        """
        content_type = facts.get("type", "job")
        
        # Type emoji
        type_emoji = {
            "job": "💼",
            "scheme": "🏛️",
            "result": "📊",
            "admit_card": "🎫",
            "answer_key": "📝"
        }.get(content_type, "📄")
        
        # Build card
        card = {
            "type": content_type,
            "type_emoji": type_emoji,
            "title": facts.get("title", ""),
            "summary": self.compose_quick(facts, language),
            "quick_info": [],
            "links": facts.get("links", [])[:3],
            "cta_text": "आवेदन करें" if language == "hi" else "Apply Now"
        }
        
        # Quick info items
        if facts.get("last_date"):
            card["quick_info"].append({
                "icon": "📅",
                "label": "Last Date" if language == "en" else "अंतिम तिथि",
                "value": facts["last_date"]
            })
        
        if facts.get("vacancies"):
            card["quick_info"].append({
                "icon": "👥",
                "label": "Vacancies" if language == "en" else "पद",
                "value": str(facts["vacancies"])
            })
        
        fees = facts.get("fees", {})
        if fees.get("total"):
            card["quick_info"].append({
                "icon": "💰",
                "label": "Fee" if language == "en" else "शुल्क",
                "value": f"₹{fees['total']}"
            })
        
        return card


# ===================== FACTORY FUNCTION =====================

def compose_answer(
    facts: Dict[str, Any],
    language: str = "hi",
    style: str = "default"
) -> str:
    """
    Factory function to compose answer from facts.
    
    Args:
        facts: Structured facts dictionary
        language: 'hi' or 'en'
        style: Style preset
        
    Returns:
        Composed natural language text
    """
    ds_talk = DSTalk(style=style)
    return ds_talk.compose_quick(facts, language)


def compose_full(
    facts: Dict[str, Any],
    language: str = "hi",
    style: str = "default",
    source_texts: List[str] = None
) -> DSTalkResponse:
    """
    Factory function for full compose with metadata.
    
    Args:
        facts: Structured facts
        language: 'hi' or 'en'
        style: Style preset
        source_texts: Source snippets for safety
        
    Returns:
        DSTalkResponse object
    """
    ds_talk = DSTalk(style=style)
    return ds_talk.compose(facts, language, source_texts)


# ===================== ENHANCED COMPOSE FUNCTIONS =====================

def compose_with_greeting(
    facts: Dict[str, Any],
    language: str = "hi",
    style: str = "default"
) -> str:
    """
    Compose answer with time-appropriate greeting.
    
    Args:
        facts: Structured facts
        language: 'hi' or 'en'
        style: Style preset
        
    Returns:
        Composed text with greeting
    """
    greeting = get_greeting(language)
    ds_talk = DSTalk(style=style)
    response = ds_talk.compose_quick(facts, language)
    return f"{greeting}\n\n{response}"


def compose_with_urgency(
    facts: Dict[str, Any],
    days_left: int,
    language: str = "hi",
    style: str = "default"
) -> str:
    """
    Compose answer with urgency indicator.
    
    Args:
        facts: Structured facts
        days_left: Days left for deadline
        language: 'hi' or 'en'
        style: Style preset
        
    Returns:
        Composed text with urgency
    """
    urgency_text = get_urgency_template(days_left, language)
    ds_talk = DSTalk(style=style)
    response = ds_talk.compose_quick(facts, language)
    return f"{urgency_text}\n\n{response}"


def compose_regional(
    facts: Dict[str, Any],
    region: str,
    language: str = "hi",
    style: str = "default"
) -> str:
    """
    Compose answer with regional Hindi variation.
    
    Args:
        facts: Structured facts
        region: Region code ('bihar', 'up', 'jharkhand', etc.)
        language: 'hi' or 'en'
        style: Style preset
        
    Returns:
        Composed text with regional flavor
    """
    greeting = get_regional_template(region, "greeting", language)
    ds_talk = DSTalk(style=style)
    response = ds_talk.compose_quick(facts, language)
    closing = get_regional_template(region, "closing", language)
    
    parts = []
    if greeting:
        parts.append(greeting)
    parts.append(response)
    if closing:
        parts.append(closing)
    
    return "\n\n".join(parts)


def compose_for_messaging(
    facts: Dict[str, Any],
    template_type: str = "job_alert",
    language: str = "hi"
) -> str:
    """
    Compose short message for any messaging platform.
    Works with WhatsApp, Telegram, SMS, Custom Chat, etc.
    
    Args:
        facts: Structured facts
        template_type: 'job_alert', 'result_alert', 'admit_card', 'reminder', etc.
        language: 'hi' or 'en'
        
    Returns:
        Short formatted message
    """
    template = get_messaging_template(template_type, language)
    
    if template:
        return template.format(
            title=facts.get("title", ""),
            last_date=facts.get("last_date", ""),
            vacancies=facts.get("vacancies", ""),
            link=facts.get("link", facts.get("links", [""])[0] if facts.get("links") else ""),
            exam_date=facts.get("exam_date", ""),
            benefit=facts.get("benefit", ""),
            days=facts.get("days_left", "")
        )
    
    # Fallback to regular compose
    ds_talk = DSTalk(style="quick")
    return ds_talk.compose_quick(facts, language)


def compose_conversational(
    facts: Dict[str, Any],
    user_query: str,
    language: str = "hi",
    style: str = "chatbot"
) -> str:
    """
    Compose conversational response for chatbot.
    
    Args:
        facts: Structured facts
        user_query: Original user query
        language: 'hi' or 'en'
        style: Style preset
        
    Returns:
        Conversational response
    """
    if not facts:
        no_info = get_conversational_template("no_info", language)
        if no_info:
            return no_info.format(query=user_query)
        return "जानकारी नहीं मिली।" if language == "hi" else "Information not found."
    
    # Opening
    question_response = get_conversational_template("question_response", language)
    if question_response:
        opening = question_response.format(title=facts.get("title", user_query))
    else:
        opening = ""
    
    # Main content
    ds_talk = DSTalk(style=style)
    content = ds_talk.compose_quick(facts, language)
    
    # Follow up
    follow_up = get_conversational_template("follow_up", language)
    
    parts = [p for p in [opening, content, follow_up] if p]
    return "\n\n".join(parts)


def compose_category_specific(
    facts: Dict[str, Any],
    category: str,
    language: str = "hi",
    style: str = "default"
) -> str:
    """
    Compose answer with category-specific opening.
    
    Args:
        facts: Structured facts
        category: Job category ('railway', 'bank', 'ssc', 'police', 'defence', etc.)
        language: 'hi' or 'en'
        style: Style preset
        
    Returns:
        Composed text with category-specific intro
    """
    category_intro = get_category_template(category, language)
    
    if category_intro:
        intro = category_intro.format(title=facts.get("title", ""))
    else:
        intro = ""
    
    ds_talk = DSTalk(style=style)
    content = ds_talk.compose_quick(facts, language)
    
    if intro:
        return f"{intro}\n\n{content}"
    return content
