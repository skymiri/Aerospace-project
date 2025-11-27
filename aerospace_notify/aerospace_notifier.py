# author: sky
# Domain-specific notification helper
# - Standardizes message format/tags reflecting "Aerospace project context" for pipeline stages/sensor events.
# - Internally calls NotifyBus to send notifications simultaneously to Flash + ntfy + Slack.
# - Callers (existing scripts) only need to call domain functions; channel details are managed here.

from .notify_bus import NotifyBus

_bus = NotifyBus()


def wind_over_threshold(speed_ms: float, threshold_ms: float, when: str, src: str):
    """
    Wind speed threshold exceeded alert:
    - speed_ms: Measured wind speed (m/s)
    - threshold_ms: Alert threshold value (m/s)
    - when: Display timestamp (e.g., ISO string)
    - src: Data source (e.g., anemometer_convert, watcher, etc.)
    """
    msg = (
        f"[ALERT] Wind {speed_ms:.1f} m/s (> {threshold_ms:.1f} m/s)\n"
        f"- time: {when}\n- source: {src}"
    )
    _bus.warn(msg)


def data_lag(delta_sec: float, source: str):
    """
    Data lag alert:
    - delta_sec: Elapsed seconds since last reception/update
    - source: Data source experiencing lag (e.g., 'DJI vs Anemometer' / 'Drone raw file', etc.)
    """
    msg = f"[WARN] Data lag {delta_sec:.0f}s from '{source}'"
    _bus.warn(msg)


def pipeline_success(stage: str, note: str = ""):
    """
    Pipeline stage success:
    - stage: Stage name (e.g., 'DroneClean', 'AnemometerConvert', 'DBIngest', 'Analytics')
    - note: Additional information (row count, filename, etc.)
    """
    msg = f"[OK] {stage} completed {('- ' + note) if note else ''}"
    _bus.success(msg)


def pipeline_failure(stage: str, err: str):
    """
    Pipeline stage failure:
    - stage: Failed stage name
    - err: Exception message/stack trace portion (may be truncated if too long)
    """
    snippet = (err or "")[:400]  # Limit notification message length for readability
    msg = f"[FAIL] {stage} error\n{snippet}"
    _bus.error(msg)
