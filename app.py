"""
app.py - Main Flask application for the Job Application Tracker.

Pages:
    /              Dashboard (statistics overview)
    /companies     Companies   - list / view / add / edit / delete
    /jobs          Jobs        - list / view / add / edit / delete
    /applications  Applications - list / view / add / edit / delete
    /contacts      Contacts    - list / view / add / edit / delete
    /job-match     Job Match   - rank jobs by how many required skills you have
"""

import json
import os
import re
from datetime import date, datetime

from flask import Flask, abort, flash, redirect, render_template, request, url_for

from database import execute, parse_json, query_all, query_one

app = Flask(__name__)
# Needed for flash() messages. Change it (or set SECRET_KEY) for a real deployment.
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# Allowed values - these match the ENUM columns in schema.sql
JOB_TYPES = ["Full-time", "Part-time", "Contract", "Internship"]
STATUSES = ["Applied", "Screening", "Interview", "Offer", "Rejected", "Withdrawn"]
INTERVIEW_TYPES = ["Phone", "Video", "Onsite", "Technical", "Other"]

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


# =====================================================
# Small helper functions
# =====================================================

def clean(value):
    """Strip spaces from a form value and turn empty strings into None (NULL)."""
    if value is None:
        return None
    value = value.strip()
    return value if value else None


def check_length(errors, label, value, max_len):
    if value and len(value) > max_len:
        errors.append(f"{label} must be {max_len} characters or fewer.")


def to_int(errors, label, value):
    """Convert a form value to a whole number, adding an error if it isn't one."""
    if value is None:
        return None
    try:
        number = int(value.replace(",", ""))
    except ValueError:
        errors.append(f"{label} must be a whole number.")
        return None
    if number < 0:
        errors.append(f"{label} cannot be negative.")
    return number


def to_date(errors, label, value, required=False):
    """Check a YYYY-MM-DD date from an <input type="date">."""
    if value is None:
        if required:
            errors.append(f"{label} is required.")
        return None
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        errors.append(f"{label} must be a valid date (YYYY-MM-DD).")
        return None
    return value


def check_url(errors, label, value, max_len):
    check_length(errors, label, value, max_len)
    if value and not value.lower().startswith(("http://", "https://", "www.")):
        errors.append(f"{label} should start with http://, https:// or www.")


def parse_skills(text):
    """Turn 'Python, SQL , flask' into ['Python', 'SQL', 'flask'] (no blanks, no duplicates)."""
    skills = []
    seen = set()
    for part in (text or "").split(","):
        skill = part.strip()
        if skill and skill.lower() not in seen:
            seen.add(skill.lower())
            skills.append(skill)
    return skills


def company_choices():
    return query_all("SELECT company_id, company_name FROM companies ORDER BY company_name")


def job_choices():
    return query_all(
        """SELECT j.job_id, j.job_title, c.company_name
           FROM jobs j LEFT JOIN companies c ON j.company_id = c.company_id
           ORDER BY c.company_name, j.job_title"""
    )


@app.template_filter("money")
def money(value):
    """Format 70000 as $70,000 in templates."""
    if value is None:
        return "—"
    return f"${int(value):,}"


@app.template_filter("datefmt")
def datefmt(value):
    """Show dates as 'Jan 15, 2025'."""
    if value is None or value == "":
        return "—"
    if isinstance(value, str):
        try:
            value = datetime.strptime(value[:10], "%Y-%m-%d").date()
        except ValueError:
            return value
    if isinstance(value, (date, datetime)):
        return value.strftime("%b %d, %Y").replace(" 0", " ")
    return str(value)


@app.context_processor
def inject_globals():
    return {"STATUSES": STATUSES, "JOB_TYPES": JOB_TYPES, "INTERVIEW_TYPES": INTERVIEW_TYPES}


# =====================================================
# Dashboard
# =====================================================

