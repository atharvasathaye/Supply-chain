"""
statistical_analysis.py
Granger causality, VAR forecasting, and lagged correlation analysis
for the Supply Chain Pressure vs Inflation project.

Run standalone:
    python statistical_analysis.py

Or import individual functions in app.py.
"""

import os
import warnings
import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests, adfuller
from statsmodels.tsa.api import VAR

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


# ── Helpers ────────────────────────────────────────────────────────────────────

def load_merged() -> pd.DataFrame:
    path = os.path.join(BASE_DIR, "merged_data_for_bi.csv")
    if not os.path.exists(path):
        raise FileNotFoundError(
            "merged_data_for_bi.csv not found. Run data_pipeline.py first."
        )
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


def stationarity_test(series: pd.Series, name: str = "") -> dict:
    """Augmented Dickey-Fuller test. Returns dict with result summary."""
    result = adfuller(series.dropna(), autolag="AIC")
    return {
        "series": name,
        "adf_stat": round(result[0], 4),
        "p_value":  round(result[1], 4),
        "stationary": result[1] < 0.05,
        "critical_1pct": round(result[4]["1%"], 4),
        "critical_5pct": round(result[4]["5%"], 4),
    }


# ── Granger causality ─────────────────────────────────────────────────────────

def run_granger(df: pd.DataFrame, max_lag: int = 12) -> pd.DataFrame:
    """
    Test whether GSCPI Granger-causes CPI YoY inflation at each lag 1-max_lag.
    Returns a DataFrame of p-values per lag.
    """
    data = df[["cpi_all_yoy", "gscpi"]].dropna()
    results = grangercausalitytests(data[["cpi_all_yoy", "gscpi"]], maxlag=max_lag, verbose=False)

    rows = []
    for lag, res in results.items():
        p_f   = res[0]["ssr_ftest"][1]
        p_chi = res[0]["ssr_chi2test"][1]
        rows.append({
            "lag_months": lag,
            "p_value_F": round(p_f, 4),
            "p_value_chi2": round(p_chi, 4),
            "significant": p_f < 0.05,
        })

    return pd.DataFrame(rows)


# ── Lagged cross-correlation ──────────────────────────────────────────────────

def lagged_correlations(df: pd.DataFrame, max_lag: int = 18) -> pd.DataFrame:
    """
    Pearson correlation between GSCPI(t-lag) and CPI_YoY(t)
    for lags 0 to max_lag months.
    """
    rows = []
    cpi   = df["cpi_all_yoy"].dropna()
    gscpi = df["gscpi"]
    for lag in range(0, max_lag + 1):
        shifted = gscpi.shift(lag).loc[cpi.index]
        mask    = cpi.notna() & shifted.notna()
        r       = cpi[mask].corr(shifted[mask])
        rows.append({"lag_months": lag, "correlation": round(r, 4)})
    return pd.DataFrame(rows)


# ── VAR model & forecast ──────────────────────────────────────────────────────

def run_var_forecast(df: pd.DataFrame, forecast_steps: int = 12) -> pd.DataFrame:
    """
    Fit a VAR model on stationary (differenced) GSCPI and CPI_YoY,
    then forecast forecast_steps months ahead.
    Returns a DataFrame of forecasted values with dates.
    """
    data = df[["gscpi", "cpi_all_yoy"]].dropna()

    # Difference to ensure stationarity
    data_diff = data.diff().dropna()

    # Select optimal lag order (AIC)
    model      = VAR(data_diff)
    res_order  = model.select_order(maxlags=12)
    best_lag   = max(res_order.selected_orders.get("aic", 3), 1)

    # Fit
    fitted = model.fit(best_lag)

    # Forecast
    fc_input = data_diff.values[-best_lag:]
    raw_fc   = fitted.forecast(fc_input, steps=forecast_steps)

    # Reverse differencing
    last_cpi_yoy = data["cpi_all_yoy"].iloc[-1]
    last_gscpi   = data["gscpi"].iloc[-1]
    fc_cpi_yoy   = np.cumsum(raw_fc[:, 1]) + last_cpi_yoy
    fc_gscpi     = np.cumsum(raw_fc[:, 0]) + last_gscpi

    # Build future date index
    last_date    = df["date"].dropna().iloc[-1]
    future_dates = pd.date_range(start=last_date, periods=forecast_steps + 1, freq="MS")[1:]

    forecast_df = pd.DataFrame({
        "date":             future_dates,
        "cpi_yoy_forecast": np.round(fc_cpi_yoy, 3),
        "gscpi_forecast":   np.round(fc_gscpi, 3),
    })

    out = os.path.join(BASE_DIR, "forecast_data.csv")
    forecast_df.to_csv(out, index=False)
    print(f"Forecast saved -> {out}")
    return forecast_df


# ── Standalone report ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    df = load_merged()
    print(f"Loaded {len(df)} rows  ({df['date'].min().date()} -> {df['date'].max().date()})\n")

    # Stationarity
    print("=== Stationarity Tests ===")
    for col in ["cpi_all_yoy", "gscpi"]:
        r      = stationarity_test(df[col], col)
        status = "STATIONARY" if r["stationary"] else "non-stationary"
        print(f"  {col:20s}  ADF={r['adf_stat']:8.4f}  p={r['p_value']:.4f}  -> {status}")

    # Granger
    print("\n=== Granger Causality (GSCPI -> CPI) ===")
    gc  = run_granger(df)
    sig = gc[gc["significant"]]
    print(f"  Significant lags: {sig['lag_months'].tolist()}")
    best = int(gc.loc[gc["p_value_F"].idxmin(), "lag_months"])
    print(f"  Strongest lag: {best} months  (p={gc.loc[gc['lag_months']==best,'p_value_F'].values[0]:.4f})")

    # Lagged correlations
    print("\n=== Lagged Correlations (top 5) ===")
    lc = lagged_correlations(df).sort_values("correlation", ascending=False)
    print(lc.head(5).to_string(index=False))

    # VAR forecast
    print("\n=== VAR Forecast (next 12 months) ===")
    fc = run_var_forecast(df)
    print(fc.to_string(index=False))

    print("\nDone.")
