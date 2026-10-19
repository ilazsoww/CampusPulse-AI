import json
import os
from mcp.server.fastmcp import FastMCP
import database
from models import Assignment
import PyPDF2

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

@mcp.tool()
def search_study_materials(query: str) -> str:
    """
    Search through local study materials (PDF, TXT, MD) in the study_materials directory 
    to answer academic questions based on lecture notes.
    """
    directory = "study_materials"
    if not os.path.exists(directory):
        return "Error: study_materials directory does not exist."

    results = []
    
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        content = ""
        
        try:
            if filename.lower().endswith(('.txt', '.md')):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
            elif filename.lower().endswith('.pdf'):
                with open(filepath, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text = page.extract_text()
                        if text:
                            content += text + "\n"
                            
            # Простой поиск по вхождению ключевого слова (query)
            if query.lower() in content.lower():
                # Возвращаем фрагмент текста вокруг найденного слова (для экономии контекста)
                idx = content.lower().find(query.lower())
                start = max(0, idx - 200)
                end = min(len(content), idx + 500)
                snippet = content[start:end].replace('\n', ' ')
                results.append(f"Found in {filename}:\n...{snippet}...\n")
                
        except Exception as e:
            results.append(f"Could not read {filename}: {str(e)}")

    if not results:
        return f"No materials found matching the query: '{query}'"
    
    return "\n".join(results)

if __name__ == "__main__":
    # Запуск сервера в режиме stdio
    mcp.run()