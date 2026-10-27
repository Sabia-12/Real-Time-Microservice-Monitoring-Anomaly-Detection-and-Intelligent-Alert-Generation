"""
Telemetry enrichment for alerts with domain evidence, descriptions, and log/trace snippets.
"""

from typing import Dict, List, Optional


FAULT_DESCRIPTIONS = {
    "cpu": "CPU throttling and compute saturation",
    "mem": "Memory pressure approaching cgroup limits",
    "disk": "Disk I/O saturation and filesystem write queue blockage",
    "delay": "Network round-trip latency and connection timeout degradation",
    "loss": "Network packet drop and TCP retransmission spike",
    "socket": "Socket limit exhaustion and socket descriptor leaks",
}


def enrich_alert_metadata(
    service: str,
    metric: str,
    observed: float,
    baseline: float,
    score: float,
    fault_type: Optional[str] = None,
    log_snippet: Optional[str] = None,
    trace_snippet: Optional[str] = None,
    correlated_metrics: Optional[List[str]] = None,
) -> Dict[str, str]:
    """
    Generate human-readable title, description, evidence, and affected metrics list.
    """
    fault_label = FAULT_DESCRIPTIONS.get(fault_type or "", "Metric anomaly")
    title = f"{fault_label} on {service}"

    desc = (
        f"{metric} reached {observed:.2f} (baseline ~{baseline:.2f}), "
        f"exceeding normal threshold by {score:.1f}σ."
    )

    evidence_parts = [
        f"Anomaly score {score:.2f}σ observed on {service}.",
    ]
    if correlated_metrics:
        evidence_parts.append(f"Correlated metric shifts detected on: {', '.join(correlated_metrics[:4])}.")
    if log_snippet:
        evidence_parts.append(f"Log evidence: {log_snippet}")
    if trace_snippet:
        evidence_parts.append(f"Trace latency: {trace_snippet}")

    evidence = " ".join(evidence_parts)

    affected = [metric]
    if correlated_metrics:
        affected.extend([m for m in correlated_metrics if m != metric])

    return {
        "title": title,
        "description": desc,
        "evidence": evidence,
        "affected_metrics": affected[:5],
    }
