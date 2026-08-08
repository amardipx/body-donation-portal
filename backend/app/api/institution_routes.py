from fastapi import APIRouter, Depends, File, HTTPException, BackgroundTasks, UploadFile
import pandas as pd
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import User, UserRole, Institution, Institution_Staff, StaffRole
from app.schemas.institution_schema import InstitutionStaffCreate    
from app.api.auth_routes import get_current_user

from app.utils.security import hash_password
from app.services.password_service import generate_random_password
from app.services.notification_service import send_staff_credentials

router = APIRouter(
    prefix="/institutions",
    tags=["Institution"]
)

@router.post("/add_staff")
def add_staff(
    staff: InstitutionStaffCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can use these features."
        )
    
    current_user_institute = (
        db.query(Institution_Staff)
        .filter(Institution_Staff.user_id == current_user.id)
        .first()
    )
    
    if not current_user_institute or current_user_institute.role != StaffRole.admin_head.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution admin heads can add staff."
        )
        
    existing_employee = (
        db.query(Institution_Staff)
        .filter(Institution_Staff.employee_id == staff.employee_id)
        .first()
    )

    if existing_employee:
        raise HTTPException(
            status_code=400,
            detail="Staff with this employee ID already exists."
        )
    
    existing_email = (
        db.query(User)
        .filter(User.email == staff.email)
        .first()
    )
    if existing_email:
        raise HTTPException(
            status_code = 400,
            detail = "Staff with this email already exists."
        )
    
    existing_phone = (
        db.query(User)
        .filter(User.phone == staff.phone)
        .first()
    )

    if existing_phone:
        raise HTTPException(
            status_code=400,
            detail="Staff with this phone number already exists."
        )
    
    password = generate_random_password(staff.full_name)
    
    new_user = User(
            full_name = staff.full_name,
            email = staff.email,
            phone = staff.phone,
            password_hash = hash_password(password),
            role = UserRole.institution_staff.value,
            is_email_verified=True,
            is_phone_verified=True,
        )
    
    db.add(new_user)
    db.flush()

    new_staff = Institution_Staff(
        user_id = new_user.id,
        institution_id = current_user_institute.institution_id,
        employee_id = staff.employee_id,
        role = staff.role.value,
        full_name = staff.full_name,
        email = staff.email,
        phone = staff.phone,
        is_active = True
    )
    
    db.add(new_staff) 
    db.commit()
    
    db.refresh(new_user)
    db.refresh(new_staff)
    
    background_tasks.add_task(
            send_staff_credentials,
            staff_email = staff.email,
            staff_name = staff.full_name,
            institution_name = current_user_institute.institution.name,
            staff_password = password
        )
    
    return {
        "message": "Staff added successfully."
        }

