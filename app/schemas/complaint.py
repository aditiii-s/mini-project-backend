from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Category = Literal["Hardware", "Software", "Network", "Printer", "Other"]
Priority = Literal["Low", "Medium", "High", "Critical"]
Status = Literal["Pending", "Assigned", "In Progress", "Resolved"]


class ComplaintCreate(BaseModel):
    subject: str = Field(min_length=5, max_length=200)
    description: str = Field(min_length=10, max_length=1500)
    category: Category
    priority: Priority = "Medium"
    asset_tag: Optional[str] = Field(default=None, max_length=60)
    contact_extension: Optional[str] = Field(default=None, max_length=30)
    attachment_name: Optional[str] = Field(default=None, max_length=255)


class ComplaintOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    ticket_id: str
    subject: str
    category: Category
    priority: Priority
    status: Status
    assigned_engineer: Optional[str] = None
    created_at: datetime


class ComplaintHistoryOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    previous_status: Optional[str] = None
    new_status: str
    remarks: Optional[str] = None
    updated_by: str
    created_at: datetime


class ComplaintDetail(ComplaintOut):
    description: str
    asset_tag: Optional[str] = None
    contact_extension: Optional[str] = None
    attachment_name: Optional[str] = None
    resolution_remarks: Optional[str] = None
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    raised_by: Optional[str] = None
    raised_by_employee_id: Optional[str] = None
    department: Optional[str] = None
    office_location: Optional[str] = None
    history: List[ComplaintHistoryOut] = []


class ComplaintTrack(BaseModel):
    ticket_id: str
    subject: str
    category: Category
    priority: Priority
    status: Status
    assigned_engineer: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    raised_by: str


class AssignRequest(BaseModel):
    assigned_engineer: str = Field(min_length=2, max_length=120)
    remarks: Optional[str] = None
    updated_by: str = "IT Cell"


class StatusUpdateRequest(BaseModel):
    status: Status
    remarks: Optional[str] = None
    resolution_remarks: Optional[str] = None
    updated_by: str = "IT Cell"


class DashboardStats(BaseModel):
    total: int
    pending: int
    in_progress: int
    resolved: int
