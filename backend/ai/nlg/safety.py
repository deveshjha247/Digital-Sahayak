"""
DS-Talk Safety Checker
======================
Prevents plagiarism, excessive quotes, and ensures safe output.
Validates links and content before including in responses.
"""

import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from difflib import SequenceMatcher


@dataclass
class SafetyResult:
    """Result of safety check"""
    is_safe: bool
    issues: List[str]
    cleaned_text: str
    warnings: List[str]


# ===================== TRUSTED DOMAINS =====================

TRUSTED_DOMAINS = [
    ".gov.in",
    ".nic.in",
    "india.gov.in",
    ".ac.in",
    ".edu.in",
]

BLOCKED_DOMAINS = [
    "spam",
    "fake",
    "phishing",
    "malware",
]


# ===================== SAFETY CHECKER =====================

class SafetyChecker:
    """Checks generated content for safety issues"""
    
    def __init__(
        self,
        max_quote_length: int = 50,
        similarity_threshold: float = 0.8,
        max_excerpt_words: int = 20
    ):
        self.max_quote_length = max_quote_length
        self.similarity_threshold = similarity_threshold
        self.max_excerpt_words = max_excerpt_words
    
    def check(
        self,
        generated_text: str,
        source_texts: List[str] = None,
        facts: Dict[str, Any] = None
    ) -> SafetyResult:
        """
        Run all safety checks on generated text.
        
        Args:
            generated_text: The generated response
            source_texts: Original source snippets to compare against
            facts: Extracted facts for validation
            
        Returns:
            SafetyResult with cleaned text and issues
        """
        issues = []
        warnings = []
        cleaned_text = generated_text
        
        # Check 1: Plagiarism detection
        if source_texts:
            plagiarism_result = self._check_plagiarism(cleaned_text, source_texts)
            if plagiarism_result[0]:
                issues.extend(plagiarism_result[1])
                cleaned_text = plagiarism_result[2]
        
        # Check 2: Link validation
        if facts:
            link_result = self._validate_links(facts.get("links", []))
            if not link_result[0]:
                warnings.extend(link_result[1])
        
        # Check 3: Excessive quotes
        quote_result = self._check_quotes(cleaned_text)
        if quote_result[0]:
            warnings.extend(quote_result[1])
            cleaned_text = quote_result[2]
        
        # Check 4: Sensitive content
        sensitive_result = self._check_sensitive(cleaned_text)
        if not sensitive_result[0]:
            issues.extend(sensitive_result[1])
            cleaned_text = sensitive_result[2]
        
        # Check 5: Length validation
        length_result = self._check_length(cleaned_text)
        if not length_result[0]:
            warnings.extend(length_result[1])
            cleaned_text = length_result[2]
        
        is_safe = len(issues) == 0
        
        return SafetyResult(
            is_safe=is_safe,
            issues=issues,
            cleaned_text=cleaned_text,
            warnings=warnings
        )
    
    def _check_plagiarism(
        self,
        text: str,
        sources: List[str]
    ) -> Tuple[bool, List[str], str]:
        """Check for plagiarism against source texts"""
        issues = []
        cleaned_text = text
        has_issues = False
        
        for source in sources:
            if not source:
                continue
            
            # Check similarity
            similarity = SequenceMatcher(None, text.lower(), source.lower()).ratio()
            
            if similarity > self.similarity_threshold:
                has_issues = True
                issues.append(f"High similarity ({similarity:.0%}) with source text")
                
                # Try to paraphrase or shorten
                cleaned_text = self._paraphrase_excerpt(text, source)
        
        return has_issues, issues, cleaned_text
    
    def _paraphrase_excerpt(self, text: str, source: str) -> str:
        """Reduce similarity with source"""
        # Find common phrases and mark as quoted
        words = text.split()
        source_words = set(source.lower().split())
        
        # If too many common words, add "according to sources" prefix
        common_count = sum(1 for w in words if w.lower() in source_words)
        
        if common_count > len(words) * 0.5:
            # Significant overlap - add attribution
            return f"स्रोतों के अनुसार, {text}"
        
        return text
    
    def _validate_links(self, links: List[str]) -> Tuple[bool, List[str]]:
        """Validate that links are from trusted domains"""
        warnings = []
        all_trusted = True
        
        for link in links:
            if not link:
                continue
            
            link_lower = link.lower()
            
            # Check for blocked domains
            for blocked in BLOCKED_DOMAINS:
                if blocked in link_lower:
                    warnings.append(f"Potentially unsafe link detected: {link}")
                    all_trusted = False
            
            # Check if from trusted domain
            is_trusted = any(domain in link_lower for domain in TRUSTED_DOMAINS)
            
            if not is_trusted:
                warnings.append(f"Link not from official domain: {link}")
        
        return all_trusted, warnings
    
    def _check_quotes(self, text: str) -> Tuple[bool, List[str], str]:
        """Check for excessive quoted content"""
        warnings = []
        cleaned_text = text
        has_issues = False
        
        # Find quoted sections
        quotes = re.findall(r'"([^"]+)"', text)
        
        for quote in quotes:
            if len(quote) > self.max_quote_length:
                has_issues = True
                warnings.append(f"Long quote detected ({len(quote)} chars)")
                
                # Truncate quote
                truncated = quote[:self.max_quote_length] + "..."
                cleaned_text = cleaned_text.replace(f'"{quote}"', f'"{truncated}"')
        
        return has_issues, warnings, cleaned_text
    
    def _check_sensitive(self, text: str) -> Tuple[bool, List[str], str]:
        """Check for sensitive or inappropriate content"""
        issues = []
        cleaned_text = text
        
        # Patterns to detect sensitive content
        sensitive_patterns = [
            (r'\b(?:password|पासवर्ड)\s*[:=]\s*\S+', "Password detected in text"),
            (r'\b\d{12}\b', "Potential Aadhaar number detected"),  # 12 digit number
            (r'\b[A-Z]{5}\d{4}[A-Z]\b', "Potential PAN number detected"),
            (r'\b\d{10}\b', "Potential phone number detected"),  # 10 digit number
        ]
        
        for pattern, message in sensitive_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                issues.append(message)
                # Mask the sensitive data
                cleaned_text = re.sub(pattern, "[REDACTED]", cleaned_text, flags=re.IGNORECASE)
        
        is_safe = len(issues) == 0
        return is_safe, issues, cleaned_text
    
    def _check_length(self, text: str) -> Tuple[bool, List[str], str]:
        """Check response length"""
        warnings = []
        cleaned_text = text
        
        max_length = 2000  # Max characters
        
        if len(text) > max_length:
            warnings.append(f"Response too long ({len(text)} chars), truncating")
            
            # Truncate at sentence boundary
            truncated = text[:max_length]
            last_period = truncated.rfind("।")
            if last_period == -1:
                last_period = truncated.rfind(".")
            
            if last_period > max_length * 0.7:
                cleaned_text = truncated[:last_period + 1]
            else:
                cleaned_text = truncated + "..."
        
        is_ok = len(text) <= max_length
        return is_ok, warnings, cleaned_text
    
    def validate_facts(self, facts: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate extracted facts for consistency"""
        issues = []
        
        # Check for required fields
        if not facts.get("title"):
            issues.append("Missing title in facts")
        
        # Validate date format
        last_date = facts.get("last_date", "")
        if last_date and not re.match(r'\d{1,2}[/-]\d{1,2}[/-]\d{4}', str(last_date)):
            issues.append(f"Invalid date format: {last_date}")
        
        # Validate fee is numeric
        fees = facts.get("fees", {})
        if fees:
            for key in ["govt_fee", "total"]:
                val = fees.get(key)
                if val and not isinstance(val, (int, float)):
                    issues.append(f"Invalid fee value: {key}={val}")
        
        # Check links are valid URLs
        links = facts.get("links", [])
        for link in links:
            if not link.startswith("http"):
                issues.append(f"Invalid URL: {link}")
        
        is_valid = len(issues) == 0
        return is_valid, issues


# ===================== FACTORY FUNCTION =====================

def check_safety(
    text: str,
    source_texts: List[str] = None,
    facts: Dict[str, Any] = None
) -> SafetyResult:
    """
    Factory function to run safety checks.
    
    Args:
        text: Generated text
        source_texts: Source snippets
        facts: Extracted facts
        
    Returns:
        SafetyResult
    """
    checker = SafetyChecker()
    return checker.check(text, source_texts, facts)
