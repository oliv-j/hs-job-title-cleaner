# HubSpot job title cleaner for Operations Hub

Python utilities to normalize job titles locally, through a simple Flask UI, and inside HubSpot custom coded workflow actions.

## Components
- `job_title_cleaning.py`: Shared cleaning logic plus a CLI that reads a CSV and writes an indexed output with change flags.
- `app.py` + `static/`: Flask UI/API for drag/drop CSV uploads; jobs are stored under `jobs/` by default.
- `hs-custom_code_action.py`: HubSpot Operations Hub custom coded action (see `CCA.md` for a concise action reference).

## Repository structure (high level)
- `app.py`, `job_title_cleaning.py`, `hs-custom_code_action.py` — core app, CLI cleaner, and HubSpot action.
- `static/` — single-page UI for uploads, job listing, validation samples.
- `scripts/validate_job.py` — CLI to inspect changed rows for a job.
- `tests/` — pytest suites for cleaner, API, and HubSpot action.
- `jobs/` — local storage (metadata, logs, per-job original/cleaned CSVs).
- `README.md`, `PLAN.md`, `TESTING.md`, `CCA.md` — docs; `requirements.txt` — dependencies.

## Quick start (local web app)
- Requires Python 3.10+.
- From the project root, create/activate a virtual environment and install deps:
  ```bash
  python3 -m venv .venv
  source .venv/bin/activate
  pip install -r requirements.txt
  ```
- Start the app (optionally override storage with `JOBS_DIR=/path/to/jobs`):
  ```bash
  python app.py
  ```
  Then visit http://localhost:5000.
- Drag/drop a CSV (single column; header optional). A job is created (`JobTitleClean###`), processed immediately, and the cleaned CSV auto-downloads. Jobs and files persist under `jobs/`; runs are appended to `jobs/runs.log`.
- The API also exposes `GET /api/jobs`, `GET /api/download/<job_name>`, and `GET /api/validate/<job_name>` (sample changed rows).

## Command-line cleaner
- Place your input CSV as `job_titles.csv` (single column of titles, or a column named `Job Title` / `Original Job Title`).
- Run:
  ```bash
  python job_title_cleaning.py
  ```
  It writes `cleaned_job_titles.csv` with columns `Index`, `Original Job Title`, `Cleaned Job Title`, `Has Changed`, `Removed`, and `Removed Reason`. Removed/invalid titles have blank cleaned values, the original value copied into `Removed`, and a short reason (e.g., `junk_value`, `phone_like`, `non_latin_preserved`, `non_letter_ratio`); a BOM is included for Excel compatibility. Non-Latin values not in the translation map are preserved unchanged and flagged via `Removed Reason` so you can filter them separately.

## Jobs storage and validation
- Job folders live under `jobs/` (or `$JOBS_DIR`) with `jobs/jobs.json` metadata. File names follow `JobTitleClean###-original.csv` and `JobTitleClean###-cleaned.csv`.
- Use `scripts/validate_job.py JobTitleClean001 --jobs-dir jobs` or `GET /api/validate/<job_name>` to inspect changed rows for a run.

## Testing
- After installing requirements, run `pytest tests`. See `TESTING.md` for coverage details and recommended cases.

## Cleaning rules (summary)
- Strip leading/trailing punctuation/quotes, enclosing parentheses/quotes/backticks, emails, and repeated quotes.
- Convert diacritics to ASCII; translate known non-Latin exact matches; drop any remaining non-Latin strings.
- Remove phone-like strings (7+ digits/symbols), numeric-only values, single characters, punctuation-only strings, and junk tokens (e.g., `n/a`, `mr`, `aaa`, `4a`, `god`, spammy noise).
- Expand abbreviations (e.g., `R&D` → `Research and Development`, `PI` → `Primary Investigator`) before casing; uppercase roman numerals attached to words.
- Preserve all-uppercase acronyms in a whitelist (IT, VP, AIO, APHL); convert `phd` to `PhD`; title-case the rest. Lowercase `And` only when between words; preserve `Post Doc`.
- Replace vertical bars `|` with commas and insert spacing around slashes when both sides are 4+ letter words. Return `None` for invalid results.

## HubSpot custom coded action
1. Add a custom coded action in your workflow and choose Python.
2. Set input key `jobTitle` to the contact’s Job Title field.
3. Paste the contents of `hs-custom_code_action.py`.
4. Output keys: `newTitle` (string) and `outcome` (string: `changed`, `no_change`, `removed`, or `non_latin`) plus `non_latin_title` when non-Latin is detected. The script also returns `error`, `error_message`, and `error_state` for visibility. Brackets are preserved (balance-aware trim) to avoid adding/removing parentheses.
5. Branch on `outcome == "changed"` to write `newTitle` back to the record. When cleaning removes the title entirely, `newTitle` is blank and `outcome` is `removed`. When unchanged, `outcome` is `no_change`. When non-Latin is detected, `newTitle` and `non_latin_title` carry the original and `outcome` is `non_latin`.

## Notes from bulk testing
- On a test sandbox with ~100k multilingual job titles, the script removed ~800 values, made ~1.2k major changes, and ~23k minor changes.
- Removes illegal entries such as email addresses, single characters, or values consisting solely of special characters.
- Translates known non-Latin exact matches per lookup and ignores remaining non-Latin strings.
- Fixes formatting issues (capitalisation, double spaces, punctuation at start/end) and removes repeated-character junk (e.g., `aaaa`, `jooooob title`).
- Does not remove gibberish words that still look like text (e.g., `jqocleruair`) or polite rejections (e.g., `No thank you`). Ordinal suffixes like `1st` may become `1St`.

Future idea: After cleaning, call a model to validate any remaining value as a plausible job title.
