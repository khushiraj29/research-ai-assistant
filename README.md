# 🔬 Research AI Assistant

A **production-ready, full-stack AI assistant** that lets you upload research documents, ask natural-language questions, generate structured summaries, and explore interactive knowledge graphs — all powered by a Retrieval-Augmented Generation (RAG) pipeline, LangChain, OpenAI GPT, FAISS vector search, and Neo4j.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     Browser (Next.js 14)                     │
│  Dashboard │ Upload │ Chat │ Summaries │ Knowledge Graph      │
└─────────────────────────┬────────────────────────────────────┘
                          │ REST/JSON (Axios)
┌─────────────────────────▼────────────────────────────────────┐
│               FastAPI Backend  (Python 3.11+)                 │
│                                                               │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │  API Routes │  │ Orchestrator │  │    RAG Pipeline      │ │
│  │  /upload    │  │              │  │  ┌────────────────┐  │ │
│  │  /process   │─▶│  process_doc │─▶│  │ EmbeddingGen   │  │ │
│  │  /ask       │  │  answer_q    │  │  │ (MiniLM-L6-v2) │  │ │
│  │  /summarize │  │  summarize   │  │  ├────────────────┤  │ │
│  │  /kg        │  │  gen_kg      │  │  │ FAISSRetriever │  │ │
│  └─────────────┘  └──────┬───────┘  │  ├────────────────┤  │ │
│                          │          │  │  OpenAI GPT    │  │ │
│  ┌───────────────────────┼──────┐   │  └────────────────┘  │ │
│  │  Document Processing  │      │   └──────────────────────┘ │
│  │  extractor.py  chunker.py    │                             │
│  └───────────────────────┘      │                             │
│                                 │                             │
│  ┌──────────────────────────────▼──────────────────────────┐  │
│  │            Knowledge Graph (spaCy + Neo4j)               │  │
│  │        extractor.py          neo4j_client.py             │  │
│  └──────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────┘
          │                                      │
   ┌──────▼──────┐                     ┌────────▼────────┐
   │  FAISS Index │                     │  Neo4j Database │
   │  (disk/mem)  │                     │  (Docker)       │
   └─────────────┘                     └─────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js 14, React 18, Tailwind CSS |
| Graph visualisation | react-force-graph-2d |
| File upload | react-dropzone |
| Markdown rendering | react-markdown |
| Backend | FastAPI, Python 3.11+, Uvicorn |
| LLM & RAG | LangChain, OpenAI GPT-3.5/4 |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Vector store | FAISS (CPU) |
| Knowledge graph | spaCy en_core_web_sm + Neo4j |
| Document parsing | PyMuPDF, python-docx |
| Containerisation | Docker Compose (Neo4j) |

---

## Prerequisites

- **Python 3.11+**
- **Node.js 18+** and npm
- **Docker & Docker Compose** (for Neo4j; optional but recommended)
- An **OpenAI API key** (`gpt-3.5-turbo` or `gpt-4`)

---

## Installation

### 1. Clone and enter the repository

```bash
git clone <your-repo-url>
cd research-ai-assistant
```

### 2. Environment configuration

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Start Neo4j (optional, needed for knowledge graph persistence)

```bash
docker compose up -d
# Neo4j browser available at http://localhost:7474
# Default credentials: neo4j / password
```

### 4. Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

pip install -r requirements.txt

# Download the spaCy language model
python -m spacy download en_core_web_sm
```

### 5. Frontend setup

> **Important:** run this from the **project root** (`research-ai-assistant/`), not from inside `backend/`.

```bash
cd ..            # return to project root if you are still inside backend/
cd frontend
npm install
```

---

## Running the Application

### Start the backend

```bash
cd backend
source .venv/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### Start the frontend (in a separate terminal)

```bash
cd frontend       # run from project root
npm run dev
```

The UI will be available at `http://localhost:3000`.

---

## Running the Tests

The backend ships with a full unit-test suite that runs without any ML models or external services.

### 1. Install the lightweight test dependencies

```bash
# From the project root (research-ai-assistant/)
pip install -r requirements-test.txt
```

