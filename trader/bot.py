"""
AutoTrader — 24/7 crypto trading bot
Paper mode standaard. Zet LIVE_TRADING=true + Kraken API keys voor echte trades.

Databronnen:
- Binance: kaarsen (technische analyse) + live prijzen
- CoinGecko: EUR-prijzen, top-50 op volume
- CryptoPanic: nieuws-sentiment per coin
- Reddit: sociale sentiment r/cryptocurrency
- Fear & Greed: marktpsychologie (alternative.me)
"""

import asyncio, json, os, math, logging, time
from datetime import datetime, timezone
from pathlib import Path
import aiohttp

# ── Configuratie ──────────────────────────────────────────────
LIVE_TRADING    = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
KRAKEN_KEY      = os.getenv('KRAKEN_API_KEY', '')
KRAKEN_SECRET   = os.getenv('KRAKEN_API_SECRET', '')
CRYPTOPANIC_KEY = os.getenv('CRYPTOPANIC_KEY', '')   # gratis op cryptopanic.com
SCAN_INTERVAL   = int(os.getenv('SCAN_INTERVAL', '300'))  # seconden tussen scans
START_BALANCE   = float(os.getenv('START_BALANCE', '10000'))
DATA_DIR        = Path(os.getenv('DATA_DIR', 'trader/data'))

STABLE_COINS = {'USDT','BUSD','USDC','DAI','TUSD','USDP','FRAX','LUSD','STETH','WBTC','WETH'}

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    handlers=[logging.StreamHandler()]
)
log = logging.getLogger('autotrader')

# ── Portfolio opslag ──────────────────────────────────────────
def load_portfolio():
    f = DATA_DIR / 'portfolio.json'
    if f.exists():
        return json.loads(f.read_text())
    return {'balance': START_BALANCE, 'start': START_BALANCE,
            'realized_pnl': 0.0, 'positions': [], 'closed': []}

def save_portfolio(p):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / 'portfolio.json').write_text(json.dumps(p, indent=2))

def log_trade(entry: dict):
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    with open(DATA_DIR / 'trades.log', 'a') as f:
        f.write(json.dumps(entry) + '\n')

# ── Data ophalen ──────────────────────────────────────────────
async def fetch_gecko(session) -> dict:
    """EUR-prijzen top-50 van CoinGecko"""
    try:
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        params = {'vs_currency':'eur','order':'volume_desc','per_page':50,'page':1}
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
            data = await r.json()
            return {c['symbol'].upper(): c for c in data if isinstance(data, list)}
    except Exception as e:
        log.warning(f'CoinGecko fout: {e}')
        return {}

async def fetch_binance_klines(session, symbol: str, interval='4h', limit=100) -> list:
    """4u-kaarsen van Binance"""
    try:
        url = 'https://api.binance.com/api/v3/klines'
        params = {'symbol': symbol, 'interval': interval, 'limit': limit}
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
            data = await r.json()
            if not isinstance(data, list): return []
            return [{'time':int(c[0])//1000,'open':float(c[1]),'high':float(c[2]),
                     'low':float(c[3]),'close':float(c[4]),'vol':float(c[5])} for c in data]
    except Exception as e:
        log.debug(f'Binance klines {symbol}: {e}')
        return []

async def fetch_binance_price(session, symbols: list) -> dict:
    """Live Binance USDT prijzen"""
    try:
        syms = json.dumps([s+'USDT' for s in symbols])
        url = f'https://api.binance.com/api/v3/ticker/price?symbols={syms}'
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
            data = await r.json()
            return {d['symbol'].replace('USDT',''): float(d['price']) for d in data}
    except:
        return {}

async def fetch_fear_greed(session) -> int:
    """Fear & Greed index 0–100"""
    try:
        async with session.get('https://api.alternative.me/fng/?limit=1',
                               timeout=aiohttp.ClientTimeout(total=5)) as r:
            d = await r.json()
            return int(d['data'][0]['value'])
    except:
        return 50

