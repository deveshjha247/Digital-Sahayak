"""
Document Validation Data Collector
Collects images of documents with expected properties
For training OCR and document validation models
"""

import json
import logging
import hashlib
import base64
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
from enum import Enum

logger = logging.getLogger(__name__)


class DocumentType(Enum):
    """Types of documents supported"""
    # Identity documents
    AADHAR_CARD = "aadhar_card"
    PAN_CARD = "pan_card"
    VOTER_ID = "voter_id"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    
    # Education certificates
    MARKSHEET_10TH = "marksheet_10th"
    MARKSHEET_12TH = "marksheet_12th"
    DEGREE_CERTIFICATE = "degree_certificate"
    DIPLOMA_CERTIFICATE = "diploma_certificate"
    
    # Other certificates
    CASTE_CERTIFICATE = "caste_certificate"
    INCOME_CERTIFICATE = "income_certificate"
    DOMICILE_CERTIFICATE = "domicile_certificate"
    BIRTH_CERTIFICATE = "birth_certificate"
    DISABILITY_CERTIFICATE = "disability_certificate"
    EWS_CERTIFICATE = "ews_certificate"
    
    # Photos
    PASSPORT_PHOTO = "passport_photo"
    SIGNATURE = "signature"
    
    # Bank related
    BANK_PASSBOOK = "bank_passbook"
    CANCELLED_CHEQUE = "cancelled_cheque"
    
    # Employment
    EXPERIENCE_LETTER = "experience_letter"
    SALARY_SLIP = "salary_slip"
    NOC_LETTER = "noc_letter"


class QualityIssue(Enum):
    """Document quality issues"""
    BLURRY = "blurry"
    LOW_RESOLUTION = "low_resolution"
    DARK = "dark"
    OVEREXPOSED = "overexposed"
    CROPPED = "cropped"
    ROTATED = "rotated"
    GLARE = "glare"
    DAMAGED = "damaged"
    PARTIAL = "partial"
    GOOD = "good"


# Expected fields for each document type
DOCUMENT_FIELDS = {
    DocumentType.AADHAR_CARD: [
        "name", "dob", "gender", "aadhar_number", "address",
        "photo", "qr_code"
    ],
    DocumentType.PAN_CARD: [
        "name", "father_name", "dob", "pan_number", "photo", "signature"
    ],
    DocumentType.VOTER_ID: [
        "name", "father_name", "dob", "epic_number", "address",
        "photo", "gender"
    ],
    DocumentType.MARKSHEET_10TH: [
        "name", "father_name", "roll_number", "year", "school_name",
        "subjects", "marks", "total_marks", "percentage", "result"
    ],
    DocumentType.MARKSHEET_12TH: [
        "name", "father_name", "roll_number", "year", "school_name",
        "stream", "subjects", "marks", "total_marks", "percentage", "result"
    ],
    DocumentType.DEGREE_CERTIFICATE: [
        "name", "father_name", "degree", "branch", "university",
        "year", "roll_number", "cgpa", "division"
    ],
    DocumentType.CASTE_CERTIFICATE: [
        "name", "father_name", "caste", "sub_caste", "category",
        "address", "issuing_authority", "issue_date", "certificate_number"
    ],
    DocumentType.INCOME_CERTIFICATE: [
        "name", "father_name", "annual_income", "address",
        "issuing_authority", "issue_date", "certificate_number"
    ],
    DocumentType.PASSPORT_PHOTO: [
        "face_visible", "background_color", "proper_lighting", "recent"
    ],
    DocumentType.SIGNATURE: [
        "clear", "consistent", "on_white_background"
    ],
    DocumentType.BANK_PASSBOOK: [
        "account_holder_name", "account_number", "ifsc_code",
        "bank_name", "branch_name"
    ],
    DocumentType.CANCELLED_CHEQUE: [
        "account_holder_name", "account_number", "ifsc_code",
        "bank_name", "cheque_number", "micr_code"
    ],
}


