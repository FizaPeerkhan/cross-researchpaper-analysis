# tests/test_cross_paper.py

import pytest
from src.fazilat.cross_paper.comparison import CrossPaperComparator
from src.fazilat.cross_paper.trend_analysis import TrendAnalyzer
from src.shared.schemas import PaperExtraction, ExtractedItem, Evidence

def create_mock_extraction(paper_id: str, methods: list, datasets: list) -> PaperExtraction:
    """Create a mock extraction for testing."""
    return PaperExtraction(
        paper_id=paper_id,
        title=f"Paper {paper_id}",
        file_path="",
        methods=[
            ExtractedItem(value=m, evidence=[Evidence(text=f"Using {m}", page_number=1)])
            for m in methods
        ],
        datasets=[
            ExtractedItem(value=d, evidence=[Evidence(text=f"On {d}", page_number=1)])
            for d in datasets
        ],
        limitations=[
            ExtractedItem(value="Small dataset", evidence=[Evidence(text="The dataset is small", page_number=1)])
        ],
    )

def test_cross_paper_comparison():
    """Test cross-paper comparison."""
    comparator = CrossPaperComparator()
    
    extractions = [
        create_mock_extraction("1", ["BERT", "LSTM"], ["CoNLL"]),
        create_mock_extraction("2", ["BERT", "CNN"], ["CoNLL"]),
        create_mock_extraction("3", ["RoBERTa"], ["SQuAD"]),
    ]
    
    result = comparator.compare(extractions)
    
    # BERT should be common
    assert "bert" in result.common_methods
    assert len(result.common_methods["bert"]) == 2
    
    # CoNLL should be common
    assert "conll" in result.common_datasets

def test_trend_analysis():
    """Test trend analysis."""
    analyzer = TrendAnalyzer()
    
    extractions = [
        create_mock_extraction("1", ["BERT", "LSTM"], ["CoNLL"]),
        create_mock_extraction("2", ["BERT", "CNN"], ["CoNLL"]),
        create_mock_extraction("3", ["BERT"], ["SQuAD"]),
    ]
    
    trends = analyzer.analyze(extractions)
    
    assert "method_frequency" in trends
    assert trends["method_frequency"].get("bert", 0) == 3