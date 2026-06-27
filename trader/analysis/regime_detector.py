from trader.config import ADX_TREND_THRESHOLD


def detect_regime(indicators: dict) -> str:
    """
    trending  — ADX > 25, volg de trend (EMA-richting)
    sideways  — ADX <= 25, mean-reversion op Bollinger Bands
    """
    adx = indicators.get('adx', 0.0)
    return 'trending' if adx > ADX_TREND_THRESHOLD else 'sideways'
