"""Demo: purchase / conversion prediction pipeline (Day 3).

Pokretanje (bilo gde):

    python3 "Day 3/examples/demo_conversion.py"

Prikazuje: clean training dataset (labela iz prediction window-a) -> split ->
skaliranje (fit na trening) -> logistic regression vs random forest -> evaluacija
(confusion matrix/precision/recall/F1) + majority baseline -> leakage vežba
(before/after) -> verovatnoća poznatog i nepoznatog korisnika.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd

from app.data.events import EventStore
from app.data.paths import dataset_path
from app.ml.conversion import (
    CONVERSION_FEATURE_COLUMNS,
    build_training_dataset,
    evaluate_model,
    majority_class_baseline,
    predict_conversion_probability,
    run_leakage_exercise,
    split_dataset,
    train_conversion_model,
)
from app.ml.features import build_customer_features, scale_customer_features

WINDOW_DAYS = 7
TEST_SIZE = 0.3
RANDOM_STATE = 42


def main() -> None:
    print("=== Day 3 — Purchase / Conversion Prediction (demo) ===\n")

    store = EventStore.load_seeded()
    orders = pd.read_csv(dataset_path("orders.csv"))
    events = store.events_dataframe()
    print(f"Događaja: {len(events):,}  porudžbina: {orders['order_id'].nunique():,} ({len(orders):,} stavki)")

    # 1) Clean training dataset (feature-i pre cut-off-a; labela iz window-a)
    dataset = build_training_dataset(
        events, orders, window_days=WINDOW_DAYS, leaky=False
    )
    pos = int(dataset["will_purchase"].sum())
    print(f"\n[1] Clean training dataset: {len(dataset):,} korisnika, "
          f"pozitivnih (kupovina u {WINDOW_DAYS}-dnevnom window-u): {pos} "
          f"({pos / len(dataset):.1%})")
    print(dataset.head(5).to_string(index=False))

    # 2) Split + skaliranje (scaler fit na TREINING splitu)
    train_df, test_df = split_dataset(dataset, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    scaled_train, scaler = scale_customer_features(train_df, CONVERSION_FEATURE_COLUMNS)
    scaled_test, _ = scale_customer_features(test_df, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
    print(f"\n[2] Split: train={len(train_df)}, test={len(test_df)} "
          f"(pozitivnih u testu: {int(test_df['will_purchase'].sum())})")

    # 3) Logistic regression vs random forest (ista podešavanja, isti split)
    baseline = majority_class_baseline(test_df["will_purchase"].to_numpy())
    print("\n[3] Majority-class baseline (predict 0 za sve):")
    print(f"    accuracy={baseline['accuracy']}  precision/recall/F1="
          f"{baseline['precision']}/{baseline['recall']}/{baseline['f1']} "
          f"(0 — baseline nikog ne proglašava pozitivnim)")
    for model_type in ("logistic_regression", "random_forest"):
        model = train_conversion_model(
            scaled_train.to_numpy(),
            train_df["will_purchase"].to_numpy(),
            model_type=model_type,
            random_state=RANDOM_STATE,
        )
        m = evaluate_model(model, scaled_test.to_numpy(), test_df["will_purchase"].to_numpy())
        print(f"    {model_type:>19}: accuracy={m['accuracy']} precision={m['precision']} "
              f"recall={m['recall']} F1={m['f1']}")

    # 4) Leakage vežba: clean vs leaky feature-i
    print("\n[4] Leakage vežba (isti model, isti split):")
    leakage = run_leakage_exercise(
        events, orders, window_days=WINDOW_DAYS,
        test_size=TEST_SIZE, random_state=RANDOM_STATE, model_type="logistic_regression",
    )
    c, l = leakage["clean"], leakage["leaky"]
    print(f"    clean (feature-i pre cut-off-a): accuracy={c['accuracy']} precision={c['precision']} "
          f"recall={c['recall']} F1={c['f1']}")
    print(f"    leaky (feature-i iz cele istorije): accuracy={l['accuracy']} precision={l['precision']} "
          f"recall={l['recall']} F1={l['f1']}")
    print(f"    delta_F1 = {leakage['delta_f1']:+.3f} — leaky izgleda bolje jer VARA "
          "(feature-i vide budućnost)")

    # 5) Verovatnoća jednog korisnika (iste feature definicije kao trening)
    print("\n[5] Verovatnoća kupovine (scaler transform-only, cut-off kao trening):")
    reference = pd.to_datetime(pd.concat(
        [events["timestamp"], orders["timestamp"]]
    )).max()
    cutoff = reference - pd.Timedelta(days=WINDOW_DAYS)
    model = train_conversion_model(
        scaled_train.to_numpy(), train_df["will_purchase"].to_numpy(),
        model_type="logistic_regression", random_state=RANDOM_STATE,
    )
    for uid in (2, 999999):
        ev2 = events[pd.to_datetime(events["timestamp"]) < cutoff]
        od2 = orders[pd.to_datetime(orders["timestamp"]) < cutoff]
        cust_ev = ev2[ev2["user_id"] == uid]
        cust_od = od2[od2["user_id"] == uid]
        if len(cust_ev) == 0 and len(cust_od) == 0:
            print(f"    user {uid:>7}: P(will_purchase) = {dataset['will_purchase'].mean():.4f} "
                  "(fallback base_rate — bez istorije pre cut-off-a)")
            continue
        feats = build_customer_features(cust_ev, cust_od, reference=cutoff)
        scaled_row, _ = scale_customer_features(feats, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
        prob = predict_conversion_probability(model, scaled_row.iloc[0])
        print(f"    user {uid:>7}: P(will_purchase) = {prob:.4f}")

    print("\nGotovo. Vizualizacija: python3 \"Day 3/examples/visualize_confusion.py\"")


if __name__ == "__main__":
    main()
