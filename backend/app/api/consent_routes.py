from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Donor, Consent, Consent_Witness
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

    existing_donor = (
        db.query(Donor)
        .filter(Donor.user_id == current_user.id)
        .first()
    )

    if existing_donor:
        raise HTTPException(
            status_code=400,
            detail="Consent form already submitted for this user."
        )
    
    if len(consent_data.witnesses) != 2:
        raise HTTPException(
            status_code=400,
            detail="Exactly 2 witnesses are required."
        )

    donor = Donor(
        user_id=current_user.id,

        first_name=consent_data.first_name,
        middle_name=consent_data.middle_name,
        last_name=consent_data.last_name,
        parent_name=consent_data.parent_name,

        gender=consent_data.gender.value,
        date_of_birth=consent_data.date_of_birth,
        blood_type=consent_data.blood_type.value,

        address_line_1=consent_data.address_line_1,
        address_line_2=consent_data.address_line_2,

        city=consent_data.city,
        district=consent_data.district,
        state=consent_data.state,
        zip_code=consent_data.zip_code,
        country=consent_data.country,

        identity_type=consent_data.identity_type,
        identity_number=consent_data.identity_number,

        declaration_accepted=consent_data.declaration_accepted,

        preferred_institution=consent_data.preferred_institution,
    )

    db.add(donor)
    db.flush()

    consent = Consent(
        donor_id=donor.id
    )

    db.add(consent)
    db.flush()

    for witness_data in consent_data.witnesses:
        witness = Consent_Witness(
            consent_id=consent.id,
            full_name=witness_data.full_name,
            relation=witness_data.relation.value,
            email=witness_data.email,
            phone=witness_data.phone,
        )
    
        db.add(witness)

    db.commit()

    db.refresh(donor)
    db.refresh(consent)

    return {
        "message": "Donor object created",
        "donor_id": str(donor.id),
        "consent_id": str(consent.id),
        "donor_status": donor.status,
        "consent_status": consent.status
    }

