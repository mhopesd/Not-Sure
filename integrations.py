"""
Stub integrations module.

Provides placeholder classes so api_server.py can import without errors.
Real OAuth / calendar integrations can be added here later.
"""
import logging

logger = logging.getLogger(__name__)


class OAuthManager:
    """Stub OAuth manager — returns not-configured responses."""

    def __init__(self, config=None):
        self.config = config

    def get_auth_url(self, provider: str) -> str:
        logger.warning(f"OAuthManager.get_auth_url called for '{provider}' but OAuth is not configured")
        return ""

    def handle_callback(self, provider: str, code: str, state: str) -> dict:
        return {"error": "OAuth not configured"}


class MicrosoftIntegration:
    """Stub Microsoft integration."""

    def __init__(self, config=None):
        self.config = config

    def get_calendar_events(self, token: str) -> list:
        return []


class GoogleIntegration:
    """Stub Google integration."""

    def __init__(self, config=None):
        self.config = config

    def get_calendar_events(self, token: str) -> list:
        return []
