# author: sky
# Notification Bus (NotifyBus)
# - Sends notifications simultaneously to Flash (browser toast), ntfy (push), and Slack (channel) with a single call.
# - Uses Flash only when web request context is available (has_request_context).
# - Swallows exceptions internally (best-effort) so ntfy/Slack send failures don't break the entire pipeline.
# - Keeps callers simple while 'separating' UI and operational notifications (domain code only calls the bus).

import os
from flask import has_request_context, flash
from .ntfy_client import NtfyClient


class NotifyBus:
    def __init__(self):
        # Assemble ntfy/slack clients. Flexible deployment with environment variable-based configuration.
        self.ntfy = NtfyClient()

        # Common ntfy notification title/link/icon (optional): injected via environment variables
        self.base_title = "Aerospace · Telemetry"
        self.base_click = os.getenv("NTFY_CLICK", "")
        self.base_icon = os.getenv("NTFY_ICON", "")

    # ----------------- Internal utilities (channel-specific helper methods) -----------------
    def _flash(self, message: str, category: str = "info") -> None:
        """
        Displays browser toast using Flask flash.
        - Only works when web request context is available (has_request_context).
        - Category is used for Bootstrap toast color mapping (info/success/warning/danger).
        """
        if has_request_context():
            try:
                flash(message, category)
            except Exception:
                # Flash failure only affects UI. Non-critical, so silently ignore.
                pass

    def _ntfy(self, message: str, *, tags: list[str], priority: str) -> None:
        """
        Sends ntfy push notification.
        - Priority and tags are used for client display/filtering.
        - Swallows exceptions here (network/auth failures) to protect the pipeline.
        """
        try:
            self.ntfy.publish(
                message,
                title=self.base_title,
                priority=priority,
                tags=tags,
                click=self.base_click or None,
                icon=self.base_icon or None,
            )
        except Exception:
            pass

    # ----------------- Public API (by status type) -----------------
    def info(self, message: str) -> None:
        """General information notification (blue color scheme)."""
        self._flash(message, "info")
        self._ntfy(
            message, tags=["information_source", "Aerospace"], priority="default"
        )

    def success(self, message: str) -> None:
        """Success notification (green color scheme)."""
        self._flash(message, "success")
        self._ntfy(message, tags=["ok", "pipeline", "Aerospace"], priority="low")

    def warn(self, message: str) -> None:
        """Warning/alert notification (yellow color scheme)."""
        self._flash(message, "warning")
        self._ntfy(message, tags=["warning", "Aerospace"], priority="high")

    def error(self, message: str) -> None:
        """Error/urgent notification (red color scheme)."""
        self._flash(message, "danger")
        self._ntfy(message, tags=["error", "x", "Aerospace"], priority="urgent")
