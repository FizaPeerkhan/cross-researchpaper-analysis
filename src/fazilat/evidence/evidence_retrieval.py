# src/fazilat/evidence/evidence_retrieval.py

from typing import List, Dict, Any, Optional, Tuple
from loguru import logger
from src.shared.embeddings import get_embedding_model
from src.shared.vector_store import VectorStore
from src.shared.schemas import PaperExtraction, ExtractedItem, Evidence
from config.settings import settings

class EvidenceRetriever:
    """Retrieve and link evidence from papers."""
    
    def __init__(self, collection_name: str = "paper_evidence"):
        self.embedding_model = get_embedding_model()
        self.vector_store = VectorStore()
        self.collection_name = collection_name
        self.vector_store.create_collection(collection_name, reset=False)
    
    def index_paper(
        self,
        extraction: PaperExtraction,
    ) -> int:
        """Index all sentences from a paper for evidence retrieval."""
        if not extraction.structure:
            logger.warning(f"No structure for paper {extraction.paper_id}")
            return 0
        
        documents = []
        metadatas = []
        ids = []
        
        # Index all sentences with page numbers
        sentence_id = 0
        for section in extraction.structure.sections:
            sentences = self._split_sentences(section.text)
            for sentence in sentences:
                if len(sentence.strip()) < 20:
                    continue
                
                doc_id = f"{extraction.paper_id}_s{sentence_id}"
                documents.append(sentence)
                metadatas.append({
                    "paper_id": extraction.paper_id,
                    "paper_title": extraction.title,
                    "section": section.name,
                    "page_start": section.page_start,
                    "page_end": section.page_end,
                    "sentence_id": sentence_id,
                })
                ids.append(doc_id)
                sentence_id += 1
        
        if documents:
            self.vector_store.add_documents(documents, metadatas, ids)
            logger.info(f"Indexed {len(documents)} sentences from paper {extraction.paper_id}")
        
        return len(documents)
    
    def retrieve_evidence(
        self,
        query: str,
        paper_id: Optional[str] = None,
        n_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Retrieve evidence sentences for a query."""
        where = {"paper_id": paper_id} if paper_id else None
        
        results = self.vector_store.query(
            query_text=query,
            n_results=n_results,
            where=where,
        )
        
        evidence_list = []
        if results and results.get("documents"):
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results.get("metadatas") else {}
                distance = results["distances"][0][i] if results.get("distances") else 0
                
                evidence_list.append({
                    "text": doc,
                    "paper_id": metadata.get("paper_id", ""),
                    "paper_title": metadata.get("paper_title", ""),
                    "section": metadata.get("section", ""),
                    "page": metadata.get("page_start", 1),
                    "relevance_score": 1 - distance,  # Convert distance to similarity
                })
        
        return evidence_list
    
    def link_evidence_to_extraction(
        self,
        item: ExtractedItem,
        paper_id: str,
        top_k: int = 3,
    ) -> List[Evidence]:
        """Link evidence to an extracted item."""
        if item.evidence:
            return item.evidence
        
        # Retrieve evidence
        evidence_list = self.retrieve_evidence(
            query=item.value,
            paper_id=paper_id,
            n_results=top_k,
        )
        
        linked = []
        for ev in evidence_list:
            if ev["relevance_score"] > 0.5:
                linked.append(Evidence(
                    text=ev["text"],
                    page_number=ev["page"],
                    section=ev["section"],
                    confidence=ev["relevance_score"],
                ))
        
        return linked
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences."""
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        return [s.strip() for s in sentences if s.strip()]