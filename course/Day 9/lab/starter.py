"""Starter za Day 9 lab — session features, recency i CTR (feedback loop).

Implementiraš mali deo onoga što kursni modul ``dm-ml/app/recommenders/session.py``
već sadrži (da razumeš *šta* session-aware preporuke i CTR rade). Ne menjaš
``dm-ml`` — radiš u ovom fajlu i proveravaš svoje rešenje sa ``test_lab.py``.

Lab radi na malim, ručno napravljenim strukturama (list dict-ova) — bez pandas-a.
"""

# Težine događaja unutar sesije (Day 9 / Day 5-8 kontinuitet).
EVENT_WEIGHTS = {"product_view": 1.0, "add_to_cart": 3.0, "purchase": 5.0}


# --------------------------------------------------------------------------- #
# 1) recency_weights — geometrijska recency težina
# --------------------------------------------------------------------------- #
def recency_weights(n, decay):
    """Težina po događaju, od najnovijeg (1.0) ka najstarijem (``decay**i``).

    Za ``n`` događaja (najnoviji je POSLEDNJI): težina i-tog je
    ``decay ** (n - 1 - i)``. ``n == 0`` -> ``[]``.

    Zašto: skoriji događaji nose više informacije o tekućem interesu — sesija
    koja je pre 2 min gledala 'tenis' je verovatnije o tenisu nego ona koja je
    tenis gledala pre 30 min (recency).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) recent_product_interest — recency-weighted interes proizvoda
# --------------------------------------------------------------------------- #
def recent_product_interest(events, decay=0.8):
    """``{product_id: interes}`` iz proizvodnih događaja sesije.

    ``events`` = lista dict-ova ``{"event_type": str, "product_id": int}``
    (hronološki poredak — najnoviji POSLEDNJI). Za svaki proizvodni događaj
    (``event_type`` u ``EVENT_WEIGHTS``): težina = ``EVENT_WEIGHTS[type] *
    recency_weights[i]``; agregira se (zbir) po proizvodu.

    Vraća dict ``product_id -> interes``. Bez proizvodnih događaja -> ``{}``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) recent_category_interest — interes kategorija iz sesije
# --------------------------------------------------------------------------- #
def recent_category_interest(events, product_categories, decay=0.8):
    """``{category_id: interes}`` — mapira proizvodni interes na kategorije.

    ``product_categories`` = dict ``product_id -> category_id`` (katalog je
    source of truth). Interes proizvoda (iz ``recent_product_interest``) se
    sabira po kategoriji. Proizvodi kojih nema u katalogu se ignorišu.

    Vraća dict ``category_id -> interes``. Prazno -> ``{}``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) recommendation_ctr — CTR sa zero-division handling-om
# --------------------------------------------------------------------------- #
def recommendation_ctr(impressions, clicks):
    """Click-through rate: ``len(clicks) / len(impressions)``.

    ``impressions`` = lista (npr. impression događaja); ``clicks`` = lista
    (npr. click događaja). **Zero-division:** ``len(impressions) == 0`` ->
    vraća ``0.0`` (bez ``None``, bez deljenja kroz nulu).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 5) ctr_by_algorithm — CTR po algoritmu
# --------------------------------------------------------------------------- #
def ctr_by_algorithm(impressions, clicks):
    """CTR po ``algorithm`` (``recommendation_source``).

    ``impressions``/``clicks`` = liste dict-ova sa ključem ``algorithm`` (npr.
    ``"popular"``/``"personalized"``). Vraća listu dict-ova sortiranu po
    ``algorithm`` rastuće:

        [{"algorithm": "popular", "impressions": N, "clicks": C, "ctr": float},
         {"algorithm": "personalized", ...}, ...]

    Algoritam sa 0 impresija -> ``ctr = 0.0`` (zero-division).
    """
    # TODO: implementiraj
    raise NotImplementedError
