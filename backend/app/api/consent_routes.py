from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User
from app.schemas.consent_schema import ConsentFormCreate
from app.api.auth_routes import get_current_user

router = APIRouter(
    prefix="/consent",
    tags=["Consent"]
)

@router.post("/")
def submit_consent(
    consent_data: ConsentFormCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if current_user.role != "donor":
        raise HTTPException(status_code=403, detail="Only donors can submit consent forms.")
    return {
        "message": "Consent endpoint reached",
        "user": current_user.email,
        "role": current_user.role
    }
