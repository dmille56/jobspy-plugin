#!/usr/bin/env python3
"""
jobspy search script — wraps python-jobspy with preference-based filtering and fit scoring.
Preferences are read from ~/.config/openclaw-jobspy/preferences.json automatically.
Jobs already tracked in the applications DB are filtered out automatically.

Usage:
    python search.py --search-term "software engineer" --location "Austin, TX" [options]
"""

import argparse
import csv
import json
import os
import re
import sqlite3
import sys

import pandas as pd


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

PREFS_PATH = os.path.expanduser("~/.config/openclaw-jobspy/preferences.json")
DB_PATH = os.path.expanduser("~/.config/openclaw-jobspy/applications.db")


def load_preferences():
    if os.path.exists(PREFS_PATH):
        with open(PREFS_PATH) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Applied-jobs filter
# ---------------------------------------------------------------------------

def load_applied_urls():
    """Return the set of job URLs already tracked in the applications DB."""
    if not os.path.exists(DB_PATH):
        return set()
    try:
        conn = sqlite3.connect(DB_PATH)
        rows = conn.execute("SELECT job_url FROM applications").fetchall()
        conn.close()
        return {row[0] for row in rows}
    except sqlite3.Error:
        return set()


def filter_applied(jobs, applied_urls):
    if not applied_urls:
        return jobs
    before = len(jobs)
    jobs = jobs[~jobs["job_url"].isin(applied_urls)]
    removed = before - len(jobs)
    if removed > 0:
        print(f"[tracker] Skipped {removed} job(s) you have already applied to.", file=sys.stderr)
    return jobs.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Preferences filtering
# ---------------------------------------------------------------------------

def apply_filters(jobs, prefs):
    before = len(jobs)

    for company in prefs.get("blocked_companies", []):
        jobs = jobs[~jobs["company"].str.contains(company, case=False, na=False)]

    for kw in prefs.get("blocked_title_keywords", []):
        jobs = jobs[~jobs["title"].str.contains(kw, case=False, na=False)]

    for kw in prefs.get("blocked_description_keywords", []):
        jobs = jobs[~jobs["description"].str.contains(kw, case=False, na=False)]

    required = prefs.get("required_title_keywords", [])
    if required:
        pattern = "|".join(re.escape(k) for k in required)
        jobs = jobs[jobs["title"].str.contains(pattern, case=False, na=False)]

    removed = before - len(jobs)
    if removed > 0:
        print(f"[filter] Removed {removed} job(s) based on preferences.", file=sys.stderr)

    return jobs.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Fit scoring
# ---------------------------------------------------------------------------

def score_fit(jobs, prefs):
    fit_keywords = prefs.get("fit_keywords", [])
    jobs = jobs.copy()
    jobs["fit_score"] = 0

    if not fit_keywords:
        return sort_jobs(jobs)

    def score_row(row):
        text = f"{row.get('title', '')} {row.get('description', '')}".lower()
        total = 0
        for item in fit_keywords:
            if isinstance(item, dict):
                kw = item.get("keyword", "").lower()
                weight = item.get("weight", 1)
            else:
                kw = str(item).lower()
                weight = 1
            if kw in text:
                total += weight
        return total

    jobs["fit_score"] = jobs.apply(score_row, axis=1)
    return sort_jobs(jobs)


def sort_jobs(jobs):
    if "date_posted" in jobs.columns:
        jobs["_date_posted_sort"] = pd.to_datetime(jobs["date_posted"], errors="coerce", utc=True)
        jobs = jobs.sort_values(
            by=["fit_score", "_date_posted_sort"],
            ascending=[False, False],
            na_position="last",
        ).drop(columns=["_date_posted_sort"])
    else:
        jobs = jobs.sort_values("fit_score", ascending=False)
    return jobs.reset_index(drop=True)


def fmt_salary(row):
    lo, hi, interval, currency = (
        row.get("min_amount"),
        row.get("max_amount"),
        row.get("salary_interval"),
        row.get("currency"),
    )
    if pd.isna(lo) and pd.isna(hi):
        return ""
    cur = currency or ""
    interval_label = f"/{interval}" if interval else ""
    if pd.notna(lo) and pd.notna(hi):
        return f"{cur}{int(lo):,}-{int(hi):,}{interval_label}"
    val = lo if pd.notna(lo) else hi
    return f"{cur}{int(val):,}{interval_label}"


