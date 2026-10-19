import pytest
from models import Assignment

def test_valid_assignment():
    task = Assignment(
        title="Prepare Presentation", 
        course="AI", 
        due_date="2026-10-25", 
        priority="High"
    )
    assert task.title == "Prepare Presentation"
    assert task.status == "Pending"

def test_invalid_priority():
    with pytest.raises(ValueError, match="Priority must be one of"):
        Assignment(
            title="Task", 
            course="AI", 
            due_date="2026-10-25", 
            priority="SuperHigh"  # Неверный приоритет
        )

def test_invalid_date():
    with pytest.raises(ValueError, match="due_date must be in YYYY-MM-DD format"):
        Assignment(
            title="Task", 
            course="AI", 
            due_date="25-10-2026",  # Неверный формат
            priority="Medium"
        )