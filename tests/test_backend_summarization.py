"""Tests for LLM summarization routing and providers."""

import json
import pytest
from unittest.mock import patch, MagicMock


class TestGenerateSummaryRouting:
    def test_routes_to_gemini(self, app):
        app.config["SETTINGS"]["default_llm"] = "gemini"
        with patch.object(app, "_summarize_with_gemini", return_value={"title": "T"}) as m:
            app.generate_summary("transcript", "/audio.wav")
            m.assert_called_once_with("transcript", "/audio.wav")

    def test_routes_to_ollama(self, app):
        app.config["SETTINGS"]["default_llm"] = "ollama"
        with patch.object(app, "_summarize_with_ollama", return_value={"title": "T"}) as m:
            app.generate_summary("transcript", "/audio.wav")
            m.assert_called_once_with("transcript", "/audio.wav")

    def test_routes_to_openai(self, app):
        app.config["SETTINGS"]["default_llm"] = "openai"
        with patch.object(app, "_summarize_with_openai", return_value={"title": "T"}) as m:
            app.generate_summary("transcript", "/audio.wav")
            m.assert_called_once_with("transcript", "/audio.wav")

    def test_routes_to_anthropic(self, app):
        app.config["SETTINGS"]["default_llm"] = "anthropic"
        with patch.object(app, "_summarize_with_anthropic", return_value={"title": "T"}) as m:
            app.generate_summary("transcript", "/audio.wav")
            m.assert_called_once_with("transcript", "/audio.wav")

    def test_unsupported_llm_returns_error(self, app):
        app.config["SETTINGS"]["default_llm"] = "unknown_llm"
        result = app.generate_summary("transcript")
        assert result["title"] == "Error Processing"
        assert "Unsupported LLM" in result["executive_summary"]


class TestOllamaSummarization:
    @patch("backend.requests.get")
    @patch("backend.requests.post")
    def test_success(self, mock_post, mock_get, app):
        mock_get.return_value = MagicMock(status_code=200)
        response_json = {
            "title": "Test Meeting",
            "executive_summary": "A summary",
            "speaker_info": {"count": 1, "list": ["Speaker 1"]},
            "highlights": ["Point 1"],
            "full_summary_sections": [],
            "tasks": [],
        }
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"response": json.dumps(response_json)},
        )
        result = app._summarize_with_ollama("Test transcript")
        assert result["title"] == "Test Meeting"
        assert result["transcript"] == "Test transcript"

    @patch("backend.requests.get")
    def test_not_running(self, mock_get, app):
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        result = app._summarize_with_ollama("Test transcript")
        assert result["title"] == "Error Processing"
        assert "Ollama not running" in result["executive_summary"]

    @patch("backend.requests.get")
    @patch("backend.requests.post")
    def test_invalid_json_salvages_response(self, mock_post, mock_get, app):
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200, json=lambda: {"response": "not json {"}
        )
        result = app._summarize_with_ollama("Test transcript")
        # Invalid JSON is salvaged into a basic summary, not an error
        assert result["transcript"] == "Test transcript"
        assert "tasks" in result
        assert result["title"] is not None

    @patch("backend.requests.get")
    def test_timeout(self, mock_get, app):
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        result = app._summarize_with_ollama("Test transcript")
        assert result["title"] == "Error Processing"
        assert "timed out" in result["executive_summary"]

    @patch("backend.requests.get")
    @patch("backend.requests.post")
    def test_strips_markdown_wrappers(self, mock_post, mock_get, app):
        mock_get.return_value = MagicMock(status_code=200)
        inner = {"title": "Wrapped", "executive_summary": "x", "highlights": [], "tasks": []}
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"response": f"```json\n{json.dumps(inner)}\n```"},
        )
        result = app._summarize_with_ollama("t")
        assert result["title"] == "Wrapped"


