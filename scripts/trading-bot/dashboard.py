"""
Trading Bot Dashboard — lokale webpagina met live trade-overzicht.
Start: python dashboard.py  →  opent automatisch in browser op http://localhost:5050
Leest logs/trades.csv elke 10 seconden.
"""
import csv
import os
import threading
import webbrowser
from pathlib import Path

from flask import Flask, jsonify, render_template_string

app = Flask(__name__)

TRADES_CSV = Path(__file__).parent / "logs" / "trades.csv"

HTML = """
<!DOCTYPE html>
<html lang="nl">
<head>
  <meta charset="UTF-8">
  <title>Trading Dashboard</title>
  <meta http-equiv="refresh" content="10">
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: 'Segoe UI', sans-serif; background: #0f0f1a; color: #e0e0e0; padding: 24px; }
    h1   { color: #00d4aa; margin-bottom: 20px; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 28px; }
    .card {
      background: #1a1a2e; border-radius: 10px; padding: 18px;
      border-left: 4px solid #00d4aa;
    }
    .card .label { font-size: 12px; color: #888; text-transform: uppercase; letter-spacing: 1px; }
    .card .value { font-size: 28px; font-weight: 700; margin-top: 6px; }
    .pos { color: #00d4aa; }
    .neg { color: #ff5555; }
    .neutral { color: #e0e0e0; }
    table { width: 100%; border-collapse: collapse; background: #1a1a2e; border-radius: 10px; overflow: hidden; }
    th { background: #252540; padding: 12px 16px; text-align: left; font-size: 12px;
         text-transform: uppercase; color: #888; letter-spacing: 1px; }
    td { padding: 11px 16px; border-top: 1px solid #252540; font-size: 14px; }
    tr:hover td { background: #252540; }
    .badge {
      display: inline-block; padding: 2px 10px; border-radius: 20px;
      font-size: 12px; font-weight: 600;
    }
    .buy  { background: #003322; color: #00d4aa; }
    .sell { background: #2a0022; color: #ff5555; }
    .refresh { float: right; font-size: 12px; color: #555; margin-top: 4px; }
  </style>
</head>
<body>
  <h1>Trading Dashboard <span class="refresh">auto-refresh 10s</span></h1>

  <div class="grid">
    <div class="card">
      <div class="label">Totaal P&L</div>
      <div class="value {{ 'pos' if summary.total_pnl >= 0 else 'neg' }}">
        {{ '+' if summary.total_pnl >= 0 else '' }}{{ "%.2f"|format(summary.total_pnl) }} USDT
      </div>
    </div>
    <div class="card">
      <div class="label">Aantal trades</div>
      <div class="value neutral">{{ summary.total_trades }}</div>
    </div>
    <div class="card">
      <div class="label">Win rate</div>
      <div class="value {{ 'pos' if summary.win_rate >= 50 else 'neg' }}">
        {{ "%.1f"|format(summary.win_rate) }}%
      </div>
    </div>
    <div class="card">
      <div class="label">Actieve pairs</div>
      <div class="value neutral">{{ summary.active_pairs | join(', ') or '—' }}</div>
    </div>
  </div>

  <table>
    <thead>
      <tr>
        <th>Tijdstip</th>
        <th>Pair</th>
        <th>Side</th>
        <th>Prijs</th>
        <th>Qty</th>
        <th>P&L (USDT)</th>
        <th>Status</th>
      </tr>
    </thead>
    <tbody>
      {% for t in trades %}
      <tr>
        <td>{{ t.get('timestamp', '—') }}</td>
        <td>{{ t.get('pair', '—') }}</td>
        <td><span class="badge {{ t.get('side', '').lower() }}">{{ t.get('side', '—') }}</span></td>
        <td>{{ t.get('price', '—') }}</td>
        <td>{{ t.get('qty', '—') }}</td>
        <td class="{{ 'pos' if (t.get('pnl') or 0)|float >= 0 else 'neg' }}">
          {{ '+' if (t.get('pnl') or 0)|float >= 0 else '' }}{{ "%.4f"|format((t.get('pnl') or 0)|float) }}
        </td>
        <td>{{ t.get('status', '—') }}</td>
      </tr>
      {% else %}
      <tr><td colspan="7" style="text-align:center;color:#555;padding:30px">Geen trades gevonden in logs/trades.csv</td></tr>
      {% endfor %}
    </tbody>
  </table>
</body>
</html>
"""


def load_trades():
    if not TRADES_CSV.exists():
        return []
    with open(TRADES_CSV, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    return list(reversed(rows))  # nieuwste bovenaan


def compute_summary(trades):
    total_pnl = sum((float(t.get("pnl") or 0) for t in trades), 0.0)
    winning = sum(1 for t in trades if float(t.get("pnl") or 0) > 0)
    win_rate = (winning / len(trades) * 100) if trades else 0.0
    # "actief" = laatste trade per pair nog geen SELL gesloten — simpele benadering
    seen = {}
    for t in reversed(trades):
        seen[t.get("pair", "")] = t.get("side", "").upper()
    active = [p for p, side in seen.items() if side == "BUY"]
    return {
        "total_pnl": total_pnl,
        "total_trades": len(trades),
        "win_rate": win_rate,
        "active_pairs": active,
    }


@app.route("/")
def index():
    trades = load_trades()
    summary = compute_summary(trades)
    return render_template_string(HTML, trades=trades, summary=summary)


@app.route("/api/trades")
def api_trades():
    trades = load_trades()
    return jsonify({"trades": trades, "summary": compute_summary(trades)})


def open_browser():
    webbrowser.open("http://localhost:5050")


if __name__ == "__main__":
    # Open browser na 1 seconde zodat Flask op tijd start
    threading.Timer(1.0, open_browser).start()
    print("Dashboard: http://localhost:5050  (Ctrl+C om te stoppen)")
    app.run(host="127.0.0.1", port=5050, debug=False)
