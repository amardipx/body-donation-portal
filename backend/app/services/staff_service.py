from app.db.models import User, UserRole, Institution_Staff, StaffRole
from app.utils.security import hash_password
from app.services.password_service import generate_random_password

def create_new_staff(
    db,
    full_name: str,
    email: str,
    phone: str,
    employee_id: str,
    role: StaffRole,
    institution_id
):
    password = generate_random_password(full_name)
    
    new_user = User(
            full_name = full_name,
            email = email,
            phone = phone,
            password_hash = hash_password(password),
            role = UserRole.institution_staff.value,
            is_email_verified=True,
            is_phone_verified=True,
        )
    
    db.add(new_user)
    db.flush()

    new_staff = Institution_Staff(
        user_id = new_user.id,
        institution_id = institution_id,
        employee_id = employee_id,
        role = role.value,
        full_name = full_name,
        email = email,
        phone = phone,
        is_active = True
    )
    
    db.add(new_staff) 
    
    db.commit()
    
    db.refresh(new_user)
    db.refresh(new_staff)
    
    return new_user, new_staff, password