async def fetch_cryptopanic(session, symbol: str) -> float:
    """Nieuws-sentiment -1 tot +1 via CryptoPanic"""
    try:
        params = {'currencies': symbol, 'kind': 'news', 'filter': 'hot'}
        if CRYPTOPANIC_KEY:
            params['auth_token'] = CRYPTOPANIC_KEY
        async with session.get('https://cryptopanic.com/api/v1/posts/',
                               params=params, timeout=aiohttp.ClientTimeout(total=6)) as r:
            data = await r.json()
            posts = data.get('results', [])
            if not posts: return 0.0
            scores = []
            for p in posts:
                v = p.get('votes', {})
                bull = v.get('bullish', 0) + v.get('positive', 0)
                bear = v.get('bearish', 0) + v.get('negative', 0)
                tot = bull + bear
                if tot > 0: scores.append((bull - bear) / tot)
            return sum(scores) / len(scores) if scores else 0.0
    except:
        return 0.0

async def fetch_reddit_sentiment(session, symbol: str) -> float:
    """Reddit sentiment uit r/cryptocurrency — geen API key nodig"""
    try:
        url = 'https://www.reddit.com/r/cryptocurrency/search.json'
        params = {'q': symbol, 'sort': 'new', 'limit': 25, 't': 'day'}
        headers = {'User-Agent': 'autotrader-bot/1.0'}
        async with session.get(url, params=params, headers=headers,
                               timeout=aiohttp.ClientTimeout(total=6)) as r:
            data = await r.json()
            posts = data.get('data', {}).get('children', [])
            if not posts: return 0.0
            ratios = [p['data']['upvote_ratio'] for p in posts if 'upvote_ratio' in p['data']]
            if not ratios: return 0.0
            return (sum(ratios) / len(ratios) - 0.5) * 2  # 0.5 baseline → -1..+1
    except:
        return 0.0

# ── Technische analyse ────────────────────────────────────────
def calc_rsi(closes: list, period=14) -> float:
    if len(closes) < period + 1: return 50.0
    gains = [max(closes[i]-closes[i-1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i-1]-closes[i], 0) for i in range(1, len(closes))]
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    return 100 - 100 / (1 + ag/al) if al > 0 else 100.0

def calc_ema(closes: list, period: int) -> float:
    if not closes: return 0.0
    k = 2 / (period + 1)
    ema = closes[0]
    for c in closes[1:]: ema = c * k + ema * (1 - k)
    return ema

def calc_bb(closes: list, period=20) -> dict:
    if len(closes) < period: return {'pct': 0.5, 'width': 0.0}
    sl = closes[-period:]
    mid = sum(sl) / period
    std = math.sqrt(sum((x-mid)**2 for x in sl) / period) * 2
    last = closes[-1]
    pct = (last - (mid - std)) / (std * 2) if std > 0 else 0.5
    return {'pct': round(max(0, min(1, pct)), 3), 'width': round(std * 2 / mid if mid > 0 else 0, 4)}

def calc_tp_ratio(candles: list) -> float:
    """Natuurlijke TP-ratio uit historische kaarsen"""
    up_sum = down_sum = n = 0
    for c in candles:
        up = (c['high'] - c['open']) / c['open'] if c['open'] > 0 else 0
        dn = (c['open'] - c['low'])  / c['open'] if c['open'] > 0 else 0
        if up > 0 and dn > 0:
            up_sum += up; down_sum += dn; n += 1
    return round(up_sum / down_sum, 2) if n >= 10 and down_sum > 0 else 3.0

