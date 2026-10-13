"""Generiše seed.sql za lokalnu bazu iz Day 1 CSV-ova (katalog + SEO + opcioni uzorak događaja).

python seed.py [--events N]   (N = poslednjih N događaja iz Day 1 events.csv; 0 = bez; podrazumevano 5000)
"""
import argparse
import json
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1] / "course"
D1 = ROOT / "Day 1" / "data"


def q(v):
    if v is None or (isinstance(v, float) and pd.isna(v)) or v is pd.NA:
        return "NULL"
    if isinstance(v, (int, float)):
        return str(v)
    return "'" + str(v).replace("\\", "\\\\").replace("'", "''") + "'"


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--events", type=int, default=5000); a = ap.parse_args()
    cats = pd.read_csv(D1 / "categories.csv"); prods = pd.read_csv(D1 / "products.csv")
    cname = dict(zip(cats.category_id, cats.name))
    out = ["SET NAMES utf8mb4;", "SET FOREIGN_KEY_CHECKS=0;"]
    out.append("INSERT INTO category (category_id,name,slug,img_url) VALUES " + ",".join(
        f"({r.category_id},{q(r.name)},{q(r.slug)},{q('/images/categories/' + r.slug + '.jpg')})" for r in cats.itertuples()) + ";")
    seo_rows, prod_rows = [], []
    for r in prods.itertuples():
        title = f"{r.name} | {cname[r.category_id]}"[:60]
        desc = f"Kupite {r.name}. {r.description}"[:155]
        kw = json.dumps([r.name.split(" ")[0].lower(), cname[r.category_id].lower(), "online shop"])
        seo_rows.append(f"({r.product_id},{q(title)},{q(desc)},{q(kw)})")
        prod_rows.append(f"({r.product_id},{q(r.name)},{q(r.description)},{q(r.img_url)},{q(r.slug)},{r.category_id},{r.price},{r.product_id})")
    out.append("INSERT INTO seo (seo_id,title,description,key_words) VALUES " + ",".join(seo_rows) + ";")
    out.append("INSERT INTO product (product_id,name,description,img_url,slug,category_id,price,seo_id) VALUES " + ",".join(prod_rows) + ";")
    if a.events:
        ev = pd.read_csv(D1 / "events.csv").tail(a.events)
        cols = ["event_id", "event_type", "user_id", "user_session", "product_id", "category_id", "price", "quantity",
                "source", "timestamp", "recommendation_source", "recommendation_position"]
        for i in range(0, len(ev), 1000):
            chunk = ev.iloc[i:i + 1000]
            vals = []
            for r in chunk[cols].itertuples(index=False):
                vals.append("(" + ",".join(q(int(x)) if isinstance(x, float) and not pd.isna(x) and c in ("product_id", "category_id", "recommendation_position")
                                          else q(x) for x, c in zip(r, cols)) + ")")
            out.append(f"INSERT INTO event (`{'`,`'.join(cols)}`) VALUES " + ",".join(vals) + ";")
    out.append("SET FOREIGN_KEY_CHECKS=1;")
    p = Path(__file__).with_name("seed.sql"); p.write_text("\n".join(out) + "\n")
    print(f"seed.sql: {len(cats)} kategorija, {len(prods)} proizvoda, {a.events} događaja")


if __name__ == "__main__":
    main()