class DocumentCollector:
    """
    Collects document images with ground truth annotations
    For training OCR and document validation models
    
    Data Collection Strategy:
    1. Collect document images (anonymized/sample)
    2. Annotate with expected field locations
    3. Mark quality issues
    4. Extract ground truth text for OCR training
    """
    
    def __init__(self, data_dir: str = "data/training/documents"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.data_dir / "images").mkdir(exist_ok=True)
        (self.data_dir / "annotations").mkdir(exist_ok=True)
        
        # Data files
        self.documents_file = self.data_dir / "documents.jsonl"
        self.annotations_file = self.data_dir / "annotations.jsonl"
        self.quality_labels_file = self.data_dir / "quality_labels.jsonl"
        self.ocr_ground_truth_file = self.data_dir / "ocr_ground_truth.jsonl"
        
        self.stats = {
            "documents_collected": 0,
            "annotations_added": 0,
            "quality_labels": 0,
            "ocr_samples": 0,
        }
    
    def collect_document(
        self,
        image_path: str,
        document_type: DocumentType,
        is_sample: bool = False,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Collect a document image
        
        Args:
            image_path: Path to the document image
            document_type: Type of document
            is_sample: True if sample/synthetic document (no real data)
            metadata: Additional info
        
        Returns:
            document_id
        """
        doc_id = self._generate_id(image_path + datetime.now().isoformat())
        
        # Copy image to data directory with doc_id as filename
        image_path = Path(image_path)
        if image_path.exists():
            new_path = self.data_dir / "images" / f"{doc_id}{image_path.suffix}"
            # Just record path, don't copy (to avoid storing sensitive docs)
            stored_path = str(image_path) if is_sample else str(new_path)
        else:
            stored_path = None
        
        record = {
            "doc_id": doc_id,
            "document_type": document_type.value,
            "image_path": stored_path,
            "is_sample": is_sample,
            "expected_fields": DOCUMENT_FIELDS.get(document_type, []),
            "metadata": metadata or {},
            "collected_at": datetime.now().isoformat(),
            
            # Will be filled by annotation
            "quality": None,
            "has_annotations": False,
            "has_ocr_truth": False,
        }
        
        self._append_jsonl(self.documents_file, record)
        self.stats["documents_collected"] += 1
        
        return doc_id
    
    def add_field_annotations(
        self,
        doc_id: str,
        annotations: List[Dict],
        annotator_id: str
    ) -> Dict:
        """
        Add bounding box annotations for document fields
        
        annotations format: [
            {
                "field_name": "name",
                "bbox": [x1, y1, x2, y2],  # Normalized 0-1
                "text": "RAJESH KUMAR",  # Ground truth text
                "confidence": 0.95
            },
            ...
        ]
        """
        record = {
            "doc_id": doc_id,
            "annotations": annotations,
            "num_fields": len(annotations),
            "annotator_id": annotator_id,
            "annotated_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.annotations_file, record)
        self.stats["annotations_added"] += 1
        
        return record
    
    def add_quality_label(
        self,
        doc_id: str,
        quality: QualityIssue,
        issues: List[QualityIssue] = None,
        is_acceptable: bool = True,
        labeler_id: str = None,
        notes: str = None
    ) -> Dict:
        """
        Label document quality for quality assessment model
        """
        record = {
            "doc_id": doc_id,
            "primary_quality": quality.value,
            "issues": [i.value for i in (issues or [])],
            "is_acceptable": is_acceptable,
            "labeler_id": labeler_id,
            "notes": notes,
            "labeled_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.quality_labels_file, record)
        self.stats["quality_labels"] += 1
        
        return record
    
    def add_ocr_ground_truth(
        self,
        doc_id: str,
        field_name: str,
        image_crop_path: str,  # Path to cropped field image
        ground_truth_text: str,
        language: str = "en",
        annotator_id: str = None
    ) -> Dict:
        """
        Add OCR ground truth for a specific field
        Used for training OCR models
        """
        record = {
            "doc_id": doc_id,
            "field_name": field_name,
            "image_path": image_crop_path,
            "text": ground_truth_text,
            "language": language,
            "char_count": len(ground_truth_text),
            "annotator_id": annotator_id,
            "added_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.ocr_ground_truth_file, record)
        self.stats["ocr_samples"] += 1
        
        return record
    
    def collect_document_with_full_annotation(
        self,
        image_path: str,
        document_type: DocumentType,
        field_values: Dict[str, str],
        quality: QualityIssue,
        is_sample: bool,
        annotator_id: str
    ) -> Dict:
        """
        Convenience method to collect document with all annotations at once
        
        field_values: {
            "name": "RAJESH KUMAR",
            "dob": "01-01-1990",
            ...
        }
        """
        # Collect document
        doc_id = self.collect_document(
            image_path=image_path,
            document_type=document_type,
            is_sample=is_sample
        )
        
        # Add annotations (without bbox - just text ground truth)
        annotations = [
            {"field_name": k, "text": v}
            for k, v in field_values.items()
        ]
        self.add_field_annotations(doc_id, annotations, annotator_id)
        
        # Add quality label
        self.add_quality_label(
            doc_id=doc_id,
            quality=quality,
            labeler_id=annotator_id
        )
        
        return {
            "doc_id": doc_id,
            "document_type": document_type.value,
            "fields_annotated": len(field_values),
        }
    
    def create_synthetic_sample(
        self,
        document_type: DocumentType,
        field_values: Dict[str, str],
        template_path: str = None
    ) -> Dict:
        """
        Create a synthetic document sample for training
        Without using real personal data
        """
        sample_id = self._generate_id(
            document_type.value + str(field_values) + datetime.now().isoformat()
        )
        
        record = {
            "sample_id": sample_id,
            "document_type": document_type.value,
            "field_values": field_values,
            "template_path": template_path,
            "is_synthetic": True,
            "created_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.data_dir / "synthetic_samples.jsonl", record)
        
        return record
    
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
    
    def export_ocr_training_data(self, output_file: str = None) -> str:
        """
        Export OCR ground truth for training
        Format: {"image_path": ..., "text": ...}
        """
        if not output_file:
            output_file = str(self.data_dir / "ocr_training.jsonl")
        
        ocr_data = self._read_jsonl(self.ocr_ground_truth_file)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for record in ocr_data:
                training_example = {
                    "image_path": record["image_path"],
                    "text": record["text"],
                    "language": record["language"],
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file
    
    def export_quality_training_data(self, output_file: str = None) -> str:
        """
        Export quality labels for training quality assessment model
        """
        if not output_file:
            output_file = str(self.data_dir / "quality_training.jsonl")
        
        documents = {d["doc_id"]: d for d in self._read_jsonl(self.documents_file)}
        quality_labels = self._read_jsonl(self.quality_labels_file)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for label in quality_labels:
                doc_id = label["doc_id"]
                if doc_id not in documents:
                    continue
                
                doc = documents[doc_id]
                training_example = {
                    "image_path": doc["image_path"],
                    "document_type": doc["document_type"],
                    "quality": label["primary_quality"],
                    "issues": label["issues"],
                    "is_acceptable": label["is_acceptable"],
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file
    
    def export_field_extraction_data(self, output_file: str = None) -> str:
        """
        Export data for training field extraction model
        """
        if not output_file:
            output_file = str(self.data_dir / "field_extraction_training.jsonl")
        
        documents = {d["doc_id"]: d for d in self._read_jsonl(self.documents_file)}
        annotations = self._read_jsonl(self.annotations_file)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for ann in annotations:
                doc_id = ann["doc_id"]
                if doc_id not in documents:
                    continue
                
                doc = documents[doc_id]
                training_example = {
                    "image_path": doc["image_path"],
                    "document_type": doc["document_type"],
                    "fields": ann["annotations"],
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file


# Sample data generators for bootstrapping

def generate_sample_aadhar_data() -> Dict[str, str]:
    """Generate synthetic Aadhar card data"""
    return {
        "name": "SAMPLE NAME",
        "dob": "01/01/1990",
        "gender": "MALE",
        "aadhar_number": "XXXX XXXX XXXX",
        "address": "Sample Address, City, State - 000000",
    }


def generate_sample_pan_data() -> Dict[str, str]:
    """Generate synthetic PAN card data"""
    return {
        "name": "SAMPLE NAME",
        "father_name": "FATHER NAME",
        "dob": "01/01/1990",
        "pan_number": "XXXXX0000X",
    }


def generate_sample_marksheet_data(class_level: str = "10th") -> Dict[str, str]:
    """Generate synthetic marksheet data"""
    return {
        "name": "SAMPLE STUDENT",
        "father_name": "FATHER NAME",
        "roll_number": "0000000",
        "year": "2020",
        "school_name": "Sample School",
        "total_marks": "500",
        "obtained_marks": "450",
        "percentage": "90.00",
        "result": "PASS",
    }
