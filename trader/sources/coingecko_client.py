import logging
import aiohttp
from trader.config import TOP_N_COINS, STABLE_COINS

log = logging.getLogger('autotrader.coingecko')

async def fetch_top_coins(session: aiohttp.ClientSession) -> dict:
    """EUR-prijzen van top-50 coins op volume. Retourneert {SYM: coin_dict}."""
    try:
        url = 'https://api.coingecko.com/api/v3/coins/markets'
        params = {
            'vs_currency': 'eur',
            'order': 'volume_desc',
            'per_page': 50,
            'page': 1,
        }
        async with session.get(url, params=params, timeout=aiohttp.ClientTimeout(total=12)) as r:
            data = await r.json()
            if not isinstance(data, list):
                return {}
            return {
                c['symbol'].upper(): c
                for c in data
                if isinstance(c, dict) and c.get('symbol', '').upper() not in STABLE_COINS
            }
    except Exception as e:
        log.warning(f'CoinGecko fout: {e}')
        return {}
