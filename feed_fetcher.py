"""RSS and web feed fetcher for company context in Meeting Coach."""
import json
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

try:
    import feedparser
    FEEDPARSER_AVAILABLE = True
except ImportError:
    FEEDPARSER_AVAILABLE = False
    logger.info("feedparser not installed — RSS feeds unavailable (pip install feedparser)")


class FeedFetcher:
    """Fetches and caches RSS/web feed items for meeting context."""

    CACHE_FILE = "feed_cache.json"

    def __init__(self, config=None):
        self.config = config
        self.cache = {"last_fetched": None, "items": []}
        self._load_cache()

    def _load_cache(self):
        if os.path.exists(self.CACHE_FILE):
            try:
                with open(self.CACHE_FILE, 'r') as f:
                    self.cache = json.load(f)
            except Exception:
                pass

    def _save_cache(self):
        try:
            with open(self.CACHE_FILE, 'w') as f:
                json.dump(self.cache, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save feed cache: {e}")

    def needs_refresh(self):
        """Check if the cache is stale and needs refreshing."""
        if not self.cache.get("last_fetched"):
            return True
        try:
            refresh_hours = 4
            if self.config:
                refresh_hours = int(self.config.get('COACH', 'feed_refresh_hours', fallback='4'))
            last = datetime.fromisoformat(self.cache["last_fetched"])
            return datetime.now() - last > timedelta(hours=refresh_hours)
        except Exception:
            return True

    def fetch_feeds(self, urls):
        """Fetch all configured RSS feeds and cache results."""
        if not FEEDPARSER_AVAILABLE:
            logger.warning("Cannot fetch feeds: feedparser not installed")
            return

        items = []
        for url in urls:
            try:
                feed = feedparser.parse(url)
                for entry in feed.entries[:10]:  # Max 10 per feed
                    summary = entry.get("summary", entry.get("description", ""))[:200]
                    items.append({
                        "title": entry.get("title", ""),
                        "source": feed.feed.get("title", url),
                        "url": entry.get("link", ""),
                        "summary": summary,
                        "fetched_at": datetime.now().isoformat()
                    })
            except Exception as e:
                logger.error(f"Failed to fetch feed {url}: {e}")

        self.cache = {
            "last_fetched": datetime.now().isoformat(),
            "items": items
        }
        self._save_cache()
        logger.info(f"Fetched {len(items)} feed items from {len(urls)} feeds")

    def get_context_strings(self, max_items=10):
        """Return cached feed items as strings for LLM context."""
        return [
            f"[{item['source']}] {item['title']}: {item['summary']}"
            for item in self.cache.get("items", [])[:max_items]
        ]

    def refresh_if_needed(self, urls):
        """Refresh feeds if cache is stale."""
        if self.needs_refresh() and urls:
            self.fetch_feeds(urls)
