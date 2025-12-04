import importlib.machinery
import importlib.util
from pathlib import Path

import pytest


def load_custom_code():
    """Load the HubSpot action module from hs-custom_code_action.py."""
    path = Path(__file__).resolve().parent.parent / "hs-custom_code_action.py"
    loader = importlib.machinery.SourceFileLoader("custom_code", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


custom_code = load_custom_code()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("博士", "Doctor of Philosophy"),
        ("博士后", "Postdoctoral Researcher"),
        ("R&D", "Research and Development"),
        ("PI", "Primary Investigator"),
        ('"Title".', "Title"),
        ("mr", None),
        ("Yes", None),
        ("副研", "Research Associate"),
        ("Adj. prof, PI", "Adiunct Professor, Principal Investigator"),
        ("md", "MD"),
        ("m.d.", "M.D"),
        ("VP Of Research", "VP of Research"),
        ("Technicien De Laboratoire", "Technicien de Laboratoire"),
        ("Studies On The Cultivation Of Useful Plants", "Studies on the Cultivation of Useful Plants"),
        ("Tutor & Demonstrater (Clinical Microbiologist", "Tutor & Demonstrater (Clinical Microbiologist"),
        ("Technical Specialist (Genetics", "Technical Specialist (Genetics"),
        ("Scientist II (E-T", "Scientist II (E-T"),
        ("Scientist (Project", "Scientist (Project"),
        ("Scientist (SS", "Scientist (SS"),
        ("a@@@@@@@", None),
    ],
)
def test_clean_job_title_cases(raw, expected):
    assert custom_code.clean_job_title(raw) == expected


def _is_bracket_balanced(text: str) -> bool:
    pairs = {")": "(", "]": "[", "}": "{", ">": "<"}
    stack = []
    for ch in text:
        if ch in pairs.values():
            stack.append(ch)
        elif ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
    return not stack


def test_balanced_brackets_preserved():
    cases = [
        "Technical Product Manager (Sequencing Devices)",
        "Lead Scientist [Genomics Platform]",
        "Engineer {R&D Team}",
    ]
    for raw in cases:
        cleaned = custom_code.clean_job_title(raw)
        assert _is_bracket_balanced(cleaned)


def test_main_changed():
    event = {"inputFields": {"jobTitle": "R&D"}}
    output = custom_code.main(event)["outputFields"]
    assert output["newTitle"] == "Research and Development"
    assert output["outcome"] == "changed"
    assert output["error_state"] == 0


def test_main_no_change_marks_failed():
    event = {"inputFields": {"jobTitle": "Director"}}
    output = custom_code.main(event)["outputFields"]
    assert output["newTitle"] == "Director"
    assert output["outcome"] == "no_change"
    assert output["non_latin_title"] == ""
    assert output["error_state"] == 0


def test_main_invalid_passes_original():
    event = {"inputFields": {"jobTitle": "mr"}}
    output = custom_code.main(event)["outputFields"]
    assert output["newTitle"] == ""  # cleaned is None -> removed
    assert output["non_latin_title"] == ""
    assert output["outcome"] == "removed"
    assert output["error_state"] == 0


def test_main_non_latin_preserved():
    raw = "こんにちは"
    output = custom_code.main({"inputFields": {"jobTitle": raw}})["outputFields"]
    assert output["outcome"] == "non_latin"
    assert output["newTitle"] == raw
    assert output["non_latin_title"] == raw
    assert output["error_state"] == 0


def test_main_punct_only_removed():
    raw = "—"  # em dash
    output = custom_code.main({"inputFields": {"jobTitle": raw}})["outputFields"]
    assert output["outcome"] == "non_latin"
    assert output["newTitle"] == raw
    assert output["non_latin_title"] == raw
    assert output["error_state"] == 0


def test_main_handles_exception():
    # Force an exception by passing a non-dict inputFields
    event = {"inputFields": None}
    output = custom_code.main(event)["outputFields"]
    assert output["outcome"] == "error"
    assert output["error_state"] == 1
    assert output["newTitle"] == ""
