"""
Backtesting engine.
Uses the `backtesting` library strategy wrapper for each of our strategies,
then delegates to metrics.py for reporting.
"""

import logging
from typing import Optional

import numpy as np
import pandas as pd
from ta.trend import EMAIndicator, SMAIndicator, MACD as MACDIndicator
from ta.momentum import RSIIndicator
from ta.volatility import AverageTrueRange
from backtesting import Backtest, Strategy as BTStrategy

import config
from backtester.metrics import BacktestResult, compute_metrics, plot_equity_curve

logger = logging.getLogger(__name__)


def _ema(series: pd.Series, window: int) -> np.ndarray:
    return EMAIndicator(series, window=window, fillna=False).ema_indicator().values

def _sma(series: pd.Series, window: int) -> np.ndarray:
    return SMAIndicator(series, window=window, fillna=False).sma_indicator().values

def _rsi(series: pd.Series, window: int) -> np.ndarray:
    return RSIIndicator(series, window=window, fillna=False).rsi().values

def _atr(high: pd.Series, low: pd.Series, close: pd.Series, window: int) -> np.ndarray:
    return AverageTrueRange(high, low, close, window=window, fillna=False).average_true_range().values


# ---------------------------------------------------------------------------
# backtesting-lib adapter classes
# ---------------------------------------------------------------------------

class _EMABase(BTStrategy):
    fast = config.EMA_FAST
    slow = config.EMA_SLOW
    atr_period = config.ATR_PERIOD
    atr_mult = config.ATR_MULTIPLIER
    rr = config.MIN_REWARD_RISK

    def init(self):
        close = pd.Series(self.data.Close)
        high  = pd.Series(self.data.High)
        low   = pd.Series(self.data.Low)
        self.ema_fast = self.I(_ema, close, self.fast)
        self.ema_slow = self.I(_ema, close, self.slow)
        self.atr      = self.I(_atr, high, low, close, self.atr_period)

    def next(self):
        if np.isnan(self.ema_fast[-1]) or np.isnan(self.ema_slow[-1]) or np.isnan(self.atr[-1]):
            return

        cross_up   = self.ema_fast[-2] <= self.ema_slow[-2] and self.ema_fast[-1] > self.ema_slow[-1]
        cross_down = self.ema_fast[-2] >= self.ema_slow[-2] and self.ema_fast[-1] < self.ema_slow[-1]
        price = self.data.Close[-1]
        stop_dist = self.atr[-1] * self.atr_mult
        tp_dist = stop_dist * self.rr

        if cross_up and not self.position.is_long:
            if self.position.is_short:
                self.position.close()
            self.buy(sl=price - stop_dist, tp=price + tp_dist)

        elif cross_down and not self.position.is_short:
            if self.position.is_long:
                self.position.close()
            self.sell(sl=price + stop_dist, tp=price - tp_dist)


class _RSIBase(BTStrategy):
    rsi_period = config.RSI_PERIOD
    ob = config.RSI_OVERBOUGHT
    os_ = config.RSI_OVERSOLD
    sma_period = 20
    atr_period = config.ATR_PERIOD
    atr_mult = config.ATR_MULTIPLIER
    rr = config.MIN_REWARD_RISK

    def init(self):
        close = pd.Series(self.data.Close)
        high  = pd.Series(self.data.High)
        low   = pd.Series(self.data.Low)
        self.rsi = self.I(_rsi, close, self.rsi_period)
        self.sma = self.I(_sma, close, self.sma_period)
        self.atr = self.I(_atr, high, low, close, self.atr_period)

    def next(self):
        if any(np.isnan(v) for v in [self.rsi[-1], self.sma[-1], self.atr[-1]]):
            return
        price = self.data.Close[-1]
        stop_dist = self.atr[-1] * self.atr_mult
        tp_dist = stop_dist * self.rr

        if self.rsi[-1] < self.os_ and price > self.sma[-1] and not self.position.is_long:
            if self.position.is_short:
                self.position.close()
            self.buy(sl=price - stop_dist, tp=price + tp_dist)

        elif self.rsi[-1] > self.ob and price < self.sma[-1] and not self.position.is_short:
            if self.position.is_long:
                self.position.close()
            self.sell(sl=price + stop_dist, tp=price - tp_dist)


