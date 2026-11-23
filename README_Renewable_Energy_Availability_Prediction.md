# Renewable Energy Availability Prediction

A hybrid renewable-energy project concept combining **solar photovoltaic (PV) generation**, **piezoelectric energy harvesting**, **battery storage**, and **IoT-based monitoring** with a basic renewable-energy availability prediction dashboard.

> **Project status:** This repository contains a software demonstration and proposed system design. The sample dataset is synthetic. No physical prototype, live ESP32 connection, or real sensor measurements are claimed.

## Project Objectives

- Explain a hybrid solar and piezoelectric energy-generation concept.
- Present a proposed battery-storage and monitoring architecture.
- Visualize solar and battery telemetry using a Streamlit dashboard.
- Estimate solar-energy availability using a simple time-of-day historical-average baseline.
- Provide sample data, simulation scripts, proposed firmware, and project documentation.

## System Overview

The proposed concept combines:

1. **Solar PV source** – converts sunlight into DC electrical energy.
2. **Piezoelectric harvesting concept** – converts mechanical pressure or footsteps into electrical energy.
3. **Power-conditioning stage** – proposed rectification and DC-DC conditioning for the sources.
4. **Battery storage** – proposed Li-ion battery storage with an appropriate protection/management system.
5. **ESP32-based monitoring concept** – proposed controller for collecting selected sensor and electrical measurements.
6. **Dashboard and prediction** – displays sample telemetry and a simple solar-availability estimate.

## Repository Structure

```text
.
├── README.md
├── LICENSE
├── requirements.txt
├── app.py
├── documents/
│   ├── Project_Report_Final.pdf
│   └── Project_Synopsis_Final.pdf
├── presentation/
│   └── Project_Presentation.pptx
├── hardware_source/
│   ├── firmware/
│   │   └── renewable_energy_blynk_v2.ino
│   └── ...
├── simulation/
│   ├── sample_telemetry.csv
│   └── simulate_project.py
├── prediction/
│   ├── predict_availability.py
│   └── sample_predictions.csv
└── dashboard_demo/
    └── index.html
```

The exact contents may vary slightly depending on which project files have been uploaded to the repository.

## Streamlit Dashboard

The Streamlit application is `app.py`. It provides:

- Solar power visualization (calculated as voltage × current).
- Battery-voltage visualization.
- An illustrative battery-level indicator.
- A time-of-day solar-power baseline estimate.
- Light-intensity, temperature, and footstep-activity charts.
- CSV upload support for compatible telemetry data.

### Run Locally

Use Python 3.9 or newer.

```bash
pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL printed by Streamlit in your terminal.

### Deploy on Streamlit Community Cloud

1. Push `app.py`, `requirements.txt`, and the project files to GitHub.
2. Open [Streamlit Community Cloud](https://share.streamlit.io/).
3. Choose **Deploy an app** and connect your GitHub account if prompted.
4. Select this repository and the `main` branch.
5. Set the main file path to `app.py`.
6. Deploy the application.

## CSV Data Format

The dashboard accepts a CSV containing these columns:

```text
timestamp,solar_voltage_v,solar_current_a,battery_voltage_v,battery_current_a,light_lux,temperature_c,footstep_count
```

- `timestamp`: date and time of the reading.
- `solar_voltage_v`: PV-side voltage in volts.
- `solar_current_a`: PV-side current in amperes.
- `battery_voltage_v`: battery voltage in volts.
- `battery_current_a`: battery-path current in amperes.
- `light_lux`: light intensity in lux.
- `temperature_c`: temperature in degrees Celsius.
- `footstep_count`: activity count used as an indicator only.

If `simulation/sample_telemetry.csv` is available, the dashboard loads it by default. Otherwise, it generates a built-in synthetic demonstration dataset.

## Prediction Method

The dashboard uses a **time-of-day historical-average baseline**: it groups the available solar-power records by hour and calculates the average power for each hour. This is a simple demonstration method, not a trained or field-validated forecasting model.

## Important Limitations and Safety Notes

- The included sample data is synthetic and must not be described as measured experimental results.
- The dashboard does not connect to an ESP32, Blynk, or physical sensors.
- Piezoelectric voltage, current, power, and energy are **not directly measured** by this dashboard. Footstep count is only an activity indicator.
- The displayed battery percentage is a rough voltage-derived illustration, not true BMS state of charge (SOC).
- The prediction method has not been validated against real-world measurements.
- The proposed hardware design is not a construction-ready wiring approval. Before any physical implementation, verify battery chemistry, cell configuration, charger compatibility, BMS ratings, converter ratings, insulation, protection, and all wiring with a qualified supervisor.

## Technologies and Tools

- Python
- Streamlit
- Pandas
- NumPy
- Plotly
- ESP32 / Arduino-style firmware concept
- Solar PV and piezoelectric energy-harvesting concepts

## License

This project is released under the **MIT License**. See the `LICENSE` file for details.

---

**Academic project demonstration:** Renewable Energy Availability Prediction – A Hybrid Solar and Piezoelectric Energy Generation and Storage System.
