from sqlalchemy.orm import Session

from app.db.models import Donor, Death_Report, Cadaver

def get_donor_status(db: Session, donor_id):
    donor = (
        db.query(Donor)
        .filter(Donor.id == donor_id)
        .first()
    )
    
    if not donor:
        return None
    
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

    response = {
        "donor": {
            "name": f"{donor.first_name} "
                    f"{donor.middle_name + ' ' if donor.middle_name else ''}"
                    f"{donor.last_name}",
            "donor_status": donor.status,
            "death_report": None,
            "cadaver": None
        }
    }

    if death_report:
        response["donor"]["death_report"] = {
            "status": death_report.status,
            "assigned_admin": (
                death_report.assigned_admin.full_name
                if death_report.assigned_admin
                else None
            )
        }

    if cadaver:
        response["donor"]["cadaver"] = {
            "status": cadaver.status,
            "assigned_admin": (
                cadaver.assigned_admin.full_name
                if cadaver.assigned_admin
                else None
            )
        }

    return response