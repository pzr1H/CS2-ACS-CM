#!/usr/bin/env python3
# =============================================================================
# round_dropdown_utils.py — Round Extractor + Label Builder
# Timestamp-TOP: 2025-07-26T12:00-EDT | Version: v0.0001-LOCKED
# Source of Truth: parsed_data["events"] (via event_log.py)
# =============================================================================

# =============================================================================
# BLOCK 1: Imports + Logging Setup
# =============================================================================
import logging
from typing import List, Dict, Any, Set

try:
    from cross_module_debugging import trace_log
except ImportError:
    def trace_log(func): return func  # No-op fallback

log = logging.getLogger(__name__)
log.info("📦 round_dropdown_utils.py loaded")

# =============================================================================
# BLOCK 2: Canonical Round Label Builder
# =============================================================================
@trace_log
def format_round_label(round_num: int) -> str:
    """
    Returns a standard label for round selection dropdowns.
    Example: 7 → 'Round 7'
    """
    return f"Round {round_num}"

# =============================================================================
# BLOCK 3: Extract Unique Rounds From Events
# =============================================================================
@trace_log
def parse_round_dropdown(event_data: List[Dict[str, Any]]) -> List[str]:
    """
    Extracts a sorted list of unique round labels from event data.
    Returns:
        - List[str]: Labels such as 'Round 1', 'Round 2', ...
    """
    round_ids: Set[int] = set()

    for event in event_data:
        round_val = (
            event.get("round") or
            event.get("roundNumber") or
            event.get("roundNum")
        )

        if isinstance(round_val, int):
            round_ids.add(round_val)

    if not round_ids:
        log.warning("⚠️ No rounds found in event data")

    sorted_rounds = sorted(round_ids)
    return [format_round_label(r) for r in sorted_rounds]

# =============================================================================
# BLOCK 4: Round Accessor / Label Lookup (Optional)
# =============================================================================
@trace_log
def get_round_number(label: str) -> int:
    """
    Extracts numeric round value from label string.
    Example: 'Round 12' → 12
    """
    try:
        return int(label.replace("Round", "").strip())
    except Exception:
        log.warning(f"⚠️ Could not parse round number from label: {label}")
        return -1

# =============================================================================
# BLOCK 5: Debug Utility (Optional)
# =============================================================================
@trace_log
def debug_log_rounds(round_labels: List[str]) -> None:
    """
    Prints the parsed round dropdown list.
    """
    print("\n📍 Parsed Round Labels:")
    for label in round_labels:
        print(f"  - {label}")

# =============================================================================
# EOF: round_dropdown_utils.py — TLOC: 89 | Verified by Athlenia QA + pzr1H
# =============================================================================
