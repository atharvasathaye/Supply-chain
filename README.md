# Supply Chain Pressure and US Inflation

Analysis of the relationship between the NY Fed Global Supply Chain Pressure Index (GSCPI)
and US Consumer Price Index (CPI) inflation, with a Streamlit dashboard and VAR forecast.

![Dashboard preview](preview.png)

## What this does

The pipeline pulls monthly GSCPI readings from the NY Fed and CPI sub-indices from
FRED, merges them, and runs:

- Augmented Dickey-Fuller stationarity tests
- Granger causality tests (lags 1–12 months)
- Lagged cross-correlation analysis
- VAR(p) forecast 12 months ahead

Results are surfaced through an interactive Streamlit dashboard with four tabs:
historical comparison, lagged correlations, Granger causality, and the VAR forecast.

A GitHub Actions workflow refreshes the data on the 5th of each month.

## Data sources

| Series | Source | Frequency |
|--------|--------|-----------|
| CPI (all items, core, food, energy, vehicles, shelter) | FRED (St. Louis Fed) | Monthly |
| Global Supply Chain Pressure Index | NY Federal Reserve | Monthly |

## Project structure

```
.
├── data_pipeline.py          # fetches and merges CPI + GSCPI
├── statistical_analysis.py   # stationarity, Granger, lagged correlation, VAR forecast
├── app.py                    # Streamlit dashboard
├── forecast_model.py         # standalone VAR forecast script
├── requirements.txt
├── Dockerfile
├── .github/
│   └── workflows/
│       └── update_data.yml   # monthly cron job
├── cpi_data.csv              # raw CPI series (auto-updated)
├── gscpi_data.csv            # raw GSCPI series (auto-updated)
├── merged_data_for_bi.csv    # merged dataset used by the dashboard
└── forecast_data.csv         # 12-month VAR forecast output
```

## Getting started

```bash
git clone https://github.com/atharvasathaye/Supply-chain.git
cd Supply-chain
pip install -r requirements.txt
```

Refresh the data (optional — the repo already includes current data):

```bash
python data_pipeline.py
python statistical_analysis.py
```

Run the dashboard:

```bash
streamlit run app.py
```

Run with Docker:

```bash
docker build -t supply-chain .
docker run -p 8501:8501 supply-chain
```

## Key findings

GSCPI Granger-causes CPI at all lags 1–12 months (p < 0.0001 at lag 1).
Peak lagged correlation is r = 0.63 at a 10-month lag.
The VAR model forecasts CPI YoY at roughly 3–4% through mid-2027.

These results are consistent with the academic literature finding that supply chain
disruptions feed into consumer prices with a 6–12 month delay.

## Automated updates

`.github/workflows/update_data.yml` runs on the 5th of every month. It fetches the
latest CPI and GSCPI readings, regenerates the merged dataset and forecast, and commits
the updated CSVs back to the repository. Power BI or Tableau can connect directly to
the raw GitHub URL for a live-refreshing data source.

## Requirements

Python 3.10+. See `requirements.txt` for package versions.

---

Atharva Sathaye — [GitHub](https://github.com/atharvasathaye) · [LinkedIn](https://linkedin.com/in/atharvasathaye)
