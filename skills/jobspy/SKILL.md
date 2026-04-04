---
name: jobspy
description: Search for job postings across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, and more using the python-jobspy library
metadata: {"openclaw": {"emoji": "💼", "requires": {"bins": ["python3"]}, "install": [{"id": "uv", "kind": "uv", "label": "Install python-jobspy", "formula": "python-jobspy"}]}}
---

Use `search.py` (in the same directory as this file) to search for jobs across multiple boards. The script handles scraping, filtering, and fit scoring automatically — do not write your own Python for these tasks.

## Trigger

TRIGGER when the user wants to search for jobs, find job postings, scrape job listings, or query job boards (LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, BDJobs).

## Running a search

Find `search.py` in the same directory as this SKILL.md, then run:

```bash
python <path_to_search.py> --search-term "software engineer" --location "Austin, TX" [options]
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

## User preferences (`~/.config/jobspy/preferences.json`)

The script reads this file automatically on every run. Filtering and fit scoring require no flags — just maintain this file.

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
- **`fit_keywords`**: Weighted terms scored against title + description; results are sorted by `fit_score` descending.
- **`fit_description`**: Plain-English ideal-job description — use as context when summarizing or highlighting top matches.

## Workflow

1. Ask for search term and location if not provided.
2. Run `search.py` with the appropriate flags.
3. Display the printed table (already sorted by `fit_score` if preferences are set).
4. Offer to save to CSV (`--output jobs.csv`).
5. If the user wants to update preferences (block a company, add a keyword, etc.), update `~/.config/jobspy/preferences.json` and confirm.
6. If rate-limited (HTTP 429), suggest reducing `--results` or adding proxies via the `proxies` parameter in a manual script call.
