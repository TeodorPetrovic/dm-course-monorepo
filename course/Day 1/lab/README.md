# Lab — Dan 1: implementacija event sloja i konverzije

Ovaj lab je **vođena praksa**: ponovo implementiraš mali deo onoga što kursni
modul `dm-ml/app/data/` već sadrži (da bi razumeo *šta* ti moduli rade). Ne
menjaš `dm-ml` — radiš u `starter.py` i proveravaš svoje rešenje.

Cilj: do kraja lab-a tvoj `starter.py` prolazi `test_lab.py`.

## Preduslovi

* Python 3 + `pandas` (`pip install pandas` ili `.venv` iz `dm-ml/`).
* Generisan seeded dataset: `Day 1/data/events.csv` (već postoji u repou;
  regenerišeš sa `python -m app.data.generate_dataset --seed 42` iz `dm-ml/`).

## Zadatak (koraci)

1. **`create_event`** — vrati dict događaja sa normalizovanim `timestamp`
   (format `YYYY-MM-DD HH:MM:SS`), podrazumevanim `source` po tipu, i
   `quantity >= 1`. Nepoznat `event_type` -> `ValueError`.
2. **`EventStore.save_event`** — dodeli `event_id` (sledeći), dodaj red u
   `self.events` i vrati sačuvan dict. Ovo je **round-trip ugovor**.
3. **Upiti** — `get_session_events`, `get_product_events`, `get_customer_events`
   (filter po koloni; sort po `timestamp`).
4. **`calculate_funnel_counts` i `calculate_conversion_rate`** —
   konverzija = sesije sa kupovinom / sve sesije; prazan dataset -> `0.0`.
5. **Vežba (nezavisna):** dodaj `average_order_value(orders)` (prosek
   `total_price`) i upit `get_search_events(store)` (svi `search` događaji).

## Provera

```
# iz Day 1/lab/ — testira tvoj starter
python3 -m pytest test_lab.py

# uporedi sa referentnim rešenjem (odgovor je na kraju lab-a)
LAB_MODULE=reference_solutions python3 -m pytest test_lab.py
```

## Šta radiš, a šta ne

* Radiš: ručnu implementaciju skladišta i analitike nad CSV-om.
* Ne radiš: MySQL, API, generator — to je u `dm-ml/` i koristi se u narednim
  danima. Generator je *jedini izvor istine* za podatke; ovaj lab ga samo čita.

## Rešenje

Pogledaj `reference_solutions.py` — ali prvo probaj sam.
