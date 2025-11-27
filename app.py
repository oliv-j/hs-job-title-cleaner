import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from flask import Flask, jsonify, request, send_from_directory

from job_title_cleaning import clean_job_title, clean_csv_file


BASE_DIR = Path(__file__).parent
JOBS_DIR = Path(os.environ.get("JOBS_DIR", BASE_DIR / "jobs"))
METADATA_PATH = JOBS_DIR / "jobs.json"
LOG_PATH = JOBS_DIR / "runs.log"
JOB_PREFIX = "JobTitleClean"

app = Flask(__name__, static_folder="static", static_url_path="")


def ensure_storage() -> None:
    JOBS_DIR.mkdir(exist_ok=True)


def load_jobs() -> list:
    if not METADATA_PATH.exists():
        return []
    try:
        return json.loads(METADATA_PATH.read_text())
    except json.JSONDecodeError:
        return []


def save_jobs(jobs: list) -> None:
    ensure_storage()
    METADATA_PATH.write_text(json.dumps(jobs, indent=2))


def log_run(entry: dict) -> None:
    ensure_storage()
    payload = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        **entry,
    }
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload) + "\n")


def next_job_number(jobs: list) -> int:
    highest = 0
    for job in jobs:
        name = job.get("name", "")
        if name.startswith(JOB_PREFIX):
            suffix = name[len(JOB_PREFIX) :]
            if suffix.isdigit():
                highest = max(highest, int(suffix))
    return highest + 1


def job_name_from_number(num: int) -> str:
    return f"{JOB_PREFIX}{num:03d}"


def friendly_time(iso_value: str) -> str:
    try:
        dt = datetime.fromisoformat(iso_value)
    except ValueError:
        return iso_value
    return dt.astimezone().strftime("%b %d, %Y %I:%M %p")


@app.route("/api/jobs", methods=["GET"])
def list_jobs():
    jobs = load_jobs()
    result = []
    for job in jobs:
        item = dict(job)
        if "created_at" in item:
            item["created_at_display"] = friendly_time(item["created_at"])
        result.append(item)
    return jsonify({"jobs": result})


@app.route("/api/upload", methods=["POST"])
def upload_job():
    ensure_storage()
    upload = request.files.get("file")
    if not upload:
        return jsonify({"error": "No file provided"}), 400

    filename = upload.filename or ""
    if not filename.lower().endswith(".csv"):
        return jsonify({"error": "Only CSV files are supported"}), 400

    jobs = load_jobs()
    job_number = next_job_number(jobs)
    job_name = job_name_from_number(job_number)
    job_folder = JOBS_DIR / job_name
    job_folder.mkdir(parents=True, exist_ok=True)

    original_name = f"{job_name}-original.csv"
    cleaned_name = f"{job_name}-cleaned.csv"
    original_path = job_folder / original_name
    cleaned_path = job_folder / cleaned_name

    upload.save(original_path)

    job_entry = {
        "name": job_name,
        "status": "new",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "original_filename": original_name,
        "cleaned_filename": cleaned_name,
    }

    try:
        _, stats = clean_csv_file(original_path, cleaned_path)
        job_entry["status"] = "complete"
        job_entry["stats"] = stats
    except Exception as exc:
        job_entry["status"] = "error"
        job_entry["error"] = str(exc)
        log_run({"job": job_name, "status": "error", "error": str(exc)})
    else:
        log_run({"job": job_name, "status": "complete", "stats": stats})

    jobs.append(job_entry)
    save_jobs(jobs)

    download_url = f"/api/download/{job_name}" if job_entry["status"] == "complete" else None
    return (
        jsonify(
            {
                "job": job_entry,
                "download_url": download_url,
            }
        ),
        (200 if job_entry["status"] == "complete" else 500),
    )


@app.route("/api/download/<job_name>", methods=["GET"])
def download_job(job_name: str):
    if not re.fullmatch(rf"{JOB_PREFIX}\d{{3}}", job_name):
        return jsonify({"error": "Invalid job name"}), 400

    cleaned_name = f"{job_name}-cleaned.csv"
    job_folder = JOBS_DIR / job_name
    cleaned_path = job_folder / cleaned_name
    if not cleaned_path.exists():
        return jsonify({"error": "Cleaned file not found"}), 404

    return send_from_directory(job_folder, cleaned_name, as_attachment=True)


@app.route("/api/validate/<job_name>", methods=["GET"])
def validate_job(job_name: str):
    if not re.fullmatch(rf"{JOB_PREFIX}\d{{3}}", job_name):
        return jsonify({"error": "Invalid job name"}), 400

    job_folder = JOBS_DIR / job_name
    original_path = job_folder / f"{job_name}-original.csv"
    cleaned_path = job_folder / f"{job_name}-cleaned.csv"

    if not original_path.exists() or not cleaned_path.exists():
        return jsonify({"error": "Job files not found"}), 404

    try:
        orig_df = pd.read_csv(original_path)
        cleaned_df = pd.read_csv(cleaned_path)
    except Exception as exc:
        return jsonify({"error": f"Failed to read CSV: {exc}"}), 500

    try:
        merged = cleaned_df[["Original Job Title", "Cleaned Job Title"]]
        changed = merged[merged["Original Job Title"] != merged["Cleaned Job Title"]]
    except Exception as exc:
        return jsonify({"error": f"Failed to compute changes: {exc}"}), 500

    sample = changed.head(10).to_dict(orient="records")
    result = {
        "job": job_name,
        "total_rows": len(orig_df),
        "changed_rows": len(changed),
        "sample": sample,
    }
    return jsonify(result)


@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_frontend(path: str):
    if path and (BASE_DIR / "static" / path).exists():
        return app.send_static_file(path)
    return app.send_static_file("index.html")


if __name__ == "__main__":
    ensure_storage()
    app.run(debug=True, port=5000)
