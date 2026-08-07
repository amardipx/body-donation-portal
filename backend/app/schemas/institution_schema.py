from uuid import UUID

from pydantic import BaseModel

from app.db.models import StaffRole, InstitutionType

class InstitutionCreate(BaseModel):
    type: InstitutionType
    name: str
    registration_number: str
    
    address: str
    city: str
    state: str
    zip_code: str
    country: str = "India"
    
    contact_email: str
    contact_phone: str

class InstitutionAdminCreate(BaseModel):
    employee_id : str
    full_name : str
    
    email : str
    phone : str

class InstitutionStaffCreate(InstitutionAdminCreate):
    
    role : StaffRole

