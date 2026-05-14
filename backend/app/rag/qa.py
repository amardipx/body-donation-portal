import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from ingest import INDEX_NAME, NAME_SPACE

load_dotenv()

_embeddings = GoogleGenerativeAIEmbeddings(
    model="models/gemini-embedding-001", 
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    )

_llm = ChatGroq(
    model="llama-3.1-8b-instant",
    temperature=0,
    max_retries=2,
    api_key=os.getenv("GROQ_API_KEY"),
)

_PROMPT = ChatPromptTemplate.from_template("""
You are an assistant that helps users understand
body donation and organ transplantation regulations in India.

Use the provided context to answer the user's question.

Instructions:
- Keep answers short and precise.
- Maximum 3-4 sentences.
- Use simple and clear language.
- Fix OCR mistakes if necessary.
- If the context contains relevant information, summarize it clearly.
- If the context does not contain enough information,
  say:
  "I could not find this in the documents."

Context:
{context}

Question:
{question}

Answer:
""")

def _format_chunk(chunks) -> str:
    
    return "\n\n".join([chunk.page_content for chunk in chunks])


def _extract_references(chunks) -> list[str]:
    
    seen = set()
    references = []
    
    for chunk in chunks:
        title  = chunk.metadata.get("title", "Unknown Title")
        page = chunk.metadata.get("page", "?")
        
        key = (title, page)
        if key not in seen:
            seen.add(key)
            references.append(f"{title} (Page {page})")
    
    return references


def answer(question: str, top_k: int = 5, filter: dict = None) -> dict:
    
    if not question.strip():
        return {"answer": "Please provide a question.", "references": []}
    
    vectorstore = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=_embeddings,
        namespace=NAME_SPACE,
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    )
    
    search_kwargs = {"k": top_k}
    
    if filter:
        search_kwargs["filter"] = filter
    
    retriever = vectorstore.as_retriever(search_kwargs=search_kwargs)
    
    retrieved_chunks = retriever.invoke(question)
    
    if not retrieved_chunks:
        return {"answer": "I could not find this in the documents.", "references": []}
    
    context = _format_chunk(retrieved_chunks)
    
    reference = _extract_references(retrieved_chunks)
    
    chain = _PROMPT | _llm | StrOutputParser()
    
    response = chain.invoke({"context": context, "question": question})
    
    return {
        "answer": response.strip(),
        "references": reference,
        }
    
if __name__ == "__main__":
    question = "What are Offences and Penalties ?"
    result = answer(question)
    print("Answer:", result["answer"])
    print("References:", result["references"])