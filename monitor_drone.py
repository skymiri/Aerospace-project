"""
Drone connection monitoring module
Periodically checks connection status with drone,
and sends notifications when connection is lost consecutively.
"""

import time
import os
from typing import Optional, Dict
from dotenv import load_dotenv
from notifier import send_priority_notification

load_dotenv()

# Configuration values
CHECK_INTERVAL = int(os.getenv("DRONE_CHECK_INTERVAL", "30"))  # seconds
FAILURE_THRESHOLD = int(
    os.getenv("DRONE_FAILURE_THRESHOLD", "3")
)  # consecutive failure count


def check_drone_connection() -> tuple[bool, Optional[Dict]]:
    """
    Checks drone connection status (sample implementation)

    In actual implementation:
    - Use DJI SDK for connection check
    - Check serial port communication
    - Check network socket connection
    - etc.

    Returns:
        tuple: (connection status, additional info dictionary)
            - connection status: True = connected, False = disconnected
            - additional info: battery, signal strength, etc. (optional)
    """
    # ============================================
    # Sample implementation: randomly returns True/False
    # In actual implementation, replace with real drone connection check code
    # ============================================
    import random

    # 90% probability of successful connection (for testing)
    is_connected = random.random() > 0.1

    if is_connected:
        # Return additional info when connected
        info = {
            "battery": random.randint(20, 100),  # Battery level (%)
            "signal_strength": random.randint(50, 100),  # Signal strength (%)
            "altitude": random.randint(0, 100),  # Altitude (m)
            "gps_status": "good" if random.random() > 0.2 else "poor",
        }
        return True, info
    else:
        return False, None


def get_drone_battery() -> Optional[int]:
    """
    Gets drone battery level (sample implementation)

    Returns:
        int: Battery level (%), None if unavailable
    """
    is_connected, info = check_drone_connection()
    if is_connected and info:
        return info.get("battery")
    return None


def check_drone_battery_low() -> bool:
    """
    Checks if drone battery is low.

    Returns:
        bool: True if battery is low, False otherwise
    """
    BATTERY_LOW_THRESHOLD = int(os.getenv("DRONE_BATTERY_LOW_THRESHOLD", "20"))

    battery = get_drone_battery()
    if battery is not None and battery < BATTERY_LOW_THRESHOLD:
        return True
    return False


def monitor_drone_connection_loop():
    """
    Main loop that periodically monitors drone connection status.
    """
    print(
        f"🚁 Starting drone connection monitoring (interval: {CHECK_INTERVAL}s, threshold: {FAILURE_THRESHOLD} times)"
    )

    consecutive_failures = 0
    last_battery_warning = 0
    BATTERY_WARNING_COOLDOWN = (
        300  # 5 minutes cooldown to prevent duplicate battery warnings
    )

    while True:
        try:
            is_connected, info = check_drone_connection()

            if is_connected:
                consecutive_failures = 0
                print(f"✅ Drone connection normal")

                if info:
                    battery = info.get("battery")
                    signal = info.get("signal_strength")
                    print(f"   Battery: {battery}%, Signal: {signal}%")

                    # Low battery warning
                    if battery is not None and battery < 20:
                        current_time = time.time()
                        if (
                            current_time - last_battery_warning
                            > BATTERY_WARNING_COOLDOWN
                        ):
                            send_priority_notification(
                                message=f"Drone battery is low!\n"
                                f"Current battery: {battery}%\n"
                                f"Signal strength: {signal}%\n"
                                f"Consider landing immediately.",
                                title="🔋 Drone Battery Warning",
                                priority="high",
                                tags=["warning", "battery"],
                            )
                            last_battery_warning = current_time
                            print(f"⚠️ Battery warning sent: {battery}%")

                    # Weak signal warning
                    if signal is not None and signal < 30:
                        send_priority_notification(
                            message=f"Drone signal is weak!\n"
                            f"Signal strength: {signal}%\n"
                            f"Connection may be unstable.",
                            title="📡 Drone Signal Weak",
                            priority="default",
                            tags=["warning", "signal"],
                        )
            else:
                consecutive_failures += 1
                print(
                    f"❌ Drone connection lost (consecutive {consecutive_failures} times)"
                )

                if consecutive_failures >= FAILURE_THRESHOLD:
                    send_priority_notification(
                        message=f"Connection to drone lost!\n"
                        f"Consecutive failures: {consecutive_failures} times\n"
                        f"Please check drone status.",
                        title="🚨 Drone Connection Lost",
                        priority="urgent",
                        tags=["warning", "skull", "rotating_light"],
                    )
                    consecutive_failures = 0  # Reset after notification

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n⏹️ Stopping drone monitoring")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    # Single test execution
    print("Testing drone connection...")
    is_connected, info = check_drone_connection()

    if is_connected:
        print("✅ Drone connected")
        if info:
            print(f"   Battery: {info.get('battery')}%")
            print(f"   Signal: {info.get('signal_strength')}%")
    else:
        print("❌ Drone disconnected")

    # Continuous monitoring mode (uncomment to run)
    # monitor_drone_connection_loop()
