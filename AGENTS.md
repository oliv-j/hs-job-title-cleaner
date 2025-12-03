# AGENTS.md

## 1. Overview
This document defines how AI coding assistants (e.g., ChatGPT Codex or Copilot) should interpret the repository’s purpose, structure, and workflows.  
Agents assist in maintaining, extending, and documenting the *HubSpot job title cleaner* project while adhering to the design, testing, and operational principles in `PLAN.md`.

---

## 2. Core objectives
- Preserve functional equivalence across CLI, Flask, and HubSpot contexts.  
- Maintain reproducibility (no hidden dependencies, clear I/O contracts).  
- Comply with HubSpot CCA constraints (see `CCA.md`).  
- Follow testing and style conventions (see `TESTING.md`).  
- Keep Pythonic, readable, and modular code.  
- Avoid speculative model-based validation (out of scope per `PLAN.md`).

---

## 3. Agent roles

| Agent | Purpose | Primary Files | Notes |
|--------|----------|---------------|-------|
| **Planner** | Expands or revises `PLAN.md`, defines development phases. | `PLAN.md` | Acts as project owner. |
| **Engineer** | Implements CLI, Flask, or CCA scripts. | `job_title_cleaning.py`, `app.py`, `hs-custom_code_action.py` | Uses test-driven approach. |
| **QA Tester** | Extends pytest coverage, runs or proposes new suites. | `tests/`, `TESTING.md` | Ensures consistency across interfaces. |
| **Documenter** | Updates `README.md`, `CCA.md`, and `PLAN.md`. | Docs | Keeps consistency with code. |
| **Integrator** | Aligns local (Flask/CLI) with HubSpot CCA environment. | `CCA.md`, `hs-custom_code_action.py` | Ensures input/output parity and logging policy compliance. |

---

## 4. Working context and constraints
- **Runtime:** Python 3.10+; Flask for local API; HubSpot CCAs limited to 20 s / 128 MB.  
- **Storage:** File-based under `/jobs`; no databases or auth.  
- **Error handling:** Prefer explicit `try/except`; never suppress exceptions in HubSpot code.  
- **Logging:** Follow PII-masking and structure rules in `CCA.md`.  
- **Testing:** All code must be pytest-compatible and runnable locally.  
- **Security:** Never store secrets in code; use environment variables or HubSpot Secrets.

---

## 5. File and dependency awareness

| Purpose | File |
|----------|------|
| Requirements and roadmap | `PLAN.md` |
| HubSpot execution contract | `CCA.md` |
| Testing scope and conventions | `TESTING.md` |
| User and developer setup | `README.md` |

Any new feature **must** update at least one of these files to reflect changes.

---

## 6. Prompt and collaboration conventions
- Use **British English** and maintain sentence case.  
- Use **line numbers** for code insertion points when editing.  
- Prefer **small, testable PR-sized changes** rather than monolithic edits.  
- Ask clarifying questions if the spec or behaviour is ambiguous.  
- When generating code, **cite the corresponding section** of `PLAN.md` or `CCA.md` that justifies it.  
- Avoid introducing speculative ML functionality unless approved in a future plan phase.

---

## 7. Agent memory anchors
Agents should keep short summaries in memory:
- Repository name and goal.  
- Current version of `PLAN.md`.  
- Cleaning logic principles (regex, casing, diacritics, junk filters).  
- API surface (`/api/jobs`, `/api/upload`, `/api/download`, `/api/validate`).  
- HubSpot CCA input/output rules.  
- Test coverage expectations.

---

## 8. Governance and updates
- When significant design choices are made, update the **Decision Log** in `PLAN.md`.  
- `AGENTS.md` itself should be versioned; changes require sign-off from the **Planner** agent role.  
- Before running agents automatically, validate their prompt scopes with sample tasks.

---

## 9. Example invocation templates

**Engineer role (implementing):**
> “Using the current PLAN.md and TESTING.md as context, modify `app.py` to add an optional parameter `--no-auto-download` in the Flask route. Show insertion points and respect current code style.”

**QA role:**
> “Based on TESTING.md, add a pytest for validating that empty job title rows are written as blank cleaned titles in the CSV output.”

---

## 10. References
- [PLAN.md](PLAN.md)  
- [CCA.md](CCA.md)  
- [TESTING.md](TESTING.md)  
- [README.md](README.md)
