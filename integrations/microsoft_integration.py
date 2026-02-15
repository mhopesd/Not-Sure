"""
Microsoft Integration — Outlook Mail + Calendar via Microsoft Graph API.

Uses MSAL (Microsoft Authentication Library) for OAuth2 and the
MS Graph REST API for calendar events and email.
"""

import logging
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# Microsoft Graph endpoints
GRAPH_BASE = "https://graph.microsoft.com/v1.0"
AUTH_BASE = "https://login.microsoftonline.com/common/oauth2/v2.0"

# Required scopes
SCOPES = [
    "openid",
    "profile",
    "email",
    "offline_access",
    "Mail.Send",
    "Calendars.ReadWrite",
]


class MicrosoftIntegration:
    """Handles Microsoft Graph API interactions for Outlook and Calendar."""

    # ── OAuth Flow ─────────────────────────────────────────────────

    @staticmethod
    def get_auth_url(client_id: str, redirect_uri: str, state: str = "") -> str:
        """Generate the Microsoft OAuth2 authorization URL."""
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "response_mode": "query",
            "scope": " ".join(SCOPES),
            "state": state,
        }
        return f"{AUTH_BASE}/authorize?{urlencode(params)}"

    @staticmethod
    def exchange_code(
        code: str, client_id: str, client_secret: str, redirect_uri: str
    ) -> dict:
        """Exchange an authorization code for access + refresh tokens."""
        data = {
            "client_id": client_id,
            "scope": " ".join(SCOPES),
            "code": code,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
            "client_secret": client_secret,
        }
        resp = requests.post(f"{AUTH_BASE}/token", data=data, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()

        # Calculate expiry timestamp
        expires_in = token_data.get("expires_in", 3600)
        token_data["expires_at"] = time.time() + expires_in

        # Fetch user profile to get email / display name
        profile = MicrosoftIntegration._get_profile(token_data["access_token"])
        token_data["email"] = profile.get("mail") or profile.get("userPrincipalName", "")
        token_data["display_name"] = profile.get("displayName", "")

        return token_data

    @staticmethod
    def refresh_tokens(refresh_token: str, client_id: str, client_secret: str) -> dict:
        """Refresh an expired access token."""
        data = {
            "client_id": client_id,
            "scope": " ".join(SCOPES),
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
            "client_secret": client_secret,
        }
        resp = requests.post(f"{AUTH_BASE}/token", data=data, timeout=30)
        resp.raise_for_status()
        token_data = resp.json()
        expires_in = token_data.get("expires_in", 3600)
        token_data["expires_at"] = time.time() + expires_in
        return token_data

    # ── Graph API Helpers ──────────────────────────────────────────

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
            f"{GRAPH_BASE}/me",
            headers=MicrosoftIntegration._headers(access_token),
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Calendar ───────────────────────────────────────────────────

    @staticmethod
    def get_calendar_events(access_token: str, days_ahead: int = 7) -> list[dict]:
        """Fetch upcoming calendar events from Outlook Calendar."""
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days_ahead)

        params = {
            "$orderby": "start/dateTime",
            "$top": 50,
            "$filter": (
                f"start/dateTime ge '{now.isoformat()}' "
                f"and start/dateTime le '{end.isoformat()}'"
            ),
            "$select": "subject,start,end,location,bodyPreview,organizer,isAllDay",
        }
        resp = requests.get(
            f"{GRAPH_BASE}/me/calendarview",
            headers=MicrosoftIntegration._headers(access_token),
            params=params,
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()

        events = []
        for item in data.get("value", []):
            events.append({
                "id": item.get("id", ""),
                "title": item.get("subject", "Untitled"),
                "start": item.get("start", {}).get("dateTime", ""),
                "end": item.get("end", {}).get("dateTime", ""),
                "location": (item.get("location") or {}).get("displayName", ""),
                "description": item.get("bodyPreview", ""),
                "organizer": (item.get("organizer", {}).get("emailAddress", {}).get("name", "")),
                "is_all_day": item.get("isAllDay", False),
                "source": "microsoft",
            })
        return events

    @staticmethod
    def create_calendar_event(
        access_token: str,
        title: str,
        start: str,
        end: str,
        body: str = "",
        location: str = "",
    ) -> dict:
        """Create a new calendar event in Outlook Calendar.

        Args:
            start/end: ISO 8601 datetime strings (e.g. "2026-02-12T10:00:00")
        """
        event_body = {
            "subject": title,
            "start": {"dateTime": start, "timeZone": "UTC"},
            "end": {"dateTime": end, "timeZone": "UTC"},
            "body": {"contentType": "HTML", "content": body},
        }
        if location:
            event_body["location"] = {"displayName": location}

        resp = requests.post(
            f"{GRAPH_BASE}/me/events",
            headers=MicrosoftIntegration._headers(access_token),
            json=event_body,
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    # ── Email ──────────────────────────────────────────────────────

    @staticmethod
    def send_email(
        access_token: str,
        to: str,
        subject: str,
        body_html: str,
    ) -> bool:
        """Send an email via Outlook/Microsoft Graph.

        Returns True on success.
        """
        message = {
            "message": {
                "subject": subject,
                "body": {"contentType": "HTML", "content": body_html},
                "toRecipients": [
                    {"emailAddress": {"address": to}}
                ],
            }
        }
        resp = requests.post(
            f"{GRAPH_BASE}/me/sendMail",
            headers=MicrosoftIntegration._headers(access_token),
            json=message,
            timeout=15,
        )
        resp.raise_for_status()
        logger.info("Email sent via Microsoft to %s", to)
        return True
