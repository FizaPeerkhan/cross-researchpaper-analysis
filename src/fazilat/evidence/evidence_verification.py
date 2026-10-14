# src/fazilat/evidence/evidence_verification.py

from typing import List, Dict, Any, Optional
from loguru import logger
from src.shared.schemas import ExtractedItem, Evidence, EvidenceType
from src.shared.llm_client import get_llm_client
import yaml

with open("config/prompts.yaml") as f:
    PROMPTS = yaml.safe_load(f)

class EvidenceVerifier:
    """Verify extracted claims against evidence."""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.prompts = PROMPTS
    
    def verify_claim(
        self,
        claim: str,
        claim_type: str,
        candidate_evidence: List[str],
    ) -> Dict[str, Any]:
        """Verify a claim against candidate evidence."""
        if not candidate_evidence:
            return {"verdict": "no_evidence", "confidence": 0.0}
        
        candidates_text = "\n".join(
            f"[{i+1}] {ev}" for i, ev in enumerate(candidate_evidence)
        )
        
        prompt = self.prompts["evidence_verification"]["verify"].format(
            claim=claim,
            claim_type=claim_type,
            candidates=candidates_text,
        )
        
        system = self.prompts["evidence_verification"]["system"]
        
        try:
            result = self.llm.complete_json(prompt=prompt, system=system)
            return result
        except Exception as e:
            logger.error(f"Verification failed: {e}")
            return {"verdict": "error", "confidence": 0.0}
    
    def verify_extraction(
        self,
        item: ExtractedItem,
        paper_id: str,
        retriever: 'EvidenceRetriever',
    ) -> ExtractedItem:
        """Verify an extracted item and update its evidence."""
        # Get candidate evidence
        candidates = retriever.retrieve_evidence(
            query=item.value,
            paper_id=paper_id,
            n_results=5,
        )
        
        candidate_texts = [c["text"] for c in candidates]
        
        # Verify
        verification = self.verify_claim(
            claim=item.value,
            claim_type="extraction",
            candidate_evidence=candidate_texts,
        )
        
        # Update evidence
        verified_evidence = []
        verdict = verification.get("verdict", "neutral")
        
        for i, cand in enumerate(candidates):
            ev_type = EvidenceType.NEUTRAL
            if i == 0 and verdict == "SUPPORTS":
                ev_type = EvidenceType.SUPPORTS
            elif verdict == "REFUTES":
                ev_type = EvidenceType.REFUTES
            
            verified_evidence.append(Evidence(
                text=cand["text"],
                page_number=cand["page"],
                section=cand.get("section", ""),
                confidence=cand["relevance_score"],
                evidence_type=ev_type,
            ))
        
        item.evidence = verified_evidence
        return item