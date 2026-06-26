"""Data loading: USGS daily streamflow + NASA POWER weather, merged per basin.

USGS streamflow gauges do not report precipitation/temperature, so weather is
sourced from NASA POWER (global daily reanalysis) at each basin's coordinates.
This makes the dataset a genuine rainfall-runoff problem rather than pure
streamflow autoregression.
"""

from __future__ import annotations

import json
import urllib.parse
import urllib.request

import numpy as np
import pandas as pd


# USGS site id -> basin metadata (name + gauge coordinates for weather lookup)
BASIN_META: dict[str, dict] = {
    "01646500": {"name": "Potomac River (DC)", "lat": 38.9498, "lon": -77.1276},
    "01491000": {"name": "Choptank River (MD)", "lat": 38.9972, "lon": -75.7858},
    "03339000": {"name": "Vermilion River (IL)", "lat": 40.1011, "lon": -87.5976},
    "04085427": {"name": "Manitowoc River (WI)", "lat": 44.1062, "lon": -87.7160},
}
DEFAULT_SITE_IDS: tuple[str, ...] = tuple(BASIN_META)


def load_daily_nwis(sites=DEFAULT_SITE_IDS, start: str = "2018-01-01", end: str = "2023-12-31") -> pd.DataFrame:
    """Load merged daily streamflow (USGS) + precip/temp (NASA POWER) per basin."""

    frames = []
    for site in (str(s) for s in sites):
        flow = _fetch_streamflow(site, start, end)
        weather = _fetch_power_weather(site, start, end)
        merged = flow.merge(weather, on="date", how="inner")
        merged["basin_id"] = site
        merged["precip_in"] = merged["precip_in"].fillna(0.0)
        merged["air_temp_c"] = merged["air_temp_c"].interpolate(limit_direction="both")
        frames.append(merged.dropna(subset=["streamflow_cfs"]))
    if not frames:
        raise ValueError("No basins loaded.")
    out = pd.concat(frames, ignore_index=True)
    return (
        out[["basin_id", "date", "streamflow_cfs", "precip_in", "air_temp_c"]]
        .sort_values(["basin_id", "date"])
        .reset_index(drop=True)
    )


def _fetch_streamflow(site: str, start: str, end: str) -> pd.DataFrame:
    """Daily mean streamflow (cfs) from USGS NWIS, gap-filled to a daily index."""

    import dataretrieval.nwis as nwis

    raw, _meta = nwis.get_dv(
        sites=[site], start=start, end=end,
        parameterCd=["00060"], statCd="00003", multi_index=False,
    )
    if raw is None or raw.empty:
        raise ValueError(f"NWIS returned no streamflow for site {site}.")
    frame = raw.reset_index()
    date_col = _find_date_column(frame)
    value_col = _find_parameter_value_column(frame, "00060")
    if value_col is None:
        raise ValueError(f"No streamflow value column for site {site}: {list(frame.columns)}")
    df = pd.DataFrame({
        "date": pd.to_datetime(frame[date_col], errors="coerce").dt.tz_localize(None).dt.normalize(),
        "streamflow_cfs": pd.to_numeric(frame[value_col], errors="coerce"),
    }).dropna(subset=["date"]).drop_duplicates("date").sort_values("date").set_index("date")
    full = df.reindex(pd.date_range(df.index.min(), df.index.max(), freq="D"))
    full["streamflow_cfs"] = full["streamflow_cfs"].interpolate(limit=3, limit_direction="both")
    return full.rename_axis("date").reset_index().dropna(subset=["streamflow_cfs"])


def _fetch_power_weather(site: str, start: str, end: str) -> pd.DataFrame:
    """Daily precipitation (in) and mean air temperature (C) from NASA POWER."""

    meta = BASIN_META[site]
    base = "https://power.larc.nasa.gov/api/temporal/daily/point"
    query = urllib.parse.urlencode({
        "parameters": "PRECTOTCORR,T2M", "community": "AG",
        "longitude": meta["lon"], "latitude": meta["lat"],
        "start": start.replace("-", ""), "end": end.replace("-", ""), "format": "JSON",
    })
    with urllib.request.urlopen(f"{base}?{query}", timeout=120) as response:
        payload = json.load(response)
    params = payload["properties"]["parameter"]
    weather = pd.DataFrame({
        "precip_in": pd.Series(params["PRECTOTCORR"], dtype="float64") / 25.4,  # mm -> in
        "air_temp_c": pd.Series(params["T2M"], dtype="float64"),
    }).replace(-999.0 / 25.4, np.nan)
    weather["air_temp_c"] = weather["air_temp_c"].replace(-999.0, np.nan)
    weather.index = pd.to_datetime(weather.index, format="%Y%m%d")
    return weather.rename_axis("date").reset_index()


def _find_date_column(frame: pd.DataFrame) -> str:
    for column in ("datetime", "dateTime", "Date", "date", "index"):
        if column in frame.columns:
            return column
    datetime_columns = [c for c in frame.columns if pd.api.types.is_datetime64_any_dtype(frame[c])]
    if datetime_columns:
        return datetime_columns[0]
    raise ValueError(f"Could not find a date column: {list(frame.columns)}")


def _find_parameter_value_column(frame: pd.DataFrame, parameter_code: str) -> str | None:
    candidates = [
        c for c in frame.columns
        if parameter_code in str(c) and not str(c).endswith("_cd")
    ]
    if not candidates:
        return None
    mean_columns = [c for c in candidates if "mean" in str(c).lower()]
    return str(mean_columns[0] if mean_columns else candidates[0])
