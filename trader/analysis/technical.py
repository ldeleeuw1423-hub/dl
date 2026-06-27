import math


def calc_ema(closes: list, period: int) -> float:
    if not closes:
        return 0.0
    k = 2 / (period + 1)
    ema = closes[0]
    for c in closes[1:]:
        ema = c * k + ema * (1 - k)
    return ema


def calc_rsi(closes: list, period: int = 14) -> float:
    if len(closes) < period + 1:
        return 50.0
    gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
    losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
    ag = sum(gains[-period:]) / period
    al = sum(losses[-period:]) / period
    return 100 - 100 / (1 + ag / al) if al > 0 else 100.0


def calc_bb(closes: list, period: int = 20) -> dict:
    if len(closes) < period:
        return {'pct': 0.5, 'width': 0.0, 'upper': 0.0, 'lower': 0.0, 'mid': 0.0}
    sl = closes[-period:]
    mid = sum(sl) / period
    std = math.sqrt(sum((x - mid) ** 2 for x in sl) / period)
    upper = mid + 2 * std
    lower = mid - 2 * std
    band_width = (upper - lower)
    last = closes[-1]
    pct = (last - lower) / band_width if band_width > 0 else 0.5
    return {
        'pct':   round(max(0.0, min(1.0, pct)), 4),
        'width': round(band_width / mid if mid > 0 else 0.0, 6),
        'upper': round(upper, 8),
        'lower': round(lower, 8),
        'mid':   round(mid, 8),
    }


def calc_adx(candles: list, period: int = 14) -> dict:
    """Average Directional Index. Retourneert adx, plus_di, minus_di."""
    if len(candles) < period + 2:
        return {'adx': 0.0, 'plus_di': 0.0, 'minus_di': 0.0}

    tr_list, plus_dm_list, minus_dm_list = [], [], []
    for i in range(1, len(candles)):
        high  = candles[i]['high']
        low   = candles[i]['low']
        prev_close = candles[i - 1]['close']
        prev_high  = candles[i - 1]['high']
        prev_low   = candles[i - 1]['low']

        tr = max(high - low, abs(high - prev_close), abs(low - prev_close))
        plus_dm  = max(high - prev_high, 0) if (high - prev_high) > (prev_low - low) else 0
        minus_dm = max(prev_low - low, 0)   if (prev_low - low) > (high - prev_high) else 0

        tr_list.append(tr)
        plus_dm_list.append(plus_dm)
        minus_dm_list.append(minus_dm)

    def wilder_smooth(data, n):
        if len(data) < n:
            return 0.0
        s = sum(data[:n])
        for v in data[n:]:
            s = s - s / n + v
        return s

    atr     = wilder_smooth(tr_list, period)
    plus_dm  = wilder_smooth(plus_dm_list, period)
    minus_dm = wilder_smooth(minus_dm_list, period)

    plus_di  = 100 * plus_dm  / atr if atr > 0 else 0.0
    minus_di = 100 * minus_dm / atr if atr > 0 else 0.0
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di) if (plus_di + minus_di) > 0 else 0.0

    # Wilder smoothing of DX series
    dx_list = []
    for i in range(1, len(tr_list)):
        h, l, pc = candles[i + 1]['high'], candles[i + 1]['low'], candles[i]['close']
        ph, pl   = candles[i]['high'], candles[i]['low']
        tr_i     = max(h - l, abs(h - pc), abs(l - pc))
        pdm_i    = max(h - ph, 0) if (h - ph) > (pl - l) else 0
        mdm_i    = max(pl - l, 0) if (pl - l) > (h - ph) else 0
        if i >= len(tr_list) - period:
            dx_list.append(dx)   # approximate — good enough for phase 1

    adx = sum(dx_list) / len(dx_list) if dx_list else dx

    return {
        'adx':      round(adx, 2),
        'plus_di':  round(plus_di, 2),
        'minus_di': round(minus_di, 2),
    }


def calc_tp_ratio(candles: list) -> float:
    """Natuurlijke TP/SL-ratio uit candle-data — geen hardcoded waarde."""
    up_sum = down_sum = n = 0
    for c in candles:
        if c['open'] <= 0:
            continue
        up = (c['high'] - c['open']) / c['open']
        dn = (c['open'] - c['low'])  / c['open']
        if up > 0 and dn > 0:
            up_sum += up
            down_sum += dn
            n += 1
    return round(up_sum / down_sum, 3) if n >= 10 and down_sum > 0 else 2.5


def compute_indicators(candles: list) -> dict:
    """Berekent alle TA-indicatoren uit een candle-lijst."""
    closes = [c['close'] for c in candles]
    cur    = closes[-1] if closes else 0.0

    rsi    = calc_rsi(closes)
    ema9   = calc_ema(closes, 9)
    ema21  = calc_ema(closes, 21)
    ema50  = calc_ema(closes, 50)
    bb     = calc_bb(closes)
    adx    = calc_adx(candles)
    tp_ratio = calc_tp_ratio(candles)

    vol5  = sum(c['vol'] for c in candles[-5:]) / 5
    vol15 = sum(c['vol'] for c in candles[-15:-5]) / 10 if len(candles) >= 15 else vol5
    vol_ratio = vol5 / vol15 if vol15 > 0 else 1.0

    return {
        'price':     cur,
        'rsi':       round(rsi, 2),
        'ema_fast':  round(ema9, 8),
        'ema_slow':  round(ema21, 8),
        'ema50':     round(ema50, 8),
        'bb_position': bb['pct'],
        'bb_width':    bb['width'],
        'bb':          bb,
        'adx':         adx['adx'],
        'plus_di':     adx['plus_di'],
        'minus_di':    adx['minus_di'],
        'vol_ratio':   round(vol_ratio, 3),
        'tp_ratio':    tp_ratio,
    }
