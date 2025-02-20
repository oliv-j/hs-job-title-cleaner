import re
import html
import unicodedata

phone_pattern = re.compile(r'^\+?[0-9()\s\-]{7,}$')
roman_pattern = re.compile(r'(\b[A-Za-z]+[ -])(i{1,3}|iv|vi{1,3}|ix)\b', re.IGNORECASE)
email_pattern = re.compile(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', re.IGNORECASE)

junk_values = {
    "job", "job title", "test", "n/a", "none", "unknown", "???", "---", "-", "_", "zzz", "vmeinupi", "vivvixza",
    "vivvviio", "vkodhyqc", "aaa", "aaaa", "aaaaa", "aaaaaa", "aaaaaaaab", "aaaaaaaaab", "abc", "youknowwho",
    "who?", "no", "no response", "no title", "nobody", "no job title", "nil", "na"
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

    # Unescape HTML & strip whitespace
    t = html.unescape(title.strip())

    # Remove leading punctuation/symbols (including ¨)
    t = re.sub(r'^[,\-–¨\s]+', '', t)

    # Remove enclosing quotes/parentheses
    t = re.sub(r'^"(.*)"$', r'\1', t)
    t = re.sub(r'^\((.*)\)$', r'\1', t)
    # Remove backticks & repeated quotes
    t = re.sub(r'^`+', '', t)
    t = re.sub(r'"{2,}', '', t)

    # Remove diacritics
    t = remove_diacritics(t)

    # Remove emails
    t = email_pattern.sub('', t).strip()

    # Check phone / numeric / short
    if phone_pattern.fullmatch(t) or t.isdigit() or re.fullmatch(r'[-_. ]+', t) or len(t) == 1:
        return None

    # Junk
    if t.lower() in junk_values:
        return None

    # Roman numerals
    t = roman_pattern.sub(roman_to_upper, t)

    # Convert to words, preserve uppercase acronyms
    words = t.split()
    final_words = []
    for w in words:
        if w.isupper() or w.upper() in preserve_caps:
            final_words.append("PhD" if w.lower() == "phd" else w.upper())
        else:
            final_words.append("PhD" if w.lower() == "phd" else w.title())
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

    return t or None


def main(event):
    try:
        job_title = event["inputFields"].get("jobTitle", "")
        cleaned = clean_job_title(job_title)
        final = cleaned if cleaned is not None else ""

        if final != job_title:
            hs_state = "Succeeded"
            outcome = "success"
        else:
            hs_state = "Failed, object removed from workflow"
            outcome = "no_change"

        return {
            "outputFields": {
                "newTitle": final,
                "hs_execution_state": hs_state,
                "outcome": outcome
            }
        }

    except Exception:
        return {
            "outputFields": {
                "newTitle": "",
                "hs_execution_state": "Failed, object removed from workflow",
                "outcome": "error"
            }
        }
