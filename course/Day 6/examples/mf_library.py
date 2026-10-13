"""MF extension: matrix factorization preko biblioteka (Day 6).

Toy SGD (``toy_sgd.py``) pokazuje mehanizam iz osnova; ovo je **library-level
ekstenzija** — isti koncept kroz dve biblioteke:

  1. ``implicit`` — **Alternating Least Squares (ALS)** za implicitni feedback
     (naš slučaj: interaction matrica sesije × proizvodi). Faktorizuje matricu i
     nudi ``similar_items`` iz naučenih faktora proizvoda.
  2. ``surprise`` — **SVD** za eksplicitne ocene (toy primer 1–5) i predikcija
     nepoznate ocene.

Obe biblioteke su **opcione** (Day 6 ekstenzija): instaliraj ih sa
``pip install scikit-surprise implicit`` (dodate su u ``dm-ml/requirements.txt``).
Ako nisu instalirane, skripta prijavljuje jasnu poruku i izlazi — ne pada.

Pokretanje (koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 6/examples/mf_library.py"
"""

from __future__ import annotations

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import numpy as np

from app.recommenders.collaborative import InteractionMatrix

DEFAULT_INTERACTIONS = (
    Path(__file__).resolve().parents[2] / "Day 6" / "data" / "interactions.csv"
)
TARGET_PRODUCT = 1


def load_user_item_matrix(path: Path = DEFAULT_INTERACTIONS):
    """Long-format interaction matrica -> ``(user_item_matrix, products)``.

    ALS iz ``implicit`` očekuje **users × items** CSR matricu (red = korisnik/
    sesija, kolona = proizvod) — to je tačno ``inter.matrix``. Vraća i
    ``products`` listu za mapiranje indeksa kolona.
    """
    inter = InteractionMatrix.from_long_csv(path)
    return inter.matrix, inter.products


def implicit_als_similar_items(n_similar: int = 5) -> None:
    """ALS (implicit feedback) -> top-N sličnih proizvoda za target."""
    try:
        import implicit
    except ImportError:
        print("implicit nije instaliran — pokreni: "
              "dm-ml/.venv/bin/pip install implicit")
        return

    print("[1] implicit ALS (implicit feedback) — na Day 6 interaction matrici")
    user_item, products = load_user_item_matrix()
    print(f"    matrica: {user_item.shape[0]} sesija × {user_item.shape[1]} proizvoda")

    model = implicit.als.AlternatingLeastSquares(
        factors=20, iterations=15, regularization=0.1, random_state=42
    )
    model.fit(user_item, show_progress=False)

    if TARGET_PRODUCT not in products:
        print(f"    target {TARGET_PRODUCT} nije u matrici")
        return
    item_idx = products.index(TARGET_PRODUCT)
    ids, scores = model.similar_items(item_idx, N=n_similar + 1)
    print(f"    top-{n_similar} sličnih proizvoda za {TARGET_PRODUCT} "
          f"(iz naučenih faktora):")
    for idx, score in zip(ids[1:], scores[1:]):  # ids[0] je sam proizvod
        print(f"      {products[idx]:>3}  similarity={score:.4f}")
    print()


def surprise_svd_explicit_toy() -> None:
    """SVD (explicit ratings) na toy primeru -> predikcija nepoznate ocene."""
    try:
        from surprise import Dataset, Reader, SVD
    except ImportError:
        print("scikit-surprise nije instaliran — pokreni: "
              "dm-ml/.venv/bin/pip install scikit-surprise")
        return

    print("[2] surprise SVD (explicit ratings) — toy primer")
    # 3 korisnika × 4 proizvoda, ocene 1–5; zadnja ćelija je „nepoznata" (0).
    rows = [
        ("u1", "p1", 5), ("u1", "p2", 4), ("u1", "p3", 2),
        ("u2", "p1", 4), ("u2", "p2", 5), ("u2", "p4", 1),
        ("u3", "p1", 1), ("u3", "p3", 5), ("u3", "p4", 4),
    ]
    import pandas as pd

    reader = Reader(rating_scale=(1, 5))
    data = Dataset.load_from_df(pd.DataFrame(rows, columns=["user", "item", "rating"]), reader)
    trainset = data.build_full_trainset()
    algo = SVD(n_factors=3, random_state=42)
    algo.fit(trainset)

    # Nepoznata ćelija: korisnik u1, proizvod p4 — koliko bi ocenio?
    pred = algo.predict("u1", "p4").est
    print(f"    predikcija ocene u1->p4 (nepoznata ćelija): {pred:.2f} (skala 1–5)")
    print()


def main() -> None:
    print("=== Day 6 — MF extension (surprise / implicit) ===\n")
    implicit_als_similar_items()
    surprise_svd_explicit_toy()
    print("Gotovo.")


if __name__ == "__main__":
    main()
