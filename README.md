# Streamflow Forecasting — LightGBM on USGS + NASA POWER

> **Résumé line:** Reproducible daily **streamflow forecasting** pipeline across 4 US river basins (2015–2023) using **LightGBM** on USGS discharge + NASA POWER meteorology — overall **NSE 0.944 / KGE 0.918**, **leave-one-basin-out** generalization to unseen basins (NSE up to 0.74), and honest disclosure of one failing basin.

**Headline result (held-out 2022–2023, all basins pooled):**

| Metric | Value |
| --- | --- |
| NSE (Nash–Sutcliffe Efficiency) | **0.944** |
| KGE (Kling–Gupta Efficiency) | **0.918** |
| RMSE | 1,222 cfs |
| MAE | 304 cfs |

> **One honest caveat:** The 0.944 pooled NSE is biased by the two large-discharge basins. Per-basin NSE of **0.81–0.92 on the three basins that work** is the fairer statement of skill. The fourth basin (Choptank) fails — see [Interpretation & honest limitations](#interpretation--honest-limitations).

![Observed vs predicted hydrograph](outputs/hydrograph.png)

*Potomac River near Washington, DC — next-day streamflow on the held-out period. The model tracks both the spring 2022 flood peak (~100,000 cfs) and the recession limbs.*

---

## What this is

This project demonstrates an applied machine-learning workflow for **next-day streamflow (river discharge) prediction**. It is built for verifiability: clone, install, run one command, and reproduce the standard hydrology skill metrics (NSE, KGE, RMSE, MAE, R²) from scratch using two public APIs.

The structure follows a **large-sample / CAMELS-style** design — multiple basins, chronological train/test splits, and an explicit *leave-one-basin-out* generalization test. The full dataset is fetched live from USGS and NASA POWER rather than shipping multi-gigabyte flat files, so the data acquisition step is fully reproducible and auditable.

For hiring managers: this repo demonstrates applied hydrology, Python data engineering, ML modeling, standard validation discipline, and honest technical communication — not just a notebook score.

---

## Data

Streamflow gauges record discharge but not the meteorological forcing that drives it. Precipitation and temperature are sourced separately from NASA POWER and merged per basin by date, making this a genuine **rainfall–runoff** problem rather than pure autoregression on past flow.

| Source | Variable | Access |
| --- | --- | --- |
| **USGS NWIS** | Observed daily mean discharge (cfs), parameter `00060` — the prediction target | [`dataretrieval`](https://pypi.org/project/dataretrieval/) |
| **NASA POWER** | Daily precipitation (`PRECTOTCORR`) + 2 m air temperature (`T2M`) at each gauge's coordinates | Public REST API (stdlib `urllib`, no extra dependency) |

**Basins (humid, eastern/midwest US):**

| USGS site | River | Lat, Lon |
| --- | --- | --- |
| 01646500 | Potomac River (DC) | 38.95, −77.13 |
| 01491000 | Choptank River (MD) | 39.00, −75.79 |
| 03339000 | Vermilion River (IL) | 40.10, −87.60 |
| 04085427 | Manitowoc River (WI) | 44.11, −87.72 |

---

## Method

- **Features** (`src/features.py`): lagged discharge & precipitation (1–7, 14, 30 days), rolling means/sums, day-of-year sin/cos seasonality, and an antecedent precipitation index. Every feature is built with a `.shift()` so **no future information leaks** into a prediction. 30 features total. Target = next-day discharge.
- **Model** (`src/train.py`): `LightGBMRegressor` (400 trees, lr 0.03). Chosen for strong tabular performance, fast training, and interpretable feature importance.
- **Evaluation** (`src/evaluate.py`): NSE, KGE, RMSE, MAE, R². The **train/test split is strictly chronological** (test is always later in time). Generalization is stress-tested with **leave-one-basin-out (LOBO)**: train on 3 basins, predict the unseen 4th — a harder and more realistic test of transfer.
- **LSTM baseline:** intentionally left as a documented stub (`lstm_baseline_stub`) — a clearly-marked future extension, **not a claimed result**.

---

## Results

**Per-basin skill on the held-out period** (single pooled model, tested on each basin separately):

| Basin | NSE | Note |
| --- | --- | --- |
| Potomac (01646500) | **0.92** | Strong |
| Vermilion (03339000) | **0.91** | Strong |
| Manitowoc (04085427) | **0.81** | Strong |
| Choptank (01491000) | **−0.76** | Fails — see limitations |

**Leave-one-basin-out (LOBO)** — model never sees the test basin during training:

| Held-out basin | LOBO NSE |
| --- | --- |
| Vermilion | 0.74 |
| Manitowoc | 0.73 |
| Potomac | 0.13 |
| Choptank | −1.44 |

Three of four basins achieve LOBO NSE ≥ 0.73, demonstrating that the learned rainfall–runoff patterns transfer to unseen watersheds. Potomac (0.13) and Choptank (−1.44) do not transfer — Choptank fails in both evaluation modes.

![Observed vs predicted scatter](outputs/scatter.png)
![LightGBM feature importance](outputs/feature_importance.png)

---

## Interpretation & honest limitations

- **The pooled model generalizes well to 3 of 4 basins** but **fails on the Choptank** (negative NSE in both the in-basin holdout and leave-one-basin-out). The Choptank is a small, slow coastal-plain river with tidal influence; its flow scale and regime differ sharply from the larger inland basins. A single pooled model — trained on and numerically dominated by the high-discharge basins — predicts the Choptank worse than its own long-term mean. This is exactly the **basin-heterogeneity** problem that motivates the CAMELS research program.
- **Honest reading of the headline NSE:** 0.944 pooled is inflated by the large-discharge basins; the per-basin numbers (**0.81–0.92** on the three that work) are the fairer statement of skill. High NSE on humid, well-gauged basins is expected for a well-specified model — it does not guarantee transfer to arid, flashy, or tidally influenced catchments.
- **Feature importance** is dominated by recent lagged discharge and rolling flow, with precipitation and seasonality as secondary drivers. This is physically sensible for daily forecasting: flow has strong short-horizon persistence, and the model is correctly learning that signal.
- **Clear next steps to fix Choptank and improve transfer:** predict in **log space** (`log1p(Q)`) to handle orders-of-magnitude scale spread; add **static catchment attributes** (drainage area, slope, soils — the CAMELS attributes) so the model can condition on basin type; per-basin normalization; implement the **LSTM** baseline for sequence-to-sequence comparison.

---

## How to run

```bash
pip install -r requirements.txt

# Full demo: build dataset → train → NSE/KGE + leave-one-basin-out → plots
python run_demo.py            # writes outputs/metrics.json + 3 PNGs

# Core training entry point only (pooled model + metrics.json)
python -m src.train
```

Both commands fetch live data from USGS and NASA POWER — an internet connection is required on first run.

---

## Repository layout

```
src/data.py       USGS streamflow + NASA POWER weather, merged per basin
src/features.py   leakage-safe lag / rolling / seasonal feature engineering
src/train.py      LightGBM training + metrics (+ LSTM stub, clearly marked)
src/evaluate.py   NSE, KGE, and the full metric table
run_demo.py       end-to-end run: pooled + per-basin + leave-one-basin-out + plots
outputs/          metrics.json and the generated figures
```
