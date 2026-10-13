"""Day 11 — template (rule/heuristic) baseline: SEO meta, opis proizvoda, kopija kampanje."""
from __future__ import annotations

import re

STOPWORDS = {"a", "an", "and", "are", "as", "at", "be", "but", "by", "for", "from", "has", "in", "is", "it",
             "item", "of", "on", "or", "that", "the", "to", "was", "were", "will", "with", "you", "your",
             "za", "i", "je", "na", "u", "se", "od", "sa", "sve", "kupite", "kupovina"}
TITLE_MAX, DESC_MAX = 60, 155


def significant_tokens(text: str) -> list:
    return [t.lower() for t in re.findall(r"[a-z0-9čćžšđ]+", str(text or ""), re.IGNORECASE)
            if t.lower() not in STOPWORDS and len(t) > 1]


def template_keywords(name, category, description, n=5) -> list:
    return list(dict.fromkeys(significant_tokens(f"{name} {category} {description}")))[:n]


def _cut(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def template_seo_metadata(name: str, description: str = "", category: str = "") -> dict:
    title = f"{name} | {category}" if category else name
    desc = f"Kupite {name}. {description}".strip()
    return {"seo_title": _cut(title, TITLE_MAX), "seo_description": _cut(desc, DESC_MAX),
            "keywords": template_keywords(name, category, description)}


def template_product_description(name: str, description: str = "", category: str = "") -> str:
    cat = f" iz kategorije {category}" if category else ""
    return f"{name}{cat}. {description} Pogledajte detalje i dostupnost u prodavnici.".replace("  ", " ")


def template_campaign_copy(name: str, goal: str = "", audience: str = "") -> str:
    aud = f" Stvoreno za publiku: {audience}." if audience else ""
    return f"{name}. Cilj: {goal or 'posebna ponuda'}.{aud} Iskoristite priliku dok traje ponuda!"
