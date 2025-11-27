import importlib.machinery
import importlib.util
from pathlib import Path

import pytest


def load_custom_code():
    """Load custom-code.py despite the hyphen in its filename."""
    path = Path(__file__).resolve().parent.parent / "custom-code.py"
    loader = importlib.machinery.SourceFileLoader("custom_code", str(path))
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


custom_code = load_custom_code()


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("博士", "Doctor Of Philosophy"),
        ("博士后", "Postdoctoral Researcher"),
        ("R&D", "Research and Development"),
        ("PI", "Primary Investigator"),
        ('"Title".', "Title"),
        ("mr", None),
        ("副研", "Research Associate"),
        ("Adj. prof, PI", "Adiunct Professor, Principal Investigator"),
    ],
)
def test_clean_job_title_cases(raw, expected):
    assert custom_code.clean_job_title(raw) == expected


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
    assert output["error_state"] == 0


def test_main_invalid_passes_original():
    event = {"inputFields": {"jobTitle": "mr"}}
    output = custom_code.main(event)["outputFields"]
    assert output["newTitle"] == "mr"  # cleaned is None; pass-through original
    assert output["outcome"] == "no_change"
    assert output["error_state"] == 0


def test_main_handles_exception():
    # Force an exception by passing a non-dict inputFields
    event = {"inputFields": None}
    output = custom_code.main(event)["outputFields"]
    assert output["outcome"] == "error"
    assert output["error_state"] == 1
    assert output["newTitle"] == ""
