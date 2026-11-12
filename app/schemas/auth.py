from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class LoginRequest(BaseModel):
    employee_id: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=3, max_length=128)


class RegisterRequest(BaseModel):
    employee_id: str = Field(min_length=3, max_length=20)
    full_name: str = Field(min_length=3, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    designation: str = "Employee"
    department: str = "General"
    office_location: str = "Head Office, Patna"


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    employee_id: str
    full_name: str
    email: str
    designation: str
    department: str
    office_location: str
    role: str
    created_at: datetime


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    employee: EmployeeOut
