"""RSI mean-reversion with SMA(20) trend filter."""

import logging

import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import SMAIndicator

import config
from strategies.base import Direction, Signal, Strategy

logger = logging.getLogger(__name__)

SMA_PERIOD = 20


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rsi"] = RSIIndicator(df["close"], window=config.RSI_PERIOD, fillna=False).rsi()
    df[f"sma_{SMA_PERIOD}"] = SMAIndicator(df["close"], window=SMA_PERIOD, fillna=False).sma_indicator()
    return df


class RSIMeanReversionStrategy(Strategy):
    name = "rsi_mean_reversion"

    def generate_signal(self, df: pd.DataFrame, instrument: str, **kwargs) -> Signal:
        df = add_indicators(df)
        sma_col = f"sma_{SMA_PERIOD}"

        if len(df) < SMA_PERIOD + config.RSI_PERIOD:
            return Signal("flat", 0.0, "insufficient data", instrument)

        df = df.dropna(subset=["rsi", sma_col])
        if df.empty:
            return Signal("flat", 0.0, "insufficient data after dropna", instrument)

        rsi = df["rsi"].iloc[-1]
        price = df["close"].iloc[-1]
        sma = df[sma_col].iloc[-1]

        # Oversold + price above SMA → potential long
        if rsi < config.RSI_OVERSOLD and price > sma:
            direction: Direction = "long"
            reason = f"RSI {rsi:.1f} < {config.RSI_OVERSOLD} (oversold), price above SMA{SMA_PERIOD}"
            confidence = (config.RSI_OVERSOLD - rsi) / config.RSI_OVERSOLD

        # Overbought + price below SMA → potential short
        elif rsi > config.RSI_OVERBOUGHT and price < sma:
            direction = "short"
            reason = f"RSI {rsi:.1f} > {config.RSI_OVERBOUGHT} (overbought), price below SMA{SMA_PERIOD}"
            confidence = (rsi - config.RSI_OVERBOUGHT) / (100 - config.RSI_OVERBOUGHT)

        else:
            direction = "flat"
            reason = f"RSI {rsi:.1f} neutral"
            confidence = 0.0

        logger.debug("[%s] RSI signal: %s (%s)", instrument, direction, reason)
        return Signal(direction, confidence, reason, instrument, entry_price=price)
