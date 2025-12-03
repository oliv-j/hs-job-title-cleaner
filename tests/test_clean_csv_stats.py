import csv
from pathlib import Path

from job_title_cleaning import clean_csv_file


def test_clean_csv_file_stats(tmp_path: Path):
    input_path = tmp_path / "input.csv"
    output_path = tmp_path / "output.csv"

    rows = [
        ["CTO"],  # expanded (counts as cleaned)
        ["cto"],  # cleaned to CTO (counts as cleaned)
        ["aaaa"],  # removed (junk)
        ["n/a"],  # removed (junk)
        ["こんにちは"],  # non-Latin preserved with reason
    ]
    with input_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Original Job Title"])
        writer.writerows(rows)

    _, stats = clean_csv_file(input_path, output_path)

    assert stats["total_rows"] == 5
    assert stats["good"] == 1  # non-Latin preserved
    assert stats["cleaned"] == 2
    assert stats["removed"] == 2

    with output_path.open() as f:
        lines = list(csv.reader(f))
    header = [col.lstrip("\ufeff") for col in lines[0]]  # strip BOM on first column
    assert header == ["Index", "Original Job Title", "Cleaned Job Title", "Has Changed", "Removed", "Removed Reason"]
    # first row expanded -> changed; removed column blank
    assert lines[1][3] == "True"
    assert lines[1][4] == ""
    assert lines[1][5] == ""
    # second row cleaned -> True; removed column blank
    assert lines[2][3] == "True"
    assert lines[2][4] == ""
    assert lines[2][5] == ""
    # third row removed -> True; removed column contains original
    assert lines[3][3] == "True"
    assert lines[3][4] == "aaaa"
    assert lines[3][5] == "junk_value"
    # fourth row removed -> True; removed column contains original
    assert lines[4][3] == "True"
    assert lines[4][4].lower() == "n/a"
    assert lines[4][5] == "junk_value"
    # fifth row non-Latin preserved -> no change, reason noted
    assert lines[5][3] == "False"
    assert lines[5][4] == ""
    assert lines[5][5] == "non_latin_preserved"
