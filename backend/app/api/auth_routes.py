from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user_schema import UserSignup
from app.db.database import get_db
from app.db.models import User
from app.utils.security import hash_password

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
        role="donor",
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User registered successfully.",
        "user_id": str(new_user.id),
    }
