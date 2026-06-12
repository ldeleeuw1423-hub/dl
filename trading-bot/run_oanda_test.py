"""
OANDA connection verification script.
Fetches account info and a sample of candles for each instrument.

Run: python run_oanda_test.py
(requires .env with OANDA_API_KEY + OANDA_ACCOUNT_ID)
"""

import logging
import sys

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

import config
from data.market_data import get_account_summary, get_candles, get_current_price


def main() -> None:
    try:
        config.validate()
    except RuntimeError as exc:
        logger.critical("%s", exc)
        sys.exit(1)

    logger.info("Environment: %s", config.OANDA_ENV)

    # Account
    print("\n=== Account Summary ===")
    account = get_account_summary()
    print(f"  ID       : {account.get('id')}")
    print(f"  Currency : {account.get('currency')}")
    print(f"  Balance  : {account.get('balance')}")
    print(f"  NAV      : {account.get('NAV')}")
    print(f"  Open pos.: {account.get('openPositionCount')}")

    # Candles + prices
    for instrument in config.INSTRUMENTS:
        print(f"\n=== {instrument} ===")
        df = get_candles(instrument, granularity="M15", count=10)
        if not df.empty:
            print(f"  Last 3 M15 candles:\n{df.tail(3).to_string()}")
        else:
            print("  No data returned.")

        price = get_current_price(instrument)
        print(f"  Current price  bid={price['bid']}  ask={price['ask']}  mid={price['mid']:.5f}")


if __name__ == "__main__":
    main()
