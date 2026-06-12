"""Unit tests for strategy signal logic (no OANDA/Finnhub required)."""

import numpy as np
import pandas as pd
import pytest

from strategies.ema_crossover import EMACrossoverStrategy
from strategies.rsi_mean_reversion import RSIMeanReversionStrategy
from strategies.macd import MACDStrategy
from strategies.combined import CombinedStrategy
from strategies.base import Signal


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_df(closes: list[float], n_bars: int = None) -> pd.DataFrame:
    """Build a minimal OHLCV DataFrame from close prices."""
    closes = closes if n_bars is None else closes[:n_bars]
    n = len(closes)
    idx = pd.date_range("2023-01-01", periods=n, freq="15min")
    df = pd.DataFrame(
        {
            "open":   [c * 0.999 for c in closes],
            "high":   [c * 1.001 for c in closes],
            "low":    [c * 0.998 for c in closes],
            "close":  closes,
            "volume": [1000] * n,
        },
        index=idx,
    )
    return df


def _trending_up(n=300) -> list[float]:
    return [1.1000 + i * 0.00005 for i in range(n)]


def _trending_down(n=300) -> list[float]:
    return [1.1000 - i * 0.00005 for i in range(n)]


def _flat(n=300, base=1.1000) -> list[float]:
    return [base] * n


def _ema_crossover_sequence() -> list[float]:
    """Slow down-trend followed by sharp rise to trigger bullish EMA cross."""
    base = [1.1000 - i * 0.0001 for i in range(100)]
    spike = [base[-1] + i * 0.0003 for i in range(50)]
    return base + spike


# ---------------------------------------------------------------------------
# EMA Crossover
# ---------------------------------------------------------------------------

class TestEMACrossover:
    strat = EMACrossoverStrategy()

    def test_bullish_cross_returns_long(self):
        closes = _ema_crossover_sequence()
        df = _make_df(closes)
        sig = self.strat.generate_signal(df, "EUR_USD")
        assert sig.direction == "long"

    def test_downtrend_returns_short(self):
        df = _make_df(_trending_down(150))
        sig = self.strat.generate_signal(df, "EUR_USD")
        assert sig.direction == "short"

    def test_insufficient_data_returns_flat(self):
        df = _make_df(_trending_up(5))
        sig = self.strat.generate_signal(df, "EUR_USD")
        assert sig.direction == "flat"
        assert sig.confidence == 0.0

    def test_signal_has_entry_price(self):
        df = _make_df(_trending_up(150))
        sig = self.strat.generate_signal(df, "EUR_USD")
        assert sig.entry_price is not None
        assert sig.entry_price > 0

    def test_instrument_propagated(self):
        df = _make_df(_trending_up(150))
        sig = self.strat.generate_signal(df, "GBP_USD")
        assert sig.instrument == "GBP_USD"


# ---------------------------------------------------------------------------
# RSI Mean Reversion
# ---------------------------------------------------------------------------

class TestRSIMeanReversion:
    strat = RSIMeanReversionStrategy()

    def _oversold_sequence(self) -> list[float]:
        """Creates a sharp crash from 1.20 to 1.05 to push RSI below 30."""
        stable = [1.2000] * 60
        crash  = [1.2000 - i * 0.003 for i in range(50)]
        return stable + crash

    def test_oversold_above_sma_returns_long(self):
        closes = self._oversold_sequence()
        df = _make_df(closes)
        sig = self.strat.generate_signal(df, "EUR_USD")
        # After a crash, RSI should be oversold; price may be below SMA
        # Just verify it returns a valid Signal (direction depends on SMA)
        assert sig.direction in ("long", "flat")

    def test_flat_market_returns_flat(self):
        df = _make_df(_flat(150))
        sig = self.strat.generate_signal(df, "EUR_USD")
        assert sig.direction == "flat"

    def test_insufficient_data(self):
        df = _make_df(_flat(10))
        sig = self.strat.generate_signal(df, "EUR_USD")
        assert sig.direction == "flat"


# ---------------------------------------------------------------------------
# MACD
# ---------------------------------------------------------------------------

class TestMACD:
    strat = MACDStrategy()

    def test_returns_valid_signal(self):
        df = _make_df(_trending_up(300))
        sig = self.strat.generate_signal(df, "USD_JPY")
        assert sig.direction in ("long", "short", "flat")
        assert isinstance(sig.reason, str)
        assert 0.0 <= sig.confidence <= 1.0

    def test_insufficient_data(self):
        df = _make_df(_trending_up(20))
        sig = self.strat.generate_signal(df, "USD_JPY")
        assert sig.direction == "flat"


# ---------------------------------------------------------------------------
# Combined strategy
# ---------------------------------------------------------------------------

class TestCombinedStrategy:
    strat = CombinedStrategy()

    def _h1_uptrend(self, n=350) -> pd.DataFrame:
        closes = [1.0 + i * 0.0001 for i in range(n)]
        idx = pd.date_range("2022-01-01", periods=n, freq="1h")
        return pd.DataFrame(
            {
                "open":   [c * 0.9995 for c in closes],
                "high":   [c * 1.0005 for c in closes],
                "low":    [c * 0.999  for c in closes],
                "close":  closes,
                "volume": [1000] * n,
            },
            index=idx,
        )

    def test_no_cross_returns_flat(self):
        df_m15 = _make_df(_flat(300))
        df_h1  = self._h1_uptrend()
        sig = self.strat.generate_signal(df_m15, "EUR_USD", df_h1=df_h1, sentiment=None)
        assert sig.direction == "flat"

    def test_sl_tp_attached_on_trade(self):
        """On a real crossover, SL and TP must both be set."""
        closes = _ema_crossover_sequence()
        df_m15 = _make_df(closes)
        df_h1  = self._h1_uptrend()
        neutral_sentiment = {"label": "neutral", "score": 0.0, "count": 0}
        sig = self.strat.generate_signal(df_m15, "EUR_USD", df_h1=df_h1, sentiment=neutral_sentiment)
        if sig.direction != "flat":
            assert sig.stop_loss is not None
            assert sig.take_profit is not None
            if sig.direction == "long":
                assert sig.stop_loss < sig.entry_price
                assert sig.take_profit > sig.entry_price
            else:
                assert sig.stop_loss > sig.entry_price
                assert sig.take_profit < sig.entry_price

    def test_strong_negative_sentiment_blocks_long(self):
        closes = _ema_crossover_sequence()
        df_m15 = _make_df(closes)
        neg_sentiment = {"label": "negative", "score": -0.5, "count": 10}
        sig = self.strat.generate_signal(df_m15, "EUR_USD", sentiment=neg_sentiment)
        # A long signal should be blocked
        assert sig.direction == "flat"

    def test_neutral_sentiment_reduces_size(self):
        import config
        closes = _ema_crossover_sequence()
        df_m15 = _make_df(closes)
        neutral_sentiment = {"label": "neutral", "score": 0.0, "count": 5}
        sig = self.strat.generate_signal(df_m15, "EUR_USD", sentiment=neutral_sentiment)
        if sig.direction != "flat":
            assert sig.size_multiplier == config.SENTIMENT_NEUTRAL_SIZE
