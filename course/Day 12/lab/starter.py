"""Starter za Day 12 lab — taksonomija, fallback i izbor modula (student piše).

Capstone (``dm-ml/app/services/platform.py``) već sadrži pravi integrisani
sistem. U ovom lab-u **ti pišeš čistu logiku** koja dokazuje da razumeš tri
capstone veštine, pre nego što ocenjuješ dizajn:

  1. **``classify``** — označi svaku komponentu: pravilo/heuristika,
     statistika, ML, generative AI, data pipeline, evaluacija;
  2. **``fallback_for``** — za svaki failure scenario vrati definisani fallback
     (acceptance: „failure cases are handled");
  3. **``select_module``** — za svaki marketing zadatak izaberi primarni modul
     (flywheel: data → segment → predict → target → recommend → generate).

Ne menjaš ``dm-ml`` — radiš u ovom fajlu i proveravaš rešenje sa ``test_lab.py``:

    cd "Day 12/lab"
    python3 -m pytest test_lab.py                          # tvoje rešenje
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # referentno

Fajl je samostalan (bez importa iz ``dm-ml``).
"""


# --------------------------------------------------------------------------- #
# Taksonomija komponenti (day-agnostic, ista kao u systemu)
# --------------------------------------------------------------------------- #
RULE = "rule / heuristic"
STATISTICAL = "statistical"
ML = "ML (prediction / learned representation)"
GENAI = "generative AI"
DATA_PIPELINE = "data pipeline"
EVAL = "statistical / evaluation protocol"

# Komponenta (id) -> klasa. Ovo je odgovor na „označi svaku komponentu".
TAXONOMY: dict[str, str] = {
    "events": DATA_PIPELINE,
    "rfm": RULE,
    "kmeans_segmentation": ML,
    "majority_baseline": STATISTICAL,
    "conversion_model": ML,
    "rule_targeting": RULE,
    "popularity": STATISTICAL,
    "content_tfidf": STATISTICAL,
    "template_text": RULE,
    "collaborative": STATISTICAL,
    "evaluation": EVAL,
    "hybrid": RULE,  # merge težine + pipeline su heuristika, ne naučen model
    "session": RULE,
    "ctr": STATISTICAL,
    "embeddings": ML,
    "generative_ai": GENAI,
    "seo_template": RULE,
}


# --------------------------------------------------------------------------- #
# Fallback-i (failure handling) — scenario -> fallback
# --------------------------------------------------------------------------- #
FALLBACKS: dict[str, str] = {
    # nepoznat korisnik bez istorije
    "unknown_user": "unsegmented (no_history) + base_rate p(buy)",
    # sesija bez ijednog proizvodnog događaja
    "no_session_signal": "popularity top-N (no_session_signal)",
    # segment / konverzija model nije treniran
    "untrained_model": "unsegmented (untrained_model) / base_rate (untrained_model)",
    # LLM provider nije dostupan (nema API-ja, model nije keširan)
    "model_unavailable": "template (source=template, model_unavailable)",
    # LLM output ne prođe validaciju (bounded retry iscrpljen)
    "invalid_llm_output": "template (source=template, invalid_llm_output)",
    # proizvod nema red u embedding store-u
    "no_embedding": "popularity (no_embedding)",
    # embedding model (query embedder) se ne može učitati
    "embedder_unavailable": "keyword fallback (embedder_unavailable)",
    # nov proizvod bez TF-IDF reda / bez interakcija (content/collaborative)
    "cold_start": "popularity (unknown_product / no_interactions)",
    # nema events.csv -> svi zavisni moduli su nedostupni
    "events_file_missing": "module available=false (fallback lanac)",
    # CTR nad 0 impresija
    "zero_impressions": "ctr=0.0 (zero-division handling)",
}


# --------------------------------------------------------------------------- #
# Marketing zadaci -> primarni modul (flywheel)
# --------------------------------------------------------------------------- #
TASKS: dict[str, str] = {
    "segment_user": "kmeans_segmentation",
    "predict_purchase": "conversion_model",
    "target_campaign": "rule_targeting",
    "recommend_for_user": "hybrid",
    "recommend_for_session": "session",
    "semantic_search": "embeddings",
    "generate_content": "generative_ai",
    "evaluate_recommendations": "evaluation",
}


# --------------------------------------------------------------------------- #
# 1) classify — označi komponentu
# --------------------------------------------------------------------------- #
def classify(component_id: str) -> str:
    """Vraća klasu komponente (``TAXONOMY``), npr. ``classify("rfm") -> RULE``.

    Nepoznata komponenta -> ``ValueError`` (ne vraćaj ``None`` tiho).
    Ovo je „student can label each component" iz acceptance-a.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) fallback_for — koji fallback za koji scenario
# --------------------------------------------------------------------------- #
def fallback_for(failure_code: str) -> str:
    """Vraća definisani fallback za scenario (``FALLBACKS``).

    Nepoznat scenario -> ``ValueError``. Failure handling je deo dizajna:
    svaki pad mora da ima imenovan fallback — NIKAD tiho prazno.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) select_module — izaberi modul za zadatak
# --------------------------------------------------------------------------- #
def select_module(task: str) -> str:
    """Vraća primarni modul za marketing zadatak (``TASKS``).

    Nepoznat zadatak -> ``ValueError``. Ovo je flywheel iz Day 12 teorije:
    data -> segment -> predict -> target -> recommend -> generate -> evaluate.
    """
    # TODO: implementiraj
    raise NotImplementedError
