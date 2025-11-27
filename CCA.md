# HubSpot Custom Code Actions (Workflows)

This guide summarizes how to develop and run Python (or Node.js) Custom Code Actions inside HubSpot workflows. It focuses on supported libraries, inputs/outputs, operational limits, and common caveats.

## Supported Python Libraries
- `requests` 2.28.2
- `@hubspot/api-client` ^8
- `google-api-python-client` 2.74.0
- `mysql-connector-python` 8.0.32
- `redis` 4.4.2
- `nltk` 3.8.1
- Standard library modules are allowed (e.g., `os`, `json`, `re`).

Import format for SDK modules: `from hubspot import HubSpot`, `from redis.client import Redis`, etc.

## Inputs (Workflow Properties)
- Add up to 50 properties directly in the workflow action UI.
- Access them via the `event` payload, e.g.:
  ```python
  email = event.get("inputFields").get("email")
  ```
- Prefer inputs over extra HubSpot API calls when possible.

## Outputs (Workflow Data)
- Return a JSON object containing `outputFields`:
  ```python
  return {
    "outputFields": {
      "email": email,
      "phone": phone
    }
  }
  ```
- Set output types in the workflow sidebar (string, number, boolean, datetime, enum, date, phone).
- String outputs are limited to 65,000 characters (otherwise `OUTPUT_VALUES_TOO_LARGE`).
- For datetime outputs: use UNIX milliseconds. For date-only outputs: UNIX milliseconds with time set to midnight UTC (e.g., `currentDate.setUTCHours(0,0,0,0)`).
- When copying values, ensure source and target property types are compatible.

## Secrets
- Store API keys/private app tokens as workflow secrets and read via environment variables:
  ```python
  hubspot = HubSpot(access_token=os.getenv("SECRET_NAME"))
  ```

## Example: Fetch a Contact Phone and Return Email/Phone
```python
import os
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException

def main(event):
    hubspot = HubSpot(access_token=os.getenv("SECRET_NAME"))

    phone = ""
    try:
        api_response = hubspot.crm.contacts.basic_api.get_by_id(
            event.get("object").get("objectId"),
            properties=["phone"],
        )
        phone = api_response.properties.get("phone")
    except ApiException as e:
        print(e)
        # Raise to trigger automatic retries on rate limits
        raise

    email = event.get("inputFields").get("email")

    return {
        "outputFields": {
            "email": email,
            "phone": phone,
        }
    }
```

## Execution Limits
- Max runtime: 20 seconds.
- Memory limit: 128 MB.
- Exceeding either limit results in an error.

## Retries and Rate Limits
- For HubSpot API rate-limit errors in Python, re-raise the exception in the `except` block to let HubSpot retry.

## Caveats
- **Node.js**:
  - `Math.random` can repeat across executions; use a CSPRNG such as `random-number-csprng@1.0.2`.
  - Variables declared outside `exports.main` may persist across executions; keep per-run logic inside `exports.main`.
- **Python**:
  - Variables declared outside `def main` may persist across executions. Use `global` if you must mutate them:
    ```python
    a = 1
    def main(event):
        global a
        a += 1
    ```

## Error Handling (Recommended Outputs)
- Include standard outputs to make downstream branching easier:
  - `error`: detailed error string
  - `error_message`: short human-readable message
  - `error_state`: `0` by default; set to `1` (or other codes) on errors

## Workflow Branching Note
- When reading workflow JSON from the v4 automation API (`/automation/v4/flows/{flowId}`): if a `staticBranch` has a `branchValue` but no other parameters, the workflow terminates at that branch for matching records. Keep this in mind when designing branch logic.
