# Custom code actions (CCA) — supporting reference

**Last verified:** 3 December 2025  
**Audience:** AI agent (primary), engineers (secondary)  
**Purpose:** Source of truth for constraints, naming conventions, and I/O contracts when generating or reviewing HubSpot **Custom code actions** (CCAs) inside **Workflows**. This file is cited by plans (e.g. `PLAN.md`); it does not teach workflow authoring.

---

## Source of truth and assumptions {{#source-of-truth}}

- **Canonical docs:** HubSpot *Workflows | Custom code actions* and linked knowledge base pages.  
  – Runtime & limits, inputs/outputs, retries, logs, and rate‑limiting are defined there.  
- **Team baselines for examples (not assertions about HubSpot’s runtime):**  
  – **Python 3.9**, **Node.js 20.x**, **HubSpot client v11** (when using the Node SDK outside the CCA preinstalled set).  
  – HubSpot’s CCA environment controls the actual runtime and preinstalled versions; always cross‑check the docs page at build time.

---

## At‑a‑glance constraints {{#limits-runtime}}

- **Execution time:** MUST finish within **20 seconds**.  
- **Memory:** MUST remain within **128 MB**.  
- **Properties in “Properties to include in code”:** MUST be **≤ 50** per action.  
- **Secrets:** In‑action aggregate secret values MUST be **≤ 1000 characters**; in test accounts you MUST use OAuth or a private app token.  
- **Retries:** To trigger HubSpot re‑attempts on 429/5xx, you MUST **throw** (Node) or **raise** (Python). HubSpot reattempts for up to **three days**, starting ~1 minute after failure, with increasing backoff (max gap ≈ 8 hours).  
- **Logging panel:** Test results show status, data outputs, total runtime, and memory usage.

> See the HubSpot docs for the exact wording and current behaviour (linked inline in this file).

---

## Inputs and outputs contract {{#io-contract}}

### Inputs (from the action UI)
- Inputs appear in code as `event.inputFields` with developer‑provided keys.  
- You MAY reference formatted values from earlier workflow actions via the data panel.  
- Each property can only be added once and MUST have a unique variable ID.  
- Limit: **≤ 50** inputs per CCA.

### Outputs (`outputFields`)
- The workflow reads outputs from an object:  
  – **Node:** `callback({{ outputFields: {{ ... }} }})`  
  – **Python:** `return {{ "outputFields": {{ ... }} }}`  
- Data output **types** (select in the action): **string**, **number**, **boolean**, **datetime**, **date**, **enum**, **phone number**.  
- **String length:** MUST be **≤ 65,000 characters** (exceeding throws `OUTPUT_VALUES_TOO_LARGE`).  
- **Datetime:** MUST be **UNIX milliseconds**.  
- **Date (no time):** MUST be **UNIX milliseconds at midnight UTC**.  
- **Downstream availability:** Outputs MUST be defined in the action for later steps to consume.

### Property‑type compatibility (Edit records) {{#outputs-types}}
- **Text →** text (single or multi‑line).  
- **Number →** text, number.  
- **Date picker →** date picker, datetime (time defaults to midnight UTC).  
- **Datetime →** datetime only.  
- **Enumeration / checkbox / select →** same type when option values exist in both source and target; copying to **text** uses the **label** string.  
- **Read‑only properties** can be **sources** only.

> For the full compatibility matrix and notes, refer to HubSpot’s “Compatible property types for copying values with workflows”.

---

## Naming conventions (project‑wide) {{#naming-conventions}}

- **Case:** `snake_case` everywhere for inputs and outputs.  
- **Pass‑through values:** Use the existing system API name verbatim (e.g., `api_name`).  
- **Write‑backs:** New values intended to be written to HubSpot properties MUST use `api_name_new`.  
- **Downstream‑only values:** Use `tmp_<purpose>` (e.g., `tmp_normalised_phone`). These MUST NOT be written to CRM properties.

---

## Language specifics (minimal, object‑agnostic) {{#language-specifics}}

### Node.js (callback pattern)
- Preinstalled SDK is typically **`@hubspot/api-client` (caret ^10)** in the CCA environment; verify on the docs page at build time.  
- Always **call `callback`** with an object containing `outputFields`.

```js
// example: input → transform → output (Node)
exports.main = async (event, callback) => {{  
  const raw = event.inputFields["some_input"];
  const value = (raw || "").trim();
  if (!value) return callback({{ outputFields: {{ error: true, error_code: "EMPTY", retryable: false }} }});
  return callback({{ outputFields: {{ tmp_clean_value: value }} }});
}};
```

### Python (return pattern)
- Use a `def main(event):` entrypoint and **return** a dict with `outputFields`.  
- Prefer the standard library and `requests` for HTTP; keep runtime budget in mind.

```python
# example: input → transform → output (Python)
def main(event):
    raw = event.get("inputFields", {{}}).get("some_input", "")
    value = (raw or "").strip()
    if not value:
        return {{"outputFields": {{"error": True, "error_code": "EMPTY", "retryable": False}}}}
    return {{"outputFields": {{"tmp_clean_value": value}}}}
```

> **Note:** The docs’ “Python supported libraries” section currently lists `@hubspot/api-client` under Python. That package is the **Node** SDK. If you need an SDK in Python outside the preinstalled set, the **official** package is `hubspot-api-client`; however, in CCAs prefer `requests` unless the CCA environment explicitly documents the SDK as preinstalled.