def compute_score(candles: list, sentiment: float = 0.0) -> dict:
    """
    Score -100..+100 op basis van:
    - Regime-detectie: trending vs ranging (uit BB-breedte historie)
    - Ranging → koop laag in bereik (mean reversion)
    - Trending → volg de trend (momentum)
    - Sentiment van internet weegt 30% mee
    """
    if len(candles) < 30:
        return {'score': 0, 'tp_ratio': 3.0, 'regime': 0.5, 'price_pos': 0.5, 'price': 0}

    closes = [c['close'] for c in candles]
    highs  = [c['high']  for c in candles]
    lows   = [c['low']   for c in candles]
    cur    = closes[-1]

    rsi  = calc_rsi(closes)
    ema9 = calc_ema(closes, 9)
    ema21 = calc_ema(closes, 21)
    ema50 = calc_ema(closes, 50)
    bb   = calc_bb(closes)
    vol5  = sum(c['vol'] for c in candles[-5:]) / 5
    vol15 = sum(c['vol'] for c in candles[-15:-5]) / 10
    vol_ratio = vol5 / vol15 if vol15 > 0 else 1.0

    # Regime: BB-breedte nu vs eigen historisch gemiddelde
    bb_widths = []
    for i in range(20, len(closes)):
        sl = closes[i-20:i]
        m = sum(sl) / 20
        std = math.sqrt(sum((x-m)**2 for x in sl) / 20) * 2
        if m > 0: bb_widths.append(std / m)
    avg_bbw = sum(bb_widths) / len(bb_widths) if bb_widths else bb['width']
    regime = min(1.0, bb['width'] / avg_bbw) if avg_bbw > 0 else 0.5

    # Prijs-positie in recent bereik
    low20  = min(lows[-20:])
    high20 = max(highs[-20:])
    price_pos = (cur - low20) / (high20 - low20) if high20 > low20 else 0.5

    # Mean-reversion score (koop laag)
    mr_score = ((1 - price_pos * 2) + (50 - rsi) / 50 + (0.5 - bb['pct']) * 2) / 3

    # Momentum score (volg de trend)
    ema_s  = 1.0 if ema9>ema21>ema50 else -1.0 if ema9<ema21<ema50 else 0.5 if ema9>ema21 else -0.5
    macd_h = (calc_ema(closes, 12) - calc_ema(closes, 26))
    macd_s = min(macd_h / cur * 500, 1.0) if macd_h > 0 else max(macd_h / cur * 500, -1.0)
    vol_s  = min((vol_ratio - 1) / max(vol_ratio - 1, 0.01) * 0.5, 0.5) if vol_ratio > 1 else -0.2
    mom_score = (ema_s + macd_s + vol_s) / 2.5

    # Combineer: regime bepaalt welke strategie zwaarder weegt
    technical = (1 - regime) * mr_score + regime * mom_score

    # Sentiment van internet weegt 30% mee
    composite = technical * 0.70 + sentiment * 0.30
    score = round(composite * 100)

    return {
        'score': score, 'price': cur, 'rsi': round(rsi, 1),
        'regime': round(regime, 2), 'price_pos': round(price_pos, 2),
        'bb': bb, 'tp_ratio': calc_tp_ratio(candles)
    }

# ── Kelly positiegrootte ──────────────────────────────────────
def calc_kelly(portfolio: dict) -> float:
    recent = portfolio['closed'][-20:]
    base = portfolio['balance'] * 0.25
    if len(recent) < 5:
        return min(base, portfolio['balance'] * 0.95)
    wins   = [t['pnl'] for t in recent if t['pnl'] > 0]
    losses = [abs(t['pnl']) for t in recent if t['pnl'] < 0]
    win_rate = len(wins) / len(recent)
    avg_win  = sum(wins) / len(wins) if wins else 1
    avg_loss = sum(losses) / len(losses) if losses else 1
    odds = avg_win / avg_loss if avg_loss > 0 else 1
    kelly = max(0, (win_rate * odds - (1 - win_rate)) / odds) * 0.75
    return min(portfolio['balance'] * 0.95, max(base, portfolio['balance'] * kelly))

# ── SL multiplier uit trade-data ──────────────────────────────
def calc_sl_multiplier(portfolio: dict) -> float:
    closed = portfolio['closed']
    if len(closed) < 5: return 1.0
    sl_rate = sum(1 for t in closed if 'Stop-Loss' in (t.get('reason') or '')) / len(closed)
    if sl_rate > 0.60: return 1.8
    if sl_rate > 0.45: return 1.4
    return 1.0

