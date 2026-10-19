"""
Rebalance the Alpaca paper book to the latest portfolio selection.

Dry run (default): prints the sell / buy / hold list and does nothing.
    python rebalance.py
Send the orders:
    python rebalance.py --execute

Unlike start_live_trading.run_pipeline_once(), this passes the CURRENT positions (as weights)
to the signal generator, so names that dropped out of the selection get SELL signals.
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, "src")
sys.path.insert(0, "trading/paper_trading")

from dotenv import load_dotenv  # noqa: E402

load_dotenv()

from signals.signal_generator import QualityMomentumSignalGenerator  # noqa: E402
from alpaca_connector import AlpacaPaperTrader  # noqa: E402


def main() -> int:
    execute = "--execute" in sys.argv
    trader = AlpacaPaperTrader()
    positions = trader.get_current_positions()
    account = trader.get_account_info()
    # Portfolio value from the account; if that call fails, fall back to positions plus cash from the raw API.
    value = float(account.get("portfolio_value", 0) or 0)
    if not value:
        raw = trader.api.get_account()
        value = float(raw.portfolio_value)
    if not value:
        raise SystemExit("Could not read the portfolio value; not generating signals.")
    current = {t: float(p.get("market_value", 0)) / value for t, p in positions.items()}

    gen = QualityMomentumSignalGenerator()
    portfolio = gen.load_latest_portfolio()
    targets = gen.calculate_target_weights(portfolio) if portfolio is not None else {}
    if not targets:
        raise SystemExit("No portfolio selection found; run the research scripts first.")

    # Build the signals here rather than with generate_signals()+validate_signals(): those drop
    # every name that is not in the new selection (quality score 0), so nothing would ever be sold,
    # and they treat a 2% new position as a HOLD because it sits under the 2% drift threshold.
    signals = {}
    for t in sorted(set(current) | set(targets)):
        cur, tgt = current.get(t, 0.0), min(targets.get(t, 0.0), gen.max_position_size)
        diff = tgt - cur
        if tgt == 0 and cur > 0:
            action = "SELL"
        elif cur == 0 and tgt >= 0.005:
            action = "BUY"
        elif diff > 0.005:
            action = "INCREASE"
        elif diff < -0.005:
            action = "REDUCE"
        else:
            action = "HOLD"
        quality = gen._get_quality_score(t, portfolio)
        if action in ("BUY", "INCREASE") and quality < 0.3:  # the repo's own quality floor for new money
            action = "HOLD" if cur > 0 else "SKIP"
        signals[t] = {"action": action, "current_weight": cur, "target_weight": tgt, "weight_change": diff,
                      "signal_strength": min(1.0, abs(diff) / gen.max_position_size), "quality_score": quality,
                      "momentum_score": gen._get_momentum_score(t, portfolio), "timestamp": datetime.now().isoformat()}
    signals = {t: s for t, s in signals.items() if s["action"] != "SKIP"}
    by = lambda a: sorted(t for t, s in signals.items() if s["action"] == a)  # noqa: E731
    print(f"Portfolio value ${value:,.0f}; {len(positions)} positions now; {len(signals)} signals")
    for action in ("SELL", "REDUCE", "HOLD", "INCREASE", "BUY"):
        names = by(action)
        if names:
            print(f"{action:8s} {len(names):3d}: {' '.join(names)}")

    os.makedirs("data/signals", exist_ok=True)
    out = f"data/signals/rebalance_signals_{datetime.now():%Y-%m-%d_%H%M%S}.json"
    with open(out, "w") as f:
        json.dump(signals, f, indent=2)
    print(f"Signals saved to {out}")

    if not execute:
        print("Dry run. Re-run with --execute to send the orders to the paper account.")
        return 0
    results = trader.execute_signals({t: s for t, s in signals.items() if s["action"] != "HOLD"})
    placed = sum(1 for r in results.values() if "placed" in r)
    print(f"Orders placed: {placed}/{len(results)}")
    for t, r in sorted(results.items()):
        if "placed" not in r:
            print(f"  {t}: {r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
