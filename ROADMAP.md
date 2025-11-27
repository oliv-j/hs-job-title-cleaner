## Implemented
- Core cleaning logic (`clean_job_title`) shared between local script, HubSpot action, and web UI.
- Local CSV cleaner (`job_title_cleaning.py`) with helper to clean a file and write indexed output.
- Flask web app (`app.py`) with static UI for drag/drop uploads, job persistence under `/jobs`, and auto-download of cleaned CSVs.
- Persisted job metadata (`jobs/jobs.json`) and per-job folders with original and cleaned files.
- Translation and abbreviation lookup tables (from feedback) with exact-match expansion and updated junk list/punctuation trimming.
- HubSpot Custom Code Actions reference (`CCA.md`) outlining supported libraries, inputs/outputs, and limits.

## To Do / Future Enhancements
- Add automated tests for cleaning logic, API endpoints, and basic frontend flows.
- Add a requirements file/lock for consistent environment setup; optional makefile/task runner.
- Add lightweight secret scan to CI (API key detection).
- Improve CSV header handling/validation (explicit header option, clearer error messages).
- Add basic UX polish (progress indicator, job filtering) and error-state retries.
- Add fixtures/tests covering translation/abbreviation lookups and the expanded junk rules.
