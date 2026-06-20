from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Donor
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
    donor = Donor(
        user_id=current_user.id,
        gender=consent_data.gender.value,
        date_of_birth=consent_data.date_of_birth,
        blood_type=consent_data.blood_type.value,
        address=consent_data.address,
        city=consent_data.city,
        state=consent_data.state,
        zip_code=consent_data.zip_code,
        country=consent_data.country,
        preferred_institution=consent_data.preferred_institution,
    )

    return {
        "message": "Donor object created",
        "user": current_user.email,
        "gender": donor.gender,
        "blood_type": donor.blood_type,
        "city": donor.city,
    }
