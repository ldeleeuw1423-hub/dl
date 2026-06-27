from trader.config import KELLY_LOOKBACK, KELLY_FRACTION


def calc_kelly(portfolio: dict, regime: str) -> float:
    """
    Half-Kelly positiegrootte per regime (trending/sideways).
    Fallback naar 1% van portfolio bij < KELLY_LOOKBACK trades.
    """
    closed = [t for t in portfolio.get('closed', []) if t.get('regime') == regime]
    recent = closed[-KELLY_LOOKBACK:]
    balance = portfolio['balance']

    if len(recent) < KELLY_LOOKBACK:
        return balance * 0.01   # 1% fallback

    wins   = [t['pnl'] for t in recent if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in recent if t['pnl'] < 0]
    win_rate = len(wins) / len(recent)
    avg_win  = sum(wins) / len(wins) if wins else 1.0
    avg_loss = sum(losses) / len(losses) if losses else 1.0
    odds = avg_win / avg_loss if avg_loss > 0 else 1.0

    kelly = max(0.0, (win_rate * odds - (1 - win_rate)) / odds)
    size = balance * kelly * KELLY_FRACTION
    return min(balance * 0.95, max(balance * 0.005, size))  # nooit minder dan 0.5%
