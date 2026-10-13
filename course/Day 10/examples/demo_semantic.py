"""Demo: semantic search i embedding preporuke (Day 10).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 10/examples/demo_semantic.py"

Prikazuje:
  1) **embedding store** — učitavanje iz ``Day 10/data/embeddings.npz``
     (n_products, dim, embedder);
  2) **semantičku pretragu** — ``semantic_search`` na poznatim upitima
     (npr. „wireless earbuds for travel" -> Headphones iako nema zajedničkih reči);
  3) **embedding preporuke** — ``recommendations_for_product`` (najbliži susedi,
     bez targeta);
  4) **cold-start fallback** — proizvod bez embeddinga -> popularity
     (``fallback_reason="no_embedding"``, NIKAD tihi []);
  5) **embedding vs content preporuke** — poređenje sa Day 5 TF-IDF content
     recs-ima (preklapanje i razlika);
  6) **keyword vs TFIDF vs embedding** — summary iz ``Day 10/data/comparison.csv``
     (gde koji pristup „vara").
"""

import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.recommenders.content import build_tfidf_matrix, recommend_similar_products
from app.services.semantic import SemanticService

DEMO_QUERIES = [
    "wireless earbuds for travel",
    "a book to read before bed",
    "home cooking essentials",
]
DEMO_PRODUCT = 22  # Jacket (fashion)


def _names(results) -> str:
    if hasattr(results, "to_dict"):
        results = results.to_dict("records")
    return ", ".join(r["name"] for r in list(results)[:3])


def main() -> None:
    print("=== Day 10 — Semantic Search and Embedding-Based Recommendations ===\n")
    svc = SemanticService()

    # --- 1) Embedding store ------------------------------------------------ #
    res = svc.semantic_search("smartphone", limit=1)
    store = res["store"]
    print(f"[1] Embedding store: n_products={store['n_products']}  "
          f"dim={store['dim']}  embedder={res['embedder']}")
    print()

    # --- 2) Semantička pretraga -------------------------------------------- #
    print("[2] Semantička pretraga (upit bez zajedničkih reči -> semantički hit):")
    for q in DEMO_QUERIES:
        r = svc.semantic_search(q, limit=3)
        status = "SEMANTIC" if r["method"] == "semantic" else "FALLBACK"
        print(f"    {q!r:38s} [{status}] {_names(r['results'])}")
    print()

    # --- 3) Embedding preporuke -------------------------------------------- #
    print(f"[3] Embedding preporuke za proizvod {DEMO_PRODUCT} "
          f"({svc.products.loc[svc.products['product_id'] == DEMO_PRODUCT, 'name'].iloc[0]}):")
    recs = svc.recommendations_for_product(DEMO_PRODUCT, limit=3)
    for r in recs["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<18} score={r['score']:.4f}")
    print()

    # --- 4) Cold-start fallback -------------------------------------------- #
    print("[4] Cold-start fallback (proizvod bez embeddinga '99999'):")
    cs = svc.recommendations_for_product(99999, limit=3)
    print(f"    method={cs['method']} fallback={cs['fallback']} "
          f"reason={cs['fallback_reason']}  -> popularity top-3: "
          f"{_names(cs['recommendations'])}  (NIKAD tihi [])")
    print()

    # --- 5) Embedding vs content preporuke ----------------------------------- #
    print(f"[5] Embedding recs vs Day 5 content recs za proizvod {DEMO_PRODUCT}:")
    products: pd.DataFrame = svc.products
    tfidf, _vectorizer = build_tfidf_matrix(products, min_df=2)  # iste postavke kao Day 5 servis
    content = recommend_similar_products(products, DEMO_PRODUCT, tfidf, limit=5)
    content_recs = content["recommendations"]  # lista dict-ova (envelope)
    sem_ids = {r["product_id"] for r in recs["recommendations"]}
    cont_ids = {r["product_id"] for r in content_recs}
    print(f"    semantic: {_names(recs['recommendations'])}")
    print(f"    content : {_names(content_recs)}")
    print(f"    overlap : {len(sem_ids & cont_ids)} od {len(sem_ids | cont_ids)} "
          f"(slično u drugom prostoru, ne identično)")
    print()

    # --- 6) Keyword vs TFIDF vs embedding ----------------------------------- #
    print("[6] Keyword vs TFIDF vs embedding (Day 10/data/comparison.csv):")
    try:
        comp = svc.comparison()
        seen = set()
        for row in comp["comparison"]:
            if row["query"] in seen:
                continue
            seen.add(row["query"])
            kw = next((c for c in comp["comparison"] if c["query"] == row["query"] and c["method"] == "keyword"), None)
            tf = next((c for c in comp["comparison"] if c["query"] == row["query"] and c["method"] == "tfidf"), None)
            em = next((c for c in comp["comparison"] if c["query"] == row["query"] and c["method"] == "embedding"), None)
            print(f"    {row['query']!r}")
            print(f"        keyword  = {kw['name'] if kw else '—'}")
            print(f"        tfidf    = {tf['name'] if tf else '—'}")
            print(f"        embedding= {em['name'] if em else '—'}")
        print("    (vidi gde embedding pobeđuje, a gde keyword 'vara' — npr. 'bed'.)")
    except FileNotFoundError as exc:
        print(f"    {exc}")
    print()

    print("API: GET /search/semantic?q=… · GET /recommendations/semantic/{product_id}")
    print("Lab: Day 10/lab — brute-force NN petlja pišeš SAM.")


if __name__ == "__main__":
    main()
