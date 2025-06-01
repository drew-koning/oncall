import oncall.db_config as db_config
import polars as pl
from oncall.helper_classes import TeacherList, Teacher
from datetime import datetime, timedelta, date
from typing import List, Union


def load_teacher_list_from_db() -> TeacherList:
    """Load the teacher list from the SQLite database."""
    query: str = "SELECT * FROM teachers"
    paramaters: tuple = ()
    result = db_config.execute_query(query, paramaters)
    if result.success:
        teacher_list = TeacherList()
        for row in result.data:
            """Create a Teacher object from the row data and add it to the TeacherList."""
            teacher = Teacher(
                id=row[0],
                name=row[1],
                period1=row[2],
                period2=row[3],
                period3=row[4],
                period4=row[5],
            )
            teacher_list.add_teacher(teacher)
    else:
        raise Exception("Failed to load teacher list from database.")
    return teacher_list


def get_absences_from_db(date: str) -> list:
    """grab the currently active teacher list with all absences for the provided date in the
    following format teaher id, teacher name, period 1, period 2, period 3, period 4"""
    
    query: str = """
        SELECT 
            teachers.teacher_id, 
            teachers.teacher_name, 
            ua.period1, 
            ua.period2, 
            ua.period3, 
            ua.period4
        FROM teachers
        LEFT JOIN (
            SELECT * FROM unfilled_absences WHERE date = ?
        ) ua ON teachers.teacher_id = ua.teacher_id
        WHERE teachers.active = 1
        """
    params: tuple[str] =  (date,)
    result: db_config.Result = db_config.execute_query(query, params)
    if result.success:
        return [
            [
                row[0],
                row[1],
                bool(row[2]),
                bool(row[3]),
                bool(row[4]),
                bool(row[5]),
                all(row[2:]),
            ]
            for row in result.data
        ]
    else:
        raise Exception("Failed to load absences from database.")


def load_schedule_from_file(file_path: str) -> dict[str, list[Teacher]]:
    """Load a schedule from a file."""
    # Read the schedule from the provided file path
    schedule: pl.DataFrame = pl.read_excel(file_path)
    # setup and execute the query to check if the teachers already exist in the database
    query: str = "SELECT teacher_name FROM teachers"
    params: tuple = ()
    result = db_config.execute_query(query, params)

    #setup teacher lists
    update_teachers: list = []
    new_teachers: list = []
        
    if result.success:
        existing_teachers: list = [teacher[0] for teacher in result.data]
        # if teacher exists: add to  update_teachers else add to new_teachers, 
        for row in schedule.iter_rows():
            if row[0]:
                teacher: Teacher = Teacher(
                    name=row[0],
                    period1=row[1],
                    period2=row[2],
                    period3=row[4],
                    period4=row[5],
                )
                if teacher.name in existing_teachers:
                    # If the teacher already exists, add to update_teachers
                    update_teachers.append(teacher)
                else:
                    # If the teacher does not exist, add to new_teachers
                    new_teachers.append(teacher)
        updated_teacher_names: list[str] = [x.name for x in update_teachers]
        inactive_teachers: list[Teacher] = [Teacher(name) for name in existing_teachers if name not in updated_teacher_names]
    else:
        raise Exception("Failed to load existing teachers from database.")  
    return {
        "updated_teachers": update_teachers,
        "new_teachers": new_teachers,
        "inactive_teachers": inactive_teachers,
    }

def handle_new_teachers(new_teachers: List[Teacher]) -> None:
    """Handle new teachers by adding them to the database."""
    query: str = """
        INSERT INTO teachers (teacher_name, period1, period2, period3, period4)
        VALUES (?, ?, ?, ?, ?)
    """
    params: List[tuple] = [
        (teacher.name, teacher.period1, teacher.period2, teacher.period3, teacher.period4)
        for teacher in new_teachers
    ]
    result: db_config.Result = db_config.execute_query(query, params)
    if not result.success:
        raise Exception("Failed to add new teachers to the database.")
    
