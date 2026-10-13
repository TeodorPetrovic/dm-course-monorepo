"""Referentno rešenje Day 11 lab-a."""
from __future__ import annotations

import json
import re
import urllib.error
import urllib.request

from starter import (STOPWORDS, AIProvider, GenerationFailSafeError, InvalidLLMJsonError,  # noqa: F401
                     _significant_tokens)
import starter as _s

SEO_FIELDS = ["seo_title", "seo_description", "keywords"]


def parse_json_output(raw):
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
    raise InvalidLLMJsonError("nema validnog JSON objekta")


def validate_required_fields(data, required):
    miss = [f for f in required if f not in data]
    if miss:
        raise InvalidLLMJsonError(f"nedostaju polja: {', '.join(miss)}")


def validate_length(value, max_len):
    return len(str(value)) <= max_len


def validate_product_facts(generated_text, product):
    toks = set(_significant_tokens(generated_text)); missing = []
    for fact in ("name", "category"):
        need = _significant_tokens(product.get(fact) or "")
        if need and not set(need) <= toks:
            missing.append(fact)
    return missing


def generate_with_retry(provider, prompt, *, max_retries=2, **kwargs):
    last = None
    for _ in range(max_retries + 1):          # 1 pokušaj + max_retries ponavljanja
        try:
            data = parse_json_output(provider.generate(prompt))
            validate_required_fields(data, kwargs.get("required", SEO_FIELDS))
            return data
        except Exception as e:
            last = e
    raise GenerationFailSafeError(f"iscrpljeno {max_retries + 1} pokušaja: {last}")


def http_post(url, payload, headers):
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), method="POST",
                                 headers={"Content-Type": "application/json", **headers})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")
    except urllib.error.URLError as e:
        raise ConnectionError(str(e.reason)) from e


class ExternalProvider(_s.ExternalProvider):
    def available(self):
        return bool(self.base_url and self.api_key)

    def descriptor(self):
        return {"name": "external", "base_url": self.base_url, "model": self.model}

    def generate(self, prompt, *, max_tokens=256, temperature=0.5):
        status, body = http_post(f"{self.base_url}/chat/completions",
                                 {"model": self.model, "messages": [{"role": "user", "content": prompt}],
                                  "max_tokens": max_tokens, "temperature": temperature},
                                 {"Authorization": f"Bearer {self.api_key}"})
        if status != 200:
            raise RuntimeError(f"HTTP {status}")
        return json.loads(body)["choices"][0]["message"]["content"].strip()
