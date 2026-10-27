"""
Data loader for RE2-OB (RCAEval Online Boutique) dataset.

Downloads from HuggingFace and loads parquet files into pandas DataFrames.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd

from .schema import CaseMetadata, ONLINE_BOUTIQUE_SERVICES, FAULT_TYPES

logger = logging.getLogger(__name__)

# Default data directory
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "raw"


def download_re2ob_dataset(
    target_dir: Optional[Path] = None,
    force: bool = False,
) -> Path:
    """
    Download the RE2-OB dataset from HuggingFace.

    Uses huggingface_hub.snapshot_download() with allow_patterns to
    download only the Online Boutique (re2ob_*) cases.

    Args:
        target_dir: Directory to download into. Defaults to data/raw.
        force: If True, re-download even if data exists.

    Returns:
        Path to the downloaded dataset directory.
    """
    from huggingface_hub import snapshot_download

    if target_dir is None:
        target_dir = DEFAULT_DATA_DIR

    target_dir = Path(target_dir)

    # Check if data already exists
    if not force and target_dir.exists():
        existing = list(target_dir.glob("re2ob_*"))
        if len(existing) >= 10:  # At least some cases exist
            logger.info(
                "RE2-OB data already exists at %s (%d cases found)",
                target_dir, len(existing),
            )
            return target_dir

    logger.info("Downloading RE2-OB dataset to %s ...", target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    downloaded_path = snapshot_download(
        repo_id="phamquiluan/RCAEval",
        repo_type="dataset",
        allow_patterns="re2ob_*/**",
        local_dir=str(target_dir),
    )

    logger.info("Download complete: %s", downloaded_path)
    return Path(downloaded_path)


def list_cases(data_dir: Optional[Path] = None) -> List[str]:
    """
    List all RE2-OB case directory names.

    Args:
        data_dir: Root data directory. Defaults to data/raw.

    Returns:
        Sorted list of case directory names (e.g., ['re2ob_adservice_cpu_1', ...]).
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    data_dir = Path(data_dir)
    cases = sorted([
        d.name for d in data_dir.iterdir()
        if d.is_dir() and d.name.startswith("re2ob_")
    ])

    logger.info("Found %d RE2-OB cases in %s", len(cases), data_dir)
    return cases


def load_inject_time(case_dir: Path) -> float:
    """
    Load the fault injection timestamp from inject_time.txt.

    Args:
        case_dir: Path to a case directory.

    Returns:
        Injection time as a Unix timestamp (float, seconds).
    """
    inject_file = case_dir / "inject_time.txt"
    if not inject_file.exists():
        raise FileNotFoundError(f"inject_time.txt not found in {case_dir}")

    text = inject_file.read_text().strip()
    return float(text)


def load_metrics(case_dir: Path) -> pd.DataFrame:
    """
    Load metrics.parquet from a case directory.

    Args:
        case_dir: Path to a case directory.

    Returns:
        DataFrame with a 'time' column (Unix seconds) and metric columns.
    """
    parquet_file = case_dir / "metrics.parquet"
    if not parquet_file.exists():
        raise FileNotFoundError(f"metrics.parquet not found in {case_dir}")

    df = pd.read_parquet(parquet_file)
    logger.debug(
        "Loaded %s: %d rows, %d columns",
        case_dir.name, len(df), len(df.columns),
    )
    return df


def load_case(
    case_name: str,
    data_dir: Optional[Path] = None,
) -> Tuple[pd.DataFrame, CaseMetadata]:
    """
    Load a single RE2-OB case: metrics + metadata.

    Args:
        case_name: Case directory name (e.g., 're2ob_adservice_cpu_1').
        data_dir: Root data directory. Defaults to data/raw.

    Returns:
        Tuple of (metrics_df, case_metadata).
    """
    if data_dir is None:
        data_dir = DEFAULT_DATA_DIR

    case_dir = Path(data_dir) / case_name

    if not case_dir.exists():
        raise FileNotFoundError(f"Case directory not found: {case_dir}")

    # Load metrics
    metrics_df = load_metrics(case_dir)

    # Parse metadata from directory name
    metadata = CaseMetadata.from_directory_name(case_name)

    # Load injection time
    metadata.inject_time = load_inject_time(case_dir)

    # Populate additional metadata
    metric_cols = [c for c in metrics_df.columns if c != "time"]
    metadata.num_metric_columns = len(metric_cols)
    metadata.num_rows = len(metrics_df)
    metadata.metric_columns = metric_cols

    if len(metrics_df) >= 2:
        times = metrics_df["time"].sort_values()
        metadata.duration_seconds = float(times.iloc[-1] - times.iloc[0])

    metadata.has_logs = (case_dir / "logs.parquet").exists()
    metadata.has_traces = (case_dir / "traces.parquet").exists()

    return metrics_df, metadata


def load_all_cases(
    data_dir: Optional[Path] = None,
) -> List[Tuple[pd.DataFrame, CaseMetadata]]:
    """
    Load all RE2-OB cases.

    Args:
        data_dir: Root data directory.

    Returns:
        List of (metrics_df, metadata) tuples.
    """
    cases = list_cases(data_dir)
    results = []

    for case_name in cases:
        try:
            df, meta = load_case(case_name, data_dir)
            results.append((df, meta))
        except Exception as e:
            logger.error("Failed to load case %s: %s", case_name, e)

    logger.info("Loaded %d / %d cases successfully", len(results), len(cases))
    return results
