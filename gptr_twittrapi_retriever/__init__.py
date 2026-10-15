"""X/Twitter search for GPT Researcher, backed by TwittrAPI.

Install the package, set ``TWITTRAPI_API_KEY`` and ``RETRIEVER=twittrapi``.
"""

import json
import os
import urllib.error
import urllib.parse
import urllib.request

from gpt_researcher.retrievers.base import BaseRetriever

__all__ = ["TwittrAPISearch"]
__version__ = "0.1.0"

API_URL = "https://api.twittrapi.com/search"


class TwittrAPISearch(BaseRetriever):
    """Searches recent tweets through TwittrAPI's ``/search`` endpoint.

    Each result already carries the whole tweet under ``raw_content``, so GPT
    Researcher uses it directly instead of scraping x.com (which needs a login).
    """

    requires_scraping = False

    def __init__(self, query, query_domains=None, **kwargs):
        self.query = query
        self.query_domains = query_domains or []
        self.api_key = os.environ.get("TWITTRAPI_API_KEY", "")
        self.category = os.environ.get("TWITTRAPI_SEARCH_CATEGORY", "Latest")

    def search(self, max_results=10):
        if not self.api_key:
            print("TwittrAPI: TWITTRAPI_API_KEY is not set (get a key at https://app.twittrapi.com). No X results.")
            return []
        try:
            return self._search(max_results)
        except Exception as e:  # one failing provider must not abort a research run
            print(f"TwittrAPI: search failed ({e}). No X results.")
            return []

    def _search(self, max_results):
        params = urllib.parse.urlencode(
            {"searchItem": self.query, "category": self.category, "count": max_results, "format": "simple"}
        )
        req = urllib.request.Request(
            f"{API_URL}?{params}",
            headers={
                "X-API-KEY": self.api_key,
                "Accept": "application/json",
                "User-Agent": f"gptr-twittrapi-retriever/{__version__}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            message = ""
            try:
                body = json.loads(e.read().decode("utf-8"))
                if isinstance(body, dict):
                    message = body.get("error") or ""
            except (ValueError, UnicodeDecodeError):
                pass
            raise RuntimeError(f"HTTP {e.code}: {message or e.reason}") from e

        tweets = data.get("data") if isinstance(data, dict) else None
        if not isinstance(tweets, list):
            return []

        results = []
        for tweet in tweets:
            if len(results) >= max_results:
                break
            if not isinstance(tweet, dict):
                continue
            author = tweet.get("author") if isinstance(tweet.get("author"), dict) else {}
            counts = tweet.get("counts") if isinstance(tweet.get("counts"), dict) else {}
            username = author.get("username") or "unknown"
            text = tweet.get("text") or ""
            tweet_id = tweet.get("id") or ""
            href = tweet.get("url") or f"https://x.com/{username}/status/{tweet_id}"
            stats = (
                f"likes:{counts.get('likes') or 0} retweets:{counts.get('retweets') or 0} "
                f"replies:{counts.get('replies') or 0} views:{counts.get('views') or 0}"
            )
            created = tweet.get("createdAt") or ""
            header = f"Tweet by @{username}" + (f" on {created}" if created else "")
            content = f"{header}\n\n{text}\n\n[{stats}]"
            results.append(
                {
                    "title": f"@{username}: {text[:80]}{'...' if len(text) > 80 else ''}",
                    "href": href,
                    "body": content,
                    "raw_content": content,
                }
            )
        return results
