"""OANDA candle and streaming price data."""

import logging
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import oandapyV20
import oandapyV20.endpoints.instruments as instruments_ep
import oandapyV20.endpoints.accounts as accounts_ep
import oandapyV20.endpoints.pricing as pricing_ep

import config

logger = logging.getLogger(__name__)


def _client() -> oandapyV20.API:
    return oandapyV20.API(
        access_token=config.OANDA_API_KEY,
        environment=config.OANDA_ENV,
    )


def get_account_summary() -> dict:
    """Return account summary dict from OANDA."""
    client = _client()
    req = accounts_ep.AccountSummary(config.OANDA_ACCOUNT_ID)
    try:
        resp = client.request(req)
        return resp["account"]
    except Exception as exc:
        logger.error("Failed to fetch account summary: %s", exc)
        raise


def get_candles(
    instrument: str,
    granularity: str = "M15",
    count: int = 500,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> pd.DataFrame:
    """
    Fetch OANDA candles and return a DataFrame with columns:
    time, open, high, low, close, volume
    """
    client = _client()
    params: dict = {
        "granularity": granularity,
        "price": "M",  # mid prices
    }
    if from_dt and to_dt:
        params["from"] = from_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
        params["to"] = to_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    else:
        params["count"] = count

    req = instruments_ep.InstrumentsCandles(instrument, params=params)
    try:
        resp = client.request(req)
    except Exception as exc:
        logger.error("Candle fetch failed [%s %s]: %s", instrument, granularity, exc)
        raise

    rows = []
    for candle in resp.get("candles", []):
        if not candle.get("complete", True):
            continue
        mid = candle["mid"]
        rows.append(
            {
                "time":   pd.Timestamp(candle["time"]).tz_localize(None),
                "open":   float(mid["o"]),
                "high":   float(mid["h"]),
                "low":    float(mid["l"]),
                "close":  float(mid["c"]),
                "volume": int(candle["volume"]),
            }
        )

    df = pd.DataFrame(rows)
    if df.empty:
        logger.warning("No candles returned for %s %s", instrument, granularity)
        return df

    df.set_index("time", inplace=True)
    df.sort_index(inplace=True)
    logger.debug("Fetched %d candles [%s %s]", len(df), instrument, granularity)
    return df


def get_current_price(instrument: str) -> dict:
    """Return dict with bid, ask, and mid for an instrument."""
    client = _client()
    params = {"instruments": instrument}
    req = pricing_ep.PricingInfo(config.OANDA_ACCOUNT_ID, params=params)
    try:
        resp = client.request(req)
        price = resp["prices"][0]
        bid = float(price["bids"][0]["price"])
        ask = float(price["asks"][0]["price"])
        return {
            "instrument": instrument,
            "bid": bid,
            "ask": ask,
            "mid": (bid + ask) / 2,
            "time": price["time"],
        }
    except Exception as exc:
        logger.error("Price fetch failed [%s]: %s", instrument, exc)
        raise


def get_multi_timeframe(
    instrument: str,
    granularities: Optional[list[str]] = None,
) -> dict[str, pd.DataFrame]:
    """Fetch multiple timeframes for one instrument. Returns {granularity: df}."""
    if granularities is None:
        granularities = [config.TIMEFRAMES["entry"], config.TIMEFRAMES["trend"]]

    result = {}
    for g in granularities:
        count = config.CANDLE_COUNT.get(g, 300)
        result[g] = get_candles(instrument, granularity=g, count=count)
    return result
