"""Seeds the login accounts (demo employee, IT admin, extra test users)
and four sample complaints for the demo employee."""
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.auth import hash_password
from app.database import SessionLocal
from app.models import Complaint, ComplaintHistory, Employee

DEMO_EMPLOYEE = {
    "employee_id": "EMP1024",
    "full_name": "Rakesh Kumar Sinha",
    "email": "rakesh.sinha@bsphcl.example.in",
    "password": "demo123",
    "designation": "Assistant Engineer",
    "department": "Revenue & Billing",
    "office_location": "Head Office, Patna",
    "role": "employee",
}

DEMO_ADMIN = {
    "employee_id": "ITADMIN",
    "full_name": "IT Cell Administrator",
    "email": "itcell@bsphcl.example.in",
    "password": "admin123",
    "designation": "System Administrator",
    "department": "IT Cell",
    "office_location": "Head Office, Patna",
    "role": "admin",
}

# Extra login accounts for testing. The first two above are the documented demo
# accounts; these cover a second office, a second department and an IT engineer.
EXTRA_EMPLOYEES = [
    {
        "employee_id": "EMP2048",
        "full_name": "Sunita Devi",
        "email": "sunita.devi@bsphcl.example.in",
        "password": "test123",
        "designation": "Junior Engineer",
        "department": "Transmission",
        "office_location": "Zonal Office, Muzaffarpur",
        "role": "employee",
    },
    {
        "employee_id": "EMP3301",
        "full_name": "Manoj Kumar Verma",
        "email": "manoj.verma@bsphcl.example.in",
        "password": "test123",
        "designation": "Accounts Officer",
        "department": "Finance & Accounts",
        "office_location": "Head Office, Patna",
        "role": "employee",
    },
    {
        "employee_id": "ITENG01",
        "full_name": "Anjali Mishra",
        "email": "anjali.mishra@bsphcl.example.in",
        "password": "admin123",
        "designation": "IT Engineer",
        "department": "IT Cell",
        "office_location": "Head Office, Patna",
        "role": "admin",
    },
]

ALL_EMPLOYEES = [DEMO_EMPLOYEE, DEMO_ADMIN] + EXTRA_EMPLOYEES

NOW = datetime.now()

SAMPLE_COMPLAINTS = [
    {
        "ticket_id": "IT-2026-0121",
        "subject": "Paper jam in shared printer, Billing section",
        "description": (
            "The shared HP LaserJet in the Billing section jams on every second page. "
            "Consumer bills for the Patna division could not be printed on time."
        ),
        "category": "Printer",
        "priority": "Low",
        "status": "Resolved",
        "assigned_engineer": "Rohit Raj - Printers & Peripherals",
        "resolution_remarks": "Roller cleaned and a worn pickup roller replaced. Test print verified by the section in-charge.",
        "days_ago": 18,
        "asset_tag": "PRN-BLG-07",
        "history": [
            (None, "Pending", "Complaint submitted to the IT Cell.", "Rakesh Kumar Sinha", 18),
            ("Pending", "Assigned", "Assigned to Rohit Raj - Printers & Peripherals.", "IT Cell", 17),
            ("Assigned", "In Progress", "Engineer visited the Billing section and opened the printer.", "Rohit Raj", 16),
            ("In Progress", "Resolved", "Pickup roller replaced, test print successful.", "Rohit Raj", 15),
        ],
    },
    {
        "ticket_id": "IT-2026-0134",
        "subject": "Billing application very slow during peak hours",
        "description": (
            "The revenue billing application takes 30-40 seconds per screen between 11:00 and 13:00. "
            "Counter operations at the Patna head office are getting delayed."
        ),
        "category": "Software",
        "priority": "Medium",
        "status": "In Progress",
        "assigned_engineer": "Anjali Mishra - Software",
        "resolution_remarks": None,
        "days_ago": 8,
        "contact_extension": "1147",
        "history": [
            (None, "Pending", "Complaint submitted to the IT Cell.", "Rakesh Kumar Sinha", 8),
            ("Pending", "Assigned", "Assigned to Anjali Mishra - Software.", "IT Cell", 7),
            ("Assigned", "In Progress", "Application logs collected, database query tuning under way.", "Anjali Mishra", 5),
        ],
    },
    {
        "ticket_id": "IT-2026-0144",
        "subject": "VPN disconnects every 10 minutes",
        "description": (
            "The office VPN client drops the connection roughly every ten minutes and has to be "
            "reconnected manually. Remote access to the billing server keeps breaking."
        ),
        "category": "Network",
        "priority": "High",
        "status": "Pending",
        "assigned_engineer": None,
        "resolution_remarks": None,
        "days_ago": 4,
        "history": [
            (None, "Pending", "Complaint submitted to the IT Cell.", "Rakesh Kumar Sinha", 4),
        ],
    },
    {
        "ticket_id": "IT-2026-0149",
        "subject": "UPS beeping and not holding backup",
        "description": (
            "The desktop UPS beeps continuously and the system shuts down immediately when "
            "the mains supply fails. Backup time has dropped to almost zero."
        ),
        "category": "Hardware",
        "priority": "Medium",
        "status": "Pending",
        "assigned_engineer": None,
        "resolution_remarks": None,
        "days_ago": 1,
        "asset_tag": "UPS-RB-214",
        "history": [
            (None, "Pending", "Complaint submitted to the IT Cell.", "Rakesh Kumar Sinha", 1),
        ],
    },
]


def _create_employee(db: Session, data: dict) -> Employee:
    employee = db.query(Employee).filter(Employee.employee_id == data["employee_id"]).first()
    if employee:
        return employee
    employee = Employee(
        employee_id=data["employee_id"],
        full_name=data["full_name"],
        email=data["email"],
        password_hash=hash_password(data["password"]),
        designation=data["designation"],
        department=data["department"],
        office_location=data["office_location"],
        role=data["role"],
    )
    db.add(employee)
    db.flush()
    return employee


def seed_data() -> None:
    db = SessionLocal()
    try:
        employee = _create_employee(db, DEMO_EMPLOYEE)
        for data in ALL_EMPLOYEES[1:]:
            _create_employee(db, data)
        db.commit()

        if db.query(Complaint).filter(Complaint.employee_id == employee.id).count() > 0:
            return

        for item in SAMPLE_COMPLAINTS:
            created = NOW - timedelta(days=item["days_ago"])
            complaint = Complaint(
                ticket_id=item["ticket_id"],
                employee_id=employee.id,
                subject=item["subject"],
                description=item["description"],
                category=item["category"],
                priority=item["priority"],
                status=item["status"],
                asset_tag=item.get("asset_tag"),
                contact_extension=item.get("contact_extension"),
                assigned_engineer=item["assigned_engineer"],
                resolution_remarks=item["resolution_remarks"],
                created_at=created,
                updated_at=created,
            )
            db.add(complaint)
            db.flush()

            last_at = created
            for previous, new, remarks, by, days_ago in item["history"]:
                at = NOW - timedelta(days=days_ago)
                db.add(
                    ComplaintHistory(
                        complaint_id=complaint.id,
                        previous_status=previous,
                        new_status=new,
                        remarks=remarks,
                        updated_by=by,
                        created_at=at,
                    )
                )
                last_at = at
            complaint.updated_at = last_at
            if item["status"] == "Resolved":
                complaint.resolved_at = last_at

        db.commit()
        print(
            "Seed data inserted: %d login accounts and 4 sample complaints."
            % len(ALL_EMPLOYEES)
        )
    finally:
        db.close()


if __name__ == "__main__":
    from app.database import init_db

    init_db()
    seed_data()
