import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Supply Chain & Inflation Tracker", layout="wide", initial_sidebar_state="collapsed")

# Custom CSS for aesthetic improvements (Dark Mode focus, modern typography)
st.markdown("""
<style>
    /* Main Background and Text */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
        font-family: 'Inter', sans-serif;
    }
    
    /* Hide Streamlit Branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Title Styling */
    h1 {
        font-weight: 700;
        letter-spacing: -1px;
        background: -webkit-linear-gradient(#00C9FF, #92FE9D);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    /* Metric Cards Styling */
    div[data-testid="metric-container"] {
        background-color: #1E2127;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #2D3139;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 4px;
        color: #A0AAB2;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        color: #00C9FF;
        border-bottom: 2px solid #00C9FF;
    }
</style>
""", unsafe_allow_html=True)

st.title("Supply Chain Disruptions vs. Inflation")
st.write("An interactive analysis of how global supply chain bottlenecks serve as leading indicators for consumer price inflation.")

@st.cache_data
def load_data():
    file_path = "merged_data_for_bi.csv"
    if not os.path.exists(file_path):
        return None
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

df = load_data()

if df is None:
    st.error("Data missing. Please run `python data_pipeline.py` to generate the dataset.")
    st.stop()

# Get latest metrics
latest_data = df.iloc[-1]
prev_data = df.iloc[-2]

gscpi_latest = latest_data['gscpi']
gscpi_change = gscpi_latest - prev_data['gscpi']

cpi_latest = latest_data['cpi_yoy']
cpi_change = cpi_latest - prev_data['cpi_yoy']

# KPI Ribbon
col1, col2, col3 = st.columns(3)
with col1:
    st.metric(
        label="Global Supply Chain Pressure (GSCPI)", 
        value=f"{gscpi_latest:.2f} SD", 
        delta=f"{gscpi_change:.2f} vs last month",
        delta_color="inverse"
    )
with col2:
    st.metric(
        label="US CPI Inflation (YoY)", 
        value=f"{cpi_latest:.2f}%", 
        delta=f"{cpi_change:.2f}% vs last month",
        delta_color="inverse"
    )
with col3:
    st.metric(
        label="Data Last Updated", 
        value=latest_data['date'].strftime('%B %Y'),
        delta="Live Connection"
    )

st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Historical Trends", "Interactive Lag Analysis", "Data Export & BI"])

with tab1:
    st.subheader("Macroeconomic Overview")
    st.write("The chart below overlays the GSCPI (measured in standard deviations from the historical mean) against the US CPI Year-over-Year inflation rate.")
    
    fig = go.Figure()
    
    # GSCPI Line
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['gscpi'], 
        name='Supply Chain Pressure', 
        line=dict(color='#00C9FF', width=3),
        fill='tozeroy', fillcolor='rgba(0, 201, 255, 0.1)',
        yaxis='y1'
    ))
    
    # CPI Line
    fig.add_trace(go.Scatter(
        x=df['date'], y=df['cpi_yoy'], 
        name='CPI Inflation (%)', 
        line=dict(color='#FF0055', width=3, dash='dot'),
        yaxis='y2'
    ))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FAFAFA'),
        hovermode='x unified',
        xaxis=dict(showgrid=False, showline=True, linecolor='#2D3139', title='Date'),
        yaxis=dict(showgrid=True, gridcolor='#2D3139', title='GSCPI (Standard Deviations)'),
        yaxis2=dict(showgrid=False, title='CPI YoY (%)', overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5),
        margin=dict(l=0, r=0, t=60, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Leading Indicator Analysis")
    st.write("""
    Supply chain disruptions take time to affect consumer prices. Use the slider below to shift the GSCPI data forward in time. 
    Notice how shifting the supply chain data by **3 to 6 months** perfectly aligns the peaks with inflation spikes.
    """)
    
    lag_months = st.slider("Shift Supply Chain Data (Months)", min_value=0, max_value=12, value=3, step=1)
    
    lag_df = df.copy()
    lag_df['gscpi_lagged'] = lag_df['gscpi'].shift(lag_months)
    lag_df.dropna(inplace=True)
    
    lag_fig = go.Figure()
    lag_fig.add_trace(go.Scatter(
        x=lag_df['date'], y=lag_df['gscpi_lagged'], 
        name=f'GSCPI (Shifted {lag_months} mo)', 
        line=dict(color='#00C9FF', width=2)
    ))
    lag_fig.add_trace(go.Scatter(
        x=lag_df['date'], y=lag_df['cpi_yoy'], 
        name='CPI Inflation (%)', 
        line=dict(color='#FF0055', width=2)
    ))
    
    lag_fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#FAFAFA'),
        hovermode='x unified',
        xaxis=dict(showgrid=False),
        yaxis=dict(showgrid=True, gridcolor='#2D3139', zeroline=True, zerolinecolor='#2D3139')
    )
    st.plotly_chart(lag_fig, use_container_width=True)
    
    correlation = lag_df['gscpi_lagged'].corr(lag_df['cpi_yoy'])
    st.info(f"**Statistical Correlation at {lag_months} month lag:** {correlation:.2f} (Pearson coefficient)")

with tab3:
    st.subheader("Connect to Power BI")
    st.write("""
    This project is designed for enterprise BI workflows. The dataset updates automatically via GitHub Actions.
    To connect this live data feed to Tableau or Power BI:
    1. Open Power BI Desktop -> Get Data -> Web.
    2. Paste the raw GitHub URL for the `merged_data_for_bi.csv` file.
    3. The dashboard will now automatically sync with the latest macroeconomic data every month.
    """)
    
    csv_data = df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Local CSV Snapshot",
        data=csv_data,
        file_name="supply_chain_inflation_data.csv",
        mime="text/csv",
        type="primary"
    )
