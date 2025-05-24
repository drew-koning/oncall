# Import necessary modules
import sqlite3
import pathlib
import polars as pl
from datetime import datetime, timedelta, date
from typing import List, Union


def initializeDB() -> None:
    """Initialize the SQLite database and create necessary tables."""
    # Connect to the SQLite database (or create it if it doesn't exist)
    if not pathlib.Path("oncall.db").exists():
        # Create the database file
        conn = sqlite3.connect("oncall.db")
        cursor = conn.cursor()
        # Create a table for teachers if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INTEGER PRIMARY KEY,
                teacher_name TEXT NOT NULL,
                period1 TEXT,
                period2 TEXT,
                period3 TEXT,
                period4 TEXT,
                available INTEGER DEFAULT NULL,
                active INTEGER DEFAULT 1
            )
        """)
        # Create a table for on-call schedules if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS oncall_schedule (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                teacher_id INTEGER,
                year TEXT NOT NULL,
                period TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            )
        """)
        # Create a table for unfilled absences if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS unfilled_absences (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                teacher_id INTEGER,
                period1 INTEGER,
                period2 INTEGER,
                period3 INTEGER,
                period4 INTEGER,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            )
        """)
        # Commit the changes and close the connection
        conn.commit()
        conn.close()


def load_teacher_list_from_db():
    """Load the teacher list from the SQLite database."""
    from oncall.helper_classes import TeacherList, Teacher

    with sqlite3.connect("oncall.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM teachers")
        rows = cursor.fetchall()
        teacher_list = TeacherList()
        for row in rows:
            teacher = Teacher(
                id=row[0],
                name=row[1],
                period1=row[2],
                period2=row[3],
                period3=row[4],
                period4=row[5],
            )
            teacher_list.add_teacher(teacher)
    return teacher_list


def get_absences_from_db(date):
    """grab the currently active teacher list with all absences for the provided date in the
    following format teaher id, teacher name, period 1, period 2, period 3, period 4"""
    with sqlite3.connect("oncall.db") as conn:
        cursor = conn.cursor()

        query = """
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
        cursor.execute(query, (date,))

        data = cursor.fetchall()
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
            for row in data
        ]


def load_schedule_from_file(file_path: str) -> None:
    """Load a schedule from a file."""
    from oncall.helper_classes import Teacher

    schedule = pl.read_excel(file_path)
    with sqlite3.connect("oncall.db") as conn:
        cursor = conn.cursor()

        # TODO Get current teacher list, if teacher exists, update their periods, else add them. teachers not in the new schedule, mark as inactive
        cursor.execute("SELECT teacher_name FROM teachers")
        existing_teachers = cursor.fetchall()
        existing_teachers = [teacher[0] for teacher in existing_teachers]

        for row in schedule.iter_rows():
            # Assuming the schedule has columns 'name', 'period1', 'period2', 'lunch', 'period3', 'period4'
            if row[0] and row[0] not in existing_teachers:
                # Create a new teacher object and add it to the database
                teacher = Teacher(
                    name=row[0],
                    period1=row[1],
                    period2=row[2],
                    period3=row[4],
                    period4=row[5],
                )
                cursor.execute(
                    """
                    INSERT INTO teachers (teacher_name, period1, period2, period3, period4, available)
                    VALUES (?, ?, ?, ?, ?, ?)
                """,
                    (
                        teacher.name,
                        teacher.period1,
                        teacher.period2,
                        teacher.period3,
                        teacher.period4,
                        teacher.find_available_period(),
                    ),
                )
        conn.commit()
    return


def save_absences_to_db(
    date: str, teacher_absences: List[Union[str, int, bool]]
) -> int:
    """Save the absences to the database."""
    try:
        with sqlite3.connect("oncall.db") as conn:
            cursor = conn.cursor()
            # clear any previous entries before re-saving
            try:
                cursor.execute("DELETE FROM unfilled_absences WHERE date = ?", (date,))
            except sqlite3.IntegrityError:
                return 1
            for absence in teacher_absences:
                if isinstance(absence, (list, tuple)) and len(absence) == 7:
                    (
                        teacher_id,
                        _teacher_name,
                        period1,
                        period2,
                        period3,
                        period4,
                        _allday,
                    ) = absence
                    cursor.execute(
                        """
                        INSERT INTO unfilled_absences (date, teacher_id, period1, period2, period3, period4)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
                        (date, teacher_id, period1, period2, period3, period4),
                    )
            conn.commit()
            return 0
    except Exception:
        return 1


def get_available_teachers(date: str) -> List[str]:
    """Get a list of teachers from the database who for the current day, don't have an absence"""
    with sqlite3.connect("oncall.db") as conn:
        cursor = conn.cursor()
        statement = """
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
              period1 = 1
            OR
              period2 = 1
            OR 
              period3 = 1
            OR 
              period4 =1
          )"""
        cursor.execute(statement, (date,))
        data = cursor.fetchall()
    return data


def current_week(day: str) -> list[str]:
    """Get the week range for the selected day (Sunday to Saturday)"""
    date_day = datetime.strptime(day, "%Y%m%d")
    weekend = 5 - date_day.weekday()
    if weekend < 0:
        weekend = 6
    weekstart = date_day.weekday() * -1 - 1
    if weekstart == -7:
        weekstart = 0
    weekend = (date_day + timedelta(weekend)).strftime("%Y%m%d")
    weekstart = (date_day + timedelta(weekstart)).strftime("%Y%m%d")
    return [weekstart, weekend]


def get_school_year(given_date: str) -> str:
    """
    Returns the school year in the format "YYYY/YYYY" for a given date.
    The school year runs from August 20 to August 19 of the next year.
    """
    if len(given_date) != 8:
        raise ValueError("Date not provided in the proper format")
    y, m, d = given_date[:4], given_date[4:6], given_date[6:]
    try:
        newdate = date(int(y), int(m), int(d))
    except Exception:
        raise ValueError("Date not provided int he proper format")
    if newdate >= date(newdate.year, 8, 20):
        start_year = newdate.year
    else:
        start_year = newdate.year - 1

    end_year = start_year + 1
    return f"{start_year}/{end_year}"


def split_available_teachers(available_teachers: list) -> list[list]:
    """Separate teachers into groups by which period they are available"""
    period1 = [x for x in available_teachers if x[6] == 1]
    period2 = [x for x in available_teachers if x[6] == 2]
    period3 = [x for x in available_teachers if x[6] == 3]
    period4 = [x for x in available_teachers if x[6] == 4]
    return [period1, period2, period3, period4]


def get_unfilled_absences(date: str) -> list:
    """Returns a list of all unfilled absences listed for the current day"""
    with sqlite3.connect("oncall.db") as conn:
        cursor = conn.cursor()
        # obtain the unfilled absences for the date provided
        try:
            cursor.execute("SELECT * FROM unfilled_absences WHERE date = ?", (date,))
        except sqlite3.IntegrityError:
            return []
        return cursor.fetchall()


def add_names(data: list, lookup: dict) -> list:
    """Add the names to the data list"""
    for row in data:
        row[0] = lookup.get(row[0])  # Replace teacher_id with teacher_name
    return data


def get_teacher_lookup() -> dict:
    """Get a dictionary of teacher names and their ids"""
    with sqlite3.connect("oncall.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT teacher_id, teacher_name FROM teachers")
        data = cursor.fetchall()
    return {row[0]: row[1] for row in data}