class TestGeminiSummarization:
    def test_missing_api_key(self, app):
        app.config["API_KEYS"]["gemini"] = ""
        with patch("backend.GOOGLE_GENAI_AVAILABLE", True), \
             patch("backend.secure_store") as mock_store:
            mock_store.get_api_key.return_value = None
            result = app._summarize_with_gemini("transcript")
        assert result["title"] == "Error Processing"
        assert "API Key Missing" in result["executive_summary"]

    def test_library_not_installed(self, app):
        with patch("backend.GOOGLE_GENAI_AVAILABLE", False):
            result = app._summarize_with_gemini("transcript")
        assert result["title"] == "Error Processing"
        assert "Lib Missing" in result["executive_summary"]

    @patch("backend.genai")
    @patch("backend.GOOGLE_GENAI_AVAILABLE", True)
    def test_success(self, mock_genai, app):
        app.config["API_KEYS"]["gemini"] = "test-key"
        resp_json = {
            "title": "Gemini Meeting",
            "executive_summary": "summary",
            "speaker_info": {"count": 2, "list": ["Alice", "Bob"]},
            "highlights": ["point"],
            "full_summary_sections": [],
            "tasks": [],
        }
        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = json.dumps(resp_json)
        mock_client.models.generate_content.return_value = mock_response
        result = app._summarize_with_gemini("transcript")
        assert result["title"] == "Gemini Meeting"


class TestOpenAISummarization:
    def test_missing_api_key(self, app):
        app.config["API_KEYS"]["openai"] = ""
        with patch("backend.OPENAI_AVAILABLE", True), \
             patch("backend.secure_store") as mock_store:
            mock_store.get_api_key.return_value = None
            result = app._summarize_with_openai("transcript")
        assert "API Key Missing" in result["executive_summary"]

    def test_library_not_installed(self, app):
        with patch("backend.OPENAI_AVAILABLE", False):
            result = app._summarize_with_openai("transcript")
        assert "not installed" in result["executive_summary"]

    @patch("backend.openai", create=True)
    @patch("backend.OPENAI_AVAILABLE", True)
    def test_success(self, mock_openai, app):
        app.config["API_KEYS"]["openai"] = "sk-test"
        resp_json = {
            "title": "OpenAI Meeting",
            "executive_summary": "summary",
            "highlights": [],
            "tasks": [],
        }
        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_msg = MagicMock(content=json.dumps(resp_json))
        mock_choice = MagicMock(message=mock_msg)
        mock_client.chat.completions.create.return_value = MagicMock(choices=[mock_choice])
        result = app._summarize_with_openai("transcript")
        assert result["title"] == "OpenAI Meeting"


class TestAnthropicSummarization:
    def test_missing_api_key(self, app):
        app.config["API_KEYS"]["anthropic"] = ""
        with patch("backend.ANTHROPIC_AVAILABLE", True), \
             patch("backend.secure_store") as mock_store:
            mock_store.get_api_key.return_value = None
            result = app._summarize_with_anthropic("transcript")
        assert "API Key Missing" in result["executive_summary"]

    def test_library_not_installed(self, app):
        with patch("backend.ANTHROPIC_AVAILABLE", False):
            result = app._summarize_with_anthropic("transcript")
        assert "not installed" in result["executive_summary"]

    @patch("backend.anthropic", create=True)
    @patch("backend.ANTHROPIC_AVAILABLE", True)
    def test_success(self, mock_anthropic, app):
        app.config["API_KEYS"]["anthropic"] = "ant-test"
        resp_json = {
            "title": "Anthropic Meeting",
            "executive_summary": "summary",
            "highlights": [],
            "tasks": [],
        }
        mock_client = MagicMock()
        mock_content = MagicMock(text=json.dumps(resp_json))
        mock_client.messages.create.return_value = MagicMock(content=[mock_content])
        mock_anthropic.Anthropic.return_value = mock_client
        result = app._summarize_with_anthropic("transcript")
        assert result["title"] == "Anthropic Meeting"
