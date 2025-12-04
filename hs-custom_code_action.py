import re
import html
import unicodedata

phone_pattern = re.compile(r'^\+?[0-9()\s\-]{7,}$')
roman_pattern = re.compile(r'(\b[A-Za-z]+[ -])(i{1,3}|iv|vi{1,3}|ix)\b', re.IGNORECASE)
email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.IGNORECASE)
non_latin_pattern = re.compile(r'[^\x00-\x7F]')
punct_only_pattern = re.compile(r'[-_. \u2013\u2014]+$')

junk_values = {
    "job", "job title",
    "test", "n/a", "none", "unknown", "???", "---", "-", "_", "zzz", "vmeinupi", "vivvixza",
    "vivvviio", "vkodhyqc", "aaa", "aaaa", "aaaaa", "aaaaaa", "aaaaaaaab", "aaaaaaaaab", "abc", "youknowwho",
    "who?", "no", "no response", "no title", "nobody", "no job title", "nil", "na", "aa", "abcf", "all",
    "ddf", "dff", "do", "dude", "hh", "mr", "other", "4a", "god", "miss", "self", "xs", "xx", "xxx", "yes", "sale", "team", "temp", "staff",
    "troublemaker", "testing", "wage earner",
    "null", "none", "non", "jobtitle", "job title", "individual",
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

    # Preserve non-Latin if not translated.
    if non_latin_pattern.search(t):
        return t, "non_latin"

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

    # Roman numerals
    t = roman_pattern.sub(roman_to_upper, t)

    # Convert to words, preserve uppercase acronyms
    words = t.split()
    final_words = []
    total = len(words)
    for idx, w in enumerate(words):
        lower_w = w.lower()
        if 0 < idx < total - 1 and lower_w in lower_middle_words:
            final_words.append(lower_w)
            continue
        if w.isupper() or w.upper() in preserve_caps:
            final_words.append("PhD" if lower_w == "phd" else w.upper())
        else:
            final_words.append("PhD" if lower_w == "phd" else w.title())
    t = ' '.join(final_words)

    # Replace vertical bars
    t = re.sub(r'\s*\|\s*', ', ', t)

    # Insert spacing around slash if two 4+ letter words
    # e.g. "this/string" -> "this / string"
    t = re.sub(r'(\b\w{4,}\b)\s*/\s*(\b\w{4,}\b)', r'\1 / \2', t)

    # Lowercase "And" if between words
    def replace_and(m):
        return f"{m.group(1)} and {m.group(2)}"
    t = re.sub(r'(\b\w+)\s+And\s+(\w+\b)', replace_and, t)

    # Preserve 'Post Doc'
    t = re.sub(r'\bPost Doc\b', 'Post Doc', t, flags=re.IGNORECASE)

    t = re.sub(r'^[\s"\'`“”‘’.,;:!?-]+', '', t)
    t = re.sub(r'[\s"\'`“”‘’.,;:!?-]+$', '', t)
    if t and high_noise_ratio(t):
        return None, "non_letter_ratio"
    return (t or None), ("" if t else "invalid_final")


def clean_job_title(title):
    cleaned, _ = clean_job_title_with_reason(title)
    return cleaned


def main(event):
    try:
        job_title = event.get("inputFields", {}).get("jobTitle", "")
        if not isinstance(job_title, str):
            job_title = ""
        cleaned, reason = clean_job_title_with_reason(job_title)

        if reason == "non_latin":
            return {
                "outputFields": {
                    "newTitle": job_title,
                    "non_latin_title": job_title,
                    "outcome": "non_latin",
                    "error": "",
                    "error_message": "",
                    "error_state": 0,
                }
            }

        if cleaned is None or cleaned == "":
            return {
                "outputFields": {
                    "newTitle": "",
                    "non_latin_title": "",
                    "outcome": "removed",
                    "error": "",
                    "error_message": "",
                    "error_state": 0,
                }
            }

        changed = cleaned != job_title
        outcome = "changed" if changed else "no_change"

        return {
            "outputFields": {
                "newTitle": cleaned,
                "non_latin_title": "",
                "outcome": outcome,
                "error": "",
                "error_message": "",
                "error_state": 0,
            }
        }

    except Exception as exc:
        # Surface a minimal error payload; HubSpot will retry on raised rate-limit errors upstream.
        msg = str(exc)
        return {
            "outputFields": {
                "newTitle": "",
                "non_latin_title": "",
                "outcome": "error",
                "error": msg,
                "error_message": msg[:300],
                "error_state": 1,
            }
        }
