"""EMA(9)/EMA(21) crossover strategy."""

import logging

import pandas as pd
import ta as ta_lib
from ta.trend import EMAIndicator

import config
from strategies.base import Direction, Signal, Strategy

logger = logging.getLogger(__name__)


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Add EMA fast/slow columns in-place and return df."""
    df = df.copy()
    df[f"ema_{config.EMA_FAST}"] = EMAIndicator(df["close"], window=config.EMA_FAST, fillna=False).ema_indicator()
    df[f"ema_{config.EMA_SLOW}"] = EMAIndicator(df["close"], window=config.EMA_SLOW, fillna=False).ema_indicator()
    return df


class EMACrossoverStrategy(Strategy):
    name = "ema_crossover"

    def generate_signal(self, df: pd.DataFrame, instrument: str, **kwargs) -> Signal:
        df = add_indicators(df)
        fast_col = f"ema_{config.EMA_FAST}"
        slow_col = f"ema_{config.EMA_SLOW}"

        if len(df) < config.EMA_SLOW + 5:
            return Signal("flat", 0.0, "insufficient data", instrument)

        df = df.dropna(subset=[fast_col, slow_col])
        if len(df) < 2:
            return Signal("flat", 0.0, "insufficient data after dropna", instrument)

        prev_fast = df[fast_col].iloc[-2]
        prev_slow = df[slow_col].iloc[-2]
        curr_fast = df[fast_col].iloc[-1]
        curr_slow = df[slow_col].iloc[-1]
        price = df["close"].iloc[-1]

        bullish_cross = prev_fast <= prev_slow and curr_fast > curr_slow
        bearish_cross = prev_fast >= prev_slow and curr_fast < curr_slow

        if bullish_cross:
            direction: Direction = "long"
            reason = f"EMA{config.EMA_FAST} crossed above EMA{config.EMA_SLOW}"
            confidence = min(1.0, abs(curr_fast - curr_slow) / price * 1000)
        elif bearish_cross:
            direction = "short"
            reason = f"EMA{config.EMA_FAST} crossed below EMA{config.EMA_SLOW}"
            confidence = min(1.0, abs(curr_fast - curr_slow) / price * 1000)
        else:
            # Trend direction while no fresh cross
            if curr_fast > curr_slow:
                direction = "long"
                reason = "EMA fast > slow (uptrend, no new cross)"
            elif curr_fast < curr_slow:
                direction = "short"
                reason = "EMA fast < slow (downtrend, no new cross)"
            else:
                direction = "flat"
                reason = "EMA fast == slow"
            confidence = 0.3

        logger.debug("[%s] EMA cross signal: %s (%s)", instrument, direction, reason)
        return Signal(direction, confidence, reason, instrument, entry_price=price)
