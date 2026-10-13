"""Putanje do kursnih podataka.

``package_root()`` = direktorijum ``dm-ml/``; kursni dani su njegovi
susedi (``../Day N/``) ili, u monorepu, ``<repo>/course/Day N``. ``DM_DATA_DIR`` menja direktorijum Day 1 podataka.
"""
from __future__ import annotations

import os
from pathlib import Path


def package_root() -> Path:
    return Path(__file__).resolve().parents[2]


def course_root() -> Path:
    """Folder sa ``Day N/``: ``DM_COURSE_ROOT``, inače sused od ``dm-ml/`` (kurs), inače ``<repo>/course`` (monorepo)."""
    env = os.environ.get("DM_COURSE_ROOT")
    if env:
        return Path(env)
    pr = package_root()
    if (pr.parent / "Day 1").is_dir():
        return pr.parent
    mono = pr.parents[1] / "course"
    return mono if (mono / "Day 1").is_dir() else pr.parent


def day_dir(day: int) -> Path:
    return course_root() / f"Day {day}"


def data_dir() -> Path:
    env = os.environ.get("DM_DATA_DIR")
    return Path(env) if env else day_dir(1) / "data"


def dataset_path(name: str) -> Path:
    return data_dir() / name


def day_data(day: int, name: str) -> Path:
    return day_dir(day) / "data" / name


def models_dir() -> Path:
    env = os.environ.get("DM_MODELS_DIR")
    p = Path(env) if env else package_root() / "app" / "models"
    p.mkdir(parents=True, exist_ok=True)
    return p
