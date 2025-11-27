import re
import html
import unicodedata
from pathlib import Path
import pandas as pd

phone_pattern = re.compile(r'^\+?[0-9()\s\-]{7,}$')
roman_pattern = re.compile(r'(\b[A-Za-z]+[ -])(i{1,3}|iv|vi{1,3}|ix)\b', re.IGNORECASE)
email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.IGNORECASE)

junk_values = {
    "job", "job title",
    "test", "n/a", "none", "unknown", "???", "---", "-", "_", "zzz", "vmeinupi", "vivvixza",
    "vivvviio", "vkodhyqc", "aaa", "aaaa", "aaaaa", "aaaaaa", "aaaaaaaab", "aaaaaaaaab",
    "abc", "youknowwho", "who?", "no", "no response", "no title", "nobody", "no job title",
    "nil", "na"
}

preserve_caps = {"IS", "IT", "IR", "IP", "PI", "PM", "PR", "PhD", "VP", "AIO", "AIOS", "APHL"}

def remove_diacritics(s):
    n = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in n if unicodedata.category(ch) != 'Mn')

def roman_to_upper(m):
    return m.group(1) + m.group(2).upper()

def clean_job_title(title):
    if not isinstance(title, str):
        return None
    t = html.unescape(title.strip())
    t = re.sub(r'^[,\-–¨\s]+', '', t)
    t = re.sub(r'^"(.*)"$', r'\1', t)
    t = re.sub(r'^\((.*)\)$', r'\1', t)
    t = re.sub(r'^`+', '', t)
    t = re.sub(r'"{2,}', '', t)
    t = remove_diacritics(t)
    t = email_pattern.sub('', t).strip()

    if phone_pattern.fullmatch(t) or t.isdigit() or re.fullmatch(r'[-_. ]+', t) or len(t) == 1:
        return None
    if t.lower() in junk_values:
        return None
    t = roman_pattern.sub(roman_to_upper, t)

    words = t.split()
    final = []
    for w in words:
        if w.isupper() or w.upper() in preserve_caps:
            final.append("PhD" if w.lower() == "phd" else w.upper())
        else:
            final.append("PhD" if w.lower() == "phd" else w.title())
    t = ' '.join(final)

    t = re.sub(r'\s*\|\s*', ', ', t)
    t = re.sub(r'(\b\w{4,}\b)\s*/\s*(\b\w{4,}\b)', r'\1 / \2', t)

    def replace_and(m):
        return f"{m.group(1)} and {m.group(2)}"
    t = re.sub(r'(\b\w+)\s+And\s+(\w+\b)', replace_and, t)

    t = re.sub(r'\bPost Doc\b', 'Post Doc', t, flags=re.IGNORECASE)
    return t or None


def clean_csv_file(input_csv, output_csv):
    """
    Clean a CSV file and write output with index, original, cleaned, and change flag columns.
    Returns (output_path, stats).
    """
    input_path = Path(input_csv)
    output_path = Path(output_csv)

    df = pd.read_csv(input_path)
    if df.empty:
        raise ValueError("Uploaded file is empty")

    if "Job Title" in df.columns and "Original Job Title" not in df.columns:
        df.rename(columns={"Job Title": "Original Job Title"}, inplace=True)

    col_to_clean = "Original Job Title" if "Original Job Title" in df.columns else df.columns[0]
    stats = {"total_rows": 0, "good": 0, "cleaned": 0, "removed": 0}

    cleaned_series = []
    changed_flags = []
    for val in df[col_to_clean]:
        stats["total_rows"] += 1
        original = "" if not isinstance(val, str) else val.strip()
        cleaned = clean_job_title(original)
        if cleaned is None or cleaned == "":
            stats["removed"] += 1
            cleaned_series.append("")
            changed_flags.append(True)
        elif cleaned == original:
            stats["good"] += 1
            cleaned_series.append(cleaned)
            changed_flags.append(False)
        else:
            stats["cleaned"] += 1
            cleaned_series.append(cleaned)
            changed_flags.append(True)

    df["Cleaned Job Title"] = cleaned_series
    df["Has Changed"] = changed_flags

    if "Index" not in df.columns:
        df.insert(0, "Index", range(1, len(df)+1))

    df["Cleaned Job Title"] = df["Cleaned Job Title"].fillna("")
    df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",  # BOM for better Excel compatibility
        columns=["Index", col_to_clean, "Cleaned Job Title", "Has Changed"],
    )
    return output_path, stats


if __name__ == "__main__":
    input_csv = "job_titles.csv"
    output_csv = "cleaned_job_titles.csv"

    _, stats = clean_csv_file(input_csv, output_csv)
    print(f"Done! Cleaned output written to {output_csv}. Stats: {stats}")
