"""NASA POWER daily weather and grain-filling heat exposure per plot.

Source: NASA POWER Daily API (MERRA-2 based), community=AG.
https://power.larc.nasa.gov/  Meteorology native grid: 0.5 deg lat x 0.625 deg lon.
Raw JSON responses are cached in data/external/nasa_power/ (one file per grid cell).

Weather is decided by nature, not by the irrigation, so it is a valid effect modifier.
"""
from __future__ import annotations

import json
import time
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
CACHE = ROOT / "data" / "external" / "nasa_power"
PARAMS = ["T2M_MAX", "T2M_MIN", "PRECTOTCORR", "RH2M"]
START, END = "20161001", "20220531"
API = ("https://power.larc.nasa.gov/api/temporal/daily/point?parameters={p}"
       "&community=AG&longitude={lon}&latitude={lat}&start={s}&end={e}&format=JSON")

# Grain-filling window in days after sowing (DAS). Eastern Indo-Gangetic Plain wheat
# typically flowers ~90-100 DAS and matures ~125-135 DAS. Assumption; tested in
# sensitivity runs with shifted windows.
GF_START_DAS, GF_END_DAS = 95, 125
HEAT_THRESHOLD_C = 34.0  # common wheat grain-filling heat-stress threshold for Tmax


def grid_cell(lat, lon):
    return np.round(np.asarray(lat) * 2) / 2, np.round(np.asarray(lon) / 0.625) * 0.625


def fetch_cell(lat: float, lon: float, retries: int = 3) -> pd.DataFrame:
    CACHE.mkdir(parents=True, exist_ok=True)
    f = CACHE / f"power_{lat:.3f}_{lon:.3f}_{START}_{END}.json"
    if not f.exists():
        url = API.format(p=",".join(PARAMS), lon=lon, lat=lat, s=START, e=END)
        for i in range(retries):
            try:
                with urllib.request.urlopen(url, timeout=120) as r:
                    f.write_bytes(r.read())
                break
            except Exception:  # network hiccup: back off and retry
                if i == retries - 1:
                    raise
                time.sleep(5 * (i + 1))
    js = json.loads(f.read_text())
    p = js["properties"]["parameter"]
    w = pd.DataFrame({k: pd.Series(v) for k, v in p.items()})
    w.index = pd.to_datetime(w.index, format="%Y%m%d")
    return w.replace(-999.0, np.nan)


def fetch_all(df: pd.DataFrame) -> dict[tuple[float, float], pd.DataFrame]:
    glat, glon = grid_cell(df.Latitude, df.Longitude)
    cells = sorted(set(zip(glat.tolist(), glon.tolist())))
    return {c: fetch_cell(*c) for c in cells}


def plot_exposure(df: pd.DataFrame, wx: dict, start_das=GF_START_DAS,
                  end_das=GF_END_DAS, threshold=HEAT_THRESHOLD_C) -> pd.DataFrame:
    """Weather during each plot's own grain-filling window (based on its sowing date)."""
    sow = pd.to_datetime(df.SowingDate.astype(str), format="%Y.%m.%d")
    glat, glon = grid_cell(df.Latitude, df.Longitude)
    rows = []
    for s, la, lo in zip(sow, glat, glon):
        w = wx[(la, lo)].loc[s + pd.Timedelta(days=start_das): s + pd.Timedelta(days=end_das)]
        tmax = w.T2M_MAX
        rows.append({
            "GF_TmaxMean": tmax.mean(),
            "GF_HeatDays": int((tmax > threshold).sum()),
            "GF_HeatDegreeDays": float((tmax - threshold).clip(lower=0).sum()),
            "GF_TminMean": w.T2M_MIN.mean(),
            "GF_RainMM": float(w.PRECTOTCORR.sum()),
            "GF_RHMean": w.RH2M.mean(),
            "GF_StartDate": (s + pd.Timedelta(days=start_das)).date(),
        })
    return pd.DataFrame(rows, index=df.index)
