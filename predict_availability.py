#!/usr/bin/env python3
"""Transparent time-of-day historical-average renewable energy baseline."""
import argparse, math
import pandas as pd

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="CSV with timestamp, solar_power_w, piezo_power_w")
    ap.add_argument("--horizon-min", type=int, default=60)
    ap.add_argument("--bucket-hours", type=int, default=1)
    ap.add_argument("--test-fraction", type=float, default=0.25)
    ap.add_argument("--output", default="prediction/predictions.csv")
    args = ap.parse_args()

    df = pd.read_csv(args.input, parse_dates=["timestamp"]).sort_values("timestamp")
    required = {"timestamp", "solar_power_w", "piezo_power_w"}
    missing = required - set(df.columns)
    if missing:
        raise SystemExit(f"Missing columns: {sorted(missing)}")
    df["source_power_w"] = df["solar_power_w"].clip(lower=0) + df["piezo_power_w"].clip(lower=0)
    # Target: observed energy during the next horizon, using sample interval inferred from timestamps.
    dt_h = df["timestamp"].diff().dt.total_seconds().median()/3600
    if pd.isna(dt_h) or dt_h <= 0:
        raise SystemExit("Could not infer a positive sampling interval from timestamps.")
    samples = max(1, round((args.horizon_min/60)/dt_h))
    df["actual_future_energy_wh"] = df["source_power_w"].shift(-1).rolling(samples, min_periods=samples).sum().shift(-(samples-1))*dt_h
    df["bucket"] = (df["timestamp"].dt.hour // args.bucket_hours) * args.bucket_hours

    split = max(1, int(len(df)*(1-args.test_fraction)))
    train = df.iloc[:split].copy()
    test = df.iloc[split:].copy()
    means = train.groupby("bucket")["source_power_w"].mean()
    overall = train["source_power_w"].mean()
    test["predicted_energy_wh"] = test["bucket"].map(means).fillna(overall) * (args.horizon_min/60)
    valid = test.dropna(subset=["actual_future_energy_wh"])
    if len(valid):
        err = valid["predicted_energy_wh"] - valid["actual_future_energy_wh"]
        mae = err.abs().mean()
        rmse = math.sqrt((err**2).mean())
        print(f"Holdout MAE: {mae:.4f} Wh")
        print(f"Holdout RMSE: {rmse:.4f} Wh")
    else:
        print("Not enough rows for holdout evaluation; add more samples or reduce horizon.")
    cols = ["timestamp","solar_power_w","piezo_power_w","predicted_energy_wh","actual_future_energy_wh"]
    test[cols].to_csv(args.output, index=False)
    print(f"Saved predictions to {args.output}")
    print("Interpretation: estimated renewable source energy, not guaranteed load-deliverable energy.")
    print("Use real calibrated measurements and a chronological held-out test period for project claims.")

if __name__ == "__main__":
    main()
