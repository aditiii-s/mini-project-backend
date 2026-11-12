"""Business logic for complaints - kept out of the routers."""
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models import Complaint, ComplaintHistory, Employee, Notification
from app.schemas import ComplaintCreate

TICKET_PREFIX = "IT"
SEQUENCE_WIDTH = 4


def generate_ticket_id(db: Session) -> str:
    """Build the next ticket id for the current year: IT-YYYY-0001."""
    year = datetime.now().year
    prefix = f"{TICKET_PREFIX}-{year}-"
    last = (
        db.query(Complaint.ticket_id)
        .filter(Complaint.ticket_id.ilike(f"{prefix}%"))
        .order_by(Complaint.ticket_id.desc())
        .first()
    )
    next_number = 1
    if last:
        try:
            next_number = int(last[0].rsplit("-", 1)[1]) + 1
        except (IndexError, ValueError):
            next_number = db.query(func.count(Complaint.id)).scalar() + 1
    return f"{prefix}{next_number:0{SEQUENCE_WIDTH}d}"


def create_complaint(db: Session, employee: Employee, payload: ComplaintCreate) -> Complaint:
    """Insert a complaint plus its first history row. Retries on ticket id clash."""
    for _ in range(5):
        complaint = Complaint(
            ticket_id=generate_ticket_id(db),
            employee_id=employee.id,
            subject=payload.subject.strip(),
            description=payload.description.strip(),
            category=payload.category,
            subcategory=payload.subcategory,
            priority=payload.priority,
            status="Pending",
            office_location=payload.office_location or employee.office_location,
            asset_tag=payload.asset_tag,
            contact_extension=payload.contact_extension,
            attachment_name=payload.attachment_name,
        )
        db.add(complaint)
        try:
            db.flush()
        except IntegrityError:
            db.rollback()
            continue

        db.add(
            ComplaintHistory(
                complaint_id=complaint.id,
                previous_status=None,
                new_status="Pending",
                remarks="Complaint submitted to the IT Cell.",
                updated_by=employee.full_name,
            )
        )
        db.commit()
        db.refresh(complaint)
        return complaint

    raise RuntimeError("Could not allocate a unique ticket id, please retry.")


def list_complaints(
    db: Session,
    employee: Employee,
    search: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[str] = None,
    limit: Optional[int] = None,
):
    stmt = select(Complaint).where(Complaint.employee_id == employee.id)

    if search:
        term = f"%{search.strip()}%"
        # ilike: PostgreSQL comparisons are case-sensitive, unlike MySQL's default collation.
        stmt = stmt.where(or_(Complaint.ticket_id.ilike(term), Complaint.subject.ilike(term)))
    if status and status != "All":
        stmt = stmt.where(Complaint.status == status)
    if category and category != "All":
        stmt = stmt.where(Complaint.category == category)

    stmt = stmt.order_by(Complaint.created_at.desc(), Complaint.id.desc())
    if limit:
        stmt = stmt.limit(limit)
    return db.execute(stmt).scalars().all()


def get_complaint(db: Session, ticket_id: str, employee: Optional[Employee] = None):
    stmt = (
        select(Complaint)
        .options(
            selectinload(Complaint.history),
            selectinload(Complaint.comments),
            selectinload(Complaint.employee),
        )
        .where(Complaint.ticket_id == ticket_id.strip().upper())
    )
    if employee is not None:
        stmt = stmt.where(Complaint.employee_id == employee.id)
    return db.execute(stmt).scalars().first()


def assign_engineer(db: Session, complaint: Complaint, engineer: str, remarks, updated_by) -> Complaint:
    previous = complaint.status
    complaint.assigned_engineer = engineer
    if complaint.status == "Pending":
        complaint.status = "Assigned"
    db.add(
        ComplaintHistory(
            complaint_id=complaint.id,
            previous_status=previous,
            new_status=complaint.status,
            remarks=remarks or f"Assigned to {engineer}.",
            updated_by=updated_by,
        )
    )
    db.add(
        Notification(
            employee_id=complaint.employee_id,
            title=f"{complaint.ticket_id} assigned to an engineer",
            body=f"{engineer} is now handling '{complaint.subject}'.",
            kind="Assignment",
            ticket_id=complaint.ticket_id,
        )
    )
    db.commit()
    db.refresh(complaint)
    return complaint


def update_status(
    db: Session, complaint: Complaint, new_status: str, remarks, resolution_remarks, updated_by
) -> Complaint:
    previous = complaint.status
    complaint.status = new_status
    if new_status == "Resolved":
        complaint.resolved_at = datetime.now(timezone.utc).replace(tzinfo=None)
        if resolution_remarks:
            complaint.resolution_remarks = resolution_remarks
    else:
        complaint.resolved_at = None
    db.add(
        ComplaintHistory(
            complaint_id=complaint.id,
            previous_status=previous,
            new_status=new_status,
            remarks=remarks or resolution_remarks or f"Status changed to {new_status}.",
            updated_by=updated_by,
        )
    )
    db.add(
        Notification(
            employee_id=complaint.employee_id,
            title=f"{complaint.ticket_id} is now {new_status}",
            body=resolution_remarks or remarks or f"'{complaint.subject}' moved to {new_status}.",
            kind="Resolution" if new_status == "Resolved" else "Status",
            ticket_id=complaint.ticket_id,
        )
    )
    db.commit()
    db.refresh(complaint)
    return complaint


def dashboard_stats(db: Session, employee: Employee) -> dict:
    rows = (
        db.query(Complaint.status, func.count(Complaint.id))
        .filter(Complaint.employee_id == employee.id)
        .group_by(Complaint.status)
        .all()
    )
    counts = {status: count for status, count in rows}
    return {
        "total": sum(counts.values()),
        "pending": counts.get("Pending", 0),
        "in_progress": counts.get("In Progress", 0) + counts.get("Assigned", 0),
        "resolved": counts.get("Resolved", 0),
    }
