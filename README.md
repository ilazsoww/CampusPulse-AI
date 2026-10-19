# 🎓 CampusPulse AI — Smart Autonomous AI Agent

An autonomous AI agent built for the GDG Astana hackathon to help university students manage their academic workload, deadlines, and priorities using a genuine Reasoning Loop and MCP (Model Context Protocol).

## Key Features
- **Autonomous Reasoning Loop**: The agent determines whether to answer directly or invoke tools based on the user's prompt.
- **MCP Integration**: Uses `FastMCP` (via `stdio`) to securely bridge local tools with the LLM context.
- **Zero-Budget Architecture**: Fully operational local prototype using Gemini Free Tier and SQLite, requiring zero cloud spending.
- **Streamlit Dashboard**: A live, interactive UI that visualizes the agent's internal thought process and tool execution in real-time.

## Technology Stack
- **Language**: Python 3.10+
- **LLM**: Gemini API (`gemini-2.5-flash` / `gemini-3.8`) via `google-genai` SDK
- **MCP Framework**: `mcp<2.0.0` (FastMCP)
- **Frontend**: Streamlit
- **Storage**: SQLite
- **Testing**: Pytest

## Quick Start (Local Setup)

1. **Clone the repository and create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: .\venv\Scripts\Activate.ps1

2. Install dependencies:
    ```bash
    pip install -r requirements.txt

3. Configure Environment Variables:
    Rename .env.example to .env and add your free Google AI Studio key:
    ```bash
    GEMINI_API_KEY="your_api_key_here"
    DB_PATH="campuspulse.db"

4. Run the Application:
    ```bash
    streamlit run app.py

5. Testing
    Run the automated test suite for database and data model validation:
    ```bash
    pytest -v

6. Google Cloud Deployment (Vertex AI)
    Fulfilling Evaluation Criterion 2

    The architecture is fully designed to be deployed to Vertex AI Agent Engine / Reasoning Engine. A deployment script (deploy.py) is included in the repository, utilizing reasoning_engines.ReasoningEngine.create.

    Deploying to Vertex AI requires an active Google Cloud Billing Account. To maintain the project's $0 budget constraint for this demonstration, the primary evaluation environment is the local Streamlit application. The local environment successfully demonstrates the core requirement: how the agent executes its decision-making process, invokes tools via MCP, and solves student problems.

    To deploy to GCP (if billing is enabled):

    Bash
    export GCP_PROJECT_ID="your-project-id"
    python deploy.py

## Optional Google Calendar integration

CampusPulse can read upcoming events from the **primary calendar of the Google account you authorize**. This is not an AITU-wide events feed.

1. In [Google Cloud Console](https://console.cloud.google.com/), create/select a project and enable **Google Calendar API**.
2. Configure the OAuth consent screen. If the app is in Testing mode, add your Google account as a test user.
3. Create an OAuth client ID of type **Desktop app**, download its JSON file, and save it as `credentials.json` in the project root (next to `app.py`). Do not commit this file.
4. Install dependencies: `pip install -r requirements.txt`.
5. Run `python setup_google_calendar.py` and authorize read-only access in the browser. This creates a local `token.json`, which is also excluded from Git.
6. Start or restart the app and ask: “Show my Google Calendar events for the next 7 days.”

The agent exposes this through the `get_google_calendar_events` MCP tool. The tool returns setup instructions if OAuth has not been configured. Revoke access through your Google Account security/third-party connections settings and delete local `token.json` if you want to disconnect.
