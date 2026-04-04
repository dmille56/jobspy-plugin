#!/usr/bin/env python3
"""
jobspy application tracker — records jobs you have applied to so they are
automatically filtered out of future searches.

Database: ~/.config/openclaw-jobspy/applications.db

Usage:
    python tracker.py add <url> [--title "..."] [--company "..."] [--location "..."]
    python tracker.py list [--status <status>]
    python tracker.py status <url> <new_status>
    python tracker.py remove <url>
"""

import argparse
import os
import sqlite3
import sys
from datetime import datetime, timezone

DB_PATH = os.path.expanduser("~/.config/openclaw-jobspy/applications.db")

VALID_STATUSES = ["applied", "interviewing", "offer", "rejected", "withdrawn"]


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

def open_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            job_url     TEXT    UNIQUE NOT NULL,
            title       TEXT,
            company     TEXT,
            location    TEXT,
            date_applied TEXT   NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%SZ', 'now')),
            status      TEXT    NOT NULL DEFAULT 'applied'
        )
    """)
    conn.commit()
    return conn


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------

def cmd_add(args):
    conn = open_db()
    try:
        conn.execute(
            """
            INSERT INTO applications (job_url, title, company, location)
            VALUES (?, ?, ?, ?)
            """,
            (args.url, args.title, args.company, args.location),
        )
        conn.commit()
        print(f"Added: {args.url}")
        if args.title or args.company:
            parts = [p for p in [args.title, args.company, args.location] if p]
            print(f"       {' | '.join(parts)}")
    except sqlite3.IntegrityError:
        print(f"Already tracked: {args.url}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


def cmd_list(args):
    conn = open_db()
    query = "SELECT * FROM applications"
    params = []
    if args.status:
        query += " WHERE status = ?"
        params.append(args.status)
    query += " ORDER BY date_applied DESC"

    rows = conn.execute(query, params).fetchall()
    conn.close()

    if not rows:
        print("No applications tracked yet.")
        return

    col_widths = {"status": 11, "date": 10, "company": 20, "title": 30}
    header = (
        f"{'Status':<{col_widths['status']}} "
        f"{'Date':<{col_widths['date']}} "
        f"{'Company':<{col_widths['company']}} "
        f"{'Title':<{col_widths['title']}} "
        f"URL"
    )
    print(header)
    print("-" * len(header))
    for row in rows:
        date = (row["date_applied"] or "")[:10]
        company = (row["company"] or "")[:col_widths["company"]]
        title = (row["title"] or "")[:col_widths["title"]]
        print(
            f"{row['status']:<{col_widths['status']}} "
            f"{date:<{col_widths['date']}} "
            f"{company:<{col_widths['company']}} "
            f"{title:<{col_widths['title']}} "
            f"{row['job_url']}"
        )
    print(f"\n{len(rows)} application(s) total.")


def cmd_status(args):
    if args.new_status not in VALID_STATUSES:
        print(f"Invalid status '{args.new_status}'. Choose from: {', '.join(VALID_STATUSES)}", file=sys.stderr)
        sys.exit(1)
    conn = open_db()
    cur = conn.execute(
        "UPDATE applications SET status = ? WHERE job_url = ?",
        (args.new_status, args.url),
    )
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        print(f"URL not found in tracker: {args.url}", file=sys.stderr)
        sys.exit(1)
    print(f"Updated status to '{args.new_status}': {args.url}")


def cmd_remove(args):
    conn = open_db()
    cur = conn.execute("DELETE FROM applications WHERE job_url = ?", (args.url,))
    conn.commit()
    conn.close()
    if cur.rowcount == 0:
        print(f"URL not found in tracker: {args.url}", file=sys.stderr)
        sys.exit(1)
    print(f"Removed: {args.url}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Track job applications and filter them from future searches.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # add
    p_add = sub.add_parser("add", help="Record a job you have applied to")
    p_add.add_argument("url", help="Job posting URL")
    p_add.add_argument("--title", help="Job title")
    p_add.add_argument("--company", help="Company name")
    p_add.add_argument("--location", help="Job location")

    # list
    p_list = sub.add_parser("list", help="List tracked applications")
    p_list.add_argument(
        "--status",
        choices=VALID_STATUSES,
        help="Filter by status",
    )

    # status
    p_status = sub.add_parser("status", help="Update the status of an application")
    p_status.add_argument("url", help="Job posting URL")
    p_status.add_argument("new_status", choices=VALID_STATUSES, help="New status")

    # remove
    p_remove = sub.add_parser("remove", help="Remove a URL from the tracker")
    p_remove.add_argument("url", help="Job posting URL")

    args = parser.parse_args()
    {"add": cmd_add, "list": cmd_list, "status": cmd_status, "remove": cmd_remove}[args.command](args)


if __name__ == "__main__":
    main()