@router.post("/add_staff_bulk")
def add_staff_bulk(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can use these features."
        )
    
    current_user_institute = (
        db.query(Institution_Staff)
        .filter(Institution_Staff.user_id == current_user.id)
        .first()
    )
    
    if not current_user_institute or current_user_institute.role != StaffRole.admin_head.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution admin heads can add staff."
        )
    
    if file.filename.endswith('.csv'):
        df = pd.read_csv(file.file)
    
    elif file.filename.endswith('.xlsx'):
        df = pd.read_excel(
            file.file,
            engine='openpyxl'
        )
    
    else:
        raise HTTPException(
            status_code=400,
            detail="Only CSV and Excel files are supported."
        )
        
    df.columns = df.columns.str.strip()
    
    required_columns = {'employee_id', 'full_name', 'email', 'phone', 'role'}
    
    file_columns = set(df.columns)
    missing_columns = required_columns - file_columns
    
    if missing_columns:
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Invalid file format.",
                "missing_columns": list(missing_columns),
                "required_columns": list(required_columns),
            }
        )
    added_staff = []
    failed_staff = []
    
    for _, row in df.iterrows():
        try:
            staff = InstitutionStaffCreate(
                employee_id = str(row['employee_id']),
                full_name = str(row['full_name']),
                email = str(row['email']),
                phone = str(row['phone']),
                role = StaffRole(row['role'])
            )
            
            existing_employee = (
                db.query(Institution_Staff)
                .filter(Institution_Staff.employee_id == staff.employee_id)
                .first()
            )

            if existing_employee:
                failed_staff.append({
                    "name": staff.full_name,
                    "reason": "Staff with this employee ID already exists."
                })
                continue
            
            existing_email = (
                db.query(User)
                .filter(User.email == staff.email)
                .first()
            )
            if existing_email:
                failed_staff.append({
                    "name": staff.full_name,
                    "reason": "Staff with this email already exists."
                })
                continue
            
            existing_phone = (
                db.query(User)
                .filter(User.phone == staff.phone)
                .first()
            )

            if existing_phone:
                failed_staff.append({
                    "name": staff.full_name,
                    "reason": "Staff with this phone number already exists."
                })
                continue
            
            password = generate_random_password(staff.full_name)
            
            new_user = User(
                    full_name = staff.full_name,
                    email = staff.email,
                    phone = staff.phone,
                    password_hash = hash_password(password),
                    role = UserRole.institution_staff.value,
                    is_email_verified=True,
                    is_phone_verified=True,
                )
            
            db.add(new_user)
            db.flush()

            new_staff = Institution_Staff(
                user_id = new_user.id,
                institution_id = current_user_institute.institution_id,
                employee_id = staff.employee_id,
                role = staff.role.value,
                full_name = staff.full_name,
                email = staff.email,
                phone = staff.phone,
                is_active = True
            )
            
            db.add(new_staff) 
       
            added_staff.append((staff.full_name, password))
            
            background_tasks.add_task(
                send_staff_credentials,
                staff_email = staff.email,
                staff_name = staff.full_name,
                institution_name = current_user_institute.institution.name,
                staff_password = password
            )
            
        except Exception as e:
            failed_staff.append({
                "name": str(row.get('full_name', 'Unknown')),
                "reason": str(e)
            })
            continue
    
    db.commit()
    
    return {
        "message": "Bulk staff addition completed.",
        "added": len(added_staff),
        "failed": len(failed_staff),
        "added_staff": added_staff,
        "failed_staff": failed_staff,
    }


@router.delete("/remove_staff/{employee_id}")
def remove_staff(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can use these features."
        )

    current_user_institute = (
        db.query(Institution_Staff)
        .filter(Institution_Staff.user_id == current_user.id)
        .first()
    )

    if not current_user_institute or current_user_institute.role != StaffRole.admin_head.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution admin heads can remove staff."
        )

    staff = (
        db.query(Institution_Staff)
        .filter(
            Institution_Staff.employee_id == employee_id,
            Institution_Staff.institution_id == current_user_institute.institution_id
        )
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="Staff with this employee ID not found."
        )

    user = (
        db.query(User)
        .filter(User.id == staff.user_id)
        .first()
    )

    staff.is_active = False
    user.is_active = False

    db.commit()

    return {
        "message": "Staff removed successfully."
    }

@router.delete("/remove_staff/{employee_id}")
def remove_staff(
    employee_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can use these features."
        )

    current_user_institute = (
        db.query(Institution_Staff)
        .filter(Institution_Staff.user_id == current_user.id)
        .first()
    )

    if not current_user_institute or current_user_institute.role != StaffRole.admin_head.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution admin heads can remove staff."
        )
    
    if current_user_institute.employee_id == employee_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot remove your own staff account."
        )
        
    staff = (
        db.query(Institution_Staff)
        .filter(
            Institution_Staff.employee_id == employee_id,
            Institution_Staff.institution_id == current_user_institute.institution_id
        )
        .first()
    )

    if not staff:
        raise HTTPException(
            status_code=404,
            detail="Staff with this employee ID not found."
        )

    user = (
        db.query(User)
        .filter(User.id == staff.user_id)
        .first()
    )

    staff.is_active = False
    user.is_active = False

    db.commit()

    return {
        "message": "Staff removed successfully."
    }