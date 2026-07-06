from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Certificate, Family_Member, DonorStatus, UserRole
from app.schemas.family_member_schema import LinkDonorRequest
from app.api.auth_routes import get_current_user

router = APIRouter(
    prefix="/family",
    tags=["Family"],
)

@router.post("/link-donor")
def link_donor(
    link_donor: LinkDonorRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.family_member.value:
        raise HTTPException(
            status_code=403,
            detail="Only family members can link to a donor."
        )
    
    certificate = (
        db.query(Certificate)
        .filter(Certificate.certificate_number == link_donor.certificate_number)
        .first()
    )
    
    if certificate is None:
        raise HTTPException(
            status_code=404,
            detail="Invalid certificate number."
        )
    
    existing = (
        db.query(Family_Member)
        .filter(
            Family_Member.user_id == current_user.id,
            Family_Member.donor_id == certificate.donor_id
        )
        .first()
    )
    
    if existing:
        raise HTTPException(
            status_code=409,
            detail="You are already linked to this donor."
        )
    
    family_member = Family_Member(
        user_id = current_user.id,
        donor_id = certificate.donor_id,
        relation = link_donor.relationship
    )
    
    db.add(family_member)
    db.commit()
    db.refresh(family_member)
    
    return {
        "message": "Family member linked successfully."
    }
    
@router.post("/report-death")
def report_death(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if current_user.role != UserRole.family_member.value:
        raise HTTPException(
            status_code=403,
            detail="Only family members can report death."
        )
    
    family_member = (
        db.query(Family_Member)
        .filter(Family_Member.user_id == current_user.id)
        .first()
    )
    
    if family_member is None:
        raise HTTPException(
            status_code=404,
            detail="No donor linked to this family member."
        )
    
    donor = family_member.donor
    
    if donor.status != DonorStatus.registered.value:
        raise HTTPException(
            status_code=400,
            detail=f"Death cannot be reported because donor status is '{donor.status}'."
        )   
    
    return {
        "message": "Donor found successfully.",
        "donor_id": str(donor.id),
        "status": donor.status,
    }