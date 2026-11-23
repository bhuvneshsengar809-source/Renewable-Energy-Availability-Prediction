#!/usr/bin/env python3
"""Generate a reproducible synthetic telemetry dataset for project demonstration."""
import argparse, csv, math, random
from datetime import datetime, timedelta

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hours", type=float, default=24)
    ap.add_argument("--interval-min", type=int, default=10)
    ap.add_argument("--output", default="simulation/generated_telemetry.csv")
    args = ap.parse_args()
    random.seed(17)
    start = datetime(2026, 1, 1, 0, 0, 0)
    rows = []
    n = int(args.hours * 60 / args.interval_min) + 1
    soc = 62.0
    for i in range(n):
        ts = start + timedelta(minutes=i*args.interval_min)
        hour = ts.hour + ts.minute/60
        daylight = max(0.0, math.sin(math.pi*(hour-6)/12)) if 6 <= hour <= 18 else 0.0
        cloud = random.uniform(0.72, 1.0)
        solar_power = max(0, 28 * daylight * cloud + random.uniform(-0.4, 0.4))
        footsteps = max(0, int(random.gauss(18 if 8 <= hour <= 20 else 2, 8)))
        piezo_power = max(0, footsteps * random.uniform(0.004, 0.012))
        solar_v = 18.0 if daylight > 0 else 0.2
        solar_i = solar_power / solar_v if solar_v else 0
        piezo_v = 5.0 if piezo_power > 0 else 0.0
        piezo_i = piezo_power / piezo_v if piezo_v else 0
        battery_v = 11.9 + soc/100*0.7
        battery_i = (solar_power + piezo_power - 3.0) / max(battery_v, 1)
        total_p = solar_power + piezo_power
        soc = min(95, max(20, soc + (total_p-3.0)*args.interval_min/60/90*100))
        rows.append({
            "timestamp": ts.isoformat(),
            "solar_voltage_v": round(solar_v, 3),
            "solar_current_a": round(solar_i, 4),
            "solar_power_w": round(solar_power, 4),
            "piezo_voltage_v": round(piezo_v, 3),
            "piezo_current_a": round(piezo_i, 5),
            "piezo_power_w": round(piezo_power, 5),
            "battery_voltage_v": round(battery_v, 3),
            "battery_current_a": round(battery_i, 4),
            "battery_soc_percent_demo": round(soc, 2),
            "footstep_count_demo": footsteps,
            "illuminance_lux_demo": round(70000*daylight*cloud, 1),
            "temperature_c_demo": round(24 + 7*daylight + random.uniform(-1,1), 2),
            "load_power_w_demo": 3.0,
        })
    with open(args.output, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=rows[0].keys())
        w.writeheader(); w.writerows(rows)
    print(f"Wrote {len(rows)} synthetic rows to {args.output}")
    print("NOTE: all generated values are simulated, not measured hardware data.")

if __name__ == "__main__":
    main()
