import unittest
from unittest.mock import patch

from integrations import google_calendar


class TestGoogleCalendar(unittest.TestCase):
    def test_rejects_invalid_days_ahead(self):
        self.assertIn("error", google_calendar.get_calendar_events(0))
        self.assertIn("error", google_calendar.get_calendar_events(31))
        self.assertIn("error", google_calendar.get_calendar_events("7"))

    def test_missing_credentials_returns_setup_instructions(self):
        with patch.object(google_calendar, "TOKEN_FILE") as token_file, patch.object(
            google_calendar, "CREDENTIALS_FILE"
        ) as credentials_file:
            token_file.exists.return_value = False
            credentials_file.exists.return_value = False
            result = google_calendar.get_calendar_events(7)
        self.assertIn("error", result)
        self.assertIn("credentials.json", result["error"])


if __name__ == "__main__":
    unittest.main()
