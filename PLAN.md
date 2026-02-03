# PLAN.md

## Objective and scope
Deliver a job title cleaning solution usable via CLI, a local Flask UI (local-only for now), and a HubSpot Custom Coded Action. In scope: normalize single-column CSV job titles, store job outputs locally, expose a small API, and return structured outputs in HubSpot workflows. Out of scope: hosted/SaaS deployment, databases, authentication/authorization, model-based semantic validation.

## Success metrics & acceptance criteria
- CLI generates `cleaned_job_titles.csv` with columns `Index`, original, `Cleaned Job Title`, `Has Changed`; removed/invalid entries are blank; stats match expectations for sample data.
- Flask upload API returns 200 with `status=complete` for valid CSV; creates per-job folders and downloadable cleaned CSV; `/api/jobs` lists jobs with statuses; `/api/validate/<job>` reports changed rows.
- HubSpot action returns `newTitle` and `outcome` (`changed` when modified, `no_change` when identical/invalid); on error, sets `outcome=error` and `error_state=1` without crashing.
- Tests (`pytest tests`) pass.

## Background and context (link to README)
See README.md for overview, setup, and user-facing usage. This plan summarizes the confirmed behaviors from the repository.

## Requirements
### Current functional baseline (implemented)
- Shared `clean_job_title` used by CLI (`job_title_cleaning.py`), Flask app (`app.py` + `static/`), and HubSpot action (`hs-custom_code_action.py`).
- Accept single-column CSVs (or column named `Job Title`/`Original Job Title`); output indexed CSV with cleaned values and change flags; BOM included for Excel.
- Job storage under `jobs/` (configurable via `JOBS_DIR`) with metadata (`jobs.json`), per-job folders, and append-only log (`runs.log`).
- API endpoints: list jobs, upload CSV (creates job), download cleaned CSV, validate sample changes.
- HubSpot action input `jobTitle`; outputs `newTitle`, `non_latin_title`, `outcome` (`changed`/`no_change`/`removed`/`non_latin`), `error`, `error_message`, `error_state`. Bracket handling is balance-aware (no auto-closing).
- Non-functional: local-first; file-based storage; no auth; performance target up to ~500,000 rows via pandas; best-effort error handling; Python 3.10+; configurable storage path.

### Future requirements (pending)
- Broaden test coverage for edge cases, UI flows, and CSV header validation.
- Add dependency pinning/lockfile and minimal CI (tests + secret scan).
- Enhance UX/resilience (progress indicators, retries, filtering, clearer errors).
- Expand data quality rules (translations/abbreviations, regressions for known quirks).
- Optional Docker packaging/task runner for deployment.
- Local test harness to execute `hs-custom_code_action.py` with saved events before sandbox use.
- Non-functional additions as needed: performance profiling beyond 500k rows, accessibility guidance, metrics/backup if hosting scope changes.

### Out of scope
- Hosted multi-user service, auth, RBAC.
- Database-backed storage.
- Semantic validation via external models.
- Automated scheduling or workflow orchestration beyond HubSpot action usage.

## Data model and file formats
- Input CSV: single column of titles; optionally header `Job Title` or `Original Job Title`. Input is normalized so outputs always use `Original Job Title` as the source column.
- Output CSV (CLI/web): `Index`, `Original Job Title`, `Cleaned Job Title`, `Has Changed` (True when cleaned or removed), `Removed` (original value when the cleaned title is blank/removed), and `Removed Reason` (short code such as `junk_value`, `phone_like`, `non_latin_preserved`, `non_letter_ratio`). Blank cleaned values represent removed/invalid titles; non-Latin values not in the translation map are preserved unchanged and flagged via `non_latin_preserved`. Brackets are preserved with balance-aware trimming (no auto-closing).
- Job folders: `jobs/JobTitleClean###/JobTitleClean###-original.csv` and `...-cleaned.csv`; metadata in `jobs/jobs.json`; run log in `jobs/runs.log`.
- HubSpot CCA: input key `jobTitle` (string). Output fields: `newTitle` (string), `non_latin_title` (string when non-Latin detected), `outcome` (`changed`/`no_change`/`removed`/`non_latin`/`error`), `error`, `error_message`, `error_state` (int).

## Architecture and approach
- Components: cleaning core (`clean_job_title`), CLI wrapper, Flask API/UI, HubSpot CCA wrapper.
- Flow (textual):  
  - CLI: CSV → `clean_csv_file` → output CSV + stats.  
  - Flask: upload CSV → save under job folder → `clean_csv_file` → update `jobs.json` + log → download/validate endpoints.  
  - HubSpot: workflow input → `clean_job_title` → structured outputs for branching.
- Shared logic avoids divergence between interfaces; file-based persistence chosen for simplicity over DB. Trade-offs: limited concurrency, local-only durability, no auth.

## Web UI design
- Drag/drop or file-select CSV; shows banner messages for success/errors.
- Jobs list shows name, time, status (`new`, `complete`, `error`), stats when available, download button on completion, validate button to sample changes.
- Validation view: changed count and sample rows (from `/api/validate/<job>`).
- Auto-download cleaned CSV on successful upload. Accessibility notes: not explicitly addressed in code (currently blank for formal accessibility review).

