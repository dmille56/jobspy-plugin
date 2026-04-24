# jobspy-plugin

Job search and application tracking helpers for OpenClaw. Search across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, and BDJobs with smart filtering, fit scoring, and a built-in application tracker.

**Requires Python 3.11+**

## Install (run from the repo root)

```bash
pipx install .
```

This package wraps `python-jobspy` from the `dmille56/JobSpy` fork, pinned in both `pyproject.toml` and `flake.nix`.

## Quick Start

```bash
jobspy search --search-term "software engineer" --location "Austin, TX"
jobspy tracker list
```

Run `jobspy --help` or `jobspy search --help` for full flag reference.

## jobspy search

| Flag | Default | Description |
|------|---------|-------------|
| `--search-term`, `-s` | *(required)* | Job title or keyword |
| `--location`, `-l` | | City, state, or country |
| `--sites` | `indeed,linkedin,zip_recruiter,google` | Comma-separated boards: dice, indeed, linkedin, zip_recruiter, glassdoor, google, bayt, bdjobs |
| `--results`, `-n` | `15` | Results per site |
| `--hours-old` | | Only postings newer than N hours |
| `--job-type` | | `fulltime`, `parttime`, `internship`, `contract` |
| `--remote` | | Remote positions only |
| `--distance` | `50` | Search radius in miles |
| `--output`, `-o` | | Save results to CSV |

### Site-specific notes

- **LinkedIn**: Strictest rate limits — reduce `--results` for large searches; `--hours-old` and `easy_apply` cannot be combined
- **Indeed/Glassdoor**: `--hours-old` cannot be combined with `--job-type` or `--remote`
- **ZipRecruiter**: US and Canada only

## jobspy tracker

Track jobs you've applied to. Tracked jobs are automatically excluded from future searches.

### Subcommands

```bash
# Record an application
jobspy tracker add <url> \
    --site linkedin --title "Software Engineer" --company "Acme" \
    --location "Austin, TX" --remote --min-amount 120000 --max-amount 150000 \
    --application-method easy_apply --notes "Applied via LinkedIn"

# List all tracked applications
jobspy tracker list [--status applied|interviewing|offer|rejected|withdrawn]

# Show full details
jobspy tracker show <id|url>

# Update status
jobspy tracker status <id|url> interviewing

# Add a note
jobspy tracker notes <id|url> "Had phone screen with Sarah. Next: technical."

# Remove from tracker
jobspy tracker remove <id|url>
```

Jobs are assigned a short **numeric ID** on creation (printed by `add` and `list`). All commands except `add` accept either the ID or the full URL.

**Valid statuses:** `applied`, `interviewing`, `offer`, `rejected`, `withdrawn`

**Application methods:** `website`, `easy_apply`, `referral`, `email`, `other`

## Fit Scoring

Results are sorted by a fit score calculated from `~/.config/openclaw-jobspy/preferences.json`:

```json
{
  "fit_keywords": [
    {"keyword": "python", "weight": 3},
    {"keyword": "remote", "weight": 2}
  ],
  "blocked_companies": ["Acme Corp"],
  "blocked_title_keywords": ["staff", "principal"],
  "required_title_keywords": ["engineer"]
}
```

- Each matching keyword in title + description adds its weight to the score
- Blocked companies and title keywords are filtered out entirely
- `required_title_keywords` — only keep jobs matching at least one
- Tiebreaker: newer `date_posted` values rank higher

Run `jobspy search` and results are pre-filtered and pre-sorted — no extra flags needed.

## Configuration

Preferences file: `~/.config/openclaw-jobspy/preferences.json`

Tracker database: `~/.config/openclaw-jobspy/applications.db` (SQLite, created automatically)

## License

MIT
