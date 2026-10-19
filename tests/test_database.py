import pytest
from datetime import datetime, timedelta
import database
from models import Assignment

@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch, tmp_path):
    """Overrides DB_PATH to use a temporary file for tests."""
    test_db = tmp_path / "test.db"
    monkeypatch.setattr(database, 'DB_PATH', str(test_db))
    database.init_db()
    yield

def test_add_and_list_assignments():
    task = Assignment(title="Test Task", course="Math", due_date="2026-10-25", priority="High")
    database.add_assignment(task)
    
    tasks = database.list_assignments()
    assert len(tasks) == 1
    assert tasks[0]["title"] == "Test Task"
    assert tasks[0]["status"] == "Pending"

def test_mark_completed():
    task = Assignment(title="Test Task 2", course="Physics", due_date="2026-10-26", priority="Medium")
    database.add_assignment(task)
    
    tasks = database.list_assignments()
    task_id = tasks[0]["id"]
    
    database.mark_assignment_completed(task_id)
    updated_tasks = database.list_assignments(status="Completed")
    assert len(updated_tasks) == 1
    assert updated_tasks[0]["id"] == task_id

def test_upcoming_deadlines():
    today = datetime.now()
    # Задача на завтра
    task1 = Assignment(
        title="Urgent Task", 
        course="CS", 
        due_date=(today + timedelta(days=1)).strftime("%Y-%m-%d"), 
        priority="High"
    )
    # Задача через месяц
    task2 = Assignment(
        title="Future Task", 
        course="CS", 
        due_date=(today + timedelta(days=30)).strftime("%Y-%m-%d"), 
        priority="Low"
    )
    
    database.add_assignment(task1)
    database.add_assignment(task2)
    
    deadlines = database.get_upcoming_deadlines(days=7)
    assert len(deadlines) == 1
    assert deadlines[0]["title"] == "Urgent Task"