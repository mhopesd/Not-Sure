"""Tests for FastAPI API server endpoints and helpers."""

import sys
from unittest.mock import MagicMock

# Mock heavy deps before importing api_server
sys.modules.setdefault("whisper", MagicMock())
sys.modules.setdefault("sounddevice", MagicMock())

import pytest


class TestParseDurationToSeconds:
    """Test the pure parse_duration_to_seconds function."""

    @pytest.fixture(autouse=True)
    def _import(self):
        from api_server import parse_duration_to_seconds
        self.parse = parse_duration_to_seconds

    def test_integer_passthrough(self):
        assert self.parse(120) == 120

    def test_float_passthrough(self):
        assert self.parse(90.5) == 90

    def test_seconds_string(self):
        assert self.parse("24s") == 24

    def test_minutes_and_seconds(self):
        assert self.parse("5m 23s") == 323

    def test_hours_minutes_seconds(self):
        assert self.parse("1h 2m 3s") == 3723

    def test_minutes_only(self):
        assert self.parse("10m") == 600

    def test_non_string_returns_zero(self):
        assert self.parse(None) == 0
        assert self.parse([]) == 0

    def test_empty_string_returns_zero(self):
        assert self.parse("") == 0

    def test_no_units_returns_zero(self):
        assert self.parse("hello") == 0
