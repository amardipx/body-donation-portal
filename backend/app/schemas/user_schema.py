from pydantic import BaseModel

class UserSignup(BaseModel):
    full_name: str
    email: str
    phone: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str