"""
RAG Chain Module
Builds the LangChain RAG chain with conversation memory.
"""
import os
from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from .vector_store import get_retriever


# Store chat history per session
_session_histories: Dict[str, List] = {}


def get_history(session_id: str) -> List:
    """Get or create chat history for a session."""
    if session_id not in _session_histories:
        _session_histories[session_id] = []
    return _session_histories[session_id]


def clear_memory(session_id: str) -> bool:
    """Clear conversation memory for a session."""
    if session_id in _session_histories:
        del _session_histories[session_id]
        return True
    return False


def format_docs(docs):
    """Format retrieved documents into a string."""
    return "\n\n".join(doc.page_content for doc in docs)


def query(question: str, session_id: str = "default") -> Dict[str, Any]:
    """
    Query the RAG system.
    
    Args:
        question: The question to ask
        session_id: Session identifier for conversation memory
    
    Returns:
        Dictionary containing answer and source documents
    """
    llm = ChatOpenAI(
        model="gpt-4o",
        temperature=0.7,
        openai_api_key=os.getenv("OPENAI_API_KEY")
    )
    
    retriever = get_retriever(k=4)
    history = get_history(session_id)
    
    # Get relevant documents
    docs = retriever.invoke(question)
    context = format_docs(docs)
    
    # Build prompt with history
    system_prompt = """You are a helpful AI assistant that answers questions based on the provided documents.
Use the following context to answer the question. If you cannot find the answer in the context, 
say so clearly but try to be helpful.

Context:
{context}"""

    messages = [("system", system_prompt)]
    
    # Add chat history
    for msg in history:
        messages.append(msg)
    
    messages.append(("human", "{question}"))
    
    prompt = ChatPromptTemplate.from_messages(messages)
    
    chain = prompt | llm | StrOutputParser()
    
    answer = chain.invoke({"context": context, "question": question})
    
    # Update history
    history.append(("human", question))
    history.append(("assistant", answer))
    
    # Keep only last 10 exchanges
    if len(history) > 20:
        _session_histories[session_id] = history[-20:]
    
    # Extract source information
    sources = []
    for doc in docs:
        sources.append({
            "source": doc.metadata.get("source", "Unknown"),
            "type": doc.metadata.get("type", "Unknown"),
            "content_preview": doc.page_content[:200] + "..." if len(doc.page_content) > 200 else doc.page_content
        })
    
    return {
        "answer": answer,
        "sources": sources
    }
