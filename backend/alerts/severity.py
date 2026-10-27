"""
Rule-based severity scoring for anomaly events and alerts.
"""

from typing import List, Optional


def calculate_severity(
    score: float,
    fault_type: Optional[str] = None,
    metric_name: str = "",
    observed: float = 0.0,
    error_rate: float = 0.0,
    latency: float = 0.0,
) -> str:
    """
    Calculate alert severity ("Critical" | "Warning" | "Info") based on domain rules.

    Args:
        score: Anomaly magnitude (e.g. z-score).
        fault_type: RE2-OB fault code (cpu, delay, disk, loss, mem, socket).
        metric_name: Name of anomalous metric.
        observed: Current metric value.
        error_rate: Service error rate.
        latency: Service latency in ms.

    Returns:
        "Critical" | "Warning" | "Info"
    """
    # 1. Critical Rules:
    # - Extreme deviation (score >= 10.0 sigma)
    # - High error rate (> 5%)
    # - Packet loss or socket exhaustion with elevated score
    # - Severe latency spike (> 1000ms)
    if score >= 10.0:
        return "Critical"

    if error_rate >= 0.05:
        return "Critical"

    if latency >= 1000.0:
        return "Critical"

    if fault_type in ("loss", "socket", "disk") and score >= 7.0:
        return "Critical"

    # 2. Warning Rules:
    # - Score >= 6.0 sigma
    # - Elevated latency (> 300ms)
    # - Moderate error rate (> 1%)
    # - Memory pressure near cgroup limits
    if score >= 6.0:
        return "Warning"

    if latency >= 300.0:
        return "Warning"

    if error_rate >= 0.01:
        return "Warning"

    if fault_type == "mem" and score >= 5.0:
        return "Warning"

    # 3. Info Rules (early telemetry drift)
    return "Info"