def handle_updated_teachers(updated_teachers: List[Teacher]) -> None:
    """Handle updated teachers by updating their information in the database."""
    query: str = """
        UPDATE teachers
        SET period1 = ?, period2 = ?, period3 = ?, period4 = ?
        WHERE teacher_name = ?
    """
    params: List[tuple] = [
        (teacher.period1, teacher.period2, teacher.period3, teacher.period4, teacher.name)
        for teacher in updated_teachers
    ]
    result: db_config.Result = db_config.execute_query(query, params)
    if not result.success:
        raise Exception("Failed to update teachers in the database.")
    
def handle_inactive_teachers(inactive_teachers: List[Teacher]) -> None:
    """Handle inactive teachers by deactivating them in the database."""
    query: str = """
        UPDATE teachers
        SET active = 0
        WHERE teacher_name = ?
    """
    params: List[tuple] = [(teacher.name,) for teacher in inactive_teachers]
    result: db_config.Result = db_config.execute_query(query, params)
    if not result.success:
        raise Exception("Failed to deactivate teachers in the database.")


def save_absences_to_db(
    date: str, teacher_absences: List[Union[str, int, bool]]
) -> None:
    """Save the absences to the database."""
    query: str = "DELETE FROM unfilled_absences WHERE date = ?"
    params: tuple = (date,)
    result: db_config.Result = db_config.execute_query(query, params)
    if not result.success:
        raise Exception("Failed to clear existing absences for the date.")
    
    params2: List[tuple] = []
    for absence in teacher_absences:
        if isinstance(absence, (list, tuple)) and len(absence) == 7:
            params2.append(
                (
                    date,
                    absence[0],  # teacher_id
                    absence[2],  # period1
                    absence[3],  # period2
                    absence[4],  # period3
                    absence[5],  # period4
                )
            )
           
    query2: str = """INSERT INTO unfilled_absences (date, teacher_id, period1, period2, period3, period4)
                        VALUES (?, ?, ?, ?, ?, ?)"""
    result2: db_config.Result = db_config.execute_query(query2, params2)
    if not result2.success:
        raise Exception("Failed to save absences to the database.")



def get_available_teachers(date: str) -> List[str]:
    """Get a list of teachers from the database who for the current day, don't have an absence"""

    query: str = """
        SELECT 
          * 
        FROM 
          teachers 
        WHERE 
          teacher_id NOT IN (
            SELECT 
              teacher_id 
            FROM 
              unfilled_absences 
            WHERE 
              date = ?
            AND
              (period1 = 1
            OR
              period2 = 1
            OR 
              period3 = 1
            OR 
              period4 =1)
          )"""
    params: tuple[str] = (date,)
    result: db_config.Result = db_config.execute_query(query, params)
    if not result.success:
        raise Exception("Failed to load available teachers from database.")
    return result.data


def current_week(day: str) -> list[str]:
    """Get the week range for the selected day (Sunday to Saturday)"""
    date_day: datetime = datetime.strptime(day, "%Y%m%d")
    weekend: int = 5 - date_day.weekday()
    if weekend < 0:
        weekend: int = 6
    weekstart: int = date_day.weekday() * -1 - 1
    if weekstart == -7:
        weekstart: int = 0
    weekend_date: str = (date_day + timedelta(weekend)).strftime("%Y%m%d")
    weekstart_date: str = (date_day + timedelta(weekstart)).strftime("%Y%m%d")
    return [weekstart_date, weekend_date]


def get_school_year(given_date: str) -> str:
    """
    Returns the school year in the format "YYYY/YYYY" for a given date.
    The school year runs from August 20 to August 19 of the next year.
    """
    if len(given_date) != 8:
        raise ValueError("Date not provided in the proper format")
    y: str = given_date[:4] 
    m: str = given_date[4:6]
    d: str = given_date[6:]
    try:
        newdate: date = date(int(y), int(m), int(d))
    except Exception:
        raise ValueError("Date not provided in the proper format")
    if newdate >= date(newdate.year, 8, 20):
        start_year: int = newdate.year
    else:
        start_year: int = newdate.year - 1

    end_year: int = start_year + 1
    return f"{start_year}/{end_year}"


