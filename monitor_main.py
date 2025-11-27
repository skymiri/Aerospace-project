"""
Monitoring system main execution file
Runs all monitoring modules in parallel.
"""

import threading
import signal
import sys
import os
from dotenv import load_dotenv

# Import monitoring modules
from monitor_latency import monitor_latency_loop
from monitor_drone import monitor_drone_connection_loop
from monitor_system import (
    monitor_sensor_data_loop,
    monitor_database_loop,
    monitor_disk_space_loop,
)

load_dotenv()

# Global variables: thread management
threads = []
running = True


def signal_handler(sig, frame):
    """Cleans up all threads when terminated with Ctrl+C."""
    global running
    print("\n\n🛑 Termination signal received... Stopping all monitoring.")
    running = False

    # Wait for all threads to terminate
    for thread in threads:
        thread.join(timeout=2)

    print("✅ All monitoring stopped.")
    sys.exit(0)


def run_monitor(monitor_func, name: str):
    """
    Runs monitoring function in a separate thread.

    Args:
        monitor_func: Monitoring function to execute
        name: Monitoring name (for logging)
    """
    try:
        print(f"🚀 Starting {name}...")
        monitor_func()
    except Exception as e:
        print(f"❌ {name} error: {e}")


def main():
    """Main execution function"""
    print("=" * 60)
    print("🚁 BCIT Aerospace Monitoring System Starting")
    print("=" * 60)
    print()

    # Check environment variables
    ntfy_topic = os.getenv("NTFY_TOPIC")
    discord_webhook = os.getenv("DISCORD_WEBHOOK_URL")

    if not ntfy_topic:
        print("⚠️ Warning: NTFY_TOPIC is not set.")
    if not discord_webhook:
        print("⚠️ Warning: DISCORD_WEBHOOK_URL is not set.")

    print()

    # Register Ctrl+C handler
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Run each monitoring in a separate thread
    monitors = [
        (monitor_latency_loop, "ntfy Latency Monitoring"),
        (monitor_drone_connection_loop, "Drone Connection Monitoring"),
        (monitor_sensor_data_loop, "Sensor Data Monitoring"),
        (monitor_database_loop, "Database Connection Monitoring"),
        (monitor_disk_space_loop, "Disk Space Monitoring"),
    ]

    for monitor_func, name in monitors:
        thread = threading.Thread(
            target=run_monitor,
            args=(monitor_func, name),
            daemon=True,  # Auto-terminate when main process exits
        )
        thread.start()
        threads.append(thread)
        print(f"✅ {name} thread started")

    print()
    print("=" * 60)
    print("All monitoring is running. Press Ctrl+C to stop.")
    print("=" * 60)
    print()

    # Main thread continues running (threads run in background)
    try:
        while running:
            import time

            time.sleep(1)
    except KeyboardInterrupt:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
