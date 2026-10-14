# src/fiza/information_extraction/entity_extraction.py

import re
import json
from typing import List, Dict, Any, Optional
from loguru import logger
from config.settings import settings
from src.shared.schemas import ExtractedItem, Evidence
from src.shared.llm_client import get_llm_client
from src.shared.pdf_utils import find_sentence_in_pdf
import yaml

with open("config/prompts.yaml") as f:
    PROMPTS = yaml.safe_load(f)

class ScientificInformationExtractor:
    """Extract structured information from scientific papers."""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.prompts = PROMPTS
    
    def extract_all(
        self,
        text: str,
        paper_id: str,
        pdf_path: Optional[str] = None,
    ) -> Dict[str, List[ExtractedItem]]:
        """Extract all information types from paper text."""
        logger.info(f"Extracting information from paper: {paper_id}")
        
        # Truncate text if too long
        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[... truncated ...]"
        
        prompt = self.prompts["information_extraction"]["extract_entities"].format(
            text=text
        )
        
        system = self.prompts["information_extraction"]["system"]
        
        try:
            result = self.llm.complete_json(
                prompt=prompt,
                system=system,
            )
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            return self._empty_result()
        
        # Convert to ExtractedItem objects with evidence
        extracted = {}
        field_mapping = {
            "problem": "problem",
            "method": "methods",
            "dataset": "datasets",
            "task": "tasks",
            "metric": "metrics",
            "result": "results",
            "limitation": "limitations",
            "future_work": "future_work",
        }
        
        for json_key, schema_key in field_mapping.items():
            items = result.get(json_key, [])
            if isinstance(items, str):
                items = [items]
            elif isinstance(items, dict):
                items = [items]
            
            extracted_items = []
            for item in items:
                if isinstance(item, str):
                    value = item
                    evidence_text = None
                    confidence = 0.5
                elif isinstance(item, dict):
                    value = item.get("value", item.get("text", str(item)))
                    evidence_text = item.get("evidence", item.get("sentence"))
                    confidence = item.get("confidence", 0.5)
                else:
                    continue
                
                # Create evidence
                evidence_list = []
                if evidence_text:
                    page_num = 1
                    if pdf_path:
                        found = find_sentence_in_pdf(pdf_path, evidence_text)
                        if found:
                            page_num = found[0]
                    
                    evidence_list.append(Evidence(
                        text=evidence_text,
                        page_number=page_num,
                        confidence=confidence,
                    ))
                
                extracted_items.append(ExtractedItem(
                    value=value,
                    evidence=evidence_list,
                    confidence=confidence,
                ))
            
            extracted[schema_key] = extracted_items
        
        logger.info(f"Extracted {sum(len(v) for v in extracted.values())} items")
        return extracted
    
    def _empty_result(self) -> Dict[str, List[ExtractedItem]]:
        return {
            "problem": [],
            "methods": [],
            "datasets": [],
            "tasks": [],
            "metrics": [],
            "results": [],
            "limitations": [],
            "future_work": [],
        }