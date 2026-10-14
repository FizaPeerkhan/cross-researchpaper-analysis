# scripts/run_pipeline.py

"""Run the full pipeline on a directory of PDFs."""

import os
import sys
import json
from loguru import logger
from tqdm import tqdm

from src.fiza.structured_output.json_builder import PaperProcessor
from src.fazilat.cross_paper.comparison import CrossPaperComparator
from src.fazilat.cross_paper.trend_analysis import TrendAnalyzer
from src.fazilat.research_gaps.gap_detection import GapDetector
from src.fazilat.evidence.evidence_retrieval import EvidenceRetriever

def run_pipeline(
    pdf_dir: str,
    output_dir: str = "data/processed",
    analyze: bool = True,
):
    """Run the complete pipeline."""
    # Find PDFs
    pdfs = [
        os.path.join(pdf_dir, f)
        for f in os.listdir(pdf_dir)
        if f.endswith(".pdf")
    ]
    
    if not pdfs:
        logger.error(f"No PDFs found in {pdf_dir}")
        return
    
    logger.info(f"Found {len(pdfs)} PDFs")
    
    # Process each paper
    processor = PaperProcessor()
    retriever = EvidenceRetriever()
    extractions = []
    
    for pdf_path in tqdm(pdfs, desc="Processing papers"):
        try:
            paper_id = os.path.splitext(os.path.basename(pdf_path))[0]
            extraction = processor.process_paper(pdf_path, paper_id)
            processor.save_extraction(extraction, output_dir)
            retriever.index_paper(extraction)
            extractions.append(extraction)
            logger.info(f"Processed: {paper_id}")
        except Exception as e:
            logger.error(f"Failed to process {pdf_path}: {e}")
    
    if analyze and len(extractions) >= 2:
        # Cross-paper analysis
        logger.info("Running cross-paper analysis...")
        comparator = CrossPaperComparator()
        comparison = comparator.compare(extractions)
        
        trend_analyzer = TrendAnalyzer()
        trends = trend_analyzer.analyze(extractions)
        
        # Gap detection
        logger.info("Detecting research gaps...")
        gap_detector = GapDetector()
        gaps = gap_detector.detect_gaps(extractions)
        
        # Save results
        results = {
            "num_papers": len(extractions),
            "comparison": comparison.model_dump(),
            "trends": trends,
            "gaps": gaps.model_dump(),
        }
        
        results_path = os.path.join(output_dir, "analysis_results.json")
        with open(results_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info(f"Saved analysis results to {results_path}")
        logger.info(f"Detected {len(gaps.gaps)} candidate research gaps")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run scientific literature pipeline")
    parser.add_argument("pdf_dir", help="Directory containing PDF files")
    parser.add_argument("--output", default="data/processed", help="Output directory")
    parser.add_argument("--no-analyze", action="store_true", help="Skip cross-paper analysis")
    
    args = parser.parse_args()
    run_pipeline(args.pdf_dir, args.output, not args.no_analyze)