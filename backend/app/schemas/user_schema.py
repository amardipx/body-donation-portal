from pydantic import BaseModel
from app.db.models import UserRole

class UserSignup(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str
    role: UserRole

class UserLogin(BaseModel):
    email: str
    password: str