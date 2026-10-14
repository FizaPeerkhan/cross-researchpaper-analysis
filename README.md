# 📄 Complete `README.md`

Create `README.md` in the **root of your project** (`C:\Users\fizap\mitproj\scientific-literature-intelligence\README.md`) with this content:

```markdown
# 🔬 Scientific Literature Intelligence System

**Evidence-Grounded Information Extraction and Cross-Paper Research Gap Analysis**

A complete end-to-end system that extracts structured information from scientific research papers (PDFs), grounds every extraction in page-level evidence, compares multiple papers to find patterns, and identifies candidate research gaps.

---

## ✨ Features

### 📄 Paper Understanding & Information Extraction
- **PDF Processing**: Extract text, sections, and metadata from research paper PDFs
- **Section Detection**: Automatically identify Abstract, Introduction, Methods, Results, Limitations, Future Work
- **Scientific Information Extraction**: Extract structured fields:
  - Research Problem
  - Methods (BERT, LSTM, SVM, etc.)
  - Datasets (CoNLL, SQuAD, LIAR, etc.)
  - Tasks (NER, Classification, QA, etc.)
  - Metrics (F1, Accuracy, Precision, Recall)
  - Results
  - Limitations
  - Future Work
- **Evidence Grounding**: Every extraction links back to the exact sentence and page in the source PDF

### 📊 Cross-Paper Analysis
- **Evidence Retrieval**: Vector-based search across all indexed papers
- **Evidence Verification**: Verify extracted claims against source text
- **Multi-Paper Comparison**: Find common methods, datasets, metrics, and limitations
- **Trend Detection**: Identify emerging methods and datasets
- **Contradiction Detection**: Flag conflicting findings across papers
- **Paper Clustering**: Group papers by content similarity

### 🔍 Research Gap Detection
- **Rule-Based Gaps**: Detect recurring limitations and under-explored method-dataset combinations
- **LLM-Based Gaps**: Use language models to identify candidate research directions
- **Evidence Linking**: Attach supporting evidence (paper + page) to every candidate gap
- **Confidence Scoring**: Rank gaps by confidence and frequency
- **Gap Types**: Methodological, Dataset, Evaluation, Theoretical, Application

### 🖥️ Interactive Dashboard
- **📤 Upload Papers**: Batch upload PDFs and auto-extract information
- **📄 Paper Explorer**: View structured extraction per paper with evidence
- **📊 Cross-Paper Analysis**: Compare methods, datasets, and trends with charts
- **🔍 Research Gaps**: Browse candidate gaps with supporting evidence
- **🔎 Evidence Viewer**: Search evidence across all papers by semantic query

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    USER (Streamlit Dashboard)               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                          │
│  /upload  /extract  /compare  /gaps  /evidence              │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ FIZA'S MODULE │    │FAZILAT'S MOD. │    │ SHARED UTILS  │
│               │    │               │    │               │
│ Paper → JSON  │───▶│ JSON → Gaps   │    │ • PDF Store   │
│               │    │               │    │ • Vector DB   │
│ • PDF Parse   │    │ • Evidence    │    │ • LLM Client  │
│ • Sections    │    │ • Compare     │    │ • Embeddings  │
│ • Extract     │    │ • Gaps        │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
```

---

## 📁 Project Structure

```
scientific-literature-intelligence/
│
├── config/
│   ├── settings.py              # Pydantic settings (API keys, paths)
│   └── prompts.yaml             # LLM prompts for extraction
│
├── data/
│   ├── raw_papers/              # Uploaded PDFs
│   ├── processed/               # Extracted JSON per paper
│   ├── embeddings/              # Vector embeddings
│   └── vector_db/               # ChromaDB persistent storage
│
├── src/
│   ├── shared/                  # Shared utilities
│   │   ├── schemas.py           # Pydantic models
│   │   ├── pdf_utils.py         # PDF text extraction
│   │   ├── llm_client.py        # LLM interface (Groq/Gemini/OpenAI)
│   │   ├── embeddings.py        # Sentence transformer wrapper
│   │   └── vector_store.py      # ChromaDB wrapper
│   │
│   ├── fiza/                    # Paper Understanding Module
│   │   ├── pdf_processing/
│   │   │   └── section_detection.py
│   │   ├── information_extraction/
│   │   │   ├── entity_extraction.py
│   │   │   ├── method_extraction.py
│   │   │   └── limitation_extraction.py
│   │   ├── structured_output/
│   │   │   └── json_builder.py  # Complete pipeline
│   │   └── evaluation/
│   │       └── evaluate_ie.py
│   │
│   ├── fazilat/                 # Cross-Paper Analysis Module
│   │   ├── evidence/
│   │   │   ├── evidence_retrieval.py
│   │   │   └── evidence_verification.py
│   │   ├── cross_paper/
│   │   │   ├── comparison.py
│   │   │   └── trend_analysis.py
│   │   ├── research_gaps/
│   │   │   ├── gap_detection.py
│   │   │   └── gap_evidence.py
│   │   └── evaluation/
│   │       └── evaluate_gaps.py
│   │
│   └── api/                     # FastAPI backend
│       └── main.py
│
├── frontend/
│   └── app.py                   # Streamlit dashboard
│
├── scripts/
│   ├── download_datasets.py
│   └── run_pipeline.py
│
├── tests/                       # pytest tests
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yaml
└── README.md
```

