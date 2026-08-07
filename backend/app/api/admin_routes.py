from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, UserRole, Institution, Institution_Staff, StaffRole
from app.schemas.institution_schema import InstitutionCreate, InstitutionAdminCreate
from app.api.auth_routes import get_current_user

from app.utils.security import hash_password
from app.services.password_service import generate_random_password
from app.services.notification_service import send_institution_created_email
from pydantic import BaseModel

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

class AddInstitutionRequest(BaseModel):
    institution: InstitutionCreate
    institution_admin: InstitutionAdminCreate

@router.post("/add_institution")
def add_institution(
    request: AddInstitutionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.admin.value:
        raise HTTPException(
            status_code=403,
            detail="Only admins can add institutions."
        )
    
    institution_data = request.institution
    admin_data = request.institution_admin

    existing_institution = (
        db.query(Institution)
        .filter(Institution.registration_number == institution_data.registration_number)
        .first()
    )
    if existing_institution:
        raise HTTPException(
            status_code = 400,
            detail ="Institution with this registration number already exists."
        )
    
    existing_user = (
        db.query(User)
        .filter(User.email == admin_data.email)
        .first()
    )
    if existing_user:
        raise HTTPException(
            status_code = 400,
            detail = "User with this email already exists."
        )
    
    password = generate_random_password(admin_data.full_name)
    
    new_user = User(
            full_name = admin_data.full_name,
            email = admin_data.email,
            phone = admin_data.phone,
            password_hash = hash_password(password),
            role = UserRole.institution_staff.value,
            is_email_verified=True,
            is_phone_verified=True,
        )
    
    db.add(new_user)
    db.flush()
    
    new_institution = Institution(
        type = institution_data.type.value,
        name = institution_data.name,
        registration_number = institution_data.registration_number,
        address = institution_data.address,
        city = institution_data.city,
        state = institution_data.state,
        zip_code = institution_data.zip_code,
        country = institution_data.country,
        contact_email = institution_data.contact_email,
        contact_phone = institution_data.contact_phone
    )
    
    db.add(new_institution)
    db.flush()
    
    new_staff = Institution_Staff(
        user_id = new_user.id,
        institution_id = new_institution.id,
        employee_id = admin_data.employee_id,
        role = StaffRole.admin_head.value,
        full_name = admin_data.full_name,
        email = admin_data.email,
        phone = admin_data.phone,
        is_active = True
    )
    
    db.add(new_staff) 
    
    db.commit()
    db.refresh(new_user)
    db.refresh(new_institution)
    db.refresh(new_staff)
    
    background_tasks.add_task(
        send_institution_created_email,
        staff_email = admin_data.email,
        staff_name = admin_data.full_name,
        institution_name = institution_data.name,
        staff_password = password
    )

    return {
        "message": "Institution and staff added successfully."
    }