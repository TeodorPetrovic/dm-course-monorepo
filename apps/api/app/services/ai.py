"""Day 11 — strukturisani generative-AI servis: AIProvider, Pydantic šeme, validacija,
bounded retry + fail-safe (template fallback). Ključevi se čitaju SAMO iz env-a."""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import List, Optional

from pydantic import BaseModel, Field

from app.services.templates import (DESC_MAX, TITLE_MAX, significant_tokens, template_campaign_copy,
                                    template_keywords, template_product_description,
                                    template_seo_metadata)

SEO_FIELDS = ["seo_title", "seo_description", "keywords"]


class InvalidLLMJsonError(Exception):
    pass


class GenerationFailSafeError(Exception):
    pass


class SEOResponse(BaseModel):
    seo_title: str
    seo_description: str
    keywords: List[str] = Field(default_factory=list)
    source: str = "template"
    fallback: bool = False
    fallback_reason: Optional[str] = None
    validated: bool = True
    raw: str = ""


class ContentResponse(BaseModel):
    content: str
    kind: str
    source: str = "template"
    fallback: bool = False
    fallback_reason: Optional[str] = None


class AIProvider(ABC):
    @abstractmethod
    def generate(self, prompt: str, *, max_tokens: int = 256, temperature: float = 0.5) -> str: ...

    @abstractmethod
    def available(self) -> bool: ...

    @abstractmethod
    def descriptor(self) -> dict: ...

    def __repr__(self):
        return f"<{type(self).__name__} {self.descriptor()}>"


def http_post(url: str, payload: dict, headers: dict, timeout: float = 30.0) -> tuple:
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except urllib.error.URLError as e:
        raise ConnectionError(str(e.reason)) from e


class ExternalProvider(AIProvider):
    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4o-mini"):
        self.base_url = (base_url or "").rstrip("/"); self.api_key = api_key or ""
        self.model = model or "gpt-4o-mini"

    def available(self):
        return bool(self.base_url and self.api_key)

    def descriptor(self):
        return {"name": "external", "base_url": self.base_url, "model": self.model}  # nikad ključ

    def generate(self, prompt, *, max_tokens=256, temperature=0.5):
        # TEACH d11+: ExternalProvider.generate
        status, body = http_post(f"{self.base_url}/chat/completions",
                                 {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                                  "max_tokens": max_tokens, "temperature": temperature},
                                 {"Authorization": f"Bearer {self.api_key}"})
        if status != 200:
            raise RuntimeError(f"external provider HTTP {status}")
        return json.loads(body)["choices"][0]["message"]["content"].strip()
        # /TEACH


