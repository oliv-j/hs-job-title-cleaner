import pytest

from job_title_cleaning import clean_job_title


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("Other - Microbilogist", "Microbiologist"),  # prefix removal + full-string typo fix
        ("Lead Sientist", "Lead Scientist"),  # partial typo fix with boundary
        ("Scientist 2ND", "Scientist 2nd"),  # ordinal suffix normalisation
        ("Prof anna", "Professor Anna"),  # trailing-space abbreviation expansion
        ("Senior_Tech", "Senior Technician"),  # underscore swap before abbreviations
        ("Biotech Lead", "Biotech Lead"),  # ensure Tech replacement is boundary-scoped
    ],
)
def test_new_cleaning_rules(raw, expected):
    assert clean_job_title(raw) == expected
