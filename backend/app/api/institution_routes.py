from fastapi import APIRouter, Depends, File, HTTPException, BackgroundTasks, UploadFile
import pandas as pd
from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.db.database import get_db
from app.db.models import User, UserRole, Family_Member, Institution_Staff, StaffRole, Donor, DonorStatus, Death_Report, Cadaver, Certificate, DeathReportStatus, CadaverStatus
from app.schemas.institution_schema import InstitutionStaffCreate, DeathReportStatusUpdate, CadaverStatusUpdate 
from app.api.auth_routes import get_current_user

from app.utils.security import hash_password
from app.services.password_service import generate_random_password
from app.services.notification_service import send_staff_credentials, send_death_report_completed, send_cadaver_use_completed

DEATH_REPORT_TRANSITIONS = {
    DeathReportStatus.assigned.value: [
        DeathReportStatus.in_progress.value
    ],
    DeathReportStatus.in_progress.value: [
        DeathReportStatus.completed.value
    ],
    DeathReportStatus.completed.value: []
}

CADAVER_TRANSITIONS = {
    CadaverStatus.available.value: [
        CadaverStatus.in_use.value
    ],
    CadaverStatus.in_use.value: [
        CadaverStatus.available.value,
        CadaverStatus.completed.value
    ],
    CadaverStatus.completed.value: []
}

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

@router.get("/donors_status")
def get_current_donors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can access this feature."
        )


    current_staff = (
        db.query(Institution_Staff)
        .filter(Institution_Staff.user_id == current_user.id)
        .first()
    )

    if not current_staff or current_staff.role != StaffRole.admin_head.value:
            raise HTTPException(
                status_code=403,
                detail="Only institution admin heads can view all donors."
            )

    donors = (
        db.query(Donor)
        .filter(Donor.preferred_institution == current_staff.institution_id)
        .all()
    )

    current_donors = []

    for donor in donors:

        certificate = (
            db.query(Certificate)
            .filter(Certificate.donor_id == donor.id)
            .first()
        )
        
        death_report = (
            db.query(Death_Report)
            .filter(Death_Report.donor_id == donor.id)
            .order_by(Death_Report.reported_at.desc())
            .first()
        )

        cadaver = (
            db.query(Cadaver)
            .filter(Cadaver.donor_id == donor.id)
            .first()
        )

        current_donors.append({
            "certificate_number": (
                certificate.certificate_number
                if certificate else None
            ),
            "donor_name": (
                f"{donor.first_name} "
                f"{donor.middle_name + ' ' if donor.middle_name else ''}"
                f"{donor.last_name}"
            ),
            "donor_status": donor.status,
            "death_report_status":(
                death_report.status
                if death_report else None
            ),
            "cadaver_status": (
                cadaver.status
                if cadaver else None
            ),
            "assigned_admin": (
                {"name": death_report.assigned_admin.full_name,
                 "employee_id": death_report.assigned_admin.employee_id}
                if death_report else None
            )
        })

    return current_donors


@router.get("/donors/assigned")
def get_assigned_donors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can access this feature."
        )


    current_staff = (
        db.query(Institution_Staff)
        .filter(Institution_Staff.user_id == current_user.id)
        .first()
    )

    if not current_staff or current_staff.role != StaffRole.admin_staff.value:
            raise HTTPException(
                status_code=403,
                detail="Only institution admin staff can assigned donors."
            )

    death_reports = (
        db.query(Death_Report)
        .filter(
            Death_Report.assigned_admin_id == current_staff.id
        )
        .all()
    )

    assigned_donors = []

    for death_report in death_reports:

        donor = death_report.donor

        certificate = (
            db.query(Certificate)
            .filter(Certificate.donor_id == donor.id)
            .first()
        )

        cadaver = (
            db.query(Cadaver)
            .filter(Cadaver.donor_id == donor.id)
            .first()
        )

        assigned_donors.append({
            "certificate_number": (
                certificate.certificate_number
                if certificate else None
            ),
            "donor_name": (
                f"{donor.first_name} "
                f"{donor.middle_name + ' ' if donor.middle_name else ''}"
                f"{donor.last_name}"
            ),
            "donor_status": donor.status,
            "death_report_status": death_report.status,
            "cadaver_status": (
                cadaver.status
                if cadaver else None
            )
        })

    return assigned_donors

