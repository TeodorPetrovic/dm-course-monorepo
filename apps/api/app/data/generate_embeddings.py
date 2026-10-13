"""Day 10 generator: embeddings.npz + embeddings.json + comparison.csv."""
from __future__ import annotations

import argparse
import json

import pandas as pd

from app.data.paths import day_data
from app.services.semantic import SemanticService

QUERIES = ["smartphone", "something to listen to music with", "a book to read before bed",
           "fitness and training gear", "home cooking essentials", "wireless earbuds for travel"]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--embedder", default="auto", help="auto | hash | st | st:<hf-model-name>")
    ap.add_argument("--out-dir", default=None)
    a = ap.parse_args(argv)
    out = day_data(10, "x").parent if a.out_dir is None else __import__("pathlib").Path(a.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    if a.embedder.startswith("st:"):
        from app.recommenders.embeddings import STEmbedder
        svc = SemanticService(store_path=out / "__none__.npz")
        svc._embedder = STEmbedder(a.embedder[3:])
        m = svc._embedder.encode(svc.products["product_text"].fillna(""))
        svc._store = {"matrix": m, "product_ids": [int(x) for x in svc.products["product_id"]],
                      "embedder_name": svc._embedder.name, "embedder_params": {}}
    else:
        svc = SemanticService(store_path=out / "__none__.npz", embedder=a.embedder)
    svc.save(out / "embeddings.npz")
    info = svc.store_info()
    (out / "embeddings.json").write_text(json.dumps({"dataset": "dm_semantic_v1", "embedder": {
        "name": info["embedder"], "params": svc._store["embedder_params"]}}, indent=2) + "\n")
    rows = svc.build_comparison(QUERIES, 3)
    pd.DataFrame(rows)[["query", "method", "rank", "product_id", "name", "category_id", "score"]].to_csv(
        out / "comparison.csv", index=False)
    print(f"embeddings: {info} · comparison rows: {len(rows)} -> {out}")


if __name__ == "__main__":
    main()
