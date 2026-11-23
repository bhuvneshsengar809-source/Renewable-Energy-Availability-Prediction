"""
Renewable Energy Availability Prediction
Professional presentation dashboard for a hybrid solar + piezoelectric concept.

Data integrity:
- Default readings are synthetic sample data for demonstration.
- This application does not connect to ESP32, Blynk, or physical sensors.
- Footstep count is an activity indicator only; piezoelectric electrical output is not measured.
- Battery percentage is an illustrative voltage-derived estimate, not BMS SOC.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Renewable Energy | Smart Monitoring",
    page_icon="☀️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown(
    """
    <style>
      .stApp { background: #f5f8fc; }
      [data-testid="stHeader"] { background: rgba(245,248,252,0.92); }
      .block-container { padding-top: 1.5rem; padding-bottom: 2rem; max-width: 1450px; }
      .hero {
        padding: 1.35rem 1.55rem; border-radius: 18px;
        background: linear-gradient(115deg, #102a43 0%, #176b87 58%, #2a9d8f 100%);
        color: white; margin-bottom: 1rem;
      }
      .hero h1 { color: white; font-size: 2rem; margin: 0 0 .3rem 0; }
      .hero p { color: #e4f1f5; margin: 0; font-size: 1rem; }
      .status-row { display:flex; gap:.5rem; flex-wrap:wrap; margin-top:.9rem; }
      .status {
        display:inline-block; padding:.28rem .7rem; border-radius:999px;
        background:rgba(255,255,255,.15); color:#fff; font-size:.78rem;
        border:1px solid rgba(255,255,255,.25);
      }
      div[data-testid="stMetric"] {
        background: #ffffff; border: 1px solid #e4ebf2; padding: 14px 16px;
        border-radius: 14px; box-shadow: 0 2px 9px rgba(25,55,80,.04);
      }
      div[data-testid="stMetricLabel"] { color:#536779; }
      div[data-testid="stMetricValue"] { color:#12344d; }
      .section-note {
        color:#617487; font-size:.88rem; padding:.55rem .8rem;
        background:#edf3f8; border-left:3px solid #2a9d8f;
        border-radius:7px; margin:.25rem 0 1rem 0;
      }
      .footnote { color:#6c7d8c; font-size:.78rem; }
      .stTabs [data-baseweb="tab-list"] { gap: .45rem; }
      .stTabs [data-baseweb="tab"] {
        background:#eaf0f6; border-radius:9px 9px 0 0; padding:.65rem 1rem;
      }
      .stTabs [aria-selected="true"] { background:#ffffff; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- Data ----------
DATA_PATH = Path(__file__).parent / "simulation" / "sample_telemetry.csv"
REQUIRED_COLUMNS = [
    "timestamp", "solar_voltage_v", "solar_current_a",
    "battery_voltage_v", "battery_current_a", "light_lux",
    "temperature_c", "footstep_count",
]


def generate_sample_data():
    rng = np.random.default_rng(42)
    times = pd.date_range("2026-11-22 06:00", periods=36, freq="30min")
    hour = times.hour + times.minute / 60.0
    daylight = np.clip(np.sin(np.pi * (hour - 6) / 12), 0, None)
    return pd.DataFrame({
        "timestamp": times,
        "solar_voltage_v": np.round(17.5 + 1.2 * daylight + rng.normal(0, .25, len(times)), 2),
        "solar_current_a": np.round(np.clip(1.65 * daylight + rng.normal(0, .06, len(times)), 0, None), 3),
        "battery_voltage_v": np.round(11.4 + .55 * daylight + np.linspace(0, .12, len(times)), 2),
        "battery_current_a": np.round(np.clip(.9 * daylight + rng.normal(0, .08, len(times)), 0, None), 3),
        "light_lux": np.round(np.clip(42000 * daylight + rng.normal(0, 900, len(times)), 0, None), 0),
        "temperature_c": np.round(23 + 7 * daylight + rng.normal(0, .7, len(times)), 1),
        "footstep_count": rng.poisson(18, len(times)),
    })


def load_data(uploaded):
    if uploaded is not None:
        raw = pd.read_csv(uploaded)
        source = "Uploaded CSV"
    elif DATA_PATH.exists():
        raw = pd.read_csv(DATA_PATH)
        source = "Project sample dataset"
    else:
        raw = generate_sample_data()
        source = "Generated sample dataset"

    missing = [col for col in REQUIRED_COLUMNS if col not in raw.columns]
    if missing:
        st.error("CSV is missing required columns: " + ", ".join(missing))
        st.stop()

    raw = raw.copy()
    raw["timestamp"] = pd.to_datetime(raw["timestamp"], errors="coerce")
    for col in REQUIRED_COLUMNS[1:]:
        raw[col] = pd.to_numeric(raw[col], errors="coerce")
    raw = raw.dropna(subset=["timestamp"]).sort_values("timestamp")
    return raw, source


with st.sidebar:
    st.markdown("## ⚙️ Dashboard settings")
    uploaded_file = st.file_uploader("Upload telemetry data (CSV)", type=["csv"])
    st.caption("Upload a CSV with the required columns to visualize your own readings.")
    with st.expander("Required CSV columns"):
        st.code(", ".join(REQUIRED_COLUMNS))
    st.markdown("---")
    st.markdown("### System overview")
    st.write("☀️ Solar PV monitoring")
    st.write("🔋 Battery parameter display")
    st.write("📈 Hourly availability estimate")
    st.write("🌡️ Environmental indicators")
    st.markdown("---")
    st.caption("Academic project dashboard • Hybrid renewable-energy concept")

df, data_source = load_data(uploaded_file)
if df.empty:
    st.error("No valid telemetry rows were found.")
    st.stop()

df["solar_power_w"] = df["solar_voltage_v"] * df["solar_current_a"]
df["battery_power_w"] = df["battery_voltage_v"] * df["battery_current_a"]
df["hour"] = df["timestamp"].dt.hour
# Display-only rough voltage mapping for a proposed 3S Li-ion concept.
df["battery_level_estimate"] = ((df["battery_voltage_v"] - 9.0) / 3.6 * 100).clip(0, 100)

latest = df.iloc[-1]
avg_solar = float(df["solar_power_w"].mean())
peak_solar = float(df["solar_power_w"].max())
avg_temp = float(df["temperature_c"].mean())
interval_hours = 0.5
if len(df) > 1:
    deltas = df["timestamp"].diff().dropna().dt.total_seconds() / 3600
    interval_hours = float(deltas.median()) if not deltas.empty else 0.5
energy_wh = float(df["solar_power_w"].sum() * interval_hours)

# ---------- Header ----------
st.markdown(
    """
    <div class="hero">
      <h1>☀️ Renewable Energy Availability Prediction</h1>
      <p>Hybrid Solar + Piezoelectric Energy Generation and Storage System</p>
      <div class="status-row">
        <span class="status">● Dashboard available</span>
        <span class="status">Data source: sample / uploaded</span>
        <span class="status">Academic prototype interface</span>
      </div>
    </div>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    f'<div class="section-note">Currently displaying <b>{data_source}</b> · '
    f'{len(df)} records · Latest timestamp: <b>{latest["timestamp"]}</b>. '
    'Values are only as reliable as the dataset supplied.</div>',
    unsafe_allow_html=True,
)

# ---------- KPI cards ----------
m1, m2, m3, m4 = st.columns(4)
m1.metric("Latest solar power", f'{latest["solar_power_w"]:.2f} W')
m2.metric("Average solar power", f"{avg_solar:.2f} W")
m3.metric("Peak solar power", f"{peak_solar:.2f} W")
m4.metric("Battery voltage", f'{latest["battery_voltage_v"]:.2f} V')

m5, m6, m7, m8 = st.columns(4)
m5.metric("Battery level estimate", f'{latest["battery_level_estimate"]:.0f}%')
m6.metric("Estimated solar energy", f"{energy_wh:.1f} Wh")
m7.metric("Average temperature", f"{avg_temp:.1f} °C")
m8.metric("Total footstep count", f'{int(df["footstep_count"].sum())}')

tab1, tab2, tab3, tab4 = st.tabs(
    ["📊 Energy Monitoring", "🔮 Availability Prediction", "🌤️ Environment & Activity", "ℹ️ Project Details"]
)

plot_config = {"displayModeBar": False, "responsive": True}

with tab1:
    st.subheader("Solar generation and storage")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.area(
            df, x="timestamp", y="solar_power_w",
            title="Solar PV output power",
            labels={"timestamp": "Time", "solar_power_w": "Power (W)"},
        )
        fig.update_traces(line={"color": "#168aad"}, fillcolor="rgba(22,138,173,.16)")
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10), hovermode="x unified")
        st.plotly_chart(fig, use_container_width=True, config=plot_config)
    with c2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"], y=df["battery_voltage_v"],
            mode="lines+markers", name="Battery voltage",
            line=dict(color="#2a9d8f", width=3),
        ))
        fig.update_layout(
            title="Battery voltage trend", xaxis_title="Time", yaxis_title="Voltage (V)",
            margin=dict(l=10, r=10, t=55, b=10), hovermode="x unified",
        )
        st.plotly_chart(fig, use_container_width=True, config=plot_config)

    st.subheader("Telemetry records")
    view = df[[
        "timestamp", "solar_voltage_v", "solar_current_a", "solar_power_w",
        "battery_voltage_v", "battery_current_a", "light_lux",
        "temperature_c", "footstep_count",
    ]].copy()
    st.dataframe(view.tail(20), use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Solar availability estimate")
    st.write(
        "A time-of-day historical-average baseline is calculated from the available "
        "records. It is a simple reference estimate, not a machine-learning forecast."
    )
    hourly = (
        df.groupby("hour", as_index=False)["solar_power_w"]
        .mean().rename(columns={"solar_power_w": "estimated_average_power_w"})
    )
    full_hours = pd.DataFrame({"hour": range(24)})
    hourly = full_hours.merge(hourly, on="hour", how="left")
    hourly["estimated_average_power_w"] = hourly["estimated_average_power_w"].fillna(0)
    fig = px.bar(
        hourly, x="hour", y="estimated_average_power_w",
        title="Average solar power by hour",
        labels={"hour": "Hour of day", "estimated_average_power_w": "Estimated power (W)"},
    )
    fig.update_traces(marker_color="#168aad")
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True, config=plot_config)

    selected_hour = st.slider("Select hour to inspect", 0, 23, 12)
    selected_value = float(hourly.loc[hourly["hour"] == selected_hour, "estimated_average_power_w"].iloc[0])
    st.metric(f"Historical-average estimate at {selected_hour:02d}:00", f"{selected_value:.2f} W")
    st.caption(
        "Forecast accuracy has not been validated against real-world test measurements. "
        "Collect multiple days of measured data and evaluate on a separate test period "
        "before making performance claims."
    )

with tab3:
    st.subheader("Environmental and activity indicators")
    c1, c2 = st.columns(2)
    with c1:
        fig = px.line(
            df, x="timestamp", y="light_lux", markers=True,
            title="Light intensity", labels={"light_lux": "Illuminance (lux)", "timestamp": "Time"},
        )
        fig.update_traces(line_color="#e9a23b")
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig, use_container_width=True, config=plot_config)
    with c2:
        fig = px.line(
            df, x="timestamp", y="temperature_c", markers=True,
            title="Temperature trend", labels={"temperature_c": "Temperature (°C)", "timestamp": "Time"},
        )
        fig.update_traces(line_color="#e76f51")
        fig.update_layout(margin=dict(l=10, r=10, t=55, b=10))
        st.plotly_chart(fig, use_container_width=True, config=plot_config)

    fig = px.bar(
        df, x="timestamp", y="footstep_count", title="Footstep activity indicator",
        labels={"footstep_count": "Count", "timestamp": "Time"},
    )
    fig.update_traces(marker_color="#2a9d8f")
    fig.update_layout(margin=dict(l=10, r=10, t=55, b=10))
    st.plotly_chart(fig, use_container_width=True, config=plot_config)
    st.caption(
        "Footstep count represents activity only. Piezoelectric voltage, current, power, "
        "and harvested energy are not measured in this dashboard."
    )

with tab4:
    st.subheader("Project overview")
    st.markdown(
        """
        This project explores a hybrid renewable-energy concept that combines solar PV
        generation and piezoelectric energy harvesting with battery storage and proposed
        ESP32-based monitoring.

        **Main blocks**
        - Solar PV energy generation
        - Piezoelectric energy harvesting concept
        - Proposed rectification and DC-DC power conditioning
        - Proposed battery storage and protection
        - Proposed sensor and ESP32 monitoring
        - Dashboard visualization and energy-availability estimation
        """
    )
    st.subheader("Measurement and implementation notes")
    st.info(
        "This public dashboard is currently a software demonstration. The default dataset "
        "is synthetic unless a CSV is uploaded. It is not connected to ESP32, Blynk, or "
        "physical sensors. The battery percentage is a rough voltage-derived display "
        "estimate, not true BMS state of charge (SOC)."
    )
    st.markdown(
        """
        **Piezoelectric measurement:** No piezoelectric electrical output is measured here.
        Footstep count is an activity indicator only.

        **Hardware safety:** A physical build requires verified component ratings, a
        compatible Li-ion charger and BMS, correct power conditioning, wiring protection,
        and supervisor review before energizing the circuit.
        """
    )

st.markdown("---")
st.markdown(
    '<div class="footnote">Renewable Energy Availability Prediction · Academic project dashboard · '
    'Sample-data / uploaded-data visualization</div>',
    unsafe_allow_html=True,
)
