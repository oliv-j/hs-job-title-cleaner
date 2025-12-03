import re
import html
import unicodedata
from pathlib import Path
import pandas as pd

phone_pattern = re.compile(r'^\+?[0-9()\s\-]{7,}$')
roman_pattern = re.compile(r'(\b[A-Za-z]+[ -])(i{1,3}|iv|vi{1,3}|ix)\b', re.IGNORECASE)
email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.IGNORECASE)
non_latin_pattern = re.compile(r'[^\x00-\x7F]')
punct_only_pattern = re.compile(r'[-_. \u2013\u2014]+$')

junk_values = {
    "job", "job title",
    "test", "n/a", "none", "unknown", "???", "---", "-", "_", "zzz", "vmeinupi", "vivvixza",
    "vivvviio", "vkodhyqc", "aaa", "aaaa", "aaaaa", "aaaaaa", "aaaaaaaab", "aaaaaaaaab",
    "abc", "youknowwho", "who?", "no", "no response", "no title", "nobody", "no job title",
    "nil", "na", "aa", "abcf", "all", "ddf", "dff", "do", "dude", "hh", "mr", "other", "4a",
    "god", "miss", "self", "xs", "xx", "xxx", "yes", "sale", "team", "temp", "staff",
    "troublemaker", "testing", "wage earner",
}

preserve_caps = {"IS", "IT", "IR", "IP", "PI", "PM", "PR", "PhD", "VP", "AIO", "AIOS", "APHL", "MD"}
lower_middle_words = {"the", "at", "of", "in", "de", "en", "on"}
def high_noise_ratio(text: str) -> bool:
    total = len(text)
    if total <= 5:
        return False
    non_letters = sum(1 for ch in text if not (ch.isalpha() or ch.isspace()))
    return (non_letters / total) > 0.75

translation_map = {
    "业务员": "Salesperson",
    "主任": "Director",
    "主管": "Manager",
    "兽医师": "Veterinarian",
    "内勤": "Supervisor",
    "副主任": "Deputy director",
    "副所长": "Deputy institute director",
    "副教授": "Associate professor",
    "副研": "Research associate",
    "副總": "Vice president",
    "副组长": "Deputy group leader",
    "副院长": "Deputy dean",
    "助教": "Teaching assistant",
    "助理": "Assistant",
    "助研": "Research assistant",
    "医师": "Physician",
    "医師": "Physician",
    "医生": "Doctor",
    "博后": "Postdoctoral researcher",
    "博士": "PhD",
    "博士后": "Postdoctoral researcher",
    "博士生": "PhD student",
    "员工": "Employee",
    "商务": "Business",
    "営業": "Sales",
    "学员": "Student",
    "学士": "Bachelor's degree holder",
    "学生": "Student",
    "學生": "Student",
    "实习生": "Intern",
    "实验员": "Laboratory technician",
    "实验师": "Laboratory technologist",
    "工程师": "Engineer",
    "市场": "Marketing",
    "干部": "Cadre",
    "待业": "Unemployed",
    "总监": "Director",
    "总经理": "General manager",
    "所长": "Director",
    "技师": "Technician",
    "技术": "Technology",
    "技术员": "Technician",
    "技术岗": "Technical post",
    "技術員": "Technician",
    "提取": "Extraction",
    "教室": "Classroom",
    "教师": "Teacher",
    "教授": "Professor",
    "本科生": "Undergraduate student",
    "检测员": "Inspector",
    "检验": "Testing",
    "检验员": "Laboratory tester",
    "检验师": "Laboratory technologist",
    "检验科": "Laboratory department",
    "法人": "Legal representative",
    "测序": "Sequencing",
    "研助": "Research assistant",
    "研发": "Research and development",
    "研发员": "R&D staff",
    "研究员": "Researcher",
    "研究員": "Researcher",
    "研究生": "Graduate student",
    "研究者": "Researcher",
    "研究院": "Research institute",
    "硕士生": "Master's student",
    "社員": "Employee",
    "科员": "Section staff",
    "科学家": "Scientist",
    "科研": "Scientific research",
    "科研员": "Research staff",
    "科长": "Section chief",
    "管理员": "Administrator",
    "系主任": "Department head",
    "组长": "Team leader",
    "经理": "Manager",
    "老师": "Teacher",
    "职工": "Employee",
    "药剂师": "Pharmacist",
    "董事长": "Chairman",
    "行政": "Administration",
    "讲师": "Lecturer",
    "購物員": "Purchasing staff",
    "購買": "Purchasing",
    "醫檢師": "Medical laboratory scientist",
    "采购": "Purchasing",
    "采购员": "Purchasing staff",
    "销售": "Sales",
}

