from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth import get_current_employee
from app.database import get_db
from app.models import Complaint, ComplaintComment, Employee, Notification
from app.schemas import (
    AssignRequest,
    ComplaintCreate,
    ComplaintDetail,
    ComplaintOut,
    ComplaintTrack,
    StatusUpdateRequest,
)
from app.schemas.extras import CommentCreate, CommentOut
from app.services import (
    assign_engineer,
    create_complaint,
    get_complaint,
    list_complaints,
    update_status,
)

router = APIRouter(prefix="/api/complaints", tags=["Complaints"])


def _to_detail(complaint: Complaint) -> ComplaintDetail:
    detail = ComplaintDetail.model_validate(complaint)
    if complaint.employee:
        detail.raised_by = complaint.employee.full_name
        detail.raised_by_employee_id = complaint.employee.employee_id
        detail.department = complaint.employee.department
        detail.office_location = complaint.employee.office_location
    return detail


@router.post("", response_model=ComplaintDetail, status_code=status.HTTP_201_CREATED)
def submit_complaint(
    payload: ComplaintCreate,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    complaint = create_complaint(db, employee, payload)
    return _to_detail(get_complaint(db, complaint.ticket_id, employee))


@router.get("", response_model=List[ComplaintOut])
def my_complaints(
    search: Optional[str] = Query(default=None, max_length=120),
    status_filter: Optional[str] = Query(default=None, alias="status"),
    category: Optional[str] = Query(default=None),
    limit: Optional[int] = Query(default=None, ge=1, le=200),
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    return list_complaints(db, employee, search, status_filter, category, limit)


@router.get("/track/{ticket_id}", response_model=ComplaintTrack)
def track(ticket_id: str, db: Session = Depends(get_db)):
    """Public tracking - returns a summary for any valid ticket id."""
    complaint = get_complaint(db, ticket_id)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No complaint found with ticket ID {ticket_id.upper()}.",
        )
    return ComplaintTrack(
        ticket_id=complaint.ticket_id,
        subject=complaint.subject,
        category=complaint.category,
        priority=complaint.priority,
        status=complaint.status,
        assigned_engineer=complaint.assigned_engineer,
        created_at=complaint.created_at,
        updated_at=complaint.updated_at,
        resolved_at=complaint.resolved_at,
        raised_by=complaint.employee.full_name if complaint.employee else "-",
    )


@router.get("/{ticket_id}", response_model=ComplaintDetail)
def complaint_details(
    ticket_id: str,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    complaint = get_complaint(db, ticket_id, None if employee.role == "admin" else employee)
    if not complaint:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Complaint {ticket_id.upper()} was not found.",
        )
    return _to_detail(complaint)


# ---------------------------------------------------------------- IT Cell ---


def _admin_only(employee: Employee = Depends(get_current_employee)) -> Employee:
    if employee.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only IT Cell administrators can perform this action.",
        )
    return employee


@router.put("/{ticket_id}/assign", response_model=ComplaintDetail)
def assign(
    ticket_id: str,
    payload: AssignRequest,
    db: Session = Depends(get_db),
    admin: Employee = Depends(_admin_only),
):
    complaint = get_complaint(db, ticket_id)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {ticket_id.upper()} was not found.")
    assign_engineer(db, complaint, payload.assigned_engineer, payload.remarks, admin.full_name)
    return _to_detail(get_complaint(db, ticket_id))


@router.put("/{ticket_id}/status", response_model=ComplaintDetail)
def change_status(
    ticket_id: str,
    payload: StatusUpdateRequest,
    db: Session = Depends(get_db),
    admin: Employee = Depends(_admin_only),
):
    complaint = get_complaint(db, ticket_id)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {ticket_id.upper()} was not found.")
    update_status(
        db, complaint, payload.status, payload.remarks, payload.resolution_remarks, admin.full_name
    )
    return _to_detail(get_complaint(db, ticket_id))


@router.get("/{ticket_id}/comments", response_model=List[CommentOut])
def list_comments(
    ticket_id: str,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    complaint = get_complaint(db, ticket_id, None if employee.role == "admin" else employee)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {ticket_id.upper()} was not found.")
    return complaint.comments


@router.post("/{ticket_id}/comments", response_model=CommentOut, status_code=status.HTTP_201_CREATED)
def add_comment(
    ticket_id: str,
    payload: CommentCreate,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    """Employees may comment on their own tickets; the IT Cell on any ticket."""
    complaint = get_complaint(db, ticket_id, None if employee.role == "admin" else employee)
    if not complaint:
        raise HTTPException(status_code=404, detail=f"Complaint {ticket_id.upper()} was not found.")

    comment = ComplaintComment(
        complaint_id=complaint.id,
        author_name=employee.full_name,
        author_role=employee.role,
        message=payload.message.strip(),
    )
    db.add(comment)

    # Tell the ticket owner when the IT Cell replies.
    if employee.role == "admin" and complaint.employee_id != employee.id:
        db.add(
            Notification(
                employee_id=complaint.employee_id,
                title=f"New reply on {complaint.ticket_id}",
                body=payload.message.strip()[:180],
                kind="Status",
                ticket_id=complaint.ticket_id,
            )
        )

    db.commit()
    db.refresh(comment)
    return comment
