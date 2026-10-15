# gptr-twittrapi-retriever

X/Twitter search for [GPT Researcher](https://github.com/assafelovic/gpt-researcher), backed by [TwittrAPI](https://twittrapi.com). It adds recent tweets as sources to a research run, next to web search.

## Use it

```bash
pip install gptr-twittrapi-retriever
export TWITTRAPI_API_KEY=your-key        # from https://app.twittrapi.com
export RETRIEVER=twittrapi,tavily        # combine with any built-in retriever
```

Needs GPT Researcher 0.16.1 or newer (retriever plugins).

| Variable | Default | |
| --- | --- | --- |
| `TWITTRAPI_API_KEY` | (required) | API key, sent as `X-API-KEY` |
| `TWITTRAPI_SEARCH_CATEGORY` | `Latest` | `Latest` or `Top` |

The query can use X's search operators, e.g. `from:openai`, `lang:en`, `min_faves:100`.

## What it returns

One source per tweet: the tweet URL, author, date, text and engagement counts. The tweet text comes in `raw_content`, so GPT Researcher does not try to scrape x.com, which needs a login. On a missing key or an API error it logs one line and returns no results, so the rest of the research run continues.

## Pricing

TwittrAPI bills per call, from $0.065 per 1,000 calls; one search returns one page of tweets. New accounts get a small test credit. See [pricing](https://twittrapi.com/pricing).

## Develop

```bash
python -m venv .venv && .venv/bin/pip install -e ".[test]"
.venv/bin/pytest
```

MIT licensed. TwittrAPI is not affiliated with X Corp.
