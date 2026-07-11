# FilmInsight — Architecture Documentation

## System Overview

FilmInsight is a full-stack AI application using Retrieval-Augmented Generation (RAG) to answer questions from movie screenplay PDFs.

## Architecture Diagram

```
                    ┌─────────────────────────────────┐
                    │         User Browser             │
                    └────────────┬────────────────────┘
                                 │ HTTP (port 5000)
                    ┌────────────▼────────────────────┐
                    │    React Frontend (Nginx)        │
                    │    Tailwind · Framer Motion      │
                    └────────────┬────────────────────┘
                                 │ /api proxy
                    ┌────────────▼────────────────────┐
                    │   FastAPI Backend (port 8000)    │
                    │   Pydantic · httpx              │
                    └────────────┬────────────────────┘
                                 │ REST
                    ┌────────────▼────────────────────┐
                    │      Flowise (port 9000)         │
                    │  Conversational Retrieval QA     │
                    │  ┌──────────────────────────┐   │
                    │  │  HuggingFace Embeddings  │   │
                    │  │  Chroma Retriever        │   │
                    │  │  Groq LLaMA 3 LLM        │   │
                    │  └──────────────────────────┘   │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────▼────────────────────┐
                    │    ChromaDB (port 8001)          │
                    │    Screenplay Vector Store       │
                    └────────────┬────────────────────┘
                                 │
                    ┌────────────▼────────────────────┐
                    │    Movie Screenplay PDFs         │
                    │    (Chunked & Embedded)          │
                    └─────────────────────────────────┘
```

## RAG Pipeline

1. **Document Ingestion**
   - PDF is uploaded via Flowise Document Store
   - Split into 1000-char chunks with 200-char overlap
   - Each chunk embedded via `sentence-transformers/all-MiniLM-L6-v2`
   - Vectors stored in ChromaDB collection

2. **Query Processing**
   - User question embedded into vector space
   - Top-K (k=4) most similar chunks retrieved from Chroma
   - Chunks passed as context to Groq LLaMA 3

3. **Response Generation**
   - Groq LLM generates contextual answer from retrieved passages
   - Source documents returned alongside the answer
   - Conversational history maintained per session

## API Endpoints

### FastAPI (port 8000)
| Method | Path | Description |
|--------|------|-------------|
| GET    | /health | Health check |
| POST   | /chat | Send a message |
| GET    | /chat/history/{id} | Get session history |
| DELETE | /chat/history/{id} | Clear session |

### Flowise (port 9000)
| Method | Path | Description |
|--------|------|-------------|
| POST   | /api/v1/prediction/{chatflow_id} | RAG prediction |
| GET    | /api/v1/ping | Health check |

## Environment Variables

```env
FLOWISE_URL=http://localhost:9000
FLOWISE_CHATFLOW_ID=<your-chatflow-id>
FLOWISE_API_KEY=<optional>
VITE_API_URL=/api
```

## Ports

| Service   | Port |
|-----------|------|
| Frontend  | 5000 |
| Backend   | 8000 |
| ChromaDB  | 8001 |
| Flowise   | 9000 |