abbreviation_map = {
    "adiunct": "Adiunct professor",
    "adiunkt": "Adiunct professor",
    "adj. prof, pi": "Adiunct professor, principal investigator",
    "avp": "Assistant vice president",
    "bdm": "Business development manager",
    "bio": "Biologist",
    "cao": "Chief analytics officer",
    "cbo": "Chief business officer",
    "cco": "Chief commercial officer",
    "cdo": "Chief data officer",
    "ceo": "Chief executive officer",
    "cfo": "Chief financial officer",
    "cio": "Chief information officer",
    "cls": "Clinical laboratory scientist",
    "cma": "Certified management accountant",
    "cmo": "Chief medical officer",
    "coo": "Chief operating officer",
    "cpo": "Chief product officer",
    "crc": "Clinical research coordinator",
    "cro": "Chief research officer",
    "csm": "Customer success manager",
    "cso": "Chief scientific officer",
    "cta": "Clinical trial associate",
    "cto": "Chief technical/technology officer",
    "cts": "Clinical trial specialist",
    "dev": "Developer",
    "dir": "Director",
    "doc": "Doctor",
    "dr": "Doctor / Doctorate",
    "dr.": "Doctor / Doctorate",
    "dvm": "Doctor of veterinary medicine",
    "eir": "Entrepreneur in residence",
    "eng": "Engineer",
    "gm": "General manager",
    "gp": "General practitioner",
    "ing": "Engineer",
    "inv": "Investigator",
    "it": "Information technology",
    "lab": "Laboratory",
    "m.d": "M.D",
    "m.d.": "M.D",
    "mai": "MAI",
    "md": "MD",
    "mgr": "Manager",
    "mla": "Medical laboratory assistant",
    "mls": "Medical laboratory scientist",
    "mlt": "Medical laboratory technologist",
    "msl": "Medical science liaison",
    "ned": "Non-executive director",
    "p i": "Principal investigator",
    "pa": "Physician assistant",
    "pdra": "Postdoctoral research associate",
    "pdrf": "Postdoctoral research fellow",
    "phd": "Doctor of philosophy",
    "pi": "Primary investigator",
    "pm": "Project manager",
    "pmo": "Project management office",
    "pr": "Professor",
    "prof": "Professor",
    "ps": "Project manager",
    "qa": "QA / QC / QM",
    "qc": "QA / QC / QM",
    "qm": "QA / QC / QM",
    "r&d": "Research and development",
    "r&amp;d": "Research and development",
    "ra": "Research assistant",
    "ra1": "Research assistant 1",
    "ra2": "Research assistant 2",
    "rco": "Research contracts officer",
    "res": "Researcher",
    "rse": "Research software engineer",
    "sci": "Scientist",
    "sra": "Senior research associate",
    "sro": "Senior research officer",
    "sso": "Senior scientific officer",
    "ste": "Senior test engineer",
    "stu": "Student",
    "svp": "Senior vice president",
    "tam": "Technical account manager",
    "tas": "Technical assistant",
    "tea": "Teacher",
    "tec": "Technician",
    "tech": "Technician",
    "tmm": "Technical marketing manager",
    "tsm": "Technical support manager",
    "tss": "Technical support specialist",
    "vgm": "Vice general manager",
    "vp": "Vice president",
}

def remove_diacritics(s):
    n = unicodedata.normalize('NFD', s)
    return ''.join(ch for ch in n if unicodedata.category(ch) != 'Mn')

def roman_to_upper(m):
    return m.group(1) + m.group(2).upper()

def strip_edge_punctuation(t):
    if not t:
        return t
    pairs = {"(": ")", "[": "]", "{": "}", "<": ">"}
    # If we see a bracket opener at start or closer at end, do not drop it; just trim outside.
    left = t[0] in pairs
    right = any(t.endswith(v) for v in pairs.values())
    if left or right:
        return t.strip(' \t\n\r"\'`“”‘’.,;:!?-')
    # No brackets, fall back to generic trim.
    t = re.sub(r'^[\s"\'`“”‘’.,;:!?()\[\]{}<>-]+', '', t)
    t = re.sub(r'[\s"\'`“”‘’.,;:!?()\[\]{}<>-]+$', '', t)
    return t

