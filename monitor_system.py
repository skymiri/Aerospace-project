"""
System monitoring module
Monitors additional events such as sensor data anomalies, server errors, and database connections.
"""

import time
import os
import numpy as np
from typing import Optional, Dict, List
from dotenv import load_dotenv
from notifier import send_priority_notification

load_dotenv()


# ============================================
# Sensor data anomaly detection
# ============================================


def check_sensor_anomaly(sensor_data: Dict[str, float]) -> Optional[Dict]:
    """
    Detects anomalies in sensor data.

    Args:
        sensor_data: Sensor data dictionary
            Example: {
                "wind_speed": 15.5,  # m/s
                "wind_direction": 180,  # degrees
                "temperature": 25.3,  # celsius
                "humidity": 60.0,  # %
                "pressure": 1013.25  # hPa
            }

    Returns:
        Dict: Anomaly information or None
            {
                "sensor": "wind_speed",
                "value": 150.0,
                "expected_range": (0, 50),
                "severity": "high"
            }
    """
    # Define normal ranges
    thresholds = {
        "wind_speed": {"min": 0, "max": 50, "severity": "high"},  # m/s
        "wind_direction": {"min": 0, "max": 360, "severity": "default"},  # degrees
        "temperature": {"min": -40, "max": 60, "severity": "default"},  # celsius
        "humidity": {"min": 0, "max": 100, "severity": "default"},  # %
        "pressure": {"min": 800, "max": 1100, "severity": "high"},  # hPa
    }

    anomalies = []

    for sensor, value in sensor_data.items():
        if sensor in thresholds:
            threshold = thresholds[sensor]
            if value < threshold["min"] or value > threshold["max"]:
                anomalies.append(
                    {
                        "sensor": sensor,
                        "value": value,
                        "expected_range": (threshold["min"], threshold["max"]),
                        "severity": threshold["severity"],
                    }
                )

    if anomalies:
        # Return the most severe anomaly
        severity_order = {"high": 2, "default": 1, "low": 0}
        return max(anomalies, key=lambda x: severity_order.get(x["severity"], 0))

    return None


def check_sensor_statistical_anomaly(
    sensor_values: List[float], sensor_name: str, z_threshold: float = 3.0
) -> Optional[Dict]:
    """
    Detects anomalies using statistical method (Z-score).

    Args:
        sensor_values: List of sensor values (recent N measurements)
        sensor_name: Sensor name
        z_threshold: Z-score threshold (default 3.0 = 3 sigma)

    Returns:
        Dict: Anomaly information or None
    """
    if len(sensor_values) < 10:  # Minimum data points required
        return None

    values = np.array(sensor_values)
    mean = np.mean(values)
    std = np.std(values)

    if std == 0:
        return None

    # Calculate Z-score of the latest value
    latest_value = values[-1]
    z_score = abs((latest_value - mean) / std)

    if z_score > z_threshold:
        return {
            "sensor": sensor_name,
            "value": latest_value,
            "mean": mean,
            "std": std,
            "z_score": z_score,
            "severity": "high" if z_score > 4.0 else "default",
        }

    return None


# ============================================
# Database connection monitoring
# ============================================


def check_database_connection() -> tuple[bool, Optional[str]]:
    """
    Checks database connection status.

    Returns:
        tuple: (connection status, error message)
    """
    try:
        from sqlalchemy import create_engine, text

        # Read DB connection info from environment variables
        db_url = os.getenv("DATABASE_URL")
        if not db_url:
            return False, "DATABASE_URL environment variable is not set."

        engine = create_engine(db_url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))

        return True, None
    except Exception as e:
        return False, str(e)


# ============================================
# Disk space monitoring
# ============================================


def check_disk_space(path: str = "/") -> Optional[Dict]:
    """
    Checks disk usage.

    Args:
        path: Path to check

    Returns:
        Dict: Disk information or None
            {
                "total": 1000000000,  # bytes
                "used": 800000000,
                "free": 200000000,
                "percent": 80.0
            }
    """
    try:
        import shutil

        total, used, free = shutil.disk_usage(path)
        percent = (used / total) * 100

        return {"total": total, "used": used, "free": free, "percent": percent}
    except Exception as e:
        print(f"Failed to check disk space: {e}")
        return None


# ============================================
# Main monitoring loops
# ============================================


