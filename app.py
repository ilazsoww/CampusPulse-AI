import streamlit as st
import asyncio
import database
from integrations.google_calendar import get_calendar_events
from agent import CampusPulseAgent
import pandas as pd

# Инициализация базы данных
database.init_db()

# Настройка страницы Streamlit
st.set_page_config(page_title="CampusPulse AI", page_icon="🎓", layout="wide")

# Инициализация истории чата в сессии
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- SIDEBAR: DASHBOARD & INFO ---
with st.sidebar:
    st.title("🎓 CampusPulse Dashboard")
    
    st.subheader("📊 Task Statistics")
    all_tasks = database.list_assignments()
    pending = [t for t in all_tasks if t['status'] == 'Pending']
    completed = [t for t in all_tasks if t['status'] == 'Completed']
    
    col1, col2 = st.columns(2)
    col1.metric("Pending", len(pending))
    col2.metric("Completed", len(completed))

    st.subheader("📎 Upload Study Materials")
    uploaded_file = st.file_uploader("Upload PDF or TXT", type=["pdf", "txt", "md"])
    if uploaded_file is not None:
        import os
        # Убеждаемся, что папка существует
        os.makedirs("study_materials", exist_ok=True)
        
        file_path = os.path.join("study_materials", uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        st.success(f"File '{uploaded_file.name}' successfully attached and ready for analysis!")
    
    st.divider()
    
    st.subheader("📅 Upcoming Deadlines (7 Days)")
    deadlines = database.get_upcoming_deadlines(7)
    if deadlines:
        df_deadlines = pd.DataFrame(deadlines)[['title', 'due_date', 'priority']]
        st.dataframe(df_deadlines, use_container_width=True, hide_index=True)
    else:
        st.info("No upcoming deadlines. Great job!")

    st.divider()

    st.subheader("📅 Google Calendar")
    st.caption("События из вашего личного Google Calendar")

    if st.button("Показать события на 7 дней"):
        st.session_state["calendar_result"] = get_calendar_events(7)

    calendar_result = st.session_state.get("calendar_result")

    if calendar_result:
        if "error" in calendar_result:
            st.warning(calendar_result["error"])
        else:
            events = calendar_result.get("events", [])

            if events:
                df = pd.DataFrame(events)
                df = df[["title", "start", "location"]]
                df.columns = ["Мероприятие", "Начало", "Место"]
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("На ближайшие 7 дней событий нет.")

    st.divider()

    st.subheader("➕ Manual Task Entry")
    with st.form("add_task_form"):
        # Использование персонализированного примера (AITU / ORKEN) для удобства презентации
        t_title = st.text_input("Title", placeholder="e.g., Prepare AITU Tech Week presentation")
        t_course = st.text_input("Course", placeholder="e.g., Project Management")
        t_date = st.date_input("Due Date")
        t_priority = st.selectbox("Priority", ["High", "Medium", "Low"])
        submitted = st.form_submit_button("Add Assignment")
        
        if submitted and t_title and t_course:
            from models import Assignment
            new_task = Assignment(
                title=t_title, 
                course=t_course, 
                due_date=t_date.strftime("%Y-%m-%d"), 
                priority=t_priority
            )
            database.add_assignment(new_task)
            st.success("Task added!")
            st.rerun()

    st.divider()
    
    st.markdown("""
    ### ⚙️ Architecture
    - **UI**: Streamlit
    - **Agent Core**: Gemini 3.8 Flash (Function Calling)
    - **Tools Bridge**: FastMCP Server (`stdio`)
    - **Storage**: Local SQLite
    """)

# --- MAIN AREA: CHAT INTERFACE ---
st.title("🤖 CampusPulse AI Assistant")
st.markdown("Ask me to manage your schedule, create tasks, or show priorities!")

# Функция для асинхронного запуска агента и потокового вывода шагов в UI
async def process_user_input(prompt, status_container, response_container):
    agent = CampusPulseAgent()
    final_text = ""

    try:
        await agent.initialize()

        async for step in agent.process_request(
            prompt,
            chat_history=None
        ):
            if step["type"] == "tool_call":
                status_container.write(
                    f"🛠️ **Вызов инструмента:** `{step['tool']}`"
                )
                status_container.json(step["args"])

            elif step["type"] == "tool_result":
                status_container.write("✅ **Результат инструмента:**")
                status_container.code(step["result"])

            elif step["type"] == "final_answer":
                response_container.markdown(step["text"])
                final_text = step["text"]

            elif step["type"] == "error":
                response_container.error(step["text"])
                final_text = step["text"]

    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "Failed to initialize or run CampusPulse agent"
        )

        final_text = (
            "Не удалось запустить ИИ-ассистента. "
            "Проверь настройки и подключение, затем попробуй снова."
        )
        response_container.error(final_text)

    finally:
        try:
            await agent.close()
        except Exception:
            import logging
            logging.getLogger(__name__).exception(
                "Failed to close CampusPulse agent"
            )

    return final_text

# Отображение истории сообщений
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Обработка нового ввода пользователя
if prompt := st.chat_input("E.g., What are my upcoming deadlines?"):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
        
    with st.chat_message("assistant"):
        # Создаем экспандер (статус), который визуализирует "мысли" агента
        status = st.status("🧠 Agent Reasoning Loop (MCP Execution)...", expanded=True)
        response_placeholder = st.empty()
        
        # Запускаем асинхронную функцию в синхронном Streamlit
        final_response = asyncio.run(process_user_input(prompt, status, response_placeholder))
        
        # Закрываем статус после завершения
        status.update(label="Reasoning Complete", state="complete", expanded=False)
        
        st.session_state.messages.append({"role": "assistant", "content": final_response})
        
        # Перезагружаем страницу, чтобы обновить дашборд в боковой панели (новые задачи и т.д.)
        st.rerun()