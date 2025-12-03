# Testing Strategy

Automated tests focus on `clean_job_title` behavior, CSV I/O, the HubSpot wrapper, and API endpoints. Manual checks help validate real job files.

## Setup
- Python 3.10+ with `pytest` and `pandas` installed (e.g., `pip install -r requirements.txt`).
- Tests set `JOBS_DIR` to a temporary folder, so they will not touch your local `jobs/` directory.

## Commands
- Automated tests: `pytest tests`
- Optional quick scan for obvious secrets (no bundled script yet): run your preferred scanner or use a simple regex with `rg --pcre2 "sk-[A-Za-z0-9]{32,}|ghp_[A-Za-z0-9]{36,}|AKIA[0-9A-Z]{16}"`.

## Existing suites
- `tests/test_clean_csv_stats.py`: Validates CSV stats, output columns (`Has Changed`), and index insertion.
- `tests/test_api.py`: Upload/list/validate endpoints using a temp `JOBS_DIR`.
- `tests/test_custom_code.py`: Ensures cleaning cases, `main(event)` outputs, and error handling for the HubSpot action.

## What to cover (unit/integration)
- **Input validation**: Non-string input returns `None`; empty/whitespace-only strings cleaned to empty; single-character values rejected.
- **Email & phone filtering**: Email-like and phone-like inputs return `None`.
- **Junk filtering**: Values in the junk list (e.g., `n/a`, `job title`, `aaa`, `mr`, `do`, `aa`, `4a`, lone `god`) return `None`.
- **Diacritics**: “Käse” → “Kase”.
- **Leading/trailing punctuation/quotes**: `" ,-- CTO"` → `CTO`; `"("Researcher")"` → `Researcher`; `"Title".` → `Title`.
- **Non-Latin handling**: Known translations (exact match) are applied; remaining non-Latin strings are dropped.
- **Capitalisation rules**: Acronyms preserved (IT, VP, APHL); `phd` → `PhD`; mixed-case words title-cased.
- **Roman numerals**: `Founder iv` → `Founder IV`.
- **Vertical bars**: `"Head|Sales"` → `Head, Sales`.
- **Slash spacing**: `"This/Thing"` → `This / Thing` when both words are 4+ letters.
- **Lowercasing And**: `"Head And Finance"` → `Head and Finance`.
- **Post Doc**: Preserves “Post Doc”.
- **Abbreviation/translation expansion**: `R&D` → `Research And Development`; `PI` → `Primary Investigator`; `Adj. prof, PI` → `Adiunct Professor, Principal Investigator`; `博士` → `Doctor Of Philosophy`.
- **Outcome flags (HubSpot)**: When cleaned value differs, `outcome=changed`; when unchanged, `outcome=no_change`; when cleaning removes the title entirely, `outcome=removed`; when non-Latin is detected (not in the translation map), `outcome=non_latin` and `non_latin_title` is populated; exceptions produce `outcome=error` and set `error_state=1`. Brackets are preserved with balance-aware trimming (no auto-closing).
- **CSV flow**: End-to-end on a small fixture CSV writes `cleaned_job_titles.csv` with expected columns and cleaned values (blank for removed titles).

## Manual checks
- Run `python job_title_cleaning.py` on a small CSV to confirm the output and `Has Changed` flags.
- For the web app, upload a CSV, then call `GET /api/validate/<job_name>` or run `python scripts/validate_job.py JobTitleClean001 --jobs-dir jobs` to inspect changed rows.

## Secret/API key checks
- No dedicated script is included yet; add a lightweight scanner in CI to fail on likely secrets (e.g., `[A-Za-z0-9]{32,}` not in an allowlist, and common prefixes such as `sk-`, `AKIA`, `ghp_`, `xoxb-`).
