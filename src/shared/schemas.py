# src/shared/schemas.py

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class EvidenceType(str, Enum):
    SUPPORTS = "supports"
    REFUTES = "refutes"
    NEUTRAL = "neutral"

class GapType(str, Enum):
    METHODOLOGICAL = "methodological"
    DATASET = "dataset"
    EVALUATION = "evaluation"
    THEORETICAL = "theoretical"
    APPLICATION = "application"

class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

class Evidence(BaseModel):
    """Evidence linking an extraction to source text."""
    text: str = Field(..., description="The exact evidence sentence(s)")
    page_number: int = Field(..., description="Page number in the PDF")
    section: Optional[str] = Field(None, description="Section name")
    char_start: Optional[int] = Field(None, description="Character start position")
    char_end: Optional[int] = Field(None, description="Character end position")
    confidence: float = Field(0.0, ge=0.0, le=1.0)
    evidence_type: EvidenceType = EvidenceType.SUPPORTS

class ExtractedItem(BaseModel):
    """A single extracted information item with evidence."""
    value: str = Field(..., description="The extracted value")
    normalized_value: Optional[str] = Field(None, description="Normalized form")
    evidence: List[Evidence] = Field(default_factory=list)
    confidence: float = Field(0.0, ge=0.0, le=1.0)

class PaperSection(BaseModel):
    """A section of a research paper."""
    name: str
    text: str
    page_start: int
    page_end: int
    subsections: List['PaperSection'] = Field(default_factory=list)

class PaperStructure(BaseModel):
    """Structured representation of a paper's content."""
    title: str
    abstract: str
    sections: List[PaperSection]
    references: List[str] = Field(default_factory=list)
    full_text: str = ""
    num_pages: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class PaperExtraction(BaseModel):
    """Complete structured extraction from a single paper."""
    paper_id: str
    title: str
    file_path: str
    
    # Core extractions
    problem: List[ExtractedItem] = Field(default_factory=list)
    methods: List[ExtractedItem] = Field(default_factory=list)
    datasets: List[ExtractedItem] = Field(default_factory=list)
    tasks: List[ExtractedItem] = Field(default_factory=list)
    metrics: List[ExtractedItem] = Field(default_factory=list)
    results: List[ExtractedItem] = Field(default_factory=list)
    limitations: List[ExtractedItem] = Field(default_factory=list)
    future_work: List[ExtractedItem] = Field(default_factory=list)
    
    # Metadata
    extraction_timestamp: datetime = Field(default_factory=datetime.now)
    model_version: str = "1.0.0"
    processing_time_seconds: float = 0.0
    
    # Raw structure
    structure: Optional[PaperStructure] = None

class ComparisonResult(BaseModel):
    """Result of comparing multiple papers."""
    common_methods: Dict[str, List[str]] = Field(default_factory=dict)
    common_datasets: Dict[str, List[str]] = Field(default_factory=dict)
    common_metrics: Dict[str, List[str]] = Field(default_factory=dict)
    common_tasks: Dict[str, List[str]] = Field(default_factory=dict)
    common_limitations: Dict[str, List[str]] = Field(default_factory=dict)
    
    method_trends: Dict[str, Any] = Field(default_factory=dict)
    dataset_trends: Dict[str, Any] = Field(default_factory=dict)
    
    clusters: Dict[str, List[str]] = Field(default_factory=dict)
    contradictions: List[Dict[str, Any]] = Field(default_factory=list)

class ResearchGap(BaseModel):
    """A candidate research gap."""
    gap_id: str
    description: str
    gap_type: GapType
    confidence: ConfidenceLevel
    supporting_papers: List[str] = Field(default_factory=list)
    evidence: List[Evidence] = Field(default_factory=list)
    suggested_direction: str = ""
    related_limitations: List[str] = Field(default_factory=list)
    frequency: int = 0  # How many papers exhibit this gap

class GapAnalysisResult(BaseModel):
    """Complete gap analysis result."""
    gaps: List[ResearchGap] = Field(default_factory=list)
    analysis_timestamp: datetime = Field(default_factory=datetime.now)
    num_papers_analyzed: int = 0
    methodology_notes: str = ""