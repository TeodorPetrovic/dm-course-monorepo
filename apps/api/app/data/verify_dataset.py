"""Proverava Day 1 dataset: sha256 iz metadata.json, funnel brojeve iz lekcije i unutrašnju konzistentnost.

Konzistentnost: levak monotono opada (views >= carts >= purchases), suma udela po kategoriji = 1,
broj stavki u orders.csv == broj purchase događaja, stopa konverzije u realnom opsegu (0.5%–20%),
svaki purchase event_id postoji u events.csv.
"""
import json
import sys

import pandas as pd

from app.data.analytics import calculate_conversion_rate, calculate_funnel_counts, share_by_category
from app.data.generators import sha
from app.data.paths import day_data

EXPECTED_FUNNEL = {"views": 94220, "carts": 3159, "purchases": 1045, "sessions": 15361, "sessions_with_purchase": 893}


def main():
    meta = json.loads(day_data(1, "metadata.json").read_text())
    shas = (meta.get("manifest") or {}).get("sha256") or meta.get("sha256", {})
    ok = True

    def rep(name, cond, info=""):
        nonlocal ok
        print(f"{name}: {'OK' if cond else 'MISMATCH'}{(' ' + info) if info else ''}"); ok &= bool(cond)

    for f, h in shas.items():
        p = day_data(1, f)
        rep(f, p.exists() and sha(p) == h)
    ev = pd.read_csv(day_data(1, "events.csv")); od = pd.read_csv(day_data(1, "orders.csv"))
    pr = pd.read_csv(day_data(1, "products.csv"))
    f = calculate_funnel_counts(ev)
    for k, v in EXPECTED_FUNNEL.items():
        rep(f"funnel {k}", f[k] == v, f"{f[k]} (očekivano {v})")
    rep("levak monotono opada", f["views"] >= f["carts"] >= f["purchases"])
    sh = share_by_category(ev, pr, "view")
    total = float(sum(sh.values()) if isinstance(sh, dict) else pd.DataFrame(sh)["share"].sum())
    rep("suma udela po kategoriji = 1 (±0.001, udeli zaokruženi na 4 dec.)", abs(total - 1) < 1e-3, f"{total:.4f}")
    rep("stavke porudžbina == purchase događaji", len(od) == f["purchases"], f"{len(od)} vs {f['purchases']}")
    rep("purchase event_id postoje", set(od["event_id"]) <= set(ev.loc[ev.event_type == "purchase", "event_id"]))
    cr = calculate_conversion_rate(ev)
    rep("konverzija u realnom opsegu (0.5%–20%)", 0.005 <= cr <= 0.20, f"{cr:.4f}")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
