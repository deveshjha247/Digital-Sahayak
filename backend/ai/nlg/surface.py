"""
DS-Talk Surface Realizer
========================
Converts planned sections into natural language sentences.
Uses templates, synonyms, and variation for human-like text.
"""

import random
from typing import Dict, List, Any, Optional

from .templates import TEMPLATES, BULLET_TEMPLATES, CONNECTORS
from .synonyms import SYNONYMS_HI, SYNONYMS_EN, get_synonym, get_emoji


# ===================== SURFACE REALIZER =====================

class SurfaceRealizer:
    """Realizes sections into natural language"""
    
    def __init__(
        self,
        use_synonyms: bool = True,
        use_emojis: bool = True,
        variation_level: int = 2  # 1=low, 2=medium, 3=high
    ):
        self.use_synonyms = use_synonyms
        self.use_emojis = use_emojis
        self.variation_level = variation_level
    
    def realise(
        self,
        section: str,
        data: Dict[str, Any],
        language: str = "hi"
    ) -> str:
        """
        Realise a section into text.
        
        Args:
            section: Section name
            data: Section data
            language: 'hi' or 'en'
            
        Returns:
            Realized text
        """
        # Get template key
        template_key = f"{section}_{language}"
        
        # Check for type-specific templates
        content_type = data.get("type", "")
        type_template_key = f"{content_type}_{section}_{language}" if content_type else None
        
        # Special handling for different sections
        if section == "summary":
            return self._realise_summary(data, language)
        elif section == "eligibility":
            return self._realise_eligibility(data, language)
        elif section == "documents":
            return self._realise_documents(data, language)
        elif section == "fees":
            return self._realise_fees(data, language)
        elif section == "links":
            return self._realise_links(data, language)
        elif section == "date":
            return self._realise_date(data, language)
        elif section == "cta":
            return self._realise_cta(data, language)
        elif section == "disclaimer":
            return self._realise_disclaimer(language)
        else:
            return self._realise_generic(section, data, language)
    
    def _get_template(self, key: str) -> Optional[str]:
        """Get a random template for a key"""
        templates = TEMPLATES.get(key, [])
        if templates:
            return random.choice(templates)
        return None
    
    def _apply_synonyms(self, text: str, language: str) -> str:
        """Apply random synonym substitution"""
        if not self.use_synonyms:
            return text
        
        synonyms = SYNONYMS_HI if language == "hi" else SYNONYMS_EN
        
        # Only substitute some words (based on variation level)
        substitution_chance = 0.2 * self.variation_level
        
        for word, syns in synonyms.items():
            if word in text and random.random() < substitution_chance:
                text = text.replace(word, random.choice(syns), 1)
        
        return text
    
    def _realise_summary(self, data: Dict, language: str) -> str:
        """Realise summary section"""
        content_type = data.get("type", "job")
        title = data.get("title", "")
        
        # Choose template based on content type
        template_key = f"{content_type}_summary_{language}"
        template = self._get_template(template_key)
        
        if not template:
            # Try result_summary for exam_result type
            if content_type == "exam_result":
                template_key = f"result_summary_{language}"
                template = self._get_template(template_key)
            
            # Fallback to job summary
            if not template:
                template_key = f"job_summary_{language}"
                template = self._get_template(template_key)
        
        if template:
            text = template.format(title=title)
            return self._apply_synonyms(text, language)
        
        return title
    
    def _realise_date(self, data: Dict, language: str) -> str:
        """Realise date section"""
        parts = []
        
        # Last date
        last_date = data.get("last_date")
        if last_date:
            template = self._get_template(f"date_{language}")
            if template:
                text = template.format(last_date=last_date)
                if self.use_emojis:
                    text = f"{get_emoji('date')} {text}"
                parts.append(self._apply_synonyms(text, language))
        
        # Start date
        start_date = data.get("start_date")
        if start_date:
            template = self._get_template(f"start_date_{language}")
            if template:
                text = template.format(start_date=start_date)
                parts.append(self._apply_synonyms(text, language))
        
        return " ".join(parts)
    
    def _realise_eligibility(self, data: Dict, language: str) -> str:
        """Realise eligibility section"""
        eligibility = data.get("eligibility", [])
        qualifications = data.get("qualifications", [])
        
        all_items = eligibility + [f"Education: {q}" for q in qualifications if q not in str(eligibility)]
        
        if not all_items:
            return ""
        
        # If more than 3 items, use bullet list
        if len(all_items) > 3:
            bullet = BULLET_TEMPLATES[f"bullet_{language}"]
            items_text = "\n".join([bullet.format(item=item) for item in all_items])
            
            header = self._get_template(f"eligibility_{language}")
            if header:
                header = header.split(":")[0] + ":"  # Get just the header part
                if self.use_emojis:
                    header = f"{get_emoji('info')} {header}"
                return f"{header}\n{items_text}"
            return items_text
        else:
            # Join with commas
            items_text = ", ".join(all_items)
            template = self._get_template(f"eligibility_{language}")
            if template:
                text = template.format(eligibility=items_text)
                return self._apply_synonyms(text, language)
            return items_text
    
    def _realise_documents(self, data: Dict, language: str) -> str:
        """Realise documents section"""
        documents = data.get("documents", [])
        
        if not documents:
            return ""
        
        # Random choice: bullet list or sentence
        use_bullets = len(documents) > 3 or random.random() > 0.5
        
        if use_bullets:
            bullet = BULLET_TEMPLATES[f"bullet_{language}"]
            items_text = "\n".join([bullet.format(item=doc) for doc in documents[:7]])
            
            template = self._get_template(f"documents_{language}")
            if template:
                header = template.split(":")[0] + ":"
                if self.use_emojis:
                    header = f"{get_emoji('document')} {header}"
                return f"{header}\n{items_text}"
            return items_text
        else:
            docs_text = ", ".join(documents[:5])
            template = self._get_template(f"documents_{language}")
            if template:
                text = template.format(documents=docs_text)
                if self.use_emojis:
                    text = f"{get_emoji('document')} {text}"
                return self._apply_synonyms(text, language)
            return docs_text
    
    def _realise_fees(self, data: Dict, language: str) -> str:
        """Realise fees section"""
        govt_fee = data.get("govt_fee", 0)
        service_fee = data.get("service_fee", 20)
        total = data.get("total", 0)
        
        if not total and not govt_fee:
            return ""
        
        if not total:
            total = govt_fee + service_fee
        
        template = self._get_template(f"fees_{language}")
        if template:
            text = template.format(
                govt_fee=govt_fee,
                service_fee=service_fee,
                total=total
            )
            if self.use_emojis:
                text = f"{get_emoji('fee')} {text}"
            return self._apply_synonyms(text, language)
        
        return f"Fee: ₹{total}"
    
    def _realise_links(self, data: Dict, language: str) -> str:
        """Realise links section"""
        links = data.get("links", [])
        apply_link = data.get("apply_link")
        pdf_links = data.get("pdf_links", [])
        
        if not links and not apply_link:
            return ""
        
        parts = []
        
        # Main link
        main_link = apply_link or (links[0] if links else "")
        if main_link:
            template = self._get_template(f"links_{language}")
            if template:
                text = template.format(link=main_link)
                if self.use_emojis:
                    text = f"{get_emoji('link')} {text}"
                parts.append(text)
        
        # Additional links (max 2)
        for link in links[1:3]:
            if link != main_link:
                parts.append(f"🔗 {link}")
        
        return "\n".join(parts)
    
    def _realise_cta(self, data: Dict, language: str) -> str:
        """Realise call to action"""
        template = self._get_template(f"cta_{language}")
        if template:
            text = self._apply_synonyms(template, language)
            if self.use_emojis:
                text = f"{get_emoji('tip')} {text}"
            return text
        return ""
    
    def _realise_disclaimer(self, language: str) -> str:
        """Realise disclaimer"""
        template = self._get_template(f"disclaimer_{language}")
        return template or ""
    
    def _realise_generic(self, section: str, data: Dict, language: str) -> str:
        """Realise any other section"""
        template_key = f"{section}_{language}"
        template = self._get_template(template_key)
        
        if template:
            try:
                text = template.format(**data)
                return self._apply_synonyms(text, language)
            except KeyError:
                pass
        
        # Fallback: return data values
        return str(list(data.values())[0]) if data else ""


# ===================== FACTORY FUNCTION =====================

def realise_section(
    section: str,
    data: Dict[str, Any],
    language: str = "hi"
) -> str:
    """
    Factory function to realise a section.
    
    Args:
        section: Section name
        data: Section data
        language: 'hi' or 'en'
        
    Returns:
        Realized text
    """
    realizer = SurfaceRealizer()
    return realizer.realise(section, data, language)
