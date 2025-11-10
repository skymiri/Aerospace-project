import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os, glob
from datetime import datetime

# ======================================================
# CONFIGURATION
# ======================================================
DATA_DIR = "/data"
CLEANED_DIR = os.path.join(DATA_DIR, "Cleaned")
PLOT_DIR = "/app/static/plots"


# ======================================================
# AUTO-DETECT FILES
# ======================================================
def get_latest(patterns, required=True):
    """Return the newest file matching any of the patterns (list or string)."""
    if isinstance(patterns, str):
        patterns = [patterns]

    matches = []
    for pattern in patterns:
        matches.extend(glob.glob(pattern))

    if not matches:
        if required:
            raise FileNotFoundError(f"No files found matching any of: {patterns}")
        return None

    return max(matches, key=os.path.getmtime)


# ======================================================
# LOAD DATA
# ======================================================
def load_data():
    drone_path = get_latest([
        os.path.join(CLEANED_DIR, "CLEAN_*.csv"),
        os.path.join(DATA_DIR, "CLEAN_*.csv"),
    ])
    anemo_path = get_latest(os.path.join(DATA_DIR, "Anemometer_data_*.csv"))

    print(f"[INFO] Using Drone CSV: {drone_path}")
    print(f"[INFO] Using Anemometer CSV: {anemo_path}")

    drone = pd.read_csv(drone_path, low_memory=False)
    anemo = pd.read_csv(anemo_path, low_memory=False)

    # Normalize timestamps
    drone["Drone_Time(UTC+RFC3339)"] = pd.to_datetime(
        drone["Drone_Time(UTC+RFC3339)"], utc=True, errors="coerce"
    )
    anemo["ts"] = pd.to_datetime(anemo["ts"], utc=True, errors="coerce")

    # Drop invalid timestamps
    drone = drone.dropna(subset=["Drone_Time(UTC+RFC3339)"])
    anemo = anemo.dropna(subset=["ts"])

    # Ensure numeric conversion for all relevant columns
    numeric_cols = [
        "VectorMag", "VectorDir", "U", "V",
        "BatteryPct", "BattV", "BattC",
        "WEATHER.windSpeed [MPH]", "WEATHER.windDirection"
    ]
    for df_name, df in [("Drone", drone), ("Anemometer", anemo)]:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")

    # Debug info for ranges
    print("\n[DEBUG] Drone time range:")
    print(" ", drone["Drone_Time(UTC+RFC3339)"].min(), "→", drone["Drone_Time(UTC+RFC3339)"].max())
    print("[DEBUG] Anemometer time range:")
    print(" ", anemo["ts"].min(), "→", anemo["ts"].max())

    return drone, anemo, drone_path


# ======================================================
# COMPARE WIND DATA
# ======================================================
def compare_vectors(drone, anemo, tolerance_seconds=300):
    """
    Compare wind data between drone and anemometer.
    Tolerance defaults to ±5 minutes to catch minor clock offsets.
    """
    print(f"[INFO] Merging datasets with ±{tolerance_seconds}s tolerance...")

    merged = pd.merge_asof(
        drone.sort_values("Drone_Time(UTC+RFC3339)"),
        anemo.sort_values("ts"),
        left_on="Drone_Time(UTC+RFC3339)",
        right_on="ts",
        direction="nearest",
        tolerance=pd.Timedelta(seconds=tolerance_seconds),
    )

    if "VectorMag" not in merged.columns or "WEATHER.windSpeed [MPH]" not in merged.columns:
        raise KeyError("[ERROR] Missing one or more required columns: 'VectorMag', 'WEATHER.windSpeed [MPH]'")

    # Convert again to be sure (handles merge dtype promotion)
    for col in ["VectorMag", "VectorDir", "WEATHER.windSpeed [MPH]", "WEATHER.windDirection"]:
        merged[col] = pd.to_numeric(merged[col], errors="coerce")

    merged = merged.dropna(subset=["VectorMag", "WEATHER.windSpeed [MPH]"], how="any")

    print(f"[INFO] Matched {len(merged)} rows after merge.")
    if len(merged) == 0:
        print("[WARN] No overlapping timestamps found — check timezone or timestamp offset.")
        return merged

    # Compute metrics
    merged["speed_diff"] = merged["WEATHER.windSpeed [MPH]"] - merged["VectorMag"]
    merged["speed_pct_diff"] = (
        (merged["speed_diff"].abs() / merged["VectorMag"].replace(0, np.nan)) * 100
    )
    merged["dir_diff"] = (
        (merged["WEATHER.windDirection"] - merged["VectorDir"]).abs() % 360
    )

    return merged


# ======================================================
# PLOTTING
# ======================================================
def generate_plots():
    drone, anemo, used_path = load_data()
    merged = compare_vectors(drone, anemo)

    os.makedirs(PLOT_DIR, exist_ok=True)

    if merged.empty:
        print("[ERROR] No merged data available — skipping plot generation.")
        return used_path

    # --- 1. Wind Speed Comparison ---
    plt.figure(figsize=(10, 5))
    plt.plot(
        merged["Drone_Time(UTC+RFC3339)"],
        merged["WEATHER.windSpeed [MPH]"],
        label="Drone Wind Speed (mph)",
    )
    plt.plot(
        merged["Drone_Time(UTC+RFC3339)"],
        merged["VectorMag"],
        label="Anemometer Wind Speed (mph)",
    )
    plt.legend()
    plt.xlabel("Timestamp (UTC)")
    plt.ylabel("Speed (mph)")
    plt.title("Wind Speed Comparison: Drone vs Anemometer (±5 min alignment)")
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/wind_comparison.png", dpi=150)
    plt.close()

    # --- 2. Percentage Difference ---
    plt.figure(figsize=(10, 5))
    plt.plot(
        merged["Drone_Time(UTC+RFC3339)"],
        merged["speed_pct_diff"],
        color="orange",
    )
    plt.xlabel("Timestamp (UTC)")
    plt.ylabel("Speed Difference (%)")
    plt.title("Percentage Difference in Wind Speed (Drone vs Anemometer)")
    plt.axhline(0, color="gray", linestyle="--", linewidth=1)
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/speed_difference.png", dpi=150)
    plt.close()

    # --- 3. Direction Difference ---
    plt.figure(figsize=(10, 5))
    plt.plot(
        merged["Drone_Time(UTC+RFC3339)"],
        merged["dir_diff"],
        color="purple",
    )
    plt.xlabel("Timestamp (UTC)")
    plt.ylabel("Direction Difference (°)")
    plt.title("Wind Direction Difference (Drone vs Anemometer)")
    plt.axhline(0, color="gray", linestyle="--", linewidth=1)
    plt.tight_layout()
    plt.savefig(f"{PLOT_DIR}/direction_difference.png", dpi=150)
    plt.close()

    print(f"[INFO] Saved plots to {PLOT_DIR}/")
    return used_path


# ======================================================
# CLI ENTRYPOINT
# ======================================================
if __name__ == "__main__":
    used = generate_plots()
    print(f"✅ Analytics generated using {used}")
