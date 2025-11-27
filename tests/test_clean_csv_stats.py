import csv
from pathlib import Path

from job_title_cleaning import clean_csv_file


def test_clean_csv_file_stats(tmp_path: Path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"

    rows = [
        ["CTO"],  # good
        ["cto"],  # cleaned to CTO (counts as cleaned)
        ["aaaa"],  # removed (junk)
        ["n/a"],  # removed (junk)
    ]
    with input_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Original Job Title"])
        writer.writerows(rows)

    _, stats = clean_csv_file(input_path, output_path)

    assert stats["total_rows"] == 4
    assert stats["good"] == 1
    assert stats["cleaned"] == 1
    assert stats["removed"] == 2

    with output_path.open() as f:
        lines = list(csv.reader(f))
    header = lines[0]
    assert header == ["Index", "Original Job Title", "Cleaned Job Title", "Has Changed"]
    # first row unchanged
    assert lines[1][-1] == "False"
    # second row cleaned -> True
    assert lines[2][-1] == "True"
