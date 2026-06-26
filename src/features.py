"""Feature engineering for next-day streamflow prediction."""

from __future__ import annotations

import numpy as np
import pandas as pd


DEFAULT_LAGS: tuple[int, ...] = (1, 2, 3, 4, 5, 6, 7, 14, 30)


def make_features(
    data: pd.DataFrame,
    lags: tuple[int, ...] = DEFAULT_LAGS,
    target_horizon_days: int = 1,
) -> pd.DataFrame:
    """Create hydrologic lag, rolling, seasonal, and target columns."""

    required = {"basin_id", "date", "streamflow_cfs", "precip_in", "air_temp_c"}
    missing = required.difference(data.columns)
    if missing:
        raise ValueError(f"Missing required columns for feature engineering: {sorted(missing)}")

    frame = data.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values(["basin_id", "date"]).reset_index(drop=True)
    pieces = [_make_one_basin_features(group, lags, target_horizon_days) for _, group in frame.groupby("basin_id")]
    features = pd.concat(pieces, ignore_index=True)
    feature_columns = [column for column in features.columns if column not in {"basin_id", "date"}]
    return features.dropna(subset=feature_columns).reset_index(drop=True)


def _make_one_basin_features(
    group: pd.DataFrame,
    lags: tuple[int, ...],
    target_horizon_days: int,
) -> pd.DataFrame:
    out = group.sort_values("date").copy()

    for column in ("precip_in", "streamflow_cfs"):
        for lag in lags:
            out[f"{column}_lag_{lag}d"] = out[column].shift(lag)

    out["streamflow_rolling_mean_7d"] = out["streamflow_cfs"].shift(1).rolling(7).mean()
    out["streamflow_rolling_mean_30d"] = out["streamflow_cfs"].shift(1).rolling(30).mean()
    out["precip_rolling_sum_7d"] = out["precip_in"].shift(1).rolling(7).sum()
    out["precip_rolling_sum_30d"] = out["precip_in"].shift(1).rolling(30).sum()
    out["air_temp_rolling_mean_7d"] = out["air_temp_c"].shift(1).rolling(7).mean()

    day_of_year = out["date"].dt.dayofyear
    out["day_of_year"] = day_of_year
    out["day_sin"] = np.sin(2.0 * np.pi * day_of_year / 366.0)
    out["day_cos"] = np.cos(2.0 * np.pi * day_of_year / 366.0)
    out["antecedent_precip_index"] = _antecedent_precipitation_index(out["precip_in"])
    out["target_streamflow_cfs"] = out["streamflow_cfs"].shift(-target_horizon_days)
    return out


def _antecedent_precipitation_index(precip: pd.Series, decay: float = 0.85) -> pd.Series:
    """Compute API using only previous-day and older precipitation."""

    values: list[float] = []
    running = 0.0
    for amount in precip.fillna(0.0):
        values.append(running)
        running = float(amount) + decay * running
    return pd.Series(values, index=precip.index)
