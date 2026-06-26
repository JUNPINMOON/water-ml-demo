"""End-to-end demo: train + evaluate (NSE/KGE) + leave-one-basin-out + plots."""

from __future__ import annotations

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from lightgbm import LGBMRegressor

from src.data import BASIN_META, load_daily_nwis
from src.evaluate import metric_table
from src.features import make_features
from src.train import NON_FEATURE_COLUMNS, TARGET_COLUMN, chronological_split

OUT = Path("outputs")
OUT.mkdir(exist_ok=True)
START, END = "2015-01-01", "2023-12-31"


def feature_cols(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns
            if c not in NON_FEATURE_COLUMNS and pd.api.types.is_numeric_dtype(df[c])]


def fit_model(train: pd.DataFrame, cols: list[str]) -> LGBMRegressor:
    model = LGBMRegressor(objective="regression", n_estimators=400, learning_rate=0.03,
                          num_leaves=31, subsample=0.9, colsample_bytree=0.9,
                          random_state=42, verbose=-1)
    model.fit(train[cols], train[TARGET_COLUMN])
    return model


def main() -> None:
    print("Loading USGS streamflow + NASA POWER weather ...", flush=True)
    daily = load_daily_nwis(start=START, end=END)
    feats = make_features(daily)
    cols = feature_cols(feats)
    print(f"rows={len(feats)} basins={feats['basin_id'].nunique()} features={len(cols)}", flush=True)

    # --- Pooled chronological holdout (test is strictly later in time) ---
    train, test = chronological_split(feats, 0.2)
    model = fit_model(train, cols)
    test = test.copy()
    test["pred"] = model.predict(test[cols])
    overall = metric_table(test[TARGET_COLUMN].to_numpy(), test["pred"].to_numpy())

    per_basin = {}
    for bid, g in test.groupby("basin_id"):
        per_basin[bid] = {"name": BASIN_META[bid]["name"], "n": int(len(g)),
                          **metric_table(g[TARGET_COLUMN].to_numpy(), g["pred"].to_numpy())}

    # --- Leave-one-basin-out: train on 3 basins, predict the unseen 4th ---
    lobo = {}
    for held in feats["basin_id"].unique():
        tr = feats[feats["basin_id"] != held]
        te = feats[feats["basin_id"] == held].copy()
        m = fit_model(tr, cols)
        te["pred"] = m.predict(te[cols])
        lobo[held] = {"name": BASIN_META[held]["name"], "n": int(len(te)),
                      **metric_table(te[TARGET_COLUMN].to_numpy(), te["pred"].to_numpy())}

    summary = {"period": [START, END], "feature_count": len(cols),
               "train_rows": int(len(train)), "test_rows": int(len(test)),
               "overall_holdout": overall, "per_basin_holdout": per_basin,
               "leave_one_basin_out": lobo}
    (OUT / "metrics.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    # --- Plot 1: hydrograph for best-performing basin (held-out period) ---
    best = max(per_basin, key=lambda b: per_basin[b]["nse"])
    g = test[test["basin_id"] == best].sort_values("date")
    plt.figure(figsize=(11, 4))
    plt.plot(g["date"], g[TARGET_COLUMN], label="Observed", linewidth=1.1)
    plt.plot(g["date"], g["pred"], label="Predicted", linewidth=1.1, alpha=0.8)
    plt.title(f"Next-day streamflow - {BASIN_META[best]['name']} "
              f"(held-out, NSE={per_basin[best]['nse']:.2f}, KGE={per_basin[best]['kge']:.2f})")
    plt.ylabel("Streamflow (cfs)")
    plt.legend()
    plt.tight_layout()
    plt.savefig(OUT / "hydrograph.png", dpi=130)
    plt.close()

    # --- Plot 2: observed vs predicted scatter (all held-out basins) ---
    plt.figure(figsize=(5, 5))
    plt.scatter(test[TARGET_COLUMN], test["pred"], s=6, alpha=0.25)
    lim = [0.0, float(test[TARGET_COLUMN].quantile(0.995))]
    plt.plot(lim, lim, "k--", linewidth=1)
    plt.xlim(lim)
    plt.ylim(lim)
    plt.xlabel("Observed (cfs)")
    plt.ylabel("Predicted (cfs)")
    plt.title(f"Observed vs Predicted (NSE={overall['nse']:.2f}, KGE={overall['kge']:.2f})")
    plt.tight_layout()
    plt.savefig(OUT / "scatter.png", dpi=130)
    plt.close()

    # --- Plot 3: feature importance (top 15) ---
    imp = pd.Series(model.feature_importances_, index=cols).sort_values().tail(15)
    plt.figure(figsize=(7, 5))
    plt.barh(imp.index, imp.values, color="#2a6f97")
    plt.title("LightGBM feature importance (top 15)")
    plt.tight_layout()
    plt.savefig(OUT / "feature_importance.png", dpi=130)
    plt.close()

    print("OVERALL", json.dumps(overall, indent=2), flush=True)
    print("PER_BASIN_NSE", {b: round(per_basin[b]["nse"], 3) for b in per_basin}, flush=True)
    print("LOBO_NSE", {b: round(lobo[b]["nse"], 3) for b in lobo}, flush=True)
    print("Saved: outputs/metrics.json + hydrograph.png + scatter.png + feature_importance.png", flush=True)


if __name__ == "__main__":
    main()
