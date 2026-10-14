# tests/test_pdf_processing.py

import pytest
import os
from src.shared.pdf_utils import extract_pdf_content
from src.fiza.pdf_processing.section_detection import SectionDetector

def test_extract_pdf_content():
    """Test PDF content extraction."""
    # This test requires a sample PDF
    sample_pdf = "data/sample_paper.pdf"
    if not os.path.exists(sample_pdf):
        pytest.skip("Sample PDF not available")
    
    doc = extract_pdf_content(sample_pdf)
    assert doc.num_pages > 0
    assert len(doc.full_text) > 0

def test_section_detection():
    """Test section detection."""
    detector = SectionDetector()
    
    # Test heading classification
    assert detector._classify_heading("Abstract") == "abstract"
    assert detector._classify_heading("1. Introduction") == "introduction"
    assert detector._classify_heading("2. Related Work") == "related_work"
    assert detector._classify_heading("3. Method") == "method"
    assert detector._classify_heading("References") == "references"
    assert detector._classify_heading("This is a regular sentence.") is None