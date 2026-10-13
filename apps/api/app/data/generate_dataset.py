"""Deterministički, realističan generator Day 1 dataseta (v2, 2026-10-13).

Simulira mesec dana (januar 2026) e-commerce prodavnice:

* **katalog** — 12 kategorija x 21 proizvod; cene po tipu proizvoda u realnim
  opsezima (EUR, log-uniformno), opisi sa atributima (materijal, namena, ...);
* **kupci** — 5 preklapajućih persona (sekundarna persona, šum), novi korisnici
  se pridružuju tokom meseca;
* **sezonalnost** — 1. januar slab, zimsko sniženje 2.–6. januara (popusti na deo
  kataloga), pad za Božić 7. januara, vikendi jači, vrhovi u podne i uveče;
* **sesije** — ulaz (search / kategorija / shop / direktno), lanac pregleda koji
  se drži kategorije ili prelazi u srodnu (afinitet kategorija), log-normalno
  vreme između događaja (< 30 min), preporuke „top u kategoriji“ sa position-bias
  CTR-om;
* **levak** — korpa zavisi od persone i uklapanja cene, napuštanje korpe ~60–75%,
  korpa sa više stavki (komplementarni proizvodi: laptop -> miš ...), ponovne
  kupovine u srodnim kategorijama.

``orders.csv`` ima **jedan red po stavci**; stavke iste porudžbine dele
``order_id`` (``frequency`` = broj različitih ``order_id``).
Determinizam: ``numpy.random.default_rng(seed + offset)`` po delu; dva pokretanja
sa istim seed-om daju identične bajtove (sha256 u ``metadata.json``).

Pokretanje: ``python -m app.data.generate_dataset --seed 42``
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import pandas as pd

from app.data.paths import data_dir

WINDOW_START = pd.Timestamp("2026-01-01")
N_DAYS = 31
N_CUSTOMERS = 3000
EVENT_COLUMNS = ["event_id", "event_type", "user_id", "user_session", "product_id",
                 "category_id", "price", "quantity", "source", "timestamp",
                 "recommendation_source", "recommendation_position"]

# (naziv, slug, relativni saobraćaj, [(tip, cena_od, cena_do, opis), ...])
CATALOG = [
    ("Electronics", "electronics", 1.6, [
        ("Smartphone", 179, 999, "5G smartphone with OLED display, dual camera and fast charging"),
        ("Laptop", 449, 1599, "lightweight laptop for work and study, SSD storage, long battery life"),
        ("Headphones", 25, 299, "wireless over-ear headphones with noise cancelling and 30h battery"),
        ("Tablet", 149, 799, "10-inch tablet for streaming, reading and video calls"),
        ("Monitor", 119, 549, "27-inch IPS monitor, full HD, slim bezel, for office and gaming"),
        ("Keyboard", 19, 149, "mechanical keyboard with backlight, quiet switches"),
        ("Mouse", 9, 79, "ergonomic wireless mouse with silent clicks"),
        ("Speaker", 29, 249, "portable bluetooth speaker, waterproof, deep bass"),
        ("Camera", 299, 1299, "mirrorless camera with 4K video and interchangeable lens"),
        ("Smartwatch", 59, 399, "fitness smartwatch with heart rate, GPS and sleep tracking")]),
    ("Fashion", "fashion", 1.4, [
        ("Jacket", 49, 249, "warm winter jacket, water-repellent, hooded"),
        ("Jeans", 29, 119, "slim fit denim jeans, stretch cotton"),
        ("Sneakers", 39, 179, "everyday sneakers, breathable mesh, cushioned sole"),
        ("Dress", 25, 149, "midi dress for office and evening, soft fabric"),
        ("T-shirt", 8, 39, "basic cotton t-shirt, regular fit"),
        ("Scarf", 9, 59, "knitted wool scarf for winter"),
        ("Belt", 12, 69, "genuine leather belt with metal buckle"),
        ("Backpack", 25, 129, "city backpack with laptop sleeve, water-resistant"),
        ("Cap", 9, 35, "cotton baseball cap, adjustable"),
        ("Boots", 59, 219, "leather winter boots, non-slip sole")]),
    ("Books", "books", 0.8, [
        ("Novel", 9, 25, "bestselling contemporary novel, paperback"),
        ("Thriller", 9, 22, "crime thriller, gripping page-turner"),
        ("Cookbook", 15, 45, "cookbook with healthy everyday recipes"),
        ("Biography", 12, 35, "biography of a famous entrepreneur"),
        ("Fantasy", 10, 29, "epic fantasy saga, first book in the series"),
        ("Textbook", 25, 89, "university textbook on marketing and statistics"),
        ("Guide", 12, 30, "travel guide with maps and itineraries"),
        ("Children's Book", 6, 19, "illustrated picture book for children"),
        ("Poetry", 8, 20, "collection of modern poetry"),
        ("Dictionary", 15, 49, "English-Serbian dictionary, updated edition")]),
    ("Sports", "sports", 1.0, [
        ("Running Shoes", 49, 179, "running shoes with responsive cushioning"),
        ("Yoga Mat", 15, 69, "non-slip yoga mat, eco-friendly material"),
        ("Dumbbell Set", 29, 199, "adjustable dumbbell set for home workouts"),
        ("Bicycle", 249, 1199, "city and trekking bicycle, aluminium frame, 21 gears"),
        ("Tent", 59, 349, "lightweight camping tent for two, waterproof"),
        ("Football", 15, 49, "official size football, durable"),
        ("Tennis Racket", 39, 229, "graphite tennis racket for intermediate players"),
        ("Sports Bottle", 6, 29, "insulated sports water bottle, leak-proof"),
        ("Fitness Band", 9, 39, "resistance bands set for strength training"),
        ("Ski Gloves", 19, 79, "insulated ski gloves, waterproof")]),
    ("Home", "home", 1.1, [
        ("Blender", 29, 179, "kitchen blender for smoothies and soups"),
        ("Coffee Maker", 39, 399, "espresso coffee maker with milk frother"),
        ("Table Lamp", 15, 99, "LED table lamp with dimmer, warm light"),
        ("Bedding Set", 25, 119, "cotton bedding set, soft and breathable"),
        ("Towel Set", 15, 69, "absorbent bath towel set"),
        ("Cookware Set", 49, 299, "non-stick cookware set, induction compatible"),
        ("Rug", 29, 249, "soft living room rug, easy to clean"),
        ("Vacuum Cleaner", 79, 449, "bagless vacuum cleaner with HEPA filter"),
        ("Kettle", 15, 79, "electric kettle, 1.7 litre, auto shut-off"),
        ("Candle", 5, 29, "scented candle, vanilla and amber")]),
    ("Beauty", "beauty", 1.0, [
        ("Face Cream", 9, 79, "hydrating face cream for daily use"),
        ("Serum", 12, 89, "vitamin C serum for radiant skin"),
        ("Shampoo", 4, 25, "nourishing shampoo for dry hair"),
        ("Perfume", 29, 149, "eau de parfum, floral and woody notes"),
        ("Lipstick", 7, 39, "long-lasting matte lipstick"),
        ("Hair Dryer", 25, 199, "ionic hair dryer, fast drying"),
        ("Body Lotion", 5, 29, "body lotion with shea butter"),
        ("Sunscreen", 8, 35, "sunscreen SPF 50, water-resistant"),
        ("Makeup Brush Set", 9, 49, "makeup brush set, soft synthetic bristles"),
        ("Beard Trimmer", 19, 99, "rechargeable beard trimmer with combs")]),
    ("Toys", "toys", 0.8, [
        ("Building Blocks", 15, 129, "building blocks set, creative construction toy"),
        ("Board Game", 15, 59, "family board game for 2-6 players"),
        ("Puzzle", 8, 35, "1000-piece jigsaw puzzle"),
        ("Doll", 12, 59, "fashion doll with accessories"),
        ("RC Car", 25, 149, "remote control car, rechargeable"),
        ("Plush Toy", 8, 39, "soft plush teddy bear"),
        ("Robot Kit", 39, 199, "programmable robot kit, STEM learning"),
        ("Paint Set", 9, 39, "kids paint set with brushes"),
        ("Toy Train", 19, 99, "wooden toy train set"),
        ("Card Game", 5, 19, "fast card game for kids and adults")]),
    ("Food", "food", 0.9, [
        ("Coffee Beans", 8, 29, "arabica coffee beans, medium roast"),
        ("Green Tea", 4, 15, "organic green tea, loose leaf"),
        ("Dark Chocolate", 2, 9, "dark chocolate 70% cocoa"),
        ("Olive Oil", 7, 25, "extra virgin olive oil, cold pressed"),
        ("Honey", 6, 19, "natural forest honey"),
        ("Pasta", 2, 7, "durum wheat pasta"),
        ("Granola", 4, 12, "crunchy granola with nuts and honey"),
        ("Spice Set", 9, 35, "gourmet spice set for grilling and cooking"),
        ("Protein Bar Box", 12, 35, "protein bars box, 12 pieces"),
        ("Juice", 2, 6, "fresh orange juice, no added sugar")]),
    ("Furniture", "furniture", 0.7, [
        ("Sofa", 349, 1499, "three-seat sofa, fabric upholstery"),
        ("Office Chair", 79, 449, "ergonomic office chair with lumbar support"),
        ("Desk", 99, 499, "home office desk, wooden top"),
        ("Bookshelf", 49, 249, "five-tier bookshelf"),
        ("Bed Frame", 199, 899, "double bed frame with storage"),
        ("Wardrobe", 199, 799, "two-door wardrobe with mirror"),
        ("Coffee Table", 49, 299, "coffee table, oak finish"),
        ("Nightstand", 39, 179, "nightstand with drawer"),
        ("Dining Chair", 39, 149, "upholstered dining chair"),
        ("Armchair", 129, 599, "reading armchair, velvet")]),
    ("Automotive", "automotive", 0.6, [
        ("Winter Tires", 59, 199, "winter tire, excellent grip on snow and ice"),
        ("Car Battery", 69, 199, "12V car battery, long life"),
        ("Dash Cam", 39, 199, "full HD dash cam with night vision"),
        ("Phone Holder", 9, 35, "magnetic car phone holder"),
        ("Car Charger", 9, 29, "fast USB-C car charger"),
        ("Floor Mats", 19, 79, "rubber car floor mats, all-weather"),
        ("Engine Oil", 19, 59, "synthetic engine oil 5W-30"),
        ("Ice Scraper", 4, 15, "ice scraper with snow brush"),
        ("Car Vacuum", 25, 89, "handheld car vacuum cleaner"),
        ("Jump Starter", 49, 149, "portable jump starter with power bank")]),
    ("Music", "music", 0.5, [
        ("Acoustic Guitar", 99, 599, "acoustic guitar, spruce top"),
        ("Digital Piano", 299, 999, "88-key digital piano with weighted keys"),
        ("Guitar Strings", 6, 25, "steel guitar strings, light gauge"),
        ("Studio Headphones", 59, 299, "closed-back studio monitoring headphones"),
        ("Microphone", 39, 249, "USB condenser microphone for podcasts and vocals"),
        ("Guitar Amp", 79, 399, "practice guitar amplifier, 20W"),
        ("Ukulele", 29, 129, "soprano ukulele for beginners"),
        ("Drum Sticks", 7, 25, "hickory drum sticks"),
        ("Music Stand", 15, 49, "foldable music stand"),
        ("Effects Pedal", 39, 199, "distortion effects pedal")]),
    ("Tools", "tools", 0.6, [
        ("Cordless Drill", 49, 249, "cordless drill driver with two batteries"),
        ("Screwdriver Set", 12, 59, "precision screwdriver set"),
        ("Hammer", 9, 39, "claw hammer with fiberglass handle"),
        ("Tape Measure", 5, 25, "5 metre tape measure"),
        ("Toolbox", 25, 129, "toolbox with 100 hand tools"),
        ("Ladder", 49, 199, "aluminium step ladder"),
        ("Circular Saw", 79, 299, "circular saw, 1200W"),
        ("Spirit Level", 8, 35, "spirit level, 60 cm"),
        ("Work Gloves", 5, 25, "protective work gloves"),
        ("Glue Gun", 12, 39, "hot glue gun with glue sticks")]),
]
MATERIALS = ["premium", "classic", "eco", "compact", "pro", "everyday", "deluxe", "essential"]
COLORS = ["black", "white", "grey", "blue", "red", "green", "beige", "silver"]
# srodne kategorije (kategorija -> [(srodna, težina)])
AFFINITY = {1: [(11, 3), (9, 1), (10, 1)], 2: [(6, 3), (4, 2)], 3: [(7, 3), (11, 1)],
            4: [(2, 3), (8, 2)], 5: [(9, 3), (8, 2), (6, 1)], 6: [(2, 3), (5, 1)],
            7: [(3, 3), (1, 1)], 8: [(5, 3), (4, 1)], 9: [(5, 3), (12, 1)],
            10: [(12, 3), (1, 1)], 11: [(1, 3), (3, 1)], 12: [(10, 2), (9, 2), (5, 1)]}
# komplementarni tipovi (co-purchase): tip -> tipovi
COMPLEMENT = {
    "Laptop": ["Mouse", "Keyboard", "Monitor", "Backpack"], "Smartphone": ["Headphones", "Smartwatch", "Car Charger", "Phone Holder"],
    "Tablet": ["Keyboard", "Headphones"], "Camera": ["Backpack"], "Monitor": ["Keyboard", "Mouse"],
    "Jacket": ["Scarf", "Boots", "Ski Gloves"], "Jeans": ["Belt", "T-shirt", "Sneakers"], "Dress": ["Perfume", "Lipstick"],
    "Sneakers": ["Running Shoes", "T-shirt"], "Boots": ["Scarf"],
    "Cookbook": ["Spice Set", "Cookware Set", "Olive Oil"], "Children's Book": ["Plush Toy", "Puzzle", "Paint Set"],
    "Running Shoes": ["Sports Bottle", "Fitness Band", "Smartwatch"], "Yoga Mat": ["Fitness Band", "Sports Bottle"],
    "Dumbbell Set": ["Protein Bar Box", "Fitness Band"], "Bicycle": ["Sports Bottle"], "Tent": ["Sports Bottle"],
    "Tennis Racket": ["Sports Bottle"], "Coffee Maker": ["Coffee Beans"], "Kettle": ["Green Tea"],
    "Blender": ["Granola"], "Cookware Set": ["Olive Oil", "Pasta", "Spice Set"], "Bedding Set": ["Towel Set", "Candle"],
    "Face Cream": ["Serum", "Sunscreen"], "Serum": ["Face Cream"], "Shampoo": ["Hair Dryer", "Body Lotion"],
    "Lipstick": ["Makeup Brush Set"], "Board Game": ["Card Game", "Puzzle"], "Robot Kit": ["Building Blocks"],
    "Coffee Beans": ["Dark Chocolate", "Honey"], "Pasta": ["Olive Oil", "Spice Set"], "Green Tea": ["Honey"],
    "Sofa": ["Coffee Table", "Rug", "Armchair"], "Desk": ["Office Chair", "Table Lamp", "Monitor"],
    "Bed Frame": ["Nightstand", "Bedding Set"], "Office Chair": ["Desk"], "Bookshelf": ["Novel"],
    "Winter Tires": ["Ice Scraper"], "Car Battery": ["Jump Starter"], "Dash Cam": ["Car Charger", "Phone Holder"],
    "Acoustic Guitar": ["Guitar Strings", "Music Stand"], "Digital Piano": ["Music Stand", "Studio Headphones"],
    "Guitar Amp": ["Effects Pedal", "Guitar Strings"], "Microphone": ["Studio Headphones"], "Ukulele": ["Guitar Strings"],
    "Cordless Drill": ["Screwdriver Set", "Toolbox", "Work Gloves"], "Circular Saw": ["Work Gloves", "Spirit Level"],
    "Toolbox": ["Tape Measure", "Hammer"],
}
PERSONAS = ["occasional", "category_focused", "price_sensitive", "new_user", "high_value"]
PERSONA_SHARE = [0.32, 0.20, 0.19, 0.18, 0.11]
PERSONA_DEFS = {"high_value": "high-value frequent buyers", "price_sensitive": "price-sensitive bargain hunters",
                "category_focused": "category-focused enthusiasts", "occasional": "occasional visitors",
                "new_user": "new users"}
# sesije/mesec, pregledi/sesiji, p(korpa | pregled), p(checkout | korpa), ciljna cena (beta a,b), Dirichlet alfa
PARAMS = {
    "high_value":       dict(sessions=11.0, views=5.5, cart=0.048, checkout=0.45, price=(4.0, 2.0), alpha=0.45),
    "category_focused": dict(sessions=7.0, views=7.0, cart=0.034, checkout=0.32, price=(2.5, 2.5), alpha=0.12),
    "price_sensitive":  dict(sessions=6.5, views=8.0, cart=0.019, checkout=0.20, price=(1.3, 4.5), alpha=0.6),
    "occasional":       dict(sessions=2.6, views=3.5, cart=0.026, checkout=0.22, price=(2.0, 2.5), alpha=0.6),
    "new_user":         dict(sessions=2.8, views=4.5, cart=0.027, checkout=0.20, price=(2.0, 2.5), alpha=0.6),
}
SECONDARY_PROB, BLEND_PROB, PRICE_NOISE_PROB = 0.35, 0.25, 0.15
SALE_DAYS = {2, 3, 4, 5, 6}           # zimsko sniženje
REC_SLATE_PROB, REC_K = 0.22, 3
REC_CTR = [0.035, 0.02, 0.012]          # position bias
CART_ABANDON_REMOVE = 0.12
HOUR_W = np.array([2, 1, .6, .4, .4, .6, 1.2, 2.4, 3.6, 4.2, 4.6, 5.2, 6.0, 5.8, 5.0, 4.8, 5.0, 5.6,
                   6.6, 7.8, 8.6, 8.0, 6.0, 3.8], dtype=float)


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def day_weights() -> np.ndarray:
    """Relativni saobraćaj po danu januara 2026 (sezonalnost)."""
    w = []
    for d in range(1, N_DAYS + 1):
        dow = pd.Timestamp(2026, 1, d).dayofweek  # 0=pon
        x = 1.0 + (0.18 if dow >= 5 else 0.0) + (0.06 if dow == 0 else 0.0)
        if d == 1:
            x *= 0.55                     # Nova godina
        elif d in SALE_DAYS:
            x *= 1.45                     # zimsko sniženje
        elif d == 7:
            x *= 0.65                     # Božić (pravoslavni)
        elif d in (8, 9, 10):
            x *= 0.85                     # posle praznika
        elif d >= 25:
            x *= 1.12                     # posle plate
        w.append(x)
    w = np.array(w)
    return w / w.sum()


def build_catalog(rng):
    cats, prods = [], []
    pid = 0
    for cid, (name, slug, traffic, types) in enumerate(CATALOG, 1):
        cats.append({"category_id": cid, "name": name, "slug": slug})
        slots = [t for t in types for _ in range(2)] + [types[int(rng.integers(len(types)))]]
        for tname, lo, hi, desc in slots:
            pid += 1
            model = int(rng.integers(100, 999))
            series = MATERIALS[int(rng.integers(len(MATERIALS)))]
            color = COLORS[int(rng.integers(len(COLORS)))]
            price = float(np.exp(rng.uniform(np.log(lo), np.log(hi))))
            price = round(np.floor(price) + (0.99 if price >= 10 else 0.49), 2)
            nm = f"{tname} {series.capitalize()} {model}"
            sl = nm.lower().replace(" ", "-").replace("'", "")
            prods.append({"product_id": pid, "name": nm, "slug": sl,
                          "description": f"{desc[0].upper() + desc[1:]}. {series.capitalize()} line, {color}.",
                          "img_url": f"/images/products/{sl}.jpg", "category_id": cid, "price": price,
                          "created_at": (pd.Timestamp("2025-03-01") + pd.Timedelta(days=int(rng.integers(0, 270)))).strftime("%Y-%m-%d"),
                          "_type": tname, "_traffic": traffic})
    p = pd.DataFrame(prods)
    # popularnost: Zipf unutar kategorije (nasumičan rang) x saobraćaj kategorije
    p["_pop"] = 0.0
    for cid, g in p.groupby("category_id"):
        ranks = rng.permutation(len(g)) + 1
        p.loc[g.index, "_pop"] = g["_traffic"].iloc[0] / ranks ** 0.9
    # cena relativno unutar kategorije (0..1) za uklapanje cene
    p["_pq"] = p.groupby("category_id")["price"].rank(pct=True)
    return pd.DataFrame(cats), p


def build_customers(rng):
    rows, users = [], []
    for u in range(1, N_CUSTOMERS + 1):
        per = PERSONAS[int(rng.choice(5, p=PERSONA_SHARE))]
        sec = None
        if rng.random() < SECONDARY_PROB:
            sec = PERSONAS[int(rng.choice([i for i in range(5) if PERSONAS[i] != per]))]
        if per == "new_user":
            join = WINDOW_START + pd.Timedelta(days=int(rng.integers(0, N_DAYS - 1)))
        else:
            join = pd.Timestamp("2024-03-01") + pd.Timedelta(days=int(rng.integers(0, 640)))
        pref = rng.dirichlet(np.full(12, PARAMS[per]["alpha"]))
        price_target = rng.beta(*PARAMS[per]["price"])
        activity = rng.gamma(2.0, 0.5)  # per-korisnički jitter
        rows.append({"user_id": u, "name": f"Kupac {u:04d}", "email": f"user{u:04d}@example.test",
                     "join_date": join.strftime("%Y-%m-%d"), "persona": per, "secondary_persona": sec,
                     "blend_prob": BLEND_PROB if sec else 0.0})
        users.append({"u": u, "per": per, "sec": sec, "join": join, "pref": pref, "pt": price_target,
                      "act": activity})
    return pd.DataFrame(rows), users


def generate_dataset(seed: int = 42, out_dir: Path | None = None, write: bool = True) -> dict:
    out_dir = Path(out_dir) if out_dir else data_dir()
    rng_p = np.random.default_rng(seed + 1)
    rng_c = np.random.default_rng(seed + 0)
    rng_e = np.random.default_rng(seed + 2)
    cats, P = build_catalog(rng_p)
    cust, users = build_customers(rng_c)
    pid_arr = P["product_id"].to_numpy(); pcat = dict(zip(P.product_id, P.category_id))
    price = dict(zip(P.product_id, P.price)); ptype = dict(zip(P.product_id, P._type))
    by_cat = {c: g.index.to_numpy() for c, g in P.groupby("category_id")}
    by_type = {t: g["product_id"].to_numpy() for t, g in P.groupby("_type")}
    pop = P["_pop"].to_numpy(); pq = P["_pq"].to_numpy()
    cat_top = {c: list(P.loc[by_cat[c]].sort_values("_pop", ascending=False)["product_id"]) for c in by_cat}
    # sniženje: 30% kataloga 15–35% popusta tokom SALE_DAYS
    on_sale = {int(p): float(rng_p.uniform(0.15, 0.35)) for p in pid_arr if rng_p.random() < 0.30}
    dw = day_weights(); hw = HOUR_W / HOUR_W.sum()

    def ev_price(p, ts):
        d = on_sale.get(p)
        return round(price[p] * (1 - d), 2) if d and ts.day in SALE_DAYS else price[p]

    def pick_product(cat, u, noisy, avoid):
        idx = by_cat[cat]
        fit = np.exp(-((pq[idx] - u["pt"]) ** 2) / 0.08) if not noisy else np.ones(len(idx))
        w = pop[idx] * (0.15 + fit)
        if avoid:
            w = w * np.array([0.1 if pid_arr[i] in avoid else 1.0 for i in idx])
        i = idx[int(rng_e.choice(len(idx), p=w / w.sum()))]
        return int(pid_arr[i]), float(fit[list(idx).index(i)]) if not noisy else 0.5

    sessions = []
    for u in users:
        par = PARAMS[u["per"]]
        start_day = max(0, (u["join"] - WINDOW_START).days) if u["per"] == "new_user" else 0
        active_days = N_DAYS - start_day
        lam = par["sessions"] * u["act"] * active_days / N_DAYS
        n = max(1, int(rng_e.poisson(lam)))
        dws = dw[start_day:] / dw[start_day:].sum()
        days = np.sort(start_day + rng_e.choice(active_days, size=n, p=dws))
        for d in days:
            t = WINDOW_START + pd.Timedelta(days=int(d), hours=int(rng_e.choice(24, p=hw)),
                                            seconds=int(rng_e.integers(0, 3600)))
            sessions.append((t, u))
    sessions.sort(key=lambda x: (x[0], x[1]["u"]))

    rows = []
    last_bought_cat = {}
    order_seq = 0
    orders = []
    window_end = WINDOW_START + pd.Timedelta(days=N_DAYS) - pd.Timedelta(seconds=1)
    for sno, (t0, u) in enumerate(sessions, 1):
        sid = f"session_{sno:06d}"
        persona = u["per"]
        if u["sec"] and rng_e.random() < BLEND_PROB:
            persona = u["sec"]
        par = PARAMS[persona]
        t = t0
        evs = []

        def emit(et, p=None, c=None, q=1, src="product_page", rs=None, rp=None, gap=(3.4, 0.7)):
            nonlocal t
            if evs:
                t = t + pd.Timedelta(seconds=int(min(1500, max(2, rng_e.lognormal(*gap)))))
            pr = ev_price(p, t) if p is not None else None
            if p is not None:
                c = pcat[p]
            evs.append([et, u["u"], sid, p, c, pr, q, src, t, rs, rp])

        # namera sesije: preferirana kategorija ili srodna posle kupovine
        if u["u"] in last_bought_cat and rng_e.random() < 0.30:
            aff = AFFINITY[last_bought_cat[u["u"]]]
            cat = int(rng_e.choice([a for a, _ in aff], p=np.array([w for _, w in aff]) / sum(w for _, w in aff)))
        else:
            cat = int(rng_e.choice(12, p=u["pref"])) + 1
        n_views = max(1, int(round(rng_e.gamma(2.0, par["views"] / 2.0))))
        sale_boost = 1.2 if t0.day in SALE_DAYS else 1.0
        entry = rng_e.choice(["search", "category_page", "shop", "product_page"], p=[0.27, 0.35, 0.18, 0.20])
        src = str(entry)
        if entry == "search":
            emit("search", src="search_page")
            src = "search_page"
        elif entry == "category_page":
            emit("category_view", c=cat, src="category_page")
        cart, seen, forced = [], set(), None
        for k in range(n_views):
            if forced is not None:
                p, fit = forced, 0.8; forced_src = forced_s; forced = None
            else:
                r = rng_e.random()
                if k > 0 and r > 0.72:
                    if rng_e.random() < 0.6:
                        aff = AFFINITY[cat]
                        cat = int(rng_e.choice([a for a, _ in aff], p=np.array([w for _, w in aff]) / sum(w for _, w in aff)))
                    else:
                        cat = int(rng_e.choice(12, p=u["pref"])) + 1
                    if rng_e.random() < 0.35:
                        emit("category_view", c=cat, src="category_page")
                        src = "category_page"
                if k > 0 and rng_e.random() < 0.06:
                    emit("search", src="search_page"); src = "search_page"
                p, fit = pick_product(cat, u, rng_e.random() < PRICE_NOISE_PROB, seen)
                forced_src = src if k == 0 or src in ("category_page", "search_page") else \
                    str(rng_e.choice(["product_page", "category_page", "shop"], p=[0.6, 0.25, 0.15]))
            seen.add(p)
            emit("product_view", p, src=forced_src, gap=(3.6, 0.8))
            src = "product_page"
            # preporuke „top u kategoriji“ na product strani
            if rng_e.random() < REC_SLATE_PROB:
                recs = [q for q in cat_top[pcat[p]] if q != p][:REC_K]
                clicked = None
                for pos, q in enumerate(recs, 1):
                    emit("recommendation_impression", q, src="recommendation", rs="category", rp=pos, gap=(0.0, 0.3))
                for pos, q in enumerate(recs, 1):
                    rel = 1.3 if q not in seen else 0.5
                    if clicked is None and rng_e.random() < REC_CTR[pos - 1] * rel:
                        clicked = (q, pos)
                if clicked:
                    emit("recommendation_click", clicked[0], src="recommendation", rs="category", rp=clicked[1], gap=(2.5, 0.6))
                    forced, forced_s = clicked[0], "recommendation"
            # korpa
            pc = par["cart"] * (0.4 + fit) * sale_boost
            if p not in cart and rng_e.random() < pc:
                q = int(rng_e.choice([1, 2, 3], p=[0.6, 0.3, 0.1])) if pcat[p] in (6, 8) else (2 if rng_e.random() < 0.06 else 1)
                emit("add_to_cart", p, q=q, src="product_page", gap=(3.0, 0.6))
                cart.append((p, q))
                comp = COMPLEMENT.get(ptype[p])
                if comp and forced is None and rng_e.random() < 0.45:
                    tt = comp[int(rng_e.integers(len(comp)))]
                    cands = [x for x in by_type[tt] if x not in seen]
                    if cands:
                        forced, forced_s = int(cands[int(rng_e.integers(len(cands)))]), "product_page"
                        if k == n_views - 1:
                            n_views += 1
        if forced is not None:
            seen.add(forced)
            emit("product_view", forced, src=forced_s, gap=(3.6, 0.8))
        # korpa -> uklanjanje -> checkout
        if cart:
            kept = []
            for p, q in cart:
                if rng_e.random() < CART_ABANDON_REMOVE:
                    emit("remove_from_cart", p, src="cart", gap=(3.2, 0.6))
                else:
                    kept.append((p, q))
            hv_bonus = 1.0 + 0.25 * min(len(kept), 3) / 3
            if kept and rng_e.random() < min(0.9, par["checkout"] * sale_boost * hv_bonus):
                order_seq += 1
                first = True
                for p, q in kept:
                    emit("purchase", p, q=q, src="cart", gap=(4.6, 0.5) if first else (0.0, 0.1))
                    first = False
                    e = evs[-1]
                    orders.append({"order_id": order_seq, "user_id": u["u"], "user_session": sid, "product_id": p,
                                   "quantity": q, "unit_price": e[5], "total_price": round(e[5] * q, 2),
                                   "status": "completed", "timestamp": e[8], "_ev": e})
                    last_bought_cat[u["u"]] = pcat[p]
                if rng_e.random() < 0.2:
                    p, _ = pick_product(cat, u, False, seen)
                    emit("product_view", p, src="product_page", gap=(3.8, 0.7))
        # sesija ne sme da pređe kraj prozora: odseci rep
        evs = [e for e in evs if e[8] <= window_end]
        rows.extend(evs)

    seq_of = {id(e): i for i, e in enumerate(rows)}
    ev = pd.DataFrame(rows, columns=EVENT_COLUMNS[1:])
    ev["_seq"] = np.arange(len(ev))
    ev = ev.sort_values(["timestamp", "_seq"], kind="stable").reset_index(drop=True)
    ev.insert(0, "event_id", np.arange(1, len(ev) + 1))
    seq_to_eid = dict(zip(ev["_seq"], ev["event_id"]))
    ev = ev.drop(columns="_seq")
    for col in ("product_id", "category_id", "recommendation_position"):
        ev[col] = ev[col].astype("Int64")
    ev["timestamp"] = ev["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    od = pd.DataFrame(orders)
    od["_ev"] = [seq_of.get(id(e), -1) for e in od["_ev"]]
    od = od[od["_ev"] >= 0].copy()
    od["event_id"] = od["_ev"].map(seq_to_eid).astype(int)
    od["timestamp"] = pd.to_datetime(od["timestamp"]).dt.strftime("%Y-%m-%d %H:%M:%S")
    od = od.drop(columns="_ev").sort_values("event_id").reset_index(drop=True)
    # order_id po redosledu prvog događaja porudžbine
    remap = {o: i for i, o in enumerate(dict.fromkeys(od["order_id"]), 1)}
    od["order_id"] = od["order_id"].map(remap)
    od = od[["order_id", "user_id", "user_session", "product_id", "quantity", "unit_price", "total_price",
             "status", "timestamp", "event_id"]]
    products = P[["product_id", "name", "slug", "description", "img_url", "category_id", "price", "created_at"]]

    result = {"customers": cust, "events": ev, "orders": od, "products": products, "categories": cats}
    if write:
        out_dir.mkdir(parents=True, exist_ok=True)
        files = {"categories.csv": cats, "products.csv": products, "customers.csv": cust,
                 "events.csv": ev, "orders.csv": od}
        for name, df in files.items():
            df.to_csv(out_dir / name, index=False, lineterminator="\n")
        meta = build_metadata(seed, files, out_dir, on_sale)
        (out_dir / "metadata.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n")
        result["metadata"] = meta
    return result


def build_metadata(seed, files, out_dir, on_sale):
    ev, od, cust = files["events.csv"], files["orders.csv"], files["customers.csv"]
    et = ev["event_type"]
    sess = ev["user_session"].nunique()
    buy_sess = ev.loc[et == "purchase", "user_session"].nunique()
    cart_sess = ev.loc[et == "add_to_cart", "user_session"].nunique()
    return {
        "dataset": "dm_events_v2",
        "description": "Seeded synthetic e-commerce month (January 2026): catalog, customers, behavioral events "
                       "and orders for the Digital Marketing & Recommender Systems course (Day 1).",
        "source": "synthetic",
        "generator": {"module": "app.data.generate_dataset", "function": "generate_dataset", "version": 2,
                      "params": {"n_customers": N_CUSTOMERS, "products_per_category": 21,
                                 "n_products": len(files["products.csv"]), "window_start": "2026-01-01",
                                 "window_days": N_DAYS}},
        "seed": {"rng": "numpy.default_rng", "seed_base": seed,
                 "sub_seeds": {"customers": seed, "products": seed + 1, "events": seed + 2},
                 "derivation": "seed_base + per-part integer offset; each part gets its own default_rng"},
        "personas": {"primary_counts": {k: int(v) for k, v in cust["persona"].value_counts().items()},
                     "secondary_counts": {k: int(v) for k, v in cust["secondary_persona"].value_counts().items()},
                     "secondary_probability": SECONDARY_PROB, "blend_prob": BLEND_PROB,
                     "price_noise_prob": PRICE_NOISE_PROB, "definitions": PERSONA_DEFS,
                     "behavior": PARAMS},
        "realism": {
            "seasonality": "Jan 1 low (0.55x), winter sale Jan 2-6 (1.45x traffic, 30% of catalog 15-35% off, "
                           "1.2x cart/checkout), Orthodox Christmas Jan 7 (0.65x), weekends +18%, after payday "
                           "Jan 25+ (+12%); hourly profile peaks 12-13h and 19-21h",
            "session_timing": "log-normal gaps between events (median ~35 s for views), capped at 25 min",
            "category_affinity": {str(k): v for k, v in AFFINITY.items()},
            "co_purchase": "after add_to_cart, 45% chance to view a complementary product type (e.g. Laptop -> Mouse)",
            "recommendations": {"slate_prob": REC_SLATE_PROB, "k": REC_K, "ctr_by_position": REC_CTR,
                                "rule": "top-popular in the viewed product's category"},
            "funnel": "cart probability depends on persona and price fit; 12% of cart items removed; checkout "
                      "probability by persona (0.20-0.45)",
            "products_on_sale": len(on_sale),
        },
        "counts": {"categories": len(files["categories.csv"]), "products": len(files["products.csv"]),
                   "customers": len(cust), "events": len(ev), "orders": int(od["order_id"].nunique()),
                   "order_lines": len(od)},
        "funnel": {"product_views": int((et == "product_view").sum()), "add_to_cart": int((et == "add_to_cart").sum()),
                   "purchases": int((et == "purchase").sum()), "sessions": int(sess),
                   "sessions_with_cart": int(cart_sess), "sessions_with_purchase": int(buy_sess),
                   "session_conversion_rate": round(buy_sess / sess, 4),
                   "cart_abandonment_rate": round(1 - buy_sess / cart_sess, 4),
                   "recommendation_impressions": int((et == "recommendation_impression").sum()),
                   "recommendation_clicks": int((et == "recommendation_click").sum())},
        "revenue": {"total": round(float(od["total_price"].sum()), 2),
                    "aov": round(float(od.groupby("order_id")["total_price"].sum().mean()), 2),
                    "items_per_order": round(len(od) / od["order_id"].nunique(), 3)},
        "fields": FIELDS,
        "reproducibility_note": "No wall-clock timestamp is recorded here: the generator is byte-for-byte "
                                "reproducible, so the sidecar must not change between runs.",
        "manifest": {"sha256": {n: _sha(out_dir / n) for n in files}},
    }


FIELDS = {
    "categories": {"category_id": "int, stabilan ID kategorije", "name": "str, naziv kategorije", "slug": "str, URL slug"},
    "products": {"product_id": "int, stabilan ID proizvoda", "name": "str, tip + linija + model",
                 "slug": "str, URL slug", "description": "str, opis sa atributima (namena, linija, boja)",
                 "img_url": "str, placeholder putanja slike", "category_id": "int, FK -> categories.category_id",
                 "price": "float, redovna cena u EUR (log-uniformno u opsegu tipa proizvoda), .99/.49",
                 "created_at": "str, datum dodavanja u katalog (2025)"},
    "customers": {"user_id": "int, stabilan ID korisnika", "name": "str, generisano (veštački, nije PII)",
                  "email": "str, generisani email (example.test)", "join_date": "str (YYYY-MM-DD)",
                  "persona": "str, primarna persona", "secondary_persona": "str ili prazno, sekundarna persona",
                  "blend_prob": "float, verovatnoća da sesija koristi sekundarnu personu"},
    "events": {"event_id": "int, rastući po vremenu", "event_type": "product_view|category_view|search|add_to_cart|"
               "remove_from_cart|purchase|recommendation_impression|recommendation_click",
               "user_id": "int, FK -> customers", "user_session": "str, session_NNNNNN (redosled početka sesije)",
               "product_id": "int ili prazno (category_view/search)", "category_id": "int ili prazno (search)",
               "price": "float ili prazno, cena u trenutku događaja (sa popustom tokom sniženja)",
               "quantity": "int >= 1", "source": "product_page|category_page|shop|search_page|cart|recommendation",
               "timestamp": "str YYYY-MM-DD HH:MM:SS, bez zone",
               "recommendation_source": "str ili prazno (category = Day 1 rule-based)",
               "recommendation_position": "int ili prazno, 1-based"},
    "orders": {"order_id": "int, ID porudžbine (stavke iste porudžbine dele ID)", "user_id": "int",
               "user_session": "str", "product_id": "int", "quantity": "int", "unit_price": "float, plaćena cena",
               "total_price": "float, unit_price * quantity (stavka)", "status": "str (completed)",
               "timestamp": "str, isto kao purchase događaj", "event_id": "int, FK -> purchase događaj"},
}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", type=Path, default=None)
    a = ap.parse_args()
    r = generate_dataset(seed=a.seed, out_dir=a.out)
    print(json.dumps({"counts": r["metadata"]["counts"], "funnel": r["metadata"]["funnel"],
                      "revenue": r["metadata"]["revenue"]}, indent=2))


if __name__ == "__main__":
    main()
