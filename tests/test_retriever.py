import json
import urllib.error
import urllib.parse
from io import BytesIO
from unittest.mock import patch

import gptr_twittrapi_retriever as mod
from gptr_twittrapi_retriever import TwittrAPISearch


class FakeResp:
    def __init__(self, body):
        self._body = body

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False


def run(payload, env=None, **kwargs):
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    with patch.dict("os.environ", env if env is not None else {"TWITTRAPI_API_KEY": "k"}, clear=True):
        r = TwittrAPISearch("from:openai lang:en")
        with patch.object(mod.urllib.request, "urlopen", return_value=FakeResp(body)) as urlopen:
            return r.search(**kwargs), urlopen


TWEET = {
    "id": "1",
    "url": "https://x.com/alice/status/1",
    "text": "hello world",
    "createdAt": "2026-10-01T12:00:00.000Z",
    "author": {"username": "alice", "name": "Alice"},
    "counts": {"likes": 5, "retweets": 2, "replies": 1, "views": None},
}


def test_maps_tweets_with_raw_content():
    out, urlopen = run({"data": [TWEET], "nextCursor": "c", "hasNextPage": True}, max_results=5)
    assert len(out) == 1
    r = out[0]
    assert r["href"] == "https://x.com/alice/status/1"
    assert r["title"] == "@alice: hello world"
    assert r["raw_content"] == r["body"]
    assert "Tweet by @alice on 2026-10-01T12:00:00.000Z" in r["raw_content"]
    assert "[likes:5 retweets:2 replies:1 views:0]" in r["raw_content"]
    req = urlopen.call_args.args[0]
    assert req.get_header("X-api-key") == "k"
    url = urllib.parse.urlparse(req.full_url)
    assert (url.netloc, url.path) == ("api.twittrapi.com", "/search")
    assert urllib.parse.parse_qs(url.query) == {
        "searchItem": ["from:openai lang:en"],
        "category": ["Latest"],
        "count": ["5"],
        "format": ["simple"],
    }


def test_limits_and_skips_bad_items():
    tweets = [TWEET, "bad", {"id": "2", "text": "no author", "author": None, "counts": None}, dict(TWEET, id="3")]
    out, _ = run({"data": tweets}, max_results=2)
    assert [o["href"] for o in out] == ["https://x.com/alice/status/1", "https://x.com/unknown/status/2"]


def test_non_list_data_and_non_dict_payload():
    assert run({"data": {"oops": 1}})[0] == []
    assert run(["x"])[0] == []
    assert run(b"not json")[0] == []


def test_missing_key_returns_empty_without_calling():
    out, urlopen = run({"data": [TWEET]}, env={})
    assert out == [] and urlopen.call_count == 0


def test_http_error_returns_empty():
    err = urllib.error.HTTPError("u", 401, "Unauthorized", {}, BytesIO(b'{"error":"invalid api key"}'))
    with patch.dict("os.environ", {"TWITTRAPI_API_KEY": "k"}, clear=True):
        with patch.object(mod.urllib.request, "urlopen", side_effect=err):
            assert TwittrAPISearch("q").search() == []


def test_registered_as_gpt_researcher_plugin():
    from gpt_researcher.actions.retriever import get_retriever

    assert get_retriever("twittrapi") is TwittrAPISearch
