# tests/test_information_extraction.py

import pytest
from src.fiza.information_extraction.method_extraction import MethodExtractor, DatasetExtractor
from src.fiza.information_extraction.limitation_extraction import LimitationExtractor

def test_method_extraction():
    """Test method extraction from text."""
    extractor = MethodExtractor()
    
    text = """
    We propose a BERT-based model for text classification. 
    Our approach uses a fine-tuned BERT model with an additional 
    classification head. We compare against LSTM and CNN baselines.
    """
    
    methods = extractor.extract_pattern_based(text)
    method_values = [m.value.lower() for m in methods]
    
    assert "bert" in method_values or any("bert" in m for m in method_values)
    assert len(methods) > 0

def test_dataset_extraction():
    """Test dataset extraction."""
    extractor = DatasetExtractor()
    
    text = """
    We evaluate our model on the CoNLL-2003 dataset for NER.
    We also test on SQuAD for question answering.
    """
    
    datasets = extractor.extract_pattern_based(text)
    dataset_values = [d.value for d in datasets]
    
    assert "CoNLL" in dataset_values
    assert "SQuAD" in dataset_values

def test_limitation_extraction():
    """Test limitation extraction."""
    extractor = LimitationExtractor()
    
    text = """
    However, our model was only tested on English data.
    The dataset is relatively small with only 5,000 examples.
    Future work should explore multilingual settings.
    """
    
    limitations = extractor.extract_pattern_based(text)
    assert len(limitations) > 0