## API surface (local only)
- `GET /api/jobs` → `{jobs: [...]}` with metadata and optional stats.
- `POST /api/upload` (multipart `file`) → creates job; returns job payload and optional `download_url`; 400 on missing/non-CSV; 500 on processing error.
- `GET /api/download/<job_name>` → cleaned CSV download; 400 on invalid name; 404 if missing.
- `GET /api/validate/<job_name>` → changed rows summary; 400 invalid name; 404 missing files; 500 on CSV read/merge errors.
- HubSpot-specific details remain in CCA.md.

## Operational plan
- Environments: local only; configurable `JOBS_DIR` for storage. No staging/prod separation defined.
- Secrets: none required.
- Logging/metrics: append JSON lines to `jobs/runs.log`; no metrics pipeline.
- Limits/retries: none beyond Flask/WSGI defaults; HubSpot limits covered in CCA.md.
- Backup/retention: manual; no policy defined.
- Runbook: recover by inspecting `jobs.json`, per-job folders, and `runs.log`; rerun upload if needed. Formal runbook not authored.

## How it works (current flow)
The cleaning core (`clean_job_title`) powers the CLI, Flask API/UI, and HubSpot action. Locally, users drop a single-column CSV into the web UI or run the CLI; the app saves the upload under `jobs/JobTitleClean###`, calls `clean_csv_file` (pandas-based) to write a cleaned CSV with change flags, updates `jobs/jobs.json`, logs the run, and triggers a download. The UI lists jobs with statuses and stats and can sample changed rows via `/api/validate/<job>`. The HubSpot action uses the same cleaner to return `newTitle`, `outcome`, and error metadata for workflow branching.

- [x] Core cleaning logic shared across CLI, Flask, CCA.
- [x] Local CSV cleaner with indexed output and stats.
- [x] Flask web app with drag/drop UI, job persistence, download, validate sample.
- [x] HubSpot custom coded action wrapper.
- [x] Basic pytest coverage for cleaner, CLI stats, API, CCA.
- [ ] Broaden tests for edge cases, UI flows, CSV header validation.
- [ ] Dependency pinning/lockfile and minimal CI (tests + secret scan).
- [ ] Local test harness to execute `hs-custom_code_action.py` with saved `event` fixtures before sandbox testing.
- [ ] UX/resilience: progress indicators, retries, better error states/filtering.
- [ ] Data quality expansion: more abbreviations/translations; regressions for ordinals/polite junk.
- [ ] Packaging/deployment: optional Docker container or task runner.

## Testing strategy
- See TESTING.md for detailed cases and commands.
- Current coverage: cleaning rules, CSV stats and columns, API upload/list/validate, HubSpot action outputs/error handling.
- Entry/exit (phase): tests pass; manual spot-check via CLI and Flask upload; validate sample changes.

## Risks and mitigations
- Risk: File-based storage corrupted (`jobs.json`/CSV). Mitigation: log runs; allow reprocessing from originals. Owner: TBD.
- Risk: No auth on Flask endpoints exposes data on shared hosts. Mitigation: run locally/behind trusted network. Owner: TBD.
- Risk: Large CSVs may exhaust memory (pandas). Mitigation: advise chunking; consider future streaming. Owner: TBD.
- Risk: HubSpot action edge cases diverge from core rules. Mitigation: keep logic centralized; add regression tests. Owner: TBD.
- Risk: Missing CI/secret scan allows regressions or leaks. Mitigation: add pipeline with tests/scan. Owner: TBD.

## Open questions
- None currently open (answers: local-only use, 500k-row guidance, no CI/pinning yet, containerization deferred, no accessibility/model requirements, no logging/backup mandates beyond current files).

## Decision log (ADR-lite)
- Date: not recorded (pre-plan). Decision: Single shared cleaning core across CLI/Flask/CCA. Options: separate implementations vs. shared. Rationale: consistency and test reuse. Impact: centralize changes.
- Date: not recorded (pre-plan). Decision: File-based storage under `jobs/` with metadata/log. Options: database vs. flat files. Rationale: simplicity/local use. Impact: limited concurrency/durability.
- Date: not recorded (pre-plan). Decision: Use pandas + Flask. Options: lighter CSV parsing/custom server. Rationale: speed to implement. Impact: memory-bound for very large files.

## Change log
-  (current) Rebuilt PLAN.md with confirmed scope, requirements, APIs, phases, repository map, and added explicit decisions on hosting (local-only), limits (500k rows), CI/pinning (deferred), Docker (future), accessibility/model/logging/backup (none).
-  Added cleaning rules for underscore-to-space normalisation, `Other -` prefix stripping, boundary-scoped typo and abbreviation corrections, and ordinal casing, with regression tests in `tests/test_cleaning_rules_new.py`.

## References
- README.md (overview/setup)
- CCA.md (HubSpot action details and limits)
- TESTING.md (test coverage and commands)
