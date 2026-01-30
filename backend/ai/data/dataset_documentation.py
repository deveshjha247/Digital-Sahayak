"""
Dataset Documentation (Datasheet)
Generates comprehensive documentation for datasets
Following Datasheets for Datasets (Gebru et al.) framework
"""

import logging
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


# =============================================================================
# DATASHEET SECTIONS
# =============================================================================

@dataclass
class MotivationSection:
    """Why was the dataset created?"""
    purpose: str = ""
    creators: List[str] = field(default_factory=list)
    funding: str = ""
    intended_use: str = ""


@dataclass
class CompositionSection:
    """What does the dataset contain?"""
    instance_description: str = ""
    total_instances: int = 0
    instance_types: Dict[str, int] = field(default_factory=dict)
    sample_instances: List[Dict] = field(default_factory=list)
    label_description: str = ""
    label_classes: Dict[str, str] = field(default_factory=dict)
    has_missing_data: bool = False
    missing_data_description: str = ""
    has_sensitive_data: bool = False
    sensitive_data_description: str = ""
    confidentiality_note: str = ""


@dataclass
class CollectionSection:
    """How was the data collected?"""
    collection_process: str = ""
    data_sources: List[str] = field(default_factory=list)
    collection_timeframe: str = ""
    collection_methods: List[str] = field(default_factory=list)
    sampling_strategy: str = ""
    collectors: str = ""
    ethical_review: str = ""
    consent_process: str = ""


@dataclass
class PreprocessingSection:
    """What preprocessing was done?"""
    preprocessing_steps: List[str] = field(default_factory=list)
    cleaning_operations: List[str] = field(default_factory=list)
    raw_data_available: bool = False
    raw_data_location: str = ""


@dataclass
class AnnotationSection:
    """How was the data annotated?"""
    annotation_process: str = ""
    annotators: str = ""
    annotator_training: str = ""
    annotation_guidelines: str = ""
    annotation_tools: str = ""
    inter_annotator_agreement: Dict[str, float] = field(default_factory=dict)
    quality_control: str = ""


@dataclass
class UsesSection:
    """What are the intended uses?"""
    intended_uses: List[str] = field(default_factory=list)
    not_intended_uses: List[str] = field(default_factory=list)
    potential_impact: str = ""
    use_restrictions: str = ""


@dataclass
class DistributionSection:
    """How is the dataset distributed?"""
    distribution_method: str = ""
    license: str = ""
    copyright: str = ""
    fees: str = ""
    access_control: str = ""
    export_restrictions: str = ""


@dataclass
class MaintenanceSection:
    """How is the dataset maintained?"""
    maintainers: List[str] = field(default_factory=list)
    contact: str = ""
    update_frequency: str = ""
    versioning: str = ""
    deprecation_policy: str = ""
    support_channels: str = ""


@dataclass
class BiasSection:
    """Known biases and limitations"""
    known_biases: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    bias_mitigation: List[str] = field(default_factory=list)
    demographic_representation: Dict[str, Dict] = field(default_factory=dict)


# =============================================================================
# COMPLETE DATASHEET
# =============================================================================

@dataclass
class Datasheet:
    """
    Complete dataset documentation following Datasheets for Datasets framework
    """
    # Metadata
    dataset_name: str = ""
    version: str = "1.0.0"
    created_date: str = field(default_factory=lambda: datetime.now().isoformat())
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Sections
    motivation: MotivationSection = field(default_factory=MotivationSection)
    composition: CompositionSection = field(default_factory=CompositionSection)
    collection: CollectionSection = field(default_factory=CollectionSection)
    preprocessing: PreprocessingSection = field(default_factory=PreprocessingSection)
    annotation: AnnotationSection = field(default_factory=AnnotationSection)
    uses: UsesSection = field(default_factory=UsesSection)
    distribution: DistributionSection = field(default_factory=DistributionSection)
    maintenance: MaintenanceSection = field(default_factory=MaintenanceSection)
    bias: BiasSection = field(default_factory=BiasSection)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent, default=str, ensure_ascii=False)
    
    def to_markdown(self) -> str:
        """Convert to Markdown document"""
        md = DatasheetMarkdownGenerator(self)
        return md.generate()
    
    @classmethod
    def from_dict(cls, data: Dict) -> "Datasheet":
        """Create from dictionary"""
        datasheet = cls()
        
        # Simple fields
        for field_name in ["dataset_name", "version", "created_date", "last_updated"]:
            if field_name in data:
                setattr(datasheet, field_name, data[field_name])
        
        # Section fields
        section_classes = {
            "motivation": MotivationSection,
            "composition": CompositionSection,
            "collection": CollectionSection,
            "preprocessing": PreprocessingSection,
            "annotation": AnnotationSection,
            "uses": UsesSection,
            "distribution": DistributionSection,
            "maintenance": MaintenanceSection,
            "bias": BiasSection,
        }
        
        for section_name, section_class in section_classes.items():
            if section_name in data:
                section_data = data[section_name]
                section_obj = section_class(**{
                    k: v for k, v in section_data.items()
                    if k in section_class.__dataclass_fields__
                })
                setattr(datasheet, section_name, section_obj)
        
        return datasheet


