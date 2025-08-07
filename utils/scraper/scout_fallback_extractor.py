# scout_fallback_extractor.py
# =============================================================================
# CS2 Fallback Parser – Comprehensive Stat + Metadata + Input Extractor
# Purpose: Used when `playerStats` or `metadata` are missing or malformed.
# Supports: Scout Report tab, Advanced Stats tab, Input/Keystroke Analysis
# Version: v0.0002-EXPANDED
# Target Size: ~110 KB
# =============================================================================

import os
import json
import re
import logging
from collections import defaultdict
from typing import List, Dict, Any, Optional, Tuple

logger = logging.getLogger("scout_fallback")

# -----------------------------------------------------------------------------
# Block 1 – Utilities: Tick Range, SteamID Normalization, Accuracy Tools
# -----------------------------------------------------------------------------
def normalize_steam_id(raw_id: str) -> str:
    if raw_id.startswith("STEAM_"):
        return raw_id
    try:
        sid = int(raw_id)
        y = sid % 2
        z = (sid - 76561197960265728 - y) // 2
        return f"STEAM_1:{y}:{z}"
    except Exception as e:
        logger.warning(f"Unable to normalize Steam ID: {raw_id} – {e}")
        return raw_id

def extract_tick_range(events: List[Dict[str, Any]]) -> Tuple[int, int]:
    ticks = [e.get("tick", 0) for e in events if "tick" in e]
    return min(ticks or [0]), max(ticks or [0])

# -----------------------------------------------------------------------------
# Block 2 – Metadata Reconstruction from JSON
# -----------------------------------------------------------------------------
def reconstruct_metadata(raw: Dict[str, Any]) -> Dict[str, Any]:
    metadata = {
        "sourceFilename": raw.get("sourceFilename", "unknown.dem"),
        "parserVersion": raw.get("parserVersion", "v0.0.0"),
        "parsedAt": raw.get("parsedAt", "N/A"),
        "mapName": raw.get("mapName", "unknown"),
        "matchType": raw.get("matchType", "unknown"),
        "tickrate": raw.get("tickrate", 64),
        "duration": raw.get("duration", 0),
        "players": [],
        "rounds": raw.get("rounds", [])
    }

    if "players" in raw:
        for player in raw["players"]:
            sid = normalize_steam_id(player.get("steamID", player.get("steam_id", "")))
            metadata["players"].append({
                "name": player.get("name", "Unknown"),
                "steamID": sid,
                "team": player.get("team", "")
            })
    return metadata

# -----------------------------------------------------------------------------
# Block 3 – Stat Reconstruction with Advanced Metrics
# -----------------------------------------------------------------------------
def reconstruct_player_stats(events: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    stats = defaultdict(lambda: defaultdict(int))
    shots_fired = defaultdict(int)
    shots_hit = defaultdict(int)

    for event in events:
        tick = event.get("tick", 0)
        if event.get("type") == "kill":
            attacker = normalize_steam_id(event.get("attackerSteamID", ""))
            victim = normalize_steam_id(event.get("victimSteamID", ""))
            weapon = event.get("weapon", "")
            headshot = event.get("isHeadshot", False)
            if attacker:
                stats[attacker]["kills"] += 1
                stats[attacker][f"weapon_{weapon}"] += 1
                if headshot:
                    stats[attacker]["headshots"] += 1
            if victim:
                stats[victim]["deaths"] += 1

        elif event.get("type") == "damage":
            attacker = normalize_steam_id(event.get("attackerSteamID", ""))
            dmg = event.get("damage", 0)
            if attacker:
                stats[attacker]["damage"] += dmg

        elif event.get("type") == "assist":
            assister = normalize_steam_id(event.get("assisterSteamID", ""))
            if assister:
                stats[assister]["assists"] += 1

        elif event.get("type") == "weapon_fire":
            attacker = normalize_steam_id(event.get("attackerSteamID", ""))
            shots_fired[attacker] += 1

        elif event.get("type") == "player_hurt":
            attacker = normalize_steam_id(event.get("attackerSteamID", ""))
            shots_hit[attacker] += 1

    # Derived metrics
    for sid, s in stats.items():
        s["adr"] = round(s.get("damage", 0) / max(1, s.get("deaths", 1)), 1)
        s["hs_percent"] = round((s.get("headshots", 0) / max(1, s.get("kills", 1))) * 100, 1)
        s["accuracy"] = round((shots_hit[sid] / max(1, shots_fired[sid])) * 100, 1)
        s["rating"] = round((s["kills"] * 0.6 + s.get("assists", 0) * 0.3 + s.get("adr", 0) * 0.1) / 10, 2)

    return stats

# -----------------------------------------------------------------------------
# Block 4 – Keystroke and Input Analysis
# -----------------------------------------------------------------------------
def extract_keystroke_events(events: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    input_events = defaultdict(list)
    for event in events:
        if event.get("type") == "input":
            sid = normalize_steam_id(event.get("steamID", ""))
            keys = event.get("keys", [])
            tick = event.get("tick", 0)
            input_events[sid].append({"tick": tick, "keys": keys})
    return input_events

# -----------------------------------------------------------------------------
# Block 5 – Master Orchestrator
# -----------------------------------------------------------------------------
def fallback_extract(raw: Dict[str, Any]) -> Dict[str, Any]:
    events = raw.get("events", [])
    if not events:
        logger.warning("⚠️ No events available for fallback extraction.")
        return {}

    metadata = reconstruct_metadata(raw)
    playerStats = reconstruct_player_stats(events)
    inputs = extract_keystroke_events(events)

    return {
        "metadata": metadata,
        "playerStats": playerStats,
        "playerInputs": inputs
    }

# -----------------------------------------------------------------------------
# Block 6 – CLI Mode
# -----------------------------------------------------------------------------
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Fallback extractor for CS2 demo/event JSON")
    parser.add_argument("--input", required=True, help="Path to input JSON")
    parser.add_argument("--output", required=True, help="Path to save output JSON")
    args = parser.parse_args()

    with open(args.input, "r", encoding="utf-8") as f:
        raw = json.load(f)

    result = fallback_extract(raw)
    with open(args.output, "w", encoding="utf-8") as out:
        json.dump(result, out, indent=2)

    print(f"✅ Fallback extraction complete. Output written to {args.output}")