def monitor_sensor_data_loop():
    """
    Periodically checks sensor data and detects anomalies.
    """
    print("📊 Starting sensor data monitoring...")

    # Sample data (in actual implementation, read from sensors)
    sensor_history = {"wind_speed": [], "temperature": [], "pressure": []}

    CHECK_INTERVAL = int(os.getenv("SENSOR_CHECK_INTERVAL", "60"))
    HISTORY_SIZE = 100  # Keep only the last 100 values

    while True:
        try:
            # Generate sample sensor data (in actual implementation, read from sensors)
            import random

            current_data = {
                "wind_speed": random.uniform(0, 30)
                + random.choice([0, 0, 0, 50]),  # Occasionally anomalies
                "wind_direction": random.uniform(0, 360),
                "temperature": random.uniform(10, 30),
                "humidity": random.uniform(40, 80),
                "pressure": random.uniform(980, 1020),
            }

            # 1. Range-based anomaly detection
            anomaly = check_sensor_anomaly(current_data)
            if anomaly:
                send_priority_notification(
                    message=f"Sensor anomaly detected!\n"
                    f"Sensor: {anomaly['sensor']}\n"
                    f"Value: {anomaly['value']}\n"
                    f"Normal range: {anomaly['expected_range'][0]} ~ {anomaly['expected_range'][1]}",
                    title="⚠️ Sensor Data Anomaly",
                    priority=anomaly["severity"],
                    tags=["warning", "chart_with_downwards_trend"],
                )
                print(f"⚠️ Anomaly detected: {anomaly['sensor']} = {anomaly['value']}")

            # 2. Statistical anomaly detection
            for sensor_name in sensor_history:
                if sensor_name in current_data:
                    sensor_history[sensor_name].append(current_data[sensor_name])
                    if len(sensor_history[sensor_name]) > HISTORY_SIZE:
                        sensor_history[sensor_name].pop(0)

                    stat_anomaly = check_sensor_statistical_anomaly(
                        sensor_history[sensor_name], sensor_name
                    )
                    if stat_anomaly:
                        send_priority_notification(
                            message=f"Statistical sensor anomaly detected!\n"
                            f"Sensor: {stat_anomaly['sensor']}\n"
                            f"Value: {stat_anomaly['value']:.2f}\n"
                            f"Mean: {stat_anomaly['mean']:.2f}\n"
                            f"Z-score: {stat_anomaly['z_score']:.2f}",
                            title="📈 Sensor Statistical Anomaly",
                            priority=stat_anomaly["severity"],
                            tags=["warning", "chart_with_upwards_trend"],
                        )
                        print(
                            f"⚠️ Statistical anomaly: {stat_anomaly['sensor']} (Z-score: {stat_anomaly['z_score']:.2f})"
                        )

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n⏹️ Stopping sensor monitoring")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)


def monitor_database_loop():
    """
    Periodically checks database connection.
    """
    print("🗄️ Starting database connection monitoring...")

    CHECK_INTERVAL = int(os.getenv("DB_CHECK_INTERVAL", "120"))
    consecutive_failures = 0
    FAILURE_THRESHOLD = 2

    while True:
        try:
            is_connected, error_msg = check_database_connection()

            if is_connected:
                consecutive_failures = 0
                print("✅ Database connection normal")
            else:
                consecutive_failures += 1
                print(f"❌ Database connection failed: {error_msg}")

                if consecutive_failures >= FAILURE_THRESHOLD:
                    send_priority_notification(
                        message=f"Database connection lost!\n"
                        f"Error: {error_msg}\n"
                        f"Consecutive failures: {consecutive_failures} times",
                        title="🚨 Database Connection Failed",
                        priority="urgent",
                        tags=["warning", "skull", "database"],
                    )
                    consecutive_failures = 0

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n⏹️ Stopping database monitoring")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)


def monitor_disk_space_loop():
    """
    Periodically checks disk space.
    """
    print("💾 Starting disk space monitoring...")

    CHECK_INTERVAL = int(os.getenv("DISK_CHECK_INTERVAL", "300"))  # 5 minutes
    WARNING_THRESHOLD = 80.0  # Warning when usage >= 80%
    CRITICAL_THRESHOLD = 90.0  # Critical warning when usage >= 90%

    while True:
        try:
            disk_info = check_disk_space()

            if disk_info:
                percent = disk_info["percent"]
                free_gb = disk_info["free"] / (1024**3)

                if percent >= CRITICAL_THRESHOLD:
                    send_priority_notification(
                        message=f"Disk space is almost full!\n"
                        f"Usage: {percent:.1f}%\n"
                        f"Free space: {free_gb:.2f} GB\n"
                        f"Immediate action required!",
                        title="🚨 Disk Space Low (Critical)",
                        priority="urgent",
                        tags=["warning", "skull", "floppy_disk"],
                    )
                    print(f"🚨 Disk space critical: {percent:.1f}%")
                elif percent >= WARNING_THRESHOLD:
                    send_priority_notification(
                        message=f"Disk space is running low.\n"
                        f"Usage: {percent:.1f}%\n"
                        f"Free space: {free_gb:.2f} GB",
                        title="⚠️ Disk Space Warning",
                        priority="high",
                        tags=["warning", "floppy_disk"],
                    )
                    print(f"⚠️ Disk space warning: {percent:.1f}%")
                else:
                    print(f"✅ Disk space normal: {percent:.1f}%")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n⏹️ Stopping disk monitoring")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)


# ============================================
# Server error handler (can be integrated into Flask app)
# ============================================


def handle_server_error(error: Exception, context: str = ""):
    """
    Sends notification when server error occurs.
    Can be called from Flask app's error handler.

    Args:
        error: Exception object that occurred
        context: Error context (e.g., "file upload", "data processing")
    """
    error_msg = str(error)
    error_type = type(error).__name__

    send_priority_notification(
        message=f"Server error occurred!\n"
        f"Context: {context}\n"
        f"Error type: {error_type}\n"
        f"Error message: {error_msg}",
        title="🚨 Server Error",
        priority="urgent",
        tags=["warning", "skull", "computer"],
    )

    print(f"🚨 Server error notification sent: {error_type} - {error_msg}")


if __name__ == "__main__":
    # Test execution
    print("=== Sensor Data Anomaly Test ===")
    test_data = {
        "wind_speed": 150.0,  # Anomaly
        "temperature": 25.0,
        "pressure": 500.0,  # Anomaly
    }
    anomaly = check_sensor_anomaly(test_data)
    print(f"Anomaly detected: {anomaly}")

    print("\n=== Database Connection Test ===")
    is_connected, error = check_database_connection()
    print(f"Connection status: {is_connected}, Error: {error}")

    print("\n=== Disk Space Test ===")
    disk_info = check_disk_space()
    if disk_info:
        print(f"Disk usage: {disk_info['percent']:.1f}%")
