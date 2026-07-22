import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(
    page_title="Supply Chain & Inflation",
    layout="wide",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@st.cache_data(ttl=3600)
def load_merged():
    path = os.path.join(BASE_DIR, "merged_data_for_bi.csv")
    if not os.path.exists(path):
        return None
    df = pd.read_csv(path, parse_dates=["date"])
    return df.sort_values("date").reset_index(drop=True)


@st.cache_data(ttl=3600)
def load_forecast():
    path = os.path.join(BASE_DIR, "forecast_data.csv")
    if not os.path.exists(path):
        return None
    return pd.read_csv(path, parse_dates=["date"])


df    = load_merged()
fc_df = load_forecast()

if df is None:
    st.error("Data not found. Run `python data_pipeline.py` first.")
    st.stop()


# Sidebar

st.sidebar.title("Controls")

min_date = df["date"].min().to_pydatetime()
max_date = df["date"].max().to_pydatetime()

start_date, end_date = st.sidebar.slider(
    "Date range",
    min_value=min_date,
    max_value=max_date,
    value=(min_date, max_date),
)

cpi_options = {
    "All items (headline)": "cpi_all_yoy",
    "Core (ex food & energy)": "cpi_core_yoy",
    "Food at home": "cpi_food_yoy",
    "Energy": "cpi_energy_yoy",
    "Used vehicles": "cpi_vehicles_yoy",
    "Shelter": "cpi_shelter_yoy",
}
selected_cpi_label = st.sidebar.selectbox("CPI sub-index", list(cpi_options.keys()))
selected_cpi_col   = cpi_options[selected_cpi_label]

show_forecast = st.sidebar.toggle("Show VAR forecast overlay", value=True)

filt = df[(df["date"] >= start_date) & (df["date"] <= end_date)].copy()


# Header

st.title("Supply Chain Pressure vs. US Inflation")
st.caption(
    f"FRED CPI + NY Fed GSCPI · data through {df['date'].max().strftime('%B %Y')}"
)


# KPI row

col1, col2, col3, col4 = st.columns(4)

corr_now  = filt["gscpi"].corr(filt[selected_cpi_col])
corr_lag3 = filt["gscpi"].shift(3).corr(filt[selected_cpi_col])
latest_gscpi = df["gscpi"].iloc[-1]
latest_cpi   = df[selected_cpi_col].iloc[-1] if selected_cpi_col in df.columns else np.nan

col1.metric(
    "Current GSCPI",
    f"{latest_gscpi:.2f} sd",
    delta=f"{latest_gscpi - df['gscpi'].iloc[-13]:.2f} vs 1y ago",
)
col2.metric(
    f"Current {selected_cpi_label[:18]}",
    f"{latest_cpi:.1f}%",
    delta=f"{latest_cpi - df[selected_cpi_col].iloc[-13]:.1f} pp vs 1y ago"
    if selected_cpi_col in df.columns else "",
)
col3.metric("Contemporaneous r", f"{corr_now:.3f}")
col4.metric(
    "3-month lag r",
    f"{corr_lag3:.3f}",
    delta="stronger" if abs(corr_lag3) > abs(corr_now) else "weaker",
)

st.divider()


# Tabs

tab1, tab2, tab3, tab4 = st.tabs([
    "Historical",
    "Lagged correlations",
    "Granger causality",
    "VAR forecast",
])


# Tab 1 — Historical comparison

with tab1:
    st.subheader("GSCPI vs. CPI inflation")
    st.write(
        "The blue line is the Global Supply Chain Pressure Index, measured in standard "
        "deviations from its historical average. When it spikes, as it did during "
        "COVID-era shipping bottlenecks, it tends to show up in consumer prices a few "
        "months later. The red line is year-over-year CPI inflation for whichever "
        "sub-index you have selected in the sidebar. Use the date slider to zoom into "
        "specific periods."
    )

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=filt["date"], y=filt["gscpi"],
        name="GSCPI (sd)", mode="lines",
        line=dict(color="#2563eb", width=2),
    ))
    fig.add_trace(go.Scatter(
        x=filt["date"], y=filt[selected_cpi_col],
        name=f"{selected_cpi_label} YoY (%)", mode="lines",
        line=dict(color="#dc2626", width=2, dash="dot"),
        yaxis="y2",
    ))

    if show_forecast and fc_df is not None:
        fig.add_trace(go.Scatter(
            x=fc_df["date"], y=fc_df["cpi_yoy_forecast"],
            name="CPI forecast (VAR)", mode="lines",
            line=dict(color="#dc2626", width=1.5, dash="longdash"),
            yaxis="y2",
        ))
        fig.add_trace(go.Scatter(
            x=fc_df["date"], y=fc_df["gscpi_forecast"],
            name="GSCPI forecast (VAR)", mode="lines",
            line=dict(color="#2563eb", width=1.5, dash="longdash"),
        ))

    fig.update_layout(
        xaxis=dict(title="Date"),
        yaxis=dict(title="GSCPI (standard deviations)", side="left", showgrid=False),
        yaxis2=dict(title="CPI YoY (%)", side="right", overlaying="y", showgrid=False),
        hovermode="x unified",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=480,
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption("Dashed lines are the 12-month VAR forecast. GSCPI typically leads CPI by 3–6 months.")

    st.subheader("CPI sub-indices")
    st.write(
        "Not all prices move together. Energy and used vehicles tend to react first "
        "when supply chains tighten. Core CPI strips those out and moves more slowly. "
        "Shelter is largely driven by the housing market and often lags the others "
        "by a year or more."
    )
    sub_cols = [
        c for c in [
            "cpi_all_yoy", "cpi_core_yoy", "cpi_food_yoy",
            "cpi_energy_yoy", "cpi_vehicles_yoy", "cpi_shelter_yoy",
        ]
        if c in filt.columns
    ]
    colours = ["#2563eb", "#16a34a", "#ea580c", "#7c3aed", "#dc2626", "#ca8a04"]
    labels  = ["All items", "Core", "Food", "Energy", "Used vehicles", "Shelter"]

    fig2 = go.Figure()
    for col, lab, clr in zip(sub_cols, labels, colours):
        fig2.add_trace(go.Scatter(
            x=filt["date"], y=filt[col],
            name=lab, mode="lines",
            line=dict(color=clr),
        ))
    fig2.update_layout(
        xaxis_title="Date",
        yaxis_title="YoY %",
        hovermode="x unified",
        height=380,
    )
    st.plotly_chart(fig2, use_container_width=True)


# Tab 2 — Lagged correlations

with tab2:
    st.subheader("Lagged correlation")
    st.write(
        "This answers a simple question: if supply chains were stressed a few months "
        "ago, how well does that predict inflation today? Each bar shows the correlation "
        "between GSCPI at some point in the past and CPI now. A bar at lag 10 means "
        "supply chain pressure from 10 months ago correlates with today's prices. "
        "The taller the bar, the stronger the relationship. The scatter plot below "
        "lets you pick any lag and see each individual month plotted against each other."
    )

    max_lag = st.slider("Max lag (months)", 6, 24, 18)
    rows = []
    cpi_s   = filt[selected_cpi_col].dropna()
    gscpi_s = filt["gscpi"]
    for lag in range(0, max_lag + 1):
        shifted = gscpi_s.shift(lag).loc[cpi_s.index]
        mask    = cpi_s.notna() & shifted.notna()
        r       = cpi_s[mask].corr(shifted[mask])
        rows.append({"Lag (months)": lag, "Pearson r": round(r, 4)})
    lc_df = pd.DataFrame(rows)

    best_lag = int(lc_df.loc[lc_df["Pearson r"].abs().idxmax(), "Lag (months)"])
    best_r   = lc_df.loc[lc_df["Pearson r"].abs().idxmax(), "Pearson r"]

    st.write(f"Peak correlation: r = {best_r:.3f} at lag = {best_lag} months")

    fig3 = px.bar(
        lc_df, x="Lag (months)", y="Pearson r",
        color="Pearson r",
        color_continuous_scale=["#1e3a8a", "#2563eb", "#86efac"],
        range_color=[-1, 1],
    )
    fig3.update_layout(height=360, coloraxis_showscale=False)
    st.plotly_chart(fig3, use_container_width=True)

    scatter_lag = st.slider("Lag for scatter plot", 0, max_lag, best_lag)
    filt2 = filt.copy()
    filt2["gscpi_lagged"] = filt2["gscpi"].shift(scatter_lag)
    fig4 = px.scatter(
        filt2.dropna(subset=["gscpi_lagged", selected_cpi_col]),
        x="gscpi_lagged", y=selected_cpi_col,
        trendline="ols",
        labels={
            "gscpi_lagged": f"GSCPI (t - {scatter_lag}m)",
            selected_cpi_col: f"{selected_cpi_label} YoY (%)",
        },
        opacity=0.6,
    )
    fig4.update_layout(height=380)
    st.plotly_chart(fig4, use_container_width=True)


# Tab 3 — Granger causality

with tab3:
    st.subheader("Granger causality")
    st.write(
        "Correlation alone does not tell you which series drives the other. Granger "
        "causality is a statistical test that asks whether knowing past GSCPI values "
        "helps predict future CPI, beyond what CPI alone would tell you. If the "
        "p-value for a given lag is below 0.05 (the red dotted line), GSCPI at that "
        "lag adds real predictive power. Bars above the line are not statistically meaningful."
    )

    try:
        from statistical_analysis import run_granger, stationarity_test

        gc_df    = run_granger(filt)
        sig_lags = gc_df[gc_df["significant"]]["lag_months"].tolist()

        if sig_lags:
            st.write(f"Significant lags: {sig_lags} months (p < 0.05)")
        else:
            st.write("No significant Granger causality in the selected date range.")

        fig5 = px.bar(
            gc_df, x="lag_months", y="p_value_F",
            color="significant",
            color_discrete_map={True: "#2563eb", False: "#94a3b8"},
            labels={
                "lag_months": "Lag (months)",
                "p_value_F": "p-value (F-test)",
                "significant": "p < 0.05",
            },
        )
        fig5.add_hline(
            y=0.05, line_dash="dot", line_color="#dc2626",
            annotation_text="p = 0.05",
        )
        fig5.update_layout(height=360)
        st.plotly_chart(fig5, use_container_width=True)

        st.subheader("ADF stationarity tests")
        adf_rows = []
        for col in ["cpi_all_yoy", "gscpi"]:
            if col in filt.columns:
                adf_rows.append(stationarity_test(filt[col], col))
        st.dataframe(pd.DataFrame(adf_rows), use_container_width=True)

    except Exception as e:
        st.write(f"Could not run Granger test: {e}")
        st.write("Make sure statistical_analysis.py and statsmodels are installed.")


# Tab 4 — VAR forecast

with tab4:
    st.subheader("12-month forecast")
    st.write(
        "A Vector Autoregression (VAR) model is fitted on both GSCPI and CPI "
        "together, so each series can inform the forecast of the other. The model "
        "picks how many months back to look based on which configuration fits the "
        "historical data best. The dashed section of each line is the forecast. "
        "Treat it as a reasonable trajectory given current supply chain conditions, "
        "not a precise prediction. The table below shows the month-by-month numbers."
    )

    if fc_df is not None:
        hist_tail = df.tail(36)[["date", "gscpi", "cpi_all_yoy"]].copy()

        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(
            x=hist_tail["date"], y=hist_tail["cpi_all_yoy"],
            name="CPI YoY (actual)", mode="lines",
            line=dict(color="#dc2626", width=2),
        ))
        fig6.add_trace(go.Scatter(
            x=fc_df["date"], y=fc_df["cpi_yoy_forecast"],
            name="CPI YoY (forecast)", mode="lines+markers",
            line=dict(color="#dc2626", width=2, dash="dash"),
        ))
        fig6.add_trace(go.Scatter(
            x=hist_tail["date"], y=hist_tail["gscpi"],
            name="GSCPI (actual)", mode="lines",
            line=dict(color="#2563eb", width=2),
            yaxis="y2",
        ))
        fig6.add_trace(go.Scatter(
            x=fc_df["date"], y=fc_df["gscpi_forecast"],
            name="GSCPI (forecast)", mode="lines+markers",
            line=dict(color="#2563eb", width=2, dash="dash"),
            yaxis="y2",
        ))
        fig6.update_layout(
            xaxis_title="Date",
            yaxis=dict(title="CPI YoY (%)", side="left", showgrid=False),
            yaxis2=dict(title="GSCPI (sd)", side="right", overlaying="y", showgrid=False),
            hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            height=480,
        )
        st.plotly_chart(fig6, use_container_width=True)

        st.subheader("Forecast values")
        fc_display = fc_df.copy()
        fc_display["date"] = fc_display["date"].dt.strftime("%b %Y")
        st.dataframe(
            fc_display.rename(columns={
                "date": "Month",
                "cpi_yoy_forecast": "CPI YoY forecast (%)",
                "gscpi_forecast": "GSCPI forecast (sd)",
            }),
            use_container_width=True,
        )
    else:
        st.write("Run `python statistical_analysis.py` to generate forecast_data.csv, then reload.")
        if st.button("Generate forecast now"):
            try:
                from statistical_analysis import load_merged, run_var_forecast
                run_var_forecast(load_merged())
                st.write("Forecast generated. Reload the page.")
            except Exception as e:
                st.write(f"Error: {e}")


# Export

st.divider()
st.subheader("Export")
col_a, col_b = st.columns(2)

with col_a:
    csv = filt.to_csv(index=False).encode("utf-8")
    st.download_button(
        "Download filtered data (CSV)",
        csv,
        "supply_chain_filtered.csv",
        "text/csv",
    )

with col_b:
    if fc_df is not None:
        fc_csv = fc_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download forecast (CSV)",
            fc_csv,
            "supply_chain_forecast.csv",
            "text/csv",
        )
