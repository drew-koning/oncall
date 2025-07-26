import sqlite3
import pathlib

class Result:
    """A class to represent the result of a database operation."""
    def __init__(self, success: bool, message: str = "", data: list = []):
        self.success = success
        self.message = message
        self.data = data if data is not None else []


class DatabaseConnection:
    """A context manager for handling database connections."""
    def __init__(self, db_path: str = "oncall.db"):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def __enter__(self):
        """Establish a database connection and return the connection and cursor."""
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()
        return self.conn, self.cursor

    def __exit__(self, exc_type, exc_value, traceback):    
        """Close the database connection and handle exceptions."""   
        if self.conn:     
            if exc_type is not None:
                self.conn.rollback()
            else:
                self.conn.commit()
            if self.cursor:
                self.cursor.close()
            self.conn.close()
        else:
            raise Exception("Database connection was not established.")
    

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
                half TEXT NOT NULL,
                FOREIGN KEY (teacher_id) REFERENCES teachers (id)
            )
        """)
        # Create a table for unfilled absences if it doesn't exist;
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


def execute_query(query: str, params: tuple | list[tuple] = ()) -> Result:
    """Execute a single SQL query with parameters."""
    with DatabaseConnection() as (conn, cursor):
        try:

            if len(params) > 1:
                cursor.executemany(query, params)
            else:
                cursor.execute(query, params)
            data: list = cursor.fetchall()
            conn.commit()
            return Result(success=True, message="Query executed successfully.", data=data)
        except Exception as e:
            conn.rollback()
            return Result(success=False, message=f"Query failed: {str(e)}", data=[])
        

            