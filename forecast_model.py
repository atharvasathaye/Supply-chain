import pandas as pd
import numpy as np
from statsmodels.tsa.api import VAR
import os

def generate_forecast():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "merged_data_for_bi.csv")
    
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # We will use GSCPI and CPI YoY to train the VAR model
    # VAR is designed for multivariate time series forecasting
    data = df[['cpi_yoy', 'gscpi']].dropna()
    
    # Fit the VAR model
    model = VAR(data)
    # We choose a lag of 6 months based on our Granger Causality findings
    results = model.fit(6)
    
    # Forecast the next 6 months
    lag_order = results.k_ar
    forecast_input = data.values[-lag_order:]
    forecast = results.forecast(y=forecast_input, steps=6)
    
    # Create future dates for the forecast
    last_date = df['date'].iloc[-1]
    future_dates = pd.date_range(start=last_date + pd.DateOffset(months=1), periods=6, freq='MS')
    
    # Create forecast dataframe
    forecast_df = pd.DataFrame({
        'date': future_dates,
        'cpi_yoy_forecast': forecast[:, 0],
        'gscpi_forecast': forecast[:, 1]
    })
    
    output_path = os.path.join(base_dir, "forecast_data.csv")
    forecast_df.to_csv(output_path, index=False)
    print(f"Forecast successfully saved to {output_path}")

if __name__ == "__main__":
    generate_forecast()
