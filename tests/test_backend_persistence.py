"""Tests for history, journal, and session persistence."""

import json
import os
import pytest
from unittest.mock import patch


class TestSaveAndLoadHistory:
    def test_save_appends_to_history(self, app, tmp_path):
        hf = tmp_path / "history.json"
        hf.write_text("[]")
        app.history_file = str(hf)
        app.chat_history = []

        app.save_to_history("transcript text", {"title": "Test"})

        assert len(app.chat_history) == 1
        assert app.chat_history[0]["transcript"] == "transcript text"
        assert app.chat_history[0]["title"] == "Test"

    def test_load_history_reads_file(self, app, tmp_path):
        hf = tmp_path / "history.json"
        data = [{"transcript": "t", "title": "T", "date": "2026-01-01"}]
        hf.write_text(json.dumps(data))
        app.history_file = str(hf)

        app.load_history()

        assert len(app.chat_history) == 1
        assert app.chat_history[0]["transcript"] == "t"

    def test_load_history_handles_missing_file(self, app, tmp_path):
        app.history_file = str(tmp_path / "nonexistent.json")
        app.chat_history = ["something"]
        app.load_history()
        # load_history only loads if file exists, otherwise does nothing
        assert app.chat_history == ["something"]


class TestJournalCRUD:
    def test_create_journal_entry(self, app, tmp_path):
        jf = tmp_path / "journal.json"
        jf.write_text("[]")
        # Use the actual attribute name from backend
        app.journal_file = str(jf)
        app.journal_entries = []

        entry = app.create_journal_entry("My first note")

        assert entry["entry"] == "My first note"
        assert "id" in entry
        assert "date" in entry
        assert len(app.journal_entries) == 1

    def test_get_journal_entries_returns_list(self, app):
        app.journal_entries = [{"id": "1", "entry": "note"}]
        entries = app.get_journal_entries()
        assert isinstance(entries, list)
        assert len(entries) == 1


class TestSessionManagement:
    def test_login(self, app, tmp_path):
        sf = tmp_path / "session.json"
        sf.write_text("{}")
        app.session_file = str(sf)
        app.session = {}

        result = app.login("google", "user@example.com")

        assert result is True
        assert app.is_logged_in() is True
        assert app.get_user_info()["email"] == "user@example.com"

    def test_logout(self, app, tmp_path):
        sf = tmp_path / "session.json"
        sf.write_text("{}")
        app.session_file = str(sf)
        app.session = {"logged_in": True, "provider": "google", "email": "user@example.com"}

        app.logout()

        assert app.is_logged_in() is False

    def test_is_logged_in_false_by_default(self, app):
        app.session = {}
        assert app.is_logged_in() is False

    def test_get_user_info_when_logged_out(self, app):
        app.session = {}
        info = app.get_user_info()
        assert info.get("logged_in") is not True
