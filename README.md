# BSPHCL IT Helpdesk — Backend API

FastAPI backend for the **Bihar State Power (Holding) Company Ltd. (BSPHCL)** IT Helpdesk
Management System. Employees sign in with their Employee ID, raise IT complaints, track them
by ticket ID, and the IT Cell assigns engineers and updates ticket status.

Built with FastAPI, SQLAlchemy 2, Pydantic and JWT, on **Supabase (managed PostgreSQL)**.
The frontend lives in a separate repository.

## Setup

```bash
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Create the environment file and paste your Supabase connection string into it
(Supabase dashboard → Project Settings → Database → Connection string → URI, replacing
`[YOUR-PASSWORD]` with your database password):

```bash
cp .env.example .env     # Windows: copy .env.example .env
```

```ini
DATABASE_URL=postgresql://postgres.YOUR_REF:YOUR_PASSWORD@aws-0-REGION.pooler.supabase.com:5432/postgres
SECRET_KEY=change-this-to-a-long-random-string
ACCESS_TOKEN_EXPIRE_MINUTES=720
CORS_ORIGINS=http://localhost:5173
```

That one variable is the whole database configuration, locally and in production. Credentials
are never hardcoded — `app/config.py` reads `DATABASE_URL` and normalises it to the
`postgresql+psycopg://` driver, so Supabase's plain URI can be pasted in as-is.

**Which port?** Use the session pooler (5432) for a normal long-running server. The
transaction pooler (6543) works too — the app detects that port and switches to `NullPool`
with prepared statements disabled, which PgBouncer's transaction mode requires.

## Run

```bash
uvicorn app.main:app --reload
```

* API: <http://localhost:8000>
* Interactive docs: <http://localhost:8000/docs>
* Health check: <http://localhost:8000/api/health>

On the first start the enum types, tables, test accounts and sample complaints are created
automatically. Supabase provides the database itself, so there is no `CREATE DATABASE` step.

## Database

| Table | Purpose |
|---|---|
| `employees` | id, employee_id (unique), full_name, email (unique), password_hash, designation, department, office_location, role, created_at |
| `complaints` | id, ticket_id (unique), employee_id (FK → employees.id), subject, description, category, priority, status, asset_tag, contact_extension, attachment_name, assigned_engineer, resolution_remarks, created_at, updated_at, resolved_at |
| `complaint_history` | id, complaint_id (FK → complaints.id), previous_status, new_status, remarks, updated_by, created_at |

Both foreign keys cascade on delete. `category`, `priority` and `status` are PostgreSQL enum
types; passwords are hashed with bcrypt. Tables are created from the models with
`Base.metadata.create_all()` at startup.

`seed_users.sql` does the same setup by hand — paste it into the Supabase SQL editor. It is
safe to run twice.

## API

All endpoints except `POST /api/auth/login`, `POST /api/auth/register` and
`GET /api/complaints/track/{ticket_id}` require an `Authorization: Bearer <token>` header.

| Method | Path | Description |
|---|---|---|
| POST | `/api/auth/login` | Sign in with `employee_id` + `password`, returns a JWT and the profile |
| POST | `/api/auth/register` | Create an employee account and return a JWT |
| GET | `/api/auth/me` | Current employee profile |
| GET | `/api/dashboard/stats` | `{ total, pending, in_progress, resolved }` for the signed-in employee |
| GET | `/api/dashboard/recent-complaints?limit=4` | Latest complaints, newest first |
| POST | `/api/complaints` | Submit a complaint, returns the generated ticket |
| GET | `/api/complaints?search=&status=&category=&limit=` | The employee's own complaints, filtered |
| GET | `/api/complaints/{ticket_id}` | Full details with status history |
| GET | `/api/complaints/track/{ticket_id}` | Public status lookup by ticket ID |
| PUT | `/api/complaints/{ticket_id}/assign` | Assign an engineer (role `admin`) |
| PUT | `/api/complaints/{ticket_id}/status` | Change status and record resolution remarks (role `admin`) |

Every assignment and status change writes a `complaint_history` row, which is what the
timeline on the complaint details page renders.

Tickets are issued as `IT-<year>-<4-digit sequence>`, e.g. `IT-2026-0150`, continuing from the
highest ticket of the current year.

## Test login accounts

Inserted on the first start.

| Employee ID | Password | Role | Who |
|---|---|---|---|
| `EMP1024` | `demo123` | employee | Rakesh Kumar Sinha — owns the four sample complaints |
| `ITADMIN` | `admin123` | admin | IT Cell Administrator |
| `EMP2048` | `test123` | employee | Sunita Devi |
| `EMP3301` | `test123` | employee | Manoj Kumar Verma |
| `ITENG01` | `admin123` | admin | Anjali Mishra |

Manage accounts with `manage_users.py`:

```bash
python manage_users.py seed            # insert the accounts above (skips existing ones)
python manage_users.py list            # show the accounts currently in the database
python manage_users.py reset-password EMP1024 newpassword
python manage_users.py add EMP5001 "Priya Kumari" priya@bsphcl.example.in secret123 \
    --designation "Executive Engineer" --department "Project Cell" --role employee
```

## Security notes

* **Row Level Security is enabled** on all three tables with no policies attached. Supabase
  publishes every `public`-schema table through PostgREST and the anon key is public by
  design, so without RLS anyone could read the whole `employees` table — bcrypt password
  hashes included. With RLS on and no policies, PostgREST returns nothing, while this backend
  keeps full access because it connects as the table owner, which bypasses RLS.
* `.env` holds the database password and is gitignored; `.env.example` ships placeholders only.
* Set a strong `SECRET_KEY` in production — it signs every JWT.

## Notes

This is a demo portal with fictional data and is not connected to any real BSPHCL system.
