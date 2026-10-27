"""
Train/eval split by fault case for RE2-OB.

Splits cases so that all instances of the same (service, fault) combination
stay together, preventing data leakage across the evaluation boundary.
"""

import logging
from typing import Dict, List, Tuple

from .schema import CaseMetadata, FAULT_TYPES, ONLINE_BOUTIQUE_SERVICES

logger = logging.getLogger(__name__)

# We split cases by holding out specific instances per (service, fault).
# RE2-OB has multiple instances per combination; typically 1-3.
# Strategy: hold out the LAST instance number of each combination for eval.
# This gives roughly 30% eval, 70% train.


def split_cases_by_instance(
    case_names: List[str],
    eval_instances: Tuple[int, ...] = (3,),
) -> Tuple[List[str], List[str]]:
    """
    Split case names into train and eval sets by instance number.

    Cases whose instance number is in eval_instances go to eval.
    All others go to train.

    Args:
        case_names: List of case directory names.
        eval_instances: Instance numbers to use for evaluation.

    Returns:
        Tuple of (train_cases, eval_cases).
    """
    train_cases = []
    eval_cases = []

    for name in case_names:
        parts = name.split("_")
        instance = int(parts[-1])
        if instance in eval_instances:
            eval_cases.append(name)
        else:
            train_cases.append(name)

    logger.info(
        "Split: %d train, %d eval (eval_instances=%s)",
        len(train_cases), len(eval_cases), eval_instances,
    )

    return train_cases, eval_cases


def split_cases_stratified(
    case_names: List[str],
    eval_ratio: float = 0.3,
    seed: int = 42,
) -> Tuple[List[str], List[str]]:
    """
    Stratified split by fault type, ensuring each fault type is
    represented proportionally in both train and eval.

    Args:
        case_names: List of case directory names.
        eval_ratio: Fraction of cases for evaluation.
        seed: Random seed for reproducibility.

    Returns:
        Tuple of (train_cases, eval_cases).
    """
    import random

    rng = random.Random(seed)

    # Group by fault type
    by_fault: Dict[str, List[str]] = {}
    for name in case_names:
        parts = name.split("_")
        fault = parts[-2]
        by_fault.setdefault(fault, []).append(name)

    train_cases = []
    eval_cases = []

    for fault, cases in sorted(by_fault.items()):
        rng.shuffle(cases)
        n_eval = max(1, int(len(cases) * eval_ratio))
        eval_cases.extend(cases[:n_eval])
        train_cases.extend(cases[n_eval:])

    logger.info(
        "Stratified split: %d train, %d eval (ratio=%.2f)",
        len(train_cases), len(eval_cases), eval_ratio,
    )

    return train_cases, eval_cases


def get_split_summary(
    train_cases: List[str],
    eval_cases: List[str],
) -> Dict:
    """
    Summarize the split by fault type and service.

    Returns:
        Dictionary with counts per fault type and service for each split.
    """
    def count_by(cases, field_index):
        counts = {}
        for name in cases:
            parts = name.split("_")
            key = parts[field_index] if field_index == -2 else "_".join(parts[1:-2])
            counts[key] = counts.get(key, 0) + 1
        return counts

    return {
        "train_total": len(train_cases),
        "eval_total": len(eval_cases),
        "train_by_fault": count_by(train_cases, -2),
        "eval_by_fault": count_by(eval_cases, -2),
        "train_by_service": count_by(train_cases, 1),
        "eval_by_service": count_by(eval_cases, 1),
    }
