"""
Metric schema and service catalog for Online Boutique (RE2-OB).

Defines the canonical service list, fault types, and metric-category
mappings derived from Phase 1 dataset analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Set

# ── Online Boutique services ──────────────────────────────────────────

ONLINE_BOUTIQUE_SERVICES: List[str] = [
    "adservice",
    "cartservice",
    "checkoutservice",
    "currencyservice",
    "emailservice",
    "frontend",
    "paymentservice",
    "productcatalogservice",
    "recommendationservice",
    "shippingservice",
]

# ── RE2-OB fault types ───────────────────────────────────────────────

FAULT_TYPES: List[str] = [
    "cpu",
    "delay",
    "disk",
    "loss",
    "mem",
    "socket",
]

# ── Metric categories ────────────────────────────────────────────────
# Each category maps to substrings found in RE2-OB column names.
# Columns are named: {service}_{metric_name}

METRIC_CATEGORIES: Dict[str, List[str]] = {
    "cpu": [
        "cg_cpu_usage_total",
        "cpu_usage_seconds_total",
        "cpu_user_seconds_total",
        "cpu_system_seconds_total",
        "cpu_cfs_throttled",
    ],
    "memory": [
        "cg_mem_usage",
        "cg_mem_limit",
        "cg_mem_cache",
        "cg_mem_rss",
        "memory_usage_bytes",
        "memory_working_set_bytes",
    ],
    "network": [
        "net_rx_bytes",
        "net_tx_bytes",
        "net_rx_packets",
        "net_tx_packets",
        "net_rx_errors",
        "net_tx_errors",
        "net_rx_dropped",
        "net_tx_dropped",
    ],
    "disk": [
        "fs_usage_bytes",
        "fs_limit_bytes",
        "fs_reads_total",
        "fs_writes_total",
        "fs_read_seconds_total",
        "fs_write_seconds_total",
        "diskio_reads",
        "diskio_writes",
    ],
    "latency": [
        "request_duration",
        "request_latency",
        "grpc_server_handling_seconds",
        "http_request_duration",
        "response_time",
    ],
    "error": [
        "error_count",
        "grpc_server_handled_total",
        "http_requests_total",
        "request_count",
        "error_rate",
    ],
    "workload": [
        "tasks_state",
        "threads",
        "goroutines",
        "process_open_fds",
        "process_max_fds",
    ],
}


def categorize_metric(column_name: str) -> str:
    """
    Map a metric column name to its category.

    Args:
        column_name: Column name from the parquet file (e.g., 'frontend_cg_cpu_usage_total').

    Returns:
        Category string (e.g., 'cpu', 'memory'), or 'other' if no match.
    """
    col_lower = column_name.lower()
    for category, patterns in METRIC_CATEGORIES.items():
        for pattern in patterns:
            if pattern in col_lower:
                return category
    return "other"


def extract_service_from_column(column_name: str) -> str:
    """
    Extract the service name from a metric column.

    RE2-OB columns are named {service}_{metric_name}. We match against
    the known service list to find the longest matching prefix.

    Args:
        column_name: Column name (e.g., 'frontend_cg_cpu_usage_total').

    Returns:
        Service name or 'unknown'.
    """
    for service in sorted(ONLINE_BOUTIQUE_SERVICES, key=len, reverse=True):
        if column_name.startswith(service + "_"):
            return service
    return "unknown"


@dataclass
class CaseMetadata:
    """Metadata for a single RE2-OB case."""
    case_id: str
    service: str
    fault_type: str
    instance: int
    inject_time: float  # Unix timestamp in seconds
    num_metric_columns: int = 0
    num_rows: int = 0
    duration_seconds: float = 0.0
    has_logs: bool = False
    has_traces: bool = False
    metric_columns: List[str] = field(default_factory=list)

    @classmethod
    def from_directory_name(cls, dirname: str) -> "CaseMetadata":
        """
        Parse RE2-OB directory name into metadata.

        Expected format: re2ob_{service}_{fault}_{instance}

        Args:
            dirname: Directory name like 're2ob_adservice_cpu_1'.

        Returns:
            CaseMetadata with service, fault_type, and instance populated.
        """
        parts = dirname.split("_")
        # Format: re2ob_{service}_{fault}_{instance}
        # Some services have multi-word names like 'productcatalogservice'
        # Strategy: match from the end (instance is last, fault is second-to-last)
        instance = int(parts[-1])
        fault_type = parts[-2]

        # Service name is everything between 'ob' prefix and fault type
        # e.g. re2ob_productcatalogservice_cpu_1 -> parts = [re2ob, productcatalogservice, cpu, 1]
        service = "_".join(parts[1:-2])

        return cls(
            case_id=dirname,
            service=service,
            fault_type=fault_type,
            instance=instance,
            inject_time=0.0,
        )
