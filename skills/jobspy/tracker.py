#!/usr/bin/env python3
"""
jobspy application tracker — records jobs you have applied to so they are
automatically filtered out of future searches.

Database: ~/.config/openclaw-jobspy/applications.db

Jobs are assigned a short numeric ID on creation. All commands that previously
required a full URL now accept either the numeric ID or the URL.

Usage:
    python tracker.py add <url> [options]
    python tracker.py show <id|url>
    python tracker.py list [--status <status>] [--company <name>]
    python tracker.py notes <id|url> <text>
    python tracker.py status <id|url> <new_status>
    python tracker.py remove <id|url>
"""

import argparse
import os
import sqlite3
import sys
import textwrap
from datetime import datetime

DB_PATH = os.path.expanduser("~/.config/openclaw-jobspy/applications.db")

VALID_STATUSES = ["applied", "interviewing", "offer", "rejected", "withdrawn"]

APPLICATION_METHODS = ["website", "easy_apply", "referral", "email", "other"]

# All columns in insertion order. Used for migration.
SCHEMA = """
    CREATE TABLE IF NOT EXISTS applications (
        id                  INTEGER PRIMARY KEY AUTOINCREMENT,

        -- Job posting fields (populated at add time)
        job_url             TEXT    UNIQUE NOT NULL,
        site                TEXT,
        title               TEXT,
        company             TEXT,
        company_url         TEXT,
        location            TEXT,
        is_remote           INTEGER,
        job_type            TEXT,
        job_function        TEXT,
        job_level           TEXT,
        company_industry    TEXT,
        date_posted         TEXT,
        min_amount          REAL,
        max_amount          REAL,
        salary_interval     TEXT,
        currency            TEXT,
        description         TEXT,
        emails              TEXT,

        -- Application tracking fields
        date_applied        TEXT    NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
        status              TEXT    NOT NULL DEFAULT 'applied',
        application_method  TEXT,
        follow_up_date      TEXT,
        interview_date      TEXT,
        offer_amount        REAL,
        notes               TEXT
    )
"""

# Columns added after initial release — for migration of existing DBs.
MIGRATION_COLUMNS = [
    ("site",                "TEXT"),
    ("company_url",         "TEXT"),
    ("is_remote",           "INTEGER"),
    ("job_type",            "TEXT"),
    ("job_function",        "TEXT"),
    ("job_level",           "TEXT"),
    ("company_industry",    "TEXT"),
    ("date_posted",         "TEXT"),
    ("min_amount",          "REAL"),
    ("max_amount",          "REAL"),
    ("salary_interval",     "TEXT"),
    ("currency",            "TEXT"),
    ("description",         "TEXT"),
    ("emails",              "TEXT"),
    ("application_method",  "TEXT"),
    ("follow_up_date",      "TEXT"),
    ("interview_date",      "TEXT"),
    ("offer_amount",        "REAL"),
    ("notes",               "TEXT"),
]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def open_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute(SCHEMA)
    conn.commit()
    _migrate(conn)
    return conn


def _migrate(conn):
    """Add any columns that don't exist yet (forward-only migration)."""
    existing = {row[1] for row in conn.execute("PRAGMA table_info(applications)")}
    for col_name, col_type in MIGRATION_COLUMNS:
        if col_name not in existing:
            conn.execute(f"ALTER TABLE applications ADD COLUMN {col_name} {col_type}")
    conn.commit()


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def fmt_salary(row):
    lo, hi, interval, currency = (
        row["min_amount"], row["max_amount"],
        row["salary_interval"], row["currency"],
    )
    if not lo and not hi:
        return ""
    cur = currency or ""
    interval_label = f"/{interval}" if interval else ""
    if lo and hi:
        return f"{cur}{int(lo):,}–{int(hi):,}{interval_label}"
    val = lo or hi
    return f"{cur}{int(val):,}{interval_label}"


def fmt_bool(val):
    if val is None:
        return ""
    return "yes" if val else "no"


def truncate(text, width):
    if not text:
        return ""
    text = str(text)
    return text if len(text) <= width else text[: width - 1] + "…"


# ---------------------------------------------------------------------------
# Entry resolver — accepts numeric ID or full URL
# ---------------------------------------------------------------------------

