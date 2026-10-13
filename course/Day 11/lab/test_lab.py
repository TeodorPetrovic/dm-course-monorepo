import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import json


class Scripted(lab.AIProvider):
    def __init__(self, outputs):
        self.outputs = list(outputs); self.calls = 0

    def generate(self, prompt, **kw):
        self.calls += 1
        return self.outputs[min(self.calls - 1, len(self.outputs) - 1)]

    def available(self):
        return True

    def descriptor(self):
        return {"name": "scripted"}


GOOD = '```json\n{"seo_title": "T", "seo_description": "D", "keywords": ["k"]}\n``` hvala!'


def test_parse_json_output():
    assert lab.parse_json_output(GOOD)["seo_title"] == "T"
    assert lab.parse_json_output('Evo: {"a": {"b": 1}} kraj') == {"a": {"b": 1}}
    with pytest.raises(lab.InvalidLLMJsonError):
        lab.parse_json_output("nema json-a")


def test_validators():
    with pytest.raises(lab.InvalidLLMJsonError):
        lab.validate_required_fields({"seo_title": 1}, ["seo_title", "keywords"])
    lab.validate_required_fields({"keywords": 1, "seo_title": 2}, ["seo_title", "keywords"])  # redosled nebitan
    assert lab.validate_length("x" * 60, 60) and not lab.validate_length("x" * 61, 60)
    p = {"name": "Lamp 1952", "category": "Home"}
    assert lab.validate_product_facts("Home — najbolje cene", p) == ["name"]
    assert lab.validate_product_facts("Lamp 1952 | Home", p) == []


def test_malformed_json_retried_then_rejected():
    prov = Scripted(["I'm sorry"])
    with pytest.raises(lab.GenerationFailSafeError):
        lab.generate_with_retry(prov, "p", max_retries=2)
    assert prov.calls == 3


def test_retry_recovers():
    prov = Scripted(["junk", GOOD])
    assert lab.generate_with_retry(prov, "p", max_retries=2)["keywords"] == ["k"] and prov.calls == 2


def test_external_provider_without_network(monkeypatch):
    sent = {}

    def fake_post(url, payload, headers):
        sent.update(url=url, payload=payload, headers=headers)
        return 200, json.dumps({"choices": [{"message": {"content": "  hi  "}}]})
    monkeypatch.setattr(lab, "http_post", fake_post)
    p = lab.ExternalProvider("https://api.example.com/v1/", "sk-test", "m")
    assert p.available() and p.descriptor() == {"name": "external", "base_url": "https://api.example.com/v1", "model": "m"}
    assert p.generate("x") == "hi" and sent["url"].endswith("/chat/completions")
    assert not lab.ExternalProvider("", "").available()
    monkeypatch.setattr(lab, "http_post", lambda *a: (500, "err"))
    with pytest.raises(Exception):
        p.generate("x")
