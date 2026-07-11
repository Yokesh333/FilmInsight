# 🎬 FilmInsight

> **An AI-powered Movie Assistant using Hybrid Retrieval-Augmented Generation (RAG)**

FilmInsight is an intelligent movie assistant that understands movie screenplays using Retrieval-Augmented Generation (RAG). It retrieves relevant screenplay context from uploaded PDFs and combines it with reliable web knowledge to generate natural, context-aware responses. The assistant can explain plots, analyze characters, provide trivia, quotes, cast information, IMDb ratings, and much more through a conversational interface.

---

## ✨ Features

- 🎥 Upload and analyze movie screenplays (PDF)
- 🤖 Human-like conversational AI responses
- 📖 Context-aware answers using Retrieval-Augmented Generation (RAG)
- 🔍 Semantic search with Hugging Face Embeddings
- 🗂️ Chroma Vector Database for efficient retrieval
- 🌐 Hybrid knowledge retrieval (PDF + Web)
- 🎭 Character analysis and relationship insights
- ⭐ IMDb ratings and movie information
- 🎬 Movie trivia and behind-the-scenes facts
- 💬 Famous quotes from the movie
- 📚 Relevant screenplay scene retrieval
- ⚡ Fast inference using Groq LLM
- 🎨 Modern and responsive user interface

---

## 🏗️ System Architecture

```
                User
                  │
                  ▼
        React Frontend (FilmInsight)
                  │
                  ▼
           FastAPI Backend
                  │
                  ▼
             Flowise API
                  │
        ┌───────────────────────┐
        │ Conversational RAG     │
        │                       │
        │ Groq LLM              │
        │ Chroma Retriever      │
        │ HuggingFace Embedding │
        └───────────────────────┘
                  │
                  ▼
        Chroma Vector Database
                  ▲
                  │
        Movie Screenplay PDFs
                  │
                  ▼
          Hybrid Knowledge Layer
         (Web + Retrieved Context)
```

---

## 🧠 How It Works

1. Upload a movie screenplay in PDF format.
2. The screenplay is divided into semantic chunks.
3. Hugging Face Embeddings convert each chunk into vector representations.
4. Chroma stores the vectors for semantic retrieval.
5. When a user asks a question:
   - Relevant screenplay sections are retrieved.
   - The LLM understands the retrieved context.
   - Additional movie knowledge can be incorporated when appropriate.
6. FilmInsight generates a natural, context-aware response.

---

## 💡 Example Queries

- Explain the ending of 500 Days of Summer.
- Why did Summer leave Tom?
- Describe Tom's character development.
- What is the main theme of the movie?
- Explain this dialogue.
- Who are the main characters?
- Give me some interesting trivia.
- Show famous quotes from the movie.
- Summarize the screenplay.
- Compare Tom and Summer's perspectives.

---

## 🛠️ Tech Stack

### Frontend
- React.js
- Tailwind CSS
- Axios

### Backend
- FastAPI
- Python

### AI & RAG
- Flowise
- Retrieval-Augmented Generation (RAG)
- Groq LLM
- Hugging Face Embeddings
- Chroma Vector Database

### DevOps
- Docker
- Docker Compose
- Jenkins
- GitHub

---

## 📂 Project Structure

```
FilmInsight/
│
├── frontend/               ← React + Nginx (UI)
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── Dockerfile
│
├── backend/                ← FastAPI (REST API)
│   ├── app/
│   ├── requirements.txt
│   └── Dockerfile
│
├── ingestion/              ← Automated RAG ingestion pipeline
│   ├── config.py
│   ├── pdf_loader.py
│   ├── chunker.py
│   ├── metadata_fetcher.py
│   ├── embedding_generator.py
│   ├── chroma_manager.py
│   ├── ingest_movies.py
│   ├── utils.py
│   ├── processed_movies.json
│   └── requirements.txt
│
├── movie_scripts/          ← ⚠️  NOT in Git (see below)
├── chroma_db/              ← ⚠️  NOT in Git (auto-generated)
├── logs/                   ← ⚠️  NOT in Git
│
├── docker/
│   └── docker-compose.yml
│
├── Jenkinsfile
│
└── README.md
```

---

## 🎬 Movie Scripts

> **⚠️ Screenplay PDFs are NOT included in this repository due to copyright restrictions.**

FilmInsight requires legally obtained screenplay PDFs to build its knowledge base.
Follow these steps to set up the knowledge base:

### Step 1 — Create the folder

```bash
mkdir movie_scripts
```

### Step 2 — Add screenplay PDFs

Place your legally obtained PDF screenplays inside the `movie_scripts/` folder:

```
FilmInsight/
└── movie_scripts/
    ├── Interstellar.pdf
    ├── The Dark Knight.pdf
    ├── 500 Days of Summer.pdf
    └── ...
```

> **Where to find screenplays legally:**
> - [IMSDB](https://www.imsdb.com/) — Internet Movie Script Database
> - [Simply Scripts](https://www.simplyscripts.com/)
> - [ScreenCraft](https://screencraft.org/)
> - Official studio press kits

### Step 3 — Install ingestion dependencies

```bash
pip install -r ingestion/requirements.txt
```

### Step 4 — Run the ingestion pipeline

```bash
# From the project root
python -m ingestion.ingest_movies
```

The pipeline will automatically:
1. Scan `movie_scripts/` for new PDFs
2. Extract text using PyMuPDF
3. Split text into semantic chunks
4. Fetch metadata from TMDb + OMDb
5. Generate embeddings (`sentence-transformers/all-MiniLM-L6-v2`)
6. Store everything in the Chroma vector database

> **Resumable:** If interrupted, re-running processes only new or incomplete movies.

### Pipeline output example

```
Scanning movie_scripts/...
Found 3 PDFs.
3 new movie(s) to process.

[1/3] Processing Interstellar...
  Fetching TMDb metadata...
  Fetching OMDb metadata...
  Generating embeddings...
  Stored 182 chunks.
  ✓ 'Interstellar' → 182 chunks stored.

Done. 3 succeeded, 0 failed.
```

---

## 🚀 Installation

### Clone Repository

```bash
git clone https://github.com/YOUR_USERNAME/FilmInsight.git

cd FilmInsight
```

---

### Install Frontend

```bash
cd frontend

npm install

npm start
```

---

### Install Backend

```bash
cd backend

pip install -r requirements.txt

uvicorn app:app --reload
```

---

### Run Flowise

```bash
docker compose up
```

---

## 🐳 Docker

```bash
docker compose up --build
```

---

## 🔄 Jenkins CI/CD

Pipeline includes:

- Source Code Checkout
- Install Dependencies
- Build React Application
- Build Docker Images
- Run Containers
- Deploy Application
- Health Check

---

## ☁️ Deployment

FilmInsight can be deployed using:

- Oracle Cloud VM
- AWS EC2
- Docker
- Jenkins
- Nginx

---

## 🎯 Future Enhancements

- 🎙️ Voice-based interaction
- 🎞️ Trailer recommendations
- 🎬 Scene timeline visualization
- 🧠 Character relationship graph
- 📊 Sentiment analysis
- 🌍 Multi-language support
- 📱 Mobile responsive interface
- 🔍 Live web search integration
- 🎥 Multi-movie knowledge base

---

## 📸 Screenshots

| Home | Chat |
|------|------|
| Add Screenshot | Add Screenshot |

---

## 👨‍💻 Author

**Yokesh D**

M.Tech Integrated Software Engineering

Vellore Institute of Technology

---

## ⭐ If you found this project useful, don't forget to star the repository!