import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Donor, Consent, Consent_Witness, ConsentStatus, DonorStatus, Certificate, CertificateType
from app.schemas.consent_schema import ConsentFormCreate
from app.api.auth_routes import get_current_user
from app.services.notification_service import (send_witness_verification, send_donor_confirmation)
from app.services.certificate_service import generate_consent_certificate

from fastapi.templating import Jinja2Templates

templates = Jinja2Templates(directory="app/templates/pages")

router = APIRouter(
    prefix="/consent",
    tags=["Consent"]
)

@router.post("/")
def submit_consent(
    consent_data: ConsentFormCreate,
    background_task: BackgroundTasks,
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

    emails = [w.email for w in consent_data.witnesses]
    if len(set(emails)) != 2:
        raise HTTPException(
            status_code=400,
            detail="Witness email addresses must be unique"
        )

    phones = [w.phone for w in consent_data.witnesses]
    if len(set(phones)) != 2:
        raise HTTPException(
            status_code=400,
            detail="Witness phone numbers must be unique"
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
    
    witnesses_to_notify = []
    
    for witness_data in consent_data.witnesses:
        verification_token = secrets.token_urlsafe(32)
        witness = Consent_Witness(
            consent_id=consent.id,
            full_name=witness_data.full_name,
            relation=witness_data.relation.value,
            email=witness_data.email,
            phone=witness_data.phone,

            verification_token=verification_token,
            verification_sent_at=datetime.now(timezone.utc)
        )
    
        db.add(witness)
        verification_link = (
            f"https://body-donation-portal.onrender.com/consent/verify/{verification_token}"
        )
        
        witnesses_to_notify.append(
            (
                witness.email,
                witness.full_name,
                verification_link
                )
        )

    db.commit()
    
    for email, name, link in witnesses_to_notify:
        background_task.add_task(send_witness_verification, email, name, link)
        
    db.refresh(donor)
    db.refresh(consent)

    return {
        "message": "Donor object created",
        "donor_id": str(donor.id),
        "consent_id": str(consent.id),
        "donor_status": donor.status,
        "consent_status": consent.status
    }

@router.get("/verify/{token}")
def verify_witness(request: Request, background_task: BackgroundTasks, token: str, db: Session = Depends(get_db)):
    witness = (
        db.query(Consent_Witness)
        .filter(Consent_Witness.verification_token == token)
        .first()
    )

    if witness is None:
        raise HTTPException(status_code=404, detail="Invalid verification token")
    
    if witness.witness_verified:
        raise HTTPException(status_code=409, detail="Witness already verified")
    
    witness.witness_verified = True
    witness.verified_at = datetime.now(timezone.utc)

    consent = witness.consent
    all_verified = all(w.witness_verified for w in consent.witnesses)
    
    donor_email, donor_name = None, None

    if all_verified:
        consent.status = ConsentStatus.active.value
        consent.donor.status = DonorStatus.registered.value

        donor = consent.donor
        user = donor.user
        
        certificate_number, storage_path = generate_consent_certificate(donor_name=user.full_name)
        
        certificate = Certificate(
            donor_id = donor.id,
            certificate_number = certificate_number,
            type = CertificateType.consent_certificate.value,
            certificate_file_path = storage_path,
            is_valid = True,
        )
        
        db.add(certificate)
        
        
        donor_email = user.email
        donor_name = user.full_name
        
    db.commit()
    
    if donor_email:
        background_task.add_task(send_donor_confirmation, donor_email, donor_name, storage_path)
        
    return templates.TemplateResponse(
        request = request,
        name= "witness_verified.html",
        context= {}
    )

    
