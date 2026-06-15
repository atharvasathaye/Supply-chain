import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Supply Chain & Inflation Tracker", layout="wide", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Inter', sans-serif; }
    #MainMenu {visibility: hidden;} footer {visibility: hidden;} header {visibility: hidden;}
    h1 {
        font-weight: 700; letter-spacing: -1px;
        background: -webkit-linear-gradient(#00C9FF, #92FE9D);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    div[data-testid="metric-container"] {
        background-color: #1E2127; border-radius: 12px; padding: 20px;
        border: 1px solid #2D3139; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; background-color: transparent; color: #A0AAB2; font-weight: 500; }
    .stTabs [aria-selected="true"] { color: #00C9FF; border-bottom: 2px solid #00C9FF; }
</style>
""", unsafe_allow_html=True)

st.title("Supply Chain Disruptions vs. Inflation")
st.write("An interactive analysis of how global supply chain bottlenecks serve as leading indicators for consumer price inflation.")

@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "merged_data_for_bi.csv")
    forecast_path = os.path.join(base_dir, "forecast_data.csv")
    
    if not os.path.exists(file_path):
        return None, None
        
    df = pd.read_csv(file_path)
    df['date'] = pd.to_datetime(df['date'])
    
    forecast_df = None
    if os.path.exists(forecast_path):
        forecast_df = pd.read_csv(forecast_path)
        forecast_df['date'] = pd.to_datetime(forecast_df['date'])
        
    return df, forecast_df

df, forecast_df = load_data()

if df is None:
    st.error("Data missing. Please run `python data_pipeline.py` to generate the dataset.")
    st.stop()

# KPIs
latest_data = df.iloc[-1]
prev_data = df.iloc[-2]

gscpi_latest = latest_data['gscpi']
gscpi_change = gscpi_latest - prev_data['gscpi']
cpi_latest = latest_data['cpi_yoy']
cpi_change = cpi_latest - prev_data['cpi_yoy']

col1, col2, col3 = st.columns(3)
with col1:
    st.metric(label="Global Supply Chain Pressure", value=f"{gscpi_latest:.2f} SD", delta=f"{gscpi_change:.2f} vs last month", delta_color="inverse")
with col2:
    st.metric(label="US CPI Inflation (YoY)", value=f"{cpi_latest:.2f}%", delta=f"{cpi_change:.2f}% vs last month", delta_color="inverse")
with col3:
    st.metric(label="Data Last Updated", value=latest_data['date'].strftime('%B %Y'), delta="Live Connection")

st.markdown("---")

tab1, tab2, tab3, tab4 = st.tabs(["Historical Trends", "Interactive Lag Analysis", "Sector Breakdown", "ML Forecast"])

with tab1:
    st.subheader("Macroeconomic Overview")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['date'], y=df['gscpi'], name='Supply Chain Pressure', line=dict(color='#00C9FF', width=3), fill='tozeroy', fillcolor='rgba(0, 201, 255, 0.1)', yaxis='y1'))
    fig.add_trace(go.Scatter(x=df['date'], y=df['cpi_yoy'], name='CPI Inflation (%)', line=dict(color='#FF0055', width=3, dash='dot'), yaxis='y2'))

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'), hovermode='x unified',
        xaxis=dict(showgrid=False, showline=True, linecolor='#2D3139', title='Date'),
        yaxis=dict(showgrid=True, gridcolor='#2D3139', title='GSCPI (SD)'),
        yaxis2=dict(showgrid=False, title='CPI YoY (%)', overlaying='y', side='right'),
        legend=dict(orientation="h", yanchor="bottom", y=1.05, xanchor="center", x=0.5), margin=dict(l=0, r=0, t=60, b=0)
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Leading Indicator Analysis")
    lag_months = st.slider("Shift Supply Chain Data Forward (Months)", min_value=0, max_value=12, value=3, step=1)
    
    lag_df = df.copy()
    lag_df['gscpi_lagged'] = lag_df['gscpi'].shift(lag_months)
    lag_df.dropna(inplace=True)
    
    lag_fig = go.Figure()
    lag_fig.add_trace(go.Scatter(x=lag_df['date'], y=lag_df['gscpi_lagged'], name=f'GSCPI (Shifted {lag_months} mo)', line=dict(color='#00C9FF', width=2)))
    lag_fig.add_trace(go.Scatter(x=lag_df['date'], y=lag_df['cpi_yoy'], name='CPI Inflation (%)', line=dict(color='#FF0055', width=2)))
    
    lag_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'), hovermode='x unified', xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#2D3139'))
    st.plotly_chart(lag_fig, use_container_width=True)
    st.info(f"**Statistical Correlation at {lag_months} month lag:** {lag_df['gscpi_lagged'].corr(lag_df['cpi_yoy']):.2f}")

with tab3:
    st.subheader("Inflation by Economic Sector")
    st.write("Which sectors are most volatile when supply chains break down?")
    
    if 'cpi_food_yoy' in df.columns:
        sec_fig = go.Figure()
        sectors = {
            'cpi_food_yoy': ('Food', '#2ECC71'),
            'cpi_energy_yoy': ('Energy', '#E74C3C'),
            'cpi_vehicles_yoy': ('Used Cars & Trucks', '#F39C12'),
            'cpi_core_yoy': ('Core CPI (No Food/Energy)', '#9B59B6')
        }
        for col, (name, color) in sectors.items():
            sec_fig.add_trace(go.Scatter(x=df['date'], y=df[col], name=name, line=dict(color=color, width=2)))
            
        sec_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'), hovermode='x unified', xaxis=dict(showgrid=False), yaxis=dict(title='YoY Inflation (%)', showgrid=True, gridcolor='#2D3139'))
        st.plotly_chart(sec_fig, use_container_width=True)
    else:
        st.warning("Sector data not available. Please run the updated pipeline.")

with tab4:
    st.subheader("Machine Learning Forecast (VAR Model)")
    st.write("Using a Vector Autoregression (VAR) model trained on historical supply chain and CPI data to forecast the next 6 months of inflation.")
    
    if forecast_df is not None:
        fc_fig = go.Figure()
        
        # Plot last 3 years of actuals
        recent_df = df.tail(36)
        fc_fig.add_trace(go.Scatter(x=recent_df['date'], y=recent_df['cpi_yoy'], name='Actual Inflation (%)', line=dict(color='#FAFAFA', width=3)))
        
        # Connect actuals to forecast seamlessly
        connect_df = pd.DataFrame({'date': [recent_df['date'].iloc[-1], forecast_df['date'].iloc[0]], 'cpi_yoy': [recent_df['cpi_yoy'].iloc[-1], forecast_df['cpi_yoy_forecast'].iloc[0]]})
        fc_fig.add_trace(go.Scatter(x=connect_df['date'], y=connect_df['cpi_yoy'], name='_connect', line=dict(color='#00C9FF', width=3, dash='dash'), showlegend=False))
        
        # Plot forecast
        fc_fig.add_trace(go.Scatter(x=forecast_df['date'], y=forecast_df['cpi_yoy_forecast'], name='Forecasted Inflation (%)', line=dict(color='#00C9FF', width=3, dash='dash')))
        
        fc_fig.update_layout(plot_bgcolor='rgba(0,0,0,0)', paper_bgcolor='rgba(0,0,0,0)', font=dict(color='#FAFAFA'), hovermode='x unified', xaxis=dict(showgrid=False), yaxis=dict(title='CPI YoY (%)', showgrid=True, gridcolor='#2D3139'))
        st.plotly_chart(fc_fig, use_container_width=True)
        
        # Show data table for exact numbers
        st.dataframe(forecast_df[['date', 'cpi_yoy_forecast']].rename(columns={'date': 'Month', 'cpi_yoy_forecast': 'Predicted YoY Inflation (%)'}), hide_index=True)
    else:
        st.warning("Forecast data missing. Please run `python forecast_model.py`.")
