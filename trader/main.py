"""
AutoTrader Fase 1 — Data-engine + Paper Trading Bot
Draait 24/7 op Railway.app. Paper mode standaard.
"""

import asyncio, logging, uuid
from datetime import datetime, timezone

import aiohttp

from trader.config import SCAN_INTERVAL, TOP_N_COINS, LIVE_TRADING, START_BALANCE
from trader.sources import (
    binance_client, coingecko_client, cryptopanic_client,
    reddit_client, feargreed_client,
)
from trader.analysis.technical   import compute_indicators
from trader.analysis.regime_detector import detect_regime
from trader.analysis.sentiment   import combine_sentiment
from trader.strategy.signal_generator import generate_signal
from trader.strategy.position_sizing  import calc_kelly
from trader.strategy.risk_manager     import calc_sl_tp
from trader.engine import portfolio as port_mod
from trader.engine import adaptive_params as adapt_mod
from trader.engine import trade_logger, executor
from trader.sources.cryptopanic_client import clear_cache as cp_clear

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
    handlers=[logging.StreamHandler()],
)
log = logging.getLogger('autotrader')


async def scan_cycle(session: aiohttp.ClientSession, portfolio: dict, params: dict):
    log.info('── Scan gestart ────────────────────────────────────')

    # 1. Globale databronnen parallel ophalen
    gecko_coins, fear_greed = await asyncio.gather(
        coingecko_client.fetch_top_coins(session),
        feargreed_client.fetch(session),
    )
    if not gecko_coins:
        log.warning('Geen CoinGecko data — cyclus overgeslagen')
        return

    log.info(f'Fear & Greed: {fear_greed} · {len(gecko_coins)} coins geladen')
    cp_clear()  # CryptoPanic-cache leegmaken voor nieuwe cyclus

    coins = list(gecko_coins.items())[:TOP_N_COINS]
    sl_mul = params['sl_multiplier']
    total_val = port_mod.total_value(portfolio)
    kelly_size = calc_kelly(portfolio, 'all')  # globale Kelly als fallback

    results = []

    # 2. Scan in batches van 10
    for i in range(0, len(coins), 10):
        batch = coins[i:i + 10]
        tasks = [
            asyncio.gather(
                binance_client.fetch_klines(session, sym),
                cryptopanic_client.fetch_sentiment(session, sym),
                reddit_client.fetch_sentiment(session, sym),
                return_exceptions=True,
            )
            for sym, _ in batch
        ]
        batch_results = await asyncio.gather(*tasks)

        for j, (sym, coin_data) in enumerate(batch):
            br = batch_results[j]
            if isinstance(br, Exception):
                continue
            candles, news_sent, reddit_sent = br
            if isinstance(candles, Exception) or len(candles) < 30:
                continue
            if isinstance(news_sent, Exception):
                news_sent = 0.0
            if isinstance(reddit_sent, Exception):
                reddit_sent = 0.0

            sentiment = combine_sentiment(news_sent, reddit_sent, fear_greed)
            indicators = compute_indicators(candles)
            regime     = detect_regime(indicators)
            signal     = generate_signal(indicators, regime, sentiment)
            eur_price  = coin_data.get('current_price', indicators['price'])

            results.append({
                'sym':            sym,
                'pair':           sym + 'EUR',
                'eur_price':      eur_price,
                'sentiment':      sentiment,
                'news_sentiment': news_sent,
                'reddit_sentiment': reddit_sent,
                'indicators':     indicators,
                'regime':         regime,
                'signal':         signal,
                'fear_greed':     fear_greed,
            })

    results.sort(key=lambda r: r['signal']['score'], reverse=True)
    if results:
        best = results[0]
        log.info(
            f'Scan klaar: {len(results)} coins · '
            f'beste: {best["sym"]} ({best["signal"]["score"]:+.3f}) · '
            f'regime: {best["regime"]}'
        )

    # 3. SL/TP checken met actuele EUR-prijzen
    price_map = {r['sym']: r['eur_price'] for r in results}
    closed_now = port_mod.check_sl_tp(portfolio, price_map)

    for closed in closed_now:
        trade_logger.log_close(closed, total_val)
        params = adapt_mod.maybe_update(params, portfolio)

    # 4. Trades uitvoeren op BUY-signalen
    for r in results:
        sym   = r['sym']
        pair  = r['pair']
        price = r['eur_price']
        sig   = r['signal']
        ind   = r['indicators']

        if not price or price <= 0:
            continue
        if sig['signal'] != 'BUY':
            continue

        already_open = any(p['pair'] == pair for p in portfolio['positions'])
        pos_val      = next((p['pos_size'] for p in portfolio['positions'] if p['pair'] == pair), 0)
        pos_pct      = pos_val / total_val if total_val > 0 else 0

        regime = r['regime']
        kelly  = calc_kelly(portfolio, regime)
        kelly_pct = kelly / total_val if total_val > 0 else 0

        if pos_pct >= kelly_pct:
            continue   # positie al groot genoeg voor Kelly

        free_pct   = portfolio['balance'] / (total_val or 1)
        size_boost = 0.5 if already_open else 1.0
        size       = min(portfolio['balance'] * 0.95, kelly * (1 + free_pct) * size_boost)
        if size < 1:
            continue

        sl_tp  = calc_sl_tp(ind, sl_mul)
        sl_pct = sl_tp['sl_pct']
        tp_pct = sl_tp['tp_pct']
        qty    = size / price

        pos = {
            'trade_id':     str(uuid.uuid4()),
            'sym':          sym,
            'pair':         pair,
            'entry':        price,
            'qty':          qty,
            'pos_size':     size,
            'sl':           round(price * (1 - sl_pct / 100), 8),
            'tp':           round(price * (1 + tp_pct / 100), 8),
            'sl_pct':       sl_pct,
            'tp_pct':       tp_pct,
            'sl_multiplier': sl_mul,
            'score':        sig['score'],
            'regime':       regime,
            'adx':          ind['adx'],
            'rsi':          ind['rsi'],
            'bb_width':     ind['bb_width'],
            'bb_position':  ind['bb_position'],
            'ema_fast':     ind['ema_fast'],
            'ema_slow':     ind['ema_slow'],
            'news_sentiment':    r['news_sentiment'],
            'reddit_sentiment':  r['reddit_sentiment'],
            'fear_greed':   fear_greed,
            'kelly_fraction_used': kelly / total_val if total_val > 0 else 0,
            'ts':           datetime.now(timezone.utc).isoformat(),
        }

        executor.open_trade(portfolio, pos)

    # 5. Status
    total_after  = port_mod.total_value(portfolio)
    pnl          = total_after - portfolio['start']
    pnl_pct      = pnl / portfolio['start'] * 100
    log.info(
        f'Status: €{total_after:.0f} · P&L €{pnl:+.0f} ({pnl_pct:+.1f}%) · '
        f'{len(portfolio["positions"])} posities open · SL-mul {sl_mul:.3f}'
    )


async def main():
    mode = 'LIVE (Kraken)' if LIVE_TRADING else 'PAPER'
    log.info(f'AutoTrader Fase 1 gestart · modus: {mode} · scan elke {SCAN_INTERVAL}s')

    portfolio = port_mod.load()
    params    = adapt_mod.load()

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await scan_cycle(session, portfolio, params)
            except Exception as e:
                log.error(f'Scan fout: {e}', exc_info=True)
            log.info(f'Volgende scan over {SCAN_INTERVAL}s')
            await asyncio.sleep(SCAN_INTERVAL)


if __name__ == '__main__':
    asyncio.run(main())
