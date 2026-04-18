# AGENTS.md — jobspy plugin

This plugin provides job search capabilities across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, and BDJobs using the python-jobspy library.

## Principles

- Always ask for search term and location before running a search if not provided.
- Always run searches via `search.py` — never write custom scraping or filtering Python from scratch.
- Default to `--sites indeed,linkedin,zip_recruiter,google` unless the user specifies otherwise.
- Present the printed table in the default search layout: company, fit, recency, salary, title, and URL. Results are already filtered and sorted by fit score, then recency.
- Offer to save results to CSV (`--output <file>`) after every search.
- When the user says they applied to a job, immediately run `tracker.py add <url>` and pass every available field from the search results (site, title, company, company_url, location, is_remote, job_type, job_function, job_level, company_industry, date_posted, salary fields, description, emails). The command prints the assigned numeric ID — tell the user what it is.
- Use the numeric ID (not the URL) in all subsequent `show`, `notes`, `status`, and `remove` commands. The URL is still accepted but the ID is far easier for the user to reference.
- Use `tracker.py notes <id> "<text>"` whenever the user mentions a new development (phone screen, interview scheduled, offer received) rather than re-running `add`.
- Use `tracker.py status <id> <status>` when the user reports a status change.
- If rate-limited (HTTP 429), suggest reducing `--results` or adding proxies — do not retry blindly.
- Never expose proxy credentials in output or saved files.

## Adding a job to the tracker by URL

When the user gives you a job URL to track directly (not from a prior search result), follow these steps before calling `tracker.py add`:

1. **Detect the board** from the URL domain — see the domain→site mapping table in SKILL.md.

2. **Fetch the page** using the WebFetch tool. Extract every field the tracker stores: title, company, company_url, location, is_remote, job_type, job_function, job_level, company_industry, date_posted, salary (min/max/interval/currency), description, emails. Strip HTML from description text.

3. **If WebFetch fails or returns a login wall** (common with LinkedIn):
   - Parse any title or company visible in the URL path or that the user mentioned.
   - Run `search.py` with a narrow query (`--search-term "<title>" --sites <board> --results 5`) and find the closest matching result by URL similarity or title+company match.
   - Use that result's structured data to fill the tracker fields.
   - If still no match, add the URL with only what is known and tell the user which fields are missing.

4. **Run `tracker.py add`** with all extracted fields. Show the user a brief summary: which fields were filled and which were left blank.

Do not ask the user to manually supply fields that you can fetch yourself.

## Preferences

- Preferences live at `~/.config/openclaw-jobspy/preferences.json` and are applied automatically by `search.py`.
- When the user says things like "block that company", "never show clearance jobs", or "add React as a fit keyword", update the JSON file and confirm the change.
- If the preferences file doesn't exist yet and the user wants to set one up, create `~/.config/openclaw-jobspy/` and write the file — show the user the JSON before saving.
- Use `fit_description` as context when writing summaries or calling out top matches; don't just print it verbatim.

## Knobs

- No required environment variables.
- `~/.config/openclaw-jobspy/preferences.json` (optional): persistent filtering and fit-scoring preferences — see SKILL.md for the full schema.
- `~/.config/openclaw-jobspy/applications.db` (SQLite): application tracker — created automatically on first `tracker.py` use; read by `search.py` on every run.
- `proxies` (optional): pass directly in a manual `scrape_jobs()` call if `search.py` doesn't expose it yet.

## Rate limit notes

- LinkedIn is the strictest — use proxies or reduce `--results` for large searches.
- Indeed/Glassdoor: `--hours-old` cannot be combined with `--job-type` or `--remote`.
- LinkedIn: `--hours-old` and `easy_apply` cannot be combined.
- ZipRecruiter: US and Canada only.