def resolve_entry(conn, ref):
    """Return the application row matching a numeric ID or a job URL.
    Exits with an error message if nothing is found.
    """
    if str(ref).lstrip("-").isdigit():
        row = conn.execute(
            "SELECT * FROM applications WHERE id = ?", (int(ref),)
        ).fetchone()
        if not row:
            print(f"No application with ID {ref}.", file=sys.stderr)
            sys.exit(1)
    else:
        row = conn.execute(
            "SELECT * FROM applications WHERE job_url = ?", (ref,)
        ).fetchone()
        if not row:
            print(f"URL not found in tracker: {ref}", file=sys.stderr)
            sys.exit(1)
    return row


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_add(args):
    conn = open_db()
    try:
        conn.execute(
            """
            INSERT INTO applications (
                job_url, site, title, company, company_url, location,
                is_remote, job_type, job_function, job_level, company_industry,
                date_posted, min_amount, max_amount, salary_interval, currency,
                description, emails,
                status, application_method, follow_up_date, interview_date,
                offer_amount, notes
            ) VALUES (
                :job_url, :site, :title, :company, :company_url, :location,
                :is_remote, :job_type, :job_function, :job_level, :company_industry,
                :date_posted, :min_amount, :max_amount, :salary_interval, :currency,
                :description, :emails,
                :status, :application_method, :follow_up_date, :interview_date,
                :offer_amount, :notes
            )
            """,
            {
                "job_url":            args.url,
                "site":               args.site,
                "title":              args.title,
                "company":            args.company,
                "company_url":        args.company_url,
                "location":           args.location,
                "is_remote":          (1 if args.remote else None),
                "job_type":           args.job_type,
                "job_function":       args.job_function,
                "job_level":          args.job_level,
                "company_industry":   args.company_industry,
                "date_posted":        args.date_posted,
                "min_amount":         args.min_amount,
                "max_amount":         args.max_amount,
                "salary_interval":    args.salary_interval,
                "currency":           args.currency,
                "description":        args.description,
                "emails":             args.emails,
                "status":             args.status,
                "application_method": args.application_method,
                "follow_up_date":     args.follow_up_date,
                "interview_date":     args.interview_date,
                "offer_amount":       args.offer_amount,
                "notes":              args.notes,
            },
        )
        row_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
        conn.commit()
        print(f"Added (ID {row_id}): {args.url}")
        parts = [p for p in [args.title, args.company, args.location] if p]
        if parts:
            print(f"       {' | '.join(parts)}")
        salary = fmt_salary({
            "min_amount": args.min_amount, "max_amount": args.max_amount,
            "salary_interval": args.salary_interval, "currency": args.currency,
        })
        if salary:
            print(f"       {salary}")
    except sqlite3.IntegrityError:
        print(f"Already tracked: {args.url}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_show(args):
    conn = open_db()
    row = resolve_entry(conn, args.ref)
    conn.close()

    fields = [
        ("ID",                  str(row["id"])),
        ("URL",                 row["job_url"]),
        ("Site",                row["site"]),
        ("Title",               row["title"]),
        ("Company",             row["company"]),
        ("Company URL",         row["company_url"]),
        ("Location",            row["location"]),
        ("Remote",              fmt_bool(row["is_remote"])),
        ("Job type",            row["job_type"]),
        ("Job function",        row["job_function"]),
        ("Job level",           row["job_level"]),
        ("Industry",            row["company_industry"]),
        ("Date posted",         row["date_posted"]),
        ("Salary",              fmt_salary(row)),
        ("Contact emails",      row["emails"]),
        ("Date applied",        (row["date_applied"] or "")[:10]),
        ("Status",              row["status"]),
        ("Applied via",         row["application_method"]),
        ("Follow-up date",      row["follow_up_date"]),
        ("Interview date",      row["interview_date"]),
        ("Offer amount",        f"{row['offer_amount']:,}" if row["offer_amount"] else ""),
        ("Notes",               row["notes"]),
    ]

    label_width = max(len(label) for label, _ in fields)
    print()
    for label, value in fields:
        if not value:
            continue
        if label == "Description":
            print(f"{'Description':<{label_width}}  (see below)")
        else:
            print(f"{label:<{label_width}}  {value}")

    if row["description"]:
        print()
        print("Description")
        print("-" * 60)
        print(textwrap.fill(row["description"], width=80))

    print()


def cmd_list(args):
    conn = open_db()
    query = "SELECT * FROM applications"
    conditions, params = [], []
    if args.status:
        conditions.append("status = ?")
        params.append(args.status)
    if args.company:
        conditions.append("company LIKE ?")
        params.append(f"%{args.company}%")
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date_applied DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        if args.status or args.company:
            filters = " + ".join(filter(None, [args.status, args.company and f'company~"{args.company}"']))
            print(f"No applications found matching: {filters}")
        else:
            print("No applications tracked yet.")
        return

    W = {"id": 4, "status": 11, "date": 10, "company": 18, "title": 28, "salary": 16, "site": 12}
    header = (
        f"{'ID':<{W['id']}} "
        f"{'Status':<{W['status']}} "
        f"{'Applied':<{W['date']}} "
        f"{'Company':<{W['company']}} "
        f"{'Title':<{W['title']}} "
        f"{'Salary':<{W['salary']}} "
        f"{'Site':<{W['site']}} "
        f"URL"
    )
    print(header)
    print("-" * len(header))

    for row in rows:
        date = (row["date_applied"] or "")[:10]
        salary = fmt_salary(row)
        print(
            f"{row['id']:<{W['id']}} "
            f"{truncate(row['status'], W['status']):<{W['status']}} "
            f"{date:<{W['date']}} "
            f"{truncate(row['company'], W['company']):<{W['company']}} "
            f"{truncate(row['title'], W['title']):<{W['title']}} "
            f"{truncate(salary, W['salary']):<{W['salary']}} "
            f"{truncate(row['site'], W['site']):<{W['site']}} "
            f"{row['job_url']}"
        )

    print(f"\n{len(rows)} application(s) total.")


def cmd_notes(args):
    conn = open_db()
    row = resolve_entry(conn, args.ref)

    timestamp = datetime.now().strftime("%Y-%m-%d")
    existing = row["notes"] or ""
    updated = f"{existing}\n[{timestamp}] {args.text}".strip()

    conn.execute(
        "UPDATE applications SET notes = ? WHERE id = ?",
        (updated, row["id"]),
    )
    conn.commit()
    conn.close()
    print(f"Notes updated for ID {row['id']}: {row['job_url']}")


def cmd_status(args):
    if args.new_status not in VALID_STATUSES:
        print(f"Invalid status '{args.new_status}'. Choose from: {', '.join(VALID_STATUSES)}", file=sys.stderr)
        sys.exit(1)
    conn = open_db()
    row = resolve_entry(conn, args.ref)
    conn.execute(
        "UPDATE applications SET status = ? WHERE id = ?",
        (args.new_status, row["id"]),
    )
    conn.commit()
    conn.close()
    print(f"ID {row['id']} status → '{args.new_status}': {row['job_url']}")


def cmd_remove(args):
    conn = open_db()
    row = resolve_entry(conn, args.ref)
    conn.execute("DELETE FROM applications WHERE id = ?", (row["id"],))
    conn.commit()
    conn.close()
    print(f"Removed ID {row['id']}: {row['job_url']}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Track job applications and filter them from future searches.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # -- add ------------------------------------------------------------------
    p_add = sub.add_parser("add", help="Record a job you have applied to")
    p_add.add_argument("url", help="Job posting URL")

    # Job posting fields
    grp_post = p_add.add_argument_group("job posting details")
    grp_post.add_argument("--site", help="Job board (indeed, linkedin, etc.)")
    grp_post.add_argument("--title", help="Job title")
    grp_post.add_argument("--company", help="Company name")
    grp_post.add_argument("--company-url", help="Company website URL")
    grp_post.add_argument("--location", help="Job location")
    grp_post.add_argument("--remote", action="store_true", help="Remote position")
    grp_post.add_argument("--job-type", choices=["fulltime", "parttime", "contract", "internship"])
    grp_post.add_argument("--job-function", help="Job function / category")
    grp_post.add_argument("--job-level", help="Seniority level (e.g. Mid-Senior, Entry)")
    grp_post.add_argument("--company-industry", help="Company industry")
    grp_post.add_argument("--date-posted", help="Date the job was originally posted (YYYY-MM-DD)")
    grp_post.add_argument("--min-amount", type=float, help="Minimum salary")
    grp_post.add_argument("--max-amount", type=float, help="Maximum salary")
    grp_post.add_argument("--salary-interval", help="Salary interval (yearly, hourly, etc.)")
    grp_post.add_argument("--currency", help="Salary currency (e.g. USD)")
    grp_post.add_argument("--description", help="Job description text")
    grp_post.add_argument("--emails", help="Contact email(s) from the posting")

    # Application tracking fields
    grp_app = p_add.add_argument_group("application tracking")
    grp_app.add_argument("--status", default="applied", choices=VALID_STATUSES)
    grp_app.add_argument("--application-method", choices=APPLICATION_METHODS, help="How you applied")
    grp_app.add_argument("--follow-up-date", help="Date to follow up (YYYY-MM-DD)")
    grp_app.add_argument("--interview-date", help="Scheduled interview date (YYYY-MM-DD)")
    grp_app.add_argument("--offer-amount", type=float, help="Offer amount if received")
    grp_app.add_argument("--notes", help="Free-text notes")

    # -- show -----------------------------------------------------------------
    p_show = sub.add_parser("show", help="Show all details for one application")
    p_show.add_argument("ref", help="Numeric ID (from 'list') or job posting URL")

    # -- list -----------------------------------------------------------------
    p_list = sub.add_parser("list", help="List tracked applications")
    p_list.add_argument("--status", choices=VALID_STATUSES, help="Filter by status")
    p_list.add_argument("--company", help="Filter by company name (partial match, case-insensitive)")

    # -- notes ----------------------------------------------------------------
    p_notes = sub.add_parser("notes", help="Append a note to an application")
    p_notes.add_argument("ref", help="Numeric ID (from 'list') or job posting URL")
    p_notes.add_argument("text", help="Note text to append")

    # -- status ---------------------------------------------------------------
    p_status = sub.add_parser("status", help="Update the status of an application")
    p_status.add_argument("ref", help="Numeric ID (from 'list') or job posting URL")
    p_status.add_argument("new_status", choices=VALID_STATUSES)

    # -- remove ---------------------------------------------------------------
    p_remove = sub.add_parser("remove", help="Remove an application from the tracker")
    p_remove.add_argument("ref", help="Numeric ID (from 'list') or job posting URL")

    args = parser.parse_args()
    {
        "add":    cmd_add,
        "show":   cmd_show,
        "list":   cmd_list,
        "notes":  cmd_notes,
        "status": cmd_status,
        "remove": cmd_remove,
    }[args.command](args)


if __name__ == "__main__":
    main()
