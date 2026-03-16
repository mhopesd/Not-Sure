"""Tests for configuration loading and LLM auto-detection."""

import pytest
from unittest.mock import patch, MagicMock


class TestConfigDefaults:
    def test_default_llm_when_no_keys(self, app):
        # auto_detect_llm uses _get_api_key which checks keychain first
        with patch.object(app, "_get_api_key", return_value=None):
            app.config["SETTINGS"]["default_llm"] = "auto"
            app.auto_detect_llm()
            assert app.config["SETTINGS"]["default_llm"] == "ollama"

    def test_has_required_config_sections(self, app):
        assert "SETTINGS" in app.config
        assert "API_KEYS" in app.config

    def test_default_ollama_model(self, app):
        assert app.config["SETTINGS"].get("ollama_model") == "llama3:8b"


class TestAutoDetectLLM:
    def test_prefers_openai(self, app):
        app.config["SETTINGS"]["default_llm"] = "auto"

        def fake_key(provider):
            return {"openai": "sk-test", "gemini": "gem-test"}.get(provider)

        with patch.object(app, "_get_api_key", side_effect=fake_key):
            app.auto_detect_llm()
        assert app.config["SETTINGS"]["default_llm"] == "openai"

    def test_falls_back_to_gemini(self, app):
        app.config["SETTINGS"]["default_llm"] = "auto"

        def fake_key(provider):
            return {"gemini": "gem-test"}.get(provider)

        with patch.object(app, "_get_api_key", side_effect=fake_key):
            app.auto_detect_llm()
        assert app.config["SETTINGS"]["default_llm"] == "gemini"

    def test_falls_back_to_anthropic(self, app):
        app.config["SETTINGS"]["default_llm"] = "auto"

        def fake_key(provider):
            return {"anthropic": "ant-test"}.get(provider)

        with patch.object(app, "_get_api_key", side_effect=fake_key):
            app.auto_detect_llm()
        assert app.config["SETTINGS"]["default_llm"] == "anthropic"

    def test_skips_when_not_auto(self, app):
        app.config["SETTINGS"]["default_llm"] = "gemini"
        app.auto_detect_llm()
        assert app.config["SETTINGS"]["default_llm"] == "gemini"


class TestGetApiKey:
    @patch("backend.secure_store")
    def test_returns_keychain_key_first(self, mock_store, app):
        mock_store.get_api_key.return_value = "keychain-key"
        assert app._get_api_key("gemini") == "keychain-key"

    @patch("backend.secure_store")
    def test_falls_back_to_config(self, mock_store, app):
        mock_store.get_api_key.return_value = None
        app.config["API_KEYS"]["gemini"] = "config-key"
        assert app._get_api_key("gemini") == "config-key"

    @patch("backend.secure_store")
    def test_strips_quotes_from_config_key(self, mock_store, app):
        mock_store.get_api_key.return_value = None
        app.config["API_KEYS"]["gemini"] = '"quoted-key"'
        result = app._get_api_key("gemini")
        assert result == "quoted-key"