# ── Handelen ─────────────────────────────────────────────────
def execute_trade(portfolio: dict, pair: str, price: float, size: float,
                  sl_pct: float, tp_pct: float, score: int, reason: str):
    """Voegt een positie toe aan portfolio (paper of live)"""
    if LIVE_TRADING:
        log.info(f'[LIVE] Koop {pair} @ €{price:.4f} voor €{size:.0f} — nog niet geïmplementeerd')
        # TODO: Kraken API order plaatsen
        return False

    qty = size / price
    portfolio['balance'] -= size
    portfolio['positions'].append({
        'pair': pair, 'entry': price, 'qty': qty, 'pos_size': size,
        'sl': round(price * (1 - sl_pct / 100), 8),
        'tp': round(price * (1 + tp_pct / 100), 8),
        'atr_pct': sl_pct, 'score': score,
        'ts': datetime.now(timezone.utc).isoformat()
    })
    entry = {'ts': datetime.now(timezone.utc).isoformat(), 'action': 'KOOP',
             'pair': pair, 'price': price, 'qty': round(qty, 8),
             'value': round(size, 2), 'score': score, 'reason': reason}
    log_trade(entry)
    log.info(f'KOOP {pair} @ €{price:.4f} · €{size:.0f} · SL {sl_pct:.1f}% · TP {tp_pct:.1f}% · score {score}')
    return True

def check_sl_tp(portfolio: dict, prices: dict):
    """Controleer stop-loss en take-profit voor alle open posities"""
    changed = False
    for i in range(len(portfolio['positions']) - 1, -1, -1):
        pos = portfolio['positions'][i]
        sym = pos['pair'].replace('EUR', '')
        cur = prices.get(sym, pos['entry'])
        if cur <= 0: continue

        # Trailing stop
        if cur > pos['entry'] and pos.get('atr_pct'):
            trail_sl = round(cur * (1 - pos['atr_pct'] / 100), 8)
            if trail_sl > pos['sl']:
                portfolio['positions'][i]['sl'] = trail_sl
                changed = True

        hit_price, reason = None, ''
        if pos['sl'] and cur <= pos['sl']: hit_price, reason = pos['sl'], 'Stop-Loss geraakt'
        if pos['tp'] and cur >= pos['tp']: hit_price, reason = pos['tp'], 'Take-Profit bereikt'

        if hit_price:
            pnl = (hit_price - pos['entry']) * pos['qty']
            portfolio['balance'] += pos['pos_size'] + pnl
            portfolio['realized_pnl'] = portfolio.get('realized_pnl', 0) + pnl
            portfolio['closed'].append({
                'pair': pos['pair'], 'entry': pos['entry'], 'exit': hit_price,
                'qty': pos['qty'], 'pnl': round(pnl, 4),
                'reason': reason, 'ts': datetime.now(timezone.utc).isoformat()
            })
            log_trade({'ts': datetime.now(timezone.utc).isoformat(), 'action': reason,
                       'pair': pos['pair'], 'price': hit_price, 'pnl': round(pnl, 4)})
            log.info(f'{reason}: {pos["pair"]} @ €{hit_price:.4f} · P&L €{pnl:+.2f}')
            portfolio['positions'].pop(i)
            changed = True
    return changed

