"""Tests for RSS feed fetcher and caching logic."""

import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

import pytest


@pytest.fixture()
def fetcher(tmp_path, monkeypatch):
    """Create a FeedFetcher with a temporary cache file."""
    monkeypatch.chdir(tmp_path)
    from feed_fetcher import FeedFetcher
    return FeedFetcher(config=None)


class TestNeedsRefresh:
    def test_true_when_never_fetched(self, fetcher):
        assert fetcher.needs_refresh() is True

    def test_false_when_recently_fetched(self, fetcher):
        fetcher.cache["last_fetched"] = datetime.now().isoformat()
        assert fetcher.needs_refresh() is False

    def test_true_when_stale(self, fetcher):
        stale = (datetime.now() - timedelta(hours=5)).isoformat()
        fetcher.cache["last_fetched"] = stale
        assert fetcher.needs_refresh() is True

    def test_respects_config_refresh_hours(self, fetcher):
        cfg = MagicMock()
        cfg.get.return_value = "1"
        fetcher.config = cfg
        two_hours_ago = (datetime.now() - timedelta(hours=2)).isoformat()
        fetcher.cache["last_fetched"] = two_hours_ago
        assert fetcher.needs_refresh() is True


class TestFetchFeeds:
    def test_noop_without_feedparser(self, fetcher):
        with patch("feed_fetcher.FEEDPARSER_AVAILABLE", False):
            fetcher.fetch_feeds(["http://example.com/feed"])
        # Items unchanged (still empty from init)
        assert fetcher.cache["items"] == []

    def test_parses_entries(self, fetcher):
        """Test feed parsing when feedparser is available."""
        import feed_fetcher as ff_module

        entry = MagicMock()
        entry.get.side_effect = lambda k, default="": {
            "title": "Article 1",
            "summary": "Summary text",
            "description": "",
            "link": "http://example.com/1",
        }.get(k, default)

        feed_result = MagicMock()
        feed_result.entries = [entry]
        feed_result.feed.get.return_value = "Test Blog"

        mock_fp = MagicMock()
        mock_fp.parse.return_value = feed_result

        with patch.object(ff_module, "FEEDPARSER_AVAILABLE", True), \
             patch.object(ff_module, "feedparser", mock_fp, create=True):
            fetcher.fetch_feeds(["http://example.com/feed"])

        assert len(fetcher.cache["items"]) == 1
        assert fetcher.cache["items"][0]["title"] == "Article 1"
        assert fetcher.cache["last_fetched"] is not None

    def test_limits_to_10_entries_per_feed(self, fetcher):
        import feed_fetcher as ff_module

        entries = []
        for i in range(15):
            e = MagicMock()
            e.get.side_effect = lambda k, default="", idx=i: {
                "title": f"Article {idx}", "summary": "s", "description": "", "link": ""
            }.get(k, default)
            entries.append(e)

        feed_result = MagicMock()
        feed_result.entries = entries
        feed_result.feed.get.return_value = "Blog"

        mock_fp = MagicMock()
        mock_fp.parse.return_value = feed_result

        with patch.object(ff_module, "FEEDPARSER_AVAILABLE", True), \
             patch.object(ff_module, "feedparser", mock_fp, create=True):
            fetcher.fetch_feeds(["http://example.com/feed"])

        assert len(fetcher.cache["items"]) == 10

    def test_handles_feed_error(self, fetcher):
        import feed_fetcher as ff_module
        mock_fp = MagicMock()
        mock_fp.parse.side_effect = Exception("Network error")

        with patch.object(ff_module, "FEEDPARSER_AVAILABLE", True), \
             patch.object(ff_module, "feedparser", mock_fp, create=True):
            fetcher.fetch_feeds(["http://bad.example.com"])
        assert fetcher.cache["items"] == []


class TestGetContextStrings:
    def test_empty_cache(self, fetcher):
        assert fetcher.get_context_strings() == []

    def test_formats_items(self, fetcher):
        fetcher.cache["items"] = [
            {"source": "Blog", "title": "Post", "summary": "Text"}
        ]
        result = fetcher.get_context_strings()
        assert len(result) == 1
        assert "[Blog] Post: Text" in result[0]

    def test_respects_max_items(self, fetcher):
        fetcher.cache["items"] = [
            {"source": "S", "title": f"T{i}", "summary": "s"} for i in range(20)
        ]
        assert len(fetcher.get_context_strings(max_items=5)) == 5


class TestRefreshIfNeeded:
    def test_refreshes_when_stale(self, fetcher):
        with patch.object(fetcher, "needs_refresh", return_value=True), \
             patch.object(fetcher, "fetch_feeds") as mock_fetch:
            fetcher.refresh_if_needed(["http://example.com/feed"])
            mock_fetch.assert_called_once()

    def test_skips_when_fresh(self, fetcher):
        with patch.object(fetcher, "needs_refresh", return_value=False), \
             patch.object(fetcher, "fetch_feeds") as mock_fetch:
            fetcher.refresh_if_needed(["http://example.com/feed"])
            mock_fetch.assert_not_called()

    def test_skips_when_no_urls(self, fetcher):
        with patch.object(fetcher, "needs_refresh", return_value=True), \
             patch.object(fetcher, "fetch_feeds") as mock_fetch:
            fetcher.refresh_if_needed([])
            mock_fetch.assert_not_called()
