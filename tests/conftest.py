"""Shared fixtures for all test modules."""

import sys
import json
import os
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Mock heavy dependencies BEFORE any project code is imported.
# These modules require hardware (sounddevice) or large binaries (whisper).
# ---------------------------------------------------------------------------
_mock_whisper = MagicMock()
_mock_sd = MagicMock()
sys.modules.setdefault("whisper", _mock_whisper)
sys.modules.setdefault("sounddevice", _mock_sd)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_sd():
    """Pre-configured sounddevice mock."""
    with patch("backend.sd") as sd:
        sd.query_hostapis.return_value = []
        sd.query_devices.return_value = []
        sd.default.device = [0, 0]
        yield sd


@pytest.fixture()
def mock_whisper():
    """Pre-configured whisper mock."""
    with patch("backend.whisper") as w:
        yield w


@pytest.fixture()
def app(mock_sd, mock_whisper):
    """A fully-initialised EnhancedAudioApp with mocked hardware."""
    from backend import EnhancedAudioApp
    return EnhancedAudioApp()


@pytest.fixture()
def tmp_config(tmp_path):
    """Create a temporary config file and return its path."""
    cfg = tmp_path / "audio_config.ini"
    cfg.write_text(
        "[SETTINGS]\ndefault_llm = ollama\nollama_model = llama3:8b\n"
        "[API_KEYS]\ngemini =\nopenai =\nanthropic =\n"
    )
    return str(cfg)


@pytest.fixture()
def tmp_history(tmp_path):
    """Create a temporary history file and return its path."""
    hf = tmp_path / "audio_history.json"
    hf.write_text("[]")
    return str(hf)