# ── Hoofdscan ────────────────────────────────────────────────
async def run_scan(session):
    log.info('── Scan gestart ──────────────────────────────────')

    # 1. Haal alle databronnen op
    gecko_coins, fear_greed = await asyncio.gather(
        fetch_gecko(session), fetch_fear_greed(session)
    )
    if not gecko_coins:
        log.warning('Geen CoinGecko data — scan overgeslagen')
        return

    log.info(f'Fear & Greed: {fear_greed} · {len(gecko_coins)} coins geladen')

    # 2. Filter stablecoins, neem top-45
    coins_to_scan = [
        {'sym': sym, 'coin': coin}
        for sym, coin in gecko_coins.items()
        if sym not in STABLE_COINS
    ][:45]

    portfolio = load_portfolio()
    kelly = calc_kelly(portfolio)
    sl_mul = calc_sl_multiplier(portfolio)
    total_val = portfolio['balance'] + sum(p['pos_size'] for p in portfolio['positions'])
    kelly_pct = kelly / total_val if total_val > 0 else 0.25

    log.info(f'Portfolio: €{total_val:.0f} · vrij €{portfolio["balance"]:.0f} · Kelly €{kelly:.0f}')

    # 3. Fear & Greed als globale sentimentmodifier
    fg_sentiment = (fear_greed - 50) / 50  # -1 (extreme fear) tot +1 (extreme greed)

    results = []

    # 4. Scan parallel in batches van 10
    for i in range(0, len(coins_to_scan), 10):
        batch = coins_to_scan[i:i+10]
        tasks = []
        for item in batch:
            sym = item['sym']
            tasks.append(asyncio.gather(
                fetch_binance_klines(session, sym + 'USDT'),
                fetch_cryptopanic(session, sym),
                fetch_reddit_sentiment(session, sym),
                return_exceptions=True
            ))

        batch_results = await asyncio.gather(*tasks)

        for j, item in enumerate(batch):
            sym = item['sym']
            coin = item['coin']
            br = batch_results[j]
            if isinstance(br, Exception): continue

            candles, cp_sentiment, reddit_sentiment = br
            if isinstance(candles, Exception) or len(candles) < 30: continue

            # Combineer sentimentbronnen
            sentiment = (
                (cp_sentiment if not isinstance(cp_sentiment, Exception) else 0) * 0.40 +
                (reddit_sentiment if not isinstance(reddit_sentiment, Exception) else 0) * 0.30 +
                fg_sentiment * 0.30
            )

            res = compute_score(candles, sentiment)
            res['sym'] = sym
            res['pair'] = sym + 'EUR'
            res['eur_price'] = coin.get('current_price', res['price'])
            results.append(res)

    results.sort(key=lambda r: r['score'], reverse=True)
    log.info(f'Scan klaar: {len(results)} coins · beste: {results[0]["sym"]} ({results[0]["score"]}) · slechtste: {results[-1]["sym"]} ({results[-1]["score"]}) ' if results else 'Geen resultaten')

    # 5. SL/TP checken met live prijzen
    price_map = {r['sym']: r['eur_price'] for r in results}
    changed = check_sl_tp(portfolio, price_map)

    # 6. Handelen op basis van scores
    for res in results:
        sym, pair = res['sym'], res['pair']
        price = res['eur_price']
        if not price or price <= 0: continue

        already_open = any(p['pair'] == pair for p in portfolio['positions'])
        pos_val = next((p['pos_size'] for p in portfolio['positions'] if p['pair'] == pair), 0)
        pos_pct = pos_val / total_val if total_val > 0 else 0

        # Kopen: score positief en positie past nog binnen Kelly-max
        if res['score'] > 0 and pos_pct < kelly_pct and portfolio['balance'] > 1:
            free_pct = portfolio['balance'] / (total_val or 1)
            free_boost = 1 + free_pct
            size = min(portfolio['balance'] * 0.95, kelly * free_boost * (0.5 if already_open else 1))
            if size < 1: continue

            bb_w = res['bb']['width']
            sl_pct = (bb_w * 100 if bb_w > 0 else 5) * sl_mul
            tp_pct = sl_pct * res['tp_ratio']

            reason = (f"Score {res['score']} · regime {res['regime']} · "
                      f"prijs {res['price_pos']*100:.0f}% van bereik · "
                      f"sentiment {res.get('sentiment', 0):.2f}")

            if execute_trade(portfolio, pair, price, size, sl_pct, tp_pct, res['score'], reason):
                changed = True

    # 7. Opslaan
    if changed or True:  # altijd opslaan voor dashboard
        save_portfolio(portfolio)

    # 8. Status loggen
    total_after = portfolio['balance'] + sum(p['pos_size'] for p in portfolio['positions'])
    pnl_total = total_after - portfolio['start']
    log.info(f'Status: totaal €{total_after:.0f} · P&L {pnl_total:+.0f} ({pnl_total/portfolio["start"]*100:+.1f}%) · {len(portfolio["positions"])} posities open')

# ── Hoofdloop ────────────────────────────────────────────────
async def main():
    mode = 'LIVE (Kraken)' if LIVE_TRADING else 'PAPER'
    log.info(f'AutoTrader gestart · modus: {mode} · scan elke {SCAN_INTERVAL}s')
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                await run_scan(session)
            except Exception as e:
                log.error(f'Scan fout: {e}', exc_info=True)
            log.info(f'Volgende scan over {SCAN_INTERVAL}s')
            await asyncio.sleep(SCAN_INTERVAL)

if __name__ == '__main__':
    asyncio.run(main())
