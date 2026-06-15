import pandas as pd
from statsmodels.tsa.stattools import grangercausalitytests
import os

def run_causality_test():
    file_path = "merged_data_for_bi.csv"
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return

    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    # We want to test if GSCPI (supply chain pressure) predicts CPI_YOY (inflation).
    # The grangercausalitytests function takes a 2D array where the first column is the 
    # dependent variable (the one being predicted) and the second is the independent variable.
    
    # Ensure no NaN values exist in the columns we are testing
    test_data = df[['cpi_yoy', 'gscpi']].dropna()

    print("\n" + "="*50)
    print("GRANGER CAUSALITY TEST RESULTS")
    print("Hypothesis: Global Supply Chain Pressure (GSCPI) predicts Inflation (CPI YoY)")
    print("="*50)
    
    # We test up to 6 months of lag, as supply chain shocks take time to reach consumers.
    max_lag = 6
    
    try:
        # verbose=False suppresses the massive wall of text from statsmodels
        results = grangercausalitytests(test_data, maxlag=max_lag, verbose=False)
        
        for lag in range(1, max_lag + 1):
            # We look at the SSR based F test p-value
            p_value = results[lag][0]['ssr_ftest'][1]
            significance = "Statistically Significant" if p_value < 0.05 else "Not Significant"
            print(f"Lag {lag} month(s): p-value = {p_value:.4f} -> {significance}")
            
        print("\nInterpretation:")
        print("A p-value below 0.05 indicates strong evidence that the supply chain")
        print("pressure from X months ago causes/predicts the inflation rate today.")
    except Exception as e:
        print(f"Error running statistical test: {e}")

if __name__ == "__main__":
    run_causality_test()
