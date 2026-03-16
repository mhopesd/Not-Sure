"""Tests for pure/near-pure helper methods in backend.py."""

import pytest


class TestFormatTime:
    def test_zero(self, app):
        assert app._format_time(0) == "00:00"

    def test_seconds_only(self, app):
        assert app._format_time(45) == "00:45"

    def test_minutes_and_seconds(self, app):
        assert app._format_time(125) == "02:05"

    def test_exact_minute(self, app):
        assert app._format_time(60) == "01:00"

    def test_large_value(self, app):
        assert app._format_time(3661) == "61:01"


class TestSetMode:
    def test_microphone(self, app):
        app.set_mode("Microphone")
        assert app.recording_mode == "microphone"

    def test_system_audio(self, app):
        app.set_mode("System Audio")
        assert app.recording_mode == "system"

    def test_hybrid(self, app):
        app.set_mode("Hybrid")
        assert app.recording_mode == "hybrid"

    def test_unknown_defaults_to_microphone(self, app):
        app.set_mode("SomeUnknownValue")
        assert app.recording_mode == "microphone"


class TestErrorSummary:
    def test_structure(self, app):
        result = app.error_summary("Something broke", "transcript text")
        assert result["title"] == "Error Processing"
        assert result["executive_summary"] == "Something broke"
        assert result["full_summary"] == ""
        assert result["tasks"] == []
        assert result["transcript"] == "transcript text"


class TestSafeErrorMessage:
    def test_strips_api_key_patterns(self, app):
        err = Exception("Error with key=sk-abc123xyz in request")
        msg = app._safe_error_message(err)
        assert "sk-abc123xyz" not in msg

    def test_returns_string(self, app):
        msg = app._safe_error_message(ValueError("test"))
        assert isinstance(msg, str)


class TestUpdateStatus:
    def test_calls_callback(self, app):
        messages = []
        app.status_callback = lambda m: messages.append(m)
        app.update_status("hello")
        assert messages == ["hello"]

    def test_no_callback_no_error(self, app):
        app.status_callback = None
        app.update_status("hello")  # should not raise
