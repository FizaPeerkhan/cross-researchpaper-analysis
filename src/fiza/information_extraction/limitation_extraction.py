# src/fiza/information_extraction/limitation_extraction.py

import re
from typing import List, Dict, Any
from loguru import logger
from src.shared.schemas import ExtractedItem, Evidence
from src.shared.llm_client import get_llm_client

class LimitationExtractor:
    """Extract limitations from papers."""
    
    # Patterns indicating limitations
    LIMITATION_PATTERNS = [
        r'(?:however|but|although|though|while|nevertheless)[^.]*\.',
        r'(?:limitation|drawback|weakness|shortcoming|constraint)[^.]*\.',
        r'(?:fail|unable|cannot|does not|doesn\'t)[^.]*\.',
        r'(?:future work|future research|further investigation)[^.]*\.',
        r'(?:only|just|merely|simply)[^.]*\.',
        r'(?:small|limited|insufficient|inadequate)[^.]*\.',
    ]
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.LIMITATION_PATTERNS]
        self.llm = get_llm_client()
    
    def extract_pattern_based(self, text: str) -> List[ExtractedItem]:
        """Extract limitation-like sentences using patterns."""
        limitations = []
        seen = set()
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 500:
                continue
            
            for pattern in self.patterns:
                if pattern.search(sentence):
                    normalized = " ".join(sentence.lower().split())
                    if normalized in seen:
                        continue
                    seen.add(normalized)
                    
                    # Skip if it's just a citation
                    if re.match(r'^\[\d+\]', sentence):
                        continue
                    
                    limitations.append(ExtractedItem(
                        value=sentence,
                        normalized_value=normalized,
                        evidence=[Evidence(
                            text=sentence,
                            page_number=1,
                            confidence=0.6,
                        )],
                        confidence=0.6,
                    ))
                    break
        
        return limitations
    
    def extract_llm_based(
        self,
        text: str,
        max_limitations: int = 10,
    ) -> List[ExtractedItem]:
        """Extract limitations using LLM."""
        prompt = f"""Extract all explicit and implicit limitations from the following research paper text.

Focus on:
1. Explicitly stated limitations
2. Dataset limitations (size, diversity, domain)
3. Method limitations
4. Evaluation limitations
5. Generalizability concerns

For each limitation, provide:
- The limitation description (concise)
- The exact sentence(s) as evidence
- Confidence score (0-1)

Text:
{text[:8000]}

Output as JSON with format:
{{
  "limitations": [
    {{"value": "...", "evidence": "...", "confidence": 0.8}}
  ]
}}
"""
        
        try:
            result = self.llm.complete_json(prompt)
            items = result.get("limitations", [])
            
            extracted = []
            for item in items:
                if isinstance(item, dict):
                    extracted.append(ExtractedItem(
                        value=item.get("value", ""),
                        evidence=[Evidence(
                            text=item.get("evidence", ""),
                            page_number=1,
                            confidence=item.get("confidence", 0.5),
                        )],
                        confidence=item.get("confidence", 0.5),
                    ))
            
            return extracted[:max_limitations]
        except Exception as e:
            logger.error(f"LLM limitation extraction failed: {e}")
            return []

class FutureWorkExtractor:
    """Extract future work suggestions from papers."""
    
    FUTURE_PATTERNS = [
        r'(?:future work|future research|further study|further investigation|next steps)[^.]*\.',
        r'(?:could be|can be|should be|might be|may be)\s+(?:extended|improved|applied|explored|investigated)[^.]*\.',
        r'(?:leave|left)\s+(?:for|as)\s+future[^.]*\.',
        r'(?:promising|interesting|important)\s+(?:direction|avenue|research)[^.]*\.',
    ]
    
    def __init__(self):
        self.patterns = [re.compile(p, re.IGNORECASE) for p in self.FUTURE_PATTERNS]
        self.llm = get_llm_client()
    
    def extract_pattern_based(self, text: str) -> List[ExtractedItem]:
        """Extract future work sentences."""
        items = []
        seen = set()
        
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 20 or len(sentence) > 500:
                continue
            
            for pattern in self.patterns:
                if pattern.search(sentence):
                    normalized = " ".join(sentence.lower().split())
                    if normalized in seen:
                        continue
                    seen.add(normalized)
                    
                    items.append(ExtractedItem(
                        value=sentence,
                        normalized_value=normalized,
                        evidence=[Evidence(
                            text=sentence,
                            page_number=1,
                            confidence=0.6,
                        )],
                        confidence=0.6,
                    ))
                    break
        
        return items