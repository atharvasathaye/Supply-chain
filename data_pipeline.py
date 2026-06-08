import os
import pandas as pd
from datetime import datetime

def setup_directories():
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    os.makedirs(os.path.join(base_dir, "data", "raw"), exist_ok=True)
    os.makedirs(os.path.join(base_dir, "data", "processed"), exist_ok=True)

def fetch_cpi_data(start_date, end_date):
    # Fetch US Consumer Price Index directly from FRED CSV endpoint.
    url = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CPIAUCSL"
    cpi_data = pd.read_csv(url)
    cpi_data.rename(columns={'observation_date': 'date', 'CPIAUCSL': 'cpi'}, inplace=True)
    cpi_data['date'] = pd.to_datetime(cpi_data['date'])
    cpi_data = cpi_data[(cpi_data['date'] >= start_date) & (cpi_data['date'] <= end_date)]
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    cpi_data.to_csv(os.path.join(base_dir, "cpi_data.csv"), index=False)
    return cpi_data

def fetch_gscpi_data():
    # Fetch the Global Supply Chain Pressure Index directly from the NY Fed.
    # We skip the first few rows because they contain header descriptions.
    url = "https://www.newyorkfed.org/medialibrary/research/interactives/gscpi/downloads/gscpi_data.xlsx"
    gscpi_data = pd.read_excel(url, sheet_name='GSCPI Monthly Data', skiprows=4)
    
    # Rename columns to standard names.
    gscpi_data.rename(columns={'Unnamed: 0': 'date', 'Unnamed: 1': 'gscpi'}, inplace=True)
    
    # Keep only date and index columns.
    gscpi_data = gscpi_data[['date', 'gscpi']]
    
    # Drop rows with empty dates.
    gscpi_data.dropna(subset=['date'], inplace=True)
    
    # Ensure dates are datetime objects.
    gscpi_data['date'] = pd.to_datetime(gscpi_data['date'])
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    gscpi_data.to_csv(os.path.join(base_dir, "gscpi_data.csv"), index=False)
    
    return gscpi_data

def process_data(cpi_df, gscpi_df):
    # Normalize dates to the first of the month for proper merging.
    cpi_df['date'] = cpi_df['date'].dt.to_period('M').dt.to_timestamp()
    gscpi_df['date'] = gscpi_df['date'].dt.to_period('M').dt.to_timestamp()
    
    # Merge datasets on the date column.
    merged_df = pd.merge(cpi_df, gscpi_df, on='date', how='inner')
    
    # Calculate Year-over-Year (YoY) percentage change for CPI to represent inflation rate.
    merged_df['cpi_yoy'] = merged_df['cpi'].pct_change(periods=12) * 100
    merged_df.dropna(inplace=True)
    
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(base_dir, "merged_data_for_bi.csv")
    merged_df.to_csv(output_path, index=False)
    print(f"Data processed and saved to {output_path}")
    return merged_df

if __name__ == "__main__":
    setup_directories()
    
    start_time = datetime(2000, 1, 1)
    end_time = datetime.now()
    
    print("Fetching CPI data...")
    cpi_df = fetch_cpi_data(start_time, end_time)
    
    print("Fetching GSCPI data...")
    gscpi_df = fetch_gscpi_data()
    
    print("Processing and merging data...")
    final_df = process_data(cpi_df, gscpi_df)
    
    print("Pipeline complete.")
