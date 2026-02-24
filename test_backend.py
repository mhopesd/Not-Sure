"""
Unit tests for backend.py

Run with: python -m unittest test_backend -v
"""

import unittest
from unittest.mock import patch, MagicMock, PropertyMock
import json
import sys

# Mock heavy dependencies before importing backend
sys.modules['whisper'] = MagicMock()
sys.modules['sounddevice'] = MagicMock()

from backend import EnhancedAudioApp


class TestEnhancedAudioAppConfig(unittest.TestCase):
    """Test configuration loading and defaults."""

    @patch('backend.sd')
    @patch('backend.whisper')
    @patch('os.path.exists')
    def test_default_config_values(self, mock_exists, mock_whisper, mock_sd):
        """Test that default config values are set correctly."""
        mock_sd.query_hostapis.return_value = []
        mock_sd.query_devices.return_value = []
        mock_sd.default.device = [0, 0]
        # Simulate no config file exists to test defaults
        mock_exists.return_value = False

        app = EnhancedAudioApp()

        # With no config file and no API keys, should fall back to ollama
        self.assertEqual(app.config['SETTINGS'].get('default_llm'), 'ollama')
        self.assertEqual(app.config['SETTINGS'].get('ollama_model'), 'llama3:8b')
        self.assertIn('API_KEYS', app.config)

    @patch('backend.sd')
    @patch('backend.whisper')
    def test_auto_detect_llm_with_gemini_key(self, mock_whisper, mock_sd):
        """Test that auto-detect selects gemini when key is present."""
        mock_sd.query_hostapis.return_value = []
        mock_sd.query_devices.return_value = []
        mock_sd.default.device = [0, 0]

        app = EnhancedAudioApp()
        # Simulate having a Gemini API key
        app.config['SETTINGS']['default_llm'] = 'auto'
        app.config['API_KEYS']['gemini'] = 'test-api-key'
        app.auto_detect_llm()

        self.assertEqual(app.config['SETTINGS']['default_llm'], 'gemini')

    @patch('backend.sd')
    @patch('backend.whisper')
    def test_auto_detect_llm_fallback_to_ollama(self, mock_whisper, mock_sd):
        """Test that auto-detect falls back to ollama when no API keys."""
        mock_sd.query_hostapis.return_value = []
        mock_sd.query_devices.return_value = []
        mock_sd.default.device = [0, 0]

        app = EnhancedAudioApp()
        # Clear all API keys and reset to auto
        app.config['API_KEYS'] = {'openai': '', 'anthropic': '', 'gemini': ''}
        app.config['SETTINGS']['default_llm'] = 'auto'
        app.auto_detect_llm()

        self.assertEqual(app.config['SETTINGS']['default_llm'], 'ollama')


