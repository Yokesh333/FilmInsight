# 🎬 CineQuery AI - Movie Question Answering System using RAG

CineQuery AI is an intelligent movie assistant powered by Retrieval-Augmented Generation (RAG) that allows users to ask questions about movies and receive accurate, context-aware responses. The system retrieves relevant movie information from documents and generates human-like answers using Large Language Models (LLMs).

---

## 🚀 Features

- 💬 Conversational movie question-answering system
- 📄 Document-based knowledge retrieval using RAG
- 🔍 Semantic search with vector embeddings
- 🧠 Context-aware responses using Large Language Models
- 📚 Retrieves relevant movie scenes, characters, and storyline details
- ⚡ Fast inference using Groq LLM
- 🎯 Reduced hallucination through retrieval-based generation

---

## 🛠️ Tech Stack

- **RAG Framework:** LangChain / Flowise
- **LLM:** Groq Llama Model
- **Embeddings:** HuggingFace Sentence Transformers
- **Vector Database:** ChromaDB
- **Workflow Builder:** Flowise AI
- **Programming:** JavaScript / Node.js
- **Deployment:** Docker

---

## 🏗️ System Architecture


User Query
|
v
Flowise Chat Interface
|
v
Conversational Retrieval QA Chain
|
v
ChromaDB Vector Search
|
v
Relevant Movie Context Retrieval
|
v
Groq LLM
|
v
Context-Aware Response


---

## ⚙️ How It Works

### 1. Document Processing
Movie-related documents are uploaded and processed into smaller chunks.

### 2. Embedding Generation
Text chunks are converted into vector embeddings using:
sentence-transformers/all-MiniLM-L6-v2


### 3. Vector Storage
Generated embeddings are stored inside ChromaDB for similarity-based retrieval.

### 4. User Query Processing
When a user asks a movie-related question:

- Query is converted into embeddings
- Similar content is retrieved from ChromaDB
- Retrieved context is passed to the LLM

### 5. Response Generation
Groq LLM generates accurate answers based on retrieved movie knowledge.

---

## 🧠 Model Details

### Large Language Model
Groq - Llama Model


Used for:
- Natural language understanding
- Context analysis
- Answer generation

### Embedding Model
HuggingFace all-MiniLM-L6-v2