"""Service requests, announcements, notifications and the knowledge base."""
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.auth import get_current_employee
from app.database import get_db
from app.models import Announcement, Employee, KbArticle, Notification, ServiceRequest
from app.schemas.extras import (
    AnnouncementOut,
    KbArticleOut,
    NotificationList,
    NotificationOut,
    ServiceRequestCreate,
    ServiceRequestOut,
    ServiceRequestUpdate,
)

service_router = APIRouter(prefix="/api/service-requests", tags=["Service Requests"])
announcement_router = APIRouter(prefix="/api/announcements", tags=["Announcements"])
notification_router = APIRouter(prefix="/api/notifications", tags=["Notifications"])
kb_router = APIRouter(prefix="/api/knowledge-base", tags=["Knowledge Base"])


def _next_request_id(db: Session) -> str:
    year = datetime.now().year
    prefix = f"SR-{year}-"
    last = (
        db.query(ServiceRequest.request_id)
        .filter(ServiceRequest.request_id.ilike(f"{prefix}%"))
        .order_by(ServiceRequest.request_id.desc())
        .first()
    )
    number = 1
    if last:
        try:
            number = int(last[0].rsplit("-", 1)[1]) + 1
        except (IndexError, ValueError):
            number = db.query(func.count(ServiceRequest.id)).scalar() + 1
    return f"{prefix}{number:04d}"


# ------------------------------------------------------- service requests ---
@service_router.post("", response_model=ServiceRequestOut, status_code=status.HTTP_201_CREATED)
def create_service_request(
    payload: ServiceRequestCreate,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    request = ServiceRequest(
        request_id=_next_request_id(db),
        employee_id=employee.id,
        request_type=payload.request_type,
        item=payload.item.strip(),
        justification=payload.justification.strip(),
        office_location=payload.office_location or employee.office_location,
        status="Submitted",
    )
    db.add(request)
    db.add(
        Notification(
            employee_id=employee.id,
            title=f"Service request {request.request_id} submitted",
            body=f"{payload.request_type}: {payload.item.strip()}",
            kind="Status",
        )
    )
    db.commit()
    db.refresh(request)
    return request


@service_router.get("", response_model=List[ServiceRequestOut])
def list_service_requests(
    status_filter: Optional[str] = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    stmt = select(ServiceRequest).where(ServiceRequest.employee_id == employee.id)
    if status_filter and status_filter != "All":
        stmt = stmt.where(ServiceRequest.status == status_filter)
    stmt = stmt.order_by(ServiceRequest.created_at.desc(), ServiceRequest.id.desc())
    return db.execute(stmt).scalars().all()


@service_router.get("/{request_id}", response_model=ServiceRequestOut)
def service_request_details(
    request_id: str,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    stmt = select(ServiceRequest).where(ServiceRequest.request_id == request_id.strip().upper())
    if employee.role != "admin":
        stmt = stmt.where(ServiceRequest.employee_id == employee.id)
    request = db.execute(stmt).scalars().first()
    if not request:
        raise HTTPException(status_code=404, detail=f"Request {request_id.upper()} was not found.")
    return request


@service_router.put("/{request_id}", response_model=ServiceRequestOut)
def update_service_request(
    request_id: str,
    payload: ServiceRequestUpdate,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    if employee.role != "admin":
        raise HTTPException(status_code=403, detail="Only IT Cell administrators can do this.")
    request = db.execute(
        select(ServiceRequest).where(ServiceRequest.request_id == request_id.strip().upper())
    ).scalars().first()
    if not request:
        raise HTTPException(status_code=404, detail=f"Request {request_id.upper()} was not found.")
    request.status = payload.status
    if payload.remarks:
        request.remarks = payload.remarks
    db.add(
        Notification(
            employee_id=request.employee_id,
            title=f"Service request {request.request_id} is {payload.status}",
            body=payload.remarks,
            kind="Status",
        )
    )
    db.commit()
    db.refresh(request)
    return request


# ---------------------------------------------------------- announcements ---
@announcement_router.get("", response_model=List[AnnouncementOut])
def list_announcements(limit: int = Query(default=5, ge=1, le=50), db: Session = Depends(get_db)):
    stmt = (
        select(Announcement)
        .where(Announcement.active.is_(True))
        .order_by(Announcement.created_at.desc())
        .limit(limit)
    )
    return db.execute(stmt).scalars().all()


# ---------------------------------------------------------- notifications ---
@notification_router.get("", response_model=NotificationList)
def list_notifications(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    items = (
        db.execute(
            select(Notification)
            .where(Notification.employee_id == employee.id)
            .order_by(Notification.created_at.desc(), Notification.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    unread = (
        db.query(func.count(Notification.id))
        .filter(Notification.employee_id == employee.id, Notification.is_read.is_(False))
        .scalar()
    )
    return NotificationList(unread=unread or 0, items=[NotificationOut.model_validate(i) for i in items])


@notification_router.put("/{notification_id}/read", response_model=NotificationOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    item = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.employee_id == employee.id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Notification not found.")
    item.is_read = True
    db.commit()
    db.refresh(item)
    return item


@notification_router.put("/read-all", response_model=NotificationList)
def mark_all_read(
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    db.query(Notification).filter(
        Notification.employee_id == employee.id, Notification.is_read.is_(False)
    ).update({Notification.is_read: True})
    db.commit()
    return list_notifications(limit=20, db=db, employee=employee)


# ----------------------------------------------------------- knowledge base ---
@kb_router.get("", response_model=List[KbArticleOut])
def list_articles(
    search: Optional[str] = Query(default=None, max_length=120),
    category: Optional[str] = Query(default=None),
    db: Session = Depends(get_db),
):
    stmt = select(KbArticle)
    if search:
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                KbArticle.question.ilike(term),
                KbArticle.summary.ilike(term),
                KbArticle.steps.ilike(term),
            )
        )
    if category and category != "All":
        stmt = stmt.where(KbArticle.category == category)
    return db.execute(stmt.order_by(KbArticle.category, KbArticle.id)).scalars().all()
