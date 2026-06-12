"""
Risk management:
  - Position sizing (max 1% account equity per trade)
  - ATR-based stop-loss, 2:1 take-profit
  - Max 3 open positions
  - Daily loss 3% halt
  - Kill switch (STOP file)
"""

import logging
from datetime import date, datetime, timezone
from pathlib import Path

import config

logger = logging.getLogger(__name__)


class DailyLossTracker:
    """Tracks realised P&L per day and raises halt when limit exceeded."""

    def __init__(self) -> None:
        self._date: date = datetime.now(timezone.utc).date()
        self._start_equity: float = 0.0
        self._realised_pnl: float = 0.0
        self._halted: bool = False

    def set_equity(self, equity: float) -> None:
        today = datetime.now(timezone.utc).date()
        if today != self._date:
            # New trading day — reset
            self._date = today
            self._start_equity = equity
            self._realised_pnl = 0.0
            self._halted = False
            logger.info("New trading day — daily loss tracker reset. Equity: %.2f", equity)
        elif self._start_equity == 0.0:
            self._start_equity = equity

    def record_trade(self, pnl: float) -> None:
        self._realised_pnl += pnl

    @property
    def is_halted(self) -> bool:
        if self._halted:
            return True
        if self._start_equity > 0:
            loss_pct = -self._realised_pnl / self._start_equity
            if loss_pct >= config.MAX_DAILY_LOSS_PCT:
                self._halted = True
                logger.critical(
                    "Daily loss limit reached: %.2f%% (%.2f). Trading halted for today.",
                    loss_pct * 100,
                    self._realised_pnl,
                )
        return self._halted

    @property
    def daily_pnl(self) -> float:
        return self._realised_pnl


class RiskManager:
    def __init__(self) -> None:
        self.daily_tracker = DailyLossTracker()

    # ------------------------------------------------------------------
    # Kill switch
    # ------------------------------------------------------------------
    @staticmethod
    def kill_switch_active() -> bool:
        active = config.KILL_SWITCH_FILE.exists()
        if active:
            logger.critical("KILL SWITCH active (STOP file found). Halting all trading.")
        return active

    # ------------------------------------------------------------------
    # Position sizing
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_units(
        account_equity: float,
        entry_price: float,
        stop_price: float,
        instrument: str,
        sentiment_multiplier: float = 1.0,
    ) -> int:
        """
        Calculate position size so that risk = MAX_RISK_PER_TRADE_PCT × equity.
        Returns integer units (OANDA uses units, not lots).
        """
        risk_amount = account_equity * config.MAX_RISK_PER_TRADE_PCT * sentiment_multiplier
        stop_distance = abs(entry_price - stop_price)
        if stop_distance == 0:
            logger.warning("Stop distance is zero, cannot size position.")
            return 0

        # For forex: 1 unit ≈ 1 base currency unit
        # risk_amount = units × stop_distance  (simplified; ignores pip value conversion)
        units = int(risk_amount / stop_distance)
        logger.debug(
            "Position size [%s]: equity=%.2f risk=%.2f stop_dist=%.5f units=%d",
            instrument,
            account_equity,
            risk_amount,
            stop_distance,
            units,
        )
        return max(units, 1)

    # ------------------------------------------------------------------
    # Stop / TP from ATR
    # ------------------------------------------------------------------
    @staticmethod
    def calculate_stops(
        entry_price: float,
        atr: float,
        direction: str,
    ) -> tuple[float, float]:
        """Return (stop_loss, take_profit)."""
        stop_distance = atr * config.ATR_MULTIPLIER
        tp_distance = stop_distance * config.MIN_REWARD_RISK
        if direction == "long":
            sl = entry_price - stop_distance
            tp = entry_price + tp_distance
        else:
            sl = entry_price + stop_distance
            tp = entry_price - tp_distance
        return sl, tp

    # ------------------------------------------------------------------
    # Gate checks
    # ------------------------------------------------------------------
    def can_trade(
        self,
        account_equity: float,
        open_positions_count: int,
    ) -> tuple[bool, str]:
        """Return (allowed, reason). Updates daily tracker with current equity."""
        self.daily_tracker.set_equity(account_equity)

        if self.kill_switch_active():
            return False, "Kill switch active"
        if self.daily_tracker.is_halted:
            return False, "Daily loss limit reached"
        if open_positions_count >= config.MAX_OPEN_POSITIONS:
            return False, f"Max open positions ({config.MAX_OPEN_POSITIONS}) reached"
        return True, "ok"
