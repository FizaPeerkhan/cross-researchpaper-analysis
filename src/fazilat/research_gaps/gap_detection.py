# src/fazilat/research_gaps/gap_detection.py

import uuid
from typing import List, Dict, Any, Optional
from collections import defaultdict
from loguru import logger
from src.shared.schemas import (
    PaperExtraction, ResearchGap, GapAnalysisResult,
    GapType, ConfidenceLevel, Evidence
)
from src.shared.llm_client import get_llm_client
from src.fazilat.cross_paper.comparison import CrossPaperComparator
from src.fazilat.cross_paper.trend_analysis import TrendAnalyzer
import yaml

with open("config/prompts.yaml") as f:
    PROMPTS = yaml.safe_load(f)

class GapDetector:
    """Detect candidate research gaps from multiple papers."""
    
    def __init__(self):
        self.llm = get_llm_client()
        self.comparator = CrossPaperComparator()
        self.trend_analyzer = TrendAnalyzer()
        self.prompts = PROMPTS
    
    def detect_gaps(
        self,
        extractions: List[PaperExtraction],
    ) -> GapAnalysisResult:
        """Detect research gaps from multiple papers."""
        logger.info(f"Detecting gaps from {len(extractions)} papers")
        
        result = GapAnalysisResult(
            num_papers_analyzed=len(extractions),
        )
        
        # 1. Rule-based gap detection
        rule_based_gaps = self._detect_rule_based_gaps(extractions)
        
        # 2. LLM-based gap detection
        llm_gaps = self._detect_llm_gaps(extractions)
        
        # 3. Merge and rank
        all_gaps = rule_based_gaps + llm_gaps
        result.gaps = self._merge_and_rank_gaps(all_gaps)
        
        result.methodology_notes = (
            "Gaps detected using: (1) rule-based analysis of recurring limitations, "
            "under-explored method-dataset combinations, and contradictions; "
            "(2) LLM-based analysis of paper summaries. "
            "All gaps are CANDIDATE gaps requiring human validation."
        )
        
        logger.info(f"Detected {len(result.gaps)} candidate research gaps")
        return result
    
    def _detect_rule_based_gaps(
        self,
        extractions: List[PaperExtraction],
    ) -> List[ResearchGap]:
        """Detect gaps using rules and patterns."""
        gaps = []
        
        # 1. Dataset size limitation gap
        small_dataset_papers = []
        for ext in extractions:
            for lim in ext.limitations:
                text = (lim.normalized_value or lim.value).lower()
                if any(kw in text for kw in ["small dataset", "limited data", "insufficient data"]):
                    small_dataset_papers.append(ext.paper_id)
        
        if len(small_dataset_papers) >= 2:
            gaps.append(ResearchGap(
                gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                description="Limited dataset sizes across studies",
                gap_type=GapType.DATASET,
                confidence=ConfidenceLevel.HIGH if len(small_dataset_papers) >= 3 else ConfidenceLevel.MEDIUM,
                supporting_papers=list(set(small_dataset_papers)),
                suggested_direction="Develop or utilize larger-scale datasets for more robust evaluation",
                related_limitations=["small dataset", "limited data"],
                frequency=len(set(small_dataset_papers)),
            ))
        
        # 2. Single dataset evaluation gap
        single_dataset_papers = []
        for ext in extractions:
            for lim in ext.limitations:
                text = (lim.normalized_value or lim.value).lower()
                if any(kw in text for kw in ["single dataset", "one dataset", "only tested on"]):
                    single_dataset_papers.append(ext.paper_id)
        
        if len(single_dataset_papers) >= 2:
            gaps.append(ResearchGap(
                gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                description="Most studies evaluate on a single dataset",
                gap_type=GapType.EVALUATION,
                confidence=ConfidenceLevel.HIGH if len(single_dataset_papers) >= 3 else ConfidenceLevel.MEDIUM,
                supporting_papers=list(set(single_dataset_papers)),
                suggested_direction="Multi-dataset evaluation and cross-domain validation",
                related_limitations=["single dataset", "only tested on"],
                frequency=len(set(single_dataset_papers)),
            ))
        
        # 3. Generalization gap
        generalization_papers = []
        for ext in extractions:
            for lim in ext.limitations:
                text = (lim.normalized_value or lim.value).lower()
                if any(kw in text for kw in ["generaliz", "cross-domain", "out-of-domain", "transfer"]):
                    generalization_papers.append(ext.paper_id)
        
        if len(generalization_papers) >= 2:
            gaps.append(ResearchGap(
                gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                description="Limited cross-domain generalization of methods",
                gap_type=GapType.METHODOLOGICAL,
                confidence=ConfidenceLevel.MEDIUM,
                supporting_papers=list(set(generalization_papers)),
                suggested_direction="Investigate domain adaptation and transfer learning approaches",
                related_limitations=["generalization", "cross-domain"],
                frequency=len(set(generalization_papers)),
            ))
        
        # 4. Under-explored method-dataset combinations
        method_dataset_combos = defaultdict(list)
        all_methods = set()
        all_datasets = set()
        
        for ext in extractions:
            methods = [m.value.lower().strip() for m in ext.methods]
            datasets = [d.value.lower().strip() for d in ext.datasets]
            all_methods.update(methods)
            all_datasets.update(datasets)
            
            for method in methods:
                for dataset in datasets:
                    method_dataset_combos[(method, dataset)].append(ext.paper_id)
        
        # Find methods never combined with certain datasets
        for method in all_methods:
            method_datasets = set()
            for (m, d), papers in method_dataset_combos.items():
                if m == method:
                    method_datasets.add(d)
            
            unexplored = all_datasets - method_datasets
            if len(unexplored) >= 3 and len(method_datasets) <= 2:
                gaps.append(ResearchGap(
                    gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                    description=f"Method '{method}' has limited dataset coverage",
                    gap_type=GapType.METHODOLOGICAL,
                    confidence=ConfidenceLevel.LOW,
                    supporting_papers=[],
                    suggested_direction=f"Evaluate {method} on additional datasets: {', '.join(list(unexplored)[:3])}",
                    frequency=1,
                ))
        
        # 5. Limited diversity gap
        diversity_papers = []
        for ext in extractions:
            for lim in ext.limitations:
                text = (lim.normalized_value or lim.value).lower()
                if any(kw in text for kw in ["diversity", "demographic", "bias", "fairness"]):
                    diversity_papers.append(ext.paper_id)
        
        if len(diversity_papers) >= 2:
            gaps.append(ResearchGap(
                gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                description="Limited demographic and linguistic diversity in datasets",
                gap_type=GapType.DATASET,
                confidence=ConfidenceLevel.MEDIUM,
                supporting_papers=list(set(diversity_papers)),
                suggested_direction="Create more diverse and representative datasets",
                related_limitations=["diversity", "demographic"],
                frequency=len(set(diversity_papers)),
            ))
        
        # 6. Multilingual gap
        multilingual_papers = []
        for ext in extractions:
            for lim in ext.limitations:
                text = (lim.normalized_value or lim.value).lower()
                if any(kw in text for kw in ["english", "multilingual", "cross-lingual", "low-resource language"]):
                    multilingual_papers.append(ext.paper_id)
        
        if len(multilingual_papers) >= 2:
            gaps.append(ResearchGap(
                gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                description="Limited multilingual and cross-lingual evaluation",
                gap_type=GapType.EVALUATION,
                confidence=ConfidenceLevel.MEDIUM,
                supporting_papers=list(set(multilingual_papers)),
                suggested_direction="Extend methods to multilingual settings and low-resource languages",
                related_limitations=["english", "multilingual"],
                frequency=len(set(multilingual_papers)),
            ))
        
        return gaps
    
    def _detect_llm_gaps(
        self,
        extractions: List[PaperExtraction],
    ) -> List[ResearchGap]:
        """Detect gaps using LLM analysis."""
        if not extractions:
            return []
        
        # Create paper summaries
        summaries = []
        for ext in extractions:
            summary = {
                "paper_id": ext.paper_id,
                "title": ext.title,
                "methods": [m.value for m in ext.methods[:5]],
                "datasets": [d.value for d in ext.datasets[:5]],
                "tasks": [t.value for t in ext.tasks[:3]],
                "limitations": [l.value[:200] for l in ext.limitations[:5]],
                "future_work": [f.value[:200] for f in ext.future_work[:3]],
            }
            summaries.append(summary)
        
        import json
        summaries_text = json.dumps(summaries, indent=2)
        
        prompt = self.prompts["gap_detection"]["detect_gaps"].format(
            paper_analyses=summaries_text[:8000]
        )
        
        system = self.prompts["gap_detection"]["system"]
        
        try:
            result = self.llm.complete_json(prompt=prompt, system=system)
            gaps_data = result.get("gaps", [])
            
            gaps = []
            for gap_data in gaps_data:
                gap_type = GapType.METHODOLOGICAL
                type_str = gap_data.get("gap_type", "").lower()
                if "dataset" in type_str:
                    gap_type = GapType.DATASET
                elif "evaluation" in type_str:
                    gap_type = GapType.EVALUATION
                elif "theoretical" in type_str:
                    gap_type = GapType.THEORETICAL
                elif "application" in type_str:
                    gap_type = GapType.APPLICATION
                
                confidence = ConfidenceLevel.MEDIUM
                conf_str = gap_data.get("confidence", "").lower()
                if "high" in conf_str:
                    confidence = ConfidenceLevel.HIGH
                elif "low" in conf_str:
                    confidence = ConfidenceLevel.LOW
                
                gaps.append(ResearchGap(
                    gap_id=f"gap_{uuid.uuid4().hex[:8]}",
                    description=gap_data.get("description", ""),
                    gap_type=gap_type,
                    confidence=confidence,
                    supporting_papers=gap_data.get("supporting_papers", []),
                    suggested_direction=gap_data.get("suggested_direction", ""),
                    frequency=len(gap_data.get("supporting_papers", [])),
                ))
            
            return gaps
        except Exception as e:
            logger.error(f"LLM gap detection failed: {e}")
            return []
    
    def _merge_and_rank_gaps(
        self,
        gaps: List[ResearchGap],
    ) -> List[ResearchGap]:
        """Merge similar gaps and rank by importance."""
        if not gaps:
            return []
        
        # Simple deduplication by description similarity
        merged = []
        seen_descriptions = set()
        
        for gap in gaps:
            desc_key = " ".join(gap.description.lower().split()[:5])
            if desc_key in seen_descriptions:
                continue
            seen_descriptions.add(desc_key)
            merged.append(gap)
        
        # Rank by: confidence, frequency, type priority
        type_priority = {
            GapType.METHODOLOGICAL: 3,
            GapType.DATASET: 2,
            GapType.EVALUATION: 2,
            GapType.APPLICATION: 1,
            GapType.THEORETICAL: 1,
        }
        
        confidence_priority = {
            ConfidenceLevel.HIGH: 3,
            ConfidenceLevel.MEDIUM: 2,
            ConfidenceLevel.LOW: 1,
        }
        
        merged.sort(
            key=lambda g: (
                confidence_priority.get(g.confidence, 0),
                g.frequency,
                type_priority.get(g.gap_type, 0),
            ),
            reverse=True,
        )
        
        return merged