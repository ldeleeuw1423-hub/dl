def calc_sl_tp(indicators: dict, sl_multiplier: float) -> dict:
    """
    SL en TP uit BB-breedte en historische TP-ratio.
    Geen vaste percentages — alles uit marktdata.

    sl_pct  = bb_width * 100 * sl_multiplier
    tp_pct  = sl_pct * tp_ratio  (ratio uit candle-data berekend)
    """
    bb_width   = indicators.get('bb_width', 0.05)
    tp_ratio   = indicators.get('tp_ratio', 2.5)

    sl_pct = (bb_width * 100) * sl_multiplier
    sl_pct = max(sl_pct, 0.5)   # absolute minimum: half procent (marktspread)

    tp_pct = sl_pct * tp_ratio

    return {
        'sl_pct': round(sl_pct, 4),
        'tp_pct': round(tp_pct, 4),
    }
