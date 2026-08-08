from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.schemas.user_schema import (UserSignup, UserLogin)
from app.db.database import get_db
from app.db.models import User, UserRole
from app.utils.security import (hash_password, verify_password, create_access_token, decode_access_token)

from fastapi import HTTPException
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    if payload is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

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
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == form_data.username).first()

    if not existing_user:
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if not verify_password(form_data.password, existing_user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password.")
    
    if not existing_user.is_active:

        if existing_user.role in [
            UserRole.admin.value,
            UserRole.institution_staff.value
        ]:
            raise HTTPException(
                status_code=403,
                detail="Your staff account is currently deactivated. Please contact your admin."
            )

        raise HTTPException(
            status_code=403,
            detail="Your account is currently deactivated."
        )
    
    access_token = create_access_token({"sub": str(existing_user.id), "role": existing_user.role})

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "full_name": current_user.full_name,
        "email": current_user.email,
        "role": current_user.role,
    }
