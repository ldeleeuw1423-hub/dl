"""Backtest performance metrics and equity curve visualisation."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    strategy_name: str
    total_trades:  int
    win_rate:      float    # 0–1
    profit_factor: float
    max_drawdown:  float    # 0–1 fraction
    sharpe_ratio:  float
    total_return:  float    # fraction
    equity_curve:  Optional[pd.Series] = field(default=None, repr=False)
    trades_df:     Optional[pd.DataFrame] = field(default=None, repr=False)
    raw_stats:     Optional[object] = field(default=None, repr=False)

    def summary(self) -> str:
        return (
            f"Strategy: {self.strategy_name}\n"
            f"  Trades        : {self.total_trades}\n"
            f"  Win Rate      : {self.win_rate*100:.1f}%\n"
            f"  Profit Factor : {self.profit_factor:.2f}\n"
            f"  Max Drawdown  : {self.max_drawdown*100:.1f}%\n"
            f"  Sharpe Ratio  : {self.sharpe_ratio:.2f}\n"
            f"  Total Return  : {self.total_return*100:.1f}%\n"
        )


def compute_metrics(stats, trades_df: pd.DataFrame, strategy_name: str) -> BacktestResult:
    """Extract metrics from a backtesting.py stats object."""
    total_trades = int(stats.get("# Trades", 0))
    win_rate = float(stats.get("Win Rate [%]", 0)) / 100
    max_dd = abs(float(stats.get("Max. Drawdown [%]", 0))) / 100
    sharpe = float(stats.get("Sharpe Ratio", 0.0) or 0.0)
    total_ret = float(stats.get("Return [%]", 0)) / 100

    # Profit factor: gross profit / gross loss
    pf = 0.0
    if not trades_df.empty and "PnL" in trades_df.columns:
        wins  = trades_df.loc[trades_df["PnL"] > 0, "PnL"].sum()
        losses = abs(trades_df.loc[trades_df["PnL"] < 0, "PnL"].sum())
        pf = wins / losses if losses > 0 else (float("inf") if wins > 0 else 0.0)

    equity = None
    if hasattr(stats, "_equity_curve"):
        equity = stats._equity_curve.get("Equity", None)

    return BacktestResult(
        strategy_name=strategy_name,
        total_trades=total_trades,
        win_rate=win_rate,
        profit_factor=pf,
        max_drawdown=max_dd,
        sharpe_ratio=sharpe,
        total_return=total_ret,
        equity_curve=equity,
        trades_df=trades_df,
        raw_stats=stats,
    )


def plot_equity_curve(
    results: dict[str, BacktestResult],
    output_path: Optional[Path] = None,
    show: bool = False,
) -> None:
    """Plot equity curves for all strategies in a comparison chart."""
    try:
        import matplotlib.pyplot as plt
        import matplotlib.dates as mdates
    except ImportError:
        logger.warning("matplotlib not available — skipping equity curve plot.")
        return

    fig, ax = plt.subplots(figsize=(14, 6))
    for name, res in results.items():
        if res.equity_curve is not None and not res.equity_curve.empty:
            normalised = res.equity_curve / res.equity_curve.iloc[0] * 100
            ax.plot(normalised.index, normalised.values, label=name, linewidth=1.5)

    ax.set_title("Equity Curve Comparison (indexed to 100)")
    ax.set_ylabel("Equity (indexed)")
    ax.set_xlabel("Date")
    ax.legend()
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=3))
    plt.xticks(rotation=45)
    plt.tight_layout()

    if output_path:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=150)
        logger.info("Equity curve saved to %s", output_path)
    if show:
        plt.show()
    plt.close()


def print_comparison_table(results: dict[str, BacktestResult]) -> None:
    """Print a side-by-side table of all strategy results."""
    header = f"{'Strategy':<25} {'Trades':>8} {'Win%':>8} {'PF':>8} {'DD%':>8} {'Sharpe':>8} {'Ret%':>8}"
    print("\n" + "=" * len(header))
    print(header)
    print("=" * len(header))
    for name, r in results.items():
        print(
            f"{r.strategy_name:<25} "
            f"{r.total_trades:>8} "
            f"{r.win_rate*100:>7.1f}% "
            f"{r.profit_factor:>8.2f} "
            f"{r.max_drawdown*100:>7.1f}% "
            f"{r.sharpe_ratio:>8.2f} "
            f"{r.total_return*100:>7.1f}%"
        )
    print("=" * len(header) + "\n")