def fmt_recency(value):
    dt = pd.to_datetime(value, errors="coerce", utc=True)
    if pd.isna(dt):
        return ""
    delta = pd.Timestamp.now(tz="UTC") - dt
    if delta.days >= 1:
        return f"{delta.days}d ago"
    hours = max(int(delta.total_seconds() // 3600), 0)
    if hours >= 1:
        return f"{hours}h ago"
    minutes = max(int(delta.total_seconds() // 60), 0)
    return f"{minutes}m ago"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser(prog=None):
    p = argparse.ArgumentParser(
        prog=prog,
        description="Search job boards with preference-based filtering and fit scoring.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--search-term", "-s", required=True, help="Job title or keyword")
    p.add_argument("--location", "-l", default="", help="City, state, or country")
    p.add_argument(
        "--sites",
        default="indeed,linkedin,zip_recruiter,google",
        help="Comma-separated job boards: indeed, linkedin, zip_recruiter, glassdoor, google, dice, bayt, bdjobs",
    )
    p.add_argument("--results", "-n", type=int, default=15, help="Results per site")
    p.add_argument("--hours-old", type=int, help="Only postings newer than N hours")
    p.add_argument(
        "--job-type",
        choices=["fulltime", "parttime", "internship", "contract"],
        help="Filter by employment type",
    )
    p.add_argument("--remote", action="store_true", help="Remote positions only")
    p.add_argument("--distance", type=int, default=50, help="Search radius in miles")
    p.add_argument("--country-indeed", default="USA", help="Country for Indeed/Glassdoor")
    p.add_argument(
        "--no-enforce-annual-salary",
        action="store_true",
        help="Skip normalizing salaries to annual amounts",
    )
    p.add_argument(
        "--fetch-linkedin-descriptions",
        action="store_true",
        help="Fetch full descriptions from LinkedIn (slower)",
    )
    p.add_argument("--output", "-o", help="Save results to a CSV file at this path")
    p.add_argument("--verbose", type=int, default=1, choices=[0, 1, 2])
    return p


def main(argv=None, prog=None):
    args = build_parser(prog=prog).parse_args(argv)

    try:
        from jobspy import scrape_jobs
    except ImportError:
        print("Error: python-jobspy is not installed.", file=sys.stderr)
        print("Install it with the nix package for this plugin.", file=sys.stderr)
        sys.exit(1)

    # Build scrape_jobs kwargs
    kwargs = dict(
        site_name=[s.strip() for s in args.sites.split(",")],
        search_term=args.search_term,
        results_wanted=args.results,
        distance=args.distance,
        enforce_annual_salary=not args.no_enforce_annual_salary,
        description_format="markdown",
        verbose=args.verbose,
    )
    if args.location:
        kwargs["location"] = args.location
    if args.hours_old is not None:
        kwargs["hours_old"] = args.hours_old
    if args.job_type:
        kwargs["job_type"] = args.job_type
    if args.remote:
        kwargs["is_remote"] = True
    if args.country_indeed:
        kwargs["country_indeed"] = args.country_indeed
    if args.fetch_linkedin_descriptions:
        kwargs["linkedin_fetch_description"] = True

    jobs = scrape_jobs(**kwargs)

    # Filter out already-applied jobs
    jobs = filter_applied(jobs, load_applied_urls())

    # Load preferences and apply filters/scoring
    prefs = load_preferences()

    fit_desc = prefs.get("fit_description", "")
    if fit_desc:
        print(f"\nFit profile: {fit_desc}\n")

    jobs = apply_filters(jobs, prefs)
    jobs = score_fit(jobs, prefs)

    print(f"Found {len(jobs)} jobs after filtering\n")

    # Display summary table
    blank = pd.Series([""] * len(jobs), index=jobs.index)
    display_df = pd.DataFrame(index=jobs.index)
    display_df["company"] = jobs["company"] if "company" in jobs.columns else blank
    display_df["fit"] = jobs["fit_score"] if "fit_score" in jobs.columns else blank
    display_df["recency"] = jobs["date_posted"].map(fmt_recency) if "date_posted" in jobs.columns else blank
    display_df["salary"] = jobs.apply(fmt_salary, axis=1)
    display_df["title"] = jobs["title"] if "title" in jobs.columns else blank
    display_df["url"] = jobs["job_url"] if "job_url" in jobs.columns else blank
    print(display_df.to_string(index=False))

    # Optionally save to CSV
    if args.output:
        jobs.to_csv(args.output, quoting=csv.QUOTE_NONNUMERIC, index=False)
        print(f"\nSaved {len(jobs)} jobs to {args.output}")


if __name__ == "__main__":
    main()
