"""
Content Rewriting Data Collector
Builds corpus of job/scheme descriptions with human-written summaries
For training text → summary generative models
"""

import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class ContentRewritingCollector:
    """
    Collects parallel corpus for content rewriting:
    - Raw scraped job/scheme descriptions (input)
    - Human-written clean summaries/highlights (output)
    - Both Hindi and English versions
    
    Training Goal: raw_text → clean_summary
    """
    
    def __init__(self, data_dir: str = "data/training/content_rewriting"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Data files
        self.raw_texts_file = self.data_dir / "raw_texts.jsonl"
        self.summaries_file = self.data_dir / "summaries.jsonl"
        self.parallel_corpus_file = self.data_dir / "parallel_corpus.jsonl"
        self.highlights_file = self.data_dir / "highlights.jsonl"
        
        self.stats = {
            "raw_texts_collected": 0,
            "summaries_written": 0,
            "parallel_pairs": 0,
            "highlights_extracted": 0,
        }
    
    def collect_raw_text(
        self,
        text: str,
        source_url: str,
        content_type: str,  # "job" or "scheme"
        language: str = "en",
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Collect raw scraped text (input for rewriting)
        
        Args:
            text: Raw scraped description
            source_url: Where it was scraped from
            content_type: "job" or "scheme"
            language: "en" or "hi"
            metadata: Additional info (title, category, etc.)
        """
        text_id = self._generate_id(text[:100] + source_url)
        
        record = {
            "text_id": text_id,
            "raw_text": text,
            "source_url": source_url,
            "content_type": content_type,
            "language": language,
            "char_count": len(text),
            "word_count": len(text.split()),
            "metadata": metadata or {},
            "collected_at": datetime.now().isoformat(),
            
            # Quality indicators
            "has_html_tags": "<" in text and ">" in text,
            "has_special_chars": any(c in text for c in "★●►◆"),
            "is_structured": "\n" in text or "•" in text or "-" in text,
        }
        
        self._append_jsonl(self.raw_texts_file, record)
        self.stats["raw_texts_collected"] += 1
        
        return text_id
    
    def add_human_summary(
        self,
        text_id: str,
        summary: str,
        writer_id: str,
        summary_type: str = "general",  # general, brief, detailed
        language: str = "en"
    ) -> Dict:
        """
        Add human-written summary for a raw text
        This creates the training target
        
        Args:
            text_id: ID of the raw text
            summary: Human-written clean summary
            writer_id: ID of the human writer (for quality tracking)
            summary_type: Type of summary
            language: Language of summary
        """
        summary_id = self._generate_id(text_id + summary[:50])
        
        record = {
            "summary_id": summary_id,
            "text_id": text_id,
            "summary": summary,
            "summary_type": summary_type,
            "language": language,
            "writer_id": writer_id,
            "char_count": len(summary),
            "word_count": len(summary.split()),
            "created_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.summaries_file, record)
        self.stats["summaries_written"] += 1
        
        # Also create parallel corpus entry
        self._create_parallel_entry(text_id, summary_id)
        
        return record
    
    def add_highlights(
        self,
        text_id: str,
        highlights: List[str],
        writer_id: str,
        language: str = "en"
    ) -> Dict:
        """
        Add bullet-point highlights for a text
        
        Args:
            text_id: ID of raw text
            highlights: List of key points extracted
            writer_id: Human writer ID
            language: Language
        """
        record = {
            "text_id": text_id,
            "highlights": highlights,
            "num_highlights": len(highlights),
            "writer_id": writer_id,
            "language": language,
            "created_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.highlights_file, record)
        self.stats["highlights_extracted"] += 1
        
        return record
    
    def add_bilingual_pair(
        self,
        text_id: str,
        english_summary: str,
        hindi_summary: str,
        writer_id: str
    ) -> Dict:
        """
        Add both Hindi and English summaries for same text
        Useful for translation training as well
        """
        # Add English summary
        self.add_human_summary(
            text_id=text_id,
            summary=english_summary,
            writer_id=writer_id,
            summary_type="bilingual",
            language="en"
        )
        
        # Add Hindi summary
        self.add_human_summary(
            text_id=text_id,
            summary=hindi_summary,
            writer_id=writer_id,
            summary_type="bilingual",
            language="hi"
        )
        
        return {
            "text_id": text_id,
            "english_summary": english_summary,
            "hindi_summary": hindi_summary,
        }
    
    def add_structured_output(
        self,
        text_id: str,
        structured_data: Dict,
        writer_id: str
    ) -> Dict:
        """
        Add structured extraction from text
        
        structured_data should contain:
        - title: Job/scheme title
        - salary: Salary info
        - qualification: Required education
        - age_limit: Age requirements
        - deadline: Last date
        - key_points: Important points
        - eligibility: Who can apply
        """
        record = {
            "text_id": text_id,
            "structured_data": structured_data,
            "writer_id": writer_id,
            "created_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.data_dir / "structured_extractions.jsonl", record)
        
        return record
    
    def _create_parallel_entry(self, text_id: str, summary_id: str):
        """Create entry in parallel corpus"""
        raw_texts = {r["text_id"]: r for r in self._read_jsonl(self.raw_texts_file)}
        summaries = {s["summary_id"]: s for s in self._read_jsonl(self.summaries_file)}
        
        if text_id not in raw_texts or summary_id not in summaries:
            return
        
        raw = raw_texts[text_id]
        summary = summaries[summary_id]
        
        parallel_entry = {
            "text_id": text_id,
            "summary_id": summary_id,
            "source": raw["raw_text"],
            "target": summary["summary"],
            "source_language": raw["language"],
            "target_language": summary["language"],
            "content_type": raw["content_type"],
            "compression_ratio": len(summary["summary"]) / len(raw["raw_text"]) if raw["raw_text"] else 0,
            "created_at": datetime.now().isoformat(),
        }
        
        self._append_jsonl(self.parallel_corpus_file, parallel_entry)
        self.stats["parallel_pairs"] += 1
    
    def collect_job_with_summary(
        self,
        raw_description: str,
        clean_summary: str,
        highlights: List[str],
        source_url: str,
        title: str,
        writer_id: str,
        language: str = "en"
    ) -> Dict:
        """
        Convenience method to collect job with all outputs at once
        """
        # Collect raw text
        text_id = self.collect_raw_text(
            text=raw_description,
            source_url=source_url,
            content_type="job",
            language=language,
            metadata={"title": title}
        )
        
        # Add summary
        self.add_human_summary(
            text_id=text_id,
            summary=clean_summary,
            writer_id=writer_id,
            language=language
        )
        
        # Add highlights
        self.add_highlights(
            text_id=text_id,
            highlights=highlights,
            writer_id=writer_id,
            language=language
        )
        
        return {
            "text_id": text_id,
            "title": title,
            "source_url": source_url,
        }
    
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
    
    def export_training_data(self, output_file: str = None) -> str:
        """
        Export parallel corpus for training summarization model
        Format: {"source": raw_text, "target": summary}
        """
        if not output_file:
            output_file = str(self.data_dir / "training_dataset.jsonl")
        
        parallel_data = self._read_jsonl(self.parallel_corpus_file)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for entry in parallel_data:
                training_example = {
                    "source": entry["source"],
                    "target": entry["target"],
                    "source_language": entry["source_language"],
                    "target_language": entry["target_language"],
                    "content_type": entry["content_type"],
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file
    
    def export_highlight_data(self, output_file: str = None) -> str:
        """
        Export data for highlight extraction model
        Format: {"source": raw_text, "highlights": [point1, point2, ...]}
        """
        if not output_file:
            output_file = str(self.data_dir / "highlight_dataset.jsonl")
        
        raw_texts = {r["text_id"]: r for r in self._read_jsonl(self.raw_texts_file)}
        highlights = self._read_jsonl(self.highlights_file)
        
        with open(output_file, "w", encoding="utf-8") as f:
            for h in highlights:
                text_id = h["text_id"]
                if text_id not in raw_texts:
                    continue
                
                training_example = {
                    "source": raw_texts[text_id]["raw_text"],
                    "highlights": h["highlights"],
                    "language": h["language"],
                }
                f.write(json.dumps(training_example, ensure_ascii=False) + "\n")
        
        return output_file
