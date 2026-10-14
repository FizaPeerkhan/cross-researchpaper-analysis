# tests/test_gap_detection.py

import pytest
from src.fazilat.research_gaps.gap_detection import GapDetector
from src.shared.schemas import PaperExtraction, ExtractedItem, Evidence, GapType

def create_mock_paper(paper_id: str, limitations: list) -> PaperExtraction:
    """Create a mock paper with limitations."""
    return PaperExtraction(
        paper_id=paper_id,
        title=f"Paper {paper_id}",
        file_path="",
        limitations=[
            ExtractedItem(
                value=lim,
                normalized_value=lim.lower(),
                evidence=[Evidence(text=lim, page_number=1)],
            )
            for lim in limitations
        ],
    )

def test_gap_detection():
    """Test research gap detection."""
    detector = GapDetector()
    
    extractions = [
        create_mock_paper("1", ["Small dataset size", "Only tested on English"]),
        create_mock_paper("2", ["Limited dataset", "Single dataset evaluation"]),
        create_mock_paper("3", ["Small dataset", "Limited diversity"]),
    ]
    
    result = detector.detect_gaps(extractions)
    
    assert result.num_papers_analyzed == 3
    assert len(result.gaps) > 0
    
    # Should detect dataset-related gap
    dataset_gaps = [g for g in result.gaps if g.gap_type == GapType.DATASET]
    assert len(dataset_gaps) > 0