# AGENTS.md — jobspy plugin

This plugin provides job search capabilities across LinkedIn, Indeed, Glassdoor, ZipRecruiter, Google Jobs, Bayt, and BDJobs using the python-jobspy library.

## Principles

- Always ask for search term and location before running a search if not provided.
- Always run searches via `search.py` — never write custom scraping or filtering Python from scratch.
- Default to `--sites indeed,linkedin,zip_recruiter,google` unless the user specifies otherwise.
- Present the printed table as-is; results are already filtered and sorted by fit score.
- Offer to save results to CSV (`--output <file>`) after every search.
- If rate-limited (HTTP 429), suggest reducing `--results` or adding proxies — do not retry blindly.
- Never expose proxy credentials in output or saved files.

## Preferences

- Preferences live at `~/.config/jobspy/preferences.json` and are applied automatically by `search.py`.
- When the user says things like "block that company", "never show clearance jobs", or "add React as a fit keyword", update the JSON file and confirm the change.
- If the preferences file doesn't exist yet and the user wants to set one up, create `~/.config/jobspy/` and write the file — show the user the JSON before saving.
- Use `fit_description` as context when writing summaries or calling out top matches; don't just print it verbatim.

## Knobs

- No required environment variables.
- `~/.config/jobspy/preferences.json` (optional): persistent filtering and fit-scoring preferences — see SKILL.md for the full schema.
- `proxies` (optional): pass directly in a manual `scrape_jobs()` call if `search.py` doesn't expose it yet.

## Rate limit notes

- LinkedIn is the strictest — use proxies or reduce `--results` for large searches.
- Indeed/Glassdoor: `--hours-old` cannot be combined with `--job-type` or `--remote`.
- LinkedIn: `--hours-old` and `easy_apply` cannot be combined.
- ZipRecruiter: US and Canada only.
