import os
import time
from typing import Generator
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone, ServerlessSpec
from app.rag.chunking import chunk_pages
from app.rag.extractor import extract_text_pages

load_dotenv()

INDEX_NAME = "body-donation-rag-index"
BATCH_SIZE = 5
NAME_SPACE = "bdri"


# Clients
_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

_pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))


# Create Pinecone index if it doesn't exist
def _ensure_index() -> None: 
    
    existing = _pc.list_indexes().names()
    if INDEX_NAME not in existing:
        _pc.create_index(
            INDEX_NAME,
            dimension=3072,
            metric="dotproduct",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        while not _pc.describe_index(INDEX_NAME).status["ready"]:
            time.sleep(1)


# Chunk Batching
def _batch_chunks(chunks: list[dict], batch_size: int = BATCH_SIZE) -> Generator[list[dict], None, None]:
    
    for i in range(0, len(chunks), batch_size):
        yield chunks[i:i + batch_size]


# Vector Formatting
def _create_vectors(chunks: list[dict], embeddings: list[list[float]]) -> list[dict]:
    
    vectors = []
    for chunk, embedding in zip(chunks, embeddings):
        
        metadata = chunk["metadata"].copy()
        metadata["text"] = chunk["text"]
        
        vector_id = f"{metadata['doc_id']}_{metadata['page']}_{metadata['chunk_index']}"
        
        vectors.append({
            "id": vector_id,
            "values": embedding,
            "metadata": metadata
        })
    
    return vectors


# Main Ingestion Function
def index_document(pdf_bytes: str | bytes, doc_id: str, title: str, document_type: str, ) -> None:
    
    _ensure_index()
    
    index = _pc.Index(INDEX_NAME)
    
    pages_text = extract_text_pages(pdf_bytes)
    
    chunks = chunk_pages(pages_text, doc_id, title, document_type)
    if not chunks:
        raise ValueError("No text chunks were created from the document.")
    
    for batch in _batch_chunks(chunks):
        
        texts = [chunk["text"] for chunk in batch]
        embeddings = _embeddings.embed_documents(texts)
        vectors = _create_vectors(batch, embeddings)
        
        index.upsert(vectors = vectors, namespace=NAME_SPACE)
        time.sleep(1)  # Rate limit handling


# Deletion Function
def delete_document_vectors(doc_id: str) -> None:
    
    index = _pc.Index(INDEX_NAME)
    index.delete(filter={"doc_id": doc_id}, namespace=NAME_SPACE)


# Reindexing Function
def reindex_document(pdf_path: str | bytes, doc_id: str, title: str, document_type: str) -> None:
    
    delete_document_vectors(doc_id)
    index_document(pdf_path, doc_id, title, document_type)
    

if __name__ == "__main__":
    # Example usage
    with open("app/rag/test_doc/THOA_1994.pdf", "rb") as f:
        pdf_bytes = f.read()
    doc_id = "doc123"
    title = "Sample Document"
    document_type = "law"
    
    #index_document(pdf_bytes, doc_id, title, document_type)
    delete_document_vectors(doc_id)