from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

RequestType = Literal[
    "New Hardware", "Software Installation", "Network Access", "Email / Account Access"
]
RequestStatus = Literal["Submitted", "Under Review", "Approved", "Fulfilled", "Rejected"]


# ------------------------------------------------------- service requests ---
class ServiceRequestCreate(BaseModel):
    request_type: RequestType
    item: str = Field(min_length=3, max_length=200)
    justification: str = Field(min_length=10, max_length=1000)
    office_location: Optional[str] = Field(default=None, max_length=120)


class ServiceRequestOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    request_id: str
    request_type: RequestType
    item: str
    justification: str
    status: RequestStatus
    office_location: Optional[str] = None
    remarks: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ServiceRequestUpdate(BaseModel):
    status: RequestStatus
    remarks: Optional[str] = None


# ---------------------------------------------------------- announcements ---
class AnnouncementOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: str
    kind: Literal["Maintenance", "Outage", "Update", "Notice"]
    starts_at: Optional[datetime] = None
    created_at: datetime


# ---------------------------------------------------------- notifications ---
class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    body: Optional[str] = None
    kind: Literal["Assignment", "Status", "Resolution", "Announcement"]
    ticket_id: Optional[str] = None
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    unread: int
    items: List[NotificationOut]


# ----------------------------------------------------------- kb articles ---
class KbArticleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    slug: str
    category: str
    question: str
    summary: str
    steps: str


# --------------------------------------------------------------- comments ---
class CommentCreate(BaseModel):
    message: str = Field(min_length=2, max_length=1000)


class CommentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    author_name: str
    author_role: str
    message: str
    created_at: datetime


# ---------------------------------------------------------------- profile ---
class ProfileUpdate(BaseModel):
    email: EmailStr
    phone: Optional[str] = Field(default=None, max_length=30)
    office_location: Optional[str] = Field(default=None, max_length=120)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=3, max_length=128)
    new_password: str = Field(min_length=6, max_length=128)


# -------------------------------------------------------------- dashboard ---
class ActivityItem(BaseModel):
    ticket_id: str
    subject: str
    previous_status: Optional[str] = None
    new_status: str
    remarks: Optional[str] = None
    updated_by: str
    created_at: datetime


class DashboardStatsExtended(BaseModel):
    total: int
    pending: int
    in_progress: int
    resolved: int
    avg_resolution_hours: Optional[float] = None
    open_service_requests: int = 0
