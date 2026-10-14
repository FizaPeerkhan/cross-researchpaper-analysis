# src/fiza/pdf_processing/section_detection.py

import re
from typing import List, Dict, Optional, Tuple
from loguru import logger
from src.shared.schemas import PaperSection, PaperStructure
from src.shared.pdf_utils import PDFDocument

# Common section headers in scientific papers
SECTION_PATTERNS = {
    "abstract": [
        r"^abstract\b",
        r"^a\s*b\s*s\s*t\s*r\s*a\s*c\s*t\b",
    ],
    "introduction": [
        r"^1\.?\s*introduction",
        r"^introduction\b",
        r"^i\.?\s*introduction",
    ],
    "related_work": [
        r"^2\.?\s*related\s+work",
        r"^related\s+work",
        r"^literature\s+review",
        r"^background",
    ],
    "method": [
        r"^3\.?\s*method",
        r"^method",
        r"^approach",
        r"^proposed\s+method",
        r"^our\s+approach",
        r"^model",
        r"^system",
    ],
    "experiments": [
        r"^4\.?\s*experiment",
        r"^experiment",
        r"^evaluation",
        r"^experimental\s+setup",
        r"^results",
    ],
    "results": [
        r"^5\.?\s*results?",
        r"^results?\s+and\s+discussion",
        r"^discussion",
    ],
    "conclusion": [
        r"^6\.?\s*conclusion",
        r"^conclusion",
        r"^conclusions?\s+and\s+future\s+work",
    ],
    "limitations": [
        r"^limitations?\b",
        r"^limitations?\s+and\s+future\s+work",
    ],
    "future_work": [
        r"^future\s+work",
        r"^future\s+directions",
    ],
    "references": [
        r"^references?\b",
        r"^bibliography\b",
    ],
    "acknowledgments": [
        r"^acknowledg",
    ],
    "appendix": [
        r"^appendix",
        r"^supplementary",
    ],
}

class SectionDetector:
    """Detect sections in a research paper."""
    
    def __init__(self):
        self.patterns = {}
        for section, patterns in SECTION_PATTERNS.items():
            self.patterns[section] = [
                re.compile(p, re.IGNORECASE) for p in patterns
            ]
    
    def _classify_heading(self, line: str) -> Optional[str]:
        """Classify a line as a section heading."""
        line = line.strip()
        if not line or len(line) > 100:
            return None
        
        # Remove numbering
        cleaned = re.sub(r'^[\d\.\s]+', '', line).strip()
        
        for section, patterns in self.patterns.items():
            for pattern in patterns:
                if pattern.match(cleaned) or pattern.match(line):
                    return section
        
        # Check if line looks like a heading (short, title case, etc.)
        if self._looks_like_heading(line):
            return "other"
        
        return None
    
    def _looks_like_heading(self, line: str) -> bool:
        """Heuristic to detect if a line is a heading."""
        line = line.strip()
        
        # Too long
        if len(line) > 80:
            return False
        
        # Ends with period (likely sentence)
        if line.endswith('.'):
            return False
        
        # All caps
        if line.isupper() and len(line) > 3:
            return True
        
        # Title case with numbering
        if re.match(r'^\d+\.?\s+[A-Z]', line):
            return True
        
        # Bold-like patterns (starts with number)
        if re.match(r'^\d+\.\d+\s+', line):
            return True
        
        return False
    
    def detect_sections(self, pdf_doc: PDFDocument) -> PaperStructure:
        """Detect sections in a PDF document."""
        logger.info(f"Detecting sections in: {pdf_doc.title}")
        
        # Get all lines with page info
        all_lines = []
        for page in pdf_doc.pages:
            for line in page.text.split("\n"):
                all_lines.append({
                    "text": line,
                    "page": page.page_number,
                })
        
        # Find headings
        headings = []
        for i, line_info in enumerate(all_lines):
            section = self._classify_heading(line_info["text"])
            if section:
                headings.append({
                    "section": section,
                    "text": line_info["text"].strip(),
                    "page": line_info["page"],
                    "line_idx": i,
                })
        
        # Build sections
        sections = []
        for i, heading in enumerate(headings):
            start_idx = heading["line_idx"] + 1
            end_idx = headings[i + 1]["line_idx"] if i + 1 < len(headings) else len(all_lines)
            
            content_lines = [
                all_lines[j]["text"] for j in range(start_idx, end_idx)
            ]
            content = "\n".join(content_lines).strip()
            
            if content or heading["section"] in ["abstract"]:
                sections.append(PaperSection(
                    name=heading["text"],
                    text=content,
                    page_start=heading["page"],
                    page_end=all_lines[end_idx - 1]["page"] if end_idx > start_idx else heading["page"],
                ))
        
        # If no sections detected, create one big section
        if not sections:
            sections = [PaperSection(
                name="Full Text",
                text=pdf_doc.full_text,
                page_start=1,
                page_end=pdf_doc.num_pages,
            )]
        
        # Extract abstract
        abstract = self._extract_abstract(sections, pdf_doc)
        
        # Extract references
        references = self._extract_references(sections)
        
        return PaperStructure(
            title=pdf_doc.title,
            abstract=abstract,
            sections=sections,
            references=references,
            full_text=pdf_doc.full_text,
            num_pages=pdf_doc.num_pages,
            metadata=pdf_doc.metadata,
        )
    
    def _extract_abstract(
        self,
        sections: List[PaperSection],
        pdf_doc: PDFDocument,
    ) -> str:
        """Extract the abstract from the paper."""
        # Try to find abstract section
        for section in sections:
            if "abstract" in section.name.lower():
                return section.text
        
        # Try to find abstract in first page
        first_page = pdf_doc.pages[0].text if pdf_doc.pages else ""
        abstract_match = re.search(
            r'[Aa]bstract[\s:—-]*(.*?)(?:\n\s*\n|\n[A-Z][a-z]+\s)',
            first_page,
            re.DOTALL
        )
        if abstract_match:
            return abstract_match.group(1).strip()
        
        # Return first 500 chars of first page as fallback
        return first_page[:500].strip()
    
    def _extract_references(self, sections: List[PaperSection]) -> List[str]:
        """Extract references from the paper."""
        for section in sections:
            if "reference" in section.name.lower() or "bibliography" in section.name.lower():
                refs = re.split(r'\n(?=\[\d+\]|\d+\.\s)', section.text)
                return [r.strip() for r in refs if r.strip()]
        return []

def get_section_text(structure: PaperStructure, section_names: List[str]) -> str:
    """Get text from specific sections."""
    texts = []
    for section in structure.sections:
        section_lower = section.name.lower()
        for name in section_names:
            if name.lower() in section_lower:
                texts.append(section.text)
                break
    return "\n\n".join(texts)