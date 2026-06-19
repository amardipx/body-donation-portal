from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.db.models import DonorGender, DonorBloodType

class ConsentFormCreate(BaseModel):
    gender: DonorGender
    date_of_birth: datetime
    blood_type: DonorBloodType
    address: str
    city: str
    state: str
    zip_code: str
    country: str
    preferred_institution: UUID | None = None
