# Job Application Tracker

A web application to help track job applications during the job search process — COP4751 Course Project.

Built with **MySQL**, **Python 3 / Flask**, and **HTML/CSS (Bootstrap 5)**.

## Features

- **Dashboard** – totals for companies, jobs, applications and contacts; applications by status; response rate; recent applications; average salary range
- **Companies** – list, search, view details (with the company's jobs and contacts), add, edit, delete
- **Jobs** – list, search, filter by job type, view details, add, edit, delete; required skills stored in a `requirements` **JSON** column
- **Applications** – list, filter by status, view details, add, edit, delete; interview details stored in an `interview_data` **JSON** column
- **Contacts** – list, search, view details, add, edit, delete
- **Job Match** – enter your skills and see jobs ranked by the percentage of their required skills you have, with matched and missing skills
- **Validation** – required fields, length limits, salary min ≤ max, valid dates, email and URL format checks
- **Delete confirmation** – every delete asks for confirmation first; deleting a company also deletes its jobs, applications and contacts (`ON DELETE CASCADE`)

## Database

Four tables with foreign keys:

```
companies ──< jobs ──< applications
    │
    └──< contacts
```

| Table | Key columns |
|---|---|
| `companies` | `company_id` (PK), `company_name`, `industry`, `website`, `city`, `state`, `notes` |
| `jobs` | `job_id` (PK), `company_id` (FK), `job_title`, `job_type` (ENUM), `salary_min`, `salary_max`, `job_url`, `date_posted`, `requirements` (JSON) |
| `applications` | `application_id` (PK), `job_id` (FK), `application_date`, `status` (ENUM), `resume_version`, `cover_letter_sent`, `interview_data` (JSON) |
| `contacts` | `contact_id` (PK), `company_id` (FK), `contact_name`, `title`, `email`, `phone`, `linkedin_url`, `notes` |

`schema.sql` creates the database, all four tables, and sample data.

## Setup

### 1. Requirements

- Python 3.9 or newer
- MySQL Server 8.0 or newer (and MySQL Workbench, optional)

### 2. Create the database

Open `schema.sql` in MySQL Workbench and run the whole script (**Execute All**), or from a terminal:

```bash
mysql -u root -p < schema.sql
```

> ⚠️ `schema.sql` drops and recreates the `job_tracker` database.

### 3. Install the Python packages

```bash
pip3 install -r requirements.txt
```

### 4. Set your MySQL password

The app reads its connection settings from environment variables, so no password is stored in the code:

macOS / Linux:
```bash
export DB_PASSWORD='your_mysql_password'
```

Windows (PowerShell):
```powershell
$env:DB_PASSWORD = "your_mysql_password"
```

Optional: `DB_HOST` (default `localhost`), `DB_USER` (default `root`), `DB_NAME` (default `job_tracker`).

### 5. Run the app

```bash
python3 app.py
```

Then open **http://127.0.0.1:5000** in a browser.

## Project structure

```
job-application-tracker/
├── app.py              # Flask routes: dashboard, CRUD for 4 tables, job match
├── database.py         # MySQL connection and query helpers
├── schema.sql          # Creates the database, tables and sample data
├── requirements.txt    # Python dependencies
├── templates/          # HTML templates (Jinja2)
│   ├── base.html           # Shared layout and navigation
│   ├── _macros.html        # Reusable pieces (status badge, delete button…)
│   ├── dashboard.html
│   ├── companies.html, company_detail.html, company_form.html
│   ├── jobs.html, job_detail.html, job_form.html
│   ├── applications.html, application_detail.html, application_form.html
│   ├── contacts.html, contact_detail.html, contact_form.html
│   ├── job_match.html
│   └── 404.html
├── static/
│   └── style.css
├── AI_USAGE.md         # How AI tools were used
└── README.md
```

## How Job Match works

Each job stores its required skills as a JSON array, e.g. `["Python", "SQL", "Tableau"]`.
For every job, the app counts how many of those required skills the user entered (ignoring upper/lower case):

```
match % = required skills the user has ÷ total required skills × 100
```

Jobs are sorted from highest to lowest match, and each result lists the skills the user has and the ones they are missing. Jobs with no matching skills are hidden.

Example with skills **Python, SQL, Flask**:

1. Software Developer at Tech Solutions Inc — 100% (3/3 skills)
2. Data Analyst at Data Analytics Corp — 67% (2/3 skills) — Missing: Tableau

## AI usage

See [AI_USAGE.md](AI_USAGE.md).

## Screenshots

<img width="468" height="197" alt="image" src="https://github.com/user-attachments/assets/9ea8dd9d-d413-4158-a89d-e68a4b942b9c" />
