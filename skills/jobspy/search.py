#!/usr/bin/env python3
"""
jobspy search script — wraps python-jobspy with preference-based filtering and fit scoring.
Preferences are read from ~/.config/jobspy/preferences.json automatically.

Usage:
    python search.py --search-term "software engineer" --location "Austin, TX" [options]
"""

import argparse
import csv
import json
import os
import re
import sys


# ---------------------------------------------------------------------------
# Preferences
# ---------------------------------------------------------------------------

PREFS_PATH = os.path.expanduser("~/.config/openclaw-jobspy/preferences.json")


def load_preferences():
    if os.path.exists(PREFS_PATH):
        with open(PREFS_PATH) as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Filtering
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
    if not fit_keywords:
        return jobs

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

    jobs = jobs.copy()
    jobs["fit_score"] = jobs.apply(score_row, axis=1)
    return jobs.sort_values("fit_score", ascending=False).reset_index(drop=True)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser():
    p = argparse.ArgumentParser(
        description="Search job boards with preference-based filtering and fit scoring.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("--search-term", "-s", required=True, help="Job title or keyword")
    p.add_argument("--location", "-l", default="", help="City, state, or country")
    p.add_argument(
        "--sites",
        default="indeed,linkedin,zip_recruiter,google",
        help="Comma-separated job boards: indeed, linkedin, zip_recruiter, glassdoor, google, bayt, bdjobs",
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


def main():
    args = build_parser().parse_args()

    try:
        from jobspy import scrape_jobs
    except ImportError:
        print("Error: python-jobspy is not installed.", file=sys.stderr)
        print("Install it with:  uv pip install python-jobspy", file=sys.stderr)
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

    # Load preferences and apply filters/scoring
    prefs = load_preferences()

    fit_desc = prefs.get("fit_description", "")
    if fit_desc:
        print(f"\nFit profile: {fit_desc}\n")

    jobs = apply_filters(jobs, prefs)
    jobs = score_fit(jobs, prefs)

    print(f"Found {len(jobs)} jobs after filtering\n")

    # Display summary table
    display_cols = ["fit_score", "site", "title", "company", "location", "min_amount", "max_amount", "job_url"]
    display_cols = [c for c in display_cols if c in jobs.columns]
    print(jobs[display_cols].to_string(index=False))

    # Optionally save to CSV
    if args.output:
        jobs.to_csv(args.output, quoting=csv.QUOTE_NONNUMERIC, index=False)
        print(f"\nSaved {len(jobs)} jobs to {args.output}")


if __name__ == "__main__":
    main()
