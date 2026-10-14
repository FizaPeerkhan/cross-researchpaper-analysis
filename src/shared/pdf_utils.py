# src/shared/pdf_utils.py

import fitz  # PyMuPDF
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from loguru import logger

@dataclass
class PageContent:
    page_number: int
    text: str
    blocks: List[Dict[str, Any]]

@dataclass
class PDFDocument:
    file_path: str
    title: str
    num_pages: int
    pages: List[PageContent]
    metadata: Dict[str, Any]
    
    @property
    def full_text(self) -> str:
        return "\n\n".join(p.text for p in self.pages)

def extract_pdf_content(pdf_path: str) -> PDFDocument:
    """Extract text content from a PDF using PyMuPDF."""
    logger.info(f"Extracting content from: {pdf_path}")
    
    doc = fitz.open(pdf_path)
    pages = []
    
    for page_num, page in enumerate(doc):
        text = page.get_text("text")
        blocks = page.get_text("dict")["blocks"]
        
        pages.append(PageContent(
            page_number=page_num + 1,
            text=text,
            blocks=blocks,
        ))
    
    # Extract metadata
    metadata = doc.metadata or {}
    title = metadata.get("title", "").strip()
    if not title and pages:
        # Try to extract title from first page
        first_page_lines = pages[0].text.split("\n")
        title = first_page_lines[0].strip() if first_page_lines else "Unknown"
    
    pdf_doc = PDFDocument(
        file_path=pdf_path,
        title=title,
        num_pages=len(pages),
        pages=pages,
        metadata=metadata,
    )
    
    doc.close()
    logger.info(f"Extracted {len(pages)} pages from {pdf_path}")
    return pdf_doc

def extract_text_with_positions(
    pdf_path: str,
    page_num: int,
) -> List[Dict[str, Any]]:
    """Extract text with character positions from a specific page."""
    doc = fitz.open(pdf_path)
    page = doc[page_num]
    
    blocks = page.get_text("dict")["blocks"]
    results = []
    
    for block in blocks:
        if "lines" not in block:
            continue
        for line in block["lines"]:
            for span in line["spans"]:
                results.append({
                    "text": span["text"],
                    "bbox": span["bbox"],
                    "page": page_num,
                })
    
    doc.close()
    return results

def find_sentence_in_pdf(
    pdf_path: str,
    sentence: str,
    page_hint: Optional[int] = None,
) -> Optional[Tuple[int, str]]:
    """Find a sentence in the PDF and return its page number."""
    doc = fitz.open(pdf_path)
    
    search_pages = [page_hint - 1] if page_hint else range(len(doc))
    
    for page_num in search_pages:
        if page_num < 0 or page_num >= len(doc):
            continue
        page = doc[page_num]
        text = page.get_text("text")
        
        # Normalize whitespace for matching
        normalized_text = " ".join(text.split())
        normalized_sentence = " ".join(sentence.split())
        
        if normalized_sentence.lower() in normalized_text.lower():
            doc.close()
            return (page_num + 1, text)
    
    doc.close()
    return None