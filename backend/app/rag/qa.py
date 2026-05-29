import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate

from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from app.rag.ingest import INDEX_NAME, NAME_SPACE, _ensure_index

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

_ensure_index()

_vectorstore = PineconeVectorStore(
        index_name=INDEX_NAME,
        embedding=_embeddings,
        namespace=NAME_SPACE,
        pinecone_api_key=os.getenv("PINECONE_API_KEY"),
    )

_PROMPT = ChatPromptTemplate.from_template("""
You are an assistant for the Body Donation Portal of India.
You help users understand body donation procedures, regulations, and portal policies.

Answer the question using ONLY the provided context below.

Rules:
- Be concise — maximum 4-5 sentences or a short numbered list if steps are involved.
- Use simple, clear language suitable for the general public.
- Fix obvious OCR errors (e.g. broken words, missing spaces) when reading the context.
- Do not make up or infer information beyond what is in the context.
- If the context does not contain the answer, respond with exactly:
  "I could not find this in the documents."

Context:
{context}

Question:
{question}

Answer:
""")

def _format_chunk(chunks) -> str:
    
    return "\n\n".join([chunk.page_content for chunk in chunks])


def _extract_references(chunks) -> str:
    
    doc_pages = {}
    
    for chunk in chunks:
        title = chunk.metadata.get("title", "Unknown Title")
        page = int(chunk.metadata.get("page", 0))
        
        if title not in doc_pages:
            doc_pages[title] = set()
        doc_pages[title].add(page)
    
    parts = []
    for title, pages in doc_pages.items():
        sorted_pages = ", ".join(str(p) for p in sorted(pages))
        parts.append(f"{title}: page {sorted_pages}")
    
    return " | ".join(parts)


def answer(question: str, top_k: int = 5, filter: dict = None) -> dict:
    
    if not question.strip():
        return {"answer": "Please provide a question.", "references": []}
    
    search_kwargs = {"k": top_k}
    
    if filter:
        search_kwargs["filter"] = filter
    
    retriever = _vectorstore.as_retriever(search_kwargs=search_kwargs)
    
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
    question = "What is the procedure for donation?"
    result = answer(question)
    print("Answer:", result["answer"])
    print("References:", result["references"])