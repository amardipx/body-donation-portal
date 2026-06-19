from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user_schema import (UserSignup, UserLogin)
from app.db.database import get_db
from app.db.models import User
from app.utils.security import (hash_password, verify_password)

from fastapi import HTTPException

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.post("/signup")
def signup(user: UserSignup, db: Session = Depends(get_db)):
    new_user = User(
        full_name=user.full_name,
        email=user.email,
        phone=user.phone,
        password_hash=hash_password(user.password),
        role=user.role.value,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully.",
        "user_id": str(new_user.id),
    }

@router.post("/login")
def login(user: UserLogin, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == user.email).first()

    if not existing_user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if not verify_password(user.password, existing_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    return {
        "message": "Login successful.",
        "user_id": str(existing_user.id),
        "role": existing_user.role,
    }