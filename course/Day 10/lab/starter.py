"""Starter za Day 10 lab — brute-force nearest neighbors (student-written).

Implementiraš mali deo onoga što kursni modul
``dm-ml/app/recommenders/embeddings.py`` već sadrži (da razumeš *šta* semantička
pretraga i kosinusna sličnost rade). Ne menjaš ``dm-ml`` — radiš u ovom fajlu i
proveravaš svoje rešenje sa ``test_lab.py``.

Lab radi na malim, ručno napravljenim numpy strukturama — nema pandas-a, nema
embedding modela, nema ANN biblioteke.
"""

import numpy as np


# --------------------------------------------------------------------------- #
# 1) normalize — L2 normalizacija redova
# --------------------------------------------------------------------------- #
def normalize(vectors):
    """L2-normalizuje svaki red (vektor -> jedinični vektor).

    ``vectors`` je ``np.ndarray`` oblika ``(n, dim)`` (ili ``(dim,)``).
    Nula-red (norma 0) ostaje nula-red — kosinus sa njim je 0, ne ``NaN``.

    Zašto: kosinus sličnost nenormalizovanih vektora meša dužine (čest bag).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) cosine_similarity — kosinusna sličnost upita sa svakim redom
# --------------------------------------------------------------------------- #
def cosine_similarity(query_vec, matrix):
    """Kosinusne sličnosti ``query_vec`` (1-D) sa svakim redom ``matrix``.

    Vraća 1-D ``np.ndarray`` dužine ``matrix.shape[0]``, redom kao ``matrix``.
    NORMALIZUJ OBA ULAGA (preko ``normalize``) — to je lekcija dana.

    Za ``n`` normalizovanih vektora, kosinus = skalarni proizvod:
    ``matrix @ query``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) brute_force_nearest — top-k najbližih suseda (brute-force petlja)
# --------------------------------------------------------------------------- #
def brute_force_nearest(matrix, query_vec, k=3, exclude_index=None):
    """Top-``k`` ``(index, score)`` po kosinusnoj sličnosti, opadajuće.

    ``matrix`` je ``(n, dim)``; ``query_vec`` je ``(dim,)``. Redni brojevi
    rezultata se odnose na ``matrix`` (ne na product_id — to je posao
    pozivaoca). ``exclude_index`` (opciono) se izbacuje iz rezultata („ne
    preporučuj sam sebe").

    Vraća listu ``[(index, score), ...]`` — **ovo je brute-force petlja** koju
    ANN biblioteke (faiss/annoy) rade pametnije na velikim skupovima.
    """
    # TODO: implementiraj (koristi cosine_similarity, pa sortiraj opadajuće)
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) semantic_search_lite — top-k proizvoda za embedding upita
# --------------------------------------------------------------------------- #
def semantic_search_lite(products, embeddings, query_embedding, k=3):
    """Top-``k`` proizvoda za dati embedding upita (brute-force).

    ``products`` = lista dict-ova ``{"product_id": int, "name": str}``;
    ``embeddings`` = ``np.ndarray`` ``(len(products), dim)`` — red ``i`` je
    embedding proizvoda ``i`` (ISTI redosled kao ``products``).

    Vraća listu dict-ova ``{"product_id": int, "name": str, "score": float}``,
    opadajuće po skoru. (Ne menja ``products``.)
    """
    # TODO: implementiraj (brute_force_nearest, pa mapiraj na products)
    raise NotImplementedError
