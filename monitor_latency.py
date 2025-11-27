"""
ntfy server latency monitoring module
Periodically sends ping to ntfy server to measure response time,
and sends notifications when threshold is exceeded.
"""

import time
import requests
import os
from typing import Optional
from dotenv import load_dotenv
from notifier import send_priority_notification

load_dotenv()

NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")

# Configuration values
LATENCY_THRESHOLD = float(os.getenv("LATENCY_THRESHOLD", "3.0"))  # seconds
CHECK_INTERVAL = int(os.getenv("LATENCY_CHECK_INTERVAL", "60"))  # seconds
TEST_MESSAGE = os.getenv("LATENCY_TEST_MESSAGE", "ping")


def check_ntfy_latency() -> Optional[float]:
    """
    Sends a test message to ntfy server and measures response time.

    Returns:
        float: Response time in seconds, None on failure
    """
    if not NTFY_TOPIC:
        print("⚠️ NTFY_TOPIC is not set.")
        return None

    url = f"{NTFY_URL}/{NTFY_TOPIC}"

    try:
        start_time = time.time()
        response = requests.post(
            url,
            data=TEST_MESSAGE.encode("utf-8"),
            headers={"Title": "Latency Test", "Priority": "min"},
            timeout=5,
        )
        response.raise_for_status()
        latency = time.time() - start_time
        return latency
    except requests.exceptions.RequestException as e:
        print(f"❌ ntfy latency 체크 실패: {e}")
        return None


def monitor_latency_loop():
    """
    Main loop that periodically monitors ntfy latency.
    """
    print(
        f"🔍 Starting ntfy latency monitoring (threshold: {LATENCY_THRESHOLD}s, interval: {CHECK_INTERVAL}s)"
    )

    consecutive_failures = 0
    max_consecutive_failures = 3

    while True:
        try:
            latency = check_ntfy_latency()

            if latency is None:
                consecutive_failures += 1
                print(
                    f"⚠️ ntfy server response failed (consecutive {consecutive_failures} times)"
                )

                if consecutive_failures >= max_consecutive_failures:
                    send_priority_notification(
                        message=f"Cannot connect to ntfy server.\nConsecutive failures: {consecutive_failures} times",
                        title="🚨 ntfy Server Connection Failed",
                        priority="urgent",
                        tags=["warning", "skull"],
                    )
                    consecutive_failures = 0  # Reset after notification
            else:
                consecutive_failures = 0

                if latency > LATENCY_THRESHOLD:
                    send_priority_notification(
                        message=f"ntfy server response time exceeded threshold.\n"
                        f"Current latency: {latency:.2f}s\n"
                        f"Threshold: {LATENCY_THRESHOLD}s",
                        title="⚠️ ntfy Latency Warning",
                        priority="high",
                        tags=["warning", "hourglass"],
                    )
                    print(
                        f"⚠️ Latency detected: {latency:.2f}s (threshold: {LATENCY_THRESHOLD}s)"
                    )
                else:
                    print(f"✅ ntfy latency normal: {latency:.2f}s")

            time.sleep(CHECK_INTERVAL)

        except KeyboardInterrupt:
            print("\n⏹️ Stopping latency monitoring")
            break
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            time.sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    # Single test execution
    print("Testing ntfy latency...")
    latency = check_ntfy_latency()

    if latency is not None:
        print(f"✅ Response time: {latency:.2f}s")
        if latency > LATENCY_THRESHOLD:
            print(f"⚠️ Threshold ({LATENCY_THRESHOLD}s) exceeded!")
    else:
        print("❌ Measurement failed")

    # Continuous monitoring mode (uncomment to run)
    # monitor_latency_loop()
