import pytest
from unittest.mock import patch
from oncall import helper_classes


mock_teachers = [
    [1,'teacher1','MFM2PE-02 (S-202) ','PPL1OE-04 (GYM) ','','PPL1/2/3/4OE-02 (GYM)',3,1],
    [2,'teacher2','','TMJ2OE-02 (T-101) ','TMJ3/4CE-02 (T-101)','TIJ1OE-02  (T-101)  ',1,1],
    [3,'teacher3','MCV/MDM4UQ-01 (S-204) ','MTH1WE-02 (S-204) ','MPM2DE-02 (S-204) ','',4,1],
    [4,'teacher4','Literacy','','CHA3UE-01 (G-202)  ','CHC2DE-02 (G-202) ',None,1],
    [5,'teacher5','ST/GP/ID/RCR-05 (I-102)  ','ST/GP/ID/RCR-06 (I-102)  ','PAF1/2/3/4OE-02 (GYM)','',4,1],
    [6,'teacher6','','NBE3CE-02  (G-206)  ','ST/GP/ID/RCR-07 (I-102)  ','ST/GP/ID/RCR-08 (I-102)  ',1,1],
    [7,'teacher7','SPH3U/4CE-01 (S-203)  ','','SCH3/4UE-02 (S-203)   ','SPH3/4UE-01 (S-203)   ',2,1],
    [8,'teacher8','KPPDNE-02 (B-108)','','KPHDNE-02 (B-108)','KGLDNE-02 (B-108)',2,1],
    [9,'teacher9','PPL2OE-02 (GYM)  ','PAF2/3/4OE-03 (GYM) ','','SNC2DE-02 (S-208)',3,1],
]

mock_absences = [
    ("2025-05-26", 1, 1, 0, 0, 0),  # period1 only
    ("2025-05-26", 2, 0, 1, 0, 0),  # period2 only
]

@pytest.fixture
def oncall_instance():
    return helper_classes.OnCall(5, "20250526", "2024/2025", "period1", "1st")


@pytest.fixture
def oncall_schedule_instance():
    return helper_classes.OnCallSchedule("20250526")

@patch("oncall.helper_classes.logic.get_unfilled_absences", return_value=mock_absences)
@patch("oncall.helper_classes.logic.get_available_teachers", return_value=mock_teachers)
@patch("oncall.helper_classes.logic.get_school_year", return_value="2024/2025")
def test_schedule_oncalls(mock_year, mock_teachers_func, mock_absences_func):
    instance = helper_classes.OnCallSchedule("20250526")
    instance.schedule_oncalls()
    assert instance.unfilled_absences == [
    ("2025-05-26", 1, 1, 0, 0, 0),  # period1 only
    ("2025-05-26", 2, 0, 1, 0, 0),  # period2 only
]
    assert instance.get_schedule() == [
        helper_classes.OnCall(2, '20250526', '2024/2025', 'period1', '1st'), 
        helper_classes.OnCall(6, '20250526', '2024/2025', 'period1', '2nd'), 
        helper_classes.OnCall(7, '20250526', '2024/2025', 'period2', '1st'), 
        helper_classes.OnCall(8, '20250526', '2024/2025', 'period2', '2nd')
]

def test_add_oncall(oncall_schedule_instance: helper_classes.OnCallSchedule, oncall_instance: helper_classes.OnCall):
    assert oncall_schedule_instance.add_oncall(oncall_instance) == 0
    assert oncall_schedule_instance.add_oncall(oncall_instance) == 1

def test_remove_oncall(oncall_schedule_instance: helper_classes.OnCallSchedule, oncall_instance: helper_classes.OnCall):
    oncall_schedule_instance.add_oncall(oncall_instance)
    assert oncall_schedule_instance.remove_oncall(oncall_instance) == 0

