"""
DS-Talk: Natural Language Generator
====================================
Converts structured facts into natural Hindi/English responses.
Uses templates with variations, synonyms, and style controls.
Enhanced with regional Hindi, urgency detection, and messaging templates.
"""

from .ds_talk import DSTalk, compose_answer
from .planner import ResponsePlanner, plan_sections
from .surface import SurfaceRealizer, realise_section
from .templates import TEMPLATES
from .synonyms import SYNONYMS_HI, SYNONYMS_EN
from .style import StyleController
from .safety import SafetyChecker

# Enhanced Templates
from .templates_enhanced import (
    get_greeting,
    get_urgency_level,
    get_urgency_template,
    get_regional_template,
    get_messaging_template,
    get_category_template,
    get_conversational_template,
    get_state_name,
    get_state_code,
    get_all_states,
    get_salary_template,
    get_qualification_text,
    GREETINGS,
    URGENCY_TEMPLATES,
    REGIONAL_TEMPLATES,
    MESSAGING_TEMPLATES,
    ENHANCED_JOB_TEMPLATES,
    CONVERSATIONAL_TEMPLATES,
    STATE_NAMES,
    SALARY_TEMPLATES,
    QUALIFICATION_TEMPLATES
)

__all__ = [
    # Core DS-Talk
    'DSTalk',
    'compose_answer',
    'ResponsePlanner',
    'plan_sections',
    'SurfaceRealizer', 
    'realise_section',
    'TEMPLATES',
    'SYNONYMS_HI',
    'SYNONYMS_EN',
    'StyleController',
    'SafetyChecker',
    
    # Enhanced Templates
    'get_greeting',
    'get_urgency_level',
    'get_urgency_template',
    'get_regional_template',
    'get_messaging_template',
    'get_category_template',
    'get_conversational_template',
    'get_state_name',
    'get_state_code',
    'get_all_states',
    'get_salary_template',
    'get_qualification_text',
    'GREETINGS',
    'URGENCY_TEMPLATES',
    'REGIONAL_TEMPLATES',
    'MESSAGING_TEMPLATES',
    'ENHANCED_JOB_TEMPLATES',
    'CONVERSATIONAL_TEMPLATES',
    'STATE_NAMES',
    'SALARY_TEMPLATES',
    'QUALIFICATION_TEMPLATES'
]

__version__ = "2.0.0"
