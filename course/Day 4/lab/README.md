# Lab — Dan 4: prediction-vs-decision, eligibilnost i rangiranje publike

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/` već sadrži (da bi razumeo *šta* ti moduli rade). Ne menjaš
`dm-ml` — radiš u `starter.py` i proveravaš svoje rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` (`dm-ml/.venv` ih ima).
* Lab radi na malim, ručno napravljenim profilima — nema seeded CSV-a.

## Zadatak (koraci)

Kampanja je dict pravila (`target_segments`, `eligible_buckets`,
`min_probability`, `min_monetary`, `cost_per_contact`, `max_contacts`). Profil
je DataFrame po korisniku (`user_id`, `segment`, `rfm_bucket`, `probability`,
`monetary`). Pomoćna funkcija `_eligibility` je data (vraća
`(eligible, reasons)`).

1. **`score_customer(probability, segment, rfm_bucket, monetary, campaign)`** —
   skor odluke za jednog korisnika:

   * Neeligibilan -> `{"eligible": False, "score": 0.0, "expected_value": 0.0, "reasons": [...]}`.
   * Eligibilan -> `expected_value = probability*monetary − cost_per_contact`
     (zaokruži na 4 decimale), `score = expected_value`, i dodaj razlog
     `f"očekivana vrednost = {p}*{value} - {cost} = {ev}"`.
   * Ovo je **prediction-vs-decision**: korisnik sa najvećom verovatnoćom nije
     nužno najbolja odluka (npr. P=0.9×100 < P=0.6×400).
2. **`select_target_customers(profiles, campaign)`** — primeni pravila na ceo
   profil (koristi `_eligibility` red-po-red), zadrži samo eligibilne, dodaj
   kolonu `selected_reasons`, sortiraj po `user_id`. Prazan ulaz -> prazan
   DataFrame.
3. **`rank_target_customers(selected, campaign, limit=None)`** — izračunaj
   `score_customer` za svaku vrstu, sortiraj po `score` opadajuće (tie-break po
   `user_id`), dodaj `rank` 1..N, klipuj `limit` na `max_contacts` i vrati
   `head` najboljih sa kolonama `rank`, `user_id`, `score`, `expected_value`,
   `probability`, `segment`, `rfm_bucket`, `monetary`, `reasons`.
4. **`rule_based_score(rfm_bucket, monetary)`** — rule baseline bez ML-a:
   `BUCKET_PRIORITY[rfm_bucket] * 1_000_000 + monetary`.

## Provera

```
# iz Day 4/lab/ — testira tvoj starter
python3 -m pytest test_lab.py

# uporedi sa referentnim rešenjem (odgovor je na kraju lab-a)
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Šta radiš, a šta ne

* Radiš: eligibilnost + skor odluke (očekivana vrednost), selektovanje po
  pravilima, rangiranje + limita, rule-based baseline.
* Ne radiš: ceo `dm-ml` servis, API, modele (segment/konverzija), perzistenciju,
  `compare_rule_vs_ml` — to koristi tvoje funkcije u `app/ml/` i servisu.
  `_eligibility` je data (kao što je `build_features` bio dat u Day 3 lab-u).

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
