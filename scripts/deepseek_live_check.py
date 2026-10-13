"""Live provera Day 11 servisa na DeepSeek-u (malo poziva, ~6). Ključ samo iz env-a; nikad se ne štampa.
Pokretanje: cd apps/api && .venv/bin/python ../../scripts/deepseek_live_check.py   (PLAĆENO: ~6 DeepSeek poziva)"""
import os, sys
sys.path.insert(0, os.getcwd())
from app.services.ai import (AIService, DeepSeekProvider, GenerationFailSafeError, SEOResponse,
                             generate_with_retry, parse_json_output, seo_prompt, validate_generated_output)
assert os.getenv("DEEPSEEK_API_KEY"), "DEEPSEEK_API_KEY nije postavljen"
P = {"name": "Smartphone Compact 686", "category": "Electronics",
     "description": "5G smartphone with OLED display, dual camera and fast charging. Compact line, black."}
ds = DeepSeekProvider(); ok = True
def check(name, cond, info=""):
    global ok; ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  — {info}" if info else ""))

# 1) bounded retry na pravim odgovorima: max_tokens=8 -> odsečen JSON -> 3 pokušaja -> fail-safe
trace = []
try:
    generate_with_retry(ds, seo_prompt(P), max_retries=2, schema=SEOResponse, trace=trace, max_tokens=8)
    check("bounded retry (odsečen output)", False, "neočekivano uspelo")
except GenerationFailSafeError as e:
    check("bounded retry (odsečen output)", len(trace) == 3 and all(trace), f"{len(trace)} pokušaja, poslednja: {trace[-1][:60]}")

# 2) servis sa istim (namerno lošim) providerom -> template fallback
class Tiny(DeepSeekProvider):
    def generate(self, prompt, **kw): return super().generate(prompt, max_tokens=8)
svc = AIService(provider=Tiny(), max_retries=1); r = svc.generate_seo_metadata(P)
check("fallback posle neuspelih pokušaja", r.fallback and r.fallback_reason == "invalid_llm_output" and r.source == "template",
      f"{len(svc.last_trace)} pokušaja -> {r.fallback_reason}")

# 3) validacija na pravom odgovoru koji krši ograničenje dužine
raw = ds.generate("Return ONLY a JSON object with keys seo_title, seo_description, keywords (list). "
                  "Make seo_title about 120 characters long. Product: Smartphone Compact 686. Category: Electronics.")
chk = validate_generated_output(parse_json_output(raw), P)
check("validacija hvata predug naslov", not chk["title_ok"] and not chk["valid"], f"title_len={chk['title_len']} > 60")

# 4) normalan put: validan odgovor prolazi
svc = AIService(provider=ds); r = svc.generate_seo_metadata(P)
check("validan odgovor prolazi", r.source == "deepseek" and not r.fallback and svc.last_checks.get("valid"),
      f"{len(svc.last_trace)} pokušaj(a); fallback={r.fallback_reason}; checks={svc.last_checks}; title='{r.seo_title}'")
print("ALL PASS" if ok else "SOME FAILED"); sys.exit(0 if ok else 1)
