"""
data_pipeline.py
Fetches live CPI (FRED) and GSCPI (NY Fed) data, merges them,
computes YoY inflation and lagged correlations, then saves to CSV.
"""

import os
import pandas as pd
import numpy as np
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def setup_directories():
    for sub in ("data/raw", "data/processed"):
        os.makedirs(os.path.join(BASE_DIR, sub), exist_ok=True)


# ── CPI (headline + sub-indices) ──────────────────────────────────────────────

CPI_SERIES = {
    "cpi_all":       "CPIAUCSL",   # All items
    "cpi_core":      "CPILFESL",   # Core (ex food & energy)
    "cpi_food":      "CPIUFDSL",   # Food at home
    "cpi_energy":    "CPIENGSL",   # Energy
    "cpi_vehicles":  "CUSR0000SETA02",  # Used vehicles
    "cpi_shelter":   "CUSR0000SAH1",    # Shelter
}

FRED_BASE = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"


def fetch_cpi_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Download all CPI sub-index series from FRED and merge on date."""
    frames = []
    for col, series_id in CPI_SERIES.items():
        url = FRED_BASE.format(series_id)
        print(f"  Fetching {col} ({series_id})…")
        df = pd.read_csv(url, parse_dates=["observation_date"])
        df.rename(columns={"observation_date": "date", series_id: col}, inplace=True)
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        frames.append(df.set_index("date"))

    merged = pd.concat(frames, axis=1).reset_index()
    merged.to_csv(os.path.join(BASE_DIR, "cpi_data.csv"), index=False)
    print(f"  Saved {len(merged)} rows to cpi_data.csv")
    return merged


# ── GSCPI ─────────────────────────────────────────────────────────────────────

GSCPI_URL = (
    "https://www.newyorkfed.org/medialibrary/research/interactives/"
    "gscpi/downloads/gscpi_data.xlsx"
)


def fetch_gscpi_data() -> pd.DataFrame:
    """Download the Global Supply Chain Pressure Index from the NY Fed."""
    import requests, io
    print("  Fetching GSCPI from NY Fed…")
    resp = requests.get(GSCPI_URL, timeout=30)
    resp.raise_for_status()
    # NY Fed serves old .xls binary format despite the .xlsx extension.
    # Sheet name changed from 'GSCPI_data' to 'GSCPI Monthly Data' in 2025.
    df = pd.read_excel(
        io.BytesIO(resp.content),
        sheet_name="GSCPI Monthly Data",
        skiprows=4,
        engine="xlrd",
        header=0,
    )
    # Two unnamed columns: date and GSCPI value
    df.columns = ["date", "gscpi"]
    df = df[["date", "gscpi"]].dropna(subset=["date"])
    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(os.path.join(BASE_DIR, "gscpi_data.csv"), index=False)
    print(f"  Saved {len(df)} rows to gscpi_data.csv")
    return df


# ── Process & merge ───────────────────────────────────────────────────────────

def process_data(cpi_df: pd.DataFrame, gscpi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge CPI and GSCPI, compute YoY changes for every CPI series,
    and add lagged GSCPI columns (1, 3, 6, 12 months).
    CPI dates are month-start; GSCPI dates are month-end.
    Normalize both to month-start (MS) before merging.
    """
    cpi_df   = cpi_df.copy()
    gscpi_df = gscpi_df.copy()
    cpi_df["date"]   = cpi_df["date"].dt.to_period("M").dt.to_timestamp()
    gscpi_df["date"] = gscpi_df["date"].dt.to_period("M").dt.to_timestamp()
    merged = pd.merge(cpi_df, gscpi_df, on="date", how="inner").sort_values("date")

    # YoY % change for every CPI series
    for col in CPI_SERIES:
        if col in merged.columns:
            merged[f"{col}_yoy"] = merged[col].pct_change(periods=12) * 100

    # Lagged GSCPI
    for lag in (1, 3, 6, 12):
        merged[f"gscpi_lag{lag}"] = merged["gscpi"].shift(lag)

    out = os.path.join(BASE_DIR, "merged_data_for_bi.csv")
    merged.to_csv(out, index=False)
    print(f"  Saved merged dataset ({len(merged)} rows) -> {out}")
    return merged


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    setup_directories()

    start = datetime(2000, 1, 1)
    end   = datetime.now()

    print("Fetching CPI data…")
    cpi_df   = fetch_cpi_data(start, end)

    print("Fetching GSCPI data…")
    gscpi_df = fetch_gscpi_data()

    print("Processing and merging data…")
    final    = process_data(cpi_df, gscpi_df)

    print(f"\nPipeline complete. {len(final)} rows, {len(final.columns)} columns.")
    if len(final) > 0:
        print(f"Date range: {final['date'].min().date()} -> {final['date'].max().date()}")
    else:
        print("Warning: merged dataset is empty — check date alignment.")