# =============================================================================
# MARKDOWN GENERATOR
# =============================================================================

class DatasheetMarkdownGenerator:
    """Generates Markdown documentation from Datasheet"""
    
    def __init__(self, datasheet: Datasheet):
        self.ds = datasheet
    
    def generate(self) -> str:
        """Generate complete Markdown document"""
        sections = [
            self._header(),
            self._motivation_section(),
            self._composition_section(),
            self._collection_section(),
            self._preprocessing_section(),
            self._annotation_section(),
            self._uses_section(),
            self._distribution_section(),
            self._maintenance_section(),
            self._bias_section(),
            self._footer(),
        ]
        
        return "\n\n".join(sections)
    
    def _header(self) -> str:
        return f"""# Datasheet: {self.ds.dataset_name}

**Version:** {self.ds.version}  
**Created:** {self.ds.created_date}  
**Last Updated:** {self.ds.last_updated}

---"""
    
    def _motivation_section(self) -> str:
        m = self.ds.motivation
        return f"""## 1. Motivation

### Purpose
{m.purpose or "Not specified"}

### Creators
{self._list_items(m.creators) or "Not specified"}

### Funding
{m.funding or "Not specified"}

### Intended Use
{m.intended_use or "Not specified"}"""
    
    def _composition_section(self) -> str:
        c = self.ds.composition
        
        instance_types = ""
        if c.instance_types:
            instance_types = "\n".join(f"- **{k}**: {v}" for k, v in c.instance_types.items())
        
        label_classes = ""
        if c.label_classes:
            label_classes = "\n".join(f"- `{k}`: {v}" for k, v in c.label_classes.items())
        
        samples = ""
        if c.sample_instances:
            samples = "```json\n" + json.dumps(c.sample_instances[:2], indent=2, default=str, ensure_ascii=False) + "\n```"
        
        return f"""## 2. Composition

### Instance Description
{c.instance_description or "Not specified"}

### Total Instances
{c.total_instances}

### Instance Types
{instance_types or "Not specified"}

### Sample Instances
{samples or "Not provided"}

### Label Description
{c.label_description or "Not specified"}

### Label Classes
{label_classes or "Not specified"}

### Missing Data
- **Has Missing Data:** {"Yes" if c.has_missing_data else "No"}
- **Description:** {c.missing_data_description or "N/A"}

### Sensitive Data
- **Contains Sensitive Data:** {"Yes" if c.has_sensitive_data else "No"}
- **Description:** {c.sensitive_data_description or "N/A"}
- **Confidentiality Note:** {c.confidentiality_note or "N/A"}"""
    
    def _collection_section(self) -> str:
        c = self.ds.collection
        return f"""## 3. Collection Process

### Overview
{c.collection_process or "Not specified"}

### Data Sources
{self._list_items(c.data_sources) or "Not specified"}

### Collection Timeframe
{c.collection_timeframe or "Not specified"}

### Collection Methods
{self._list_items(c.collection_methods) or "Not specified"}

### Sampling Strategy
{c.sampling_strategy or "Not specified"}

### Collectors
{c.collectors or "Not specified"}

### Ethical Review
{c.ethical_review or "Not specified"}

### Consent Process
{c.consent_process or "Not specified"}"""
    
    def _preprocessing_section(self) -> str:
        p = self.ds.preprocessing
        return f"""## 4. Preprocessing

### Preprocessing Steps
{self._list_items(p.preprocessing_steps) or "None"}

### Cleaning Operations
{self._list_items(p.cleaning_operations) or "None"}

### Raw Data
- **Available:** {"Yes" if p.raw_data_available else "No"}
- **Location:** {p.raw_data_location or "N/A"}"""
    
    def _annotation_section(self) -> str:
        a = self.ds.annotation
        
        iaa = ""
        if a.inter_annotator_agreement:
            iaa = "\n".join(f"- **{k}**: {v:.4f}" for k, v in a.inter_annotator_agreement.items())
        
        return f"""## 5. Annotation

### Annotation Process
{a.annotation_process or "Not specified"}

### Annotators
{a.annotators or "Not specified"}

### Annotator Training
{a.annotator_training or "Not specified"}

### Annotation Guidelines
{a.annotation_guidelines or "Not specified"}

### Annotation Tools
{a.annotation_tools or "Not specified"}

### Inter-Annotator Agreement
{iaa or "Not measured"}

### Quality Control
{a.quality_control or "Not specified"}"""
    
    def _uses_section(self) -> str:
        u = self.ds.uses
        return f"""## 6. Uses

### Intended Uses
{self._list_items(u.intended_uses) or "Not specified"}

### NOT Intended Uses
{self._list_items(u.not_intended_uses) or "Not specified"}

### Potential Impact
{u.potential_impact or "Not specified"}

### Use Restrictions
{u.use_restrictions or "None"}"""
    
    def _distribution_section(self) -> str:
        d = self.ds.distribution
        return f"""## 7. Distribution

### Distribution Method
{d.distribution_method or "Not specified"}

### License
{d.license or "Not specified"}

### Copyright
{d.copyright or "Not specified"}

### Fees
{d.fees or "Free"}

### Access Control
{d.access_control or "Not specified"}

### Export Restrictions
{d.export_restrictions or "None"}"""
    
    def _maintenance_section(self) -> str:
        m = self.ds.maintenance
        return f"""## 8. Maintenance

### Maintainers
{self._list_items(m.maintainers) or "Not specified"}

### Contact
{m.contact or "Not specified"}

### Update Frequency
{m.update_frequency or "Not specified"}

### Versioning
{m.versioning or "Not specified"}

### Deprecation Policy
{m.deprecation_policy or "Not specified"}

### Support Channels
{m.support_channels or "Not specified"}"""
    
    def _bias_section(self) -> str:
        b = self.ds.bias
        
        demographics = ""
        if b.demographic_representation:
            for attr, dist in b.demographic_representation.items():
                demographics += f"\n**{attr}:**\n"
                for val, pct in dist.items():
                    demographics += f"- {val}: {pct:.1%}\n"
        
        return f"""## 9. Known Biases and Limitations

### Known Biases
{self._list_items(b.known_biases) or "None identified"}

### Limitations
{self._list_items(b.limitations) or "None identified"}

### Bias Mitigation Efforts
{self._list_items(b.bias_mitigation) or "None"}

### Demographic Representation
{demographics or "Not analyzed"}"""
    
    def _footer(self) -> str:
        return f"""---

## Document History

| Version | Date | Changes |
|---------|------|---------|
| {self.ds.version} | {self.ds.last_updated[:10]} | Initial documentation |

---

*This datasheet follows the "Datasheets for Datasets" framework (Gebru et al., 2021)*"""
    
    def _list_items(self, items: List[str]) -> str:
        if not items:
            return ""
        return "\n".join(f"- {item}" for item in items)


