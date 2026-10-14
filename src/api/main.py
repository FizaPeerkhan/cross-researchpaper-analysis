# src/api/main.py

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import os
import json
import uuid
from datetime import datetime
from loguru import logger

from config.settings import settings
from src.shared.schemas import (
    PaperExtraction, ComparisonResult, GapAnalysisResult
)
from src.fiza.structured_output.json_builder import PaperProcessor
from src.fazilat.cross_paper.comparison import CrossPaperComparator
from src.fazilat.cross_paper.trend_analysis import TrendAnalyzer
from src.fazilat.research_gaps.gap_detection import GapDetector
from src.fazilat.evidence.evidence_retrieval import EvidenceRetriever

app = FastAPI(
    title="Scientific Literature Intelligence API",
    description="Extract information from research papers and identify research gaps",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
paper_processor = PaperProcessor()
comparator = CrossPaperComparator()
trend_analyzer = TrendAnalyzer()
gap_detector = GapDetector()
evidence_retriever = EvidenceRetriever()

# In-memory store (use database in production)
papers_store = {}
extractions_store = {}


@app.get("/")
async def root():
    return {
        "name": "Scientific Literature Intelligence API",
        "version": "1.0.0",
        "endpoints": [
            "/upload",
            "/extract/{paper_id}",
            "/papers",
            "/compare",
            "/analyze",
            "/gaps",
            "/evidence",
        ],
    }


@app.post("/upload")
async def upload_paper(file: UploadFile = File(...)):
    """Upload a PDF paper."""
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files are supported")
    
    paper_id = str(uuid.uuid4())[:8]
    
    # Save file
    os.makedirs(settings.RAW_PAPERS_DIR, exist_ok=True)
    filepath = os.path.join(settings.RAW_PAPERS_DIR, f"{paper_id}.pdf")
    
    content = await file.read()
    with open(filepath, "wb") as f:
        f.write(content)
    
    papers_store[paper_id] = {
        "paper_id": paper_id,
        "filename": file.filename,
        "filepath": filepath,
        "uploaded_at": datetime.now().isoformat(),
    }
    
    logger.info(f"Uploaded paper {paper_id}: {file.filename}")
    
    return {
        "paper_id": paper_id,
        "filename": file.filename,
        "status": "uploaded",
    }


@app.post("/extract/{paper_id}")
async def extract_paper(paper_id: str):
    """Extract structured information from a paper."""
    if paper_id not in papers_store:
        raise HTTPException(404, f"Paper {paper_id} not found")
    
    paper_info = papers_store[paper_id]
    
    try:
        extraction = paper_processor.process_paper(
            pdf_path=paper_info["filepath"],
            paper_id=paper_id,
        )
        
        # Save extraction
        paper_processor.save_extraction(extraction)
        extractions_store[paper_id] = extraction
        
        # Index for evidence retrieval
        evidence_retriever.index_paper(extraction)
        
        return {
            "paper_id": paper_id,
            "status": "extracted",
            "extraction": extraction.model_dump(),
        }
    except Exception as e:
        logger.error(f"Extraction failed for {paper_id}: {e}")
        raise HTTPException(500, f"Extraction failed: {str(e)}")


@app.get("/papers")
async def list_papers():
    """List all uploaded papers."""
    papers = []
    for paper_id, info in papers_store.items():
        extraction = extractions_store.get(paper_id)
        papers.append({
            "paper_id": paper_id,
            "filename": info["filename"],
            "uploaded_at": info["uploaded_at"],
            "extracted": extraction is not None,
            "title": extraction.title if extraction else None,
        })
    return {"papers": papers, "total": len(papers)}


@app.get("/extract/{paper_id}")
async def get_extraction(paper_id: str):
    """Get extraction for a paper."""
    if paper_id in extractions_store:
        return extractions_store[paper_id].model_dump()
    
    # Try to load from disk
    filepath = os.path.join(settings.PROCESSED_DIR, f"{paper_id}.json")
    if os.path.exists(filepath):
        extraction = PaperProcessor.load_extraction(filepath)
        extractions_store[paper_id] = extraction
        return extraction.model_dump()
    
    raise HTTPException(404, f"Extraction for {paper_id} not found")


@app.post("/compare")
async def compare_papers(paper_ids: List[str]):
    """Compare multiple papers."""
    extractions = []
    for pid in paper_ids:
        if pid in extractions_store:
            extractions.append(extractions_store[pid])
        else:
            filepath = os.path.join(settings.PROCESSED_DIR, f"{pid}.json")
            if os.path.exists(filepath):
                extractions.append(PaperProcessor.load_extraction(filepath))
    
    if len(extractions) < 2:
        raise HTTPException(400, "Need at least 2 papers to compare")
    
    result = comparator.compare(extractions)
    trends = trend_analyzer.analyze(extractions)
    
    return {
        "comparison": result.model_dump(),
        "trends": trends,
        "num_papers": len(extractions),
    }


@app.post("/gaps")
async def detect_gaps(paper_ids: List[str]):
    """Detect research gaps from multiple papers."""
    extractions = []
    for pid in paper_ids:
        if pid in extractions_store:
            extractions.append(extractions_store[pid])
        else:
            filepath = os.path.join(settings.PROCESSED_DIR, f"{pid}.json")
            if os.path.exists(filepath):
                extractions.append(PaperProcessor.load_extraction(filepath))
    
    if len(extractions) < 2:
        raise HTTPException(400, "Need at least 2 papers to detect gaps")
    
    result = gap_detector.detect_gaps(extractions)
    
    return result.model_dump()


@app.get("/evidence")
async def get_evidence(
    query: str,
    paper_id: Optional[str] = None,
    top_k: int = 5,
):
    """Retrieve evidence for a query."""
    evidence = evidence_retriever.retrieve_evidence(
        query=query,
        paper_id=paper_id,
        n_results=top_k,
    )
    return {"query": query, "evidence": evidence}


@app.post("/analyze")
async def full_analysis(paper_ids: List[str]):
    """Run full analysis pipeline."""
    extractions = []
    for pid in paper_ids:
        if pid in extractions_store:
            extractions.append(extractions_store[pid])
        else:
            filepath = os.path.join(settings.PROCESSED_DIR, f"{pid}.json")
            if os.path.exists(filepath):
                extractions.append(PaperProcessor.load_extraction(filepath))
    
    if len(extractions) < 2:
        raise HTTPException(400, "Need at least 2 papers")
    
    comparison = comparator.compare(extractions)
    trends = trend_analyzer.analyze(extractions)
    gaps = gap_detector.detect_gaps(extractions)
    
    return {
        "num_papers": len(extractions),
        "comparison": comparison.model_dump(),
        "trends": trends,
        "gaps": gaps.model_dump(),
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)