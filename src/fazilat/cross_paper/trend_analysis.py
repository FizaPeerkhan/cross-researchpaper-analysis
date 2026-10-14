# src/fazilat/cross_paper/trend_analysis.py

from typing import List, Dict, Any
from collections import Counter
from loguru import logger
from src.shared.schemas import PaperExtraction

class TrendAnalyzer:
    """Analyze trends across papers."""
    
    def analyze(
        self,
        extractions: List[PaperExtraction],
    ) -> Dict[str, Any]:
        """Analyze trends in methods, datasets, and research focus."""
        trends = {
            "method_frequency": self._count_frequencies(extractions, "methods"),
            "dataset_frequency": self._count_frequencies(extractions, "datasets"),
            "task_frequency": self._count_frequencies(extractions, "tasks"),
            "metric_frequency": self._count_frequencies(extractions, "metrics"),
            "limitation_frequency": self._count_frequencies(extractions, "limitations"),
            "emerging_methods": self._find_emerging(extractions, "methods"),
            "emerging_datasets": self._find_emerging(extractions, "datasets"),
            "gap_indicators": self._find_gap_indicators(extractions),
        }
        return trends
    
    def _count_frequencies(
        self,
        extractions: List[PaperExtraction],
        field: str,
    ) -> Dict[str, int]:
        """Count frequency of values in a field."""
        counter = Counter()
        for ext in extractions:
            seen = set()
            for item in getattr(ext, field, []):
                value = item.normalized_value or item.value.lower().strip()
                if value and value not in seen:
                    counter[value] += 1
                    seen.add(value)
        return dict(counter.most_common(20))
    
    def _find_emerging(
        self,
        extractions: List[PaperExtraction],
        field: str,
    ) -> List[Dict[str, Any]]:
        """Find emerging methods/datasets (appearing in fewer papers but notable)."""
        counter = Counter()
        for ext in extractions:
            seen = set()
            for item in getattr(ext, field, []):
                value = item.normalized_value or item.value.lower().strip()
                if value and value not in seen:
                    counter[value] += 1
                    seen.add(value)
        
        total = len(extractions)
        emerging = []
        
        for value, count in counter.items():
            frequency = count / total if total > 0 else 0
            # Emerging: 10-40% frequency
            if 0.1 <= frequency <= 0.4:
                emerging.append({
                    "value": value,
                    "count": count,
                    "frequency": frequency,
                })
        
        return sorted(emerging, key=lambda x: x["frequency"], reverse=True)
    
    def _find_gap_indicators(
        self,
        extractions: List[PaperExtraction],
    ) -> List[Dict[str, Any]]:
        """Find indicators of research gaps."""
        indicators = []
        
        # 1. Methods mentioned in future work but not explored
        future_methods = set()
        used_methods = set()
        
        for ext in extractions:
            for item in ext.future_work:
                # Simple extraction of method-like terms
                text = item.value.lower()
                for method in ["bert", "transformer", "llm", "gpt", "multilingual",
                               "cross-lingual", "few-shot", "zero-shot", "multimodal"]:
                    if method in text:
                        future_methods.add(method)
            
            for item in ext.methods:
                used_methods.add(item.value.lower().strip())
        
        underexplored = future_methods - used_methods
        if underexplored:
            indicators.append({
                "type": "underexplored_methods",
                "items": list(underexplored),
                "description": "Methods suggested in future work but not widely used",
            })
        
        # 2. Datasets used in only one paper
        dataset_papers = Counter()
        for ext in extractions:
            for item in ext.datasets:
                dataset_papers[item.value.lower().strip()] += 1
        
        single_use_datasets = [
            ds for ds, count in dataset_papers.items() if count == 1
        ]
        if single_use_datasets:
            indicators.append({
                "type": "single_use_datasets",
                "items": single_use_datasets[:10],
                "description": "Datasets used in only one paper (potential lack of standardization)",
            })
        
        # 3. Common limitations suggesting gaps
        limitation_papers = Counter()
        for ext in extractions:
            for item in ext.limitations:
                text = item.normalized_value or item.value.lower()
                for keyword in ["small", "single", "limited", "only", "lack"]:
                    if keyword in text:
                        limitation_papers[keyword] += 1
        
        if limitation_papers:
            indicators.append({
                "type": "recurring_limitations",
                "items": dict(limitation_papers.most_common(5)),
                "description": "Limitations recurring across multiple papers",
            })
        
        return indicators