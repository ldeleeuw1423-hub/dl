import os
from pathlib import Path

LIVE_TRADING      = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
KRAKEN_KEY        = os.getenv('KRAKEN_API_KEY', '')
KRAKEN_SECRET     = os.getenv('KRAKEN_API_SECRET', '')
CRYPTOPANIC_KEY   = os.getenv('CRYPTOPANIC_KEY', '')
SCAN_INTERVAL     = int(os.getenv('SCAN_INTERVAL', '300'))
START_BALANCE     = float(os.getenv('START_BALANCE', '10000'))

BASE_DIR   = Path(__file__).parent
DATA_DIR   = BASE_DIR / 'data'
LOG_DIR    = BASE_DIR / 'logs'
TRADES_CSV = DATA_DIR / 'trades.csv'
PORTFOLIO_FILE  = DATA_DIR / 'portfolio.json'
ADAPTIVE_FILE   = DATA_DIR / 'adaptive_params.json'

DATA_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)

STABLE_COINS = {
    'USDT','BUSD','USDC','DAI','TUSD','USDP','FRAX','LUSD',
    'STETH','WBTC','WETH','USTC','USDD','GUSD',
}

CANDLE_INTERVAL = os.getenv('CANDLE_INTERVAL', '5m')
CANDLE_LIMIT    = int(os.getenv('CANDLE_LIMIT', '100'))
TOP_N_COINS     = int(os.getenv('TOP_N_COINS', '45'))

ADX_TREND_THRESHOLD = 25     # fase 2: ML vervangt dit
KELLY_LOOKBACK      = 30     # rolling window per regime
KELLY_FRACTION      = 0.5    # half-Kelly veiligheidsmarge
ADAPTIVE_WINDOW     = 10     # trades per aanpassingscyclus
ADAPTIVE_MAX_MUL    = 3.0
ADAPTIVE_MIN_MUL    = 1.0
