"""
OAuth Token Manager — Handles persistent storage, loading, and refresh
of OAuth2 tokens for Microsoft and Google integrations.

Tokens are stored in `integration_tokens.json` alongside the app,
and credentials (client_id, client_secret) are stored in `integration_credentials.json`.
Both files are gitignored.
"""

import json
import os
import time
import logging

logger = logging.getLogger(__name__)

# File paths relative to the project root
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKENS_FILE = os.path.join(_BASE_DIR, "integration_tokens.json")
CREDENTIALS_FILE = os.path.join(_BASE_DIR, "integration_credentials.json")


class OAuthManager:
    """Manages OAuth tokens and credentials for all integration providers."""

    PROVIDERS = ["microsoft", "google"]

    def __init__(self):
        self._tokens: dict = {}
        self._credentials: dict = {}
        self._load_tokens()
        self._load_credentials()

    # ── Token persistence ──────────────────────────────────────────

    def _load_tokens(self):
        """Load tokens from disk."""
        if os.path.exists(TOKENS_FILE):
            try:
                with open(TOKENS_FILE, "r") as f:
                    self._tokens = json.load(f)
                logger.info("Loaded integration tokens from %s", TOKENS_FILE)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load tokens file: %s", e)
                self._tokens = {}
        else:
            self._tokens = {}

    def _save_tokens(self):
        """Persist tokens to disk."""
        try:
            with open(TOKENS_FILE, "w") as f:
                json.dump(self._tokens, f, indent=2)
            logger.info("Saved integration tokens to %s", TOKENS_FILE)
        except IOError as e:
            logger.error("Failed to save tokens: %s", e)

    def save_tokens(self, provider: str, tokens: dict):
        """Store tokens for a provider and persist to disk."""
        tokens["saved_at"] = time.time()
        self._tokens[provider] = tokens
        self._save_tokens()

    def load_tokens(self, provider: str) -> dict | None:
        """Retrieve stored tokens for a provider, or None if not present."""
        return self._tokens.get(provider)

    def clear_tokens(self, provider: str):
        """Remove tokens for a provider (disconnect)."""
        if provider in self._tokens:
            del self._tokens[provider]
            self._save_tokens()
            logger.info("Cleared tokens for %s", provider)

    def is_connected(self, provider: str) -> bool:
        """Check if valid (non-expired) tokens exist for a provider."""
        tokens = self._tokens.get(provider)
        if not tokens:
            return False
        # Check if the access token exists
        if not tokens.get("access_token"):
            return False
        # Check expiry — allow 5-minute buffer
        expires_at = tokens.get("expires_at", 0)
        if expires_at and time.time() > (expires_at - 300):
            # Token expired but we might have a refresh token
            return bool(tokens.get("refresh_token"))
        return True

    def is_token_expired(self, provider: str) -> bool:
        """Check if the access token is expired (needs refresh)."""
        tokens = self._tokens.get(provider)
        if not tokens:
            return True
        expires_at = tokens.get("expires_at", 0)
        if not expires_at:
            return False  # No expiry info, assume valid
        return time.time() > (expires_at - 300)  # 5-minute buffer

    # ── Credential persistence ─────────────────────────────────────

    def _load_credentials(self):
        """Load OAuth client credentials from disk."""
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, "r") as f:
                    self._credentials = json.load(f)
                logger.info("Loaded integration credentials")
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load credentials file: %s", e)
                self._credentials = {}
        else:
            self._credentials = {}

    def _save_credentials(self):
        """Persist credentials to disk."""
        try:
            with open(CREDENTIALS_FILE, "w") as f:
                json.dump(self._credentials, f, indent=2)
            logger.info("Saved integration credentials")
        except IOError as e:
            logger.error("Failed to save credentials: %s", e)

    def save_credentials(self, provider: str, client_id: str, client_secret: str):
        """Store OAuth client credentials for a provider."""
        self._credentials[provider] = {
            "client_id": client_id,
            "client_secret": client_secret,
        }
        self._save_credentials()

    def get_credentials(self, provider: str) -> dict | None:
        """Get stored credentials for a provider."""
        return self._credentials.get(provider)

    def has_credentials(self, provider: str) -> bool:
        """Check if client credentials are configured for a provider."""
        creds = self._credentials.get(provider)
        return bool(creds and creds.get("client_id") and creds.get("client_secret"))

    # ── Status summary ─────────────────────────────────────────────

    def get_all_status(self) -> dict:
        """Return connection status for all providers."""
        status = {}
        for provider in self.PROVIDERS:
            tokens = self._tokens.get(provider, {})
            status[provider] = {
                "connected": self.is_connected(provider),
                "has_credentials": self.has_credentials(provider),
                "email": tokens.get("email", None),
                "display_name": tokens.get("display_name", None),
            }
        return status
