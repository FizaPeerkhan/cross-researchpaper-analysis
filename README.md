\# Scientific Literature Intelligence



Evidence-Grounded Information Extraction and Cross-Paper Research Gap Analysis.



\## What it does



1\. Extracts structured information from research paper PDFs (methods, datasets, limitations, etc.)

2\. Grounds every extraction in evidence with page-level citations

3\. Compares multiple papers to find patterns and trends

4\. Identifies candidate research gaps with supporting evidence



\## Setup



```bash

python -m venv venv

venv\\Scripts\\activate     # Windows

pip install -r requirements.txt

python -m spacy download en\_core\_web\_sm

