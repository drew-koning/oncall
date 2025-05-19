# This file contains helper classes for managing teachers and their schedules.
import wx.grid as gridlib


class Teacher:
    """ Class to manage instances of a teacher in the context of creating the on call schedule"""
    def __init__(self, name, period1, period2, period3, period4, oncalls=0, available=None, active=True, id=None):
        self.id = id
        self.name = name
        self.period1 = period1
        self.period2 = period2
        self.period3 = period3
        self.period4 = period4
        self.oncalls = oncalls
        if available:
            self.available = available
        else:
            self.available = self.find_available_period()
        self.active = active

    def find_available_period(self):
        """Find the first available period for the teacher."""
        periodList = [self.period1, self.period2, self.period3, self.period4]
        # If there is only one None period, it means the teacher is full time and the one non-working period
        # is the avaiable period
        if periodList.count(None) == 1:
            if not self.period1:
                return 1
            elif not self.period2:
                return 2
            elif not self.period3:
                return 3
            elif not self.period4:
                return 4
            else:
                return None
        elif periodList.count(None) > 1:
            # When there is more than one non-working period, the teacher isn't full time
            # Find the first non-None period and attach the aviable period to the other side 
            # of the either AM or PM block of the day
            workingPeriod=None
            for i in range(len(periodList)):
                if periodList[i]:
                    workingPeriod = i
                    break
            if workingPeriod == 0 and not self.period2:
                return 2
            elif workingPeriod == 0 and not self.period3:
                return 3
            elif workingPeriod == 0 and not self.period4:
                return 4
            elif workingPeriod == 1 and not self.period1:
                return 1
            elif workingPeriod == 1 and not self.period3:
                return 3
            elif workingPeriod == 1 and not self.period4:
                return 4
            elif workingPeriod == 2 and not self.period4:
                return 4
            elif workingPeriod == 2 and not self.period2:
                return 2
            elif workingPeriod == 2 and not self.period1:
                return 1
            elif workingPeriod == 3 and not self.period3:
                return 3
            elif workingPeriod == 3 and not self.period1:       
                return 1
            else:
                return None
        else:
            return None

    def deactivate(self):
        """Deactivate the teacher."""
        self.available = None
        self.period1 = None
        self.period2 = None
        self.period3 = None
        self.period4 = None
        self.active = False

    def __repr__(self):
        return f"Teacher(name={self.name}: Free period={self.available})"
    

class TeacherList:
    def __init__(self):
        self.teachers = []
        self.index = 0

    def add_teacher(self, teacher):
        self.teachers.append(teacher)

    def remove_teacher(self, teacher):
        self.teachers.remove(teacher)

    def get_teachers(self):
        return self.teachers
    
    def __iter__(self):
        self.index = 0
        return self
    
    def __next__(self):
        if self.index < len(self.teachers):
            teacher = self.teachers[self.index]
            self.index += 1
            return teacher
        else:
            raise StopIteration
        
class OnCall:
    def __init__(self, teacher_id: int, date: str, year: str, period:str, half:str) -> None:
        self.teacher_id = teacher_id
        self.date = date
        self.year = year
        self.period = period
        self.half = half
    
    def __eq__(self, other):
        if not isinstance(other, OnCall):
            return NotImplemented
        return (
            self.teacher_id == other.teacher_id and
            self.date == other.date and
            self.period == other.period and
            self.half == other.half
        )

    def __repr__(self):
        return f"OnCall({self.teacher_id}, {self.date}, {self.period}, {self.half})"
        

class OnCallSchedule:
    def __init__(self):
        self.schedule = []


    def add_oncall(self, oncall: OnCall) -> int:
        if oncall not in self.schedule:
            self.schedule.append(oncall)
            return 0
        return 1

    def remove_oncall(self, oncall: OnCall) -> int:
        try:
            self.schedule.remove(oncall)
            return 0
        except ValueError:
            return 1
    

    def get_schedule(self):
        return self.schedule
    

class UnfilledAbsences:
    def __init__(self):
        self.absences = []

    def add_absence(self, date, teacher):
        self.absences.append((date, teacher))

    def remove_absence(self, date, teacher):
        self.absences.remove((date, teacher))

    def get_absences(self):
        return self.absences
    

class CustomGridTable(gridlib.GridTableBase):
    def __init__(self, data):
        super().__init__()
        self.data = data
        self.col_labels = ["ID", "Name", "Period 1", "Period 2", "Period 3", "Period 4", "All Day"]
        self.attr_bool = gridlib.GridCellAttr()
        self.attr_bool.SetEditor(OneClickBoolEditor())
        self.attr_bool.SetRenderer(gridlib.GridCellBoolRenderer())
    

    def GetNumberRows(self):
        return len(self.data)

    def GetNumberCols(self):
        return len(self.data[0]) if self.data else 0

    def GetValue(self, row, col):
        val = self.data[row][col]
        return val 

    def SetValue(self, row, col, value):
        self.data[row][col] = value

    def IsEmptyCell(self, row, col):
        return False

    def GetColLabelValue(self, col):
        return self.col_labels[col]

    def CanGetValueAs(self, row, col, typeName):
        if isinstance(self.data[row][col], bool):
            return typeName == "bool"
        return False

    def CanSetValueAs(self, row, col, typeName):
        return self.CanGetValueAs(row, col, typeName)
    
class OneClickBoolEditor(gridlib.GridCellBoolEditor):
    def BeginEdit(self, row, col, grid):
        super().BeginEdit(row, col, grid)
        self.StartingClick()  # Triggers edit immediately