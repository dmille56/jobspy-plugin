---
name: jobspy
description: Search for job postings across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, and more using the python-jobspy library
metadata: {"openclaw": {"emoji": "💼", "requires": {"bins": ["jobspy"]}}}
---

Use `jobspy`. The packaged binary handles scraping, filtering, fit scoring, and application tracking automatically — do not write your own Python for these tasks.

## Trigger

TRIGGER when the user wants to search for jobs, find job postings, scrape job listings, or query job boards (LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, BDJobs).

## Running a search

Run:

```bash
jobspy search --search-term "software engineer" --location "Austin, TX" [options]
```

### Flags

| Flag | Default | Description |
|------|---------|-------------|
| `--search-term`, `-s` | *(required)* | Job title or keyword |
| `--location`, `-l` | | City, state, or country |
| `--sites` | `indeed,linkedin,zip_recruiter,google` | Comma-separated boards: `indeed`, `linkedin`, `zip_recruiter`, `glassdoor`, `google`, `bayt`, `bdjobs` |
| `--results`, `-n` | `15` | Results per site |
| `--hours-old` | | Only postings newer than N hours |
| `--job-type` | | `fulltime`, `parttime`, `internship`, or `contract` |
| `--remote` | | Remote positions only |
| `--distance` | `50` | Search radius in miles |
| `--country-indeed` | `USA` | Country for Indeed/Glassdoor |
| `--no-enforce-annual-salary` | | Skip normalizing salaries to annual |
| `--fetch-linkedin-descriptions` | | Fetch full descriptions from LinkedIn (slower) |
| `--output`, `-o` | | Save full results to this CSV path |
| `--verbose` | `1` | `0`=errors only, `1`=warnings, `2`=all logs |

### Site-specific notes

- **LinkedIn**: Strictest rate limits — reduce `--results` or use proxies for large searches; `--hours-old` and `easy_apply` cannot be combined
- **Indeed/Glassdoor**: `--hours-old` cannot be combined with `--job-type`, `--remote`
- **ZipRecruiter**: US and Canada only
- **Google**: Supports advanced search syntax natively via `--search-term`

## User preferences (`~/.config/openclaw-jobspy/preferences.json`)

The script reads this file automatically on every run. Filtering and fit scoring require no flags — just maintain this file. Results are shown as a sorted table by fit score, then recency.

```json
{
  "blocked_companies": ["Acme Corp", "Initech"],
  "blocked_title_keywords": ["staff", "principal", "director", "VP"],
  "blocked_description_keywords": ["security clearance", "10+ years"],
  "required_title_keywords": ["engineer", "developer"],
  "fit_keywords": [
    {"keyword": "python", "weight": 3},
    {"keyword": "remote", "weight": 2},
    {"keyword": "rust", "weight": 2},
    {"keyword": "kubernetes", "weight": 1}
  ],
  "fit_description": "Free-text description of the ideal role — used as context when summarizing results."
}
```

- **`blocked_companies`**: Removed from results (case-insensitive substring match).
- **`blocked_title_keywords`**: Jobs whose title matches any of these are removed.
- **`blocked_description_keywords`**: Jobs whose description matches any of these are removed.
- **`required_title_keywords`**: If non-empty, only jobs matching at least one are kept.
- **`fit_keywords`**: Weighted terms scored against title + description; results are sorted by fit score descending, with newer `date_posted` values breaking ties.
- **`fit_description`**: Plain-English ideal-job description — use as context when summarizing or highlighting top matches.

## Application tracking (`jobspy tracker`)

Use `jobspy tracker` to record jobs you have applied to. Tracked jobs are **automatically excluded** from all future `jobspy search` results.

Database: `~/.config/openclaw-jobspy/applications.db` (SQLite, created and migrated automatically)

Valid statuses: `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`

Application methods: `website`, `easy_apply`, `referral`, `email`, `other`

### Subcommands

Jobs are assigned a short **numeric ID** on creation (shown by `add` and `list`). All commands except `add` accept either the ID or the full URL — prefer the ID in practice.

```bash
# Record an application — include as much metadata as available
# Prints the assigned ID on success, e.g. "Added (ID 7): https://..."
jobspy tracker add <url> \
    --site linkedin --title "Software Engineer" --company "Acme" \
    --company-url "https://acme.com" --location "Austin, TX" --remote \
    --job-type fulltime --job-function Engineering --job-level "Mid-Senior" \
    --company-industry "Technology" --date-posted 2026-04-01 \
    --min-amount 120000 --max-amount 150000 --salary-interval yearly --currency USD \
    --description "Full job description text..." --emails "jobs@acme.com" \
    --application-method easy_apply --follow-up-date 2026-04-14 \
    --notes "Applied via LinkedIn easy apply"

# Show all stored details for one application
jobspy tracker show 7
jobspy tracker show <url>   # URL also accepted

# List all applications — ID column appears first
jobspy tracker list [--status applied|interviewing|offer|rejected|withdrawn] [--company "Acme"]

# Append a timestamped note (use ID or URL)
jobspy tracker notes 7 "Had phone screen with recruiter Sarah. Next: technical."

# Update status (use ID or URL)
jobspy tracker status 7 interviewing

# Remove from tracker — will reappear in future searches (use ID or URL)
jobspy tracker remove 7
```

