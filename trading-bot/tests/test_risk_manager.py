"""Unit tests for RiskManager (no external API calls)."""

import pytest
from pathlib import Path
from unittest.mock import patch

import config
from risk.risk_manager import DailyLossTracker, RiskManager


class TestDailyLossTracker:
    def test_not_halted_initially(self):
        t = DailyLossTracker()
        t.set_equity(10_000)
        assert not t.is_halted

    def test_halts_at_limit(self):
        t = DailyLossTracker()
        t.set_equity(10_000)
        t.record_trade(-350)   # -3.5% > 3% limit
        assert t.is_halted

    def test_not_halted_below_limit(self):
        t = DailyLossTracker()
        t.set_equity(10_000)
        t.record_trade(-200)   # -2% < 3%
        assert not t.is_halted

    def test_daily_pnl_accumulates(self):
        t = DailyLossTracker()
        t.set_equity(10_000)
        t.record_trade(100)
        t.record_trade(-50)
        assert t.daily_pnl == pytest.approx(50.0)


class TestRiskManager:
    def test_can_trade_ok(self):
        rm = RiskManager()
        allowed, reason = rm.can_trade(10_000, 0)
        assert allowed
        assert reason == "ok"

    def test_blocked_max_positions(self):
        rm = RiskManager()
        allowed, reason = rm.can_trade(10_000, config.MAX_OPEN_POSITIONS)
        assert not allowed
        assert "Max open positions" in reason

    def test_blocked_kill_switch(self, tmp_path, monkeypatch):
        stop_file = tmp_path / "STOP"
        stop_file.touch()
        monkeypatch.setattr(config, "KILL_SWITCH_FILE", stop_file)
        rm = RiskManager()
        allowed, reason = rm.can_trade(10_000, 0)
        assert not allowed
        assert "Kill switch" in reason

    def test_blocked_daily_loss(self):
        rm = RiskManager()
        rm.daily_tracker.set_equity(10_000)
        rm.daily_tracker.record_trade(-400)  # -4%
        allowed, reason = rm.can_trade(10_000, 0)
        assert not allowed
        assert "Daily loss" in reason

    def test_position_sizing_basic(self):
        rm = RiskManager()
        # equity 10000, risk 1% = 100, stop_distance 0.01 → ~10000 units
        units = rm.calculate_units(10_000, 1.10, 1.09, "EUR_USD")
        assert abs(units - 10_000) <= 1  # int truncation tolerance

    def test_position_sizing_with_sentiment(self):
        rm = RiskManager()
        units_full    = rm.calculate_units(10_000, 1.10, 1.09, "EUR_USD", sentiment_multiplier=1.0)
        units_partial = rm.calculate_units(10_000, 1.10, 1.09, "EUR_USD", sentiment_multiplier=0.75)
        assert units_partial < units_full

    def test_position_sizing_zero_stop_distance(self):
        rm = RiskManager()
        units = rm.calculate_units(10_000, 1.10, 1.10, "EUR_USD")
        assert units == 0

    def test_calculate_stops_long(self):
        sl, tp = RiskManager.calculate_stops(1.10, 0.001, "long")
        assert sl < 1.10
        assert tp > 1.10
        # TP distance ≥ 2× SL distance
        assert (tp - 1.10) >= 2 * (1.10 - sl) - 1e-9

    def test_calculate_stops_short(self):
        sl, tp = RiskManager.calculate_stops(1.10, 0.001, "short")
        assert sl > 1.10
        assert tp < 1.10
        assert (1.10 - tp) >= 2 * (sl - 1.10) - 1e-9
