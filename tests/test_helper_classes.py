import pytest
from oncall import helper_classes



@pytest.fixture
def oncall_instance():
    return helper_classes.OnCall(5, "20250526", "2024/2025", "period1", "1st")

@pytest.fixture
def oncall_schedule_instance():
    return helper_classes.OnCallSchedule()

def test_add_oncall(oncall_schedule_instance: helper_classes.OnCallSchedule, oncall_instance: helper_classes.OnCall):
    assert oncall_schedule_instance.add_oncall(oncall_instance) == 0
    assert oncall_schedule_instance.add_oncall(oncall_instance) == 1

def test_remove_oncall(oncall_schedule_instance: helper_classes.OnCallSchedule, oncall_instance: helper_classes.OnCall):
    oncall_schedule_instance.add_oncall(oncall_instance)
    assert oncall_schedule_instance.remove_oncall(oncall_instance) == 0

