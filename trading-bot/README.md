# Automated Day Trading Platform

A fully automated forex trading bot combining technical analysis (EMA crossover, RSI, MACD) with FinBERT AI sentiment analysis. Trades EUR/USD, USD/JPY, GBP/USD on OANDA practice by default.

---

## Prerequisites

- Python 3.12+
- OANDA demo account → API token from https://developer.oanda.com
- Finnhub free API key from https://finnhub.io

---

## Setup

```bash
cd trading-bot

# Create and activate virtual environment
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
# Edit .env: fill OANDA_API_KEY, OANDA_ACCOUNT_ID, FINNHUB_API_KEY
```

---

## Step-by-step verification

### 1 — Test OANDA connection
```bash
python run_oanda_test.py
```
Prints account balance and sample candles. Fix `.env` if this fails.

### 2 — Run all strategy backtests (2 years H1 data)
```bash
python run_backtest.py
```
Fetches historical data from OANDA and prints a comparison table:
```
Strategy                  Trades    Win%      PF      DD%   Sharpe     Ret%
=========================================================================
ema_crossover                 XX    XX.X%    X.XX    XX.X%     X.XX    XX.X%
rsi_mean_reversion            XX    XX.X%    X.XX    XX.X%     X.XX    XX.X%
macd                          XX    XX.X%    X.XX    XX.X%     X.XX    XX.X%
```
Equity curves saved to `reports/equity_curves.png`.

### 3 — Test FinBERT sentiment (no API key needed)
```bash
python run_sentiment_test.py
```
Downloads ProsusAI/finbert on first run (~500 MB), then scores sample headlines.

### 4 — Run unit tests
```bash
pytest tests/ -v
```

### 5 — Start live bot (practice only)
```bash
python main.py
```
The bot runs every 60 seconds. Create a `STOP` file in this directory to close all positions and halt:
```bash
touch STOP
```

---

## Project structure

```
trading-bot/
├── .env.example            # credential template
├── config.py               # all settings, loaded from .env
├── main.py                 # live trading loop (APScheduler)
├── run_oanda_test.py       # OANDA connection test
├── run_backtest.py         # run all backtests
├── run_sentiment_test.py   # FinBERT smoke test
├── data/
│   ├── market_data.py      # OANDA candles + price feed
│   └── news_feed.py        # Finnhub news with caching
├── ai/
│   └── sentiment.py        # FinBERT wrapper (lazy loaded)
├── strategies/
│   ├── base.py             # Signal dataclass + Strategy ABC
│   ├── ema_crossover.py    # EMA(9)/EMA(21) crossover
│   ├── rsi_mean_reversion.py
│   ├── macd.py             # MACD(12,26,9)
│   └── combined.py         # H1 trend + M15 entry + sentiment
├── risk/
│   └── risk_manager.py     # sizing, daily loss halt, kill switch
├── execution/
│   └── order_manager.py    # OANDA market orders, retries
├── backtester/
│   ├── backtest.py         # backtesting.py adapter
│   └── metrics.py          # win rate, PF, drawdown, Sharpe, plots
├── dashboard/
│   └── report.py           # daily HTML + console report
├── reports/                # generated reports (git-ignored)
├── logs/                   # rotating log files (git-ignored)
└── tests/
    ├── test_signals.py
    └── test_risk_manager.py
```

---

## Signal logic (combined strategy)

1. **H1 trend filter** — only long when close > EMA(200), only short when close < EMA(200)
2. **M15 entry** — EMA(9) crosses EMA(21) in trend direction, RSI not in extreme opposite zone
3. **Sentiment overlay** — FinBERT aggregate score of last 24h news:
   - Score > +0.3 → allow long, full position size
   - Score –0.3 to +0.3 → neutral, 75% size
   - Score < –0.3 → block long (and vice versa for shorts)

---

## Risk management

| Parameter | Value |
|-----------|-------|
| Max risk per trade | 1% of equity |
| Stop-loss | ATR(14) × 1.5 |
| Take-profit | Min 2× stop distance |
| Max open positions | 3 |
| Daily loss halt | 3% of equity |
| Kill switch | `touch STOP` in project root |

---

## Switching to live trading

> **Never switch to live without explicit confirmation.**

When you are ready:
1. Open a real OANDA account and generate a live API token
2. In `.env`: change `OANDA_ENV=live` and update `OANDA_API_KEY` + `OANDA_ACCOUNT_ID`
3. Remove the live-trading guard in `config.py` (`validate()`) after reviewing all risk parameters

---

## Timezone

- Internal timestamps: UTC
- Reports and scheduling: Europe/Amsterdam
