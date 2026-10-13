"""Starter za Day 11 lab — structured generative-AI service (student piše).

Kursni modul ``dm-ml/app/services/ai.py`` već sadrži punu verziju ovoga
(``parse_json_output``, ``validate_*``, ``generate_with_retry``,
``ExternalProvider``). U ovom lab-u **ti ih pišeš sam** — na malim, ručno
napravljenim strukturama — da razumeš *šta* structured generation radi pre
nego što dotakneš pravi LLM (DAY-BRIEFS: unbounded retry, positional key
mapping i izostanak validacije su česti bagovi — ovde ih svesno popravljaš).

Ne menjaš ``dm-ml`` — radiš u ovom fajlu i proveravaš rešenje sa
``test_lab.py``:

    cd "Day 11/lab"
    python3 -m pytest test_lab.py              # tvoje rešenje
    LAB_MODULE=reference_solutions python3 -m pytest test_lab.py   # referentno

Fajl je samostalan (bez importa iz ``dm-ml``) — pišeš čistu Python logiku.
"""

import json
import re


# --------------------------------------------------------------------------- #
# Greške — iste uloge kao u dm-ml (InvalidLLMJsonError -> retry, posle toga
# GenerationFailSafeError -> template fallback)
# --------------------------------------------------------------------------- #
class InvalidLLMJsonError(Exception):
    """LLM output se ne može protumačiti kao validan JSON objekat."""


class GenerationFailSafeError(Exception):
    """Iscrpljeni su bounded retry pokušaji — pozivalac prelazi na fail-safe."""


# --------------------------------------------------------------------------- #
# AIProvider apstrakcija
# --------------------------------------------------------------------------- #
class AIProvider:
    """Apstrakcija generativnog modela — ``generate(prompt) -> str``.

    Aplikacioni kod NE sme da zna koji je model iza: ``LocalModelProvider``
    (TinyLlama) i ``ExternalProvider`` (HTTP API) dele isti interfejs.
    """

    def generate(self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str:
        raise NotImplementedError

    def available(self) -> bool:
        raise NotImplementedError

    def descriptor(self) -> dict:
        raise NotImplementedError


# --------------------------------------------------------------------------- #
# 1) parse_json_output — izvuci JSON iz raw LLM teksta
# --------------------------------------------------------------------------- #
def parse_json_output(raw: str) -> dict:
    """Vadi prvi JSON objekat iz raw LLM outputa.

    LLM često doda ```json``` fence-ove, uvodni/prazeći tekst ili komentare.
    Preskoči sve to i vrati **dict**. Ako objekat ne postoji ili nije
    parsabilan -> ``InvalidLLMJsonError`` (ovo je slučaj koji bounded retry
    ponavlja).

    Anti-pattern (``current-materials/``) je ovde radio ``while True`` +
    ``json.loads`` bez ikakvog limita — ovde funkcija samo **prijavi** grešku,
    a ``generate_with_retry`` broji pokušaje.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 2) validate_required_fields — po imenu polja, ne po poziciji
# --------------------------------------------------------------------------- #
def validate_required_fields(data: dict, required: list[str]) -> None:
    """Proveri da su sva ``required`` polja prisutna (po imenu).

    Nedostajuće polje -> ``InvalidLLMJsonError`` sa imenima koja fale.

    Anti-pattern je mapirao ključeve **po poziciji** (``validKeys[i]``) —
    šema očekuje ``seo_title``/``seo_description``/``keywords``, a ti moraš
    da proveriš **imena** polja, ne redosled.
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 3) validate_length — Google limit
# --------------------------------------------------------------------------- #
def validate_length(value, max_len: int) -> bool:
    """Da li je ``len(str(value)) <= max_len`` (npr. seo_title <= 60)."""
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 4) validate_product_facts — slaba provera „istinitosti"
# --------------------------------------------------------------------------- #
# Minimalni stopwordi (lab koristi mali skup; dm-ml ima veći).
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from",
    "has", "he", "in", "is", "it", "of", "on", "or", "that", "the", "to",
    "was", "were", "will", "with", "i", "you", "your", "we", "za", "i",
    "je", "na", "u", "se", "od", "sa", "sve", "kupite", "kupovina",
}


def _significant_tokens(text: str) -> list[str]:
    return [
        t.lower()
        for t in re.findall(r"[a-z0-9čćžšđ]+", str(text), re.IGNORECASE)
        if t.lower() not in STOPWORDS and len(t) > 1
    ]


def validate_product_facts(generated_text: str, product: dict) -> list[str]:
    """Product facts: da li tekst pominje naziv/kategoriju proizvoda.

    Vraća listu nedostajućih fact-ova (``name`` / ``category``). Proizvod bez
    naziva ili kategorije -> taj fact se preskače.

    Ovo je **slaba provera istinitosti**: prisustvo tokena nije dokaz da je
    tekst tačan (vidi README — „Šta rezultat NE dokazuje"), ali odsustvo
    jeste jak signal halucinacije (generisao si tekst koji uopšte ne pominje
    proizvod).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 5) generate_with_retry — bounded retry + fail-safe
# --------------------------------------------------------------------------- #
def generate_with_retry(provider: AIProvider, prompt: str, *, max_retries: int = 2, **kwargs) -> dict:
    """Generiši + validiraj JSON, sa **bounded** retry.

    Svaki pokušaj: ``provider.generate(prompt)`` -> ``parse_json_output`` ->
    ``validate_required_fields`` (SEO šema). Neuspeh se ponavlja do
    ``max_retries`` puta — **ne bezkonačno** (anti-pattern je radio
    ``while True``). Posle iscrpljenih pokušaja -> ``GenerationFailSafeError``,
    a pozivalac prelazi na template fallback (fail-safe).

    Vraća validiran ``dict`` (parsiran JSON).
    """
    # TODO: implementiraj
    raise NotImplementedError


# --------------------------------------------------------------------------- #
# 6) http_post + ExternalProvider — model iza apstrakcije
# --------------------------------------------------------------------------- #
def http_post(url: str, payload: dict, headers: dict) -> tuple[int, str]:
    """Pošalji POST JSON i vrati ``(status_code, response_text)``.

    HTTP greške (4xx/5xx) vraćaju status + telo; mrežne greške bacaju
    ``ConnectionError``. Testovi zamenjuju ovu funkciju da ne idu na mrežu.
    """
    # TODO: implementiraj (urllib.request)
    raise NotImplementedError


class ExternalProvider(AIProvider):
    """Provider preko OpenAI-compatible HTTP API-ja (``/chat/completions``).

    ``generate`` šalje ``{"messages": [{"role": "user", "content": prompt}],
    ...}`` i vraća ``choices[0].message.content``.
    """

    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4o-mini"):
        self.base_url = (base_url or "").rstrip("/")
        self.api_key = api_key or ""
        self.model = model or "gpt-4o-mini"

    def available(self) -> bool:
        # TODO: dostupan ako su base_url i api_key konfigurisani
        raise NotImplementedError

    def descriptor(self) -> dict:
        # TODO: {"name": "external", "base_url": ..., "model": ...}
        raise NotImplementedError

    def generate(self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str:
        # TODO: POST /chat/completions preko http_post; status != 200 -> raise;
        # inače izvuci choices[0].message.content i vrati strip()-ovano
        raise NotImplementedError
