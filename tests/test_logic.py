import pytest
from oncall import logic


def test_get_school_year():
    assert logic.get_school_year("20250516") == "2024/2025"
    assert logic.get_school_year("20250819") == "2024/2025"
    assert logic.get_school_year("20250828") == "2025/2026"
    assert logic.get_school_year("19871201") == "1987/1988"
    with pytest.raises(ValueError):
        logic.get_school_year("202505005")


@pytest.fixture
def available_teachers():
    return [
        [
            1,
            "teacher1",
            "MFM2PE-02 (S-202) ",
            "PPL1OE-04 (GYM) ",
            "",
            "PPL1/2/3/4OE-02 (GYM)",
            3,
            1,
        ],
        [
            2,
            "teacher2",
            "",
            "TMJ2OE-02 (T-101) ",
            "TMJ3/4CE-02 (T-101)",
            "TIJ1OE-02  (T-101)  ",
            1,
            1,
        ],
        [
            3,
            "teacher3",
            "MCV/MDM4UQ-01 (S-204) ",
            "MTH1WE-02 (S-204) ",
            "MPM2DE-02 (S-204) ",
            "",
            4,
            1,
        ],
        [
            4,
            "teacher4",
            "Literacy",
            "",
            "CHA3UE-01 (G-202)  ",
            "CHC2DE-02 (G-202) ",
            None,
            1,
        ],
        [
            5,
            "teacher5",
            "ST/GP/ID/RCR-05 (I-102)  ",
            "ST/GP/ID/RCR-06 (I-102)  ",
            "PAF1/2/3/4OE-02 (GYM)",
            "",
            4,
            1,
        ],
        [
            6,
            "teacher6",
            "",
            "NBE3CE-02  (G-206)  ",
            "ST/GP/ID/RCR-07 (I-102)  ",
            "ST/GP/ID/RCR-08 (I-102)  ",
            1,
            1,
        ],
        [
            7,
            "teacher7",
            "SPH3U/4CE-01 (S-203)  ",
            "",
            "SCH3/4UE-02 (S-203)   ",
            "SPH3/4UE-01 (S-203)   ",
            2,
            1,
        ],
        [
            8,
            "teacher8",
            "KPPDNE-02 (B-108)",
            "",
            "KPHDNE-02 (B-108)",
            "KGLDNE-02 (B-108)",
            2,
            1,
        ],
        [
            9,
            "teacher9",
            "PPL2OE-02 (GYM)  ",
            "PAF2/3/4OE-03 (GYM) ",
            "",
            "SNC2DE-02 (S-208)",
            3,
            1,
        ],
    ]


def test_split_available_teachers(available_teachers):
    result = logic.split_available_teachers(available_teachers)
    assert result[0] == [
        [
            2,
            "teacher2",
            "",
            "TMJ2OE-02 (T-101) ",
            "TMJ3/4CE-02 (T-101)",
            "TIJ1OE-02  (T-101)  ",
            1,
            1,
        ],
        [
            6,
            "teacher6",
            "",
            "NBE3CE-02  (G-206)  ",
            "ST/GP/ID/RCR-07 (I-102)  ",
            "ST/GP/ID/RCR-08 (I-102)  ",
            1,
            1,
        ],
    ]
    assert result[1] == [
        [
            7,
            "teacher7",
            "SPH3U/4CE-01 (S-203)  ",
            "",
            "SCH3/4UE-02 (S-203)   ",
            "SPH3/4UE-01 (S-203)   ",
            2,
            1,
        ],
        [
            8,
            "teacher8",
            "KPPDNE-02 (B-108)",
            "",
            "KPHDNE-02 (B-108)",
            "KGLDNE-02 (B-108)",
            2,
            1,
        ],
    ]
    assert result[2] == [
        [
            1,
            "teacher1",
            "MFM2PE-02 (S-202) ",
            "PPL1OE-04 (GYM) ",
            "",
            "PPL1/2/3/4OE-02 (GYM)",
            3,
            1,
        ],
        [
            9,
            "teacher9",
            "PPL2OE-02 (GYM)  ",
            "PAF2/3/4OE-03 (GYM) ",
            "",
            "SNC2DE-02 (S-208)",
            3,
            1,
        ],
    ]
    assert result[3] == [
        [
            3,
            "teacher3",
            "MCV/MDM4UQ-01 (S-204) ",
            "MTH1WE-02 (S-204) ",
            "MPM2DE-02 (S-204) ",
            "",
            4,
            1,
        ],
        [
            5,
            "teacher5",
            "ST/GP/ID/RCR-05 (I-102)  ",
            "ST/GP/ID/RCR-06 (I-102)  ",
            "PAF1/2/3/4OE-02 (GYM)",
            "",
            4,
            1,
        ],
    ]


mock_teachers = {
    1: "teacher1",
    2: "teacher2",
    3: "teacher3",
    4: "teacher4",
    5: "teacher5",
    6: "teacher6",
    7: "teacher7",
    8: "teacher8",
    9: "teacher9",
}


def test_add_names():
    data = [
        [1, "20231016", 1, 1, 0, 0, 0],
        [2, "20231016", 2, 0, 1, 0, 0],
        [3, "20231016", 3, 0, 0, 1, 0],
        [4, "20231016", 4, 0, 0, 0, 1],
    ]
    result = logic.add_names(data, mock_teachers)
    assert result[0][0] == "teacher1"
    assert result[1][0] == "teacher2"
    assert result[2][0] == "teacher3"
    assert result[3][0] == "teacher4"
