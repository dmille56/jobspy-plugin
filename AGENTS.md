# AGENTS.md — jobspy plugin

This plugin provides job search capabilities across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, and BDJobs using the python-jobspy library.

## Principles

- Always ask for search term and location before running a search if not provided.
- Default to searching `["indeed", "linkedin", "zip_recruiter", "google"]` unless the user specifies otherwise.
- Present results as a concise table (title, company, location, salary, URL) before offering to save.
- Offer to save results to CSV after every search.
- If rate-limited (HTTP 429), suggest adding proxies or reducing `results_wanted` — do not retry blindly.
- Normalize salaries to annual when comparing across results (`enforce_annual_salary=True`).
- Never expose proxy credentials in output or saved files.

## Knobs

- No required environment variables.
- No configuration file — all parameters are passed at search time.
- `proxies` (optional): list of proxy strings (`"user:pass@host:port"`) passed to `scrape_jobs()` if rate limiting occurs.

## Rate limit notes

- LinkedIn is the strictest — use proxies or reduce `results_wanted` for large searches.
- Indeed/Glassdoor: `hours_old` cannot be combined with `job_type`, `is_remote`, or `easy_apply`.
- LinkedIn: `hours_old` and `easy_apply` cannot be combined.
- ZipRecruiter: US and Canada only.
