# src/shared/vector_store.py

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
from loguru import logger
from config.settings import settings

class VectorStore:
    """Vector database for evidence retrieval."""
    
    def __init__(self, persist_dir: Optional[str] = None):
        self.persist_dir = persist_dir or settings.VECTOR_DB_DIR
        self.client = chromadb.PersistentClient(
            path=self.persist_dir,
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = None
    
    def create_collection(self, name: str, reset: bool = False):
        """Create or get a collection."""
        if reset:
            try:
                self.client.delete_collection(name)
            except Exception:
                pass
        
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
        return self.collection
    
    def add_documents(
        self,
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ):
        """Add documents to the collection."""
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        logger.info(f"Added {len(documents)} documents to collection")
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """Query the collection."""
        if self.collection is None:
            raise ValueError("Collection not initialized")
        
        return self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
        )
    
    def delete_collection(self, name: str):
        """Delete a collection."""
        self.client.delete_collection(name)