class _MACDBase(BTStrategy):
    fast_w   = config.MACD_FAST
    slow_w   = config.MACD_SLOW
    sign_w   = config.MACD_SIGNAL
    atr_period = config.ATR_PERIOD
    atr_mult = config.ATR_MULTIPLIER
    rr = config.MIN_REWARD_RISK

    def init(self):
        close = pd.Series(self.data.Close)
        high  = pd.Series(self.data.High)
        low   = pd.Series(self.data.Low)
        ind = MACDIndicator(close, window_slow=self.slow_w, window_fast=self.fast_w,
                            window_sign=self.sign_w, fillna=False)
        self.macd_line   = self.I(lambda: ind.macd().values)
        self.signal_line = self.I(lambda: ind.macd_signal().values)
        self.atr = self.I(_atr, high, low, close, self.atr_period)

    def next(self):
        if any(np.isnan(v) for v in [self.macd_line[-1], self.signal_line[-1], self.atr[-1]]):
            return
        price = self.data.Close[-1]
        stop_dist = self.atr[-1] * self.atr_mult
        tp_dist = stop_dist * self.rr

        cross_up   = self.macd_line[-2] <= self.signal_line[-2] and self.macd_line[-1] > self.signal_line[-1]
        cross_down = self.macd_line[-2] >= self.signal_line[-2] and self.macd_line[-1] < self.signal_line[-1]

        if cross_up and not self.position.is_long:
            if self.position.is_short:
                self.position.close()
            self.buy(sl=price - stop_dist, tp=price + tp_dist)
        elif cross_down and not self.position.is_short:
            if self.position.is_long:
                self.position.close()
            self.sell(sl=price + stop_dist, tp=price - tp_dist)


STRATEGY_MAP = {
    "ema_crossover":      _EMABase,
    "rsi_mean_reversion": _RSIBase,
    "macd":               _MACDBase,
}


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_backtest(
    df: pd.DataFrame,
    strategy_name: str,
    initial_cash: float = 10_000.0,
    commission: float = 0.0002,   # 0.02% spread approx
) -> BacktestResult:
    """
    Run a strategy backtest on *df* (OHLCV, standard column names).
    Returns a BacktestResult with stats and trade list.
    """
    bt_cls = STRATEGY_MAP.get(strategy_name)
    if bt_cls is None:
        raise ValueError(f"Unknown strategy '{strategy_name}'. Available: {list(STRATEGY_MAP)}")

    # backtesting.py needs Title-cased columns
    df_bt = df.rename(
        columns={"open": "Open", "high": "High", "low": "Low", "close": "Close", "volume": "Volume"}
    )
    df_bt.index.name = None

    bt = Backtest(df_bt, bt_cls, cash=initial_cash, commission=commission, exclusive_orders=True)
    stats = bt.run()
    trades = stats._trades if hasattr(stats, "_trades") else pd.DataFrame()

    result = compute_metrics(stats, trades, strategy_name)
    logger.info(
        "Backtest [%s]: trades=%d win_rate=%.1f%% pf=%.2f drawdown=%.1f%% sharpe=%.2f",
        strategy_name,
        result.total_trades,
        result.win_rate * 100,
        result.profit_factor,
        result.max_drawdown * 100,
        result.sharpe_ratio,
    )
    return result


def run_all_strategies(
    df: pd.DataFrame,
    instrument: str = "EUR_USD",
) -> dict[str, BacktestResult]:
    """Run all three base strategies and return results dict."""
    results = {}
    for name in STRATEGY_MAP:
        logger.info("Running backtest: %s on %s", name, instrument)
        results[name] = run_backtest(df, name)
    return results
