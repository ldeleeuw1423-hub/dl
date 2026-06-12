"""Central configuration. Loads .env and exposes typed settings to all modules."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from the project root (trading-bot/)
_ROOT = Path(__file__).parent
load_dotenv(_ROOT / ".env")


# ---------------------------------------------------------------------------
# OANDA
# ---------------------------------------------------------------------------
OANDA_API_KEY: str = os.environ.get("OANDA_API_KEY", "")
OANDA_ACCOUNT_ID: str = os.environ.get("OANDA_ACCOUNT_ID", "")
OANDA_ENV: str = os.environ.get("OANDA_ENV", "practice")  # "practice" or "live"

# Maps OANDA_ENV to the correct hostname
OANDA_HOSTNAMES = {
    "practice": "api-fxpractice.oanda.com",
    "live":     "api-fxtrade.oanda.com",
}
OANDA_STREAM_HOSTNAMES = {
    "practice": "stream-fxpractice.oanda.com",
    "live":     "stream-fxtrade.oanda.com",
}

def _oanda_environment() -> str:
    """Return oandapyV20 environment string."""
    return "practice" if OANDA_ENV == "practice" else "live"


# ---------------------------------------------------------------------------
# Finnhub
# ---------------------------------------------------------------------------
FINNHUB_API_KEY: str = os.environ.get("FINNHUB_API_KEY", "")


# ---------------------------------------------------------------------------
# Trading instruments and timeframes
# ---------------------------------------------------------------------------
_raw_instruments = os.environ.get("TRADING_INSTRUMENTS", "EUR_USD,USD_JPY,GBP_USD")
INSTRUMENTS: list[str] = [i.strip() for i in _raw_instruments.split(",")]

# Finnhub uses different symbols (forex pairs without underscore)
INSTRUMENT_TO_FINNHUB: dict[str, str] = {
    "EUR_USD": "OANDA:EUR_USD",
    "USD_JPY": "OANDA:USD_JPY",
    "GBP_USD": "OANDA:GBP_USD",
    "AUD_USD": "OANDA:AUD_USD",
    "USD_CHF": "OANDA:USD_CHF",
    "USD_CAD": "OANDA:USD_CAD",
}

# Candle granularities used
TIMEFRAMES = {
    "entry":  "M15",   # entry signals
    "trend":  "H1",    # trend filter
    "daily":  "D",     # daily context
}

# How many candles to fetch per request
CANDLE_COUNT = {
    "M5":  500,
    "M15": 500,
    "H1":  300,
    "H4":  200,
    "D":   500,
}


# ---------------------------------------------------------------------------
# Risk parameters
# ---------------------------------------------------------------------------
MAX_RISK_PER_TRADE_PCT: float = float(
    os.environ.get("MAX_RISK_PER_TRADE_PCT", "0.01")
)  # 1 % of account equity
MAX_OPEN_POSITIONS: int = int(os.environ.get("MAX_OPEN_POSITIONS", "3"))
MAX_DAILY_LOSS_PCT: float = float(
    os.environ.get("MAX_DAILY_LOSS_PCT", "0.03")
)  # 3 % of equity
ATR_PERIOD: int = 14
ATR_MULTIPLIER: float = 1.5     # ATR × 1.5 = stop distance
MIN_REWARD_RISK: float = 2.0    # take-profit must be ≥ 2× stop distance


# ---------------------------------------------------------------------------
# Technical indicator settings
# ---------------------------------------------------------------------------
EMA_FAST: int = 9
EMA_SLOW: int = 21
EMA_TREND: int = 200
RSI_PERIOD: int = 14
RSI_OVERBOUGHT: int = 70
RSI_OVERSOLD: int = 30
MACD_FAST: int = 12
MACD_SLOW: int = 26
MACD_SIGNAL: int = 9


# ---------------------------------------------------------------------------
# Sentiment thresholds
# ---------------------------------------------------------------------------
SENTIMENT_STRONG_POSITIVE: float = 0.3
SENTIMENT_STRONG_NEGATIVE: float = -0.3
SENTIMENT_FULL_SIZE: float = 1.0    # multiplier when strongly aligned
SENTIMENT_NEUTRAL_SIZE: float = 0.75

# News lookback window (hours)
NEWS_LOOKBACK_HOURS: int = 24


# ---------------------------------------------------------------------------
# Scheduling
# ---------------------------------------------------------------------------
LOOP_INTERVAL_SECONDS: int = 60       # main loop cadence
REPORT_HOUR_AMSTERDAM: int = 20       # daily report at 20:00 Amsterdam time
EOD_CLOSE_HOUR_UTC: int = 21          # close all before weekend (Friday 21:00 UTC)


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
LOG_DIR: Path = _ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)


# ---------------------------------------------------------------------------
# Kill switch
# ---------------------------------------------------------------------------
KILL_SWITCH_FILE: Path = _ROOT / "STOP"


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------
def validate() -> None:
    """Raise RuntimeError if critical config is missing."""
    missing = []
    if not OANDA_API_KEY:
        missing.append("OANDA_API_KEY")
    if not OANDA_ACCOUNT_ID:
        missing.append("OANDA_ACCOUNT_ID")
    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}. "
            "Copy .env.example to .env and fill in your credentials."
        )
    if OANDA_ENV not in ("practice", "live"):
        raise RuntimeError("OANDA_ENV must be 'practice' or 'live'.")
    if OANDA_ENV == "live":
        raise RuntimeError(
            "OANDA_ENV is set to 'live'. Switch only after explicit confirmation."
        )
