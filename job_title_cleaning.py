import re
import html
import unicodedata
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

if __name__ == "__main__":
    input_csv = "job_titles.csv"
    output_csv = "cleaned_job_titles.csv"

    df = pd.read_csv(input_csv)

    if "Job Title" in df.columns and "Original Job Title" not in df.columns:
        df.rename(columns={"Job Title": "Original Job Title"}, inplace=True)

    col_to_clean = "Original Job Title" if "Original Job Title" in df.columns else df.columns[0]
    df["Cleaned Job Title"] = df[col_to_clean].apply(clean_job_title)

    if "Index" not in df.columns:
        df.insert(0, "Index", range(1, len(df)+1))

    df["Cleaned Job Title"] = df["Cleaned Job Title"].fillna("")
    df.to_csv(output_csv, index=False, columns=["Index", col_to_clean, "Cleaned Job Title"])
    print(f"Done! Cleaned output written to {output_csv}.")
