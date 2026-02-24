"""
OAuth Token Manager — Handles persistent storage, loading, and refresh
of OAuth2 tokens for Microsoft and Google integrations.

Tokens and credentials are stored securely in the macOS Keychain via the
secure_store module when available. Falls back to plaintext JSON files
(integration_tokens.json, integration_credentials.json) if keychain is
unavailable. Both JSON files are gitignored.
"""

import json
import os
import time
import logging

logger = logging.getLogger(__name__)

from secure_store import secure_store

# File paths relative to the project root (used as fallback only)
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
        """Load tokens from keychain (preferred) or disk (fallback)."""
        # Try keychain first for each provider
        for provider in self.PROVIDERS:
            kc_tokens = secure_store.get_oauth_tokens(provider)
            if kc_tokens:
                self._tokens[provider] = kc_tokens

        # Fall back to file for any providers not found in keychain
        if os.path.exists(TOKENS_FILE):
            try:
                with open(TOKENS_FILE, "r") as f:
                    file_tokens = json.load(f)
                # Migrate file tokens to keychain and merge
                migrated_any = False
                for provider, tokens in file_tokens.items():
                    if provider not in self._tokens:
                        self._tokens[provider] = tokens
                        if secure_store.set_oauth_tokens(provider, tokens):
                            migrated_any = True
                            logger.info("Migrated %s tokens to keychain", provider)
                # Delete file after successful migration
                if migrated_any and all(
                    secure_store.get_oauth_tokens(p) for p in file_tokens
                ):
                    try:
                        os.remove(TOKENS_FILE)
                        logger.info("Removed plaintext tokens file after migration")
                    except OSError:
                        pass
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load tokens file: %s", e)

        if self._tokens:
            logger.info("Loaded integration tokens for: %s", list(self._tokens.keys()))

    def _save_tokens(self):
        """Persist tokens to keychain (preferred) or disk (fallback)."""
        saved_to_keychain = True
        for provider, tokens in self._tokens.items():
            if not secure_store.set_oauth_tokens(provider, tokens):
                saved_to_keychain = False

        # Only write to file as fallback if keychain failed
        if not saved_to_keychain:
            try:
                with open(TOKENS_FILE, "w") as f:
                    json.dump(self._tokens, f, indent=2)
                logger.info("Saved integration tokens to %s (keychain fallback)", TOKENS_FILE)
            except IOError as e:
                logger.error("Failed to save tokens: %s", e)

    def save_tokens(self, provider: str, tokens: dict):
        """Store tokens for a provider and persist."""
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
        secure_store.delete_oauth_tokens(provider)
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
        """Load OAuth client credentials from keychain (preferred) or disk (fallback)."""
        # Try keychain first
        for provider in self.PROVIDERS:
            kc_creds = secure_store.get_oauth_credentials(provider)
            if kc_creds:
                self._credentials[provider] = kc_creds

        # Fall back to file for any providers not in keychain
        if os.path.exists(CREDENTIALS_FILE):
            try:
                with open(CREDENTIALS_FILE, "r") as f:
                    file_creds = json.load(f)
                migrated_any = False
                for provider, creds in file_creds.items():
                    if provider not in self._credentials:
                        self._credentials[provider] = creds
                        if secure_store.set_oauth_credentials(
                            provider, creds.get("client_id", ""), creds.get("client_secret", "")
                        ):
                            migrated_any = True
                            logger.info("Migrated %s credentials to keychain", provider)
                # Delete file after successful migration
                if migrated_any and all(
                    secure_store.get_oauth_credentials(p) for p in file_creds
                ):
                    try:
                        os.remove(CREDENTIALS_FILE)
                        logger.info("Removed plaintext credentials file after migration")
                    except OSError:
                        pass
            except (json.JSONDecodeError, IOError) as e:
                logger.warning("Failed to load credentials file: %s", e)

        if self._credentials:
            logger.info("Loaded integration credentials for: %s", list(self._credentials.keys()))

    def _save_credentials(self):
        """Persist credentials to keychain (preferred) or disk (fallback)."""
        saved_to_keychain = True
        for provider, creds in self._credentials.items():
            if not secure_store.set_oauth_credentials(
                provider, creds.get("client_id", ""), creds.get("client_secret", "")
            ):
                saved_to_keychain = False

        if not saved_to_keychain:
            try:
                with open(CREDENTIALS_FILE, "w") as f:
                    json.dump(self._credentials, f, indent=2)
                logger.info("Saved integration credentials to %s (keychain fallback)", CREDENTIALS_FILE)
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
