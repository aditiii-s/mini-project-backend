from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

CATEGORIES = ("Hardware", "Software", "Network", "Printer", "Other")
PRIORITIES = ("Low", "Medium", "High", "Critical")
STATUSES = ("Pending", "Assigned", "In Progress", "Resolved")


class Complaint(Base):
    __tablename__ = "complaints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ticket_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[str] = mapped_column(Enum(*CATEGORIES, name="complaint_category"), nullable=False)
    priority: Mapped[str] = mapped_column(
        Enum(*PRIORITIES, name="complaint_priority"), nullable=False, default="Medium"
    )
    status: Mapped[str] = mapped_column(
        Enum(*STATUSES, name="complaint_status"), nullable=False, default="Pending", index=True
    )
    asset_tag: Mapped[Optional[str]] = mapped_column(String(60), nullable=True)
    contact_extension: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    attachment_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    assigned_engineer: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    resolution_remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    employee = relationship("Employee", back_populates="complaints")
    history = relationship(
        "ComplaintHistory",
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintHistory.created_at",
    )


class ComplaintHistory(Base):
    __tablename__ = "complaint_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    previous_status: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30), nullable=False)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    updated_by: Mapped[str] = mapped_column(String(120), nullable=False, default="System")
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    complaint = relationship("Complaint", back_populates="history")
