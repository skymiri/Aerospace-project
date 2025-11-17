# author: sky
# Minimal ntfy HTTP client implementation
# - Sends messages via HTTP POST to ntfy server (https://ntfy.sh or self-hosted).
# - Body contains the actual notification text; title/priority/tags/click link/icon are set via headers.
# - Automatically adds Authorization header (Bearer token) when using token-based protected topics.
# - Prioritizes environment variables NTFY_SERVER, NTFY_TOPIC, NTFY_TOKEN.
#   (Priority order: code parameters > environment variables > default values)

import os
from typing import Iterable, Optional, Dict
import requests


class NtfyClient:
    def __init__(
        self,
        server: Optional[str] = None,
        topic: Optional[str] = None,
        token: Optional[str] = None,
    ):
        # Server/topic/token: use parameters if provided, otherwise read from environment variables.
        # Server default is public ntfy service (https://ntfy.sh). Can be replaced for self-hosted.
        self.server = (server or os.getenv("NTFY_SERVER") or "https://ntfy.sh").rstrip(
            "/"
        )
        self.topic = topic or os.getenv("NTFY_TOPIC")
        self.token = token or os.getenv("NTFY_TOKEN")

        # Topic is required. Raise error immediately if missing to catch configuration mistakes early.
        if not self.topic:
            raise ValueError("NTFY_TOPIC must be set.")

    def _headers(
        self,
        title: Optional[str],
        priority: Optional[str],
        tags: Optional[Iterable[str]],
        click: Optional[str],
        icon: Optional[str],
        extras: Optional[Dict[str, str]] = None,
    ) -> Dict[str, str]:
        """
        Constructs standard headers recognized by ntfy.
        - Title: Notification title
        - Priority: min/low/default/high/urgent (affects client exposure/sound level)
        - Tags: Emoji/keyword tags (comma-separated). Used for visual emphasis or filtering in client
        - Click: Link (URL) to open when notification is clicked
        - Icon: Icon image (URL) to use in notification
        - Authorization: Bearer <token> (required for authentication with protected topics/self-hosted)
        """
        h: Dict[str, str] = {}
        if title:
            h["Title"] = title
        if priority:
            h["Priority"] = priority  # min, low, default, high, urgent
        if tags:
            h["Tags"] = ",".join(tags)
        if click:
            h["Click"] = click
        if icon:
            h["Icon"] = icon
        if self.token:
            h["Authorization"] = f"Bearer {self.token}"
        if extras:
            # Can add extended headers like X-Actions directly as needed.
            h.update(extras)
        return h

    def publish(
        self,
        message: str,
        *,
        title: Optional[str] = None,
        priority: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
        click: Optional[str] = None,
        icon: Optional[str] = None,
        extras: Optional[Dict[str, str]] = None,
        timeout: int = 10,
    ) -> requests.Response:
        """
        Method that actually sends HTTP POST request to ntfy server.
        - Message (body) is encoded as bytes for transmission.
        - Raises HTTP error via raise_for_status() on failure.
          (Callers can handle with try/except to prevent pipeline breakage)
        """
        url = f"{self.server}/{self.topic}"
        headers = self._headers(title, priority, tags, click, icon, extras)
        resp = requests.post(
            url, data=message.encode("utf-8"), headers=headers, timeout=timeout
        )
        resp.raise_for_status()
        return resp

    # Convenience methods: pre-specify common tags/priority to improve caller readability.
    def info(self, msg, **kw):
        return self.publish(
            msg,
            priority=kw.pop("priority", "default"),
            tags=kw.pop("tags", ["information_source"]),
            **kw,
        )

    def warn(self, msg, **kw):
        return self.publish(
            msg,
            priority=kw.pop("priority", "high"),
            tags=kw.pop("tags", ["warning"]),
            **kw,
        )

    def error(self, msg, **kw):
        return self.publish(
            msg,
            priority=kw.pop("priority", "urgent"),
            tags=kw.pop("tags", ["x", "skull"]),
            **kw,
        )