@router.patch(
    "/donor_status/{certificate_number}/death_report"
)
def update_death_report_status(
    status_update: DeathReportStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can update death report status."
        )

    current_staff = (
        db.query(Institution_Staff)
        .filter(
            Institution_Staff.user_id == current_user.id
        )
        .first()
    )

    if not current_staff or current_staff.role != StaffRole.admin_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution admin staff can update death report status."
        )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.certificate_number == status_update.certificate_number
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found."
        )

    death_report = (
        db.query(Death_Report)
        .filter(
            Death_Report.donor_id == certificate.donor_id
        )
        .first()
    )

    if not death_report:
        raise HTTPException(
            status_code=404,
            detail="Death report not found."
        )

    if death_report.assigned_admin_id != current_staff.id:
        raise HTTPException(
            status_code=403,
            detail="This death report is not assigned to you."
        )

    current_status = death_report.status
    new_status = status_update.status.value
    
    if new_status not in DEATH_REPORT_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition! Cannot change death report status from '{current_status}' to '{new_status}'."
        )
    
    death_report.status = new_status
    admin = death_report.assigned_admin
    
    if new_status == DeathReportStatus.completed.value:
        death_report.completed_at = datetime.now(timezone.utc)
        
        new_cadaver = Cadaver(
            donor_id = death_report.donor_id,
            family_member_id = death_report.reported_by_family_id,
            assigned_admin_id = death_report.assigned_admin_id,
            status = CadaverStatus.available.value
        )
        
        db.add(new_cadaver)
        
        
    
    db.commit()
    
    family_member = (
        db.query(User)
        .join(Family_Member, Family_Member.user_id == User.id)
        .filter(
            Family_Member.id == death_report.reported_by_family_id
        )
        .first()
    )
    
    donor_name = (f"{death_report.donor.first_name} "
                  f"{death_report.donor.middle_name + ' ' if death_report.donor.middle_name else ''}"
                  f"{death_report.donor.last_name}")
    
    if new_status == DeathReportStatus.completed.value:

        background_tasks.add_task(
            send_death_report_completed,
            family_email=family_member.email,
            family_name=family_member.full_name,
            donor_name=donor_name,
            admin_name=admin.full_name,
            admin_email=admin.email,
        )
        
    db.refresh(death_report)

    return {
        "message": "Death report status updated successfully.",
        "certificate_number": status_update.certificate_number,
        "status": death_report.status
    }

@router.patch(
    "/donor_status/{certificate_number}/cadaver"
)
def update_cadaver_status(
    status_update: CadaverStatusUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role != UserRole.institution_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution staff can update cadaver status."
        )

    current_staff = (
        db.query(Institution_Staff)
        .filter(
            Institution_Staff.user_id == current_user.id
        )
        .first()
    )

    if not current_staff or current_staff.role != StaffRole.admin_staff.value:
        raise HTTPException(
            status_code=403,
            detail="Only institution admin staff can update cadaver status."
        )

    certificate = (
        db.query(Certificate)
        .filter(
            Certificate.certificate_number == status_update.certificate_number
        )
        .first()
    )

    if not certificate:
        raise HTTPException(
            status_code=404,
            detail="Certificate not found."
        )

    cadaver = (
        db.query(Cadaver)
        .filter(
            Cadaver.donor_id == certificate.donor_id
        )
        .first()
    )

    if not cadaver:
        raise HTTPException(
            status_code=404,
            detail="Cadaver not found."
        )

    if cadaver.assigned_admin_id != current_staff.id:
        raise HTTPException(
            status_code=403,
            detail="This cadaver is not assigned to you."
        )

    current_status = cadaver.status
    new_status = status_update.status.value
    
    if new_status not in CADAVER_TRANSITIONS.get(current_status, []):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid transition! Cannot change cadaver status from '{current_status}' to '{new_status}'."
        )
    
    cadaver.status = new_status
    
    if new_status == CadaverStatus.in_use.value:
            cadaver.donor.status = DonorStatus.in_use.value
    elif new_status == CadaverStatus.completed.value:
            cadaver.donor.status = DonorStatus.completed.value
    
    db.commit()
    
    
    family_member = (
        db.query(User)
        .join(Family_Member, Family_Member.user_id == User.id)
        .filter(
            Family_Member.id == cadaver.family_member_id
        )
        .first()
    )
    
    donor_name = (f"{cadaver.donor.first_name} "
                  f"{cadaver.donor.middle_name + ' ' if cadaver.donor.middle_name else ''}"
                  f"{cadaver.donor.last_name}")
    
    admin = cadaver.assigned_admin
    
    if new_status == CadaverStatus.completed.value:

        background_tasks.add_task(
            send_cadaver_use_completed,
            family_email=family_member.email,
            family_name=family_member.full_name,
            donor_name=donor_name,
            admin_name=admin.full_name,
            admin_email=admin.email,
        )
    
    db.refresh(cadaver)

    return {
        "message": "Cadaver status updated successfully.",
        "certificate_number": status_update.certificate_number,
        "status": cadaver.status
    }