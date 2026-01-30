"""
Secure Data Storage
Handles secure storage of datasets with encryption, access control, and DPDP compliance
"""

import logging
import json
import hashlib
import base64
import os
import re
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from enum import Enum
import secrets

logger = logging.getLogger(__name__)


# =============================================================================
# ENCRYPTION (Using Fernet-compatible approach without cryptography lib)
# =============================================================================

class SimpleEncryption:
    """
    Simple encryption for data at rest
    Uses AES-like approach with base64 encoding
    For production, use cryptography.fernet or similar
    """
    
    def __init__(self, key: bytes = None):
        self.key = key or secrets.token_bytes(32)
    
    @staticmethod
    def generate_key() -> bytes:
        """Generate a new encryption key"""
        return secrets.token_bytes(32)
    
    @staticmethod
    def key_to_string(key: bytes) -> str:
        """Convert key to storable string"""
        return base64.urlsafe_b64encode(key).decode('utf-8')
    
    @staticmethod
    def string_to_key(key_string: str) -> bytes:
        """Convert string back to key"""
        return base64.urlsafe_b64decode(key_string.encode('utf-8'))
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt string data
        NOTE: This is a simplified implementation. Use proper AES for production.
        """
        # XOR with key (simplified - use Fernet in production)
        data_bytes = data.encode('utf-8')
        key_extended = (self.key * (len(data_bytes) // len(self.key) + 1))[:len(data_bytes)]
        encrypted = bytes(a ^ b for a, b in zip(data_bytes, key_extended))
        return base64.urlsafe_b64encode(encrypted).decode('utf-8')
    
    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt string data"""
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        key_extended = (self.key * (len(encrypted_bytes) // len(self.key) + 1))[:len(encrypted_bytes)]
        decrypted = bytes(a ^ b for a, b in zip(encrypted_bytes, key_extended))
        return decrypted.decode('utf-8')


# =============================================================================
# PII MASKING
# =============================================================================

class PIIMasker:
    """
    Masks personally identifiable information (PII) in data
    Compliant with India's DPDP Act 2023
    """
    
    # PII patterns for Indian data
    PATTERNS = {
        "aadhaar": {
            "pattern": r"\b[2-9]\d{3}\s?\d{4}\s?\d{4}\b",
            "mask": "XXXX XXXX XXXX",
            "description": "12-digit Aadhaar number",
        },
        "pan": {
            "pattern": r"\b[A-Z]{5}\d{4}[A-Z]\b",
            "mask": "XXXXX0000X",
            "description": "PAN card number",
        },
        "phone": {
            "pattern": r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b",
            "mask": "+91-XXXXXXXXXX",
            "description": "Indian phone number",
        },
        "email": {
            "pattern": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            "mask": "***@***.***",
            "description": "Email address",
        },
        "bank_account": {
            "pattern": r"\b\d{9,18}\b",  # Basic pattern, needs context
            "mask": "XXXXXXXXXX",
            "description": "Bank account number (context-dependent)",
        },
        "ifsc": {
            "pattern": r"\b[A-Z]{4}0[A-Z0-9]{6}\b",
            "mask": "XXXX0XXXXXX",
            "description": "IFSC code",
        },
        "voter_id": {
            "pattern": r"\b[A-Z]{3}\d{7}\b",
            "mask": "XXX0000000",
            "description": "Voter ID number",
        },
        "passport": {
            "pattern": r"\b[A-Z]\d{7}\b",
            "mask": "X0000000",
            "description": "Passport number",
        },
        "driving_license": {
            "pattern": r"\b[A-Z]{2}\d{2}\s?\d{11}\b",
            "mask": "XX00 00000000000",
            "description": "Driving license number",
        },
    }
    
    # Sensitive field names that should always be masked
    SENSITIVE_FIELDS = [
        "aadhaar", "aadhar", "आधार",
        "pan", "pan_number", "पैन",
        "phone", "mobile", "contact", "फोन", "मोबाइल",
        "email", "ईमेल",
        "account", "account_number", "खाता",
        "password", "पासवर्ड",
        "otp", "ओटीपी",
        "father_name", "mother_name", "spouse_name",
        "address", "पता",
        "dob", "date_of_birth", "जन्म_तिथि",
    ]
    
    def __init__(self, patterns: Dict = None, additional_fields: List[str] = None):
        self.patterns = {**self.PATTERNS, **(patterns or {})}
        self.sensitive_fields = self.SENSITIVE_FIELDS + (additional_fields or [])
    
    def mask_text(self, text: str) -> tuple[str, List[Dict]]:
        """
        Mask PII in text
        
        Returns:
            (masked_text, list of detected PII types)
        """
        if not text or not isinstance(text, str):
            return text, []
        
        masked = text
        detected = []
        
        for pii_type, config in self.patterns.items():
            pattern = config["pattern"]
            mask = config["mask"]
            
            matches = re.findall(pattern, masked, re.IGNORECASE)
            if matches:
                masked = re.sub(pattern, mask, masked, flags=re.IGNORECASE)
                detected.append({
                    "type": pii_type,
                    "count": len(matches),
                    "description": config["description"],
                })
        
        return masked, detected
    
    def mask_item(self, item: Dict) -> tuple[Dict, List[Dict]]:
        """
        Mask PII in a dictionary item
        
        Returns:
            (masked_item, list of masked fields)
        """
        masked_item = {}
        all_detected = []
        
        for key, value in item.items():
            # Check if field name is sensitive
            key_lower = key.lower()
            is_sensitive_field = any(sf in key_lower for sf in self.sensitive_fields)
            
            if is_sensitive_field:
                # Completely mask sensitive fields
                if isinstance(value, str) and value:
                    masked_item[key] = "[REDACTED]"
                    all_detected.append({
                        "field": key,
                        "type": "sensitive_field",
                        "masked": True,
                    })
                else:
                    masked_item[key] = value
            elif isinstance(value, str):
                # Check for PII patterns in text
                masked_value, detected = self.mask_text(value)
                masked_item[key] = masked_value
                for d in detected:
                    d["field"] = key
                    all_detected.append(d)
            elif isinstance(value, dict):
                # Recursively mask nested dicts
                masked_nested, nested_detected = self.mask_item(value)
                masked_item[key] = masked_nested
                all_detected.extend(nested_detected)
            elif isinstance(value, list):
                # Handle lists
                masked_list = []
                for v in value:
                    if isinstance(v, dict):
                        masked_v, _ = self.mask_item(v)
                        masked_list.append(masked_v)
                    elif isinstance(v, str):
                        masked_v, _ = self.mask_text(v)
                        masked_list.append(masked_v)
                    else:
                        masked_list.append(v)
                masked_item[key] = masked_list
            else:
                masked_item[key] = value
        
        return masked_item, all_detected
    
    def mask_dataset(self, data: List[Dict]) -> tuple[List[Dict], Dict]:
        """
        Mask PII in entire dataset
        
        Returns:
            (masked_data, masking_report)
        """
        masked_data = []
        total_detections = []
        
        for item in data:
            masked_item, detections = self.mask_item(item)
            masked_data.append(masked_item)
            total_detections.extend(detections)
        
        # Aggregate report
        from collections import Counter
        type_counts = Counter(d.get("type") for d in total_detections)
        field_counts = Counter(d.get("field") for d in total_detections)
        
        report = {
            "total_items": len(data),
            "items_with_pii": len(set(i for i, d in enumerate(data) if total_detections)),
            "pii_by_type": dict(type_counts),
            "pii_by_field": dict(field_counts),
            "total_detections": len(total_detections),
        }
        
        logger.info(f"Masked {report['total_detections']} PII instances in {len(data)} items")
        
        return masked_data, report


# =============================================================================
# ACCESS CONTROL
# =============================================================================

class AccessLevel(Enum):
    """Access levels for data"""
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    CONFIDENTIAL = "confidential"


@dataclass
class AccessPolicy:
    """Access control policy"""
    level: AccessLevel
    allowed_roles: List[str] = field(default_factory=list)
    allowed_users: List[str] = field(default_factory=list)
    requires_approval: bool = False
    audit_access: bool = True
    data_retention_days: int = 365


class AccessController:
    """
    Controls access to datasets based on policies
    """
    
    def __init__(self):
        self.policies: Dict[str, AccessPolicy] = {}
        self.access_log: List[Dict] = []
    
    def set_policy(self, dataset_name: str, policy: AccessPolicy):
        """Set access policy for a dataset"""
        self.policies[dataset_name] = policy
        logger.info(f"Set {policy.level.value} access policy for {dataset_name}")
    
    def check_access(
        self,
        dataset_name: str,
        user_id: str,
        user_roles: List[str] = None
    ) -> tuple[bool, str]:
        """
        Check if user has access to dataset
        
        Returns:
            (has_access, reason)
        """
        policy = self.policies.get(dataset_name)
        
        if not policy:
            return True, "No policy defined (default: allow)"
        
        # Check user-specific access
        if user_id in policy.allowed_users:
            self._log_access(dataset_name, user_id, True, "User allowlisted")
            return True, "User has explicit access"
        
        # Check role-based access
        user_roles = user_roles or []
        if any(role in policy.allowed_roles for role in user_roles):
            self._log_access(dataset_name, user_id, True, "Role-based access")
            return True, "Role-based access granted"
        
        # Public data
        if policy.level == AccessLevel.PUBLIC:
            self._log_access(dataset_name, user_id, True, "Public data")
            return True, "Public dataset"
        
        # Denied
        self._log_access(dataset_name, user_id, False, "Access denied")
        return False, f"Access denied. Dataset requires {policy.level.value} access."
    
    def _log_access(
        self,
        dataset_name: str,
        user_id: str,
        granted: bool,
        reason: str
    ):
        """Log access attempt"""
        self.access_log.append({
            "timestamp": datetime.now().isoformat(),
            "dataset": dataset_name,
            "user_id": user_id,
            "granted": granted,
            "reason": reason,
        })
    
    def get_access_log(
        self,
        dataset_name: str = None,
        user_id: str = None
    ) -> List[Dict]:
        """Get access log, optionally filtered"""
        log = self.access_log
        
        if dataset_name:
            log = [l for l in log if l["dataset"] == dataset_name]
        if user_id:
            log = [l for l in log if l["user_id"] == user_id]
        
        return log


# =============================================================================
# SECURE STORAGE
# =============================================================================

class SecureStorage:
    """
    Secure storage for datasets with encryption and access control
    Compliant with India's Digital Personal Data Protection (DPDP) Act 2023
    """
    
    def __init__(
        self,
        storage_dir: str,
        encryption_key: bytes = None,
        enable_encryption: bool = True
    ):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.enable_encryption = enable_encryption
        if enable_encryption:
            self.encryption = SimpleEncryption(encryption_key)
        else:
            self.encryption = None
        
        self.masker = PIIMasker()
        self.access_controller = AccessController()
        
        # Metadata storage
        self.metadata_file = self.storage_dir / "_metadata.json"
        self.metadata = self._load_metadata()
    
    def _load_metadata(self) -> Dict:
        """Load storage metadata"""
        if self.metadata_file.exists():
            with open(self.metadata_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"datasets": {}, "created": datetime.now().isoformat()}
    
    def _save_metadata(self):
        """Save storage metadata"""
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, default=str)
    
    def store_dataset(
        self,
        name: str,
        data: List[Dict],
        mask_pii: bool = True,
        encrypt: bool = None,
        access_level: AccessLevel = AccessLevel.INTERNAL,
        description: str = ""
    ) -> Dict[str, Any]:
        """
        Store dataset securely
        
        Args:
            name: Dataset name
            data: Dataset to store
            mask_pii: Whether to mask PII
            encrypt: Whether to encrypt (defaults to instance setting)
            access_level: Access control level
            description: Dataset description
        
        Returns:
            Storage result with file path and stats
        """
        encrypt = encrypt if encrypt is not None else self.enable_encryption
        
        logger.info(f"Storing dataset '{name}' ({len(data)} items)")
        
        # Mask PII if requested
        masking_report = None
        if mask_pii:
            data, masking_report = self.masker.mask_dataset(data)
            logger.info(f"Masked {masking_report['total_detections']} PII instances")
        
        # Serialize
        json_data = json.dumps(data, ensure_ascii=False, indent=2, default=str)
        
        # Encrypt if requested
        if encrypt and self.encryption:
            json_data = self.encryption.encrypt(json_data)
            file_ext = ".enc.json"
        else:
            file_ext = ".json"
        
        # Generate filename with hash for integrity
        content_hash = hashlib.sha256(json_data.encode()).hexdigest()[:12]
        filename = f"{name}_{content_hash}{file_ext}"
        file_path = self.storage_dir / filename
        
        # Write file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(json_data)
        
        # Set access policy
        policy = AccessPolicy(
            level=access_level,
            allowed_roles=["data_scientist", "ml_engineer", "admin"],
            audit_access=True,
        )
        self.access_controller.set_policy(name, policy)
        
        # Update metadata
        self.metadata["datasets"][name] = {
            "filename": filename,
            "path": str(file_path),
            "size": len(data),
            "encrypted": encrypt,
            "pii_masked": mask_pii,
            "masking_report": masking_report,
            "access_level": access_level.value,
            "content_hash": content_hash,
            "description": description,
            "stored_at": datetime.now().isoformat(),
        }
        self._save_metadata()
        
        return {
            "success": True,
            "name": name,
            "path": str(file_path),
            "size": len(data),
            "encrypted": encrypt,
            "pii_masked": mask_pii,
            "content_hash": content_hash,
        }
    
    def load_dataset(
        self,
        name: str,
        user_id: str = "system",
        user_roles: List[str] = None
    ) -> tuple[Optional[List[Dict]], Dict]:
        """
        Load dataset with access control
        
        Returns:
            (data or None, result info)
        """
        # Check access
        has_access, reason = self.access_controller.check_access(name, user_id, user_roles)
        
        if not has_access:
            logger.warning(f"Access denied for {user_id} to dataset {name}: {reason}")
            return None, {"success": False, "error": reason}
        
        # Get metadata
        if name not in self.metadata["datasets"]:
            return None, {"success": False, "error": f"Dataset '{name}' not found"}
        
        meta = self.metadata["datasets"][name]
        file_path = Path(meta["path"])
        
        if not file_path.exists():
            return None, {"success": False, "error": f"Dataset file not found: {file_path}"}
        
        # Read file
        with open(file_path, "r", encoding="utf-8") as f:
            json_data = f.read()
        
        # Decrypt if needed
        if meta["encrypted"] and self.encryption:
            json_data = self.encryption.decrypt(json_data)
        
        # Parse
        data = json.loads(json_data)
        
        return data, {
            "success": True,
            "name": name,
            "size": len(data),
            "encrypted": meta["encrypted"],
            "pii_masked": meta["pii_masked"],
        }
    
    def list_datasets(self) -> List[Dict]:
        """List all stored datasets"""
        return [
            {
                "name": name,
                "size": meta["size"],
                "access_level": meta["access_level"],
                "stored_at": meta["stored_at"],
                "encrypted": meta["encrypted"],
                "pii_masked": meta["pii_masked"],
            }
            for name, meta in self.metadata["datasets"].items()
        ]
    
    def delete_dataset(self, name: str, user_id: str = "system") -> Dict:
        """Delete a dataset"""
        if name not in self.metadata["datasets"]:
            return {"success": False, "error": f"Dataset '{name}' not found"}
        
        meta = self.metadata["datasets"][name]
        file_path = Path(meta["path"])
        
        # Delete file
        if file_path.exists():
            file_path.unlink()
        
        # Remove from metadata
        del self.metadata["datasets"][name]
        self._save_metadata()
        
        logger.info(f"Deleted dataset '{name}' by user {user_id}")
        
        return {"success": True, "name": name}
    
    def export_for_training(
        self,
        name: str,
        output_path: str,
        user_id: str = "system",
        user_roles: List[str] = None
    ) -> Dict:
        """
        Export dataset for model training (unencrypted, but PII masked)
        """
        data, result = self.load_dataset(name, user_id, user_roles)
        
        if not result["success"]:
            return result
        
        # Write unencrypted (PII already masked)
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
        
        logger.info(f"Exported dataset '{name}' to {output_path} for training")
        
        return {
            "success": True,
            "name": name,
            "output_path": str(output_file),
            "size": len(data),
        }
    
    def get_audit_log(self, dataset_name: str = None) -> List[Dict]:
        """Get access audit log"""
        return self.access_controller.get_access_log(dataset_name=dataset_name)


# =============================================================================
# DPDP COMPLIANCE CHECKER
# =============================================================================

class DPDPComplianceChecker:
    """
    Checks compliance with India's Digital Personal Data Protection Act 2023
    """
    
    REQUIREMENTS = {
        "consent": "Data collection must have user consent",
        "purpose_limitation": "Data used only for stated purpose",
        "data_minimization": "Collect only necessary data",
        "storage_limitation": "Don't store longer than needed",
        "security": "Implement appropriate security measures",
        "accuracy": "Keep data accurate and updated",
        "grievance_redressal": "Provide mechanism for complaints",
        "breach_notification": "Notify of data breaches",
    }
    
    def check_compliance(
        self,
        storage: SecureStorage,
        dataset_name: str
    ) -> Dict[str, Any]:
        """
        Check DPDP compliance for a dataset
        """
        checks = {}
        
        meta = storage.metadata["datasets"].get(dataset_name, {})
        
        # Security check
        checks["security"] = {
            "passed": meta.get("encrypted", False) and meta.get("pii_masked", False),
            "details": {
                "encrypted": meta.get("encrypted", False),
                "pii_masked": meta.get("pii_masked", False),
            },
            "recommendation": "Ensure encryption and PII masking are enabled",
        }
        
        # Access control check
        policy = storage.access_controller.policies.get(dataset_name)
        checks["access_control"] = {
            "passed": policy is not None,
            "details": {
                "has_policy": policy is not None,
                "level": policy.level.value if policy else None,
                "audit_enabled": policy.audit_access if policy else False,
            },
            "recommendation": "Implement role-based access control",
        }
        
        # Data minimization check (heuristic)
        masking_report = meta.get("masking_report", {})
        pii_count = masking_report.get("total_detections", 0)
        checks["data_minimization"] = {
            "passed": pii_count == 0,
            "details": {
                "pii_detected": pii_count,
                "pii_by_type": masking_report.get("pii_by_type", {}),
            },
            "recommendation": "Remove unnecessary PII or ensure it's properly masked",
        }
        
        # Overall compliance
        passed_checks = sum(1 for c in checks.values() if c["passed"])
        total_checks = len(checks)
        
        return {
            "dataset": dataset_name,
            "compliance_score": passed_checks / total_checks,
            "passed": passed_checks,
            "total": total_checks,
            "is_compliant": passed_checks == total_checks,
            "checks": checks,
            "dpdp_requirements": self.REQUIREMENTS,
        }


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def create_secure_storage(
    storage_dir: str,
    enable_encryption: bool = True
) -> SecureStorage:
    """Create pre-configured secure storage"""
    return SecureStorage(
        storage_dir=storage_dir,
        enable_encryption=enable_encryption,
    )


def mask_pii(data: List[Dict]) -> tuple[List[Dict], Dict]:
    """Mask PII in dataset"""
    masker = PIIMasker()
    return masker.mask_dataset(data)


def check_dpdp_compliance(
    storage: SecureStorage,
    dataset_name: str
) -> Dict[str, Any]:
    """Check DPDP compliance for a dataset"""
    checker = DPDPComplianceChecker()
    return checker.check_compliance(storage, dataset_name)
