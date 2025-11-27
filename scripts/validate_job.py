import argparse
import pandas as pd
from pathlib import Path


def validate_job(job_name: str, jobs_dir: Path):
    job_folder = jobs_dir / job_name
    original_path = job_folder / f"{job_name}-original.csv"
    cleaned_path = job_folder / f"{job_name}-cleaned.csv"

    if not original_path.exists() or not cleaned_path.exists():
        raise FileNotFoundError(f"Missing original/cleaned CSV in {job_folder}")

    orig = pd.read_csv(original_path)
    cleaned = pd.read_csv(cleaned_path)
    merged = cleaned[["Original Job Title", "Cleaned Job Title"]]
    changed = merged[merged["Original Job Title"] != merged["Cleaned Job Title"]]

    print(f"Job: {job_name}")
    print(f"Total rows: {len(orig)}")
    print(f"Changed rows: {len(changed)}")
    print("Sample (up to 10):")
    print(changed.head(10).to_string(index=False))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate cleaned job titles for a job run.")
    parser.add_argument("job_name", help="Job name, e.g., JobTitleClean001")
    parser.add_argument("--jobs-dir", default="jobs", help="Jobs directory (default: jobs)")
    args = parser.parse_args()
    validate_job(args.job_name, Path(args.jobs_dir))
