-- BSPHCL IT Helpdesk - schema and test login accounts for Supabase (PostgreSQL).
-- Paste into the Supabase SQL editor, or:  psql "$DATABASE_URL" -f seed_users.sql
--
-- The backend creates the tables automatically on startup; this file is for
-- setting the database up by hand or re-adding the test logins. Safe to re-run.

-- Enum types -------------------------------------------------------------
DO $$ BEGIN
  CREATE TYPE complaint_category AS ENUM ('Hardware', 'Software', 'Network', 'Printer', 'Other');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  CREATE TYPE complaint_priority AS ENUM ('Low', 'Medium', 'High', 'Critical');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;
DO $$ BEGIN
  CREATE TYPE complaint_status AS ENUM ('Pending', 'Assigned', 'In Progress', 'Resolved');
EXCEPTION WHEN duplicate_object THEN NULL;
END $$;

-- Tables ------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS employees (
	id SERIAL NOT NULL, 
	employee_id VARCHAR(20) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	email VARCHAR(160) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	designation VARCHAR(100) NOT NULL, 
	department VARCHAR(100) NOT NULL, 
	office_location VARCHAR(120) NOT NULL, 
	role VARCHAR(20) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX IF NOT EXISTS ix_employees_email ON employees (email);
CREATE UNIQUE INDEX IF NOT EXISTS ix_employees_employee_id ON employees (employee_id);

CREATE TABLE IF NOT EXISTS complaints (
	id SERIAL NOT NULL, 
	ticket_id VARCHAR(20) NOT NULL, 
	employee_id INTEGER NOT NULL, 
	subject VARCHAR(200) NOT NULL, 
	description TEXT NOT NULL, 
	category complaint_category NOT NULL, 
	priority complaint_priority NOT NULL, 
	status complaint_status NOT NULL, 
	asset_tag VARCHAR(60), 
	contact_extension VARCHAR(30), 
	attachment_name VARCHAR(255), 
	assigned_engineer VARCHAR(120), 
	resolution_remarks TEXT, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	resolved_at TIMESTAMP WITHOUT TIME ZONE, 
	PRIMARY KEY (id), 
	FOREIGN KEY(employee_id) REFERENCES employees (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_complaints_employee_id ON complaints (employee_id);
CREATE INDEX IF NOT EXISTS ix_complaints_status ON complaints (status);
CREATE UNIQUE INDEX IF NOT EXISTS ix_complaints_ticket_id ON complaints (ticket_id);

CREATE TABLE IF NOT EXISTS complaint_history (
	id SERIAL NOT NULL, 
	complaint_id INTEGER NOT NULL, 
	previous_status VARCHAR(30), 
	new_status VARCHAR(30) NOT NULL, 
	remarks TEXT, 
	updated_by VARCHAR(120) NOT NULL, 
	created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now() NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(complaint_id) REFERENCES complaints (id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_complaint_history_complaint_id ON complaint_history (complaint_id);

-- Test login accounts ------------------------------------------------------
--   EMPLOYEE ID  PASSWORD   ROLE      NAME
--   EMP1024      demo123    employee  Rakesh Kumar Sinha
--   ITADMIN      admin123   admin     IT Cell Administrator
--   EMP2048      test123    employee  Sunita Devi
--   EMP3301      test123    employee  Manoj Kumar Verma
--   ITENG01      admin123   admin     Anjali Mishra

INSERT INTO employees
  (employee_id, full_name, email, password_hash, designation, department, office_location, role)
VALUES
  ('EMP1024', 'Rakesh Kumar Sinha', 'rakesh.sinha@bsphcl.example.in',
   '$2b$12$SlFLKHwRklfbt5dWDNenlOuOS6irDmzjtFZlgSIArjAacJnhg1zOW',
   'Assistant Engineer', 'Revenue & Billing', 'Head Office, Patna', 'employee'),
  ('ITADMIN', 'IT Cell Administrator', 'itcell@bsphcl.example.in',
   '$2b$12$8Dg95ecXkb346uKeiIqVxe3.sH8rix7KppSj2ipszF2bIjW8trIU2',
   'System Administrator', 'IT Cell', 'Head Office, Patna', 'admin'),
  ('EMP2048', 'Sunita Devi', 'sunita.devi@bsphcl.example.in',
   '$2b$12$PW4Qgjx3S5rDDOi2PFASLOzUzbGeyBBvECiyiksIHlp6Yvu9iReYq',
   'Junior Engineer', 'Transmission', 'Zonal Office, Muzaffarpur', 'employee'),
  ('EMP3301', 'Manoj Kumar Verma', 'manoj.verma@bsphcl.example.in',
   '$2b$12$qumA73cNjpHL3vdEhwYfCeLyumRlaAhrcDHPHRz4DTRgs02i4Obpy',
   'Accounts Officer', 'Finance & Accounts', 'Head Office, Patna', 'employee'),
  ('ITENG01', 'Anjali Mishra', 'anjali.mishra@bsphcl.example.in',
   '$2b$12$t.pmFYmF2g2vNIW0cniaDuPVN3l8iXB31ooznWxFJB7O1yPRnCkg2',
   'IT Engineer', 'IT Cell', 'Head Office, Patna', 'admin')
ON CONFLICT (employee_id) DO UPDATE SET password_hash = EXCLUDED.password_hash;

SELECT employee_id, full_name, designation, department, role FROM employees ORDER BY id;
