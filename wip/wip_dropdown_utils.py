#!/usr/bin/env python3
# =============================================================================
# dropdown_utils.py — TreeView-Aware Dropdown Extractor (v0.0002-FIXED)
# Timestamp-TOP: 2025-07-26T11:50-EDT
# Source of Truth: event_log.py → parsed_data["events"]
# =============================================================================

# =============================================================================
# BLOCK 1: Imports + Trace + Logging Setup
# =============================================================================

import logging
import re
from typing import Dict, List, Tuple, Any, Optional
from tkinter import ttk  # ✅ Required for TreeView type

try:
    from cross_module_debugging import trace_log
except ImportError:
    def trace_log(func): return func  # Stub fallback

from utils.steam_utils import to_steam2

log = logging.getLogger(__name__)
log.info("🧩 dropdown_utils.py loaded (TreeView Extract Mode)")

# =============================================================================
# BLOCK 2: Treeview Extraction Helpers
# =============================================================================

@trace_log
def extract_players_from_treeview(tree: ttk.Treeview) -> list:
    """
    Extract unique player names (Steam2 ID) from the Event Log Treeview widget.
    """
    seen = set()
    players = []

    for child in tree.get_children():
        for grandchild in tree.get_children(child):
            values = tree.item(grandchild, "values")
            if values:
                # Expecting format like [timestamp, type, steamId, name, event]
                name = values[3] if len(values) > 3 else None
                if name and name not in seen:
                    seen.add(name)
                    players.append(name)

    return sorted(players)

@trace_log
def extract_rounds_from_treeview(tree: ttk.Treeview) -> list:
    """
    Extract unique round labels from the Event Log Treeview widget.
    """
    rounds = []
    for child in tree.get_children():
        label = tree.item(child, "text")  # Expecting "Round 1", "Round 2", etc.
        if label and label.startswith("Round"):
            rounds.append(label)
    return rounds

# =============================================================================
# BLOCK 3: Unique Player Extractor — Steam2 Format Preferred
# =============================================================================

@trace_log
def _extract_unique_players(event_data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Extracts unique players from the event log and maps them to metadata keyed by Steam2 ID.
    """
    unique_players = {}

    for event in event_data:
        if event.get("type") != "player_hurt":
            continue

        for role in ["attacker", "victim"]:
            player_info = event.get(role)
            if not player_info:
                continue

            steam_id = player_info.get("steam_id", "")
            name = player_info.get("name", "Unknown")

            if not steam_id or not name:
                continue

            steam2_id = to_steam2(steam_id)
            if steam2_id not in unique_players:
                unique_players[steam2_id] = {
                    "steam2_id": steam2_id,
                    "steam3_id": steam_id,
                    "name": name,
                    "team": player_info.get("team", "Unknown"),
                    "last_seen_ts": event.get("seconds", -1),
                }

    return unique_players

# =============================================================================
# BLOCK 4: Player Dropdown Builder — Label + Metadata Bundle
# =============================================================================

@trace_log
def build_player_dropdown(event_data: List[Dict[str, Any]]) -> Tuple[List[str], Dict[str, Dict[str, Any]]]:
    """
    Builds the player dropdown list and metadata dictionary from parsed events.
    Returns:
        - dropdown_list: Sorted list of display labels.
        - player_metadata: Dict of player info keyed by Steam2 ID.
    """
    player_metadata = _extract_unique_players(event_data)
    dropdown_list = []

    for steam2_id, meta in player_metadata.items():
        label = f"{meta['name']} ({steam2_id})"
        dropdown_list.append(label)

    dropdown_list.sort()
    return dropdown_list, player_metadata

# =============================================================================
# BLOCK 5: Metadata Accessor — Lookup by Steam2 ID or Label
# =============================================================================

@trace_log
def get_player_metadata(label: str, player_metadata: Dict[str, Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Returns metadata for a player given a dropdown label or Steam2 ID.
    Accepts:
        - label: Either "PlayerName (STEAM_1:X:Y)" or just "STEAM_1:X:Y"
        - player_metadata: Metadata dictionary returned from build_player_dropdown
    """
    if not label:
        return None

    # Try direct lookup
    if label in player_metadata:
        return player_metadata[label]

    # Try parsing from label format
    match = re.search(r"\((STEAM_1:[01]:\d+)\)", label)
    if match:
        steam2_id = match.group(1)
        return player_metadata.get(steam2_id)

    return None

# =============================================================================
# BLOCK 6: Debug Utility — Print Dropdown + Metadata Summary
# =============================================================================

@trace_log
def debug_log_dropdown(dropdown_list: List[str], player_metadata: Dict[str, Dict[str, Any]]) -> None:
    """
    Logs the current dropdown list and a summary of associated metadata.
    Useful for debugging dropdown population.
    """
    print("\n🔽 Player Dropdown List:")
    for label in dropdown_list:
        print(f"  - {label}")

    print("\n🧠 Player Metadata Snapshot:")
    for steam2_id, meta in player_metadata.items():
        print(f"  - {steam2_id}: {meta['name']} ({meta.get('team')})")

# =============================================================================
# BLOCK 7: Legacy Aliases (FIXED Scope)
# =============================================================================

parse_player_dropdown = build_player_dropdown  # ✅ FIXED — Global scope alias

# =============================================================================
# EOF: dropdown_utils.py — TLOC: 148 | Version: v0.0002‑FIXED | pzr1H + Athlenia QA
# =============================================================================
