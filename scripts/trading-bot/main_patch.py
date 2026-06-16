"""
PATCH voor main.py — trade size logica.
Vervang jouw bestaande calculate_order_size() (of vergelijkbare functie) door onderstaande.

Zet dit bovenaan main.py als constanten:
"""

TRADE_SIZE_PCT = 0.001      # 0.1% van portfolio
MIN_ORDER_USDT = 15.0       # minimum 15 USDT per order


def calculate_order_size(portfolio_value: float, price: float) -> float:
    """
    Bereken order-grootte in base-asset.

    - Gebruik 0.1% van totale portfolio waarde als order-grootte in USDT.
    - Minimaal 15 USDT per order.
    - Geeft 0 terug als zelfs 15 USDT niet mogelijk is (te klein portfolio).
    """
    usdt_size = portfolio_value * TRADE_SIZE_PCT
    usdt_size = max(usdt_size, MIN_ORDER_USDT)

    if portfolio_value < MIN_ORDER_USDT:
        return 0.0  # niet genoeg saldo

    quantity = usdt_size / price
    return quantity


# ── Voorbeeld hoe je het aanroept in je trading loop ──────────────────────────
#
#   portfolio_usdt = get_portfolio_value()   # bijv. via exchange.fetch_balance()
#   qty = calculate_order_size(portfolio_usdt, current_price)
#   if qty > 0:
#       place_order(side="buy", quantity=qty, ...)
#
# ─────────────────────────────────────────────────────────────────────────────
