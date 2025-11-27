# Testing Strategy

This project is primarily Python logic, so automated tests should focus on `clean_job_title` behavior, CSV I/O flow, HubSpot wrapper behavior, and secret leakage checks.

## Tooling
- Python 3.10+ with `pytest` and `pandas`.
- Optionally `bandit` or simple regex scans to detect hard-coded secrets/API keys.

## Test Commands
- Unit tests: `pytest tests`
- Secret scan (lightweight): `python scripts/check_secrets.py`

## What to Cover
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
- **Outcome flags (HubSpot)**: When cleaned value differs, `outcome=changed` and `hs_execution_state=Succeeded`; when unchanged or invalid, `outcome=no_change` and `hs_execution_state=Failed, object removed from workflow`.
- **CSV flow**: End-to-end on a small fixture CSV writes `cleaned_job_titles.csv` with expected columns and cleaned values (blank for removed titles).

## Suggested Test Layout
- `tests/test_clean_job_title.py`: Unit tests for pure function behavior (use parametrized cases per above).
- `tests/test_custom_code.py`: Tests `main(event)` with mocked events to assert outputs and states.
- `tests/test_cli_flow.py`: Optional integration test that writes a temporary CSV, runs `job_title_cleaning.py` via a subprocess, and checks the output CSV.

## Example Parametrized Cases
- (`"Käse"`, `"Kase"`)
- (`"john@example.com"`, `None`)
- (`"+1 (212) 555-1234"`, `None`)
- (`"n/a"`, `None`)
- (`"aaaa"`, `None`)
- (`"phd researcher"`, `"PhD Researcher"`)
- (`"cto"` , `"CTO"`)
- (`"founder iv"`, `"Founder IV"`)
- (`"Chief|Revenue"` , `"Chief, Revenue"`)
- (`"This/Thing"` , `"This / Thing"`)
- (`"Head And Finance"` , `"Head and Finance"`)
- (`"Post Doc fellow"` , `"Post Doc Fellow"`)
- (`"\"Researcher\""` , `"Researcher"`)

## Secret/API Key Checks
- Add a simple scan to fail CI if likely secrets are committed. Example detection patterns:
  - Generic: strings matching `[A-Za-z0-9]{32,}` not in a safe allowlist.
  - Common prefixes: `sk-` (OpenAI), `AKIA` (AWS), `ghp_` (GitHub), `xoxb-` (Slack).
- Keep an allowlist for known-safe test tokens if needed.
- Run scan in CI before tests or as a separate job.
