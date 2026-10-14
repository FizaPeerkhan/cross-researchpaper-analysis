# src/fazilat/research_gaps/gap_evidence.py

from typing import List, Dict, Any
from loguru import logger
from src.shared.schemas import ResearchGap, PaperExtraction, Evidence

class GapEvidenceLinker:
    """Link research gaps to supporting evidence in papers."""
    
    def link_evidence(
        self,
        gap: ResearchGap,
        extractions: List[PaperExtraction],
    ) -> ResearchGap:
        """Find and attach evidence from papers supporting this gap."""
        evidence_list = []
        
        for paper_id in gap.supporting_papers:
            # Find the extraction for this paper
            ext = next(
                (e for e in extractions if e.paper_id == paper_id),
                None
            )
            if not ext:
                continue
            
            # Look for limitations related to this gap
            for lim in ext.limitations:
                text = (lim.normalized_value or lim.value).lower()
                gap_desc = gap.description.lower()
                
                # Simple keyword overlap check
                gap_keywords = set(gap_desc.split())
                lim_keywords = set(text.split())
                overlap = gap_keywords & lim_keywords
                
                if len(overlap) >= 2 or any(
                    kw in text for kw in gap.related_limitations
                ):
                    for ev in lim.evidence:
                        evidence_list.append(Evidence(
                            text=ev.text,
                            page_number=ev.page_number,
                            section=ev.section,
                            confidence=ev.confidence,
                        ))
        
        # Deduplicate evidence
        seen = set()
        unique_evidence = []
        for ev in evidence_list:
            key = ev.text[:100]
            if key not in seen:
                seen.add(key)
                unique_evidence.append(ev)
        
        gap.evidence = unique_evidence[:5]  # Limit to top 5
        return gap