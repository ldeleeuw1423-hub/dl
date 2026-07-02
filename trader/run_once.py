"""Eenmalige scan-cyclus — aangeroepen door GitHub Actions elke 5 minuten."""
import asyncio
import aiohttp
from trader.engine import portfolio as port_mod, adaptive_params as adapt_mod
from trader.main import scan_cycle


async def main():
    portfolio = port_mod.load()
    params    = adapt_mod.load()
    async with aiohttp.ClientSession() as session:
        await scan_cycle(session, portfolio, params)


if __name__ == '__main__':
    asyncio.run(main())