---

## 🚀 Quick Start

### Prerequisites

- **Python 3.11 or 3.12** ([python.org](https://www.python.org/downloads/))
- **Git** (optional, for cloning)
- An API key from one of the LLM providers (see below)

### 1. Clone / Download

```bash
git clone https://github.com/FizaPeerkhan/cross-researchpaper-analysis.git
cd cross-researchpaper-analysis
```

Or, if you already have the folder, just `cd` into it.

### 2. Create a Virtual Environment

**Windows (PowerShell):**
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
```

**Windows (CMD):**
```cmd
python -m venv venv
venv\Scripts\activate.bat
```

**Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### 3. Install Dependencies

```bash
python -m pip install --upgrade pip setuptools wheel

# Optional (recommended): CPU-only PyTorch — much smaller download
pip install torch --index-url https://download.pytorch.org/whl/cpu

# Install everything else
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 4. Configure the LLM Provider

The system supports **Groq**, **Google Gemini**, **OpenAI**, and **Anthropic**. Groq is recommended (free, fast, no credit card).

#### Get a Groq API key (recommended)

1. Go to https://console.groq.com/keys
2. Sign in with Google or GitHub
3. Click **Create API Key**
4. Copy the key (starts with `gsk_`)

#### Create `.env`

```bash
cp .env.example .env      # Linux/macOS
copy .env.example .env    # Windows
```

Edit `.env` and add your key:

```env
GROQ_API_KEY=gsk_your_key_here
GEMINI_API_KEY=
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
```

> Only **one** key is needed. The system auto-picks the first available provider (Groq → Gemini → OpenAI → Anthropic).

#### Verify the LLM works

```bash
python -c "from src.shared.llm_client import get_llm_client; print(get_llm_client().complete('Say hi', max_tokens=20))"
```

Expected:
```
INFO     | src.shared.llm_client:_initialize:58 - LLM provider: Groq (openai/gpt-oss-120b)
Hi! How can I help you today?
```

### 5. Run the System

You need **two terminals** running at the same time.

**Terminal 1 — API (FastAPI):**
```bash
cd scientific-literature-intelligence
venv\Scripts\Activate.ps1       # Windows
uvicorn src.api.main:app --reload --port 8000
```

Wait for:
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Application startup complete.
```

Test: open http://localhost:8000/docs in your browser — you should see the Swagger UI.

**Terminal 2 — Dashboard (Streamlit):**
```bash
cd scientific-literature-intelligence
venv\Scripts\Activate.ps1       # Windows
streamlit run frontend/app.py
```

Opens automatically at http://localhost:8501

### 6. Use the System

1. **📤 Upload Papers** — Upload 3–10 PDFs on the same topic
2. Wait for auto-extraction (methods, datasets, limitations)
3. **📄 Paper Explorer** — Inspect each paper's structured extraction
4. **📊 Cross-Paper Analysis** — See common methods, datasets, and trends
5. **🔍 Research Gaps** — Detect candidate research gaps with evidence
6. **🔎 Evidence Viewer** — Search evidence across papers

---

## 🔑 LLM Provider Comparison

| Provider | Free Tier | Sign-up Complexity | Recommended |
|----------|-----------|-------------------|-------------|
| **Groq** | ✅ 30 req/min, 14,400 req/day | ✅ Sign in with Google/GitHub | ⭐ **Yes** |
| Google Gemini | ✅ 15 req/min, 1,500 req/day | ⚠️ Account verification required | No |
| OpenAI | ❌ Paid only | ✅ Simple | Only if paid |
| Anthropic | ❌ Paid only | ✅ Simple | Only if paid |

The system auto-detects which key you have — no code changes needed.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|------------|
| PDF extraction | **PyMuPDF** (fitz), pdfplumber |
| LLM providers | **Groq** (`openai/gpt-oss-120b`), Google Gemini, OpenAI, Anthropic |
| Embeddings | **sentence-transformers** (`all-MiniLM-L6-v2`) |
| Vector store | **ChromaDB** |
| API | **FastAPI** + Uvicorn |
| Dashboard | **Streamlit** + Plotly + Altair |
| Data validation | **Pydantic v2** |
| Logging | **Loguru** |
| Containerization | Docker + docker-compose |

---

## 📊 Example Workflow

Upload 10 NLP papers about misinformation detection:

### Step 1 — Extraction (Fiza's module)

For each paper, the system extracts:

```json
{
  "paper_id": "paper_001",
  "title": "BERT-based Misinformation Detection",
  "problem": [{"value": "Misinformation detection", "confidence": 0.9}],
  "methods": [{"value": "BERT", "confidence": 0.95}],
  "datasets": [{"value": "LIAR", "confidence": 0.9}],
  "metrics": [{"value": "F1", "confidence": 0.85}],
  "results": [{"value": "82%", "confidence": 0.8}],
  "limitations": [
    {"value": "Small dataset size", "evidence": [{"text": "...", "page_number": 7}]}
  ]
}
```

### Step 2 — Cross-Paper Analysis (Fazilat's module)

```
Common methods:    BERT (7/10), RoBERTa (3/10), LSTM (2/10)
Common datasets:   LIAR (4/10), FakeNewsNet (3/10)
Common limitations: Small dataset (5/10), Single dataset (4/10)
```

### Step 3 — Research Gaps

```
🟢 HIGH   "Limited multi-dataset evaluation" — 5 papers
🟡 MEDIUM "Cross-domain validation is limited" — 3 papers
🟡 MEDIUM "Lack of multilingual evaluation" — 3 papers
🔴 LOW    "Under-explored method X on dataset Y"
```

Each gap links to **evidence**: exact sentence + page from the source paper.

---

## 🐛 Troubleshooting

| Error | Fix |
|-------|-----|
| `ModuleNotFoundError: No module named 'src'` | Run from the project root (`cd scientific-literature-intelligence`) |
| `ModuleNotFoundError: No module named 'config'` | Create `config/__init__.py` |
| `FileNotFoundError: config/prompts.yaml` | Create the file with the YAML content |
| `NameError: name 'Optional' is not defined` | Add `from typing import Optional` at the top of the file |
| `numpy` / `pyarrow` version conflict | `pip install "numpy>=2.0.0"` |
| `ConnectionRefusedError: localhost:8000` | Start the API in a separate terminal |
| `Address already in use` | Change port: `uvicorn ... --port 8001` (and update `API_URL` in `frontend/app.py`) |
| Groq `404 model_not_found` | Update `GROQ_MODEL` in `llm_client.py` to a current model name |
| Groq `429 rate_limit_exceeded` | Wait 60 seconds; free tier is 30 req/min |
| Streamlit shows "API Offline" | Check the API terminal for errors |

---

## 🧪 Testing

Run the test suite:

```bash
pytest tests/ -v
```

Run a specific test file:

```bash
pytest tests/test_information_extraction.py -v
```

---

## 🐳 Docker (Optional)

```bash
docker-compose up --build
```

- API: http://localhost:8000
- Dashboard: http://localhost:8501

---

## 📖 Datasets Used for Training / Evaluation

The information extraction and evidence verification components are designed to be trained/evaluated on standard scientific NLP datasets:

- **SciERC** — Scientific entity and relation extraction
- **SciREX** — Document-level information extraction
- **SciFact** — Scientific fact verification

Download them with:

```bash
python scripts/download_datasets.py
```

---

## 📝 Project Ownership

| Module | Owner | Responsibility |
|--------|-------|----------------|
| Paper Understanding & Information Extraction | **Fiza** | PDF → Structured JSON with evidence |
| Cross-Paper Analysis & Gap Detection | **Fazilat** | JSON → Comparison → Candidate Gaps |
| Research design, experiments, evaluation | **Both** | Methodology, papers, demo |

---

## 📄 License

MIT License. See `LICENSE` for details.

---

## 🙏 Acknowledgements

- [SciBERT](https://github.com/allenai/scibert) — scientific text embeddings
- [SPECTER](https://github.com/allenai/specter) — scientific paper embeddings
- [ChromaDB](https://www.trychroma.com/) — vector database
- [Streamlit](https://streamlit.io/) — dashboard framework
- [FastAPI](https://fastapi.tiangolo.com/) — API framework
- [Groq](https://groq.com/) — fast LLM inference

---

## 📬 Contact

- **Fiza Peer Khan** — [GitHub](https://github.com/FizaPeerkhan)
- Project Repository: https://github.com/FizaPeerkhan/cross-researchpaper-analysis
```

---

## 📋 How to Save It

### Option 1: Create Manually

```powershell
cd C:\Users\fizap\mitproj\scientific-literature-intelligence
notepad README.md
```

Paste the content above, **Ctrl+S**, close Notepad.

### Option 2: One Command (PowerShell)

Save this block into a file `create_readme.ps1`, then run it — but it's simpler to just create it manually via Notepad.

---

## ✅ Verify It Saved

```powershell
Get-Content README.md | Select-Object -First 5
```

Should print:
```
# 🔬 Scientific Literature Intelligence System

**Evidence-Grounded Information Extraction and Cross-Paper Research Gap Analysis**
```

---

## 🎬 Next Steps

After saving `README.md`:

```powershell
cd C:\Users\fizap\mitproj\scientific-literature-intelligence

# Create .gitignore first (see earlier message)
# Then:
git init
git branch -M main
git add .
git status       # ← verify README.md and .gitignore are listed, venv/ is NOT
git commit -m "Initial commit: Scientific Literature Intelligence System"
git remote add origin https://github.com/FizaPeerkhan/cross-researchpaper-analysis.git
git push -u origin main
```

