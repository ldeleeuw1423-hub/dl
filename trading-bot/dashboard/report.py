"""Daily trading report: console summary + HTML file."""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import pytz

import config

logger = logging.getLogger(__name__)

AMSTERDAM = pytz.timezone("Europe/Amsterdam")
REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Trading Report – {date}</title>
<style>
  body {{ font-family: monospace; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }}
  h1 {{ color: #e94560; }} h2 {{ color: #16213e; background: #e94560; padding: 4px 8px; }}
  table {{ border-collapse: collapse; width: 100%; margin-bottom: 1.5rem; }}
  th {{ background: #16213e; color: #e94560; padding: 6px 12px; text-align: left; }}
  td {{ padding: 4px 12px; border-bottom: 1px solid #333; }}
  .pos {{ color: #4caf50; }} .neg {{ color: #f44336; }} .neu {{ color: #aaa; }}
</style>
</head>
<body>
<h1>Daily Trading Report — {date}</h1>
<p>Generated: {generated}</p>

<h2>Account Summary</h2>
<table>
  <tr><th>Metric</th><th>Value</th></tr>
  <tr><td>Equity</td><td>{equity}</td></tr>
  <tr><td>Balance</td><td>{balance}</td></tr>
  <tr><td>Daily P&amp;L</td><td class="{pnl_class}">{daily_pnl}</td></tr>
  <tr><td>Open positions</td><td>{open_positions}</td></tr>
</table>

<h2>Trades Today</h2>
{trades_table}

<h2>Sentiment Overview</h2>
{sentiment_table}

<h2>Open Positions</h2>
{positions_table}
</body>
</html>"""


def _pnl_class(pnl: float) -> str:
    if pnl > 0:
        return "pos"
    if pnl < 0:
        return "neg"
    return "neu"


def _trades_html(trades: list[dict]) -> str:
    if not trades:
        return "<p>No trades today.</p>"
    rows = "".join(
        f"<tr><td>{t.get('instrument','')}</td><td>{t.get('direction','')}</td>"
        f"<td>{t.get('units','')}</td><td>{t.get('entry_price','')}</td>"
        f"<td>{t.get('exit_price','')}</td>"
        f"<td class='{_pnl_class(float(t.get('pnl',0)))}'>{t.get('pnl','')}</td>"
        f"<td>{t.get('time','')}</td></tr>"
        for t in trades
    )
    return (
        "<table><tr><th>Instrument</th><th>Direction</th><th>Units</th>"
        "<th>Entry</th><th>Exit</th><th>P&L</th><th>Time</th></tr>"
        + rows + "</table>"
    )


def _sentiment_html(sentiments: dict[str, dict]) -> str:
    if not sentiments:
        return "<p>No sentiment data.</p>"
    rows = "".join(
        f"<tr><td>{instr}</td><td>{s.get('label','')}</td>"
        f"<td>{s.get('score', 0):.3f}</td><td>{s.get('count',0)}</td></tr>"
        for instr, s in sentiments.items()
    )
    return (
        "<table><tr><th>Instrument</th><th>Label</th><th>Score</th><th>Articles</th></tr>"
        + rows + "</table>"
    )


def _positions_html(positions: list[dict]) -> str:
    if not positions:
        return "<p>No open positions.</p>"
    rows = "".join(
        f"<tr><td>{p.get('instrument','')}</td><td>{p.get('long',{}).get('units','0')}</td>"
        f"<td>{p.get('short',{}).get('units','0')}</td>"
        f"<td>{p.get('unrealizedPL','0')}</td></tr>"
        for p in positions
    )
    return (
        "<table><tr><th>Instrument</th><th>Long Units</th><th>Short Units</th><th>Unrealized P&L</th></tr>"
        + rows + "</table>"
    )


def generate_report(
    account: dict,
    daily_pnl: float,
    trades_today: list[dict],
    sentiments: dict[str, dict],
    open_positions: list[dict],
) -> Path:
    """Generate console summary and HTML report. Returns path to HTML file."""
    now_ams = datetime.now(AMSTERDAM)
    date_str = now_ams.strftime("%Y-%m-%d")
    generated_str = now_ams.strftime("%Y-%m-%d %H:%M:%S %Z")

    equity  = float(account.get("NAV", account.get("balance", 0)))
    balance = float(account.get("balance", 0))

    # Console output
    print("\n" + "=" * 60)
    print(f" DAILY REPORT  {date_str}")
    print("=" * 60)
    print(f"  Equity     : {equity:,.2f}")
    print(f"  Balance    : {balance:,.2f}")
    print(f"  Daily P&L  : {daily_pnl:+,.2f}")
    print(f"  Open pos.  : {len(open_positions)}")
    print(f"  Trades     : {len(trades_today)}")
    print("-" * 60)
    for instr, s in sentiments.items():
        print(f"  {instr:<12} sentiment: {s.get('label','?'):>10}  score={s.get('score',0):.3f}")
    print("=" * 60 + "\n")

    # HTML
    html = _HTML_TEMPLATE.format(
        date=date_str,
        generated=generated_str,
        equity=f"{equity:,.2f}",
        balance=f"{balance:,.2f}",
        daily_pnl=f"{daily_pnl:+,.2f}",
        pnl_class=_pnl_class(daily_pnl),
        open_positions=len(open_positions),
        trades_table=_trades_html(trades_today),
        sentiment_table=_sentiment_html(sentiments),
        positions_table=_positions_html(open_positions),
    )

    report_path = REPORTS_DIR / f"report_{date_str}.html"
    report_path.write_text(html, encoding="utf-8")
    logger.info("Report written to %s", report_path)
    return report_path