This installs pytest, httpx, numpy, fastapi, pydantic, and python-dotenv. The `conftest.py` stubs out all heavy ML packages (LangChain, FAISS, sentence-transformers, spaCy, Neo4j) so you do **not** need to install `requirements.txt` first.

### 2. Run the tests

```bash
# Always run pytest from the project root, NOT from inside backend/
pytest
```

Expected output: all tests collected and passing, e.g. `118 passed in 0.6s`.

---

## Quick Start Workflow

1. **Upload** – Go to `/upload`, drag a PDF/DOCX/TXT file and click **Upload**.
2. **Process** – Click **Process & Index** to chunk, embed, and store the document in FAISS.
3. **Chat** – Go to `/chat`, type a question and receive a grounded answer with source citations.
4. **Summarise** – Go to `/summaries`, select a document and a length, then generate a summary.
5. **Knowledge Graph** – Go to `/knowledge-graph`, select a document and click **Load Graph** to explore entities and relationships.

Sample documents are available in `example_documents/` to get you started immediately.

---

## API Reference

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Service health check |
| `POST` | `/upload-document` | Multipart file upload (PDF/DOCX/TXT) |
| `POST` | `/process-document` | Chunk, embed, and index an uploaded document |
| `GET` | `/documents` | List all uploaded documents |
| `POST` | `/ask-question` | RAG-based question answering |
| `POST` | `/summarize-document` | Generate document summary (short/medium/detailed) |
| `POST` | `/generate-knowledge-graph` | Extract and store entity graph for a document |
| `GET` | `/knowledge-graph` | Retrieve graph data (optionally filtered by document) |

Full interactive documentation is served at `/docs` (Swagger UI) and `/redoc`.

### Example: Ask a question

```bash
curl -X POST http://localhost:8000/ask-question \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the main findings about solar panel efficiency?", "top_k": 5}'
```

---

## Project Structure

```
research-ai-assistant/
├── backend/
│   ├── api/             # FastAPI routes and Pydantic schemas
│   ├── services/        # High-level orchestration layer
│   ├── rag/             # FAISS retriever + RAG pipeline
│   ├── embeddings/      # sentence-transformers wrapper
│   ├── knowledge_graph/ # spaCy extractor + Neo4j client
│   ├── document_processing/ # PDF/DOCX/TXT extractor + chunker
│   ├── utils/           # Config (env vars)
│   └── main.py          # FastAPI app entry point
├── frontend/
│   ├── components/      # React UI components
│   ├── pages/           # Next.js pages
│   ├── styles/          # Global Tailwind CSS
│   └── lib/api.js       # Centralised API client
├── example_documents/   # Sample research papers
├── database/            # FAISS index stored here at runtime
├── uploads/             # Uploaded documents stored here
├── docker-compose.yml   # Neo4j container definition
├── .env.example         # Environment variable template
└── README.md
```

---

## Features

- 📄 **Multi-format document ingestion** – PDF (PyMuPDF), DOCX (python-docx), plain text
- 🔍 **Semantic search** – sentence-transformers embeddings + FAISS similarity search
- 🤖 **RAG Q&A** – LangChain-orchestrated retrieval with OpenAI GPT for grounded answers and source citations
- 📝 **AI summaries** – Three summary lengths (short / medium / detailed) generated on demand
- 🕸️ **Knowledge graph** – spaCy NER + co-occurrence relationships, persisted to Neo4j, visualised with react-force-graph-2d
- 🎨 **Modern UI** – Responsive Next.js frontend with Tailwind CSS, dark-mode ready, collapsible sidebar
- ⚡ **Async backend** – Fully async FastAPI endpoints with proper error handling and structured logging
- 🐳 **Docker-ready** – Neo4j provisioned via Docker Compose; backend and frontend run locally or in containers

---

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`.
3. Commit your changes with descriptive messages.
4. Open a Pull Request against `main`.

Please ensure all Python code includes type hints and all new API endpoints have corresponding Pydantic schemas.

---

## License

This project is licensed under the **MIT License**.

```
MIT License

Copyright (c) 2024 Research AI Assistant Contributors

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
