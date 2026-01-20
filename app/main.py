"""
Flask Web Application
Main entry point for the RAG system API.
"""
import os
import uuid
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.utils import secure_filename

from .document_loader import load_document, chunk_documents
from .vector_store import add_documents, delete_all_records
from .rag_chain import query, clear_memory


# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__, static_folder="../static")
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "uploads")
ALLOWED_EXTENSIONS = {"pdf", "docx", "xlsx", "xls"}

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Track uploaded documents in memory (for listing)
uploaded_documents = []


def allowed_file(filename: str) -> bool:
    """Check if file extension is allowed."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def index():
    """Serve the main page."""
    return send_from_directory(app.static_folder, "index.html")


@app.route("/<path:path>")
def static_files(path):
    """Serve static files."""
    return send_from_directory(app.static_folder, path)


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """
    Upload and process a document.
    The document will be chunked and stored in Pinecone.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400
    
    file = request.files["file"]
    
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400
    
    if not allowed_file(file.filename):
        return jsonify({
            "error": f"File type not allowed. Supported types: {', '.join(ALLOWED_EXTENSIONS)}"
        }), 400
    
    try:
        # Save file temporarily
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        # Load and chunk the document
        documents = load_document(file_path)
        chunks = chunk_documents(documents)
        
        # Add to vector store
        doc_ids = add_documents(chunks)
        
        # Track the document
        doc_info = {
            "id": str(uuid.uuid4()),
            "name": filename,
            "chunks": len(chunks),
            "type": os.path.splitext(filename)[1].lower()
        }
        uploaded_documents.append(doc_info)
        
        # Clean up the uploaded file (already stored in Pinecone)
        os.remove(file_path)
        
        return jsonify({
            "success": True,
            "message": f"Document processed successfully",
            "document": doc_info
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/query", methods=["POST"])
def query_documents():
    """
    Query the RAG system with a question.
    Supports conversation memory via session_id.
    """
    data = request.get_json()
    
    if not data or "question" not in data:
        return jsonify({"error": "No question provided"}), 400
    
    question = data["question"]
    session_id = data.get("session_id", "default")
    
    try:
        result = query(question, session_id)
        return jsonify({
            "success": True,
            "answer": result["answer"],
            "sources": result["sources"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/documents", methods=["GET"])
def list_documents():
    """List all uploaded documents."""
    return jsonify({
        "success": True,
        "documents": uploaded_documents
    })


@app.route("/api/documents/<doc_id>", methods=["DELETE"])
def delete_document(doc_id):
    """Delete a document (note: doesn't remove from Pinecone in this version)."""
    global uploaded_documents
    uploaded_documents = [d for d in uploaded_documents if d["id"] != doc_id]
    return jsonify({"success": True, "message": "Document removed from list"})


@app.route("/api/clear-memory", methods=["POST"])
def clear_conversation_memory():
    """Clear conversation memory for a session."""
    data = request.get_json() or {}
    session_id = data.get("session_id", "default")
    
    cleared = clear_memory(session_id)
    return jsonify({
        "success": True,
        "message": "Conversation memory cleared" if cleared else "No memory to clear"
    })


@app.route("/api/health", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return jsonify({"status": "healthy"})


@app.route("/api/delete-all-records", methods=["POST"])
def delete_all_pinecone_records():
    """Delete all records from Pinecone index."""
    try:
        global uploaded_documents
        result = delete_all_records()
        uploaded_documents = []  # Clear local tracking too
        return jsonify({
            "success": True,
            "message": f"Deleted {result['previous_vector_count']} vectors from Pinecone"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(debug=False, host="0.0.0.0", port=port)
