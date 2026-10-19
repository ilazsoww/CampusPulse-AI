import sqlite3
from contextlib import contextmanager
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from config import DB_PATH
from models import Assignment

@contextmanager
def get_db_connection():
    """Context manager for SQLite database connection."""
    conn = sqlite3.connect(DB_PATH)
    # This allows accessing columns by name
    conn.row_factory = sqlite3.Row 
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    """Initializes the SQLite database with the required tables."""
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS assignments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                course TEXT NOT NULL,
                description TEXT,
                due_date TEXT NOT NULL,
                priority TEXT NOT NULL,
                status TEXT DEFAULT 'Pending'
            )
        ''')
        conn.commit()

def add_assignment(assignment: Assignment) -> str:
    """Adds a new assignment to the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO assignments (title, course, description, due_date, priority, status)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (assignment.title, assignment.course, assignment.description, 
              assignment.due_date, assignment.priority, assignment.status))
        conn.commit()
        return f"Assignment '{assignment.title}' added successfully with ID {cursor.lastrowid}."

def list_assignments(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieves assignments, optionally filtered by status."""
    with get_db_connection() as conn:
        if status:
            rows = conn.execute('SELECT * FROM assignments WHERE status = ?', (status,)).fetchall()
        else:
            rows = conn.execute('SELECT * FROM assignments').fetchall()
        return [dict(row) for row in rows]

def mark_assignment_completed(assignment_id: int) -> str:
    """Marks an assignment as completed by ID."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE assignments SET status = ? WHERE id = ?', ("Completed", assignment_id))
        if cursor.rowcount == 0:
            return f"Error: Assignment with ID {assignment_id} not found."
        conn.commit()
        return f"Assignment {assignment_id} marked as Completed."

def get_upcoming_deadlines(days: int = 7) -> List[Dict[str, Any]]:
    """Retrieves pending assignments due within the next specified number of days."""
    target_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d')
    today = datetime.now().strftime('%Y-%m-%d')
    
    with get_db_connection() as conn:
        rows = conn.execute('''
            SELECT * FROM assignments 
            WHERE status = 'Pending' AND due_date >= ? AND due_date <= ?
            ORDER BY due_date ASC
        ''', (today, target_date)).fetchall()
        return [dict(row) for row in rows]