"""Vizualizacija: confusion matrice clean vs leaky modela (Day 3).

Pokretanje (bilo gde):

    python3 "Day 3/examples/visualize_confusion.py"

Gradi clean i leaky training dataset-e (isti split, isti model), trenira oba i
crtá confusion matrice jedna pored druge u ``confusion_clean_vs_leaky.png``
(pored ``examples/``). Crveni znak: leaky model izgleda „savršeno" jer vidi
budućnost — ne zato što je dobar.
"""

import sys
from pathlib import Path

# dm-ml na sys.path da možemo da importujemo kursne module
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "dm-ml"))

import pandas as pd
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from app.data.events import EventStore
from app.data.paths import dataset_path
from app.ml.conversion import (
    CONVERSION_FEATURE_COLUMNS,
    build_training_dataset,
    evaluate_model,
    split_dataset,
    train_conversion_model,
)
from app.ml.features import scale_customer_features

WINDOW_DAYS = 7
TEST_SIZE = 0.3
RANDOM_STATE = 42
OUT_PNG = Path(__file__).resolve().parent / "confusion_clean_vs_leaky.png"


def main() -> None:
    store = EventStore.load_seeded()
    orders = pd.read_csv(dataset_path("orders.csv"))
    events = store.events_dataframe()

    clean = build_training_dataset(events, orders, window_days=WINDOW_DAYS, leaky=False)
    leaky = build_training_dataset(events, orders, window_days=WINDOW_DAYS, leaky=True)
    clean_users = set(clean["user_id"])
    leaky = leaky[leaky["user_id"].isin(clean_users)].reset_index(drop=True)

    train_df, test_df = split_dataset(clean, test_size=TEST_SIZE, random_state=RANDOM_STATE)
    train_users = set(train_df["user_id"])
    test_users = set(test_df["user_id"])

    def _fit_eval(df: pd.DataFrame):
        tr = df[df["user_id"].isin(train_users)].reset_index(drop=True)
        te = df[df["user_id"].isin(test_users)].reset_index(drop=True)
        scaled_tr, scaler = scale_customer_features(tr, CONVERSION_FEATURE_COLUMNS)
        scaled_te, _ = scale_customer_features(te, CONVERSION_FEATURE_COLUMNS, scaler=scaler)
        model = train_conversion_model(
            scaled_tr.to_numpy(), tr["will_purchase"].to_numpy(),
            model_type="logistic_regression", random_state=RANDOM_STATE,
        )
        return evaluate_model(model, scaled_te.to_numpy(), te["will_purchase"].to_numpy())

    clean_m = _fit_eval(clean)
    leaky_m = _fit_eval(leaky)

    fig, axes = plt.subplots(1, 2, figsize=(9, 4))
    panels = [
        (f"Clean (feature-i pre cut-off-a)\nF1={clean_m['f1']}, recall={clean_m['recall']}", clean_m),
        (f"Leaky (feature-i iz cele istorije)\nF1={leaky_m['f1']}, recall={leaky_m['recall']}", leaky_m),
    ]
    for ax, (title, m) in zip(axes, panels):
        cm = m["confusion_matrix"]
        ax.imshow(cm, cmap="Blues", interpolation="nearest")
        for i in range(2):
            for j in range(2):
                ax.text(j, i, str(cm[i][j]), ha="center", va="center", fontsize=16)
        ax.set_xticks([0, 1], ["pred 0", "pred 1"])
        ax.set_yticks([0, 1], ["stvarno 0", "stvarno 1"])
        ax.set_title(title, fontsize=10)
        ax.set_xlabel("Predviđeno")
        ax.set_ylabel("Stvarno")
    fig.suptitle("Day 3 — confusion matrix: clean vs leaky model", fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT_PNG, dpi=130)
    print(f"Sačuvano: {OUT_PNG}")
    print(f"clean F1={clean_m['f1']}  leaky F1={leaky_m['f1']} "
          f"(leaky je bolji jer VARA — feature-i vide window)")


if __name__ == "__main__":
    main()
