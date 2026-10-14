# src/fiza/evaluation/evaluate_ie.py

import json
from typing import List, Dict, Any, Tuple
from collections import defaultdict
from loguru import logger
from src.shared.schemas import PaperExtraction, ExtractedItem

class IEEvaluator:
    """Evaluate information extraction quality."""
    
    def __init__(self):
        self.results = defaultdict(list)
    
    def evaluate_extraction(
        self,
        predicted: PaperExtraction,
        gold: Dict[str, List[str]],
    ) -> Dict[str, float]:
        """Evaluate a single extraction against gold standard."""
        metrics = {}
        
        for field in ["methods", "datasets", "tasks", "metrics", "limitations"]:
            predicted_values = set(
                item.value.lower().strip()
                for item in getattr(predicted, field, [])
                if item.value
            )
            gold_values = set(v.lower().strip() for v in gold.get(field, []))
            
            if not gold_values:
                continue
            
            true_positives = len(predicted_values & gold_values)
            precision = true_positives / len(predicted_values) if predicted_values else 0
            recall = true_positives / len(gold_values) if gold_values else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            
            metrics[f"{field}_precision"] = precision
            metrics[f"{field}_recall"] = recall
            metrics[f"{field}_f1"] = f1
            
            self.results[field].append({
                "precision": precision,
                "recall": recall,
                "f1": f1,
            })
        
        return metrics
    
    def evaluate_evidence_quality(
        self,
        extraction: PaperExtraction,
        pdf_text: str,
    ) -> Dict[str, float]:
        """Evaluate the quality of evidence grounding."""
        total_items = 0
        items_with_evidence = 0
        evidence_in_text = 0
        
        for field in ["methods", "datasets", "limitations", "future_work"]:
            for item in getattr(extraction, field, []):
                total_items += 1
                if item.evidence:
                    items_with_evidence += 1
                    for ev in item.evidence:
                        # Check if evidence text appears in PDF
                        normalized_ev = " ".join(ev.text.lower().split())
                        normalized_pdf = " ".join(pdf_text.lower().split())
                        if normalized_ev in normalized_pdf:
                            evidence_in_text += 1
                            break
        
        return {
            "evidence_coverage": items_with_evidence / total_items if total_items > 0 else 0,
            "evidence_accuracy": evidence_in_text / items_with_evidence if items_with_evidence > 0 else 0,
        }
    
    def get_aggregate_metrics(self) -> Dict[str, Dict[str, float]]:
        """Get aggregate metrics across all evaluations."""
        aggregate = {}
        for field, results in self.results.items():
            if results:
                aggregate[field] = {
                    "avg_precision": sum(r["precision"] for r in results) / len(results),
                    "avg_recall": sum(r["recall"] for r in results) / len(results),
                    "avg_f1": sum(r["f1"] for r in results) / len(results),
                    "num_samples": len(results),
                }
        return aggregate