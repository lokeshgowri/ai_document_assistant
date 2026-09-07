# AI Document Q&A Assistant

A Retrieval-Augmented Generation (RAG) based application that allows users to upload documents and ask questions about their content. The system retrieves relevant information from the documents and uses an LLM to generate grounded answers with source references.

## Features

* Upload PDF, DOCX, and TXT documents
* Extract and clean document text
* Split documents into searchable chunks
* Generate embeddings using Nomic Embeddings
* Semantic search using FAISS
* Keyword search using BM25
* Query expansion for improved retrieval
* Cross-Encoder reranking
* Generate answers using Llama 3.2 through Ollama
* Display relevant document sources with answers
* ChatGPT-style question and answer interface
* Persistent FAISS index and document metadata
* Index status showing document and chunk counts

## Architecture

```text
User
 │
 ▼
Frontend
HTML + CSS + JavaScript
 │
 │ HTTP API
 ▼
FastAPI Backend
 │
 ├── Document Upload
 │
 ├── Document Processing
 │
 └── RAG Pipeline
       │
       ├── Nomic Embeddings
       │
       ├── FAISS Semantic Search
       │
       ├── BM25 Keyword Search
       │
       ├── Cross-Encoder Reranking
       │
       └── Llama 3.2
              │
              ▼
        Answer + Sources
```

## RAG Pipeline

```text
User Question
      ↓
Query Processing
      ↓
Query Embedding
      ↓
FAISS Semantic Retrieval
      +
BM25 Keyword Retrieval
      ↓
Candidate Combination
      ↓
Metadata Filtering
      ↓
Cross-Encoder Reranking
      ↓
Top-K Relevant Chunks
      ↓
Grounded Prompt
      ↓
Llama 3.2
      ↓
Answer + Sources
```

## Technology Stack

| Component      | Technology               |
| -------------- | ------------------------ |
| Backend        | Python, FastAPI          |
| Frontend       | HTML, CSS, JavaScript    |
| LLM            | Llama 3.2                |
| LLM Runtime    | Ollama                   |
| Embeddings     | Nomic `nomic-embed-text` |
| Vector Store   | FAISS                    |
| Keyword Search | BM25                     |
| Reranker       | Cross-Encoder            |
| Documents      | PDF, DOCX, TXT           |
| Testing        | Pytest                   |

## Project Structure

```text
AI Document Q&A Assistant/
│
├── backend/
│   │
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── exceptions.py
│   │   ├── logging_config.py
│   │   │
│   │   ├── models/
│   │   │   └── schemas.py
│   │   │
│   │   └── services/
│   │       ├── document_loader.py
│   │       ├── text_cleaner.py
│   │       ├── chunker.py
│   │       ├── embeddings.py
│   │       ├── vector_store.py
│   │       ├── keyword_search.py
│   │       ├── reranker.py
│   │       ├── query_processor.py
│   │       ├── rag_service.py
│   │       ├── indexing_service.py
│   │       └── llm_service.py
│   │
│   ├── data/
│   │   ├── index.faiss
│   │   └── metadata.json
│   │
│   ├── tests/
│   │
│   ├── .env
│   ├── .env.example
│   ├── pytest.ini
│   └── requirements.txt
│
├── frontend/
│   ├── index.html
│   │
│   ├── css/
│   │   └── style.css
│   │
│   └── js/
│       └── app.js
│
├── .gitignore
└── README.md
```

## Installation

### 1. Clone the repository

```bash
git clone <repository-url>
cd "AI Document Q&A Assistant"
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

Move into the backend directory:

```bash
cd backend
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install and start Ollama

Make sure Ollama is installed and running.

Pull the required models:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

## Running the Application

### Start the FastAPI backend

From the project root:

```bash
uvicorn app.main:app --reload
```

The backend will run at:

```text
http://127.0.0.1:8000
```

Swagger API documentation:

```text
http://127.0.0.1:8000/docs
```

### Start the frontend

Open another terminal:

```bash
cd frontend
python -m http.server 5500
```

Open:

```text
http://127.0.0.1:5500
```

## How to Use

1. Open the frontend.
2. Select a PDF, DOCX, or TXT document.
3. Upload the document.
4. Click **Index Documents**.
5. Wait for indexing to complete.
6. Ask a question about the document.
7. The assistant retrieves relevant content and generates an answer.
8. Relevant document sources are displayed below the answer.

## API Endpoints

| Method | Endpoint        | Description              |
| ------ | --------------- | ------------------------ |
| POST   | `/upload`       | Upload a document        |
| POST   | `/index`        | Build the document index |
| GET    | `/index/status` | Get current index status |
| POST   | `/ask`          | Ask a question           |

## Retrieval Strategy

The application uses multiple retrieval techniques to improve answer quality.

### FAISS

FAISS performs semantic similarity search using the document and query embeddings.

### BM25

BM25 performs keyword-based retrieval and helps retrieve documents containing important exact terms.

### Cross-Encoder

The Cross-Encoder reranks the retrieved candidates based on the relevance between the question and each document chunk.

This gives the system a multi-stage retrieval process:

```text
FAISS + BM25
      ↓
Candidate Documents
      ↓
Cross-Encoder
      ↓
Most Relevant Chunks
```

## Evaluation

The retrieval system was evaluated using a small question-answering test set.

| Metric      | Result |
| ----------- | -----: |
| Hit@3       |   1.00 |
| MRR         |   0.70 |
| Precision@3 |   0.33 |
| Recall@3    |   1.00 |

The selected FAISS distance threshold from the evaluation was:

```text
0.9
```

## Example

**Question**

```text
How many earned leaves do employees get?
```

**Answer**

```text
According to the document, employees are entitled to
15 days of Earned/Privilege Leave per year.
```

The application also displays the document source used for the answer.

## Error Handling

The application handles common cases such as:

* Unsupported document types
* Empty or invalid documents
* Missing index
* Backend connection failures
* Failed document uploads
* Questions asked before documents are indexed

## Future Improvements

Possible future enhancements include:

* Streaming LLM responses
* Authentication and user management
* Conversation history
* Better document-level filtering
* Larger evaluation datasets
* Hybrid retrieval optimization
* Cloud deployment
* Production database integration
* Improved monitoring and logging

## License

This project is intended for educational and demonstration purposes.
