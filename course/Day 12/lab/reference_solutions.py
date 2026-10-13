"""Referentno rešenje Day 12 lab-a."""
from __future__ import annotations

from starter import (DATA_PIPELINE, EVAL, FALLBACKS, GENAI, ML, RULE, STATISTICAL, TASKS,  # noqa: F401
                     TAXONOMY)


def _lookup(table, key, what):
    if key not in table:
        raise ValueError(f"nepoznat {what}: {key!r}")
    return table[key]


def classify(component_id):
    return _lookup(TAXONOMY, component_id, "komponenta")


def fallback_for(failure_code):
    return _lookup(FALLBACKS, failure_code, "scenario")


def select_module(task):
    return _lookup(TASKS, task, "zadatak")
