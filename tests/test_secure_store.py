"""Tests for SecureCredentialStore keychain integration."""

import json
import pytest
from unittest.mock import patch, MagicMock

from secure_store import SecureCredentialStore, SERVICE_NAME


@pytest.fixture()
def store():
    """A SecureCredentialStore with keychain mocked as available."""
    with patch("secure_store.KEYRING_AVAILABLE", True), \
         patch("secure_store.keyring") as mock_kr:
        mock_kr.get_password.return_value = None  # probe succeeds
        s = SecureCredentialStore()
        s._keyring = mock_kr  # stash for assertions
        yield s


@pytest.fixture()
def unavailable_store():
    """A SecureCredentialStore with keychain unavailable."""
    with patch("secure_store.KEYRING_AVAILABLE", False):
        return SecureCredentialStore()


class TestAvailability:
    def test_available_when_keyring_works(self, store):
        assert store.is_available is True

    def test_unavailable_without_keyring(self, unavailable_store):
        assert unavailable_store.is_available is False

    def test_falls_back_on_probe_failure(self):
        with patch("secure_store.KEYRING_AVAILABLE", True), \
             patch("secure_store.keyring") as mock_kr:
            mock_kr.get_password.side_effect = Exception("no keychain")
            s = SecureCredentialStore()
            assert s.is_available is False


class TestApiKeys:
    def test_get_api_key(self, store):
        store._keyring.get_password.return_value = "my-key"
        assert store.get_api_key("gemini") == "my-key"
        store._keyring.get_password.assert_called_with(SERVICE_NAME, "api_key.gemini")

    def test_get_api_key_returns_none_when_unavailable(self, unavailable_store):
        assert unavailable_store.get_api_key("gemini") is None

    def test_set_api_key(self, store):
        assert store.set_api_key("openai", "sk-123") is True
        store._keyring.set_password.assert_called_with(SERVICE_NAME, "api_key.openai", "sk-123")

    def test_set_api_key_returns_false_when_unavailable(self, unavailable_store):
        assert unavailable_store.set_api_key("openai", "sk-123") is False

    def test_delete_api_key(self, store):
        assert store.delete_api_key("openai") is True
        store._keyring.delete_password.assert_called_with(SERVICE_NAME, "api_key.openai")

    def test_delete_already_gone(self, store):
        # Create a real PasswordDeleteError since keyring is mocked
        from keyring.errors import PasswordDeleteError
        store._keyring.delete_password.side_effect = PasswordDeleteError()
        # But the code catches `keyring.errors.PasswordDeleteError` via the real import
        # so we need to patch the keyring module used inside secure_store
        with patch("secure_store.keyring") as mock_kr:
            mock_kr.delete_password.side_effect = PasswordDeleteError()
            mock_kr.errors.PasswordDeleteError = PasswordDeleteError
            store._available = True
            assert store.delete_api_key("openai") is True

    def test_get_api_key_handles_exception(self, store):
        store._keyring.get_password.side_effect = Exception("boom")
        assert store.get_api_key("gemini") is None


class TestOAuthTokens:
    def test_set_and_get_tokens(self, store):
        tokens = {"access_token": "at", "refresh_token": "rt"}
        store.set_oauth_tokens("google", tokens)
        store._keyring.set_password.assert_called_once()

        # Verify JSON serialization
        call_args = store._keyring.set_password.call_args
        stored = json.loads(call_args[0][2])
        assert stored["access_token"] == "at"

    def test_get_tokens_deserializes_json(self, store):
        store._keyring.get_password.return_value = json.dumps({"access_token": "at"})
        result = store.get_oauth_tokens("google")
        assert result["access_token"] == "at"

    def test_get_tokens_returns_none_when_empty(self, store):
        store._keyring.get_password.return_value = None
        assert store.get_oauth_tokens("google") is None

    def test_tokens_unavailable(self, unavailable_store):
        assert unavailable_store.get_oauth_tokens("google") is None
        assert unavailable_store.set_oauth_tokens("google", {}) is False
        assert unavailable_store.delete_oauth_tokens("google") is False


class TestOAuthCredentials:
    def test_set_credentials(self, store):
        assert store.set_oauth_credentials("google", "client-id", "client-secret") is True
        call_args = store._keyring.set_password.call_args
        stored = json.loads(call_args[0][2])
        assert stored["client_id"] == "client-id"
        assert stored["client_secret"] == "client-secret"

    def test_get_credentials(self, store):
        store._keyring.get_password.return_value = json.dumps(
            {"client_id": "cid", "client_secret": "cs"}
        )
        result = store.get_oauth_credentials("microsoft")
        assert result["client_id"] == "cid"

    def test_credentials_unavailable(self, unavailable_store):
        assert unavailable_store.get_oauth_credentials("google") is None
        assert unavailable_store.set_oauth_credentials("google", "a", "b") is False