### Fields stored

| Field | Source | Description |
|-------|--------|-------------|
| `job_url` | posting | Job board listing URL |
| `site` | posting | Which job board (linkedin, indeed, etc.) |
| `title` | posting | Job title |
| `company` | posting | Company name |
| `company_url` | posting | Company website |
| `location` | posting | Job location |
| `is_remote` | posting | Whether position is remote |
| `job_type` | posting | fulltime / parttime / contract / internship |
| `job_function` | posting | Functional category |
| `job_level` | posting | Seniority level (LinkedIn) |
| `company_industry` | posting | Industry (LinkedIn) |
| `date_posted` | posting | When the job was originally posted |
| `min_amount` / `max_amount` | posting | Salary range |
| `salary_interval` | posting | yearly / hourly / monthly |
| `currency` | posting | Salary currency |
| `description` | posting | Full job description text |
| `emails` | posting | Contact email(s) from the posting |
| `date_applied` | tracking | When you ran `jobspy tracker add` |
| `status` | tracking | Current application status |
| `application_method` | tracking | How you applied |
| `follow_up_date` | tracking | Date to follow up |
| `interview_date` | tracking | Scheduled interview date |
| `offer_amount` | tracking | Offer amount if received |
| `notes` | tracking | Timestamped free-text notes |

## Adding a job to the tracker by URL

When a user provides a job posting URL to track (without first finding it via `jobspy search`), fetch the page and extract as many fields as possible before calling `jobspy tracker add`.

### Step 1 — Detect the job board from the URL

Map the domain to a `site` value:

| Domain | `site` value |
|--------|-------------|
| `linkedin.com` | `linkedin` |
| `indeed.com` | `indeed` |
| `glassdoor.com` | `glassdoor` |
| `ziprecruiter.com` | `zip_recruiter` |
| `google.com/about/careers` or Google Jobs | `google` |

If the domain doesn't match a known board, set `site` to the bare domain (e.g. `greenhouse.io`).

### Step 2 — Fetch the page and extract fields

Use the WebFetch tool to retrieve the URL. From the returned content, extract every field the tracker supports:

- **title** — job title (usually in `<h1>` or `<title>`)
- **company** — employer name
- **company_url** — link to the company's own website (not the job board)
- **location** — city/state/country; note "Remote" if present
- **is_remote** — `--remote` flag if location or description mentions remote
- **job_type** — fulltime / parttime / contract / internship
- **job_function** — functional category or department
- **job_level** — seniority (Entry, Mid-Senior, Director, etc.)
- **company_industry** — industry or sector
- **date_posted** — posting date in YYYY-MM-DD format
- **min_amount / max_amount / salary_interval / currency** — salary range if listed
- **description** — full job description text (strip HTML tags)
- **emails** — any contact email addresses found in the posting

### Step 3 — Fallback if the page is inaccessible

Some job boards (especially LinkedIn) block unauthenticated fetches or require JavaScript rendering. If WebFetch returns an error, a login wall, or no useful content:

1. Parse what you can from the URL itself (job ID, board name).
2. Run a narrow `jobspy search` query using any title/company gleaned from the URL or user:
   ```bash
    jobspy search --search-term "<title>" --sites <board> --results 5
   ```
3. Match the result whose `job_url` most closely matches the original URL and use its structured data.
4. If no match is found, add the URL to the tracker with only the fields known and tell the user which fields are missing.

### Step 4 — Run `jobspy tracker add`

Construct the `jobspy tracker add` command with every field extracted, then run it. Show the user a summary of what was filled in and what couldn't be found.

## Workflow

1. Ask for search term and location if not provided.
2. Run `jobspy search` with the appropriate flags — already-applied jobs are filtered out automatically.
3. Display the printed table (sorted by fit score, then recency).
4. Offer to save to CSV (`--output jobs.csv`).
5. When the user provides a job URL to track, follow the "Adding a job by URL" steps above before calling `jobspy tracker add`.
6. When the user says they applied to a job already in the tracker, use `jobspy tracker status` and/or `jobspy tracker notes` rather than re-adding.
7. If the user wants to update preferences (block a company, add a keyword, etc.), update `~/.config/openclaw-jobspy/preferences.json` and confirm.
8. If rate-limited (HTTP 429), suggest reducing `--results` or adding proxies via the `proxies` parameter in a manual script call.
