"""MACD(12,26,9) signal line crossover strategy."""

import logging

import pandas as pd
from ta.trend import MACD as MACDIndicator

import config
from strategies.base import Direction, Signal, Strategy

logger = logging.getLogger(__name__)

_MACD_COL  = "macd"
_HIST_COL  = "macd_hist"
_SIGNAL_COL = "macd_signal"


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    ind = MACDIndicator(
        df["close"],
        window_slow=config.MACD_SLOW,
        window_fast=config.MACD_FAST,
        window_sign=config.MACD_SIGNAL,
        fillna=False,
    )
    df[_MACD_COL]   = ind.macd()
    df[_SIGNAL_COL] = ind.macd_signal()
    df[_HIST_COL]   = ind.macd_diff()
    return df


class MACDStrategy(Strategy):
    name = "macd"

    def generate_signal(self, df: pd.DataFrame, instrument: str, **kwargs) -> Signal:
        df = add_indicators(df)

        needed = [_MACD_COL, _SIGNAL_COL]
        if not all(c in df.columns for c in needed):
            return Signal("flat", 0.0, "MACD columns missing", instrument)

        df = df.dropna(subset=needed)
        if len(df) < 2:
            return Signal("flat", 0.0, "insufficient data", instrument)

        prev_macd   = df[_MACD_COL].iloc[-2]
        prev_signal = df[_SIGNAL_COL].iloc[-2]
        curr_macd   = df[_MACD_COL].iloc[-1]
        curr_signal = df[_SIGNAL_COL].iloc[-1]
        price = df["close"].iloc[-1]

        bullish_cross = prev_macd <= prev_signal and curr_macd > curr_signal
        bearish_cross = prev_macd >= prev_signal and curr_macd < curr_signal

        if bullish_cross:
            direction: Direction = "long"
            reason = "MACD crossed above signal line"
            confidence = min(1.0, abs(curr_macd - curr_signal) * 10)
        elif bearish_cross:
            direction = "short"
            reason = "MACD crossed below signal line"
            confidence = min(1.0, abs(curr_macd - curr_signal) * 10)
        else:
            if curr_macd > curr_signal:
                direction = "long"
                reason = "MACD above signal (bullish momentum)"
            elif curr_macd < curr_signal:
                direction = "short"
                reason = "MACD below signal (bearish momentum)"
            else:
                direction = "flat"
                reason = "MACD == signal"
            confidence = 0.3

        logger.debug("[%s] MACD signal: %s (%s)", instrument, direction, reason)
        return Signal(direction, confidence, reason, instrument, entry_price=price)
