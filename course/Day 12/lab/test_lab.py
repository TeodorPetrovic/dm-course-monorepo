import importlib
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
lab = importlib.import_module(os.environ.get("LAB_MODULE", "starter"))
import json

REG = json.loads((Path(__file__).resolve().parents[1] / "data" / "module-registry.json").read_text())


def test_classify_matches_registry():
    for m in REG["modules"]:
        if m["id"] in lab.TAXONOMY:
            assert lab.classify(m["id"]) == m["class"], m["id"]
    assert lab.classify("rfm") == lab.RULE and lab.classify("embeddings") == lab.ML
    with pytest.raises(ValueError):
        lab.classify("nope")


def test_fallbacks_named():
    assert "popularity" in lab.fallback_for("no_session_signal")
    assert lab.fallback_for("zero_impressions").startswith("ctr=0.0")
    with pytest.raises(ValueError):
        lab.fallback_for("nope")


def test_select_module_flywheel():
    assert lab.select_module("recommend_for_user") == "hybrid"
    for t, mid in lab.TASKS.items():
        assert lab.select_module(t) in lab.TAXONOMY
    with pytest.raises(ValueError):
        lab.select_module("nope")
