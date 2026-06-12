"""Finnhub news fetcher with deduplication and in-memory caching."""

import hashlib
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Optional

import finnhub

import config

logger = logging.getLogger(__name__)

# Simple in-memory cache: {instrument: (fetched_at_ts, [articles])}
_CACHE: dict[str, tuple[float, list[dict]]] = {}
_CACHE_TTL_SECONDS = 300  # refresh at most every 5 minutes


def _finnhub_client() -> finnhub.Client:
    return finnhub.Client(api_key=config.FINNHUB_API_KEY)


def _article_id(article: dict) -> str:
    """Stable hash for deduplication."""
    key = (article.get("headline", "") + article.get("url", "")).encode()
    return hashlib.md5(key).hexdigest()


def fetch_news(
    instrument: str,
    lookback_hours: int = config.NEWS_LOOKBACK_HOURS,
    force_refresh: bool = False,
) -> list[dict]:
    """
    Return list of news articles for an instrument from the last *lookback_hours*.
    Each article: {id, headline, summary, source, datetime, url, sentiment_text}
    """
    now_ts = time.time()

    # Cache hit
    if not force_refresh and instrument in _CACHE:
        fetched_at, cached = _CACHE[instrument]
        if now_ts - fetched_at < _CACHE_TTL_SECONDS:
            logger.debug("News cache hit for %s (%d articles)", instrument, len(cached))
            return cached

    if not config.FINNHUB_API_KEY:
        logger.warning("FINNHUB_API_KEY not set, returning empty news list.")
        return []

    finnhub_symbol = config.INSTRUMENT_TO_FINNHUB.get(instrument)
    if not finnhub_symbol:
        logger.warning("No Finnhub symbol mapping for %s", instrument)
        return []

    since = datetime.now(timezone.utc) - timedelta(hours=lookback_hours)
    to_ts = int(now_ts)
    from_ts = int(since.timestamp())

    client = _finnhub_client()
    try:
        # Finnhub forex news endpoint
        raw = client.company_news(
            symbol=finnhub_symbol,
            _from=datetime.utcfromtimestamp(from_ts).strftime("%Y-%m-%d"),
            to=datetime.utcfromtimestamp(to_ts).strftime("%Y-%m-%d"),
        )
    except Exception as exc:
        logger.error("Finnhub news fetch failed [%s]: %s", instrument, exc)
        # Return stale cache on error if available
        if instrument in _CACHE:
            return _CACHE[instrument][1]
        return []

    seen_ids: set[str] = set()
    articles: list[dict] = []
    for item in raw or []:
        article_ts = item.get("datetime", 0)
        if article_ts < from_ts:
            continue

        uid = _article_id(item)
        if uid in seen_ids:
            continue
        seen_ids.add(uid)

        articles.append(
            {
                "id":             uid,
                "headline":       item.get("headline", ""),
                "summary":        item.get("summary", ""),
                "source":         item.get("source", ""),
                "datetime":       datetime.utcfromtimestamp(article_ts).isoformat(),
                "url":            item.get("url", ""),
                "sentiment_text": (item.get("headline", "") + " " + item.get("summary", "")).strip(),
            }
        )

    # Newest first
    articles.sort(key=lambda a: a["datetime"], reverse=True)
    _CACHE[instrument] = (now_ts, articles)
    logger.info("Fetched %d news articles for %s", len(articles), instrument)
    return articles


def get_news_texts(instrument: str) -> list[str]:
    """Convenience: return just the text strings suitable for FinBERT input."""
    return [a["sentiment_text"] for a in fetch_news(instrument) if a["sentiment_text"]]
