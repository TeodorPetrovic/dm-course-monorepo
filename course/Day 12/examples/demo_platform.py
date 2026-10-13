"""Demo: Integrated Marketing Platform (Day 12 capstone).

Pokretanje (bilo gde, koristi dm-ml venv):

    dm-ml/.venv/bin/python "Day 12/examples/demo_platform.py"

Prikazuje:
  1) **module status** — manifest arhitekture: koji modul je dostupan, koje
     je klase (rule/heuristic/statistical/ML/generative-AI) i koji mu je
     fallback (diagnostics);
  2) **marketing flywheel profil** — segment (Day 2) + verovatnoća kupovine
     (Day 3) + RFM + istorija + targeting hint (Day 4), sa fallback-ovima za
     nepoznatog korisnika;
  3) **homepage payload** — integrisana početna strana: hero AI sadržaj
     (Day 11, template fallback ako LLM nije dostupan) + hybrid preporuke
     (Day 8) + session preporuke (Day 9) + semantic (Day 10) + CTR summary;
  4) **failure cases** — nepoznat korisnik (fallback), netreniran model
     (fallback), LLM down (template) — svaki nosi ``fallback`` +
     ``fallback_reason`` + ``module_class``;
  5) **product page** — AI-asistiran opis/SEO (Day 11) + taksonomija sekcija
     koje CMS renderuje.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

from app.services.platform import IntegratedPlatformService

DEMO_USER = 395
DEMO_SESSION = "session_005246"
DEMO_PRODUCT = 22
UNKNOWN_USER = 999999


def _rec_brief(recs: dict) -> str:
    if not recs or not recs.get("recommendations"):
        return f"{recs.get('method')} (fallback={recs.get('fallback')}, {recs.get('fallback_reason')})"
    names = [r.get("name") for r in recs["recommendations"][:3]]
    return f"{recs.get('method')} n={len(recs['recommendations'])}: {', '.join(names)}"


def main() -> None:
    print("=== Day 12 — Integrated AI Marketing Platform Capstone ===\n")
    svc = IntegratedPlatformService()

    # --- 1) Module status --------------------------------------------------- #
    status = svc.module_status()
    print("[1] Module status (manifest arhitekture):")
    for m in status["modules"]:
        ok = "✓" if m["available"] else "✗ fallback"
        print(f"    {m['id']:22s} {m['class']:38s} {ok}")
    print(f"    summary: {status['summary']['available']}/{status['summary']['total']} "
          f"dostupno (generative_ai obično ✗ bez LLM providera — fail-safe)")
    print()

    # --- 2) Marketing flywheel profil --------------------------------------- #
    print("[2] Marketing flywheel profil (Day 2/3/4):")
    p = svc.profile_for_user(DEMO_USER)
    print(f"    segment : {p['segment']['label']}  (class={p['segment']['module_class']})")
    print(f"    p(buy)  : {p['conversion']['probability']:.4f}  "
          f"(class={p['conversion']['module_class']}, base_rate={p['conversion']['base_rate']:.4f})")
    print(f"    rfm     : {p['rfm']['bucket']}  (class={p['rfm']['module_class']})")
    print(f"    history : {p['history']['n_events']} događaja, "
          f"{p['history']['n_purchases']} kupovina")
    print(f"    targeting: {p['targeting_hint']['reason']}")
    print()

    # --- 3) Homepage payload (integrisani put) ------------------------------ #
    print("[3] Homepage payload (integrisana platforma):")
    hp = svc.homepage_payload(DEMO_USER, session_id=DEMO_SESSION, limit=5)
    hero = hp["hero"]
    print(f"    hero     : [{hero['source']}] fallback={hero['fallback']} "
          f"class={hero['module_class']}")
    print(f"               {hero['content'][:90]}…")
    print(f"    recs     : {_rec_brief(hp['recommendations'])}")
    print(f"    session  : {_rec_brief(hp['session_recommendations'])}")
    if hp["semantic"]:
        print(f"    semantic : n={len(hp['semantic']['recommendations'])} "
              f"class={hp['semantic']['module_class']}")
    print(f"    featured : {hp['featured_content']['kind']} "
          f"[{hp['featured_content']['source']}]")
    print(f"    ctr      : overall={hp['evaluation_summary']['overall']} "
          f"class={hp['evaluation_summary']['module_class']}")
    print(f"    modules  : {', '.join(m['id'] for m in hp['modules_used'])}")
    print()

    # --- 4) Failure cases --------------------------------------------------- #
    print("[4] Failure handling (svaki nosi fallback + reason + class):")
    unk = svc.profile_for_user(UNKNOWN_USER)
    print(f"    unknown user segment : {unk['segment']['label']} "
          f"fallback={unk['segment']['fallback']} ({unk['segment']['fallback_reason']})")
    print(f"    unknown user p(buy)  : {unk['conversion']['probability']:.4f} "
          f"(= base_rate, fallback={unk['conversion']['fallback']})")
    print(f"    hero source          : {hero['source']} "
          f"(fallback={hero['fallback']} — LLM nije dostupan -> template)")
    print()

    # --- 5) Product page ---------------------------------------------------- #
    print("[5] Product page (AI sadržaj + taksonomija sekcija):")
    pp = svc.product_page_payload(DEMO_PRODUCT)
    print(f"    product  : {pp['product']['name']}")
    print(f"    ai_desc  : [{pp['ai_description']['source']}] fallback="
          f"{pp['ai_description']['fallback']}: {pp['ai_description']['content'][:80]}…")
    print(f"    ai_seo   : {pp['ai_seo']['seo_title']}")
    for s in pp["sections"]:
        print(f"    {s['section']:26s} -> {s['module_id']:16s} ({s['class']})")
    print()

    print("API: GET /platform/modules · GET /platform/profile/{user_id} · "
          "GET /platform/homepage · GET /platform/product/{product_id}")
    print("Data: Day 12/data/module-registry.json + homepage-snapshot.json "
          "(pokreni app.data.generate_platform)")
    print("Lab: Day 12/lab — capstone brief + rubric + design write-up template")


if __name__ == "__main__":
    main()
