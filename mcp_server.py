import json
from mcp.server.fastmcp import FastMCP
import database
from models import Assignment

# Инициализируем MCP сервер
mcp = FastMCP("CampusPulse")

@mcp.tool()
def get_assignments(status: str = None) -> str:
    """Retrieve a list of assignments, optionally filtered by status ('Pending' or 'Completed')."""
    tasks = database.list_assignments(status)
    return json.dumps(tasks, ensure_ascii=False)

@mcp.tool()
def create_assignment(title: str, course: str, due_date: str, priority: str, description: str = "") -> str:
    """Create a new academic assignment. Priority must be 'High', 'Medium', or 'Low'."""
    try:
        task = Assignment(
            title=title, 
            course=course, 
            due_date=due_date, 
            priority=priority, 
            description=description
        )
        return database.add_assignment(task)
    except Exception as e:
        return f"Error creating assignment: {str(e)}"

@mcp.tool()
def get_deadlines(days: int = 7) -> str:
    """Get upcoming pending assignments due within the specified number of days from today."""
    tasks = database.get_upcoming_deadlines(days)
    return json.dumps(tasks, ensure_ascii=False)

@mcp.tool()
def complete_assignment(assignment_id: int) -> str:
    """Mark an assignment as completed using its unique integer ID."""
    return database.mark_assignment_completed(assignment_id)

if __name__ == "__main__":
    # Запуск сервера в режиме stdio
    mcp.run()