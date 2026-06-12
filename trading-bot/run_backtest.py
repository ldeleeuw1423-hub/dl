"""
Helper script: fetch 2 years of OANDA data and run all strategy backtests.
Run: python run_backtest.py

Requires OANDA_API_KEY and OANDA_ACCOUNT_ID in .env (practice account).
"""

import logging
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import config
from data.market_data import get_candles
from backtester.backtest import run_all_strategies
from backtester.metrics import plot_equity_curve, print_comparison_table

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def main() -> None:
    try:
        config.validate()
    except RuntimeError as exc:
        logger.critical("Config error: %s", exc)
        sys.exit(1)

    instruments = config.INSTRUMENTS
    granularity = "H1"   # H1 gives good data density over 2 years
    to_dt = datetime.now(timezone.utc)
    from_dt = to_dt - timedelta(days=730)

    all_results = {}

    for instrument in instruments:
        logger.info("Fetching %s data [%s → %s]…", instrument, from_dt.date(), to_dt.date())
        try:
            df = get_candles(instrument, granularity=granularity, from_dt=from_dt, to_dt=to_dt)
        except Exception as exc:
            logger.error("Failed to fetch %s: %s", instrument, exc)
            continue

        logger.info("Fetched %d bars for %s", len(df), instrument)
        results = run_all_strategies(df, instrument)

        print(f"\n{'='*60}")
        print(f"  {instrument}  ({granularity}, {len(df)} bars)")
        print_comparison_table(results)

        for name, res in results.items():
            all_results[f"{instrument}_{name}"] = res

    # Save equity curve chart
    chart_path = Path(__file__).parent / "reports" / "equity_curves.png"
    plot_equity_curve(all_results, output_path=chart_path, show=False)
    logger.info("Charts saved to %s", chart_path)


if __name__ == "__main__":
    main()
