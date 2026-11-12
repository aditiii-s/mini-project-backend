from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import get_current_employee
from app.database import get_db
from app.models import Employee
from app.schemas import ComplaintOut, DashboardStats
from app.services import dashboard_stats, list_complaints

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/stats", response_model=DashboardStats)
def stats(
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    return dashboard_stats(db, employee)


@router.get("/recent-complaints", response_model=List[ComplaintOut])
def recent_complaints(
    limit: int = 4,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    return list_complaints(db, employee, limit=max(1, min(limit, 20)))
