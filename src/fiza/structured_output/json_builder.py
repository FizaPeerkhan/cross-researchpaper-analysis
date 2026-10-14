# src/fiza/structured_output/json_builder.py

import json
import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger
from config.settings import settings
from src.shared.schemas import PaperExtraction, PaperStructure, ExtractedItem, Evidence
from src.shared.pdf_utils import extract_pdf_content, PDFDocument
from src.fiza.pdf_processing.section_detection import SectionDetector, get_section_text
from src.fiza.information_extraction.entity_extraction import ScientificInformationExtractor
from src.fiza.information_extraction.method_extraction import MethodExtractor, DatasetExtractor
from src.fiza.information_extraction.limitation_extraction import LimitationExtractor, FutureWorkExtractor

class PaperProcessor:
    """Complete pipeline: PDF → Structured JSON."""
    
    def __init__(self):
        self.section_detector = SectionDetector()
        self.ie_extractor = ScientificInformationExtractor()
        self.method_extractor = MethodExtractor()
        self.dataset_extractor = DatasetExtractor()
        self.limitation_extractor = LimitationExtractor()
        self.future_work_extractor = FutureWorkExtractor()
    
    def process_paper(
        self,
        pdf_path: str,
        paper_id: Optional[str] = None,
    ) -> PaperExtraction:
        """Process a single paper end-to-end."""
        import time
        start_time = time.time()
        
        paper_id = paper_id or str(uuid.uuid4())[:8]
        logger.info(f"Processing paper {paper_id}: {pdf_path}")
        
        # Step 1: Extract PDF content
        pdf_doc = extract_pdf_content(pdf_path)
        
        # Step 2: Detect sections
        structure = self.section_detector.detect_sections(pdf_doc)
        
        # Step 3: Extract information
        # Get relevant text sections
        full_text = structure.full_text
        
        # Combine pattern-based and LLM-based extraction
        extracted = self.ie_extractor.extract_all(
            text=full_text,
            paper_id=paper_id,
            pdf_path=pdf_path,
        )
        
        # Add pattern-based extractions
        pattern_methods = self.method_extractor.extract_pattern_based(full_text)
        pattern_datasets = self.dataset_extractor.extract_pattern_based(full_text)
        pattern_limitations = self.limitation_extractor.extract_pattern_based(full_text)
        pattern_future = self.future_work_extractor.extract_pattern_based(full_text)
        
        # Merge and deduplicate
        extracted["methods"] = self._merge_items(
            extracted.get("methods", []), pattern_methods
        )
        extracted["datasets"] = self._merge_items(
            extracted.get("datasets", []), pattern_datasets
        )
        extracted["limitations"] = self._merge_items(
            extracted.get("limitations", []), pattern_limitations
        )
        extracted["future_work"] = self._merge_items(
            extracted.get("future_work", []), pattern_future
        )
        
        processing_time = time.time() - start_time
        
        # Build result
        result = PaperExtraction(
            paper_id=paper_id,
            title=structure.title,
            file_path=pdf_path,
            problem=extracted.get("problem", []),
            methods=extracted.get("methods", []),
            datasets=extracted.get("datasets", []),
            tasks=extracted.get("tasks", []),
            metrics=extracted.get("metrics", []),
            results=extracted.get("results", []),
            limitations=extracted.get("limitations", []),
            future_work=extracted.get("future_work", []),
            processing_time_seconds=processing_time,
            structure=structure,
        )
        
        logger.info(
            f"Processed paper {paper_id} in {processing_time:.2f}s: "
            f"{len(result.methods)} methods, {len(result.datasets)} datasets, "
            f"{len(result.limitations)} limitations"
        )
        
        return result
    
    def _merge_items(
        self,
        items1: List[ExtractedItem],
        items2: List[ExtractedItem],
    ) -> List[ExtractedItem]:
        """Merge two lists of extracted items, removing duplicates."""
        seen = set()
        merged = []
        
        for item in items1 + items2:
            key = (item.value or "").lower().strip()
            if key and key not in seen:
                seen.add(key)
                merged.append(item)
        
        return merged
    
    def save_extraction(
        self,
        extraction: PaperExtraction,
        output_dir: Optional[str] = None,
    ) -> str:
        """Save extraction to JSON file."""
        output_dir = output_dir or settings.PROCESSED_DIR
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        filepath = os.path.join(output_dir, f"{extraction.paper_id}.json")
        
        with open(filepath, "w") as f:
            json.dump(extraction.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Saved extraction to {filepath}")
        return filepath
    
    @staticmethod
    def load_extraction(filepath: str) -> PaperExtraction:
        """Load extraction from JSON file."""
        with open(filepath) as f:
            data = json.load(f)
        return PaperExtraction(**data)