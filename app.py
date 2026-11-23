"""
Renewable Energy Availability Prediction
Streamlit dashboard for a hybrid solar + piezoelectric energy concept.

IMPORTANT:
- The included dataset is synthetic sample data for demonstration only.
- This app does not connect to ESP32, Blynk, sensors, or a physical prototype.
- Piezoelectric electrical output is not directly measured in this demo.
- Battery percentage is a rough illustrative voltage-based estimate, not BMS SOC.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Renewable Energy Availability Prediction",
    page_icon="☀️",
    layout="wide",
)

st.title("☀️ Renewable Energy Availability Prediction")
st.caption("Hybrid Solar + Piezoelectric Energy Generation and Storage | IoT dashboard concept")

st.warning(
    "DEMO MODE: Charts use synthetic sample data, not live sensor readings. "
    "No physical hardware or ESP32/Blynk connection is active. "
    "Piezoelectric energy output is not directly measured in this demonstration."
)

DATA_PATH = Path(__file__).parent / "simulation" / "sample_telemetry.csv"

REQUIRED_COLUMNS = [
    "timestamp",
    "solar_voltage_v",
    "solar_current_a",
    "battery_voltage_v",
    "battery_current_a",
    "light_lux",
    "temperature_c",
    "footstep_count",
]


def make_sample_data():
    """Create deterministic synthetic data for a one-day dashboard demo."""
    rng = np.random.default_rng(42)
    times = pd.date_range("2026-11-22 06:00", periods=36, freq="30min")
    hour = times.hour + times.minute / 60.0

    daylight = np.clip(np.sin(np.pi * (hour - 6) / 12), 0, None)
    solar_v = 17.5 + 1.2 * daylight + rng.normal(0, 0.25, len(times))
    solar_i = np.clip(1.65 * daylight + rng.normal(0, 0.06, len(times)), 0, None)
    battery_v = 11.4 + 0.55 * daylight + np.linspace(0, 0.12, len(times))
    battery_i = np.clip(0.9 * daylight + rng.normal(0, 0.08, len(times)), 0, None)
    lux = np.clip(42000 * daylight + rng.normal(0, 900, len(times)), 0, None)
    temp = 23 + 7 * daylight + rng.normal(0, 0.7, len(times))
    footsteps = rng.poisson(18, len(times))

    return pd.DataFrame({
        "timestamp": times,
        "solar_voltage_v": np.round(solar_v, 2),
        "solar_current_a": np.round(solar_i, 3),
        "battery_voltage_v": np.round(battery_v, 2),
        "battery_current_a": np.round(battery_i, 3),
        "light_lux": np.round(lux, 0),
        "temperature_c": np.round(temp, 1),
        "footstep_count": footsteps,
    })


def load_data(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
    elif DATA_PATH.exists():
        df = pd.read_csv(DATA_PATH)
    else:
        return make_sample_data(), "Built-in synthetic sample dataset"

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        st.error(
            "CSV format mismatch. Missing columns: "
            + ", ".join(missing)
            + ". Please use the sample CSV format shown in the sidebar."
        )
        st.stop()

    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
    for col in REQUIRED_COLUMNS[1:]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna(subset=["timestamp"]).sort_values("timestamp")
    return df, "Uploaded CSV" if uploaded_file is not None else str(DATA_PATH)


with st.sidebar:
    st.header("Dashboard controls")
    uploaded = st.file_uploader("Upload telemetry CSV (optional)", type=["csv"])
    st.markdown("---")
    st.subheader("CSV columns required")
    st.code(", ".join(REQUIRED_COLUMNS), language="text")
    st.caption(
        "Use sample data for presentation. Uploaded readings are displayed as supplied; "
        "the app does not verify sensor calibration."
    )

df, data_source = load_data(uploaded)

if df.empty:
    st.error("No valid rows found in the selected dataset.")
    st.stop()

df["solar_power_w"] = df["solar_voltage_v"] * df["solar_current_a"]
df["battery_power_w"] = df["battery_voltage_v"] * df["battery_current_a"]
df["hour"] = df["timestamp"].dt.hour

# This is an illustrative voltage-based estimate, not a BMS reading.
# For a nominal 3S Li-ion concept, 9.0–12.6 V is used only as a display range.
df["illustrative_battery_level_pct"] = (
    (df["battery_voltage_v"] - 9.0) / (12.6 - 9.0) * 100
).clip(0, 100)

st.caption(f"Data source: **{data_source}**  |  Records: **{len(df)}**")

latest = df.iloc[-1]
solar_energy_wh = (df["solar_power_w"].sum() * 0.5) if len(df) > 1 else 0.0
avg_solar_power = df["solar_power_w"].mean()
avg_temp = df["temperature_c"].mean()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Latest solar power", f"{latest['solar_power_w']:.1f} W")
c2.metric("Average solar power", f"{avg_solar_power:.1f} W")
c3.metric("Illustrative battery level", f"{latest['illustrative_battery_level_pct']:.0f}%")
c4.metric("Estimated solar energy*", f"{solar_energy_wh:.1f} Wh")

st.caption(
    "*Energy is approximated from the sample interval (30 minutes). "
    "For uploaded data with a different sampling interval, this estimate may not be accurate."
)

tab1, tab2, tab3, tab4 = st.tabs(
    ["Live-style Monitoring", "Energy Prediction", "Environment & Activity", "About the Project"]
)

with tab1:
    st.subheader("Solar and battery monitoring")
    left, right = st.columns(2)

    with left:
        fig = px.line(
            df, x="timestamp", y="solar_power_w",
            markers=True, title="Solar PV power (calculated)"
        )
        fig.update_layout(xaxis_title="Time", yaxis_title="Power (W)")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df["timestamp"], y=df["battery_voltage_v"],
            mode="lines+markers", name="Battery voltage"
        ))
        fig.update_layout(
            title="Battery voltage",
            xaxis_title="Time", yaxis_title="Voltage (V)"
        )
        st.plotly_chart(fig, use_container_width=True)

    st.subheader("Recent telemetry records")
    st.dataframe(
        df[[
            "timestamp", "solar_voltage_v", "solar_current_a",
            "solar_power_w", "battery_voltage_v", "battery_current_a",
            "light_lux", "temperature_c", "footstep_count"
        ]].tail(15),
        use_container_width=True,
        hide_index=True,
    )

with tab2:
    st.subheader("Solar availability prediction")
    st.write(
        "The demo uses a simple time-of-day historical-average baseline. "
        "It groups available records by hour and calculates the mean solar power. "
        "This is a demonstration baseline, not a trained or validated forecasting model."
    )

    hourly = (
        df.groupby("hour", as_index=False)["solar_power_w"]
        .mean()
        .rename(columns={"solar_power_w": "average_solar_power_w"})
    )
    all_hours = pd.DataFrame({"hour": range(24)})
    prediction = all_hours.merge(hourly, on="hour", how="left")
    prediction["average_solar_power_w"] = prediction["average_solar_power_w"].fillna(0)

    fig = px.bar(
        prediction, x="hour", y="average_solar_power_w",
        title="Average solar power by hour (baseline estimate)",
        labels={"hour": "Hour of day", "average_solar_power_w": "Average power (W)"},
    )
    st.plotly_chart(fig, use_container_width=True)

    selected_hour = st.slider("Explore an hour of the day", 0, 23, 12)
    predicted_value = float(
        prediction.loc[prediction["hour"] == selected_hour, "average_solar_power_w"].iloc[0]
    )
    st.metric(f"Baseline estimate at {selected_hour:02d}:00", f"{predicted_value:.2f} W")

    st.info(
        "Prediction quality has not been validated against field measurements. "
        "For a reliable forecast, collect real time-stamped PV readings over multiple days "
        "and evaluate the model on separate test data."
    )

with tab3:
    st.subheader("Environmental and activity indicators")
    left, right = st.columns(2)

    with left:
        fig = px.line(
            df, x="timestamp", y="light_lux",
            markers=True, title="Light intensity (sample BH1750-style data)"
        )
        fig.update_layout(xaxis_title="Time", yaxis_title="Illuminance (lux)")
        st.plotly_chart(fig, use_container_width=True)

    with right:
        fig = px.line(
            df, x="timestamp", y="temperature_c",
            markers=True, title="Temperature (sample sensor-style data)"
        )
        fig.update_layout(xaxis_title="Time", yaxis_title="Temperature (°C)")
        st.plotly_chart(fig, use_container_width=True)

    fig = px.bar(
        df, x="timestamp", y="footstep_count",
        title="Footstep activity count (proxy only)"
    )
    st.plotly_chart(fig, use_container_width=True)
    st.caption(
        "Footstep count is only an activity indicator in this demo. "
        "It is not converted into piezoelectric voltage, current, power, or energy."
    )

with tab4:
    st.subheader("Project overview")
    st.markdown(
        """
        **Objective:** Explore a hybrid renewable-energy concept combining solar PV
        generation and piezoelectric energy harvesting, with battery storage,
        proposed ESP32-based monitoring, and a basic energy-availability estimate.

        **Proposed monitoring concept:** PV and battery electrical measurements,
        light intensity, temperature, and footstep activity indicators.

        **Prediction method:** A transparent time-of-day historical-average baseline
        calculated from the available dataset.

        **Current implementation status:** This dashboard is a software demonstration
        using synthetic sample data. It is not connected to an ESP32, Blynk, sensors,
        battery-management system, or physical prototype.
        """
    )
    st.subheader("Important measurement limitations")
    st.markdown(
        """
        - Piezoelectric electrical output is not directly measured in this dashboard.
        - Battery level shown here is a rough voltage-derived illustration, not true BMS SOC.
        - Synthetic sample data must not be presented as experimental results.
        - Hardware implementation requires correctly rated rectification, DC-DC charging,
          battery protection/BMS, wiring, and electrical safety checks.
        """
    )

st.markdown("---")
st.caption("Academic project demonstration • Hybrid Solar + Piezoelectric Energy Concept")
