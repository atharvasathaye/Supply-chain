"""
data_pipeline.py

Fetches CPI sub-indices from FRED and the Global Supply Chain Pressure Index
from the NY Fed, merges them on month-start date, computes YoY changes and
lagged GSCPI columns, and writes the result to merged_data_for_bi.csv.
"""

import io
import os
import requests
import pandas as pd
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CPI_SERIES = {
    "cpi_all":      "CPIAUCSL",        # All items
    "cpi_core":     "CPILFESL",        # Core (ex food & energy)
    "cpi_food":     "CPIUFDSL",        # Food at home
    "cpi_energy":   "CPIENGSL",        # Energy
    "cpi_vehicles": "CUSR0000SETA02",  # Used vehicles
    "cpi_shelter":  "CUSR0000SAH1",    # Shelter
}

FRED_BASE  = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"
GSCPI_URL  = (
    "https://www.newyorkfed.org/medialibrary/research/interactives/"
    "gscpi/downloads/gscpi_data.xlsx"
)


def setup_directories():
    for sub in ("data/raw", "data/processed"):
        os.makedirs(os.path.join(BASE_DIR, sub), exist_ok=True)


def fetch_cpi_data(start_date: datetime, end_date: datetime) -> pd.DataFrame:
    """Download all CPI sub-index series from FRED and merge on date."""
    frames = []
    for col, series_id in CPI_SERIES.items():
        url = FRED_BASE.format(series_id)
        print(f"  {col} ({series_id})")
        df = pd.read_csv(url, parse_dates=["observation_date"])
        df.rename(columns={"observation_date": "date", series_id: col}, inplace=True)
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]
        frames.append(df.set_index("date"))

    merged = pd.concat(frames, axis=1).reset_index()
    merged.to_csv(os.path.join(BASE_DIR, "cpi_data.csv"), index=False)
    print(f"  saved {len(merged)} rows -> cpi_data.csv")
    return merged


def fetch_gscpi_data() -> pd.DataFrame:
    """
    Download the NY Fed GSCPI.

    The file is served as a legacy .xls binary despite the .xlsx extension.
    Sheet name changed from 'GSCPI_data' to 'GSCPI Monthly Data' in 2025.
    """
    print("  GSCPI (NY Fed)")
    resp = requests.get(GSCPI_URL, timeout=30)
    resp.raise_for_status()

    df = pd.read_excel(
        io.BytesIO(resp.content),
        sheet_name="GSCPI Monthly Data",
        skiprows=4,
        engine="xlrd",
        header=0,
    )
    df.columns = ["date", "gscpi"]
    df = df[["date", "gscpi"]].dropna(subset=["date"])
    df["date"] = pd.to_datetime(df["date"])
    df.to_csv(os.path.join(BASE_DIR, "gscpi_data.csv"), index=False)
    print(f"  saved {len(df)} rows -> gscpi_data.csv")
    return df


def process_data(cpi_df: pd.DataFrame, gscpi_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge CPI and GSCPI on month-start date, compute YoY % changes for every
    CPI series, and add lagged GSCPI columns at 1, 3, 6, and 12 months.

    CPI uses month-start dates; GSCPI uses month-end dates.
    Both are normalised to month-start before merging.
    """
    cpi_df   = cpi_df.copy()
    gscpi_df = gscpi_df.copy()
    cpi_df["date"]   = cpi_df["date"].dt.to_period("M").dt.to_timestamp()
    gscpi_df["date"] = gscpi_df["date"].dt.to_period("M").dt.to_timestamp()

    merged = pd.merge(cpi_df, gscpi_df, on="date", how="inner").sort_values("date")

    for col in CPI_SERIES:
        if col in merged.columns:
            merged[f"{col}_yoy"] = merged[col].pct_change(periods=12) * 100

    for lag in (1, 3, 6, 12):
        merged[f"gscpi_lag{lag}"] = merged["gscpi"].shift(lag)

    out = os.path.join(BASE_DIR, "merged_data_for_bi.csv")
    merged.to_csv(out, index=False)
    print(f"  saved {len(merged)} rows -> merged_data_for_bi.csv")
    return merged


if __name__ == "__main__":
    setup_directories()

    start = datetime(2000, 1, 1)
    end   = datetime.now()

    print("Fetching CPI data")
    cpi_df = fetch_cpi_data(start, end)

    print("Fetching GSCPI data")
    gscpi_df = fetch_gscpi_data()

    print("Merging")
    final = process_data(cpi_df, gscpi_df)

    print(f"\n{len(final)} rows, {len(final.columns)} columns")
    if len(final) > 0:
        print(f"{final['date'].min().date()} to {final['date'].max().date()}")
