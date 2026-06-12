"""
Combined multi-timeframe strategy:
  H1  EMA(200) trend filter  +  M15 EMA(9/21) entry  +  RSI confirmation
  + FinBERT sentiment overlay
"""

import logging
from typing import Optional

import pandas as pd
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange

import config
from strategies.base import Direction, Signal, Strategy
from strategies.ema_crossover import add_indicators as add_ema_indicators

logger = logging.getLogger(__name__)


def _add_trend_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df[f"ema_{config.EMA_TREND}"] = EMAIndicator(df["close"], window=config.EMA_TREND, fillna=False).ema_indicator()
    return df


def _add_rsi(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["rsi"] = RSIIndicator(df["close"], window=config.RSI_PERIOD, fillna=False).rsi()
    return df


def _add_atr(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["atr"] = AverageTrueRange(df["high"], df["low"], df["close"], window=config.ATR_PERIOD, fillna=False).average_true_range()
    return df


class CombinedStrategy(Strategy):
    """
    Full signal pipeline:
      1. H1 EMA(200) trend direction
      2. M15 EMA(9/21) crossover in trend direction
      3. RSI not in extreme opposite zone
      4. Sentiment overlay adjusts size_multiplier
    """

    name = "combined"

    def generate_signal(
        self,
        df: pd.DataFrame,          # M15 candles
        instrument: str,
        df_h1: Optional[pd.DataFrame] = None,
        sentiment: Optional[dict] = None,
        **kwargs,
    ) -> Signal:

        # --- 1. Trend filter (H1) ---
        trend_direction: Direction = "flat"
        if df_h1 is not None and not df_h1.empty:
            df_h1 = _add_trend_indicators(df_h1)
            trend_col = f"ema_{config.EMA_TREND}"
            h1_valid = df_h1.dropna(subset=[trend_col])
            if not h1_valid.empty:
                ema200 = h1_valid[trend_col].iloc[-1]
                price_h1 = h1_valid["close"].iloc[-1]
                trend_direction = "long" if price_h1 > ema200 else "short"

        # --- 2. M15 EMA crossover ---
        df = add_ema_indicators(df)
        df = _add_rsi(df)
        df = _add_atr(df)

        fast_col = f"ema_{config.EMA_FAST}"
        slow_col = f"ema_{config.EMA_SLOW}"

        df_clean = df.dropna(subset=[fast_col, slow_col, "rsi", "atr"])
        if len(df_clean) < 2:
            return Signal("flat", 0.0, "insufficient data", instrument)

        prev_fast = df_clean[fast_col].iloc[-2]
        prev_slow = df_clean[slow_col].iloc[-2]
        curr_fast = df_clean[fast_col].iloc[-1]
        curr_slow = df_clean[slow_col].iloc[-1]
        price = df_clean["close"].iloc[-1]
        rsi = df_clean["rsi"].iloc[-1]
        atr = df_clean["atr"].iloc[-1]

        bullish_cross = prev_fast <= prev_slow and curr_fast > curr_slow
        bearish_cross = prev_fast >= prev_slow and curr_fast < curr_slow

        entry_direction: Direction = "flat"
        reason_parts: list[str] = []

        if bullish_cross:
            entry_direction = "long"
            reason_parts.append(f"EMA{config.EMA_FAST} crossed above EMA{config.EMA_SLOW}")
        elif bearish_cross:
            entry_direction = "short"
            reason_parts.append(f"EMA{config.EMA_FAST} crossed below EMA{config.EMA_SLOW}")
        else:
            return Signal("flat", 0.0, "no EMA crossover on M15", instrument)

        # --- 3. RSI confirmation ---
        # Block long if RSI overbought; block short if RSI oversold
        if entry_direction == "long" and rsi > config.RSI_OVERBOUGHT:
            return Signal(
                "flat", 0.0,
                f"Long blocked: RSI {rsi:.1f} overbought",
                instrument,
            )
        if entry_direction == "short" and rsi < config.RSI_OVERSOLD:
            return Signal(
                "flat", 0.0,
                f"Short blocked: RSI {rsi:.1f} oversold",
                instrument,
            )
        reason_parts.append(f"RSI {rsi:.1f} ok")

        # --- H1 trend alignment ---
        if trend_direction != "flat" and entry_direction != trend_direction:
            return Signal(
                "flat", 0.0,
                f"Entry {entry_direction} conflicts with H1 trend {trend_direction}",
                instrument,
            )
        if trend_direction != "flat":
            reason_parts.append(f"H1 trend {trend_direction}")

        # Stop-loss and take-profit from ATR
        stop_distance = atr * config.ATR_MULTIPLIER
        if entry_direction == "long":
            stop_loss = price - stop_distance
            take_profit = price + stop_distance * config.MIN_REWARD_RISK
        else:
            stop_loss = price + stop_distance
            take_profit = price - stop_distance * config.MIN_REWARD_RISK

        # --- 4. Sentiment overlay ---
        size_multiplier = config.SENTIMENT_NEUTRAL_SIZE
        sentiment_score = 0.0
        if sentiment:
            sentiment_score = sentiment.get("score", 0.0)
            if (
                entry_direction == "long"
                and sentiment_score > config.SENTIMENT_STRONG_POSITIVE
            ):
                size_multiplier = config.SENTIMENT_FULL_SIZE
                reason_parts.append(f"sentiment positive ({sentiment_score:.2f})")
            elif (
                entry_direction == "short"
                and sentiment_score < config.SENTIMENT_STRONG_NEGATIVE
            ):
                size_multiplier = config.SENTIMENT_FULL_SIZE
                reason_parts.append(f"sentiment negative ({sentiment_score:.2f})")
            elif entry_direction == "long" and sentiment_score < config.SENTIMENT_STRONG_NEGATIVE:
                return Signal(
                    "flat", 0.0,
                    f"Long blocked by strong negative sentiment ({sentiment_score:.2f})",
                    instrument,
                )
            elif entry_direction == "short" and sentiment_score > config.SENTIMENT_STRONG_POSITIVE:
                return Signal(
                    "flat", 0.0,
                    f"Short blocked by strong positive sentiment ({sentiment_score:.2f})",
                    instrument,
                )
            else:
                reason_parts.append(f"sentiment neutral ({sentiment_score:.2f}) → 75% size")

        confidence = min(
            1.0,
            (abs(curr_fast - curr_slow) / price * 500)
            + (0.3 if trend_direction == entry_direction else 0.0),
        )

        return Signal(
            direction=entry_direction,
            confidence=confidence,
            reason=" | ".join(reason_parts),
            instrument=instrument,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            size_multiplier=size_multiplier,
        )