@app.route("/")
def dashboard():
    counts = {
        "companies": query_one("SELECT COUNT(*) AS n FROM companies")["n"],
        "jobs": query_one("SELECT COUNT(*) AS n FROM jobs")["n"],
        "applications": query_one("SELECT COUNT(*) AS n FROM applications")["n"],
        "contacts": query_one("SELECT COUNT(*) AS n FROM contacts")["n"],
    }

    # Applications per status (show every status, even ones with 0)
    rows = query_all("SELECT status, COUNT(*) AS n FROM applications GROUP BY status")
    by_status = {status: 0 for status in STATUSES}
    for row in rows:
        if row["status"] in by_status:
            by_status[row["status"]] = row["n"]

    total = counts["applications"]
    # "Response rate" = applications that got past 'Applied' (excluding ones I withdrew)
    responded = by_status["Screening"] + by_status["Interview"] + by_status["Offer"] + by_status["Rejected"]
    response_rate = round(responded / total * 100) if total else 0

    salary = query_one("SELECT AVG(salary_min) AS avg_min, AVG(salary_max) AS avg_max FROM jobs")

    recent = query_all(
        """SELECT a.application_id, a.application_date, a.status,
                  j.job_title, c.company_name
           FROM applications a
           LEFT JOIN jobs j ON a.job_id = j.job_id
           LEFT JOIN companies c ON j.company_id = c.company_id
           ORDER BY a.application_date DESC, a.application_id DESC
           LIMIT 5"""
    )

    return render_template(
        "dashboard.html",
        counts=counts,
        by_status=by_status,
        response_rate=response_rate,
        salary=salary,
        recent=recent,
    )


# =====================================================
# Companies
# =====================================================

def read_company_form():
    form = {
        "company_name": clean(request.form.get("company_name")),
        "industry": clean(request.form.get("industry")),
        "website": clean(request.form.get("website")),
        "city": clean(request.form.get("city")),
        "state": clean(request.form.get("state")),
        "notes": clean(request.form.get("notes")),
    }
    errors = []
    if not form["company_name"]:
        errors.append("Company name is required.")
    check_length(errors, "Company name", form["company_name"], 100)
    check_length(errors, "Industry", form["industry"], 50)
    check_url(errors, "Website", form["website"], 200)
    check_length(errors, "City", form["city"], 50)
    check_length(errors, "State", form["state"], 50)
    return form, errors


@app.route("/companies")
def companies():
    search = clean(request.args.get("q"))
    sql = """SELECT c.*,
                    (SELECT COUNT(*) FROM jobs j WHERE j.company_id = c.company_id) AS job_count,
                    (SELECT COUNT(*) FROM contacts ct WHERE ct.company_id = c.company_id) AS contact_count
             FROM companies c"""
    params = ()
    if search:
        sql += " WHERE c.company_name LIKE %s OR c.industry LIKE %s OR c.city LIKE %s"
        like = f"%{search}%"
        params = (like, like, like)
    sql += " ORDER BY c.company_name"
    return render_template("companies.html", companies=query_all(sql, params), search=search or "")


