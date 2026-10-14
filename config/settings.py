# config/settings.py

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # API Keys
    GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    # Model Configs
    SCIBERT_MODEL: str = "allenai/scibert_scivocab_uncased"
    SPECTER_MODEL: str = "allenai/specter2"
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Paths
    DATA_DIR: str = "data"
    RAW_PAPERS_DIR: str = "data/raw_papers"
    PROCESSED_DIR: str = "data/processed"
    EMBEDDINGS_DIR: str = "data/embeddings"
    VECTOR_DB_DIR: str = "data/vector_db"

    # Processing
    MAX_PDF_PAGES: int = 50
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    TOP_K_EVIDENCE: int = 5

    # LLM
    LLM_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2000

    # Evaluation
    MIN_CONFIDENCE: float = 0.5

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"  # ignore unknown env vars


settings = Settings()