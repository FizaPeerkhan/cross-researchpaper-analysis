# src/fazilat/cross_paper/comparison.py

from typing import List, Dict, Any, Optional, Tuple
from collections import Counter, defaultdict
from loguru import logger
from src.shared.schemas import PaperExtraction, ComparisonResult
from src.shared.embeddings import get_embedding_model
import numpy as np

class CrossPaperComparator:
    """Compare multiple papers to find patterns."""
    
    def __init__(self):
        self.embedding_model = get_embedding_model()
    
    def compare(
        self,
        extractions: List[PaperExtraction],
    ) -> ComparisonResult:
        """Compare multiple paper extractions."""
        logger.info(f"Comparing {len(extractions)} papers")
        
        result = ComparisonResult()
        
        # Count common methods
        method_counts = Counter()
        method_papers = defaultdict(list)
        for ext in extractions:
            seen = set()
            for item in ext.methods:
                method = item.value.lower().strip()
                if method and method not in seen:
                    method_counts[method] += 1
                    method_papers[method].append(ext.paper_id)
                    seen.add(method)
        
        result.common_methods = {
            method: papers
            for method, papers in method_papers.items()
            if len(papers) >= 2
        }
        
        # Count common datasets
        dataset_counts = Counter()
        dataset_papers = defaultdict(list)
        for ext in extractions:
            seen = set()
            for item in ext.datasets:
                dataset = item.value.lower().strip()
                if dataset and dataset not in seen:
                    dataset_counts[dataset] += 1
                    dataset_papers[dataset].append(ext.paper_id)
                    seen.add(dataset)
        
        result.common_datasets = {
            dataset: papers
            for dataset, papers in dataset_papers.items()
            if len(papers) >= 2
        }
        
        # Count common limitations
        limitation_clusters = self._cluster_limitations(extractions)
        result.common_limitations = limitation_clusters
        
        # Method trends
        result.method_trends = {
            "most_common": method_counts.most_common(10),
            "total_unique": len(method_counts),
        }
        
        # Dataset trends
        result.dataset_trends = {
            "most_common": dataset_counts.most_common(10),
            "total_unique": len(dataset_counts),
        }
        
        # Cluster papers by similarity
        result.clusters = self._cluster_papers(extractions)
        
        # Detect contradictions
        result.contradictions = self._detect_contradictions(extractions)
        
        return result
    
    def _cluster_limitations(
        self,
        extractions: List[PaperExtraction],
    ) -> Dict[str, List[str]]:
        """Cluster similar limitations across papers."""
        all_limitations = []
        for ext in extractions:
            for item in ext.limitations:
                all_limitations.append({
                    "text": item.value,
                    "paper_id": ext.paper_id,
                    "normalized": item.normalized_value or item.value.lower(),
                })
        
        if not all_limitations:
            return {}
        
        # Predefined limitation categories
        categories = {
            "dataset_size": [
                "small dataset", "limited data", "insufficient data",
                "dataset size", "small-scale", "few examples",
            ],
            "dataset_diversity": [
                "limited diversity", "demographic", "domain-specific",
                "single domain", "not diverse", "narrow",
            ],
            "single_dataset": [
                "single dataset", "one dataset", "only tested on",
                "only evaluated on", "single corpus",
            ],
            "generalization": [
                "generaliz", "cross-domain", "out-of-domain",
                "transfer", "robustness",
            ],
            "computational": [
                "computational", "resource", "expensive", "time-consuming",
                "efficiency", "scalability",
            ],
            "evaluation": [
                "evaluation", "metric", "benchmark", "baseline",
                "comparison", "fair",
            ],
            "methodology": [
                "method", "approach", "model", "architecture",
                "limitation of", "cannot handle",
            ],
            "language": [
                "english", "language", "multilingual", "cross-lingual",
                "low-resource",
            ],
            "annotation": [
                "annotation", "label", "manual", "human",
                "noisy", "quality",
            ],
        }
        
        # Assign limitations to categories
        clustered = defaultdict(list)
        
        for lim in all_limitations:
            text_lower = lim["normalized"]
            assigned = False
            
            for category, keywords in categories.items():
                for keyword in keywords:
                    if keyword in text_lower:
                        clustered[category].append(lim["paper_id"])
                        assigned = True
                        break
                if assigned:
                    break
            
            if not assigned:
                # Use embedding similarity for unassigned
                clustered["other"].append(lim["paper_id"])
        
        # Remove duplicates and count
        result = {}
        for category, papers in clustered.items():
            unique_papers = list(set(papers))
            if len(unique_papers) >= 2:
                result[category] = unique_papers
        
        return result
    
    def _cluster_papers(
        self,
        extractions: List[PaperExtraction],
        n_clusters: int = 3,
    ) -> Dict[str, List[str]]:
        """Cluster papers by content similarity."""
        if len(extractions) < 2:
            return {"all": [e.paper_id for e in extractions]}
        
        # Create paper representations
        texts = []
        for ext in extractions:
            text = f"{ext.title} "
            text += " ".join(item.value for item in ext.methods[:5])
            text += " " + " ".join(item.value for item in ext.datasets[:5])
            text += " " + " ".join(item.value for item in ext.tasks[:3])
            texts.append(text)
        
        # Embed
        embeddings = self.embedding_model.encode(texts)
        
        # Cluster
        from sklearn.cluster import KMeans
        n_clusters = min(n_clusters, len(extractions))
        
        if n_clusters >= 2:
            kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            labels = kmeans.fit_predict(embeddings)
        else:
            labels = [0] * len(extractions)
        
        # Group
        clusters = defaultdict(list)
        for i, label in enumerate(labels):
            clusters[f"cluster_{label}"].append(extractions[i].paper_id)
        
        return dict(clusters)
    
    def _detect_contradictions(
        self,
        extractions: List[PaperExtraction],
    ) -> List[Dict[str, Any]]:
        """Detect contradictory findings across papers."""
        contradictions = []
        
        # Group results by similar tasks
        task_results = defaultdict(list)
        for ext in extractions:
            for task in ext.tasks:
                task_key = task.value.lower().strip()
                for result in ext.results:
                    task_results[task_key].append({
                        "paper_id": ext.paper_id,
                        "result": result.value,
                        "method": ext.methods[0].value if ext.methods else "",
                    })
        
        # Look for contradictions (simple heuristic: same task, different rankings)
        for task, results in task_results.items():
            if len(results) >= 2:
                # Check if different methods claim different best results
                methods = [r["method"] for r in results if r["method"]]
                if len(set(methods)) > 1:
                    contradictions.append({
                        "type": "method_comparison",
                        "task": task,
                        "results": results,
                        "description": f"Multiple methods evaluated on {task} with different results",
                    })
        
        return contradictions