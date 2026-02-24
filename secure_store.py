"""
Secure Credential Store — macOS Keychain integration via keyring library.

Provides encrypted storage for API keys, OAuth tokens, and OAuth credentials.
Falls back to plaintext config files if keyring is unavailable (with a warning).

Usage:
    from secure_store import secure_store

    # API keys
    secure_store.set_api_key("gemini", "your-key-here")
    key = secure_store.get_api_key("gemini")

    # OAuth tokens
    secure_store.set_oauth_tokens("google", {"access_token": "...", ...})
    tokens = secure_store.get_oauth_tokens("google")
"""

import json
import logging

logger = logging.getLogger(__name__)

SERVICE_NAME = "com.notsure.audio-summarizer"

# Try to import keyring; graceful fallback if unavailable
try:
    import keyring
    KEYRING_AVAILABLE = True
except ImportError:
    KEYRING_AVAILABLE = False
    logger.warning(
        "keyring library not installed — credentials will NOT be stored securely. "
        "Install with: pip install keyring"
    )


class SecureCredentialStore:
    """Manages secure storage of secrets via the OS keychain."""

    # Key prefixes to namespace different credential types
    _API_KEY_PREFIX = "api_key"
    _OAUTH_TOKEN_PREFIX = "oauth_tokens"
    _OAUTH_CRED_PREFIX = "oauth_credentials"

    def __init__(self):
        self._available = KEYRING_AVAILABLE
        if self._available:
            # Verify keychain access works at init time
            try:
                keyring.get_password(SERVICE_NAME, "__probe__")
                logger.info("Keychain access verified")
            except Exception as e:
                logger.warning("Keychain access failed, falling back to plaintext: %s", e)
                self._available = False

    @property
    def is_available(self) -> bool:
        """Whether secure storage is operational."""
        return self._available

    # ── API Keys ──────────────────────────────────────────────────────

    def get_api_key(self, provider: str) -> str | None:
        """Retrieve an API key from the keychain. Returns None if not found."""
        if not self._available:
            return None
        try:
            key = keyring.get_password(SERVICE_NAME, f"{self._API_KEY_PREFIX}.{provider}")
            return key  # None if not found
        except Exception as e:
            logger.error("Failed to read API key for %s from keychain: %s", provider, e)
            return None

    def set_api_key(self, provider: str, key: str) -> bool:
        """Store an API key in the keychain. Returns True on success."""
        if not self._available:
            logger.warning("Cannot store API key — keychain not available")
            return False
        try:
            keyring.set_password(SERVICE_NAME, f"{self._API_KEY_PREFIX}.{provider}", key)
            logger.info("API key for %s stored in keychain", provider)
            return True
        except Exception as e:
            logger.error("Failed to store API key for %s: %s", provider, e)
            return False

    def delete_api_key(self, provider: str) -> bool:
        """Remove an API key from the keychain. Returns True on success."""
        if not self._available:
            return False
        try:
            keyring.delete_password(SERVICE_NAME, f"{self._API_KEY_PREFIX}.{provider}")
            logger.info("API key for %s removed from keychain", provider)
            return True
        except keyring.errors.PasswordDeleteError:
            return True  # Already gone, that's fine
        except Exception as e:
            logger.error("Failed to delete API key for %s: %s", provider, e)
            return False

    # ── OAuth Tokens ──────────────────────────────────────────────────

    def get_oauth_tokens(self, provider: str) -> dict | None:
        """Retrieve OAuth tokens from the keychain. Returns None if not found."""
        if not self._available:
            return None
        try:
            raw = keyring.get_password(SERVICE_NAME, f"{self._OAUTH_TOKEN_PREFIX}.{provider}")
            if raw:
                return json.loads(raw)
            return None
        except Exception as e:
            logger.error("Failed to read OAuth tokens for %s: %s", provider, e)
            return None

    def set_oauth_tokens(self, provider: str, tokens: dict) -> bool:
        """Store OAuth tokens in the keychain. Returns True on success."""
        if not self._available:
            logger.warning("Cannot store OAuth tokens — keychain not available")
            return False
        try:
            raw = json.dumps(tokens)
            keyring.set_password(SERVICE_NAME, f"{self._OAUTH_TOKEN_PREFIX}.{provider}", raw)
            logger.info("OAuth tokens for %s stored in keychain", provider)
            return True
        except Exception as e:
            logger.error("Failed to store OAuth tokens for %s: %s", provider, e)
            return False

    def delete_oauth_tokens(self, provider: str) -> bool:
        """Remove OAuth tokens from the keychain."""
        if not self._available:
            return False
        try:
            keyring.delete_password(SERVICE_NAME, f"{self._OAUTH_TOKEN_PREFIX}.{provider}")
            return True
        except keyring.errors.PasswordDeleteError:
            return True
        except Exception as e:
            logger.error("Failed to delete OAuth tokens for %s: %s", provider, e)
            return False

    # ── OAuth Credentials (client_id/client_secret) ───────────────────

    def get_oauth_credentials(self, provider: str) -> dict | None:
        """Retrieve OAuth client credentials from the keychain."""
        if not self._available:
            return None
        try:
            raw = keyring.get_password(SERVICE_NAME, f"{self._OAUTH_CRED_PREFIX}.{provider}")
            if raw:
                return json.loads(raw)
            return None
        except Exception as e:
            logger.error("Failed to read OAuth credentials for %s: %s", provider, e)
            return None

    def set_oauth_credentials(self, provider: str, client_id: str, client_secret: str) -> bool:
        """Store OAuth client credentials in the keychain."""
        if not self._available:
            logger.warning("Cannot store OAuth credentials — keychain not available")
            return False
        try:
            raw = json.dumps({"client_id": client_id, "client_secret": client_secret})
            keyring.set_password(SERVICE_NAME, f"{self._OAUTH_CRED_PREFIX}.{provider}", raw)
            logger.info("OAuth credentials for %s stored in keychain", provider)
            return True
        except Exception as e:
            logger.error("Failed to store OAuth credentials for %s: %s", provider, e)
            return False

    def delete_oauth_credentials(self, provider: str) -> bool:
        """Remove OAuth client credentials from the keychain."""
        if not self._available:
            return False
        try:
            keyring.delete_password(SERVICE_NAME, f"{self._OAUTH_CRED_PREFIX}.{provider}")
            return True
        except keyring.errors.PasswordDeleteError:
            return True
        except Exception as e:
            logger.error("Failed to delete OAuth credentials for %s: %s", provider, e)
            return False


# Module-level singleton for convenience
secure_store = SecureCredentialStore()
