import uuid
import enum
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum ,String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base
 
 
#RAG File Model

class DocumentType(str, enum.Enum):
    legal_act  = "legal_act"
    policy_doc = "policy_doc"
 
 
class RagFile(Base):

    __tablename__ = "rag_files"
 
    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    title = Column( String, nullable=False)
    document_type = Column(SAEnum(DocumentType, name="document_type_enum"), nullable=False, index=True)
    file_path = Column(String, nullable=False, unique=True)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    is_indexed = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True),nullable=False,server_default=func.now(),onupdate=func.now())
 