import os
import glob
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from zoneinfo import ZoneInfo

# ---- Connection ----
PG_USER = os.getenv("POSTGRES_USER", "postgres")
PG_PW   = os.getenv("POSTGRES_PASSWORD", "postgres")
PG_DB   = os.getenv("POSTGRES_DB", "postgres")
PG_HOST = os.getenv("POSTGRES_HOST", "postgres")
PG_PORT = int(os.getenv("POSTGRES_PORT", "5432"))

engine = create_engine(f"postgresql+psycopg2://{PG_USER}:{PG_PW}@{PG_HOST}:{PG_PORT}/{PG_DB}")

DATA_DIR = "/data"

# ---- Auto-detect files ----
def get_latest(pattern):
    files = sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True)
    if not files:
        raise FileNotFoundError(f"No files matching {pattern}")
    return files[0]

try:
    DRONE_CSV = get_latest(os.path.join(DATA_DIR, "CLEAN_*.csv"))
except FileNotFoundError:
    DRONE_CSV = None
    print("[WARN] No CLEAN_*.csv file found in /data")

try:
    ANEMO_CSV = get_latest(os.path.join(DATA_DIR, "Anemometer_data_*.csv"))
except FileNotFoundError:
    ANEMO_CSV = None
    print("[WARN] No Anemometer_data_*.csv file found in /data")

# ---- Helpers ----
def to_num(x):
    try:
        if x == "" or x is None:
            return None
        return float(x)
    except Exception:
        return None


# ======================================================
# Ingest DRONE CSV
# ======================================================
def ingest_drone():
    if not DRONE_CSV or not os.path.exists(DRONE_CSV):
        print("[SKIP] No cleaned drone CSV found — skipping drone ingestion.")
        return

    print(f"[INFO] Using drone file: {DRONE_CSV}")
    df = pd.read_csv(DRONE_CSV, low_memory=False)

    # --- Timestamps ---
    df["drone_time_utc"] = pd.to_datetime(df.get("Drone_Time(UTC+RFC3339)"), utc=True, errors="coerce")
    pst = pd.to_datetime(df.get("Drone_Time(PST)"), errors="coerce")
    if pst.notna().any():
        pst_aware = pst.dt.tz_localize("America/Vancouver", nonexistent="NaT", ambiguous="NaT")
        df["drone_time_pst"] = pst_aware.dt.tz_convert("UTC")
    else:
        df["drone_time_pst"] = df["drone_time_utc"]

    # --- Flexible direction detection ---
    direction_col = None
    for candidate in ["Drone_Direction", "CUSTOM.heading (°)", "CUSTOM.yaw [°]", "CUSTOM.direction [°]"]:
        if candidate in df.columns:
            direction_col = candidate
            break

    if direction_col:
        df["drone_direction_deg"] = pd.to_numeric(df[direction_col], errors="coerce")
    else:
        print("[WARN] No direction column found — defaulting to 0°.")
        df["drone_direction_deg"] = 0.0

    # --- Speed detection ---
    if "Drone_Speed" in df.columns:
        df["drone_speed_mph"] = pd.to_numeric(df["Drone_Speed"], errors="coerce").fillna(0)
    elif "CUSTOM.speed [m/s]" in df.columns:
        df["drone_speed_mph"] = pd.to_numeric(df["CUSTOM.speed [m/s]"], errors="coerce").fillna(0) * 2.237
    else:
        df["drone_speed_mph"] = 0.0
        print("[WARN] No drone speed column found — assuming stationary drone.")

    # --- Wind-related columns ---
    df["wind_direction"] = df.get("WEATHER.windDirection")
    df["wind_relative_direction"] = df.get("WEATHER.windRelativeDirection")
    df["wind_speed_mph"] = pd.to_numeric(df.get("WEATHER.windSpeed [MPH]"), errors="coerce")
    df["max_wind_speed_mph"] = pd.to_numeric(df.get("WEATHER.maxWindSpeed [MPH]"), errors="coerce")
    df["wind_strength"] = df.get("WEATHER.windStrength")
    df["is_facing_wind"] = df.get("WEATHER.isFacingWind")
    df["is_flying_into_wind"] = df.get("WEATHER.isFlyingIntoWind")
    df["update_time_local_raw"] = df.get("CUSTOM.updateTime [local]")

    # --- True wind compensation ---
    wind_rad = np.deg2rad(df["drone_direction_deg"])
    drone_rad = np.deg2rad(df["drone_direction_deg"])

    wind_u = df["wind_speed_mph"] * np.sin(wind_rad)
    wind_v = df["wind_speed_mph"] * np.cos(wind_rad)
    drone_u = df["drone_speed_mph"] * np.sin(drone_rad)
    drone_v = df["drone_speed_mph"] * np.cos(drone_rad)

    true_u = wind_u - drone_u
    true_v = wind_v - drone_v

    df["true_wind_speed_mph"] = np.sqrt(true_u**2 + true_v**2)
    df["true_wind_direction_deg"] = (np.degrees(np.arctan2(true_u, true_v)) + 360) % 360

    # --- Final selection ---
    out = df[[
        "drone_time_utc",
        "drone_time_pst",
        "update_time_local_raw",
        "wind_direction",
        "wind_relative_direction",
        "wind_speed_mph",
        "max_wind_speed_mph",
        "wind_strength",
        "is_facing_wind",
        "is_flying_into_wind",
        "drone_direction_deg",
        "true_wind_speed_mph",
        "true_wind_direction_deg"
    ]]

    out.to_sql("drone_measurements", engine, if_exists="append", index=False)
    print(f"[INFO] Inserted {len(out)} drone rows ({out['true_wind_speed_mph'].notna().sum()} valid speeds).")


