"""Service requests, announcements, notifications, comments and the knowledge base."""
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

REQUEST_TYPES = (
    "New Hardware",
    "Software Installation",
    "Network Access",
    "Email / Account Access",
)
REQUEST_STATUSES = ("Submitted", "Under Review", "Approved", "Fulfilled", "Rejected")
ANNOUNCEMENT_KINDS = ("Maintenance", "Outage", "Update", "Notice")
NOTIFICATION_KINDS = ("Assignment", "Status", "Resolution", "Announcement")


class ServiceRequest(Base):
    """Requests for new kit or access - kept separate from fault complaints."""

    __tablename__ = "service_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[str] = mapped_column(String(20), unique=True, nullable=False, index=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    request_type: Mapped[str] = mapped_column(
        Enum(*REQUEST_TYPES, name="service_request_type"), nullable=False
    )
    item: Mapped[str] = mapped_column(String(200), nullable=False)
    justification: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        Enum(*REQUEST_STATUSES, name="service_request_status"),
        nullable=False,
        default="Submitted",
        index=True,
    )
    office_location: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    remarks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    employee = relationship("Employee")


class Announcement(Base):
    """IT Cell notices shown on the dashboard."""

    __tablename__ = "announcements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    kind: Mapped[str] = mapped_column(
        Enum(*ANNOUNCEMENT_KINDS, name="announcement_kind"), nullable=False, default="Notice"
    )
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    starts_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class Notification(Base):
    """Per-employee alerts raised when their tickets move along."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    employee_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("employees.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    kind: Mapped[str] = mapped_column(
        Enum(*NOTIFICATION_KINDS, name="notification_kind"), nullable=False, default="Status"
    )
    ticket_id: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)


class ComplaintComment(Base):
    """Messages exchanged between the employee and the IT Cell on a ticket."""

    __tablename__ = "complaint_comments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    complaint_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True
    )
    author_name: Mapped[str] = mapped_column(String(120), nullable=False)
    author_role: Mapped[str] = mapped_column(String(20), nullable=False, default="employee")
    message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)

    complaint = relationship("Complaint", back_populates="comments")


class KbArticle(Base):
    """Self-help articles for the knowledge base."""

    __tablename__ = "kb_articles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(120), unique=True, nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    question: Mapped[str] = mapped_column(String(250), nullable=False)
    summary: Mapped[str] = mapped_column(String(400), nullable=False)
    steps: Mapped[str] = mapped_column(Text, nullable=False)  # one step per line
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
