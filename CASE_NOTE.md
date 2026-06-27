# Hydrology-ML Case Note: CAMELS-Style Streamflow Forecasting with LightGBM

**Junpin Moon** | Water-Resources Engineer + ML | Korea-based, remote-ready

---

## Problem

Can public hydrologic and meteorological data be assembled into a reproducible ML pipeline for daily streamflow forecasting across geographically diverse U.S. basins — and can that pipeline honestly identify where it succeeds and where it fails?

---

## Data

| Source | Variable | Role |
|---|---|---|
| **USGS NWIS** | Daily mean discharge (cfs, param `00060`) | Prediction target |
| **NASA POWER** | Daily precip (`PRECTOTCORR`) + 2 m air temp (`T2M`) at each gauge | Meteorological forcing |

- 4 basins, 2015–2023 (10,419 train rows / 2,605 test rows)
- Basins: Potomac River (DC), Choptank River (MD), Vermilion River (IL), Manitowoc River (WI)
- CAMELS-style multi-basin structure; dataset built from scratch via public APIs — no multi-GB files required

---

## Method

- **Feature engineering** (`src/features.py`): lagged discharge and precipitation (1–7, 14, 30 days), rolling means/sums, day-of-year sin/cos seasonality, antecedent precipitation index — all built with `.shift()` to prevent any target leakage
- **Model** (`src/train.py`): LightGBM (400 trees, lr 0.03) — strong for tabular environmental data, fast, interpretable feature importance
- **Evaluation** (`src/evaluate.py`): NSE, KGE, RMSE, MAE, R²; chronological train/test split; leave-one-basin-out generalization test
- **LSTM baseline**: intentionally left as a documented stub — not a claimed result

---

## Results

**Overall held-out performance (2022–2023, all basins pooled):**

| Metric | Value |
|---|---|
| NSE | **0.944** |
| KGE | **0.918** |
| RMSE | 1,222 cfs |
| MAE | 304 cfs |

**Per-basin (held-out period, pooled model):**

| Basin | NSE | KGE | Note |
|---|---|---|---|
| Potomac River (DC) | **0.922** | 0.888 | Strong |
| Vermilion River (IL) | **0.906** | 0.912 | Strong |
| Manitowoc River (WI) | **0.806** | 0.794 | Strong |
| Choptank River (MD) | **−0.760** | −0.127 | Fails — see Limitations |

**Leave-one-basin-out (model never sees the test basin during training):**

| Held-out basin | NSE |
|---|---|
| Vermilion | 0.738 |
| Manitowoc | 0.730 |
| Potomac | 0.127 |
| Choptank | −1.441 |

Outputs: 3 generated plots (`hydrograph.png`, `scatter.png`, `feature_importance.png`) + `outputs/metrics.json`.

---

## Limitations (stated honestly)

- **The pooled headline NSE (0.944) is inflated** by the two large-discharge basins dominating the pooled metric. The per-basin numbers (0.806–0.922 on the three that work) are the fairer statement of skill. High NSE on humid, well-gauged basins is expected — it does not guarantee transfer to arid or flashy catchments.
- **Choptank fails in both the held-out test (NSE −0.76) and leave-one-basin-out (NSE −1.44).** The Choptank is a small, slow coastal-plain river with tidal influence. Its flow scale and hydrologic regime differ sharply from the larger inland basins; a single pooled model dominated by high-discharge basins cannot predict it better than its own long-term mean. This is precisely the basin-heterogeneity problem the CAMELS research program was designed to study.
- **Next steps to address these gaps**: predict in log space (`log1p(Q)`) to handle scale spread; add static catchment attributes (drainage area, slope, soils); implement per-basin normalization; implement the LSTM baseline.
- **LSTM is a stub, not a result.**

---

## Why This Is Job-Relevant

| Skill domain | Evidence in this repo |
|---|---|
| **Applied hydrology** | Multi-basin CAMELS-style setup, NSE/KGE evaluation, basin heterogeneity diagnosis |
| **Python data engineering** | Public API data collection (USGS, NASA POWER), multi-basin merge, 30-feature leakage-safe pipeline |
| **ML modeling** | LightGBM tabular regression, feature importance, chronological split discipline |
| **Validation discipline** | Leave-one-basin-out generalization test; no future-data leakage |
| **Honest communication** | Choptank failure reported openly; headline bias disclosed; LSTM stub labeled correctly |

This repo is useful evidence for **remote, freelance, and L-1-adjacent roles** in water-resources ML, AEC automation, or applied environmental data science — where a hiring manager needs to verify both technical depth and professional judgment before extending trust across time zones.

---

*Reproducible from scratch: `pip install -r requirements.txt && python run_demo.py`*
*Writes `outputs/metrics.json` + 3 PNGs from live USGS and NASA POWER APIs.*