class DeepSeekProvider(ExternalProvider):
    """DeepSeek (OpenAI-kompatibilan API). Ključ SAMO iz env-a DEEPSEEK_API_KEY; nikad se ne loguje."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None, base_url: Optional[str] = None):
        super().__init__(base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
                         api_key if api_key is not None else os.getenv("DEEPSEEK_API_KEY", ""),
                         model or os.getenv("DEEPSEEK_MODEL", "deepseek-chat"))

    def descriptor(self):
        return {"name": "deepseek", "base_url": self.base_url, "model": self.model}


class LocalModelProvider(AIProvider):
    def __init__(self, model: str = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"):
        self.model = model; self._pipe = None

    def available(self):
        try:
            from huggingface_hub import try_to_load_from_cache  # samo ako je model već keširan
            import transformers  # noqa: F401
            return isinstance(try_to_load_from_cache(self.model, "config.json"), str)
        except Exception:
            return False

    def descriptor(self):
        return {"name": "local", "model": self.model}

    def generate(self, prompt, *, max_tokens=256, temperature=0.5):
        if self._pipe is None:
            from transformers import pipeline
            self._pipe = pipeline("text-generation", model=self.model)
        out = self._pipe(prompt, max_new_tokens=max_tokens, temperature=temperature, do_sample=True,
                         return_full_text=False)
        return out[0]["generated_text"].strip()


class DemoProvider(AIProvider):
    """Scripted teaching double (NIJE LLM): valid | length_fail | facts_fail | invalid_json."""

    def __init__(self, variant: str = "valid"):
        self.variant = variant; self.product: dict = {}

    def available(self):
        return True

    def descriptor(self):
        return {"name": f"demo:{self.variant}"}

    def generate(self, prompt, **kwargs):
        p = self.product; name, cat = p.get("name", "Proizvod"), p.get("category", "")
        kw = template_keywords(name, cat, "")[:3] + ["kupi", "online"]
        if self.variant == "invalid_json":
            return "Sorry, here is your SEO text: title = great product"
        if self.variant == "length_fail":
            d = {"seo_title": f"{name} | {cat} — najbolja cena online, kupi danas, uštedi više, vreme je ograničeno",
                 "seo_description": f"Kupite {name} — {cat} proizvod po najboljoj ceni i uz brzu dostavu."}
        elif self.variant == "facts_fail":
            d = {"seo_title": f"{cat} — najbolje cene",
                 "seo_description": "Otkrijte najbolje proizvode po sjajnim cenama i brzu dostavu."}
        else:
            d = {"seo_title": f"{name} | {cat}", "seo_description": f"Kupite {name} — {cat} proizvod po najboljoj ceni."}
        return "```json\n" + json.dumps({**d, "keywords": kw}, ensure_ascii=False) + "\n```"


def build_default_provider(mode: Optional[str] = None) -> Optional[AIProvider]:
    mode = (mode or os.getenv("AI_PROVIDER", "auto")).lower()
    ext = ExternalProvider(os.getenv("AI_EXTERNAL_BASE_URL", ""), os.getenv("AI_EXTERNAL_API_KEY", ""),
                           os.getenv("AI_EXTERNAL_MODEL", "gpt-4o-mini"))
    if mode == "demo":
        return DemoProvider()
    if mode == "deepseek":  # samo eksplicitno (AI_PROVIDER=deepseek); bez ključa -> None -> template fallback
        ds = DeepSeekProvider()
        return ds if ds.available() else None
    if mode in ("auto", "external") and ext.available():
        return ext
    if mode in ("auto", "local"):
        loc = LocalModelProvider(os.getenv("AI_LOCAL_MODEL", "TinyLlama/TinyLlama-1.1B-Chat-v1.0"))
        if loc.available():
            return loc
    return None


def parse_json_output(raw: str) -> dict:
    # TEACH d11: parse_json_output
    if not isinstance(raw, str):
        raise InvalidLLMJsonError("output nije string")
    dec = json.JSONDecoder()
    for m in re.finditer(r"\{", raw):
        try:
            obj, _ = dec.raw_decode(raw[m.start():])
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            return obj
    raise InvalidLLMJsonError("nema validnog JSON objekta u outputu")
    # /TEACH


def validate_required_fields(data: dict, required: list) -> None:
    # TEACH d11: validate_required_fields
    missing = [f for f in required if f not in data]
    if missing:
        raise InvalidLLMJsonError(f"nedostaju polja: {', '.join(missing)}")
    # /TEACH


def validate_length(value, max_len: int) -> bool:
    # TEACH d11: validate_length
    return len(str(value)) <= max_len
    # /TEACH


def validate_product_facts(generated_text: str, product: dict) -> list:
    # TEACH d11: validate_product_facts
    text = set(significant_tokens(generated_text)); missing = []
    for fact in ("name", "category"):
        toks = significant_tokens(product.get(fact) or "")
        if toks and not set(toks) <= text:
            missing.append(fact)
    return missing
    # /TEACH


def validate_generated_output(data: dict, product: dict) -> dict:
    # TEACH d11: validate_generated_output
    title, desc = str(data.get("seo_title", "")), str(data.get("seo_description", ""))
    checks = {"fields_ok": all(f in data for f in SEO_FIELDS), "title_ok": validate_length(title, TITLE_MAX),
              "desc_ok": validate_length(desc, DESC_MAX),
              "facts_ok": not validate_product_facts(f"{title} {desc}", product)}
    checks["valid"] = all(checks.values())
    checks.update(title_len=len(title), desc_len=len(desc))
    return checks
    # /TEACH


def generate_with_retry(provider: AIProvider, prompt: str, *, max_retries: int = 2, schema=None,
                        required=None, trace: Optional[list] = None, validator=None, **kwargs) -> dict:
    # TEACH d11: generate_with_retry
    required = required or SEO_FIELDS; last = None
    for _attempt in range(max_retries + 1):  # bounded: 1 + max_retries pokušaja
        if trace is not None:
            trace.append(None)
        try:
            data = parse_json_output(provider.generate(prompt, **kwargs))
            validate_required_fields(data, required)
            if schema is not None:
                schema(**data)
            if validator is not None:  # npr. dužina/činjenice; neuspeh = novi pokušaj (i dalje bounded)
                validator(data)
            return data
        except Exception as e:  # nevalidan JSON / šema / provider greška -> sledeći pokušaj
            last = e
            if trace is not None:
                trace[-1] = f"{type(e).__name__}: {e}"[:200]
    raise GenerationFailSafeError(f"{max_retries + 1} pokušaja neuspešno: {last}")
    # /TEACH


def seo_prompt(p: dict) -> str:
    return ("Return ONLY a JSON object with keys seo_title (<=60 chars), seo_description (<=155 chars), "
            "keywords (list of 5). seo_title or seo_description must contain the exact product name and the exact "
            f"category name. Product: {p.get('name')}. Category: {p.get('category')}. "
            f"Description: {p.get('description')}.")


class AIService:
    def __init__(self, provider: Optional[AIProvider] = "default", max_retries: int = 2):
        self.provider = build_default_provider() if provider == "default" else provider
        self.max_retries = max_retries
        self.last_trace: list = []   # greške po pokušaju poslednjeg SEO poziva (None = uspeh)
        self.last_checks: dict = {}  # rezultat validate_generated_output poslednjeg poziva

    def template_seo(self, product: dict) -> SEOResponse:
        t = template_seo_metadata(product.get("name", ""), product.get("description", ""),
                                  product.get("category", ""))
        return SEOResponse(**t, source="template")

    def _fallback(self, product, reason) -> SEOResponse:
        r = self.template_seo(product); r.fallback = True; r.fallback_reason = reason
        return r

    def generate_seo_metadata(self, product: dict) -> SEOResponse:
        # TEACH d11: AIService.generate_seo_metadata
        if not product.get("name", "").strip():
            raise ValueError("product name je obavezan")
        if self.provider is None or not self.provider.available():
            return self._fallback(product, "model_unavailable")
        if isinstance(self.provider, DemoProvider):
            self.provider.product = product
        self.last_trace = []

        def _validate(d):
            self.last_checks = validate_generated_output(d, product)
            if not self.last_checks["valid"]:
                bad = [k for k in ("fields_ok", "title_ok", "desc_ok", "facts_ok") if not self.last_checks[k]]
                raise InvalidLLMJsonError(f"validacija: {', '.join(bad)}")
        try:
            data = generate_with_retry(self.provider, seo_prompt(product), max_retries=self.max_retries,
                                       schema=SEOResponse, trace=self.last_trace, validator=_validate)
        except GenerationFailSafeError:
            return self._fallback(product, "invalid_llm_output")
        kw = data["keywords"] if isinstance(data["keywords"], list) else str(data["keywords"]).split(",")
        return SEOResponse(seo_title=data["seo_title"], seo_description=data["seo_description"],
                           keywords=[str(k).strip() for k in kw], source=self.provider.descriptor()["name"],
                           raw=json.dumps(data, ensure_ascii=False))
        # /TEACH

    def _content(self, kind, prompt, template_text, required_tokens) -> ContentResponse:
        if self.provider is None or not self.provider.available() or isinstance(self.provider, DemoProvider):
            return ContentResponse(content=template_text, kind=kind, fallback=True,
                                   fallback_reason="model_unavailable")
        for _ in range(self.max_retries + 1):
            try:
                txt = self.provider.generate(prompt).strip()
            except Exception:
                continue
            if txt and set(required_tokens) <= set(significant_tokens(txt)):
                return ContentResponse(content=txt, kind=kind, source=self.provider.descriptor()["name"])
        return ContentResponse(content=template_text, kind=kind, fallback=True, fallback_reason="invalid_llm_output")

    def generate_product_description(self, product: dict) -> ContentResponse:
        n, d, c = product.get("name", ""), product.get("description", ""), product.get("category", "")
        return self._content("product_description", f"Write a 2-sentence product description for {n} ({c}). {d}",
                             template_product_description(n, d, c), significant_tokens(n))

    def generate_campaign_copy(self, campaign: dict) -> ContentResponse:
        n, g, a = campaign.get("name", ""), campaign.get("goal", ""), campaign.get("target_segments", "")
        return self._content("campaign_copy", f"Write short marketing copy for campaign '{n}'. Goal: {g}. Audience: {a}.",
                             template_campaign_copy(n, g, a), [])
