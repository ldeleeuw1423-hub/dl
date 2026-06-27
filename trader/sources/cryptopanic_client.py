import logging
import aiohttp
from trader.config import CRYPTOPANIC_KEY

log = logging.getLogger('autotrader.cryptopanic')

_cache: dict = {}

async def fetch_sentiment(session: aiohttp.ClientSession, symbol: str) -> float:
    """Nieuws-sentiment -1..+1 via CryptoPanic. Cached binnen de cyclus."""
    if symbol in _cache:
        return _cache[symbol]
    try:
        params = {'currencies': symbol, 'kind': 'news', 'filter': 'hot'}
        if CRYPTOPANIC_KEY:
            params['auth_token'] = CRYPTOPANIC_KEY
        async with session.get(
            'https://cryptopanic.com/api/v1/posts/',
            params=params,
            timeout=aiohttp.ClientTimeout(total=6),
        ) as r:
            data = await r.json()
            posts = data.get('results', [])
            if not posts:
                _cache[symbol] = 0.0
                return 0.0
            scores = []
            for p in posts:
                v = p.get('votes', {})
                bull = v.get('bullish', 0) + v.get('positive', 0)
                bear = v.get('bearish', 0) + v.get('negative', 0)
                tot = bull + bear
                if tot > 0:
                    scores.append((bull - bear) / tot)
            result = sum(scores) / len(scores) if scores else 0.0
            _cache[symbol] = result
            return result
    except Exception as e:
        log.debug(f'CryptoPanic {symbol}: {e}')
        return 0.0

def clear_cache():
    _cache.clear()
