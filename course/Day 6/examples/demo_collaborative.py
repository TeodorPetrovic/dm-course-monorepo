"""Demo: collaborative recommender (implicit feedback, Day 6).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 6/examples/demo_collaborative.py"

Prikazuje:
  1) interaction matricu (sesije × proizvodi, sparsity) iz ``Day 6/data``;
  2) **collaborative preporuke** (item-item kosinusna sličnost) za nekoliko
     proizvoda;
  3) **cold-start fallback** — nov proizvod (bez interakcija) -> popularity
     baseline sa ``fallback=true``, ne tihi ``[]``;
  4) **existing-heuristic-vs-CF poređenje** (session co-occurrence vs item-item)
     — overlap tabela koju README citira;
  5) **weight-sensitivity** — iste težine su pretpostavke: promena šeme težina
     menja izlaz.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.collaborative import CollaborativeRecommenderService

EXAMPLES = [1, 2, 23, 144, 232]


def _ids(envelope: dict) -> str:
    return ",".join(str(r["product_id"]) for r in envelope["recommendations"])


def main() -> None:
    print("=== Day 6 — Collaborative Recommender (implicit feedback) ===\n")
    svc = CollaborativeRecommenderService()

    stats = svc.matrix_stats
    print(f"[0] Interaction matrica: {stats['sessions']} sesija × "
          f"{stats['products']} proizvoda, nnz={stats['nnz']}, "
          f"density={stats['density']:.5f} (sparse — nema dense blowup-a)")
    print()

    # --- 1) Collaborative preporuke ---------------------------------------- #
    print("[1] Collaborative preporuke (item-item kosinusna sličnost):")
    pid = 1
    res = svc.collaborative_recommendations(pid, 5)
    print(f"    /recommendations/collaborative/{pid}: method={res['method']} "
          f"fallback={res['fallback']}")
    for r in res["recommendations"]:
        print(f"      {r['product_id']:>3}  {r['name']:<20} score={r['score']:.4f}")
    ids = [r["product_id"] for r in res["recommendations"]]
    print(f"    target {pid} isključen: {pid not in ids}")
    print()

    # --- 2) Cold-start fallback -------------------------------------------- #
    print("[2] Cold-start fallback (nov proizvod bez interakcija):")
    cs = svc.collaborative_recommendations(99999, 5)
    print(f"    /recommendations/collaborative/99999: method={cs['method']} "
          f"fallback={cs['fallback']} reason={cs['fallback_reason']}")
    print(f"    -> popularity baseline, {cs['returned']} preporuka (NIKAD tihi [])")
    print()

    # --- 3) Existing heuristic vs CF ---------------------------------------- #
    print("[3] Existing heuristic vs CF (top-5, overlap):")
    print(f"    {'target':>6} {'heuristic top-5':<30} {'CF top-5':<30} {'overlap':<12}")
    for pid in EXAMPLES:
        comp = svc.collaborative_comparison(pid, 5)
        h = _ids(comp["heuristic"])
        c = _ids(comp["collaborative"])
        ov = ",".join(str(x) for x in comp["overlap"]) or "—"
        print(f"    {pid:>6} {h:<30} {c:<30} {ov:<12}")
    print()

    # --- 4) Weight sensitivity ---------------------------------------------- #
    print("[4] Weight sensitivity (težine = pretpostavke, ne istine):")
    ws = svc.weight_sensitivity(1, limit=5)
    print(f"    target 1, limit={ws['limit']}:")
    print(f"    {'weight set':<32} {'top-5':<24} {'overlap w/ default':>18}")
    for row in ws["rows"]:
        top = ",".join(str(x) for x in row["top_ids"])
        ov = row["overlap_with_default"]
        print(f"    {row['name']:<32} {top:<24} {ov!s:>18}")
    print()
    print("Promena težina menja izlaz -> težine nisu istina o kvalitetu, "
          "nego hipoteza.")
    print("Vizualizacija: python3 \"Day 6/examples/visualize_weights.py\"")


if __name__ == "__main__":
    main()