@app.route("/companies/<int:company_id>")
def company_detail(company_id):
    company = query_one("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    if company is None:
        abort(404)
    jobs = query_all(
        "SELECT * FROM jobs WHERE company_id = %s ORDER BY date_posted DESC", (company_id,)
    )
    contacts = query_all(
        "SELECT * FROM contacts WHERE company_id = %s ORDER BY contact_name", (company_id,)
    )
    return render_template("company_detail.html", company=company, jobs=jobs, contacts=contacts)


@app.route("/companies/add", methods=["GET", "POST"])
def company_add():
    form = {}
    if request.method == "POST":
        form, errors = read_company_form()
        if not errors:
            new_id = execute(
                """INSERT INTO companies (company_name, industry, website, city, state, notes)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (form["company_name"], form["industry"], form["website"],
                 form["city"], form["state"], form["notes"]),
            )
            flash(f"Added company '{form['company_name']}'.", "success")
            return redirect(url_for("company_detail", company_id=new_id))
        for error in errors:
            flash(error, "danger")
    return render_template("company_form.html", form=form, mode="Add")


@app.route("/companies/<int:company_id>/edit", methods=["GET", "POST"])
def company_edit(company_id):
    company = query_one("SELECT * FROM companies WHERE company_id = %s", (company_id,))
    if company is None:
        abort(404)
    form = company
    if request.method == "POST":
        form, errors = read_company_form()
        if not errors:
            execute(
                """UPDATE companies
                   SET company_name = %s, industry = %s, website = %s, city = %s, state = %s, notes = %s
                   WHERE company_id = %s""",
                (form["company_name"], form["industry"], form["website"],
                 form["city"], form["state"], form["notes"], company_id),
            )
            flash(f"Updated company '{form['company_name']}'.", "success")
            return redirect(url_for("company_detail", company_id=company_id))
        for error in errors:
            flash(error, "danger")
    return render_template("company_form.html", form=form, mode="Edit", company_id=company_id)


@app.route("/companies/<int:company_id>/delete", methods=["POST"])
def company_delete(company_id):
    company = query_one("SELECT company_name FROM companies WHERE company_id = %s", (company_id,))
    if company is None:
        abort(404)
    # ON DELETE CASCADE in schema.sql also removes this company's jobs, applications and contacts
    execute("DELETE FROM companies WHERE company_id = %s", (company_id,))
    flash(f"Deleted company '{company['company_name']}' and its related records.", "success")
    return redirect(url_for("companies"))


# =====================================================
# Jobs
# =====================================================

def read_job_form():
    raw = {key: clean(request.form.get(key)) for key in
           ["company_id", "job_title", "job_type", "salary_min", "salary_max",
            "job_url", "date_posted", "requirements"]}
    errors = []

    company_id = to_int(errors, "Company", raw["company_id"])
    if company_id is None and not errors:
        errors.append("Please choose a company.")
    elif company_id is not None and not query_one(
            "SELECT company_id FROM companies WHERE company_id = %s", (company_id,)):
        errors.append("That company does not exist.")

    if not raw["job_title"]:
        errors.append("Job title is required.")
    check_length(errors, "Job title", raw["job_title"], 100)

    if raw["job_type"] and raw["job_type"] not in JOB_TYPES:
        errors.append("Job type must be one of: " + ", ".join(JOB_TYPES) + ".")

    salary_min = to_int(errors, "Minimum salary", raw["salary_min"])
    salary_max = to_int(errors, "Maximum salary", raw["salary_max"])
    if salary_min is not None and salary_max is not None and salary_min > salary_max:
        errors.append("Minimum salary cannot be higher than maximum salary.")

    check_url(errors, "Job URL", raw["job_url"], 300)
    date_posted = to_date(errors, "Date posted", raw["date_posted"])
    skills = parse_skills(raw["requirements"])

    form = dict(raw)  # keeps what the user typed, so the form can be shown again on errors
    values = {
        "company_id": company_id,
        "job_title": raw["job_title"],
        "job_type": raw["job_type"],
        "salary_min": salary_min,
        "salary_max": salary_max,
        "job_url": raw["job_url"],
        "date_posted": date_posted,
        # Stored in the JSON column as a list, e.g. ["Python", "SQL"]
        "requirements": json.dumps(skills) if skills else None,
    }
    return form, values, errors


@app.route("/jobs")
def jobs():
    search = clean(request.args.get("q"))
    job_type = clean(request.args.get("type"))
    sql = """SELECT j.*, c.company_name,
                    (SELECT COUNT(*) FROM applications a WHERE a.job_id = j.job_id) AS app_count
             FROM jobs j LEFT JOIN companies c ON j.company_id = c.company_id
             WHERE 1 = 1"""
    params = []
    if search:
        sql += " AND (j.job_title LIKE %s OR c.company_name LIKE %s)"
        params += [f"%{search}%", f"%{search}%"]
    if job_type in JOB_TYPES:
        sql += " AND j.job_type = %s"
        params.append(job_type)
    sql += " ORDER BY j.date_posted DESC, j.job_id DESC"
    rows = query_all(sql, tuple(params))
    for row in rows:
        row["skills"] = parse_json(row.get("requirements")) or []
    return render_template("jobs.html", jobs=rows, search=search or "", job_type=job_type or "")


@app.route("/jobs/<int:job_id>")
def job_detail(job_id):
    job = query_one(
        """SELECT j.*, c.company_name FROM jobs j
           LEFT JOIN companies c ON j.company_id = c.company_id
           WHERE j.job_id = %s""", (job_id,))
    if job is None:
        abort(404)
    job["skills"] = parse_json(job.get("requirements")) or []
    applications = query_all(
        "SELECT * FROM applications WHERE job_id = %s ORDER BY application_date DESC", (job_id,))
    return render_template("job_detail.html", job=job, applications=applications)


@app.route("/jobs/add", methods=["GET", "POST"])
def job_add():
    form = {"company_id": request.args.get("company_id", "")}
    if request.method == "POST":
        form, values, errors = read_job_form()
        if not errors:
            new_id = execute(
                """INSERT INTO jobs (company_id, job_title, job_type, salary_min, salary_max,
                                     job_url, date_posted, requirements)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                (values["company_id"], values["job_title"], values["job_type"], values["salary_min"],
                 values["salary_max"], values["job_url"], values["date_posted"], values["requirements"]),
            )
            flash(f"Added job '{values['job_title']}'.", "success")
            return redirect(url_for("job_detail", job_id=new_id))
        for error in errors:
            flash(error, "danger")
    return render_template("job_form.html", form=form, mode="Add", companies=company_choices())


@app.route("/jobs/<int:job_id>/edit", methods=["GET", "POST"])
def job_edit(job_id):
    job = query_one("SELECT * FROM jobs WHERE job_id = %s", (job_id,))
    if job is None:
        abort(404)
    form = dict(job)
    form["requirements"] = ", ".join(parse_json(job.get("requirements")) or [])
    form["date_posted"] = job["date_posted"].isoformat() if job.get("date_posted") and hasattr(
        job["date_posted"], "isoformat") else (job.get("date_posted") or "")
    if request.method == "POST":
        form, values, errors = read_job_form()
        if not errors:
            execute(
                """UPDATE jobs
                   SET company_id = %s, job_title = %s, job_type = %s, salary_min = %s, salary_max = %s,
                       job_url = %s, date_posted = %s, requirements = %s
                   WHERE job_id = %s""",
                (values["company_id"], values["job_title"], values["job_type"], values["salary_min"],
                 values["salary_max"], values["job_url"], values["date_posted"], values["requirements"],
                 job_id),
            )
            flash(f"Updated job '{values['job_title']}'.", "success")
            return redirect(url_for("job_detail", job_id=job_id))
        for error in errors:
            flash(error, "danger")
    return render_template("job_form.html", form=form, mode="Edit", job_id=job_id,
                           companies=company_choices())


@app.route("/jobs/<int:job_id>/delete", methods=["POST"])
def job_delete(job_id):
    job = query_one("SELECT job_title FROM jobs WHERE job_id = %s", (job_id,))
    if job is None:
        abort(404)
    execute("DELETE FROM jobs WHERE job_id = %s", (job_id,))
    flash(f"Deleted job '{job['job_title']}' and its applications.", "success")
    return redirect(url_for("jobs"))


# =====================================================
# Applications
# =====================================================

def read_application_form():
    raw = {key: clean(request.form.get(key)) for key in
           ["job_id", "application_date", "status", "resume_version",
            "interview_round", "interview_type", "interview_date", "interviewer", "interview_notes"]}
    raw["cover_letter_sent"] = request.form.get("cover_letter_sent") == "on"
    errors = []

    job_id = to_int(errors, "Job", raw["job_id"])
    if job_id is None and not errors:
        errors.append("Please choose a job.")
    elif job_id is not None and not query_one("SELECT job_id FROM jobs WHERE job_id = %s", (job_id,)):
        errors.append("That job does not exist.")

    application_date = to_date(errors, "Application date", raw["application_date"], required=True)

    status = raw["status"] or "Applied"
    if status not in STATUSES:
        errors.append("Status must be one of: " + ", ".join(STATUSES) + ".")

    check_length(errors, "Resume version", raw["resume_version"], 50)

    # Interview details are stored together in the interview_data JSON column
    interview = {}
    if raw["interview_round"]:
        round_number = to_int(errors, "Interview round", raw["interview_round"])
        if round_number is not None:
            interview["round"] = round_number
    if raw["interview_type"]:
        if raw["interview_type"] not in INTERVIEW_TYPES:
            errors.append("Interview type must be one of: " + ", ".join(INTERVIEW_TYPES) + ".")
        interview["type"] = raw["interview_type"]
    if raw["interview_date"]:
        if to_date(errors, "Interview date", raw["interview_date"]):
            interview["date"] = raw["interview_date"]
    if raw["interviewer"]:
        interview["interviewer"] = raw["interviewer"]
    if raw["interview_notes"]:
        interview["notes"] = raw["interview_notes"]

    values = {
        "job_id": job_id,
        "application_date": application_date,
        "status": status,
        "resume_version": raw["resume_version"],
        "cover_letter_sent": raw["cover_letter_sent"],
        "interview_data": json.dumps(interview) if interview else None,
    }
    return raw, values, errors


@app.route("/applications")
def applications():
    status = clean(request.args.get("status"))
    sql = """SELECT a.*, j.job_title, c.company_name
             FROM applications a
             LEFT JOIN jobs j ON a.job_id = j.job_id
             LEFT JOIN companies c ON j.company_id = c.company_id"""
    params = ()
    if status in STATUSES:
        sql += " WHERE a.status = %s"
        params = (status,)
    sql += " ORDER BY a.application_date DESC, a.application_id DESC"
    rows = query_all(sql, params)
    for row in rows:
        row["interview"] = parse_json(row.get("interview_data")) or {}
    return render_template("applications.html", applications=rows, status=status or "")


@app.route("/applications/<int:application_id>")
def application_detail(application_id):
    app_row = query_one(
        """SELECT a.*, j.job_title, j.company_id, c.company_name
           FROM applications a
           LEFT JOIN jobs j ON a.job_id = j.job_id
           LEFT JOIN companies c ON j.company_id = c.company_id
           WHERE a.application_id = %s""", (application_id,))
    if app_row is None:
        abort(404)
    app_row["interview"] = parse_json(app_row.get("interview_data")) or {}
    return render_template("application_detail.html", application=app_row)


def application_to_form(row):
    """Flatten an application row (including its JSON) into form field values."""
    interview = parse_json(row.get("interview_data")) or {}
    app_date = row.get("application_date")
    return {
        "job_id": row.get("job_id"),
        "application_date": app_date.isoformat() if hasattr(app_date, "isoformat") else (app_date or ""),
        "status": row.get("status"),
        "resume_version": row.get("resume_version"),
        "cover_letter_sent": bool(row.get("cover_letter_sent")),
        "interview_round": interview.get("round", ""),
        "interview_type": interview.get("type", ""),
        "interview_date": interview.get("date", ""),
        "interviewer": interview.get("interviewer", ""),
        "interview_notes": interview.get("notes", ""),
    }


@app.route("/applications/add", methods=["GET", "POST"])
def application_add():
    form = {
        "job_id": request.args.get("job_id", ""),
        "application_date": date.today().isoformat(),
        "status": "Applied",
    }
    if request.method == "POST":
        form, values, errors = read_application_form()
        if not errors:
            new_id = execute(
                """INSERT INTO applications (job_id, application_date, status, resume_version,
                                             cover_letter_sent, interview_data)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (values["job_id"], values["application_date"], values["status"],
                 values["resume_version"], values["cover_letter_sent"], values["interview_data"]),
            )
            flash("Added application.", "success")
            return redirect(url_for("application_detail", application_id=new_id))
        for error in errors:
            flash(error, "danger")
    return render_template("application_form.html", form=form, mode="Add", jobs=job_choices())


@app.route("/applications/<int:application_id>/edit", methods=["GET", "POST"])
def application_edit(application_id):
    row = query_one("SELECT * FROM applications WHERE application_id = %s", (application_id,))
    if row is None:
        abort(404)
    form = application_to_form(row)
    if request.method == "POST":
        form, values, errors = read_application_form()
        if not errors:
            execute(
                """UPDATE applications
                   SET job_id = %s, application_date = %s, status = %s, resume_version = %s,
                       cover_letter_sent = %s, interview_data = %s
                   WHERE application_id = %s""",
                (values["job_id"], values["application_date"], values["status"],
                 values["resume_version"], values["cover_letter_sent"], values["interview_data"],
                 application_id),
            )
            flash("Updated application.", "success")
            return redirect(url_for("application_detail", application_id=application_id))
        for error in errors:
            flash(error, "danger")
    return render_template("application_form.html", form=form, mode="Edit",
                           application_id=application_id, jobs=job_choices())


@app.route("/applications/<int:application_id>/delete", methods=["POST"])
def application_delete(application_id):
    if query_one("SELECT application_id FROM applications WHERE application_id = %s",
                 (application_id,)) is None:
        abort(404)
    execute("DELETE FROM applications WHERE application_id = %s", (application_id,))
    flash("Deleted application.", "success")
    return redirect(url_for("applications"))


# =====================================================
# Contacts
# =====================================================

def read_contact_form():
    raw = {key: clean(request.form.get(key)) for key in
           ["company_id", "contact_name", "title", "email", "phone", "linkedin_url", "notes"]}
    errors = []

    company_id = to_int(errors, "Company", raw["company_id"])
    if company_id is None and not errors:
        errors.append("Please choose a company.")
    elif company_id is not None and not query_one(
            "SELECT company_id FROM companies WHERE company_id = %s", (company_id,)):
        errors.append("That company does not exist.")

    if not raw["contact_name"]:
        errors.append("Contact name is required.")
    check_length(errors, "Contact name", raw["contact_name"], 100)
    check_length(errors, "Title", raw["title"], 100)
    check_length(errors, "Email", raw["email"], 100)
    if raw["email"] and not EMAIL_PATTERN.match(raw["email"]):
        errors.append("Email address doesn't look valid (example: name@company.com).")
    check_length(errors, "Phone", raw["phone"], 20)
    if raw["phone"] and not re.fullmatch(r"[0-9()+\-.\s]+", raw["phone"]):
        errors.append("Phone can only contain numbers, spaces and ( ) + - .")
    check_url(errors, "LinkedIn URL", raw["linkedin_url"], 200)

    values = dict(raw)
    values["company_id"] = company_id
    return raw, values, errors


@app.route("/contacts")
def contacts():
    search = clean(request.args.get("q"))
    sql = """SELECT ct.*, c.company_name
             FROM contacts ct LEFT JOIN companies c ON ct.company_id = c.company_id"""
    params = ()
    if search:
        sql += " WHERE ct.contact_name LIKE %s OR c.company_name LIKE %s OR ct.title LIKE %s"
        like = f"%{search}%"
        params = (like, like, like)
    sql += " ORDER BY ct.contact_name"
    return render_template("contacts.html", contacts=query_all(sql, params), search=search or "")


@app.route("/contacts/<int:contact_id>")
def contact_detail(contact_id):
    contact = query_one(
        """SELECT ct.*, c.company_name FROM contacts ct
           LEFT JOIN companies c ON ct.company_id = c.company_id
           WHERE ct.contact_id = %s""", (contact_id,))
    if contact is None:
        abort(404)
    return render_template("contact_detail.html", contact=contact)


@app.route("/contacts/add", methods=["GET", "POST"])
def contact_add():
    form = {"company_id": request.args.get("company_id", "")}
    if request.method == "POST":
        form, values, errors = read_contact_form()
        if not errors:
            new_id = execute(
                """INSERT INTO contacts (company_id, contact_name, title, email, phone, linkedin_url, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (values["company_id"], values["contact_name"], values["title"], values["email"],
                 values["phone"], values["linkedin_url"], values["notes"]),
            )
            flash(f"Added contact '{values['contact_name']}'.", "success")
            return redirect(url_for("contact_detail", contact_id=new_id))
        for error in errors:
            flash(error, "danger")
    return render_template("contact_form.html", form=form, mode="Add", companies=company_choices())


@app.route("/contacts/<int:contact_id>/edit", methods=["GET", "POST"])
def contact_edit(contact_id):
    contact = query_one("SELECT * FROM contacts WHERE contact_id = %s", (contact_id,))
    if contact is None:
        abort(404)
    form = contact
    if request.method == "POST":
        form, values, errors = read_contact_form()
        if not errors:
            execute(
                """UPDATE contacts
                   SET company_id = %s, contact_name = %s, title = %s, email = %s, phone = %s,
                       linkedin_url = %s, notes = %s
                   WHERE contact_id = %s""",
                (values["company_id"], values["contact_name"], values["title"], values["email"],
                 values["phone"], values["linkedin_url"], values["notes"], contact_id),
            )
            flash(f"Updated contact '{values['contact_name']}'.", "success")
            return redirect(url_for("contact_detail", contact_id=contact_id))
        for error in errors:
            flash(error, "danger")
    return render_template("contact_form.html", form=form, mode="Edit", contact_id=contact_id,
                           companies=company_choices())


@app.route("/contacts/<int:contact_id>/delete", methods=["POST"])
def contact_delete(contact_id):
    contact = query_one("SELECT contact_name FROM contacts WHERE contact_id = %s", (contact_id,))
    if contact is None:
        abort(404)
    execute("DELETE FROM contacts WHERE contact_id = %s", (contact_id,))
    flash(f"Deleted contact '{contact['contact_name']}'.", "success")
    return redirect(url_for("contacts"))


# =====================================================
# Job Match
# =====================================================

def match_jobs(user_skills, jobs_list):
    """Rank jobs by the percentage of their required skills that the user has.

    Example: a job requires Python, SQL, Tableau and the user has Python, SQL
    -> 2 of 3 required skills -> 67%, missing: Tableau.
    Matching ignores upper/lower case.
    """
    have = {skill.lower() for skill in user_skills}
    results = []
    for job in jobs_list:
        required = parse_json(job.get("requirements")) or []
        if not required:
            continue  # can't score a job that lists no requirements
        matched = [skill for skill in required if skill.lower() in have]
        missing = [skill for skill in required if skill.lower() not in have]
        if not matched:
            continue  # only show jobs where at least one skill matches
        percent = round(len(matched) / len(required) * 100)
        results.append({
            "job": job,
            "matched": matched,
            "missing": missing,
            "required_count": len(required),
            "percent": percent,
        })
    # Highest percentage first; ties go to the job with more matching skills
    results.sort(key=lambda r: (r["percent"], len(r["matched"])), reverse=True)
    return results


@app.route("/job-match")
def job_match():
    skills_text = request.args.get("skills", "")
    user_skills = parse_skills(skills_text)
    results = None
    if skills_text.strip():
        jobs_list = query_all(
            """SELECT j.job_id, j.job_title, j.job_type, j.salary_min, j.salary_max,
                      j.requirements, c.company_name
               FROM jobs j LEFT JOIN companies c ON j.company_id = c.company_id"""
        )
        results = match_jobs(user_skills, jobs_list)

    # Every skill that appears in any job, to show as clickable suggestions
    all_skills = set()
    for row in query_all("SELECT requirements FROM jobs"):
        for skill in parse_json(row.get("requirements")) or []:
            all_skills.add(skill)

    return render_template(
        "job_match.html",
        skills_text=skills_text,
        user_skills=user_skills,
        results=results,
        all_skills=sorted(all_skills, key=str.lower),
    )


# =====================================================
# Errors
# =====================================================

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    app.run(debug=True)