def split_available_teachers(available_teachers: list) -> list[list]:
    """Separate teachers into groups by which period they are available"""
    period1: list[list] = [x for x in available_teachers if x[6] == 1]
    period2: list[list] = [x for x in available_teachers if x[6] == 2]
    period3: list[list] = [x for x in available_teachers if x[6] == 3]
    period4: list[list] = [x for x in available_teachers if x[6] == 4]
    return [period1, period2, period3, period4]


def get_unfilled_absences(date: str) -> list:
    """Returns a list of all unfilled absences listed for the current day"""
    query: str = "SELECT * FROM unfilled_absences WHERE date = ?"
    params: tuple[str] = (date,)
    result: db_config.Result = db_config.execute_query(query, params)
    if result.success:
        return [
            [row[0], row[1], row[2], row[3], row[4], row[5], row[6]]
            for row in result.data
        ]
    else:
        raise Exception("Failed to load unfilled absences from database.")


def add_names(data: list, lookup: dict) -> list:
    """Add the names to the data list"""
    for row in data:
        row[0] = lookup.get(row[0])  # Replace teacher_id with teacher_name
    return data


def get_teacher_lookup() -> dict[int, str]:
    """Get a dictionary of teacher names and their ids"""
    query: str = "SELECT teacher_id, teacher_name FROM teachers"
    result: db_config.Result = db_config.execute_query(query)
    if not result.success:
        raise Exception("Failed to load teacher lookup from database.")
    # Return a dictionary mapping teacher_id to teacher_name
    return {row[0]: row[1] for row in result.data}
   

def get_oncall_totals(year: str) -> list[list[str | int]]:
    """Get the total number of on-calls for each teacher in the given year."""
    query: str = """SELECT 
                teachers.teacher_name, 
                COUNT(oncall_schedule.id) AS total_oncalls
            FROM 
                teachers
            LEFT JOIN 
                oncall_schedule ON teachers.teacher_id = oncall_schedule.teacher_id
            WHERE 
                oncall_schedule.year = ?
            GROUP BY 
                teachers.teacher_name
        """
    params: tuple[str] = (year,)
    result: db_config.Result = db_config.execute_query(query, params)
    if not result.success:
        raise Exception("Failed to load on-call totals from database.")
    return [list(row) for row in result.data]


def save_oncall_schedule(schedule: list) -> None:
    """Save an on-call schedule entry to the database. overwrite existing entries.
    
    The schedule should be a list of lists, where each inner list contains:
    [teacher_id: int, year: str, date: str, period: str, half: str]
    """
    date: str = schedule[0][2]  # Assuming the first entry has the date
    query1: str = "DELETE FROM oncall_schedule WHERE date = ?"
    params1: tuple[str] = (date,)
    result1: db_config.Result = db_config.execute_query(query1, params1)
    if not result1.success:
        raise Exception("Failed to clear existing on-call schedule for the date.")
        # Insert new entries into the on-call schedule
    
    if not schedule:
        raise Exception("No schedule provided") 
    
    query2: str = """
                INSERT INTO oncall_schedule (teacher_id, year, date, period, half)
                VALUES (?, ?, ?, ?, ?)
            """
    params2: List[tuple[str | int, str | int, str | int, str | int, str | int]] = []
    for oncall in schedule:
            params2.append((oncall[0],
                oncall[1],
                oncall[2],
                oncall[3],
                oncall[4]))
    result2: db_config.Result = db_config.execute_query(query2, params2)
    if not result2.success:
        raise Exception("Failed to save on-call schedule to the database.")