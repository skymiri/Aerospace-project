"""
Notification module
Sends notifications simultaneously via ntfy and Discord Webhook.
"""

import os
import requests
import time
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Read URLs from environment variables
NTFY_URL = os.getenv("NTFY_URL", "https://ntfy.sh")
NTFY_TOPIC = os.getenv("NTFY_TOPIC", "")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")


def send_ntfy_notification(
    message: str,
    title: Optional[str] = None,
    priority: str = "default",
    tags: Optional[list] = None,
) -> bool:
    """
    Sends a notification to an ntfy topic.

    Args:
        message: Message content to send
        title: Notification title (optional)
        priority: Priority level (default, low, min, low, default, high, urgent)
        tags: List of tags (optional, e.g., ["warning", "skull"])

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not NTFY_TOPIC:
        print("⚠️ NTFY_TOPIC is not set.")
        return False

    url = f"{NTFY_URL}/{NTFY_TOPIC}"

    headers = {
        "Title": title or "BCIT Aerospace Alert",
        "Priority": priority,
    }

    if tags:
        headers["Tags"] = ", ".join(tags)

    try:
        response = requests.post(
            url, data=message.encode("utf-8"), headers=headers, timeout=5
        )
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send ntfy notification: {e}")
        return False


def send_discord_notification(
    message: str, title: Optional[str] = None, color: int = 0x3498DB  # 기본 파란색
) -> bool:
    """
    Sends a notification via Discord Webhook.

    Args:
        message: Message content to send
        title: Embed title (optional)
        color: Embed color (hexadecimal, e.g., 0xff0000 = red)

    Returns:
        bool: True if sent successfully, False otherwise
    """
    if not DISCORD_WEBHOOK_URL:
        print("⚠️ DISCORD_WEBHOOK_URL is not set.")
        return False

    # Build payload in Discord Webhook format
    embed = {
        "title": title or "BCIT Aerospace Alert",
        "description": message,
        "color": color,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
    }

    payload = {"embeds": [embed]}

    try:
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Failed to send Discord notification: {e}")
        return False


def send_notification(
    message: str,
    title: Optional[str] = None,
    priority: str = "default",
    tags: Optional[list] = None,
    color: int = 0x3498DB,
) -> dict:
    """
    Sends notifications simultaneously to ntfy and Discord.

    Args:
        message: Message content to send
        title: Notification title (optional)
        priority: ntfy priority level
        tags: List of ntfy tags
        color: Discord embed color

    Returns:
        dict: Sending results for each platform
            {
                "ntfy": bool,
                "discord": bool
            }
    """
    result = {
        "ntfy": send_ntfy_notification(message, title, priority, tags),
        "discord": send_discord_notification(message, title, color),
    }

    return result


# Priority-to-color mapping (for Discord)
PRIORITY_COLORS = {
    "min": 0x95A5A6,  # Gray
    "low": 0x3498DB,  # Blue
    "default": 0x2ECC71,  # Green
    "high": 0xF39C12,  # Orange
    "urgent": 0xE74C3C,  # Red
}


def send_priority_notification(
    message: str,
    title: Optional[str] = None,
    priority: str = "default",
    tags: Optional[list] = None,
) -> dict:
    """
    Sends a notification with color matching the priority level.

    Args:
        message: Message content to send
        title: Notification title
        priority: Priority level (min, low, default, high, urgent)
        tags: List of ntfy tags

    Returns:
        dict: Sending results for each platform
    """
    color = PRIORITY_COLORS.get(priority, 0x3498DB)
    return send_notification(message, title, priority, tags, color)


if __name__ == "__main__":
    # Test execution
    print("Sending test notification...")
    result = send_priority_notification(
        message="This is a test notification. 🚁",
        title="System Test",
        priority="default",
        tags=["test", "rocket"],
    )
    print(f"Send result: {result}")
