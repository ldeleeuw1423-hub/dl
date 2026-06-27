import csv, logging
from datetime import datetime, timezone
from trader.config import TRADES_CSV

log = logging.getLogger('autotrader.logger')

FIELDNAMES = [
    # Entry features
    'trade_id', 'coin', 'entry_timestamp', 'entry_price',
    'regime', 'adx', 'rsi', 'bb_width', 'bb_position',
    'ema_fast', 'ema_slow', 'news_sentiment_score', 'reddit_sentiment_score',
    'fear_greed_index', 'kelly_fraction_used', 'position_size_pct',
    'stop_loss_pct', 'take_profit_pct', 'stop_loss_multiplier_at_entry',
    # Exit outcomes (leeg bij openen, ingevuld bij sluiten)
    'exit_timestamp', 'exit_price', 'exit_reason',
    'pnl_absolute', 'pnl_pct', 'duration_minutes',
]


def _ensure_header():
    if not TRADES_CSV.exists():
        with open(TRADES_CSV, 'w', newline='') as f:
            csv.DictWriter(f, fieldnames=FIELDNAMES).writeheader()


def log_close(closed: dict, total_value: float):
    """Schrijft een complete trade-rij naar trades.csv nadat de positie gesloten is."""
    _ensure_header()

    entry_ts = closed.get('ts', '')
    exit_ts  = closed.get('exit_ts', datetime.now(timezone.utc).isoformat())

    try:
        dt_entry = datetime.fromisoformat(entry_ts.replace('Z', '+00:00'))
        dt_exit  = datetime.fromisoformat(exit_ts.replace('Z', '+00:00'))
        duration_minutes = round((dt_exit - dt_entry).total_seconds() / 60, 1)
    except Exception:
        duration_minutes = 0

    pnl = closed.get('pnl', 0.0)
    pos_size = closed.get('pos_size', 0.0)
    pnl_pct  = pnl / pos_size * 100 if pos_size > 0 else 0.0

    row = {
        'trade_id':                 closed.get('trade_id', ''),
        'coin':                     closed.get('sym', ''),
        'entry_timestamp':          entry_ts,
        'entry_price':              closed.get('entry', 0.0),
        'regime':                   closed.get('regime', ''),
        'adx':                      closed.get('adx', 0.0),
        'rsi':                      closed.get('rsi', 0.0),
        'bb_width':                 closed.get('bb_width', 0.0),
        'bb_position':              closed.get('bb_position', 0.0),
        'ema_fast':                 closed.get('ema_fast', 0.0),
        'ema_slow':                 closed.get('ema_slow', 0.0),
        'news_sentiment_score':     closed.get('news_sentiment', 0.0),
        'reddit_sentiment_score':   closed.get('reddit_sentiment', 0.0),
        'fear_greed_index':         closed.get('fear_greed', 50),
        'kelly_fraction_used':      closed.get('kelly_fraction_used', 0.0),
        'position_size_pct':        round(pos_size / total_value * 100, 4) if total_value > 0 else 0.0,
        'stop_loss_pct':            closed.get('sl_pct', 0.0),
        'take_profit_pct':          closed.get('tp_pct', 0.0),
        'stop_loss_multiplier_at_entry': closed.get('sl_multiplier', 1.0),
        'exit_timestamp':           exit_ts,
        'exit_price':               closed.get('exit', 0.0),
        'exit_reason':              closed.get('exit_reason', ''),
        'pnl_absolute':             round(pnl, 6),
        'pnl_pct':                  round(pnl_pct, 4),
        'duration_minutes':         duration_minutes,
    }

    with open(TRADES_CSV, 'a', newline='') as f:
        csv.DictWriter(f, fieldnames=FIELDNAMES).writerow(row)

    log.info(
        f'Trade gelogd: {row["coin"]} · {row["exit_reason"]} · '
        f'P&L €{pnl:+.2f} ({pnl_pct:+.2f}%) · {duration_minutes:.0f}min'
    )
