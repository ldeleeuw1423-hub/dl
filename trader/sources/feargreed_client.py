import logging
import aiohttp

log = logging.getLogger('autotrader.feargreed')

async def fetch(session: aiohttp.ClientSession) -> int:
    """Fear & Greed index 0–100 (alternative.me)."""
    try:
        async with session.get(
            'https://api.alternative.me/fng/?limit=1',
            timeout=aiohttp.ClientTimeout(total=5),
        ) as r:
            d = await r.json()
            return int(d['data'][0]['value'])
    except Exception as e:
        log.debug(f'Fear & Greed fout: {e}')
        return 50