# ======================================================
# Ingest ANEMOMETER CSV
# ======================================================
def ingest_anemometer():
    if not ANEMO_CSV or not os.path.exists(ANEMO_CSV):
        print("[SKIP] No anemometer CSV found — skipping anemometer ingestion.")
        return

    print(f"[INFO] Using anemometer file: {ANEMO_CSV}")
    df = pd.read_csv(ANEMO_CSV, low_memory=False)

    ts_from_ts = pd.to_datetime(df.get("ts"), utc=True, errors="coerce")
    ts_from_raw = pd.to_datetime(df.get("raw_ts"), format="%y:%m:%d:%H:%M:%S.%f", errors="coerce")
    if ts_from_raw.dt.tz is None:
        ts_from_raw = ts_from_raw.dt.tz_localize("UTC")

    ts_utc = ts_from_ts.fillna(ts_from_raw)
    total_rows = len(df)
    bad_ts = ts_utc.isna().sum()
    if bad_ts:
        print(f"[WARN] {bad_ts}/{total_rows} anemometer rows have invalid timestamps — skipped.")

    df["ts_utc"] = ts_utc
    df = df.dropna(subset=["ts_utc"])

    out = pd.DataFrame({
        "ts_utc"        : df["ts_utc"],
        "raw_ts"        : df["raw_ts"].astype(str),
        "u"             : df["U"].apply(to_num),
        "v"             : df["V"].apply(to_num),
        "temperature_c" : df["T"].apply(to_num),
        "battery_pct"   : df["BatteryPct"].apply(to_num),
        "batt_v"        : df["BattV"].apply(to_num),
        "batt_c"        : df["BattC"].apply(to_num),
        "vector_mag"    : df["VectorMag"].apply(to_num),
        "vector_dir_deg": df["VectorDir"].apply(to_num),
    })

    out.to_sql("anemometer_measurements", engine, if_exists="append", index=False)
    print(f"[INFO] Inserted {len(out)} anemometer rows (skipped {bad_ts}).")


# ======================================================
# MAIN
# ======================================================
if __name__ == "__main__":
    ingest_drone()
    ingest_anemometer()
    print("✅ Done.")
