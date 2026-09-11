# AI Document Q&A Assistant

A Retrieval-Augmented Generation (RAG) based application that allows users to upload documents and ask questions about their content. The system retrieves relevant information from the documents and uses an LLM to generate grounded answers with source references.

## Features

* Upload PDF, DOCX, and TXT documents
* Extract and clean document text
* Split documents into searchable chunks
* Generate embeddings using configurable Gemini or Ollama embedding providers
* Semantic search using FAISS with stable vector IDs
* Keyword search using BM25
* Query expansion for improved retrieval
* Hybrid retrieval combining semantic and keyword search
* Conversation-based document filtering
* Generate answers using configurable Gemini or Ollama LLM providers
* Display relevant document sources with answers
* ChatGPT-style question and answer interface
* Conversation and message persistence
* Persistent FAISS index, metadata, and index configuration
* Incremental document indexing using SHA-256 file hashes
* Skip unchanged documents and update modified documents
* Delete conversation documents and their associated vectors


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
       ├── Gemini / Ollama Embeddings
       │
       ├── FAISS Semantic Search
       │
       ├── BM25 Keyword Search
       │
       ├── Hybrid Retrieval + Metadata Filtering
       │
       └── Gemini / Ollama LLM
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
Top-K Relevant Chunks
      ↓
Grounded Prompt
      ↓
Llama 3.2
      ↓
Answer + Sources
```

## Technology Stack

| Component              | Technology                                      |
| ---------------------- | ----------------------------------------------- |
| Backend                | Python, FastAPI                                 |
| Frontend               | HTML, CSS, JavaScript                           |
| LLM                    | Gemini / Ollama (`llama3.2`)                    |
| Embeddings             | Gemini / Ollama (`nomic-embed-text`)            |
| Vector Store           | FAISS (`IndexIDMap2` + `IndexFlatL2`)           |
| Keyword Search         | BM25                                            |
| Document Storage       | Vercel Blob                                     |
| Conversation Storage   | SQLite (local)                                  |
| Documents              | PDF, DOCX, TXT                                  |
| Testing                | Pytest                                          |

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
│   │   └── conversations.db
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

### 4. Configure the AI provider

The application supports both Gemini and Ollama as configurable providers.

For local development with Ollama, make sure Ollama is installed and running.

Pull the required local models:

```bash
ollama pull llama3.2
ollama pull nomic-embed-text
```

The provider and model settings are configured through environment variables. For example:

```env
LLM_PROVIDER=ollama
EMBEDDING_PROVIDER=ollama
OLLAMA_LLM_MODEL=llama3.2
OLLAMA_EMBEDDING_MODEL=nomic-embed-text
```

Gemini can be selected by changing the corresponding provider settings and configuring the Gemini API key.

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
4. Click **Index Documents** when a full rebuild is required.
5. New and modified documents use incremental indexing.
6. Ask a question about the document.
7. The assistant retrieves relevant content using hybrid retrieval and generates a grounded answer.
8. Relevant document sources are displayed below the answer.
9. Conversations are maintained using a conversation ID, which also isolates documents associated with that conversation.

## API Endpoints

| Method | Endpoint                            | Description                                      |
| ------ | ---------------------------------- | ------------------------------------------------ |
| POST   | `/upload`                          | Upload a document                                |
| POST   | `/index`                           | Build/rebuild the document index                 |
| GET    | `/index/status`                    | Get current index status                         |
| POST   | `/ask`                             | Ask a question                                   |
| DELETE | `/conversations/{conversation_id}` | Delete conversation and associated documents/vectors |

## Retrieval Strategy

The application uses multiple retrieval techniques to improve answer quality.

### FAISS

FAISS performs semantic similarity search using the document and query embeddings.

### BM25

BM25 performs keyword-based retrieval and helps retrieve documents containing important exact terms.

### Hybrid Retrieval

FAISS semantic results and BM25 keyword results are combined, deduplicated, and filtered using document and conversation metadata before selecting the final Top-K chunks.

This gives the system a multi-stage retrieval process:

```text
FAISS + BM25
      ↓
Candidate Chunks
      ↓
Metadata / Conversation Filtering
      ↓
Top-K Relevant Chunks
```

## Persistence and Provider Architecture

### AI Providers

The application uses provider abstraction for both embeddings and LLM generation.

```text
Embedding Provider
      │
      ├── Gemini
      │     └── gemini-embedding-2
      │
      └── Ollama
            └── nomic-embed-text

LLM Provider
      │
      ├── Gemini
      │
      └── Ollama
            └── llama3.2
```

The provider can be selected through environment variables without changing the RAG pipeline.

### Document and Index Persistence

Documents and the persistent FAISS index are stored in Vercel Blob:

```text
Blob Storage
├── documents/
│   └── {conversation_id}/
│       └── document files
└── index/
    ├── index.faiss
    ├── metadata.json
    └── config.json
```

`metadata.json` stores chunk metadata and the mapping between FAISS vector IDs and metadata entries. `config.json` stores index and embedding configuration used to validate the persisted index.

For local development, conversation and message data is stored in SQLite:

```text
backend/data/conversations.db
```

The FAISS index does not need to be rebuilt every time the local FastAPI server is restarted. The persisted index is loaded when the application starts.

### Incremental Indexing

Documents are identified using SHA-256 hashes.

```text
New document
     ↓
Calculate hash
     ↓
Already indexed?
   ┌─┴─┐
  Yes  No
   │    │
 Skip  Index
        │
        ▼
   Store vectors
```

If an existing document changes, its old vectors are removed and the modified document is re-chunked and embedded. If a document is unchanged, it is skipped.

### Conversation Deletion

Deleting a conversation also removes its associated document files and FAISS vectors:

```text
Delete Conversation
        ↓
Delete conversation documents
        ↓
Remove associated vectors
        ↓
Save updated FAISS index
        ↓
Soft-delete conversation record
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
* Larger evaluation datasets
* Further hybrid retrieval optimization
* Improved monitoring and logging
* Advanced observability and analytics
* Improved monitoring and logging

## License

This project is intended for educational and demonstration purposes.
