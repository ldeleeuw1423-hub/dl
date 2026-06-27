import logging
import aiohttp

log = logging.getLogger('autotrader.reddit')

# Geen praw nodig — Reddit JSON API werkt zonder credentials.
# Sentiment = upvote_ratio als proxy voor bullish/bearish stemming.
# (0.5 baseline → normaliseer naar -1..+1)

async def fetch_sentiment(session: aiohttp.ClientSession, symbol: str) -> float:
    """Reddit r/cryptocurrency sentiment -1..+1 via publieke JSON API."""
    try:
        url = 'https://www.reddit.com/r/cryptocurrency/search.json'
        params = {'q': symbol, 'sort': 'new', 'limit': 25, 't': 'day'}
        headers = {'User-Agent': 'autotrader-bot/1.0'}
        async with session.get(
            url, params=params, headers=headers,
            timeout=aiohttp.ClientTimeout(total=6),
        ) as r:
            data = await r.json()
            posts = data.get('data', {}).get('children', [])
            if not posts:
                return 0.0
            ratios = [
                p['data']['upvote_ratio']
                for p in posts
                if 'upvote_ratio' in p.get('data', {})
            ]
            if not ratios:
                return 0.0
            avg = sum(ratios) / len(ratios)
            return (avg - 0.5) * 2   # 0.5 baseline → -1..+1
    except Exception as e:
        log.debug(f'Reddit {symbol}: {e}')
        return 0.0
