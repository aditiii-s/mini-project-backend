from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth import create_access_token, get_current_employee, hash_password, verify_password
from app.database import get_db
from app.models import Employee
from app.schemas import EmployeeOut, LoginRequest, RegisterRequest, TokenResponse
from app.schemas.extras import PasswordChange, ProfileUpdate

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    employee = (
        db.query(Employee)
        .filter(Employee.employee_id == payload.employee_id.strip().upper())
        .first()
    )
    if not employee or not verify_password(payload.password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Employee ID or password.",
        )
    return TokenResponse(
        access_token=create_access_token(employee),
        employee=EmployeeOut.model_validate(employee),
    )


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    employee_id = payload.employee_id.strip().upper()
    exists = (
        db.query(Employee)
        .filter((Employee.employee_id == employee_id) | (Employee.email == payload.email))
        .first()
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this Employee ID or email already exists.",
        )

    employee = Employee(
        employee_id=employee_id,
        full_name=payload.full_name.strip(),
        email=payload.email,
        password_hash=hash_password(payload.password),
        designation=payload.designation,
        department=payload.department,
        office_location=payload.office_location,
        role="employee",
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return TokenResponse(
        access_token=create_access_token(employee),
        employee=EmployeeOut.model_validate(employee),
    )


@router.get("/me", response_model=EmployeeOut)
def me(employee: Employee = Depends(get_current_employee)):
    return employee


@router.put("/me", response_model=EmployeeOut)
def update_profile(
    payload: ProfileUpdate,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    """Employees may correct their own contact details, nothing else."""
    clash = (
        db.query(Employee)
        .filter(Employee.email == payload.email, Employee.id != employee.id)
        .first()
    )
    if clash:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Another account already uses this email address.",
        )
    employee.email = payload.email
    employee.phone = (payload.phone or "").strip() or None
    if payload.office_location:
        employee.office_location = payload.office_location.strip()
    db.commit()
    db.refresh(employee)
    return employee


@router.post("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: PasswordChange,
    db: Session = Depends(get_db),
    employee: Employee = Depends(get_current_employee),
):
    if not verify_password(payload.current_password, employee.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Your current password is incorrect."
        )
    if payload.current_password == payload.new_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new password must be different from the current one.",
        )
    employee.password_hash = hash_password(payload.new_password)
    db.commit()
    return {"detail": "Password updated. Use it the next time you sign in."}
