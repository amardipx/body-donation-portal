from langchain_text_splitters import RecursiveCharacterTextSplitter


_SPLITTER = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=150,
    separators=["\n\n", "\n", ". ", " ", ""],
)


def chunk_pages(pages_text: list[str], doc_id: str, title: str, document_type: str) -> list[dict]:
    
    chunks = []
    chunk_index = 0

    for page_num, page_text in enumerate(pages_text, start=1):
        if not page_text.strip():
            continue

        page_chunks = _SPLITTER.split_text(page_text)

        for chunk_text in page_chunks:
            if not chunk_text.strip():
                continue

            chunks.append({
                "text": chunk_text,
                "metadata": {
                    "doc_id": doc_id,
                    "page": page_num,
                    "chunk_index": chunk_index,
                    'title': title,
                    "document_type": document_type
                },
            })

            chunk_index += 1

    return chunks