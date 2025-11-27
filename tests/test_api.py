import io
import json
import os
from pathlib import Path

import pytest


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setenv("JOBS_DIR", str(tmp_path / "jobs"))
    from app import app  # import after setting env

    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def upload_sample(client):
    data = "Original Job Title\ncto\nn/a\nCEO\n"
    return client.post(
        "/api/upload",
        data={"file": (io.BytesIO(data.encode()), "sample.csv")},
        content_type="multipart/form-data",
    )


def test_upload_and_stats(client):
    resp = upload_sample(client)
    assert resp.status_code == 200
    payload = resp.get_json()
    assert payload["job"]["status"] == "complete"
    stats = payload["job"]["stats"]
    assert stats["good"] == 1  # CEO unchanged
    assert stats["cleaned"] == 1  # cto -> CTO
    assert stats["removed"] == 1  # n/a removed


def test_jobs_listing(client):
    resp = upload_sample(client)
    job_name = resp.get_json()["job"]["name"]

    list_resp = client.get("/api/jobs")
    assert list_resp.status_code == 200
    jobs = list_resp.get_json()["jobs"]
    assert any(j["name"] == job_name for j in jobs)


def test_validate_endpoint(client):
    resp = upload_sample(client)
    job_name = resp.get_json()["job"]["name"]

    val_resp = client.get(f"/api/validate/{job_name}")
    assert val_resp.status_code == 200
    data = val_resp.get_json()
    assert data["job"] == job_name
    assert data["changed_rows"] >= 1
    assert isinstance(data.get("sample"), list)
