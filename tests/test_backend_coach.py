"""Tests for the Meeting Coach feature — prompts, time warnings, context."""

import time
import pytest
from datetime import datetime
from unittest.mock import patch


class TestSetMeetingContext:
    def test_stores_agenda(self, app):
        with patch.object(app, "_get_cached_feed_context", return_value=[]):
            app.set_meeting_context(
                agenda_items=["Item A", "Item B"],
                notes="some notes",
                duration_minutes=30,
            )
        # Actual API uses "agenda" (list of dicts) and "expected_duration_minutes"
        assert len(app.meeting_context["agenda"]) == 2
        assert app.meeting_context["agenda"][0]["text"] == "Item A"
        assert app.meeting_context["notes"] == "some notes"
        assert app.meeting_context["expected_duration_minutes"] == 30

    def test_default_duration_is_none(self, app):
        with patch.object(app, "_get_cached_feed_context", return_value=[]):
            app.set_meeting_context(agenda_items=[], notes="")
        assert app.meeting_context["expected_duration_minutes"] is None


class TestCoachToggle:
    def test_enable(self, app):
        app.set_coach_enabled(True)
        assert app._coach_enabled is True

    def test_disable(self, app):
        app._coach_enabled = True
        app.set_coach_enabled(False)
        assert app._coach_enabled is False


class TestGetCoachAlerts:
    def test_returns_alerts_list(self, app):
        app.coach_alerts = [{"type": "info", "message": "hello"}]
        result = app.get_coach_alerts()
        assert result == [{"type": "info", "message": "hello"}]


class TestCheckTimeWarnings:
    def test_no_warning_when_no_duration(self, app):
        app.meeting_context = {"expected_duration_minutes": None, "agenda": [], "notes": "", "company_context": []}
        app.recording_start_time = datetime.now()
        app.coach_alerts = []
        app._check_time_warnings()
        assert len(app.coach_alerts) == 0

    def test_warning_at_75_percent(self, app):
        app.meeting_context = {"expected_duration_minutes": 10, "agenda": [], "notes": "", "company_context": []}
        # Simulate being 8 minutes in to a 10-minute meeting (>75%)
        app.recording_start_time = datetime.now() - __import__("datetime").timedelta(minutes=8)
        app.coach_alerts = []
        app._check_time_warnings()
        assert len(app.coach_alerts) >= 1
        texts = [a.get("message", "") for a in app.coach_alerts]
        assert any("75%" in t for t in texts)


class TestBuildCoachPrompt:
    def test_includes_transcript(self, app):
        prompt = app._build_coach_prompt(
            transcript="Alice said hello",
            context={"agenda": [], "notes": "", "expected_duration_minutes": None, "company_context": []},
            existing_alerts=[],
        )
        assert "Alice said hello" in prompt

    def test_includes_agenda_items(self, app):
        prompt = app._build_coach_prompt(
            transcript="transcript",
            context={
                "agenda": [{"text": "Budget review", "covered": False, "time_mentioned": None}],
                "notes": "",
                "expected_duration_minutes": None,
                "company_context": [],
            },
            existing_alerts=[],
        )
        assert "Budget review" in prompt
