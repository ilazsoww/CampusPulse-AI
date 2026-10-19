"""Read-only Google Calendar integration for CampusPulse AI.

Authentication is performed separately by setup_google_calendar.py so the
MCP tool never unexpectedly opens a browser during an AI request.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CREDENTIALS_FILE = ROOT_DIR / "credentials.json"
TOKEN_FILE = ROOT_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_calendar_events(days_ahead: int = 7) -> dict:
    """Return upcoming events from the authenticated user's primary calendar.

    Args:
        days_ahead: Number of days to look ahead, from 1 to 30.

    Returns:
        A JSON-serializable dictionary with events or a safe error message.
    """
    if not isinstance(days_ahead, int) or isinstance(days_ahead, bool):
        return {"error": "days_ahead must be an integer between 1 and 30"}
    if not 1 <= days_ahead <= 30:
        return {"error": "days_ahead must be between 1 and 30"}

    if not TOKEN_FILE.exists():
        if not CREDENTIALS_FILE.exists():
            return {
                "error": (
                    "Google Calendar is not configured. Download an OAuth Desktop "
                    "client JSON from Google Cloud, save it as credentials.json in "
                    "the project root, then run: python setup_google_calendar.py"
                )
            }
        return {
            "error": (
                "Google Calendar is not connected. Run "
                "'python setup_google_calendar.py' from the project root first."
            )
        }

    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from googleapiclient.errors import HttpError

        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

        if not credentials.valid:
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
                TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
            else:
                return {
                    "error": (
                        "Google Calendar authorization is no longer valid. "
                        "Run 'python setup_google_calendar.py' to reconnect."
                    )
                }

        service = build(
            "calendar",
            "v3",
            credentials=credentials,
            cache_discovery=False,
        )
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        response = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=50,
        ).execute()

        events = []
        for event in response.get("items", []):
            start = event.get("start", {})
            finish = event.get("end", {})
            events.append({
                "id": event.get("id"),
                "title": event.get("summary", "Untitled event"),
                "start": start.get("dateTime", start.get("date")),
                "end": finish.get("dateTime", finish.get("date")),
                "location": event.get("location", ""),
                "description": event.get("description", ""),
                "html_link": event.get("htmlLink", ""),
            })

        return {
            "source": "google_calendar_primary",
            "days_ahead": days_ahead,
            "events": events,
        }
    except HttpError as exc:
        return {
            "error": (
                "Google Calendar API request failed "
                f"(HTTP {exc.resp.status}). Check that Calendar API is enabled "
                "and the Google account has authorized access."
            )
        }
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return {
            "error": (
                "Could not read Google Calendar credentials. Reconnect using "
                f"'python setup_google_calendar.py'. Details: {type(exc).__name__}"
            )
        }
    except Exception as exc:
        return {
            "error": (
                "Google Calendar request failed. "
                f"Details: {type(exc).__name__}"
            )
        }
