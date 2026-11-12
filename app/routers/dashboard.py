from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from sqlalchemy import select

from app.auth import get_current_employee
from app.database import get_db
from app.models import Complaint, ComplaintHistory, Employee, ServiceRequest
from app.schemas import ComplaintOut
from app.schemas.extras import ActivityItem, DashboardStatsExtended
from app.services import dashboard_stats, list_complaints

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStatsExtended)
def stats(
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    data = dashboard_stats(db, employee)

    # Mean hours between raising a complaint and it being resolved.
    resolved = db.execute(
        select(Complaint.created_at, Complaint.resolved_at).where(
            Complaint.employee_id == employee.id,
            Complaint.status == "Resolved",
            Complaint.resolved_at.is_not(None),
        )
    ).all()
    if resolved:
        hours = [
            (done - raised).total_seconds() / 3600.0
            for raised, done in resolved
            if done and raised
        ]
        data["avg_resolution_hours"] = round(sum(hours) / len(hours), 1) if hours else None
    else:
        data["avg_resolution_hours"] = None

    data["open_service_requests"] = (
        db.query(ServiceRequest)
        .filter(
            ServiceRequest.employee_id == employee.id,
            ServiceRequest.status.notin_(["Fulfilled", "Rejected"]),
        )
        .count()
    )
    return data


@router.get("/activity", response_model=List[ActivityItem])
def recent_activity(
    limit: int = 6,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    """Latest status changes across the employee's own complaints."""
    rows = db.execute(
        select(ComplaintHistory, Complaint.ticket_id, Complaint.subject)
        .join(Complaint, Complaint.id == ComplaintHistory.complaint_id)
        .where(Complaint.employee_id == employee.id)
        .order_by(ComplaintHistory.created_at.desc(), ComplaintHistory.id.desc())
        .limit(max(1, min(limit, 25)))
    ).all()
    return [
        ActivityItem(
            ticket_id=ticket_id,
            subject=subject,
            previous_status=history.previous_status,
            new_status=history.new_status,
            remarks=history.remarks,
            updated_by=history.updated_by,
            created_at=history.created_at,
        )
        for history, ticket_id, subject in rows
    ]


@router.get("/recent-complaints", response_model=List[ComplaintOut])
def recent_complaints(
    limit: int = 4,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    return list_complaints(db, employee, limit=max(1, min(limit, 20)))
