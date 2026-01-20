# RAG Document Assistant

A web-based RAG (Retrieval Augmented Generation) system built with LangChain, Pinecone, and GPT-4o. Upload PDF, Word, and Excel files, then ask questions about their content.

## Features

- 📄 **Multi-format Support**: PDF, Word (.docx), Excel (.xlsx)
- 🧠 **Persistent Storage**: Documents stored in Pinecone vector database
- 💬 **Conversation Memory**: Follow-up questions work contextually
- 🎨 **Modern Web UI**: Premium dark theme with drag-and-drop upload

## Quick Start

### 1. Configure Environment

Copy `.env.example` to `.env` and fill in your API keys:

```bash
OPENAI_API_KEY=your_openai_api_key
PINECONE_API_KEY=your_pinecone_api_key
PINECONE_INDEX_NAME=rag-documents
```

### 2. Create Pinecone Index

Go to [Pinecone Console](https://app.pinecone.io/) and create an index with:
- **Dimension**: 1536 (required for OpenAI embeddings)
- **Metric**: Cosine

### 3. Install Dependencies

```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 4. Run the Application

```bash
# Windows
run.bat

# Or manually
python -m app.main
```

Open http://localhost:5000 in your browser.

## Usage

1. **Upload Documents**: Drag and drop files or click to browse
2. **Ask Questions**: Type your question in the chat input
3. **Follow Up**: Ask follow-up questions - the bot remembers context
4. **Clear Memory**: Click "Clear Memory" to reset conversation history

## Project Structure

```
pdfloading/
├── app/
│   ├── __init__.py
│   ├── main.py           # Flask web server
│   ├── document_loader.py # PDF/Word/Excel parsing
│   ├── vector_store.py   # Pinecone integration
│   └── rag_chain.py      # LangChain RAG chain
├── static/
│   ├── index.html        # Web UI
│   ├── styles.css        # Styling
│   └── app.js            # Frontend logic
├── .env.example
├── requirements.txt
└── run.bat
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/upload` | Upload and process a document |
| POST | `/api/query` | Query the RAG system |
| GET | `/api/documents` | List uploaded documents |
| DELETE | `/api/documents/<id>` | Remove a document |
| POST | `/api/clear-memory` | Clear conversation memory |
