from pydantic import BaseModel

from app.db.models import Relation

class LinkDonorRequest(BaseModel):
    certificate_number: str
    relationship: Relation