class TestOllamaSummarization(unittest.TestCase):
    """Test Ollama summarization functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    @patch('backend.requests.get')
    @patch('backend.requests.post')
    def test_ollama_success(self, mock_post, mock_get):
        """Test successful Ollama summarization."""
        # Mock health check
        mock_get.return_value = MagicMock(status_code=200)

        # Mock generate response
        response_json = {
            "title": "Test Meeting",
            "executive_summary": "A test summary",
            "speaker_info": {"count": 1, "list": ["Speaker 1"]},
            "highlights": ["Point 1"],
            "full_summary_sections": [],
            "tasks": []
        }
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"response": json.dumps(response_json)}
        )

        result = self.app._summarize_with_ollama("Test transcript")

        self.assertEqual(result["title"], "Test Meeting")
        self.assertEqual(result["executive_summary"], "A test summary")
        self.assertEqual(result["transcript"], "Test transcript")
        self.assertIn("date", result)

    @patch('backend.requests.get')
    def test_ollama_not_running(self, mock_get):
        """Test error handling when Ollama is not running."""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()

        result = self.app._summarize_with_ollama("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("Ollama not running", result["executive_summary"])
        self.assertEqual(result["transcript"], "Test transcript")

    @patch('backend.requests.get')
    @patch('backend.requests.post')
    def test_ollama_invalid_json_response(self, mock_post, mock_get):
        """Test error handling for invalid JSON response."""
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"response": "not valid json {"}
        )

        result = self.app._summarize_with_ollama("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("invalid JSON", result["executive_summary"])

    @patch('backend.requests.get')
    def test_ollama_health_check_timeout(self, mock_get):
        """Test error handling for health check timeout."""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()

        result = self.app._summarize_with_ollama("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("timed out", result["executive_summary"])

    @patch('backend.requests.get')
    @patch('backend.requests.post')
    def test_ollama_request_timeout(self, mock_post, mock_get):
        """Test error handling for request timeout."""
        import requests
        mock_get.return_value = MagicMock(status_code=200)
        mock_post.side_effect = requests.exceptions.Timeout()

        result = self.app._summarize_with_ollama("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("timed out", result["executive_summary"])

    @patch('backend.requests.get')
    @patch('backend.requests.post')
    def test_ollama_strips_markdown_wrappers(self, mock_post, mock_get):
        """Test that markdown code block wrappers are stripped."""
        mock_get.return_value = MagicMock(status_code=200)

        response_json = {
            "title": "Wrapped Response",
            "executive_summary": "Test",
            "highlights": [],
            "tasks": []
        }
        # Wrap in markdown code blocks
        wrapped_response = f"```json\n{json.dumps(response_json)}\n```"
        mock_post.return_value = MagicMock(
            status_code=200,
            json=lambda: {"response": wrapped_response}
        )

        result = self.app._summarize_with_ollama("Test transcript")

        self.assertEqual(result["title"], "Wrapped Response")


class TestGeminiSummarization(unittest.TestCase):
    """Test Gemini summarization functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_gemini_missing_api_key(self):
        """Test error handling when Gemini API key is missing."""
        self.app.config['API_KEYS']['gemini'] = ''

        with patch('backend.GOOGLE_GENAI_AVAILABLE', True):
            result = self.app._summarize_with_gemini("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("API Key Missing", result["executive_summary"])

    def test_gemini_library_not_installed(self):
        """Test error handling when google-genai library is not installed."""
        with patch('backend.GOOGLE_GENAI_AVAILABLE', False):
            result = self.app._summarize_with_gemini("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("Lib Missing", result["executive_summary"])

    @patch('backend.genai')
    @patch('backend.GOOGLE_GENAI_AVAILABLE', True)
    def test_gemini_success(self, mock_genai):
        """Test successful Gemini summarization."""
        self.app.config['API_KEYS']['gemini'] = 'test-api-key'

        response_json = {
            "title": "Gemini Meeting",
            "executive_summary": "A gemini summary",
            "speaker_info": {"count": 2, "list": ["Alice", "Bob"]},
            "highlights": ["Discussion point"],
            "full_summary_sections": [],
            "tasks": []
        }

        mock_client = MagicMock()
        mock_genai.Client.return_value = mock_client
        mock_response = MagicMock()
        mock_response.text = json.dumps(response_json)
        mock_client.models.generate_content.return_value = mock_response

        result = self.app._summarize_with_gemini("Test transcript")

        self.assertEqual(result["title"], "Gemini Meeting")
        self.assertEqual(result["transcript"], "Test transcript")


class TestGenerateSummaryRouting(unittest.TestCase):
    """Test routing in generate_summary method."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_routes_to_gemini(self):
        """Test that 'gemini' setting routes to Gemini summarizer."""
        self.app.config['SETTINGS']['default_llm'] = 'gemini'

        with patch.object(self.app, '_summarize_with_gemini') as mock_gemini:
            mock_gemini.return_value = {"title": "Test"}
            self.app.generate_summary("transcript", "/path/to/audio.wav")
            mock_gemini.assert_called_once_with("transcript", "/path/to/audio.wav")

    def test_routes_to_ollama(self):
        """Test that 'ollama' setting routes to Ollama summarizer."""
        self.app.config['SETTINGS']['default_llm'] = 'ollama'

        with patch.object(self.app, '_summarize_with_ollama') as mock_ollama:
            mock_ollama.return_value = {"title": "Test"}
            self.app.generate_summary("transcript", "/path/to/audio.wav")
            mock_ollama.assert_called_once_with("transcript", "/path/to/audio.wav")

    def test_unsupported_llm_returns_error(self):
        """Test that unsupported LLM returns error summary."""
        self.app.config['SETTINGS']['default_llm'] = 'unknown_llm'

        result = self.app.generate_summary("transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("Unsupported LLM", result["executive_summary"])


class TestErrorSummary(unittest.TestCase):
    """Test error_summary helper method."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_error_summary_structure(self):
        """Test that error_summary returns correct structure."""
        result = self.app.error_summary("Test error message", "Original transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertEqual(result["executive_summary"], "Test error message")
        self.assertEqual(result["full_summary"], "")
        self.assertEqual(result["tasks"], [])
        self.assertEqual(result["transcript"], "Original transcript")


class TestHelperMethods(unittest.TestCase):
    """Test helper methods."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_format_time_seconds_only(self):
        """Test _format_time with seconds only."""
        result = self.app._format_time(45)
        self.assertEqual(result, "00:45")

    def test_format_time_with_minutes(self):
        """Test _format_time with minutes and seconds."""
        result = self.app._format_time(125)
        self.assertEqual(result, "02:05")

    def test_format_time_zero(self):
        """Test _format_time with zero."""
        result = self.app._format_time(0)
        self.assertEqual(result, "00:00")

    def test_set_mode_microphone(self):
        """Test set_mode for Microphone."""
        self.app.set_mode("Microphone")
        self.assertEqual(self.app.recording_mode, "microphone")

    def test_set_mode_system_audio(self):
        """Test set_mode for System Audio."""
        self.app.set_mode("System Audio")
        self.assertEqual(self.app.recording_mode, "system")

    def test_set_mode_hybrid(self):
        """Test set_mode for Hybrid."""
        self.app.set_mode("Hybrid")
        self.assertEqual(self.app.recording_mode, "hybrid")

    def test_set_mode_unknown_defaults_to_microphone(self):
        """Test set_mode with unknown value defaults to microphone."""
        self.app.set_mode("UnknownMode")
        self.assertEqual(self.app.recording_mode, "microphone")


class TestOpenAISummarization(unittest.TestCase):
    """Test OpenAI summarization functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_openai_missing_api_key(self):
        """Test error handling when OpenAI API key is missing."""
        self.app.config['API_KEYS']['openai'] = ''

        with patch('backend.OPENAI_AVAILABLE', True):
            result = self.app._summarize_with_openai("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("API Key Missing", result["executive_summary"])

    def test_openai_library_not_installed(self):
        """Test error handling when OpenAI library is not installed."""
        with patch('backend.OPENAI_AVAILABLE', False):
            result = self.app._summarize_with_openai("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("not installed", result["executive_summary"])

    @patch('backend.openai')
    @patch('backend.OPENAI_AVAILABLE', True)
    def test_openai_success(self, mock_openai):
        """Test successful OpenAI summarization."""
        self.app.config['API_KEYS']['openai'] = 'test-api-key'

        response_json = {
            "title": "OpenAI Meeting",
            "executive_summary": "An OpenAI summary",
            "speaker_info": {"count": 1, "list": ["Speaker 1"]},
            "highlights": ["Point 1"],
            "full_summary_sections": [],
            "tasks": []
        }

        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = json.dumps(response_json)
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        result = self.app._summarize_with_openai("Test transcript")

        self.assertEqual(result["title"], "OpenAI Meeting")
        self.assertEqual(result["transcript"], "Test transcript")
        self.assertIn("date", result)

    @patch('backend.openai')
    @patch('backend.OPENAI_AVAILABLE', True)
    def test_openai_strips_markdown_wrappers(self, mock_openai):
        """Test that markdown code block wrappers are stripped."""
        self.app.config['API_KEYS']['openai'] = 'test-api-key'

        response_json = {
            "title": "Wrapped OpenAI",
            "executive_summary": "Test",
            "highlights": [],
            "tasks": []
        }
        wrapped_response = f"```json\n{json.dumps(response_json)}\n```"

        mock_client = MagicMock()
        mock_openai.OpenAI.return_value = mock_client
        mock_message = MagicMock()
        mock_message.content = wrapped_response
        mock_choice = MagicMock()
        mock_choice.message = mock_message
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        mock_client.chat.completions.create.return_value = mock_response

        result = self.app._summarize_with_openai("Test transcript")

        self.assertEqual(result["title"], "Wrapped OpenAI")


class TestAnthropicSummarization(unittest.TestCase):
    """Test Anthropic summarization functionality."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_anthropic_missing_api_key(self):
        """Test error handling when Anthropic API key is missing."""
        self.app.config['API_KEYS']['anthropic'] = ''

        with patch('backend.ANTHROPIC_AVAILABLE', True):
            result = self.app._summarize_with_anthropic("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("API Key Missing", result["executive_summary"])

    def test_anthropic_library_not_installed(self):
        """Test error handling when Anthropic library is not installed."""
        with patch('backend.ANTHROPIC_AVAILABLE', False):
            result = self.app._summarize_with_anthropic("Test transcript")

        self.assertEqual(result["title"], "Error Processing")
        self.assertIn("not installed", result["executive_summary"])

    @patch('backend.ANTHROPIC_AVAILABLE', True)
    def test_anthropic_success(self):
        """Test successful Anthropic summarization."""
        self.app.config['API_KEYS']['anthropic'] = 'test-api-key'

        response_json = {
            "title": "Anthropic Meeting",
            "executive_summary": "An Anthropic summary",
            "speaker_info": {"count": 1, "list": ["Speaker 1"]},
            "highlights": ["Point 1"],
            "full_summary_sections": [],
            "tasks": []
        }

        mock_client = MagicMock()
        mock_content = MagicMock()
        mock_content.text = json.dumps(response_json)
        mock_response = MagicMock()
        mock_response.content = [mock_content]
        mock_client.messages.create.return_value = mock_response

        # Create mock anthropic module
        mock_anthropic = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict('sys.modules', {'anthropic': mock_anthropic}):
            # Re-import to get the mock
            import backend
            backend.anthropic = mock_anthropic

            result = self.app._summarize_with_anthropic("Test transcript")

        self.assertEqual(result["title"], "Anthropic Meeting")
        self.assertEqual(result["transcript"], "Test transcript")
        self.assertIn("date", result)


class TestGenerateSummaryRoutingExtended(unittest.TestCase):
    """Test routing for OpenAI and Anthropic in generate_summary."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_routes_to_openai(self):
        """Test that 'openai' setting routes to OpenAI summarizer."""
        self.app.config['SETTINGS']['default_llm'] = 'openai'

        with patch.object(self.app, '_summarize_with_openai') as mock_openai:
            mock_openai.return_value = {"title": "Test"}
            self.app.generate_summary("transcript", "/path/to/audio.wav")
            mock_openai.assert_called_once_with("transcript", "/path/to/audio.wav")

    def test_routes_to_anthropic(self):
        """Test that 'anthropic' setting routes to Anthropic summarizer."""
        self.app.config['SETTINGS']['default_llm'] = 'anthropic'

        with patch.object(self.app, '_summarize_with_anthropic') as mock_anthropic:
            mock_anthropic.return_value = {"title": "Test"}
            self.app.generate_summary("transcript", "/path/to/audio.wav")
            mock_anthropic.assert_called_once_with("transcript", "/path/to/audio.wav")


class TestAutoDetectLLMExtended(unittest.TestCase):
    """Test auto-detect LLM priority with OpenAI."""

    def setUp(self):
        """Set up test fixtures."""
        with patch('backend.sd') as mock_sd, \
             patch('backend.whisper'):
            mock_sd.query_hostapis.return_value = []
            mock_sd.query_devices.return_value = []
            mock_sd.default.device = [0, 0]
            self.app = EnhancedAudioApp()

    def test_auto_detect_prefers_openai(self):
        """Test that auto-detect prefers OpenAI when key is present."""
        self.app.config['SETTINGS']['default_llm'] = 'auto'
        self.app.config['API_KEYS'] = {
            'openai': 'test-openai-key',
            'gemini': 'test-gemini-key',
            'anthropic': ''
        }
        self.app.auto_detect_llm()

        self.assertEqual(self.app.config['SETTINGS']['default_llm'], 'openai')

    def test_auto_detect_anthropic_when_no_openai_or_gemini(self):
        """Test that auto-detect selects Anthropic when only it has a key."""
        self.app.config['SETTINGS']['default_llm'] = 'auto'
        self.app.config['API_KEYS'] = {
            'openai': '',
            'gemini': '',
            'anthropic': 'test-anthropic-key'
        }
        self.app.auto_detect_llm()

        self.assertEqual(self.app.config['SETTINGS']['default_llm'], 'anthropic')


if __name__ == '__main__':
    unittest.main()
