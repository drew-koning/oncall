import pytest
from oncall import logic

def test_get_school_year():
    assert logic.get_school_year("20250516") == "2024/2025"
    assert logic.get_school_year("20250819") == "2024/2025"
    assert logic.get_school_year("20250828") == "2025/2026"
    assert logic.get_school_year("19871201") == "1987/1988"
    with pytest.raises(ValueError):
        logic.get_school_year("202505005")