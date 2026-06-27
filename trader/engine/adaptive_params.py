import json, logging
from trader.config import (
    ADAPTIVE_FILE, ADAPTIVE_WINDOW, ADAPTIVE_MAX_MUL, ADAPTIVE_MIN_MUL, LOG_DIR
)

log = logging.getLogger('autotrader.adaptive')
_adapt_log = LOG_DIR / 'adaptive_changes.log'


def load() -> dict:
    if ADAPTIVE_FILE.exists():
        return json.loads(ADAPTIVE_FILE.read_text())
    return {'sl_multiplier': 1.0, 'trades_since_last_check': 0}


def save(params: dict):
    ADAPTIVE_FILE.write_text(json.dumps(params, indent=2))


def maybe_update(params: dict, portfolio: dict) -> dict:
    """
    Controleert na elke ADAPTIVE_WINDOW afgesloten trades of SL-multiplier
    bijgesteld moet worden.

    > 60% stopped-out → ruimer (×1.1)
    < 20% stopped-out én win-ratio > 55% → krapper (×0.95)
    """
    closed = portfolio.get('closed', [])
    params['trades_since_last_check'] = params.get('trades_since_last_check', 0) + 1

    if params['trades_since_last_check'] < ADAPTIVE_WINDOW:
        save(params)
        return params

    # Reset teller, evalueer laatste window
    params['trades_since_last_check'] = 0
    recent = closed[-ADAPTIVE_WINDOW:]
    if not recent:
        save(params)
        return params

    sl_hits  = sum(1 for t in recent if t.get('exit_reason') == 'stop_loss')
    wins     = sum(1 for t in recent if t.get('pnl', 0) > 0)
    sl_rate  = sl_hits / len(recent)
    win_rate = wins / len(recent)
    old_mul  = params['sl_multiplier']

    if sl_rate > 0.60:
        params['sl_multiplier'] = min(old_mul * 1.1, ADAPTIVE_MAX_MUL)
        _write_log(f'SL-rate {sl_rate:.0%} > 60% → multiplier {old_mul:.3f} → {params["sl_multiplier"]:.3f} (ruimer)')

    elif sl_rate < 0.20 and win_rate > 0.55:
        params['sl_multiplier'] = max(old_mul * 0.95, ADAPTIVE_MIN_MUL)
        _write_log(f'SL-rate {sl_rate:.0%} < 20% & win {win_rate:.0%} > 55% → multiplier {old_mul:.3f} → {params["sl_multiplier"]:.3f} (krapper)')

    save(params)
    return params


def _write_log(msg: str):
    from datetime import datetime, timezone
    line = f'{datetime.now(timezone.utc).isoformat()} {msg}\n'
    with open(_adapt_log, 'a') as f:
        f.write(line)
    log.info(f'Adaptieve aanpassing: {msg}')
