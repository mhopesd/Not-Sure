"""
Google Integration — Gmail + Google Calendar via Google APIs.

Uses google-auth-oauthlib for OAuth2 and the Google API Python client
for Calendar events and Gmail send.
"""

import base64
import logging
import time
from datetime import datetime, timedelta, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# Google OAuth endpoints
AUTH_BASE = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"

# Google API endpoints
CALENDAR_BASE = "https://www.googleapis.com/calendar/v3"
GMAIL_BASE = "https://gmail.googleapis.com/gmail/v1"

# Required scopes
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/calendar",
    "https://www.googleapis.com/auth/gmail.send",
]


class GoogleIntegration:
    """Handles Google API interactions for Calendar and Gmail."""

    # ── OAuth Flow ─────────────────────────────────────────────────

    @staticmethod
    def get_auth_url(client_id: str, redirect_uri: str, state: str = "") -> str:
        """Generate the Google OAuth2 authorization URL."""
        params = {
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
            "state": state,
        }
        return f"{AUTH_BASE}?{urlencode(params)}"

    @staticmethod
    def exchange_code(
        code: str, client_id: str, client_secret: str, redirect_uri: str
    ) -> dict:
        """Exchange an authorization code for access + refresh tokens."""
        data = {
            "code": code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        }
        resp = requests.post(TOKEN_URL, data=data, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()

        # Calculate expiry
        expires_in = token_data.get("expires_in", 3600)
        token_data["expires_at"] = time.time() + expires_in

        # Fetch user profile
        profile = GoogleIntegration._get_profile(token_data["access_token"])
        token_data["email"] = profile.get("email", "")
        token_data["display_name"] = profile.get("name", "")

        return token_data

    @staticmethod
    def refresh_tokens(refresh_token: str, client_id: str, client_secret: str) -> dict:
        """Refresh an expired access token."""
        data = {
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        }
        resp = requests.post(TOKEN_URL, data=data, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()
        expires_in = token_data.get("expires_in", 3600)
        token_data["expires_at"] = time.time() + expires_in
        # Preserve refresh_token if not returned in refresh response
        if "refresh_token" not in token_data:
            token_data["refresh_token"] = refresh_token
        return token_data

    # ── API Helpers ────────────────────────────────────────────────

    @staticmethod
    def _headers(access_token: str) -> dict:
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def _get_profile(access_token: str) -> dict:
        """Fetch the current user's profile."""
        resp = requests.get(
            USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Calendar ───────────────────────────────────────────────────

    @staticmethod
    def get_calendar_events(access_token: str, days_ahead: int = 7) -> list[dict]:
        """Fetch upcoming events from Google Calendar."""
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        params = {
            "timeMin": now.isoformat(),
            "timeMax": end.isoformat(),
            "singleEvents": "true",
            "orderBy": "startTime",
            "maxResults": 50,
        }
        resp = requests.get(
            f"{CALENDAR_BASE}/calendars/primary/events",
            headers=GoogleIntegration._headers(access_token),
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        events = []
        for item in data.get("items", []):
            start = item.get("start", {})
            end_time = item.get("end", {})
            events.append({
                "id": item.get("id", ""),
                "title": item.get("summary", "Untitled"),
                "start": start.get("dateTime", start.get("date", "")),
                "end": end_time.get("dateTime", end_time.get("date", "")),
                "location": item.get("location", ""),
                "description": item.get("description", ""),
                "organizer": (item.get("organizer", {}).get("displayName", "")),
                "is_all_day": "date" in start and "dateTime" not in start,
                "source": "google",
            })
        return events

    @staticmethod
    def create_calendar_event(
        access_token: str,
        title: str,
        start: str,
        end: str,
        description: str = "",
        location: str = "",
    ) -> dict:
        """Create a new Google Calendar event.

        Args:
            start/end: ISO 8601 datetime strings (e.g. "2026-02-12T10:00:00-08:00")
        """
        event_body = {
            "summary": title,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
            "description": description,
        }
        if location:
            event_body["location"] = location

        resp = requests.post(
            f"{CALENDAR_BASE}/calendars/primary/events",
            headers=GoogleIntegration._headers(access_token),
            json=event_body,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Gmail ──────────────────────────────────────────────────────

    @staticmethod
    def send_email(
        access_token: str,
        to: str,
        subject: str,
        body_html: str,
        from_email: str = "me",
    ) -> bool:
        """Send an email via Gmail API.

        Returns True on success.
        """
        message = MIMEMultipart("alternative")
        message["to"] = to
        message["subject"] = subject
        message.attach(MIMEText(body_html, "html"))

        raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")

        resp = requests.post(
            f"{GMAIL_BASE}/users/me/messages/send",
            headers=GoogleIntegration._headers(access_token),
            json={"raw": raw},
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Email sent via Gmail to %s", to)
        return True
