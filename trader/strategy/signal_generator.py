def generate_signal(indicators: dict, regime: str, sentiment: float) -> dict:
    """
    BUY / SELL / HOLD per coin.

    Trending: volg EMA-richting, sentiment weegt mee.
    Sideways: mean-reversion op BB-positie en RSI.

    Retourneert {'signal': str, 'score': float, 'reason': str}
    Score is ruw, -1..+1 voor interne ranking.
    """
    rsi      = indicators['rsi']
    ema_fast = indicators['ema_fast']
    ema_slow = indicators['ema_slow']
    bb_pct   = indicators['bb_position']
    vol_ratio = indicators['vol_ratio']

    if regime == 'trending':
        # Momentum: EMA-richting + volume-bevestiging
        ema_score = 1.0 if ema_fast > ema_slow else -1.0
        vol_score = min((vol_ratio - 1) / max(vol_ratio - 1, 0.01), 1.0) if vol_ratio > 1 else -0.2
        tech_score = (ema_score * 0.7 + vol_score * 0.3)
        reason = f'trending · EMA {ema_score:+.1f} · vol {vol_ratio:.2f}x'

    else:  # sideways
        # Mean-reversion: koop laag (BB-onderkant, oververkocht RSI)
        bb_mr  = (0.5 - bb_pct) * 2          # +1 aan onderkant, -1 aan bovenkant
        rsi_mr = (50 - rsi) / 50              # +1 bij RSI=0, -1 bij RSI=100
        tech_score = (bb_mr * 0.6 + rsi_mr * 0.4)
        reason = f'sideways · BB {bb_pct:.2f} · RSI {rsi:.1f}'

    # Technisch 70%, sentiment 30%
    composite = tech_score * 0.70 + sentiment * 0.30

    if composite > 0.15:
        signal = 'BUY'
    elif composite < -0.15:
        signal = 'SELL'
    else:
        signal = 'HOLD'

    return {
        'signal':    signal,
        'score':     round(composite, 4),
        'reason':    reason + f' · sent {sentiment:+.2f}',
    }
