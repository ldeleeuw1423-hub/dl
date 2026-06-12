"""
Live trading loop.

Scheduler cadence: every LOOP_INTERVAL_SECONDS seconds.
  1. Kill-switch check
  2. Fetch account summary → risk gate
  3. For each instrument:
     a. Fetch M15 + H1 candles
     b. Run combined strategy
     c. Fetch sentiment
     d. Execute if signal and risk allows
  5. EOD close (Friday 21:00 UTC)
  6. Daily report (20:00 Amsterdam)

Run:  python main.py
Stop: touch STOP
"""

import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytz
from apscheduler.schedulers.blocking import BlockingScheduler

import config
from data.market_data import get_account_summary, get_candles, get_multi_timeframe
from execution.order_manager import (
    close_all_positions,
    get_open_positions,
    get_open_trades,
    place_market_order,
)
from risk.risk_manager import RiskManager
from strategies.combined import CombinedStrategy
from backtester.metrics import BacktestResult
from dashboard.report import generate_report

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------
def _setup_logging() -> None:
    root = logging.getLogger()
    root.setLevel(config.LOG_LEVEL)
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    root.addHandler(ch)

    fh = logging.handlers.RotatingFileHandler(
        config.LOG_DIR / "trading.log",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
    )
    fh.setFormatter(fmt)
    root.addHandler(fh)


logger = logging.getLogger(__name__)
AMSTERDAM = pytz.timezone("Europe/Amsterdam")

# ---------------------------------------------------------------------------
# Global state
# ---------------------------------------------------------------------------
_risk_manager = RiskManager()
_strategy = CombinedStrategy()
_trades_today: list[dict] = []
_sentiments: dict[str, dict] = {}


def _is_weekend_close() -> bool:
    """True on Fridays after EOD_CLOSE_HOUR_UTC."""
    now = datetime.now(timezone.utc)
    return now.weekday() == 4 and now.hour >= config.EOD_CLOSE_HOUR_UTC


def _should_generate_report() -> bool:
    now_ams = datetime.now(AMSTERDAM)
    return now_ams.hour == config.REPORT_HOUR_AMSTERDAM and now_ams.minute < 2


# ---------------------------------------------------------------------------
# Core trading tick
# ---------------------------------------------------------------------------
def trading_tick() -> None:
    """One iteration of the main loop."""
    global _sentiments

    # Kill switch
    if _risk_manager.kill_switch_active():
        logger.critical("Kill switch active — closing all positions and exiting.")
        close_all_positions()
        sys.exit(0)

    # EOD / weekend close
    if _is_weekend_close():
        logger.info("Weekend EOD — closing all positions.")
        close_all_positions()
        return

    # Account info
    try:
        account = get_account_summary()
    except Exception as exc:
        logger.error("Cannot fetch account summary: %s", exc)
        return

    equity = float(account.get("NAV", account.get("balance", 0)))
    _risk_manager.daily_tracker.set_equity(equity)

    # Open positions count
    open_positions = get_open_positions()
    open_count = len(open_positions)

    allowed, reason = _risk_manager.can_trade(equity, open_count)
    if not allowed:
        logger.info("Trading blocked: %s", reason)
        if _should_generate_report():
            _run_daily_report(account, open_positions)
        return

    # Per-instrument loop
    for instrument in config.INSTRUMENTS:
        try:
            _process_instrument(instrument, equity, open_count)
        except Exception as exc:
            logger.error("Error processing %s: %s", instrument, exc)

    if _should_generate_report():
        _run_daily_report(account, get_open_positions())


def _process_instrument(instrument: str, equity: float, open_count: int) -> None:
    # Fetch candles
    frames = get_multi_timeframe(instrument, ["M15", "H1"])
    df_m15 = frames.get("M15")
    df_h1 = frames.get("H1")

    if df_m15 is None or df_m15.empty:
        logger.warning("[%s] No M15 data", instrument)
        return

    # Sentiment (lazy — only when actually needed, results cached in news_feed)
    sentiment = _sentiments.get(instrument)
    if sentiment is None:
        try:
            from ai.sentiment import score_instrument_sentiment
            sentiment = score_instrument_sentiment(instrument)
            _sentiments[instrument] = sentiment
        except Exception as exc:
            logger.warning("[%s] Sentiment fetch failed: %s — using neutral", instrument, exc)
            sentiment = {"label": "neutral", "score": 0.0, "count": 0}

    # Generate signal
    signal = _strategy.generate_signal(df_m15, instrument, df_h1=df_h1, sentiment=sentiment)
    logger.debug("[%s] Signal: %s conf=%.2f | %s", instrument, signal.direction, signal.confidence, signal.reason)

    if signal.direction == "flat":
        return

    # Risk gate (re-check with latest open count)
    current_positions = get_open_positions()
    allowed, reason = _risk_manager.can_trade(equity, len(current_positions))
    if not allowed:
        logger.info("[%s] Risk gate blocked after signal: %s", instrument, reason)
        return

    # Position sizing
    if signal.stop_loss is None or signal.entry_price is None:
        logger.warning("[%s] Signal missing SL/entry price, skipping", instrument)
        return

    units = _risk_manager.calculate_units(
        equity,
        signal.entry_price,
        signal.stop_loss,
        instrument,
        sentiment_multiplier=signal.size_multiplier,
    )
    if units <= 0:
        return

    if signal.direction == "short":
        units = -units

    # Place order
    try:
        resp = place_market_order(
            instrument=instrument,
            units=units,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit,
        )
        filled = resp.get("orderFillTransaction", {})
        _trades_today.append(
            {
                "instrument":  instrument,
                "direction":   signal.direction,
                "units":       units,
                "entry_price": filled.get("price", signal.entry_price),
                "exit_price":  "",
                "pnl":         0,
                "time":        datetime.now(timezone.utc).isoformat(),
            }
        )
    except Exception as exc:
        logger.error("[%s] Order failed: %s", instrument, exc)


def _run_daily_report(account: dict, open_positions: list[dict]) -> None:
    try:
        generate_report(
            account=account,
            daily_pnl=_risk_manager.daily_tracker.daily_pnl,
            trades_today=_trades_today,
            sentiments=_sentiments,
            open_positions=open_positions,
        )
    except Exception as exc:
        logger.error("Report generation failed: %s", exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
def main() -> None:
    _setup_logging()
    logger.info("=" * 60)
    logger.info("Trading bot starting up — environment: %s", config.OANDA_ENV)

    try:
        config.validate()
    except RuntimeError as exc:
        logger.critical("Config error: %s", exc)
        sys.exit(1)

    # Verify OANDA connection
    try:
        account = get_account_summary()
        logger.info(
            "OANDA connected — account %s, balance=%.2f %s",
            account.get("id"),
            float(account.get("balance", 0)),
            account.get("currency", ""),
        )
    except Exception as exc:
        logger.critical("OANDA connection failed: %s", exc)
        sys.exit(1)

    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(
        trading_tick,
        "interval",
        seconds=config.LOOP_INTERVAL_SECONDS,
        id="main_loop",
        next_run_time=datetime.now(timezone.utc),  # run immediately on start
    )

    logger.info(
        "Scheduler started — interval %ds. To stop: touch STOP or Ctrl+C.",
        config.LOOP_INTERVAL_SECONDS,
    )
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")


if __name__ == "__main__":
    main()
