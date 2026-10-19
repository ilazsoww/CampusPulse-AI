"""Authorize CampusPulse AI to read the current user's Google Calendar.

Run locally from the repository root:
    python setup_google_calendar.py
"""
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

ROOT_DIR = Path(__file__).resolve().parent
CREDENTIALS_FILE = ROOT_DIR / "credentials.json"
TOKEN_FILE = ROOT_DIR / "token.json"
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def main() -> None:
    if not CREDENTIALS_FILE.exists():
        raise SystemExit(
            "Missing credentials.json. In Google Cloud Console, enable Google "
            "Calendar API, create an OAuth client of type Desktop app, download "
            "its JSON file, and save it as credentials.json in the repository root."
        )

    credentials = None
    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE), SCOPES
        )

    if not credentials or not credentials.valid:
        if credentials and credentials.expired and credentials.refresh_token:
            credentials.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                str(CREDENTIALS_FILE), SCOPES
            )
            credentials = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    try:
        TOKEN_FILE.chmod(0o600)
    except OSError:
        # Windows may not support POSIX permission semantics.
        pass

    print("Google Calendar connected. The app has read-only calendar access.")


if __name__ == "__main__":
    main()
