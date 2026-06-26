"""Hydrology-grade evaluation metrics.

NSE  - Nash-Sutcliffe Efficiency (1 = perfect; 0 = no better than mean; <0 worse).
KGE  - Kling-Gupta Efficiency, decomposing correlation, variability, and bias.
"""

from __future__ import annotations

import numpy as np


def _clean(observed, simulated):
    obs = np.asarray(observed, dtype="float64")
    sim = np.asarray(simulated, dtype="float64")
    mask = np.isfinite(obs) & np.isfinite(sim)
    return obs[mask], sim[mask]


def nse(observed, simulated) -> float:
    obs, sim = _clean(observed, simulated)
    if obs.size < 2:
        return float("nan")
    denom = float(np.sum((obs - obs.mean()) ** 2))
    if denom == 0.0:
        return float("nan")
    return float(1.0 - np.sum((obs - sim) ** 2) / denom)


def kge(observed, simulated) -> float:
    obs, sim = _clean(observed, simulated)
    if obs.size < 2 or obs.std() == 0.0 or obs.mean() == 0.0:
        return float("nan")
    r = float(np.corrcoef(obs, sim)[0, 1])
    alpha = float(sim.std() / obs.std())
    beta = float(sim.mean() / obs.mean())
    return float(1.0 - np.sqrt((r - 1.0) ** 2 + (alpha - 1.0) ** 2 + (beta - 1.0) ** 2))


def metric_table(observed, simulated) -> dict[str, float]:
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

    obs, sim = _clean(observed, simulated)
    return {
        "nse": nse(obs, sim),
        "kge": kge(obs, sim),
        "rmse": float(np.sqrt(mean_squared_error(obs, sim))),
        "mae": float(mean_absolute_error(obs, sim)),
        "r2": float(r2_score(obs, sim)),
    }
