"""Toy SGD: matrix factorization iz osnova (Day 6 vežba).

SGD (stohastički gradijentni spust) na **toy matrici** — mala implicitna
matrica interakcija (5 korisnika × 4 proizvoda). Cilj: naučiti faktorizaciju
``R ≈ P @ Q.T`` (P = korisnički faktori, Q = proizvod faktori, ``k`` latentnih
domena) minimizovanjem greške rekonstrukcije na **posmatranim** ćelijama uz L2
regularizaciju.

Ovo je *prvi korak* ka matrix factorization (MF): isti SGD mehanizam koriste
``surprise``/``implicit`` biblioteke (vidi ``mf_library.py``). Poenta vežbe:

  - razumeš gradijentni korak ``P[u] += lr * (err * Q[i] - reg * P[u])``;
  - vidiš da se RMSE smanjuje kroz epohe;
  - proveriš da naučeni faktori **reprodukuju toy matricu** (rekonstrukcija ≈
    original) — to je acceptance za ovaj fajl.

Pokretanje (koristi dm-ml venv — treba samo numpy):

    dm-ml/.venv/bin/python "Day 6/examples/toy_sgd.py"

Zameni ``TOY_MATRIX`` svojom malom matricom i ponovo pokreni.
"""

from __future__ import annotations

import numpy as np

# Toy implicitna matrica: red = korisnik, kolona = proizvod, 0 = nema interakcije.
TOY_MATRIX = np.array(
    [
        [5, 3, 0, 1],
        [4, 0, 0, 1],
        [1, 1, 0, 5],
        [1, 0, 0, 4],
        [0, 1, 5, 4],
    ],
    dtype=float,
)

N_LATENT = 2  # broj latentnih faktora (k)
LR = 0.02     # stopa učenja
REG = 0.1     # L2 regularizacija
N_EPOCHS = 200
SEED = 42


def sgd_matrix_factorization(
    R: np.ndarray,
    k: int = N_LATENT,
    lr: float = LR,
    reg: float = REG,
    n_epochs: int = N_EPOCHS,
    seed: int = SEED,
) -> tuple[np.ndarray, np.ndarray, list[float]]:
    """SGD faktorizacija ``R ≈ P @ Q.T`` na posmatranim ćelijama.

    Vraća ``(P, Q, rmse_history)`` — P (n_users×k), Q (n_items×k) i RMSE po
    epohi nad posmatranim ćelijama. Svaka iteracija uzima jednu posmatranu
    ćeliju, računa grešku i koriguje odgovarajuće redove P i Q (gradijentni
    spust + regularizacija).
    """
    rng = np.random.default_rng(seed)
    n_users, n_items = R.shape
    P = rng.normal(scale=0.1, size=(n_users, k))
    Q = rng.normal(scale=0.1, size=(n_items, k))
    rows, cols = np.nonzero(R)
    history: list[float] = []

    for _ in range(n_epochs):
        for u, i in zip(rows, cols):
            r_ui = R[u, i]
            err = r_ui - float(P[u] @ Q[i])
            # Gradijentni koraci: učiš i korisnički i proizvod vektor.
            P[u] += lr * (err * Q[i] - reg * P[u])
            Q[i] += lr * (err * P[u] - reg * Q[i])
        history.append(rmse(R, P, Q))

    return P, Q, history


def rmse(R: np.ndarray, P: np.ndarray, Q: np.ndarray) -> float:
    """RMSE nad posmatranim ćelijama (``R > 0``)."""
    mask = R > 0
    recon = P @ Q.T
    return float(np.sqrt(((R[mask] - recon[mask]) ** 2).mean()))


def main() -> None:
    print("=== Day 6 — Toy SGD matrix factorization ===")
    print(f"Toy matrica ({TOY_MATRIX.shape[0]} korisnika × {TOY_MATRIX.shape[1]} proizvoda):")
    print(TOY_MATRIX)
    print(f"k={N_LATENT}, lr={LR}, reg={REG}, epochs={N_EPOCHS}, seed={SEED}")
    print()

    P, Q, history = sgd_matrix_factorization(TOY_MATRIX)

    print("RMSE kroz epohe (svakih 50):")
    for epoch in range(0, N_EPOCHS, 50):
        print(f"  epoch {epoch:>3}: rmse={history[epoch]:.4f}")
    print(f"  final: rmse={history[-1]:.4f}")
    print()

    recon = P @ Q.T
    print("Rekonstrukcija (P @ Q.T):")
    print(np.round(recon, 2))
    print()

    # Acceptance: naučeni faktori reprodukuju toy matricu (mala finalna greška).
    assert history[-1] < 1.0, (
        f"toy SGD nije konvergirao: finalni RMSE {history[-1]:.4f} — "
        "povećaj n_epochs ili podesi lr/reg"
    )
    print(f"OK: finalni RMSE {history[-1]:.4f} < 1.0 — faktori reprodukuju toy matricu.")

    print("\nNaučeni faktori:")
    print("P (korisnici):")
    print(np.round(P, 3))
    print("Q (proizvodi):")
    print(np.round(Q, 3))
    print("\nGotovo.")


if __name__ == "__main__":
    main()
