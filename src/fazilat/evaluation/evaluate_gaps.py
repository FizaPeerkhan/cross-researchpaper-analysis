# src/fazilat/evaluation/evaluate_gaps.py

from typing import List, Dict, Any, Set
from collections import Counter
from loguru import logger
from src.shared.schemas import ResearchGap, GapAnalysisResult

class GapEvaluator:
    """Evaluate quality of detected research gaps."""
    
    def evaluate(
        self,
        result: GapAnalysisResult,
        gold_gaps: List[str] = None,
    ) -> Dict[str, Any]:
        """Evaluate gap detection results."""
        metrics = {
            "num_gaps": len(result.gaps),
            "num_papers": result.num_papers_analyzed,
            "avg_frequency": 0.0,
            "confidence_distribution": {},
            "type_distribution": {},
            "evidence_coverage": 0.0,
        }
        
        if result.gaps:
            metrics["avg_frequency"] = sum(g.frequency for g in result.gaps) / len(result.gaps)
            
            # Confidence distribution
            conf_counts = Counter(g.confidence.value for g in result.gaps)
            metrics["confidence_distribution"] = dict(conf_counts)
            
            # Type distribution
            type_counts = Counter(g.gap_type.value for g in result.gaps)
            metrics["type_distribution"] = dict(type_counts)
            
            # Evidence coverage
            gaps_with_evidence = sum(1 for g in result.gaps if g.evidence)
            metrics["evidence_coverage"] = gaps_with_evidence / len(result.gaps)
        
        # If gold standard provided, compute precision/recall
        if gold_gaps:
            detected_descriptions = [g.description.lower() for g in result.gaps]
            gold_lower = [g.lower() for g in gold_gaps]
            
            true_positives = 0
            for gold in gold_lower:
                for detected in detected_descriptions:
                    # Simple overlap check
                    gold_words = set(gold.split())
                    detected_words = set(detected.split())
                    if len(gold_words & detected_words) / max(len(gold_words), 1) > 0.5:
                        true_positives += 1
                        break
            
            precision = true_positives / len(detected_descriptions) if detected_descriptions else 0
            recall = true_positives / len(gold_lower) if gold_lower else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics.update({
                "precision": precision,
                "recall": recall,
                "f1": f1,
            })
        
        return metrics
    
    def human_evaluation_template(
        self,
        result: GapAnalysisResult,
    ) -> List[Dict[str, Any]]:
        """Create a template for human evaluation of gaps."""
        templates = []
        
        for gap in result.gaps:
            templates.append({
                "gap_id": gap.gap_id,
                "description": gap.description,
                "type": gap.gap_type.value,
                "confidence": gap.confidence.value,
                "supporting_papers": gap.supporting_papers,
                "suggested_direction": gap.suggested_direction,
                "evidence_count": len(gap.evidence),
                # Human evaluation fields
                "is_valid": None,  # Yes/No
                "is_novel": None,  # Yes/No/Already known
                "is_significant": None,  # 1-5
                "comments": "",
            })
        
        return templates