"""
Vector Store Module
Handles Pinecone integration for document storage and retrieval.
"""
import os
from typing import List, Optional
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone


# Global instances
_pinecone_client: Optional[Pinecone] = None
_vector_store: Optional[PineconeVectorStore] = None
_embeddings: Optional[OpenAIEmbeddings] = None


def get_embeddings() -> OpenAIEmbeddings:
    """Get or create OpenAI embeddings instance."""
    global _embeddings
    if _embeddings is None:
        _embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=os.getenv("OPENAI_API_KEY")
        )
    return _embeddings


def init_pinecone() -> Pinecone:
    """Initialize Pinecone client."""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
    return _pinecone_client


def get_vector_store() -> PineconeVectorStore:
    """Get or create the Pinecone vector store instance."""
    global _vector_store
    
    if _vector_store is None:
        init_pinecone()
        index_name = os.getenv("PINECONE_INDEX_NAME", "rag-documents")
        
        _vector_store = PineconeVectorStore(
            index_name=index_name,
            embedding=get_embeddings(),
            pinecone_api_key=os.getenv("PINECONE_API_KEY")
        )
    
    return _vector_store


def add_documents(documents: List[Document]) -> List[str]:
    """
    Add documents to the Pinecone vector store.
    
    Args:
        documents: List of Document objects to add
    
    Returns:
        List of document IDs
    """
    vector_store = get_vector_store()
    ids = vector_store.add_documents(documents)
    return ids


def get_retriever(k: int = 4):
    """
    Get a retriever for querying the vector store.
    
    Args:
        k: Number of documents to retrieve
    
    Returns:
        A retriever instance
    """
    vector_store = get_vector_store()
    return vector_store.as_retriever(search_kwargs={"k": k})


def similarity_search(query: str, k: int = 4) -> List[Document]:
    """
    Perform similarity search on the vector store.
    
    Args:
        query: The search query
        k: Number of results to return
    
    Returns:
        List of matching documents
    """
    vector_store = get_vector_store()
    return vector_store.similarity_search(query, k=k)


def delete_all_records() -> dict:
    """
    Delete all records from the Pinecone index.
    
    Returns:
        Dictionary with deletion status
    """
    pc = init_pinecone()
    index_name = os.getenv("PINECONE_INDEX_NAME", "rag-documents")
    
    # Get the index
    index = pc.Index(index_name)
    
    # Get index stats to see namespaces
    stats = index.describe_index_stats()
    
    # Delete all vectors in default namespace
    index.delete(delete_all=True, namespace="")
    
    # Also delete from any other namespaces
    for namespace in stats.get("namespaces", {}).keys():
        if namespace:  # Skip empty namespace (already deleted)
            index.delete(delete_all=True, namespace=namespace)
    
    return {
        "deleted": True,
        "previous_vector_count": stats.get("total_vector_count", 0)
    }
