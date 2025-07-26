#!/usr/bin/env python3
# =============================================================================
# data_sanitizer.py — Metadata Normalization + Schema Safety Layer
# =============================================================================

import logging
from typing import Dict, Any, List

log = logging.getLogger(__name__)
# =============================================================================
# Block 2: Metadata Patch Layer (Safe Injection if missing)
# =============================================================================
def sanitize_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures metadata exists in the JSON structure with valid placeholders.
    """
    if "metadata" not in data or not isinstance(data["metadata"], dict):
        log.warning("🛑 Missing or malformed metadata block. Injecting defaults.")
        data["metadata"] = {}

    meta = data["metadata"]
    
    meta.setdefault("sourceFilename", "unknown.dem")
    meta.setdefault("parserVersion", "v0.0.1")
    meta.setdefault("parsedAt", "N/A")
    meta.setdefault("rounds", [])
    meta.setdefault("tickrate", 64)
    meta.setdefault("mapName", "de_dust2")
    meta.setdefault("matchType", "competitive")
    meta.setdefault("duration", 0)
    meta.setdefault("players", [])

    return data
#BLOCK 3 enforce_schema_safety()
# =============================================================================
# Block 3: Top-Level Schema Normalizer (Events + PlayerStats + Chat)
# =============================================================================
def enforce_schema_safety(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures that essential top-level keys exist and are in valid format.
    Injects empty placeholders if missing to prevent downstream crashes.
    """
    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")

    # Events
    if "events" not in data or not isinstance(data["events"], list):
        log.warning("⚠️ Missing or invalid 'events' key. Injecting empty list.")
        data["events"] = []

    # Chat
    if "chat" not in data or not isinstance(data["chat"], list):
        log.warning("⚠️ Missing or invalid 'chat' key. Injecting empty list.")
        data["chat"] = []

    # Player Stats
    if "playerStats" not in data or not isinstance(data["playerStats"], dict):
        log.warning("⚠️ Missing or invalid 'playerStats' key. Injecting empty dict.")
        data["playerStats"] = {}

    # Advanced Stats (optional, but common in ACS pipeline)
    if "advancedStats" not in data or not isinstance(data["advancedStats"], dict):
        log.info("📦 No advancedStats found, injecting empty.")
        data["advancedStats"] = {}

    # Scoreboard fallback
    if "scoreboard" not in data or not isinstance(data["scoreboard"], list):
        log.warning("⚠️ No scoreboard present. Injecting empty scoreboard.")
        data["scoreboard"] = []

    return data
# =============================================================================
# Block 4: Final Scoreboard Reconciliation reconcile_final_scoreboard() — Scoreboard Injection Logic
# Purpose: Guarantees a complete final scoreboard, even if demo parsing failed or data is partial.
# =============================================================================
def reconcile_final_scoreboard(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensures that all players listed in playerStats are represented in the scoreboard.
    Adds missing entries with placeholder stats (e.g., 0 KDA).
    """
    scoreboard = data.get("scoreboard", [])
    player_stats = data.get("playerStats", {})
    steam_ids_on_board = {entry.get("steamId") for entry in scoreboard if isinstance(entry, dict)}

    for steam_id, stats in player_stats.items():
        if steam_id not in steam_ids_on_board:
            log.info(f"📈 Adding missing player to scoreboard: {steam_id}")
            scoreboard.append({
                "steamId": steam_id,
                "name": stats.get("name", "Unknown"),
                "team": stats.get("team", "Unknown"),
                "kills": stats.get("kills", 0),
                "deaths": stats.get("deaths", 0),
                "assists": stats.get("assists", 0),
                "score": stats.get("score", 0),
                "adr": stats.get("adr", 0.0),
                "hsPercent": stats.get("hsPercent", 0.0),
                "utilityDamage": stats.get("utilityDamage", 0),
                "rank": stats.get("rank", "N/A"),
                "side": stats.get("side", "T"),
                "matchMvp": stats.get("matchMvp", 0)
            })

    data["scoreboard"] = scoreboard
    return data
#BLOCK 5
# =============================================================================
# Block 5: Debug Print Summary for Schema Gaps
# =============================================================================
def print_schema_summary(report: Dict[str, Any]) -> None:
    """
    Prints a simple debug-friendly summary of schema analysis.
    Used only during development and testing.
    """
    print("\n🧪 SCHEMA SUMMARY --------------------------")
    print(f"Missing Keys       : {report.get('missing_keys')}")
    print(f"Malformed Keys     : {report.get('malformed_keys')}")
    print(f"Gap Marker Count   : {report.get('gap_marker_count')}")
    print(f"Event Histogram    :")
    for k, v in report.get("event_type_histogram", {}).items():
        print(f" - {k}: {v}")
    print("--------------------------------------------\n")
#EOF 6 123 TLOC pzr1H 1045AM ET jul 26 2025