---

## Retries and error signalling {{#retries}}

- On **rate limits** or **transient 5xx** from HubSpot or upstream services, CCAs **SHOULD** bubble the error:  
  – **Node:** `throw err` inside the `catch` block.  
  – **Python:** `raise` within `except`.  
- HubSpot will reattempt execution for up to **3 days** with backoff.  
- To enable branch‑friendly handling, CCAs **SHOULD** also set outputs that encode error state:

```text
error (bool), error_code (string), error_message (string), retryable (bool)
```

Downstream plans MAY branch on `error`/`retryable` and log `error_code`/`error_message` (see logging policy).

---

## Action‑level rate limiting {{#rate-limiting}}

- CCAs **MAY** configure an action‑level throttle. It also applies to all **following actions** in the workflow after the CCA.  
- **Team default:** enable and start with **5 executions / second**; raise or lower based on upstream API guidance and observed logs.  
- If the action is paused due to rate limit, HubSpot emits a specific log entry and resumes automatically.

---

## Supported libraries (preinstalled in CCAs) — snapshot {{#supported-libraries}}

*(Do not download/install packages; use only what the CCA environment provides. Keep this list date‑stamped and refresh from the official page.)*

**Snapshot date:** 3 December 2025

**Node.js** (require/import as normal):  
- `@hubspot/api-client` ^10, `async` ^3.2.0, `aws-sdk` ^2.744.0, `axios` ^1.2.0, `lodash` ^4.17.20, `mongoose` ^6.8.0, `mysql` ^2.18.1, `redis` ^4.5.1, `request` ^2.88.2, `bluebird` ^3.7.2, `random-number-csprng` ^1.0.2, `googleapis` ^67.0.0.

**Python** (import with `import` / `from ... import ...`):  
- `requests` 2.28.2, **`@hubspot/api-client` ^8 (listed in docs; this is a Node package; treat as a documentation artefact)**, `google-api-python-client` 2.74.0, `mysql-connector-python` 8.0.32, `redis` 4.4.2, `nltk` 3.8.1.  
- Standard library imports are allowed (e.g., `os`, `json`, `datetime`).

---

## Logging and PII policy {{#logging}}

- **MUST NOT** log secrets/tokens anywhere.  
- **SHOULD NOT** log full emails or phone numbers.  
- If a downstream logging action is used, **MUST** partially mask PII (e.g., `john.s***@example.com`, `+44 ******1234`).  
- **SHOULD** include structured keys for observability (e.g., `operation`, `object_type`, `object_id`, `status`, `duration_ms`).  
- **SHOULD** keep logs concise to preserve memory/time budgets.

---

## Portal differences {{#portal-differences}}

- **Tokens:** Dev vs prod **WILL** differ; never hard‑code.  
- **IDs:** Record IDs and **object type IDs** **WILL** differ between portals. Plans MUST avoid assuming stable IDs across environments.

---

## Known behaviours and caveats {{#caveats}}

- **Container reuse:** Variables declared outside the main function **MAY** be reused across executions (Node and Python). Keep per‑execution state inside the function.  
- **Randomness (Node):** `Math.random()` **MAY** produce repeating sequences under concurrency; prefer a CSPRNG (e.g., `random-number-csprng`).  
- **Outputs must be defined:** An output not defined in the action **WILL NOT** appear downstream.  
- **Runtime drift:** HubSpot controls runtimes and preinstalled versions; verify at authoring time.

---

## Appendix A — minimal event payload (object‑agnostic) {{#event-payload}}

```json
{{
  "origin": {{"portalId": 1, "actionDefinitionId": 2}},
  "object": {{"objectType": "CONTACT", "objectId": 4}},
  "callbackId": "ap-123-456-7-8"
}}
```

---

## Appendix B — automation API note (static branches) {{#automation-static-branch}}

Where plans interact with **Automation v4** outside CCAs, be aware of “static” branch configuration behaviours in the Automation APIs. Treat this as an **observational** note and consult the Automation API docs when relying on branch semantics.

---

## Appendix C — references (direct links) {{#references}}

- **Workflows | Custom code actions** — constraints, inputs/outputs, retries, logs, rate limiting: https://developers.hubspot.com/docs/api-reference/automation-actions-v4-v4/custom-code-actions  
- **Compatible property types for copying values with workflows**: https://knowledge.hubspot.com/workflows/compatible-source-and-target-properties-for-copying-property-values-in-workflows  
- **Node SDK docs (`@hubspot/api-client`)**: https://developers.hubspot.com/docs/developer-tooling/sdks/node  
- **Node v16 deprecation (serverless)**: https://developers.hubspot.com/changelog/deprecation-of-node-v16-in-all-serverless-functions

---

## Appendix D — test harness (placeholder) {{#test-harness}}

**Objective:** Enable offline verification of CCA snippets with saved `event` fixtures, golden outputs, HTTP mocking, and environment variable injection.  
**Not implemented here.** Plans MAY reference this placeholder and specify harness details.

---

## Changelog {{#changelog}}

- 3 December 2025: Initial restructure to supporting‑reference format; added anchors; formalised naming conventions; added property‑type compatibility summary; inserted logging/PII policy; documented rate‑limit recommendation and retry/error contract.
