"""
OANDA order execution: market orders with SL/TP, status tracking, retries.
"""

import logging
import time
from typing import Optional

import oandapyV20
import oandapyV20.endpoints.orders as orders_ep
import oandapyV20.endpoints.positions as positions_ep
import oandapyV20.endpoints.trades as trades_ep

import config

logger = logging.getLogger(__name__)

MAX_RETRIES = 3
RETRY_BACKOFF = [2, 4, 8]


def _client() -> oandapyV20.API:
    return oandapyV20.API(
        access_token=config.OANDA_API_KEY,
        environment=config.OANDA_ENV,
    )


def _with_retry(fn, *args, **kwargs):
    """Call fn(*args, **kwargs) with exponential back-off on failure."""
    last_exc = None
    for attempt, wait in enumerate(RETRY_BACKOFF, start=1):
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            last_exc = exc
            logger.warning("Attempt %d failed: %s — retrying in %ds", attempt, exc, wait)
            time.sleep(wait)
    raise RuntimeError(f"All retries failed: {last_exc}") from last_exc


def _format_price(price: float, instrument: str) -> str:
    """Format price to appropriate decimal places for the instrument."""
    if "JPY" in instrument:
        return f"{price:.3f}"
    return f"{price:.5f}"


def place_market_order(
    instrument: str,
    units: int,              # positive = long, negative = short
    stop_loss: float,
    take_profit: float,
    client_order_id: Optional[str] = None,
) -> dict:
    """
    Place a market order with attached SL and TP on the OANDA practice account.
    Returns the full OANDA response dict.
    """
    if config.OANDA_ENV == "live":
        raise RuntimeError("Live trading not enabled — set OANDA_ENV=practice.")

    sl_str = _format_price(stop_loss, instrument)
    tp_str = _format_price(take_profit, instrument)

    order_data: dict = {
        "order": {
            "type": "MARKET",
            "instrument": instrument,
            "units": str(units),
            "stopLossOnFill": {"price": sl_str},
            "takeProfitOnFill": {"price": tp_str},
            "timeInForce": "FOK",  # Fill-or-Kill for market orders
        }
    }
    if client_order_id:
        order_data["order"]["clientExtensions"] = {"id": client_order_id}

    def _do_order():
        client = _client()
        req = orders_ep.OrderCreate(config.OANDA_ACCOUNT_ID, data=order_data)
        return client.request(req)

    try:
        resp = _with_retry(_do_order)
        filled = resp.get("orderFillTransaction", {})
        logger.info(
            "Order filled [%s]: units=%d price=%s SL=%s TP=%s tradeID=%s",
            instrument,
            units,
            filled.get("price", "?"),
            sl_str,
            tp_str,
            filled.get("tradeOpened", {}).get("tradeID", "?"),
        )
        return resp
    except Exception as exc:
        logger.error("Order placement failed [%s]: %s", instrument, exc)
        raise


def close_position(instrument: str, long_units: Optional[int] = None) -> dict:
    """
    Close open position for instrument.
    If long_units is None, close ALL units.
    """
    def _do_close():
        client = _client()
        data: dict = {}
        if long_units is not None:
            data = {"longUnits": str(long_units)} if long_units > 0 else {"shortUnits": str(abs(long_units))}
        else:
            data = {"longUnits": "ALL", "shortUnits": "ALL"}
        req = positions_ep.PositionClose(config.OANDA_ACCOUNT_ID, instrument, data=data)
        return client.request(req)

    try:
        resp = _with_retry(_do_close)
        logger.info("Closed position [%s]", instrument)
        return resp
    except Exception as exc:
        logger.error("Close position failed [%s]: %s", instrument, exc)
        raise


def close_all_positions() -> list[dict]:
    """Close all open positions. Used by kill switch and EOD logic."""
    results = []
    for instrument in config.INSTRUMENTS:
        try:
            resp = close_position(instrument)
            results.append({"instrument": instrument, "status": "closed", "response": resp})
        except Exception as exc:
            results.append({"instrument": instrument, "status": "error", "error": str(exc)})
    return results


def get_open_trades() -> list[dict]:
    """Return list of open trades from OANDA."""
    def _do_get():
        client = _client()
        req = trades_ep.OpenTrades(config.OANDA_ACCOUNT_ID)
        return client.request(req)

    try:
        resp = _with_retry(_do_get)
        return resp.get("trades", [])
    except Exception as exc:
        logger.error("Failed to fetch open trades: %s", exc)
        return []


def get_open_positions() -> list[dict]:
    """Return list of open positions from OANDA."""
    def _do_get():
        client = _client()
        req = positions_ep.OpenPositions(config.OANDA_ACCOUNT_ID)
        return client.request(req)

    try:
        resp = _with_retry(_do_get)
        return resp.get("positions", [])
    except Exception as exc:
        logger.error("Failed to fetch open positions: %s", exc)
        return []
