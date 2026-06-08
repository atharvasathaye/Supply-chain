# Supply Chain & Inflation Impact Analysis

This project analyzes the historical relationship between global supply chain disruptions and macroeconomic inflation in the United States. By combining the Global Supply Chain Pressure Index (GSCPI) with the Consumer Price Index (CPI), this project demonstrates how supply-side shocks serve as leading indicators for consumer price increases.

## Key Insights
*   **Supply Shocks Precede Inflation:** The data shows a clear lag between spikes in the GSCPI and subsequent rises in CPI Year-over-Year inflation.
*   **Data Sourcing:** Uses live data from the Federal Reserve Economic Data (FRED) and the New York Fed.

## Project Structure
*   `data_pipeline.py`: Downloads, cleans, and merges raw economic data from FRED and the NY Fed.
*   `merged_data_for_bi.csv`: Cleaned dataset ready for import into Tableau or Power BI.
*   `app.py`: An interactive Streamlit dashboard for programmatic data exploration.

## How to Run

1.  **Environment Setup:**
    Install `uv` (a fast Python package manager) if you don't have it, or use standard `pip`:
    ```bash
    pip install pandas requests streamlit statsmodels matplotlib openpyxl xlrd plotly
    ```

2.  **Fetch the Data:**
    Run the data pipeline to pull the latest economic figures.
    ```bash
    python data_pipeline.py
    ```

3.  **Launch the Dashboard:**
    ```bash
    python -m streamlit run app.py
    ```

## Business Application
Understanding the correlation between supply chain friction and inflation allows businesses to build more resilient pricing strategies and better forecast raw material costs during global disruptions.
