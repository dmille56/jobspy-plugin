---
name: jobspy
description: Search for job postings across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, and more using the python-jobspy library
metadata: {"openclaw": {"emoji": "💼", "requires": {"bins": ["python3"]}, "install": [{"id": "uv", "kind": "uv", "label": "Install python-jobspy", "formula": "python-jobspy"}]}}
---

Use the `python-jobspy` library to search for job postings across multiple job boards concurrently. The library is imported as `from jobspy import scrape_jobs` and returns a pandas DataFrame.

## Trigger

TRIGGER when the user wants to search for jobs, find job postings, scrape job listings, or query job boards (LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, BDJobs).

## How to search for jobs

Write and execute a Python script using `scrape_jobs()`. Always print a summary and offer to save results to CSV.

### Core parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `site_name` | list\|str | Boards to search: `"linkedin"`, `"indeed"`, `"zip_recruiter"`, `"glassdoor"`, `"google"`, `"bayt"`, `"bdjobs"` |
| `search_term` | str | Job title or keyword (e.g. `"software engineer"`) |
| `location` | str | City, state, or country (e.g. `"Austin, TX"`) |
| `results_wanted` | int | Number of results per site (default: 15) |
| `hours_old` | int | Only return postings newer than this many hours |
| `job_type` | str | `"fulltime"`, `"parttime"`, `"internship"`, or `"contract"` |
| `is_remote` | bool | Filter for remote positions |
| `distance` | int | Search radius in miles (default: 50) |
| `country_indeed` | str | Country for Indeed/Glassdoor (e.g. `"USA"`, `"UK"`) |
| `enforce_annual_salary` | bool | Normalize all salaries to annual |
| `linkedin_fetch_description` | bool | Fetch full job descriptions from LinkedIn (slower) |
| `description_format` | str | `"markdown"` (default) or `"html"` |
| `verbose` | int | `0`=errors only, `1`=warnings, `2`=all logs |
| `proxies` | list | Proxy list if rate-limited (e.g. `["user:pass@host:port"]`) |

### Site-specific notes

- **LinkedIn**: Global; strictest rate limits — use proxies for large searches; `hours_old` and `easy_apply` cannot be combined
- **Indeed/Glassdoor**: 50+ countries; requires `country_indeed`; `hours_old` cannot be combined with `job_type`/`is_remote`/`easy_apply`
- **ZipRecruiter**: US and Canada only
- **Google Jobs**: Use `google_search_term` for advanced syntax instead of `search_term`
- **Bayt/BDJobs**: International; `search_term` parameter only

### Output columns

`site`, `title`, `company`, `company_url`, `job_url`, `location`, `is_remote`, `job_type`, `job_function`, `date_posted`, `salary_interval`, `min_amount`, `max_amount`, `currency`, `description`, `emails`

LinkedIn also returns: `job_level`, `company_industry`
Indeed also returns: `company_country`, `company_addresses`, `company_employees_label`, `company_revenue_label`, `company_description`, `company_logo`

## Example script

```python
from jobspy import scrape_jobs
import csv

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "google"],
    search_term="software engineer",
    location="San Francisco, CA",
    results_wanted=20,
    hours_old=72,
    country_indeed="USA",
    enforce_annual_salary=True,
    verbose=1,
)

print(f"Found {len(jobs)} jobs")
print(jobs[["site", "title", "company", "location", "min_amount", "max_amount", "job_url"]].to_string(index=False))

# Save to CSV
jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, index=False)
print("Saved to jobs.csv")
```

## Workflow

1. Ask the user for: search term, location, job type (if not provided), and which sites to search (default: indeed, linkedin, zip_recruiter, google)
2. Run the script via Bash
3. Display a concise table of results (title, company, location, salary, URL)
4. Offer to save to CSV or filter further (by salary, job type, remote, date, etc.)
5. If rate-limited (HTTP 429), suggest adding proxies or reducing `results_wanted`