def clean_job_title_with_reason(title):
    if not isinstance(title, str):
        return None, "non_string"

    t = html.unescape(title.strip())
    t = strip_edge_punctuation(t)
    t = re.sub(r'^"(.*)"$', r'\1', t)
    t = re.sub(r'^`+', '', t)
    t = re.sub(r'"{2,}', '', t)
    t = remove_diacritics(t)
    t = email_pattern.sub('', t).strip()
    if not t:
        return None, "empty"

    translated = translation_map.get(t.lower())
    if translated is not None:
        t = translated

    # Preserve non-Latin content but flag it for downstream filtering.
    if non_latin_pattern.search(t):
        return t, "non_latin_preserved"

    if phone_pattern.fullmatch(t):
        return None, "phone_like"
    if t.isdigit():
        return None, "numeric"
    if punct_only_pattern.fullmatch(t):
        return None, "punct_only"
    if len(t) == 1:
        return None, "too_short"
    if t.lower() in junk_values:
        return None, "junk_value"

    expanded = abbreviation_map.get(t.lower())
    if expanded is not None:
        t = expanded

    t = roman_pattern.sub(roman_to_upper, t)

    words = t.split()
    final = []
    total = len(words)
    for idx, w in enumerate(words):
        lower_w = w.lower()
        if 0 < idx < total - 1 and lower_w in lower_middle_words:
            final.append(lower_w)
            continue
        if w.isupper() or w.upper() in preserve_caps:
            final.append("PhD" if lower_w == "phd" else w.upper())
        else:
            final.append("PhD" if lower_w == "phd" else w.title())
    t = ' '.join(final)

    t = re.sub(r'\s*\|\s*', ', ', t)
    t = re.sub(r'(\b\w{4,}\b)\s*/\s*(\b\w{4,}\b)', r'\1 / \2', t)

    def replace_and(m):
        return f"{m.group(1)} and {m.group(2)}"
    t = re.sub(r'(\b\w+)\s+And\s+(\w+\b)', replace_and, t)

    t = re.sub(r'\bPost Doc\b', 'Post Doc', t, flags=re.IGNORECASE)
    # Final light trim of edge punctuation/spaces (do not alter bracket pairs already handled).
    t = re.sub(r'^[\s"\'`“”‘’.,;:!?-]+', '', t)
    t = re.sub(r'[\s"\'`“”‘’.,;:!?-]+$', '', t)
    if t and high_noise_ratio(t):
        return None, "non_letter_ratio"
    return (t or None), ("" if t else "invalid_final")


def clean_job_title(title):
    cleaned, _ = clean_job_title_with_reason(title)
    return cleaned


def clean_csv_file(input_csv, output_csv):
    """
    Clean a CSV file and write output with index, original, cleaned, change flag, removed, and removed reason columns.
    Returns (output_path, stats).
    """
    input_path = Path(input_csv)
    output_path = Path(output_csv)

    df = pd.read_csv(input_path, dtype=str, keep_default_na=False)
    if df.empty:
        raise ValueError("Uploaded file is empty")

    if "Original Job Title" in df.columns:
        col_to_clean = "Original Job Title"
    elif "Job Title" in df.columns:
        df.rename(columns={"Job Title": "Original Job Title"}, inplace=True)
        col_to_clean = "Original Job Title"
    else:
        first_col = df.columns[0]
        df.rename(columns={first_col: "Original Job Title"}, inplace=True)
        col_to_clean = "Original Job Title"
    stats = {"total_rows": 0, "good": 0, "cleaned": 0, "removed": 0}

    cleaned_series = []
    changed_flags = []
    removed_values = []
    removed_reasons = []
    for val in df[col_to_clean]:
        stats["total_rows"] += 1
        original = "" if not isinstance(val, str) else val.strip()
        cleaned, removed_reason = clean_job_title_with_reason(original)
        if cleaned is None or cleaned == "":
            stats["removed"] += 1
            cleaned_series.append("")
            changed_flags.append(True)
            removed_values.append(original)
            removed_reasons.append(removed_reason or "removed")
        elif removed_reason == "non_latin_preserved":
            stats["good"] += 1
            cleaned_series.append(cleaned)
            changed_flags.append(False)
            removed_values.append("")
            removed_reasons.append(removed_reason)
        elif cleaned == original:
            stats["good"] += 1
            cleaned_series.append(cleaned)
            changed_flags.append(False)
            removed_values.append("")
            removed_reasons.append("")
        else:
            stats["cleaned"] += 1
            cleaned_series.append(cleaned)
            changed_flags.append(True)
            removed_values.append("")
            removed_reasons.append("")

    output_df = pd.DataFrame(
        {
            "Index": range(1, len(df) + 1),
            "Original Job Title": df[col_to_clean],
            "Cleaned Job Title": cleaned_series,
            "Has Changed": changed_flags,
            "Removed": removed_values,
            "Removed Reason": removed_reasons,
        }
    )

    output_df["Cleaned Job Title"] = output_df["Cleaned Job Title"].fillna("")
    output_df["Removed"] = output_df["Removed"].fillna("")
    output_df["Removed Reason"] = output_df["Removed Reason"].fillna("")
    output_df.to_csv(
        output_path,
        index=False,
        encoding="utf-8-sig",  # BOM for better Excel compatibility
        columns=["Index", "Original Job Title", "Cleaned Job Title", "Has Changed", "Removed", "Removed Reason"],
    )
    return output_path, stats


if __name__ == "__main__":
    input_csv = "job_titles.csv"
    output_csv = "cleaned_job_titles.csv"

    _, stats = clean_csv_file(input_csv, output_csv)
    print(f"Done! Cleaned output written to {output_csv}. Stats: {stats}")
