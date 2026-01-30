"""
DS-Talk Response Planner
========================
Decides which sections to include and in what order.
Based on available facts and content type.
"""

from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

# ===================== SECTION DEFINITIONS =====================

@dataclass
class Section:
    """Represents a planned section"""
    name: str
    data: Dict[str, Any]
    priority: int  # 1 = highest
    is_required: bool = False


# Section order by content type
SECTION_ORDER = {
    "job": [
        ("summary", True, 1),
        ("state", False, 2),
        ("department", False, 3),
        ("vacancies", False, 4),
        ("date", True, 5),
        ("eligibility", False, 6),
        ("age_limit", False, 7),
        ("documents", False, 8),
        ("fees", False, 9),
        ("links", True, 10),
        ("cta", True, 11),
        ("disclaimer", False, 12),
    ],
    "scheme": [
        ("summary", True, 1),
        ("state", False, 2),
        ("eligibility", True, 3),
        ("documents", False, 4),
        ("date", False, 5),
        ("links", True, 6),
        ("cta", True, 7),
        ("disclaimer", False, 8),
    ],
    "result": [
        ("summary", True, 1),
        ("date", False, 2),
        ("links", True, 3),
        ("cta", True, 4),
        ("disclaimer", False, 5),
    ],
    "admit_card": [
        ("summary", True, 1),
        ("exam_date", False, 2),
        ("links", True, 3),
        ("cta", True, 4),
        ("disclaimer", False, 5),
    ],
    "answer_key": [
        ("summary", True, 1),
        ("links", True, 2),
        ("cta", True, 3),
        ("disclaimer", False, 4),
    ],
}


# ===================== RESPONSE PLANNER =====================

class ResponsePlanner:
    """Plans response sections based on facts"""
    
    def __init__(self, include_disclaimer: bool = True, max_sections: int = 10):
        self.include_disclaimer = include_disclaimer
        self.max_sections = max_sections
    
    def plan(self, facts: Dict[str, Any], language: str = "hi") -> List[Section]:
        """
        Plan sections based on available facts.
        
        Args:
            facts: Dictionary of extracted facts
            language: Response language
            
        Returns:
            List of Section objects in order
        """
        content_type = facts.get('type', 'job')
        section_order = SECTION_ORDER.get(content_type, SECTION_ORDER['job'])
        
        planned_sections = []
        
        for section_name, is_required, priority in section_order:
            section_data = self._get_section_data(section_name, facts)
            
            # Include if required or if data is available
            if section_data or is_required:
                # Skip disclaimer if disabled
                if section_name == "disclaimer" and not self.include_disclaimer:
                    continue
                    
                planned_sections.append(Section(
                    name=section_name,
                    data=section_data or {},
                    priority=priority,
                    is_required=is_required
                ))
        
        # Limit sections
        return planned_sections[:self.max_sections]
    
    def _get_section_data(self, section_name: str, facts: Dict[str, Any]) -> Optional[Dict]:
        """Get data for a specific section"""
        
        if section_name == "summary":
            # Always include title
            return {
                "title": facts.get("title", ""),
                "type": facts.get("type", "job")
            }
        
        elif section_name == "date":
            last_date = facts.get("last_date")
            if last_date:
                return {
                    "last_date": last_date,
                    "start_date": facts.get("start_date")
                }
            return None
        
        elif section_name == "start_date":
            start_date = facts.get("start_date")
            if start_date:
                return {"start_date": start_date}
            return None
        
        elif section_name == "exam_date":
            exam_date = facts.get("exam_date")
            if exam_date:
                return {"exam_date": exam_date}
            return None
        
        elif section_name == "eligibility":
            eligibility = facts.get("eligibility", [])
            qualifications = facts.get("qualifications", [])
            if eligibility or qualifications:
                return {
                    "eligibility": eligibility,
                    "qualifications": qualifications
                }
            return None
        
        elif section_name == "age_limit":
            age_limit = facts.get("age_limit", {})
            if age_limit and ("min" in age_limit or "max" in age_limit):
                return {
                    "min_age": age_limit.get("min", ""),
                    "max_age": age_limit.get("max", "")
                }
            return None
        
        elif section_name == "documents":
            documents = facts.get("documents", [])
            if documents:
                return {"documents": documents}
            return None
        
        elif section_name == "fees":
            fees = facts.get("fees", {})
            if fees:
                return {
                    "govt_fee": fees.get("govt_fee", 0),
                    "service_fee": fees.get("service_fee", 20),
                    "total": fees.get("total", 0),
                    "category_wise": fees.get("category_wise", {})
                }
            return None
        
        elif section_name == "vacancies":
            vacancies = facts.get("vacancies")
            if vacancies:
                return {"vacancies": vacancies}
            return None
        
        elif section_name == "links":
            links = facts.get("links", [])
            apply_link = facts.get("apply_link")
            if links or apply_link:
                return {
                    "links": links,
                    "apply_link": apply_link,
                    "pdf_links": facts.get("pdf_links", [])
                }
            return None
        
        elif section_name == "state":
            state = facts.get("state")
            if state:
                return {"state": state}
            return None
        
        elif section_name == "department":
            department = facts.get("department")
            if department:
                return {"department": department}
            return None
        
        elif section_name == "cta":
            # Always include CTA
            return {"type": facts.get("type", "job")}
        
        elif section_name == "disclaimer":
            return {"type": facts.get("type", "job")}
        
        return None


# ===================== FACTORY FUNCTION =====================

def plan_sections(facts: Dict[str, Any], language: str = "hi") -> List[Tuple[str, Dict]]:
    """
    Factory function to plan sections.
    
    Args:
        facts: Dictionary of facts
        language: Response language
        
    Returns:
        List of (section_name, data) tuples
    """
    planner = ResponsePlanner()
    sections = planner.plan(facts, language)
    
    return [(s.name, s.data) for s in sections]