# =============================================================================
# DATASHEET GENERATOR
# =============================================================================

class DatasheetGenerator:
    """
    Generates datasheets from dataset and analysis
    """
    
    def __init__(self):
        pass
    
    def generate_from_analysis(
        self,
        dataset_name: str,
        data: List[Dict],
        analysis: Dict,
        split_info: Dict = None,
        annotation_info: Dict = None
    ) -> Datasheet:
        """
        Generate datasheet from dataset analysis
        """
        datasheet = Datasheet(dataset_name=dataset_name)
        
        # Motivation (default for Digital Sahayak)
        datasheet.motivation = MotivationSection(
            purpose="Training AI models for Digital Sahayak - a platform helping citizens access government jobs and schemes in India",
            creators=["Digital Sahayak Development Team"],
            funding="Self-funded project",
            intended_use="Training intent classification, job matching, form filling assistance, and scheme recommendation models",
        )
        
        # Composition from analysis
        class_dist = analysis.get("class_distribution", {})
        datasheet.composition = CompositionSection(
            instance_description="Annotated items for various AI tasks including intent classification, job categorization, and form field identification",
            total_instances=analysis.get("dataset_size", len(data)),
            instance_types=class_dist.get("distribution", {}),
            sample_instances=data[:3] if data else [],
            label_description="Task-specific labels assigned through annotation process",
            label_classes={str(k): f"{v['count']} samples ({v['percentage']}%)" 
                          for k, v in class_dist.get("distribution", {}).items()},
            has_missing_data=bool(analysis.get("missing_features", {}).get("concerning_features")),
            missing_data_description=f"Concerning features: {analysis.get('missing_features', {}).get('concerning_features', [])}",
            has_sensitive_data=True,
            sensitive_data_description="May contain PII like names, phone numbers, Aadhaar numbers (masked in dataset)",
            confidentiality_note="All PII is masked or removed. Data should be treated as confidential.",
        )
        
        # Collection
        datasheet.collection = CollectionSection(
            collection_process="Multi-source data collection including web scraping, synthetic generation, and user interaction logs",
            data_sources=[
                "Government job portals (SSC, RRB, IBPS)",
                "State scheme websites",
                "Synthetic data generators",
                "User interaction logs (anonymized)",
            ],
            collection_timeframe="Ongoing collection",
            collection_methods=[
                "Web scraping with rate limiting",
                "API integrations",
                "Synthetic generation with templates",
                "User feedback collection (with consent)",
            ],
            sampling_strategy="Stratified sampling to ensure regional and linguistic diversity",
            collectors="Automated scrapers and manual curation",
            ethical_review="Internal ethics review conducted",
            consent_process="User data collected only with explicit consent",
        )
        
        # Preprocessing
        missing_info = analysis.get("missing_features", {})
        datasheet.preprocessing = PreprocessingSection(
            preprocessing_steps=[
                "Deduplication using MD5 hashing",
                "Field name normalization (60+ mappings)",
                "Date format standardization to ISO 8601",
                "Number format normalization (lakhs, crores, K)",
                "Text cleaning and normalization",
            ],
            cleaning_operations=[
                "Remove duplicate entries",
                "Normalize Hindi/English text",
                "Standardize salary formats",
                "Mask PII fields",
                "Fix encoding issues",
            ],
            raw_data_available=True,
            raw_data_location="backend/ai/data/raw/ (gitignored)",
        )
        
        # Annotation
        if annotation_info:
            iaa = annotation_info.get("inter_annotator_agreement", {})
        else:
            iaa = {}
        
        datasheet.annotation = AnnotationSection(
            annotation_process="Multi-annotator labeling with consensus mechanism",
            annotators="Mix of trained annotators (bilingual Hindi-English speakers)",
            annotator_training="Guidelines provided for each task type with examples",
            annotation_guidelines="Detailed guidelines available in annotation_guidelines.py",
            annotation_tools="Custom annotation pipeline with heuristic pre-labeling",
            inter_annotator_agreement=iaa,
            quality_control="Two-annotator consensus required. Disagreements sent for adjudication. Gold standard items injected for quality checks.",
        )
        
        # Uses
        datasheet.uses = UsesSection(
            intended_uses=[
                "Train intent classification models for chatbot",
                "Train job category classifiers",
                "Train form field identification models",
                "Train scheme recommendation systems",
                "Research on bilingual NLP",
            ],
            not_intended_uses=[
                "Re-identification of individuals",
                "Commercial sale of data",
                "Training models for surveillance",
                "Any use violating DPDP Act",
            ],
            potential_impact="Positive: Improved access to government services for Indian citizens. Negative: Potential for model bias if data is imbalanced.",
            use_restrictions="Internal use only. Do not redistribute without authorization.",
        )
        
        # Distribution
        datasheet.distribution = DistributionSection(
            distribution_method="Internal repository access only",
            license="Proprietary - Internal Use Only",
            copyright="© 2024 Digital Sahayak Team",
            fees="Not for sale",
            access_control="Role-based access control. Requires team membership.",
            export_restrictions="Must comply with Indian DPDP Act 2023. No export of PII.",
        )
        
        # Maintenance
        datasheet.maintenance = MaintenanceSection(
            maintainers=["Digital Sahayak AI Team"],
            contact="ai-team@digitalsahayak.in",
            update_frequency="Weekly updates with new job/scheme data",
            versioning="Semantic versioning (MAJOR.MINOR.PATCH)",
            deprecation_policy="Previous versions retained for 6 months after deprecation",
            support_channels="Internal Slack channel, GitHub Issues",
        )
        
        # Bias
        bias_info = analysis.get("bias_analysis", {})
        rep_info = analysis.get("representation_analysis", {})
        
        known_biases = []
        if bias_info.get("biases_detected"):
            for bias in bias_info.get("biases", []):
                for disp in bias.get("disparities", []):
                    known_biases.append(
                        f"{bias['attribute']}: '{disp['label']}' shows disparity "
                        f"({disp['disparity_ratio']:.1%} ratio)"
                    )
        
        datasheet.bias = BiasSection(
            known_biases=known_biases or ["No significant biases detected"],
            limitations=[
                "May not represent all Indian states equally",
                "Hindi and English dominant; other regional languages underrepresented",
                "Government job data may have temporal bias (older postings)",
                "Synthetic data may not capture all real-world variations",
            ],
            bias_mitigation=[
                "Stratified sampling for regional diversity",
                "Synthetic data generation to balance rare classes",
                "Regular bias audits",
                "Diverse annotator pool",
            ],
            demographic_representation=self._extract_demographics(analysis),
        )
        
        return datasheet
    
    def _extract_demographics(self, analysis: Dict) -> Dict[str, Dict]:
        """Extract demographic representation from analysis"""
        demographics = {}
        
        # From categorical features
        cat_features = analysis.get("categorical_features", {})
        for key in ["language", "state", "category"]:
            if key in cat_features and cat_features[key].get("present"):
                top_5 = cat_features[key].get("top_5", {})
                if top_5:
                    total = sum(top_5.values())
                    demographics[key] = {k: v/total for k, v in top_5.items()}
        
        return demographics
    
    def save_datasheet(
        self,
        datasheet: Datasheet,
        output_dir: str,
        formats: List[str] = None
    ) -> Dict[str, str]:
        """
        Save datasheet in multiple formats
        
        Args:
            datasheet: The datasheet to save
            output_dir: Output directory
            formats: List of formats ("json", "markdown", "md")
        
        Returns:
            Dictionary of format to file path
        """
        formats = formats or ["json", "md"]
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        paths = {}
        base_name = datasheet.dataset_name.replace(" ", "_").lower()
        
        if "json" in formats:
            json_path = output_path / f"{base_name}_datasheet.json"
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(datasheet.to_json())
            paths["json"] = str(json_path)
            logger.info(f"Saved JSON datasheet to {json_path}")
        
        if "md" in formats or "markdown" in formats:
            md_path = output_path / f"{base_name}_datasheet.md"
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(datasheet.to_markdown())
            paths["markdown"] = str(md_path)
            logger.info(f"Saved Markdown datasheet to {md_path}")
        
        return paths


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def generate_datasheet(
    dataset_name: str,
    data: List[Dict],
    analysis: Dict,
    output_dir: str = None
) -> Datasheet:
    """
    Generate datasheet from data and analysis
    """
    generator = DatasheetGenerator()
    datasheet = generator.generate_from_analysis(dataset_name, data, analysis)
    
    if output_dir:
        generator.save_datasheet(datasheet, output_dir)
    
    return datasheet


def create_empty_datasheet(dataset_name: str) -> Datasheet:
    """
    Create empty datasheet template
    """
    return Datasheet(dataset_name=dataset_name)
