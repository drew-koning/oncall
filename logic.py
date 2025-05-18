"""OnCall is a tool for tracking and scheduling secondary Teachers On Call schedules and allotments"""

# Import necessary modules
import helper_classes as hc
import sqlite3
import pathlib
import polars as pl
from datetime import datetime, timedelta


def main():
    """Entry point for the OnCall program."""
    # Initialize the database
    initializeDB()
    # Initialize the teacher list and populate from the database
    teacher_list = load_teacher_list_from_db()
    print("Teachers loaded from database:")
    if not teacher_list.get_teachers():
        print("No teachers found in the database.")



def initializeDB() -> None:
    """Initialize the SQLite database and create necessary tables."""
    # Connect to the SQLite database (or create it if it doesn't exist)
    if not pathlib.Path('oncall.db').exists():
        # Create the database file
        conn = sqlite3.connect('oncall.db')
        cursor = conn.cursor()
        # Create a table for teachers if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS teachers (
                teacher_id INTEGER PRIMARY KEY,
                teacher_name TEXT NOT NULL,
                period1 TEXT,
                period2 TEXT,
                period3 TEXT,
                period4 TEXT,
                oncalls INTEGER DEFAULT 0,
                available INTEGER DEFAULT NULL,
                active INTEGER DEFAULT 1
            )
        ''')
        # Create a table for on-call schedules if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS oncall_schedule (
                id INTEGER PRIMARY KEY,
                date TEXT NOT NULL,
                teacher_id INTEGER,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            )
        ''')
        # Create a table for unfilled absences if it doesn't exist
        cursor.execute('''
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
        ''')
        # Commit the changes and close the connection
        conn.commit()
        conn.close()

def load_teacher_list_from_db() -> hc.TeacherList:
    """Load the teacher list from the SQLite database."""
    with sqlite3.connect('oncall.db') as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM teachers')
        rows = cursor.fetchall()
        teacher_list = hc.TeacherList()
        for row in rows:
            teacher = hc.Teacher(
                id=row[0],
                name=row[1],
                period1=row[2],
                period2=row[3],
                period3=row[4],
                period4=row[5],
                oncalls=row[6]
            )
            teacher_list.add_teacher(teacher)
    return teacher_list

def get_absences_from_db(date):
    """grab the currently active teacher list with all absences for the provided date in the
    following format teaher id, teacher name, period 1, period 2, period 3, period 4"""
    with sqlite3.connect('oncall.db') as conn:
        cursor = conn.cursor()

        query = '''
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
        '''
        cursor.execute(query, (date,))

        data = cursor.fetchall()
        return [[row[0],
                 row[1],
                 bool(row[2]), 
                 bool(row[3]),
                 bool(row[4]),
                 bool(row[5]),
                 all(row[2:])]for row in data]


def load_schedule_from_file(file_path: str) -> None:
    """Load a schedule from a file."""
    schedule = pl.read_excel(file_path)
    with sqlite3.connect('oncall.db') as conn:
        cursor = conn.cursor()
    
    #TODO Get current teacher list, if teacher exists, update their periods, else add them. teachers not in the new schedule, mark as inactive
        cursor.execute('SELECT teacher_name FROM teachers')
        existing_teachers = cursor.fetchall()
        existing_teachers = [teacher[0] for teacher in existing_teachers]


        for row in schedule.iter_rows():
            # Assuming the schedule has columns 'name', 'period1', 'period2', 'lunch', 'period3', 'period4'
            if row[0] and row[0] not in existing_teachers:
                # Create a new teacher object and add it to the database
                teacher = hc.Teacher(
                    name=row[0],
                    period1=row[1],
                    period2=row[2],
                    period3=row[4],
                    period4=row[5]
                )
                cursor.execute('''
                    INSERT INTO teachers (teacher_name, period1, period2, period3, period4)
                    VALUES (?, ?, ?, ?, ?)
                ''', (teacher.name, teacher.period1, teacher.period2, teacher.period3, teacher.period4))
        conn.commit()
    return


def save_absences_to_db(date: str, teacher_absences: list[int, str, bool, bool, bool, bool, bool]) -> int:
    """Save the absences to the database."""
    try:
        with sqlite3.connect('oncall.db') as conn:
            cursor = conn.cursor()
            #clear any previous entries before re-saving
            try:
                cursor.execute("DELETE FROM unfilled_absences WHERE date = ?", (date,))
            except sqlite3.IntegrityError:
                return 1
            for teacher_id, teacher_name, period1, period2, period3, period4, allday in teacher_absences:
                cursor.execute('''
                    INSERT INTO unfilled_absences (date, teacher_id, period1, period2, period3, period4)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (date, teacher_id, period1, period2, period3, period4))
            conn.commit()
            return 0
    except Exception:

        return 1

def schedule_oncalls(date: str) -> list:
    with sqlite3.connect('oncall.db') as conn:
        cursor = conn.cursor()
        #obtain the unfilled absences for the date provided
        try:
            cursor.execute("SELECT * FROM unfilled_absences WHERE date = ?", (date,))
        except sqlite3.IntegrityError:
            return 1
        unfilled = cursor.fetchall()
        # get the list of available teachers (dropping those that have unfilled absences or already have 2 for the current week.)


        #for each unfilled absence, per period allocate a teacher to each half, based on fewest number of oncalls
        #incorporate a limit of 2 per week.

def current_week(day: str)-> list[str, str]:
    date_day = datetime.strptime(day, "%Y%m%d")
    weekend = 5- date_day.weekday()
    if weekend <0: weekend = 6
    weekstart = date_day.weekday()*-1-1
    if weekstart == -7: weekstart=0
    weekend = date_day+timedelta(weekend)
    weekstart = date_day+timedelta(weekstart)
    return [weekstart, weekend]




if __name__ == "__main__":
    pass

