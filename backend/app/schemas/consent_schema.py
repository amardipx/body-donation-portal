from datetime import date
from uuid import UUID

from pydantic import BaseModel

from app.db.models import (DonorGender, DonorBloodType, Relation)

class WitnessCreate(BaseModel):
    full_name: str
    email: str
    phone: str
    relation: Relation

class ConsentFormCreate(BaseModel):
    first_name: str
    middle_name: str | None = None
    last_name: str
    parent_name: str

    gender: DonorGender
    date_of_birth: date
    blood_type: DonorBloodType

    address_line_1: str
    address_line_2: str | None = None

    city: str
    district: str
    state: str
    zip_code: str
    country: str = "India"

    identity_type: str
    identity_number: str
    declaration_accepted: bool

    preferred_institution: UUID | None = None
    witnesses: list[WitnessCreate]