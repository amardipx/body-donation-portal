import random

from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, Certificate, Family_Member, Institution, Institution_Staff, Death_Report, DonorStatus, DeathReportStatus, StaffRole, UserRole
from app.schemas.family_member_schema import LinkDonorRequest
from app.api.auth_routes import get_current_user
from app.services.donor_status_service import get_donor_status
from app.services.notification_service import send_family_assigned_staff, send_assigned_staff_family

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
    
    existing_family = (
        db.query(Family_Member)
        .filter(Family_Member.user_id == current_user.id)
        .first()
    )
    
    if existing_family:
        raise HTTPException(
            status_code=409,
            detail="You are already linked to a donor."
        )
    
    existing_donor = (
        db.query(Family_Member)
        .filter(Family_Member.donor_id == certificate.donor_id)
        .first()
    )
    
    if existing_donor:
        raise HTTPException(
            status_code=409,
            detail="This donor is already linked to a family member."
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
    background_tasks: BackgroundTasks,
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
    
    institution_id = donor.preferred_institution
    
    institution = (
        db.query(Institution)
        .filter(Institution.id == institution_id)
        .first()
    )

    if institution is None:
        raise HTTPException(
            status_code=404,
            detail="Preferred institution not found."
        )
    
    staff_members = (
        db.query(Institution_Staff)
        .filter(
            Institution_Staff.institution_id == institution.id,
            Institution_Staff.role == StaffRole.admin_staff.value,
            Institution_Staff.is_active == True,
        )
        .all()
    )
    
    if not staff_members:
        raise HTTPException(
            status_code=404,
            detail="No active administrative staff available."
        )
    
    assigned_admin = random.choice(staff_members)
    
    death_report = Death_Report(
        donor_id=donor.id,
        reported_by_family_id=family_member.id,
        assigned_admin_id=assigned_admin.id,
    )
    
    donor.status = DonorStatus.deceased.value
    
    db.add(death_report)
    db.commit()
    db.refresh(death_report)
    
    
    
    background_tasks.add_task(
        send_family_assigned_staff,
        family_member_email=current_user.email,
        family_member_name=current_user.full_name,
        donor_name=donor.user.full_name,
        institution_name=institution.name,
        institution_phone=institution.contact_phone,
        staff_name=assigned_admin.full_name,
        staff_phone=assigned_admin.phone,
        staff_email=assigned_admin.email,
    )
    
    background_tasks.add_task(
        send_assigned_staff_family,
        staff_email=assigned_admin.email,
        staff_name=assigned_admin.full_name,
        donor_name=donor.user.full_name,
        institution_name=institution.name,
        family_member_name=current_user.full_name,
        family_member_email=current_user.email,
        family_member_phone=current_user.phone,
    )
    
    return {
        "message": "Death reported successfully.",
        "donor": {
            "id": str(donor.id),
            "status": donor.status,
        },

        "institution": {
            "name": institution.name,
            "contact_phone": institution.contact_phone,
            "contact_email": institution.contact_email,
        },

        "assigned_admin": {
            "name": assigned_admin.full_name,
            "role": assigned_admin.role,
            "phone": assigned_admin.phone,
            "email": assigned_admin.email,
            "employee_id": assigned_admin.employee_id,
        }
    }

@router.get("/donor_status")
def donor_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "family_member":
        raise HTTPException(
            status_code=403,
            detail="Only family members can access their status."
        )
    
    family_member = (
        db.query(Family_Member)
        .filter(Family_Member.user_id == current_user.id)
        .first()
    )

    if not family_member:
        raise HTTPException(
            status_code=404,
            detail="Family member profile not found."
        )

    donor = family_member.donor

    if not donor:
        raise HTTPException(
            status_code=404,
            detail="No donor linked to this family member."
        )

    return get_donor_status(db, donor.id) 