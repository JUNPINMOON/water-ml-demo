"""Train a LightGBM next-day streamflow model."""

from __future__ import annotations

import argparse
import json
import pickle
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from .data import DEFAULT_SITE_IDS, load_daily_nwis
from .evaluate import metric_table
from .features import make_features


TARGET_COLUMN = "target_streamflow_cfs"
NON_FEATURE_COLUMNS = {"basin_id", "date", TARGET_COLUMN}


def chronological_split(
    frame: pd.DataFrame,
    test_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Split rows by date so the test set is later in time than training."""

    if not 0.0 < test_fraction < 1.0:
        raise ValueError("test_fraction must be between 0 and 1.")
    ordered = frame.sort_values("date").reset_index(drop=True)
    cutoff = max(1, int(len(ordered) * (1.0 - test_fraction)))
    if cutoff >= len(ordered):
        raise ValueError("Not enough rows for a chronological train/test split.")
    return ordered.iloc[:cutoff].copy(), ordered.iloc[cutoff:].copy()


def train_lightgbm(
    features: pd.DataFrame,
    output_dir: Path,
    test_fraction: float = 0.2,
) -> dict[str, float | int | str]:
    """Train and persist a LightGBM regressor with basic test metrics."""

    from lightgbm import LGBMRegressor

    train, test = chronological_split(features, test_fraction=test_fraction)
    feature_columns = [
        column
        for column in features.columns
        if column not in NON_FEATURE_COLUMNS and pd.api.types.is_numeric_dtype(features[column])
    ]
    if not feature_columns:
        raise ValueError("No numeric feature columns were generated.")

    model = LGBMRegressor(
        objective="regression",
        n_estimators=400,
        learning_rate=0.03,
        num_leaves=31,
        subsample=0.9,
        colsample_bytree=0.9,
        random_state=42,
    )
    model.fit(train[feature_columns], train[TARGET_COLUMN])
    predictions = model.predict(test[feature_columns])
    metrics: dict[str, float | int | str] = {
        "train_rows": int(len(train)),
        "test_rows": int(len(test)),
        "feature_count": int(len(feature_columns)),
        "test_start": str(test["date"].min().date()),
        "test_end": str(test["date"].max().date()),
        **metric_table(test[TARGET_COLUMN].to_numpy(), predictions),
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    with (output_dir / "lightgbm_streamflow_model.pkl").open("wb") as handle:
        pickle.dump({"model": model, "feature_columns": feature_columns, "metrics": metrics}, handle)
    (output_dir / "metrics.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def lstm_baseline_stub(*_args: object, **_kwargs: object) -> None:
    """Reserved hook for a future PyTorch LSTM baseline."""

    raise NotImplementedError(
        "The PyTorch LSTM baseline is intentionally left as an optional future baseline."
    )


def run_training(
    sites: Iterable[str],
    start: str,
    end: str,
    output_dir: Path,
    test_fraction: float,
) -> dict[str, float | int | str]:
    daily = load_daily_nwis(sites=sites, start=start, end=end)
    feature_frame = make_features(daily)
    return train_lightgbm(feature_frame, output_dir=output_dir, test_fraction=test_fraction)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Train next-day streamflow prediction model.")
    parser.add_argument("--start", default="2018-01-01", help="NWIS start date, YYYY-MM-DD.")
    parser.add_argument("--end", default="2023-12-31", help="NWIS end date, YYYY-MM-DD.")
    parser.add_argument("--sites", nargs="+", default=list(DEFAULT_SITE_IDS), help="USGS site IDs.")
    parser.add_argument("--output-dir", default="outputs", type=Path, help="Directory for model artifacts.")
    parser.add_argument("--test-fraction", default=0.2, type=float, help="Chronological test-set fraction.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    metrics = run_training(
        sites=args.sites,
        start=args.start,
        end=args.end,
        output_dir=args.output_dir,
        test_fraction=args.test_fraction,
    )
    print(json.dumps(metrics, indent=2))


if __name__ == "__main__":
    main()
