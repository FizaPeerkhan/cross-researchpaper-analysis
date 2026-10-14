# src/fiza/information_extraction/method_extraction.py

import re
from typing import List, Dict, Any
from loguru import logger
from src.shared.schemas import ExtractedItem, Evidence

# Common method patterns in NLP/ML papers
METHOD_PATTERNS = [
    (r'\b(BERT|RoBERTa|GPT-?\d*|T5|BART|XLNet|ALBERT|DistilBERT)\b', 'transformer'),
    (r'\b(LSTM|BiLSTM|GRU|RNN|CNN|Transformer)\b', 'neural'),
    (r'\b(Random Forest|SVM|Logistic Regression|Naive Bayes|XGBoost)\b', 'traditional_ml'),
    (r'\b(fine-?tun\w+|pre-?train\w+|zero-?shot|few-?shot)\b', 'training'),
    (r'\b(attention|self-?attention|cross-?attention)\b', 'mechanism'),
    (r'\b(embedding|word2vec|GloVe|FastText)\b', 'embedding'),
]

class MethodExtractor:
    """Extract methods using pattern matching + LLM."""
    
    def __init__(self):
        self.patterns = [(re.compile(p, re.IGNORECASE), t) for p, t in METHOD_PATTERNS]
    
    def extract_pattern_based(self, text: str) -> List[ExtractedItem]:
        """Extract methods using regex patterns."""
        methods = []
        seen = set()
        
        for pattern, method_type in self.patterns:
            for match in pattern.finditer(text):
                method_name = match.group(0)
                if method_name.lower() in seen:
                    continue
                seen.add(method_name.lower())
                
                # Get context sentence
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                
                # Find the sentence containing this method
                sentences = re.split(r'(?<=[.!?])\s+', context)
                evidence_sentence = ""
                for sent in sentences:
                    if method_name.lower() in sent.lower():
                        evidence_sentence = sent.strip()
                        break
                
                methods.append(ExtractedItem(
                    value=method_name,
                    normalized_value=method_name.lower(),
                    evidence=[Evidence(
                        text=evidence_sentence,
                        page_number=1,
                        confidence=0.7,
                    )] if evidence_sentence else [],
                    confidence=0.7,
                ))
        
        return methods

class DatasetExtractor:
    """Extract datasets using pattern matching + LLM."""
    
    # Common NLP datasets
    KNOWN_DATASETS = [
        "CoNLL", "SQuAD", "GLUE", "SuperGLUE", "MNLI", "SNLI",
        "IMDB", "AG News", "DBpedia", "Yelp", "Amazon",
        "LIAR", "FakeNewsNet", "PolitiFact", "Twitter",
        "WikiText", "Penn Treebank", "OntoNotes", "ACE", "SemEval",
        "SciERC", "SciREX", "SciFact", "PubMed", "arXiv",
        "MS MARCO", "Natural Questions", "TriviaQA", "HotpotQA",
    ]
    
    def extract_pattern_based(self, text: str) -> List[ExtractedItem]:
        """Extract datasets using known names and patterns."""
        datasets = []
        seen = set()
        
        for dataset in self.KNOWN_DATASETS:
            if dataset.lower() in seen:
                continue
            
            # Look for dataset mentions
            pattern = re.compile(
                rf'\b{re.escape(dataset)}\b',
                re.IGNORECASE
            )
            
            matches = list(pattern.finditer(text))
            if matches:
                seen.add(dataset.lower())
                
                # Get context from first match
                match = matches[0]
                start = max(0, match.start() - 200)
                end = min(len(text), match.end() + 200)
                context = text[start:end]
                
                sentences = re.split(r'(?<=[.!?])\s+', context)
                evidence_sentence = ""
                for sent in sentences:
                    if dataset.lower() in sent.lower():
                        evidence_sentence = sent.strip()
                        break
                
                datasets.append(ExtractedItem(
                    value=dataset,
                    normalized_value=dataset.lower(),
                    evidence=[Evidence(
                        text=evidence_sentence,
                        page_number=1,
                        confidence=0.8,
                    )] if evidence_sentence else [],
                    confidence=0.8,
                ))
        
        return datasets