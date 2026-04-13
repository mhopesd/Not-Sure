"""Tests for history persistence."""

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
