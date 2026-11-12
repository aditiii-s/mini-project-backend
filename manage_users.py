"""Create or list helpdesk login accounts in the Supabase database.

Usage (from the backend folder, with the virtualenv active):

    python manage_users.py seed                 # insert all built-in test users
    python manage_users.py list                 # show the accounts already in Supabase
    python manage_users.py add EMP5001 "Priya Kumari" priya@bsphcl.example.in secret123 \
        --designation "Executive Engineer" --department "Project Cell" \
        --office "Zonal Office, Gaya" --role employee
    python manage_users.py reset-password EMP1024 newpassword

Accounts that already exist are left untouched.
"""
import argparse
import os
import sys

# Allow running this file from anywhere, e.g. `python backend/manage_users.py list`.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.exc import OperationalError

from app.auth import hash_password
from app.database import SessionLocal, init_db
from app.models import Employee
from app.services.seed import ALL_EMPLOYEES


def _connect_or_exit():
    try:
        init_db()
    except RuntimeError as exc:
        print(exc)
        sys.exit(1)
    except OperationalError as exc:
        print("Supabase connection failed:", exc)
        sys.exit(1)


def cmd_seed(_args):
    _connect_or_exit()
    db = SessionLocal()
    try:
        created, skipped = [], []
        for data in ALL_EMPLOYEES:
            exists = (
                db.query(Employee).filter(Employee.employee_id == data["employee_id"]).first()
            )
            if exists:
                skipped.append(data["employee_id"])
                continue
            db.add(
                Employee(
                    employee_id=data["employee_id"],
                    full_name=data["full_name"],
                    email=data["email"],
                    password_hash=hash_password(data["password"]),
                    designation=data["designation"],
                    department=data["department"],
                    office_location=data["office_location"],
                    role=data["role"],
                )
            )
            created.append(f"{data['employee_id']} / {data['password']}")
        db.commit()
        print("Created:", ", ".join(created) if created else "none")
        print("Already present:", ", ".join(skipped) if skipped else "none")
    finally:
        db.close()


def cmd_list(_args):
    _connect_or_exit()
    db = SessionLocal()
    try:
        rows = db.query(Employee).order_by(Employee.id).all()
        if not rows:
            print("No employees in the database yet. Run: python manage_users.py seed")
            return
        print(f"{'EMPLOYEE ID':<12} {'NAME':<24} {'ROLE':<10} {'DEPARTMENT':<22} EMAIL")
        for e in rows:
            print(
                f"{e.employee_id:<12} {e.full_name:<24} {e.role:<10} "
                f"{e.department:<22} {e.email}"
            )
        print(f"\n{len(rows)} account(s).")
    finally:
        db.close()


def cmd_add(args):
    _connect_or_exit()
    db = SessionLocal()
    try:
        employee_id = args.employee_id.strip().upper()
        clash = (
            db.query(Employee)
            .filter((Employee.employee_id == employee_id) | (Employee.email == args.email))
            .first()
        )
        if clash:
            print(f"An account with Employee ID {clash.employee_id} or that email already exists.")
            sys.exit(1)
        db.add(
            Employee(
                employee_id=employee_id,
                full_name=args.full_name,
                email=args.email,
                password_hash=hash_password(args.password),
                designation=args.designation,
                department=args.department,
                office_location=args.office,
                role=args.role,
            )
        )
        db.commit()
        print(f"Created {employee_id} / {args.password} ({args.role}).")
    finally:
        db.close()


def cmd_reset_password(args):
    _connect_or_exit()
    db = SessionLocal()
    try:
        employee = (
            db.query(Employee)
            .filter(Employee.employee_id == args.employee_id.strip().upper())
            .first()
        )
        if not employee:
            print(f"No account with Employee ID {args.employee_id.upper()}.")
            sys.exit(1)
        employee.password_hash = hash_password(args.password)
        db.commit()
        print(f"Password updated for {employee.employee_id}.")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="Manage BSPHCL helpdesk login accounts.")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("seed", help="insert the built-in test accounts").set_defaults(func=cmd_seed)
    sub.add_parser("list", help="list the accounts in Supabase").set_defaults(func=cmd_list)

    add = sub.add_parser("add", help="create one account")
    add.add_argument("employee_id")
    add.add_argument("full_name")
    add.add_argument("email")
    add.add_argument("password")
    add.add_argument("--designation", default="Employee")
    add.add_argument("--department", default="General")
    add.add_argument("--office", default="Head Office, Patna")
    add.add_argument("--role", default="employee", choices=["employee", "admin"])
    add.set_defaults(func=cmd_add)

    reset = sub.add_parser("reset-password", help="set a new password for an account")
    reset.add_argument("employee_id")
    reset.add_argument("password")
    reset.set_defaults(func=cmd_reset_password)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
