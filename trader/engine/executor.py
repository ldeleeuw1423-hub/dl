import logging
from datetime import datetime, timezone
from trader.config import LIVE_TRADING, KRAKEN_KEY
from trader.engine import portfolio as port_mod

log = logging.getLogger('autotrader.executor')


def open_trade(portfolio: dict, pos: dict) -> bool:
    """
    Uniforme interface voor paper én live trading.
    pos moet alle entry-features bevatten (zie trade_logger.FIELDNAMES).
    """
    if LIVE_TRADING:
        if not KRAKEN_KEY:
            log.error('LIVE_TRADING=true maar KRAKEN_API_KEY niet gezet — trade GEBLOKKEERD')
            return False
        return _live_buy(pos)
    else:
        return _paper_buy(portfolio, pos)


def _paper_buy(portfolio: dict, pos: dict) -> bool:
    if portfolio['balance'] < pos['pos_size']:
        log.debug(f'Onvoldoende saldo voor {pos["pair"]} (nodig €{pos["pos_size"]:.0f})')
        return False
    port_mod.open_position(portfolio, pos)
    log.info(
        f'KOOP {pos["pair"]} @ €{pos["entry"]:.6f} · €{pos["pos_size"]:.0f} · '
        f'SL {pos["sl_pct"]:.2f}% · TP {pos["tp_pct"]:.2f}% · score {pos["score"]:.3f}'
    )
    return True


def _live_buy(pos: dict) -> bool:
    # Fase 3: Kraken API via ccxt
    # import ccxt
    # exchange = ccxt.kraken({'apiKey': KRAKEN_KEY, 'secret': KRAKEN_SECRET})
    # order = exchange.create_market_buy_order(pos['pair'], pos['qty'])
    log.info(f'[LIVE — nog niet geïmplementeerd] Koop {pos["pair"]} @ €{pos["entry"]:.6f}')
    return False
