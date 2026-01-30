"""
DS-Talk: Natural Language Generator
====================================
Converts structured facts into natural Hindi/English responses.
Uses templates with variations, synonyms, and style controls.
"""

from .ds_talk import DSTalk, compose_answer
from .planner import ResponsePlanner, plan_sections
from .surface import SurfaceRealizer, realise_section
from .templates import TEMPLATES
from .synonyms import SYNONYMS_HI, SYNONYMS_EN
from .style import StyleController
from .safety import SafetyChecker

__all__ = [
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
    'SafetyChecker'
]

__version__ = "1.0.0"
