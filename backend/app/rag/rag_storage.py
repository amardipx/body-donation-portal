import os
import uuid
import hashlib
from pathlib import Path

from dotenv import load_dotenv

from fastapi import UploadFile
from sqlalchemy.orm import Session

from supabase import create_client, Client

from app.db.models import RagFile


load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_KEY,
)


def _generate_file_hash(file_bytes: bytes) -> str:
    return hashlib.sha256(file_bytes).hexdigest()


async def upload_document(file: UploadFile, document_type: str, db: Session) -> RagFile:

    file_bytes = await file.read()

    file_hash = _generate_file_hash(file_bytes)

    existing = db.query(RagFile).filter(RagFile.file_hash == file_hash).first()
    if existing:
        raise ValueError("Document already exists.")

    doc_id = uuid.uuid4()
    title = Path(file.filename).stem
    storage_path = f"rag/{document_type}/{doc_id}.pdf"

    rag_file = RagFile(
        id=doc_id,
        title=title,
        document_type=document_type,
        file_path=storage_path,
        file_hash=file_hash,
    )
    db.add(rag_file)
    db.commit()

    # Supabase second — rollback DB if it fails
    try:
        supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=storage_path,
            file=file_bytes,
            file_options={"content-type": "application/pdf"}
        )
    except Exception as e:
        db.delete(rag_file)
        db.commit()
        raise RuntimeError(f"Supabase upload failed: {e}")

    db.refresh(rag_file)
    return rag_file


def delete_document(doc_id: str, db: Session) -> None:

    rag_file = db.query(RagFile).filter(RagFile.id == doc_id).first()
    if not rag_file:
        raise ValueError("Document not found.")

    supabase.storage.from_(SUPABASE_BUCKET).remove([rag_file.file_path])

    db.delete(rag_file)
    db.commit()


def download_document(file_path: str) -> bytes:
    return supabase.storage.from_(SUPABASE_BUCKET).download(file_path)