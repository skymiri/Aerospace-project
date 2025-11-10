from pathlib import Path
import pandas as pd
import sys
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

'''
USAGE:
    CLI:   python Clean_and_Timestamp.py <PATH_TO_RAW_DRONE_CSV>
    Flask: Clean_and_Timestamp.main("/app/uploads/myfile.csv")

PURPOSE:
- Combine CUSTOM.date [local] + CUSTOM.updateTime [local] into "Drone_Time(PST)"
- Convert PST → UTC (RFC3339)
- Output cleaned CSV to /data/CLEAN_<filename>.csv  (matches Docker volume)
'''

def convert_UTC(row):
    pst_time = row['Drone_Time(PST)']
    format_data = "%Y-%m-%d %I:%M:%S.%f %p"
    date = datetime.strptime(pst_time, format_data)
    date_aware = date.replace(tzinfo=ZoneInfo("America/Los_Angeles"))
    utc_time = date_aware.astimezone(timezone.utc)
    return utc_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

def format_time(df_filtered):
    # Combine local date + time columns and create UTC version
    df_filtered['Drone_Time(PST)'] = (
        df_filtered['CUSTOM.date [local]'] + ' ' + df_filtered['CUSTOM.updateTime [local]']
    )
    df_filtered['Drone_Time(UTC+RFC3339)'] = df_filtered.apply(convert_UTC, axis=1)
    df_filtered.drop('CUSTOM.date [local]', axis=1, inplace=True)
    return df_filtered

def main(input_path=None):
    # Determine file path depending on CLI or Flask call
    if input_path is None:
        if len(sys.argv) < 2:
            raise SystemExit("Usage: python Clean_and_Timestamp.py <PATH_TO_RAW_DRONE_CSV>")
        filepath = Path(sys.argv[1])
    else:
        filepath = Path(input_path)

    if not filepath.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")

    filename = filepath.name

    # Save cleaned file directly to /data (shared Docker volume)
    output_dir = Path("/data")
    output_dir.mkdir(parents=True, exist_ok=True)

    csv_path_output = output_dir / f"CLEAN_{filename}"

    # Load CSV and filter relevant columns
    df = pd.read_csv(filepath)
    relevant_cols = [c for c in df.columns if c.startswith('CUSTOM') or c.startswith('WEATHER')]
    df_filtered = df[relevant_cols]

    # Convert timestamps and write output
    formatted_time = format_time(df_filtered)
    formatted_time.to_csv(csv_path_output, index=False)

    print(f"[INFO] Cleaned file written to {csv_path_output}")
    return str(csv_path_output)

if __name__ == "__main__":
    main()
