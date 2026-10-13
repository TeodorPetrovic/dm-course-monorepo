"""Demo: structured generative-AI service (Day 11).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 11/examples/demo_generative.py"

Prikazuje:
  1) **AIProvider apstrakciju** — koji provider je aktivan (auto/local/external
     ili None -> template-only režim);
  2) **template baseline** — ``template_seo_metadata`` (rule/heuristic);
  3) **LLM put** — ``generate_seo_metadata`` (validacija + bounded retry +
     fail-safe; bez konfigurisanog modela vidljiv je template fallback);
  4) **fail-safe u praksi** — provider koji uvek vraća ne-JSON -> bounded retry
     (3 poziva) pa template fallback (``fallback_reason="invalid_llm_output"``);
  5) **content** — ``generate_product_description`` i ``generate_campaign_copy``;
  6) **template-vs-LLM poređenje** — summary iz ``Day 11/data/comparison.csv``
     (gde validacija hvata length/facts).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.ai import (
    AIService,
    AIProvider,
    GenerationFailSafeError,
    InvalidLLMJsonError,
    generate_with_retry,
    parse_json_output,
    validate_required_fields,
)
from app.services.ai import SEOResponse

PRODUCT = {
    "name": "Smartphone Compact 686",  # proizvod 1 iz Day 5 kataloga
    "description": "5G smartphone with OLED display, dual camera and fast charging. Compact line, black.",
    "category": "Electronics",
}
CAMPAIGN = {
    "name": "VIP reaktivacija",
    "goal": "Reaktiviraj najvrednije K-Means segmente",
    "target_segments": "segment_2, segment_3",
}


class _BrokenProvider(AIProvider):
    """Testni double koji uvek vrati ne-JSON (demo bounded retry + fail-safe)."""

    def available(self):
        return True

    def descriptor(self):
        return {"name": "broken"}

    def generate(self, prompt, **kwargs):
        return "I'm sorry, I cannot generate valid JSON right now."


def main() -> None:
    print("=== Day 11 — Structured Generative-AI Marketing Service ===\n")
    svc = AIService()
    print(f"[1] Aktivni provider: {svc.provider!r}  "
          f"(None = template-only režim — LLM nije konfigurisan/keširan)")
    print()

    # --- 2) Template baseline ----------------------------------------------- #
    print("[2] Template SEO baseline (rule/heuristic):")
    tpl = svc.template_seo(PRODUCT)
    print(f"    seo_title      : {tpl.seo_title}")
    print(f"    seo_description: {tpl.seo_description}")
    print(f"    keywords       : {tpl.keywords}")
    print()

    # --- 3) LLM put (sa fail-safe) ------------------------------------------ #
    print("[3] generate_seo_metadata (LLM -> validacija -> fail-safe):")
    seo = svc.generate_seo_metadata(PRODUCT)
    print(f"    source={seo.source}  fallback={seo.fallback}  "
          f"reason={seo.fallback_reason}")
    print(f"    seo_title      : {seo.seo_title}")
    print(f"    seo_description: {seo.seo_description}")
    print(f"    keywords       : {seo.keywords}")
    if svc.last_trace:  # samo kad je pravi provider pozvan (npr. AI_PROVIDER=deepseek)
        print(f"    pokušaji: {len(svc.last_trace)}  greške: {[e for e in svc.last_trace if e]}  "
              f"validacija: {svc.last_checks}")
    print()

    # --- 4) Fail-safe u praksi (bounded retry) ------------------------------- #
    print("[4] Bounded retry: broken provider (uvek ne-JSON, max_retries=2):")
    broken = _BrokenProvider()
    try:
        result = generate_with_retry(
            broken, "prompt", schema=SEOResponse,
            required=["seo_title", "seo_description", "keywords"],
            max_retries=2,
        )
        print(f"    (neočekivano uspelo: {result})")
    except GenerationFailSafeError as exc:
        print(f"    GenerationFailSafeError posle 3 pokušaja: {str(exc)[:80]}...")
    print("    (servis tada vraća template fallback — probaj svojom rukom)")
    print()

    # --- 5) Content ---------------------------------------------------------- #
    print("[5] Content generation (LLM -> template fallback):")
    desc = svc.generate_product_description(PRODUCT)
    print(f"    product_description [{desc.source}] fallback={desc.fallback}: {desc.content[:90]}…")
    copy = svc.generate_campaign_copy(CAMPAIGN)
    print(f"    campaign_copy      [{copy.source}] fallback={copy.fallback}: {copy.content[:90]}…")
    print()

    # --- 6) Template-vs-LLM poređenje ---------------------------------------- #
    print("[6] Template vs LLM (Day 11/data/comparison.csv):")
    comp_path = Path(__file__).resolve().parents[1] / "data" / "comparison.csv"
    if comp_path.exists():
        import pandas as pd

        comp = pd.read_csv(comp_path)
        for _, row in comp.iterrows():
            badge = "OK" if row["valid"] else "FAIL"
            fails = []
            if not row["title_ok"]:
                fails.append(f"title={row['title_len']}>60")
            if not row["desc_ok"]:
                fails.append(f"desc={row['desc_len']}>155")
            if not row["fields_ok"]:
                fails.append("fields")
            if not row["facts_ok"]:
                fails.append("facts")
            print(f"    {row['method']:8s} {row['source']:16s} {row['seo_title'][:34]:34s} "
                  f"[{badge}] {', '.join(fails) if fails else ''}")
    else:
        print("    comparison.csv nije generisan — pokreni "
              "`python -m app.data.generate_ai_comparison`")
    print()

    print("API: POST /ai/seo · POST /ai/content")
    print("Lab: Day 11/lab — parse_json_output, validate_*, generate_with_retry, ExternalProvider")


if __name__ == "__main__":
    main()
