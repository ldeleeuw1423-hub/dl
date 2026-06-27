import asyncio, logging
import aiohttp
from trader.config import CANDLE_INTERVAL, CANDLE_LIMIT

log = logging.getLogger('autotrader.binance')

async def fetch_klines(session: aiohttp.ClientSession, symbol: str) -> list:
    """100 candles per coin van Binance (USDT pair)."""
    try:
        url = 'https://api.binance.com/api/v3/klines'
        params = {'symbol': symbol + 'USDT', 'interval': CANDLE_INTERVAL, 'limit': CANDLE_LIMIT}
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=10)) as r:
            data = await r.json()
            if not isinstance(data, list):
                return []
            return [
                {
                    'time':  int(c[0]) // 1000,
                    'open':  float(c[1]),
                    'high':  float(c[2]),
                    'low':   float(c[3]),
                    'close': float(c[4]),
                    'vol':   float(c[5]),
                }
                for c in data
            ]
    except Exception as e:
        log.debug(f'Binance klines {symbol}: {e}')
        return []

async def fetch_prices(session: aiohttp.ClientSession, symbols: list) -> dict:
    """Live USDT prijzen voor een lijst symbolen."""
    try:
        import json as _json
        syms = _json.dumps([s + 'USDT' for s in symbols])
        url = f'https://api.binance.com/api/v3/ticker/price?symbols={syms}'
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=8)) as r:
            data = await r.json()
            return {d['symbol'].replace('USDT', ''): float(d['price']) for d in data}
    except Exception as e:
        log.debug(f'Binance prices: {e}')
        return {}
