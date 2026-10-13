"""Day 4 — jedini izvor definicija kampanja (seeded).

PAŽNJA: K-Means labele (segment_0..3) su proizvoljne — ``target_segments`` važe za model treniran na seed-u 42
(k=4, random_state=42). Posle promene podataka ili parametara proverite profile segmenata (GET /segments).
"""
from __future__ import annotations

import copy
import json

import pandas as pd

from app.data.paths import day_data

CAMPAIGNS = [
    {"campaign_id": 1, "name": "VIP reaktivacija",
     "description": "Ciljaj najvrednije K-Means segmente (segment_2 + segment_3: visok frequency/monetary u seed-u 42) i visoke RFM bucket-e; kontakt košta 0.5, očekivani prihod po konverziji 60.",
     "goal": "Reaktiviraj najvrednije korisnike", "target_segments": ["segment_2", "segment_3"],
     "eligible_buckets": ["champions", "loyal"], "min_probability": 0.2, "min_monetary": 50.0,
     "cost_per_contact": 0.5, "expected_revenue": 60.0, "budget": 150.0, "max_contacts": 200,
     "status": "active", "notes": "ML-assisted: prag verovatnoće + ciljani segmenti."},
    {"campaign_id": 2, "name": "At-risk win-back",
     "description": "Korisnici koji klize (rfm at_risk; K-Means segment_0 = najduži recency u seed-u 42). Nizak prag verovatnoće, jeftiniji kontakt.",
     "goal": "Vrati korisnike koji klize", "target_segments": ["segment_0"],
     "eligible_buckets": ["at_risk"], "min_probability": 0.15, "min_monetary": 0.0,
     "cost_per_contact": 0.3, "expected_revenue": 30.0, "budget": 90.0, "max_contacts": 300,
     "status": "active", "notes": "ML-assisted: segment filter + nizak prag."},
    {"campaign_id": 3, "name": "Široka visoko-vrednosna kampanja",
     "description": "Svi osim dormant-a; nizak prag verovatnoće (0.10) i jeftin kontakt (0.2).",
     "goal": "Širok doseg visoko-vrednosnih korisnika", "target_segments": [],
     "eligible_buckets": ["champions", "loyal", "at_risk"], "min_probability": 0.1,
     "min_monetary": 0.0, "cost_per_contact": 0.2, "expected_revenue": 35.0, "budget": 100.0,
     "max_contacts": 500, "status": "active",
     "notes": "ML-assisted: samo prag verovatnoće (bez segment filtera)."},
    {"campaign_id": 4, "name": "Dormant re-engage (pravila)",
     "description": "Pravilima-only kampanja: dormant bucket, BEZ praga verovatnoće (min_probability=0). Pokazuje kako rule targeting radi bez modela.",
     "goal": "Pokušaj povratka dormant korisnika po najnižoj ceni", "target_segments": [],
     "eligible_buckets": ["dormant"], "min_probability": 0.0, "min_monetary": 0.0,
     "cost_per_contact": 0.1, "expected_revenue": 15.0, "budget": 15.0, "max_contacts": 150,
     "status": "active", "notes": "Rule-only: nema verovatnoće — rangira se po RFM/vrednosti."},
]


def load_campaigns() -> list[dict]:
    return copy.deepcopy(CAMPAIGNS)


def get_campaign(campaign_id: int):
    return next((c for c in load_campaigns() if c["campaign_id"] == int(campaign_id)), None)


def campaigns_dataframe() -> pd.DataFrame:
    df = pd.DataFrame(load_campaigns())
    for c in ("target_segments", "eligible_buckets"):
        df[c] = df[c].map(lambda v: json.dumps(v, ensure_ascii=False))
    return df


def write_campaigns_csv(path=None):
    path = path or day_data(4, "campaigns.csv")
    campaigns_dataframe().to_csv(path, index=False, lineterminator="\n")
    return path
