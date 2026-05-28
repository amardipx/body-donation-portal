import uuid
import enum
from sqlalchemy import Boolean, Column, DateTime, Enum as SAEnum ,String, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.db.database import Base
 
 
#RAG File Model

class DocumentType(str, enum.Enum):
    legal_act  = "legal_act"
    policy_doc = "policy_doc"
 
 
class RagFile(Base):

    __tablename__ = "rag_files"
 
    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    title = Column( String, nullable=False)
    document_type = Column(String(20), nullable=False, index=True)
    file_path = Column(String, nullable=False, unique=True)
    file_hash = Column(String(64), nullable=False, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())


#User Model

class UserRole(str, enum.Enum):
    admin = "admin"
    donor = "donor"
    institution_staff = "institution_staff"
    family_member = "family_member"


class User(Base):

    __tablename__ = "users"

    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    full_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False, unique=True)
    phone = Column(String(20), nullable=False, unique=True)
    is_email_verified = Column(Boolean, default=False)
    is_phone_verified = Column(Boolean, default=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=True, index=True)
    last_login = Column(DateTime(timezone=True))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    
    donor= relationship("Donor", back_populates="user", uselist=False, cascade="all, delete-orphan")
    family_members = relationship("Family_Member", back_populates="user", uselist=False, cascade="all, delete-orphan")
    institution_staff = relationship("Institution_Staff", back_populates="user", uselist=False, cascade="all, delete-orphan")


#Donor Model

class DonorGender(str, enum.Enum):
    male = "male"
    female = "female"
    other = "other"

class DonorBloodType(str, enum.Enum):
    A_pos = "A+"
    A_neg = "A-"
    B_pos = "B+"
    B_neg = "B-"
    AB_pos = "AB+"
    AB_neg = "AB-"
    O_pos = "O+"
    O_neg = "O-"

class DonorStatus(str, enum.Enum):
    pending = "pending"
    registered = "registered"
    withdrawn = "withdrawn"
    deceased = "deceased"
    in_use = "in_use"
    completed = "completed"
    

class Donor(Base):

    __tablename__ = "donors"

    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column( UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    gender = Column(String(20), nullable=False)
    date_of_birth = Column(DateTime, nullable=False)
    blood_type = Column(String(20), nullable=False)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    preferred_institution = Column(UUID(as_uuid=True), ForeignKey("institutions.id"), nullable=True)
    status = Column(String(20), nullable=False, default= "pending")
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="donor")
    institution = relationship("Institution", back_populates="donor")
    consent = relationship("Consent", back_populates="donor", cascade="all, delete-orphan")
    family_members = relationship("Family_Member", back_populates="donor")
    certificates = relationship("Certificate", back_populates="donor", cascade="all, delete-orphan")


#Consent Model

class ConsentStatus(str, enum.Enum):
    pending_witness = "pending_witness"
    active = "active"
    revoked = "revoked"
    rejected = "rejected"

        
class Consent(Base):
    
    __tablename__ = "consents"

    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    donor_id = Column( UUID(as_uuid=True), ForeignKey("donors.id", ondelete="CASCADE"), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    signed_at = Column(DateTime(timezone=True))
    signature_hash = Column(String(64), unique=True)
    signature_file_path = Column(String, nullable=True)
    
    donor = relationship("Donor", back_populates="consent")
    witnesses = relationship("Consent_Witness", back_populates="consent", cascade="all, delete-orphan")


#Witness Model

class Relation(str, enum.Enum):
    husband = "husband"
    wife = "wife"
    parent = "parent"
    friend = "friend"
    son = "son"
    daughter = "daughter"
    other = "other"


class Consent_Witness(Base):
    
    __tablename__ = "consent_witnesses"

    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    consent_id = Column( UUID(as_uuid=True), ForeignKey("consents.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(50), nullable=False)
    relation = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    witness_verified = Column(Boolean, default=False)
    verified_at = Column(DateTime(timezone=True))
    
    consent = relationship("Consent", back_populates="witnesses")


#Certificate Model

class CertificateType(str, enum.Enum):
    consent_certificate = "consent_certificate"
    death_certificate = "death_certificate"
    
    
class Certificate(Base):
    
    __tablename__ = "certificates"
    
    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    donor_id = Column( UUID(as_uuid=True), ForeignKey("donors.id", ondelete="CASCADE"), nullable=False)
    type = Column(String(50), nullable=False)
    issued_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    certificate_file_path = Column(String, nullable=False, unique=True)
    is_valid = Column(Boolean, default=True)
    
    donor = relationship("Donor", back_populates="certificates")
        

#Family Member Model

class Family_Member(Base):
    
    __tablename__ = "family_members"

    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column( UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    donor_id = Column( UUID(as_uuid=True), ForeignKey("donors.id", ondelete="CASCADE"), nullable=False)
    full_name = Column(String(50), nullable=False)
    relation = Column(String(100), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    
    user = relationship("User", back_populates="family_members")
    donor = relationship("Donor", back_populates="family_members")


#Institution Model

class InstitutionType(str, enum.Enum):
    hospital = "hospital"
    medical_college = "medical_college"
    research_center = "research_center"
    

class Institution(Base):
    
    __tablename__ = "institutions"

    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    type = Column(String(50), nullable=False)
    name = Column(String(255), nullable=False)
    registration_number = Column(String(100), nullable=False, unique=True)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100), nullable=False)
    zip_code = Column(String(20), nullable=False)
    country = Column(String(100), nullable=False)
    contact_email = Column(String(255), nullable=False)
    contact_phone = Column(String(20), nullable=False)
    registered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    
    institution_staff = relationship("Institution_Staff", back_populates="institution", cascade="all, delete-orphan")
    donor = relationship("Donor", back_populates="institution")


#Staff Model

class StaffRole(str, enum.Enum):
    hod = "hod"
    doctor = "doctor"
    lab_technician = "lab_technician"
    admin_staff = "admin_staff"

class Institution_Staff(Base):
    
    __tablename__ = "institution_staff"

    id = Column( UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    user_id = Column( UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    institution_id = Column( UUID(as_uuid=True), ForeignKey("institutions.id", ondelete="CASCADE"), nullable=False)
    employee_id = Column(String(100), nullable=False, unique=True)
    role = Column(String(50), nullable=False)
    full_name = Column(String(50), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True)
    
    user = relationship("User", back_populates="institution_staff")
    institution = relationship("Institution", back_populates="institution_staff")
    