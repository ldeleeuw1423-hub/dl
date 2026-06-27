import json
from datetime import datetime, timezone
from trader.config import PORTFOLIO_FILE, START_BALANCE


def load() -> dict:
    if PORTFOLIO_FILE.exists():
        return json.loads(PORTFOLIO_FILE.read_text())
    return {
        'balance':      START_BALANCE,
        'start':        START_BALANCE,
        'realized_pnl': 0.0,
        'positions':    [],
        'closed':       [],
    }


def save(portfolio: dict):
    PORTFOLIO_FILE.write_text(json.dumps(portfolio, indent=2))


def total_value(portfolio: dict) -> float:
    pos_val = sum(p['pos_size'] for p in portfolio['positions'])
    return portfolio['balance'] + pos_val


def open_position(portfolio: dict, pos: dict):
    """Voegt positie toe en trekt cash af. pos bevat alle entry-features."""
    portfolio['balance'] -= pos['pos_size']
    portfolio['positions'].append(pos)
    save(portfolio)


def close_position(portfolio: dict, index: int, exit_price: float, reason: str) -> dict:
    """Sluit positie op index, retourneert afgesloten trade-dict."""
    pos = portfolio['positions'].pop(index)
    pnl = (exit_price - pos['entry']) * pos['qty']
    portfolio['balance'] += pos['pos_size'] + pnl
    portfolio['realized_pnl'] = portfolio.get('realized_pnl', 0.0) + pnl

    closed = {
        **pos,
        'exit':         exit_price,
        'exit_reason':  reason,
        'pnl':          round(pnl, 6),
        'exit_ts':      datetime.now(timezone.utc).isoformat(),
    }
    portfolio['closed'].append(closed)
    save(portfolio)
    return closed


def check_sl_tp(portfolio: dict, prices: dict) -> list:
    """
    Controleert SL/TP voor alle open posities.
    Trailing stop: verhoogt SL mee als prijs stijgt.
    Retourneert lijst van afgesloten trades.
    """
    closed_trades = []
    for i in range(len(portfolio['positions']) - 1, -1, -1):
        pos = portfolio['positions'][i]
        sym = pos.get('sym', pos['pair'].replace('EUR', ''))
        cur = prices.get(sym)
        if not cur or cur <= 0:
            continue

        # Trailing stop
        if cur > pos['entry'] and pos.get('sl_pct'):
            trail_sl = round(cur * (1 - pos['sl_pct'] / 100), 8)
            if trail_sl > pos['sl']:
                portfolio['positions'][i]['sl'] = trail_sl

        hit_price, reason = None, ''
        if pos.get('sl') and cur <= pos['sl']:
            hit_price, reason = pos['sl'], 'stop_loss'
        if pos.get('tp') and cur >= pos['tp']:
            hit_price, reason = pos['tp'], 'take_profit'

        if hit_price:
            closed = close_position(portfolio, i, hit_price, reason)
            closed_trades.append(closed)

    return closed_trades
