"""Starter za Day 8 lab — hybrid merge/rank/pravila/raznovrsnost.

Implementiraš mali deo onoga što kursni modul ``dm-ml/app/recommenders/hybrid.py``
već sadrži (da razumeš *šta* two-stage pipeline radi). Ne menjaš ``dm-ml`` —
radiš u ovom fajlu i proveravaš svoje rešenje sa ``test_lab.py``.

Kandidat = dict ``{"product_id": int, "score": float}`` (opciono ``category_id``).
"""

# --------------------------------------------------------------------------- #
# 1) normalize_scores — max-skaliranje na [0, 1]
# --------------------------------------------------------------------------- #
def normalize_scores(scores):
    """Max-skaliranje liste skorova na [0, 1].

    ``score / max``. Ako je ``max == 0`` -> svi ``0.0``; ako su svi jednaki
    (``max == min > 0``) -> svi ``1.0``. Prazna lista -> ``[]``.

    Zašto: ne možeš smisleno sabrati TF-IDF sličnost (0..1) sa sirovim
    count-om interakcija (0..stotine) pre nego što ih normalizuješ.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) merge_candidates — normalizacija + težinski spoj + dedup
# --------------------------------------------------------------------------- #
def merge_candidates(candidate_lists, weights):
    """Spaja kandidate izvora u JEDNU listu sa blended skorom.

    ``candidate_lists``: dict ``source`` -> lista kandidata (dict-ova sa
    ``product_id``/``score``). ``weights``: dict ``source`` -> težina.

    Koraci:
      1. Svaki izvor normalizuj sa ``normalize_scores`` (po izvoru).
      2. Za svaki proizvod: blended = ``Σ w_source * normalized_score``
         (normalizuj težine da zbirom budu 1.0).
      3. Duplikati se spajaju; ``sources`` = sortirana lista izvora.

    Vraća listu dict-ova: ``product_id``, ``score`` (blended), ``sources``.
    Prazan ulaz -> ``[]``; zbir težina <= 0 -> ``ValueError``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) rank_candidates — deterministički sort
# --------------------------------------------------------------------------- #
def rank_candidates(candidates):
    """Rangira kandidate: ``score`` opadajuće, tie-break ``product_id`` rastuće.

    Deterministika — isti ulaz uvek daje isti redosled.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) apply_business_rules — filter posle rangiranja
# --------------------------------------------------------------------------- #
def apply_business_rules(ranked, rules):
    """Primeni biznis pravila na RANGIRANU listu (filter, ne generator).

    ``rules`` (dict, opcioni ključevi):
      - ``available_ids`` (set) — ostaju samo proizvodi u skupu (dostupnost).
      - ``exclude_ids`` (set) — izbaci proizvode (npr. već kupljeno/viđeno).
      - ``min_score`` (float) — merged skor >= granice.

    Vraća dict: ``ranked`` (kept), ``removed`` (sa ``removed_by`` razlozima).
    Prazna lista -> ``{"ranked": [], "removed": []}``.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 5) diversify_results — raznovrsnost bez uništavanja relevantnosti
# --------------------------------------------------------------------------- #
def diversify_results(ranked, k, max_per_category=2):
    """Greedy re-ranker po kategoriji.

    Prolazi kroz rangiranu listu i zadržava kandidata ako njegova kategorija
    nije prekoračila ``max_per_category``. Ako ostane mesta do ``k``, DOPUNJUJE
    ostatkom liste po redosledu (ne skraćuje ispod onoga što ima — „fill,
    don't truncate"). Kandidat bez ``category_id`` se uvek zadržava.
    """
    # TODO: implementiraj
    raise NotImplementedError
