from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import RagFile, DocumentType
from app.rag.rag_storage import upload_document, delete_document, download_document
from app.rag.ingest import index_document, delete_document_vectors


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


# Get All Documents
@router.get("/")
def get_documents(db: Session = Depends(get_db)):
    try:
        documents = db.query(RagFile).all()
        return [
            {
                "document_id": str(doc.id),
                "title": doc.title,
                "document_type": doc.document_type,
                "created_at": doc.created_at,
            }
            for doc in documents
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Upload Document
@router.post("/upload")
async def upload_document_route(
    file: UploadFile = File(...),
    document_type: DocumentType = Form(...),
    db: Session = Depends(get_db),
):
    try:
        rag_file = await upload_document(
            file=file,
            document_type=document_type.value,
            db=db,
        )

        pdf_bytes = download_document(rag_file.file_path)

        index_document(
            pdf_bytes=pdf_bytes,
            doc_id=str(rag_file.id),
            title=rag_file.title,
            document_type=rag_file.document_type,
        )

        return {
            "message": "Document uploaded and indexed successfully.",
            "document_id": str(rag_file.id),
            "title": rag_file.title,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Delete Document
@router.delete("/{doc_id}")
def delete_document_route(
    doc_id: str,
    db: Session = Depends(get_db),
):
    try:
        delete_document_vectors(doc_id)

        delete_document(
            doc_id=doc_id,
            db=db,
        )

        return {"message": "Document deleted successfully."}

    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# Update Document
@router.put("/{doc_id}")
async def update_document_route(
    doc_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        delete_document_vectors(doc_id)
        delete_document(doc_id=doc_id, db=db)

        rag_file = await upload_document(
            file=file,
            document_type=document_type,
            db=db,
        )

        pdf_bytes = download_document(rag_file.file_path)

        index_document(
            pdf_bytes=pdf_bytes,
            doc_id=str(rag_file.id),
            title=rag_file.title,
            document_type=rag_file.document_type,
        )

        return {
            "message": "Document updated successfully.",
            "document_id": str(rag_file.id),
            "title": rag_file.title,
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))