# Quill — Document Intelligence

> Upload PDFs. Ask questions. Get grounded answers with citations.

Quill is a full-stack Retrieval-Augmented Generation (RAG) application that lets you have intelligent conversations with your documents. It retrieves the most relevant passages from your uploaded PDFs and uses GPT-4o mini to generate accurate, cited answers — never hallucinating beyond what your documents actually say.


---

## Features

- **Hybrid search** — combines vector similarity (ChromaDB) and keyword matching (BM25) for superior retrieval
- **Reranking** — retrieves 12 candidates, re-scores them for relevance, passes only the best 4 to the LLM
- **Query rewriting** — automatically fixes typos and expands informal queries before embedding
- **Conversation memory** — maintains chat history so follow-up questions work naturally
- **Source citations** — every answer shows exactly which document and chunk it came from, with confidence scores
- **Per-document filtering** — ask questions scoped to a single document or across your entire library
- **Drag-and-drop upload** — PDF files up to 50MB, indexed in seconds

---

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Frontend | React + Vite | Fast dev server, component model |
| Backend | FastAPI (Python) | Async, auto-docs, type safety |
| Vector DB | ChromaDB | Local persistent vector storage |
| Embeddings | OpenAI `text-embedding-3-small` | Fast, cheap, 1536-dim vectors |
| LLM | OpenAI `gpt-4o-mini` | Best cost/quality ratio for RAG |
| PDF parsing | PyMuPDF (fitz) | Fast, reliable text extraction |
| Keyword search | BM25 (rank-bm25) | Exact term matching complement |

---

## Architecture

```
User Question
     │
     ▼
Query Rewriter (gpt-4o-mini)     ← fixes typos, expands abbreviations
     │
     ▼
Embedder (text-embedding-3-small) ← converts question to 1536-dim vector
     │
     ├──► Vector Search (ChromaDB)    ─┐
     │                                 ├─► Hybrid Score (70% vector + 30% BM25)
     └──► Keyword Search (BM25)       ─┘
                    │
                    ▼ top 12 candidates
             Reranker (gpt-4o-mini)   ← scores each chunk 0-10 for relevance
                    │
                    ▼ top 4 chunks
          Prompt Builder               ← injects chunks + conversation history
                    │
                    ▼
             LLM (gpt-4o-mini)        ← generates grounded answer
                    │
                    ▼
        Answer + Source Citations
```

---

## Project Structure

```
rag-assistant/
├── backend/
│   ├── main.py                  # FastAPI app, CORS, logging middleware
│   ├── requirements.txt
│   ├── .env                     # OPENAI_API_KEY (never committed)
│   ├── uploads/                 # Uploaded PDFs stored here
│   ├── chroma_db/               # ChromaDB vector store (persisted to disk)
│   ├── routers/
│   │   ├── documents.py         # Upload, list, delete endpoints
│   │   └── chat.py              # Full RAG pipeline endpoint
│   ├── models/
│   │   └── schemas.py           # Pydantic request/response models
│   └── utils/
│       ├── pdf_parser.py        # PDF text extraction + chunking
│       ├── embeddings.py        # OpenAI embedding calls + cosine similarity
│       ├── chroma_store.py      # ChromaDB read/write operations
│       ├── hybrid_search.py     # BM25 + vector score fusion
│       ├── reranker.py          # LLM-based chunk reranking
│       ├── query_processor.py   # Query rewriting + spell correction
│       └── llm.py               # Prompt construction + GPT response
└── frontend/
    ├── src/
    │   ├── App.jsx              # Root component, shared state
    │   ├── index.css            # Design system (CSS variables)
    │   └── components/
    │       ├── Sidebar.jsx      # Document manager + file upload
    │       ├── ChatWindow.jsx   # Message list + input
    │       └── MessageBubble.jsx # Individual message + citations
    ├── index.html
    └── package.json
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+
- An OpenAI API key ([get one here](https://platform.openai.com/api-keys))

### 1. Clone the repository

```bash
git clone https://github.com/YOUR_USERNAME/rag-assistant.git
cd rag-assistant
```

### 2. Set up the backend

```bash
cd backend

# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Create your .env file
echo OPENAI_API_KEY=your_key_here > .env
```

### 3. Start the backend

```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`.  
Interactive API docs: `http://localhost:8000/docs`

### 4. Set up the frontend

```bash
cd ../frontend
npm install
npm run dev
```

The app will be available at `http://localhost:5173`.

---

## How It Works

### Chunking
PDFs are split into overlapping 500-character chunks (100-character overlap) so that context isn't lost at chunk boundaries.

### Embeddings
Each chunk is converted to a 1536-dimensional vector using OpenAI's `text-embedding-3-small` model. These vectors capture semantic meaning — similar concepts have similar vectors regardless of exact wording.

### Hybrid Search
Queries are searched using both:
- **Vector similarity** — finds chunks with similar *meaning*
- **BM25 keyword matching** — finds chunks with matching *exact terms*

Scores are normalized and blended (70% vector, 30% BM25), then the top 12 candidates are passed to the reranker.

### Reranking
A fast LLM call scores each of the 12 candidates specifically for relevance to the question (0–10). Scores are blended with the hybrid score and the top 4 chunks are kept. This significantly reduces irrelevant context reaching the final LLM.

### Answer Generation
The 4 reranked chunks are assembled into a grounded prompt with the conversation history. GPT-4o mini generates an answer strictly from the provided context, citing sources by name.

---

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/documents/upload` | Upload and index a PDF |
| `GET` | `/documents/list` | List all indexed documents |
| `DELETE` | `/documents/{filename}` | Delete a document and its chunks |
| `POST` | `/chat/` | Ask a question (full RAG pipeline) |
| `GET` | `/ping` | Health check |

Full interactive documentation available at `/docs` when the server is running.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |

---

## What I Learned Building This

This project was built as a deep-dive into AI engineering fundamentals:

- **RAG architecture** — why retrieval-augmented generation outperforms pure LLM prompting for document Q&A
- **Vector databases** — how embeddings work, what cosine similarity measures, why ChromaDB uses HNSW indexing
- **Hybrid search** — the complementary strengths of dense vector search vs sparse BM25 keyword matching
- **Prompt engineering** — how system prompts, context injection, and temperature affect LLM answer quality
- **FastAPI** — building typed, async Python APIs with automatic OpenAPI documentation
- **React** — component architecture, state management, async data fetching

---

## License

MIT

