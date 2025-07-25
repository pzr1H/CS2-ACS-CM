#!/usr/bin/env python3
# =============================================================================
# steam_utils.py – SteamID Conversion Utilities for CS2 ACS
# Timestamp‑TOP: 2025‑07‑25 | v1.1-NORMALIZER
# =============================================================================

import re
import logging
from typing import Union, Set

log = logging.getLogger(__name__)

# -------------------------------------------------------------------------
# Constants
# -------------------------------------------------------------------------

STEAM64_BASE = 76561197960265728

# -------------------------------------------------------------------------
# Steam64 Pre-Normalizer — Handles hex, 0x prefix, or decimal
# -------------------------------------------------------------------------

def strip_steamid64(raw: Union[str, int]) -> int:
    """
    Normalizes raw SteamID64 input from hex, 0x-prefixed, or decimal string.
    """
    try:
        if isinstance(raw, int):
            return raw
        clean = str(raw).strip().lower()
        if clean.startswith("0x"):
            clean = clean[2:]
        clean = re.sub(r'[^0-9a-f]', '', clean)
        return int(clean, 16)
    except Exception as e:
        log.warning(f"strip_steamid64 failed: {raw} → {e}")
        return -1

# -------------------------------------------------------------------------
# Conversions: SteamID64 → Steam2
# -------------------------------------------------------------------------

def steamid64_to_steam2(sid64: Union[str, int]) -> str:
    """
    Converts 64-bit SteamID to Steam2 format (STEAM_1:X:Y).
    """
    try:
        sid64 = strip_steamid64(sid64)
        if sid64 == -1:
            return "STEAM_UNKNOWN"
        y = sid64 % 2
        z = (sid64 - STEAM64_BASE - y) // 2
        return f"STEAM_1:{y}:{z}"
    except Exception as e:
        log.warning(f"steamid64_to_steam2 failed: {e}")
        return "STEAM_UNKNOWN"

# -------------------------------------------------------------------------
# Conversions: SteamID3 → Steam2
# -------------------------------------------------------------------------

def steamid3_to_steam2(sid3: str) -> str:
    """
    Converts SteamID3 format to Steam2 (e.g. '[U:1:12345678]' → 'STEAM_1:0:6172839')
    """
    try:
        match = re.match(r'\[U:1:(\d+)\]', sid3)
        if match:
            uid = int(match.group(1))
            return f"STEAM_1:{uid % 2}:{uid // 2}"
    except Exception as e:
        log.warning(f"steamid3_to_steam2 failed: {e}")
    return "STEAM_UNKNOWN"

# -------------------------------------------------------------------------
# Conversions: Steam2 → Steam64
# -------------------------------------------------------------------------

def steamid2_to_steam64(steam2: str) -> int:
    """
    Converts Steam2 format (STEAM_1:X:Y) to 64-bit SteamID.
    """
    try:
        parts = steam2.strip().split(':')
        if len(parts) == 3:
            y = int(parts[1])
            z = int(parts[2])
            return STEAM64_BASE + z * 2 + y
    except Exception as e:
        log.warning(f"steamid2_to_steam64 failed: {e}")
    return -1

# -------------------------------------------------------------------------
# Conversions: Steam2 → Steam3
# -------------------------------------------------------------------------

def steamid2_to_steam3(steam2: str) -> str:
    """
    Converts Steam2 format to Steam3 (e.g. 'STEAM_1:X:Y' → '[U:1:Z]')
    """
    try:
        parts = steam2.strip().split(':')
        if len(parts) == 3:
            x = int(parts[1])
            y = int(parts[2])
            uid = y * 2 + x
            return f"[U:1:{uid}]"
    except Exception as e:
        log.warning(f"steamid2_to_steam3 failed: {e}")
    return "STEAM_UNKNOWN"

# -------------------------------------------------------------------------
# Normalize: Attempts to convert any SteamID type to Steam2 format
# -------------------------------------------------------------------------

def normalize_steam_id(raw_id: Union[str, int]) -> str:
    """
    Normalizes various SteamID formats to Steam2 (STEAM_1:X:Y)
    """
    if not raw_id:
        return "STEAM_UNKNOWN"

    try:
        if isinstance(raw_id, int) or str(raw_id).isdigit() or str(raw_id).lower().startswith("0x"):
            return steamid64_to_steam2(raw_id)
        elif str(raw_id).startswith("[U:1:"):
            return steamid3_to_steam2(str(raw_id))
        elif str(raw_id).startswith("STEAM_"):
            return str(raw_id)
    except Exception as e:
        log.warning(f"normalize_steam_id failed: {e}")
    return "STEAM_UNKNOWN"

# -------------------------------------------------------------------------
# Extract all Steam IDs from JSON-formatted demo data
# -------------------------------------------------------------------------

def extract_steam_ids_from_data(data: dict) -> Set[str]:
    """
    Traverses parsed demo JSON data to extract all unique SteamIDs,
    normalizing them to Steam2 format.
    """
    steam_ids = set()
    events = data.get("events", [])
    for ev in events:
        for key in ev:
            if "steamid" in key:
                val = ev[key]
                steam2 = normalize_steam_id(val)
                if steam2 and steam2.startswith("STEAM_"):
                    steam_ids.add(steam2)
    return steam_ids

# -------------------------------------------------------------------------
# Compatibility Aliases
# -------------------------------------------------------------------------

to_steam2 = steamid64_to_steam2
parse_sid64 = steamid64_to_steam2
normalize_sid = normalize_steam_id

# =============================================================================
# EOF — steam_utils.py (v1.1-NORMALIZER)
# - Steam64 pre-stripper handles hex, 0x, raw input
# - Steam2/3/64 converters with logging
# - extract_steam_ids_from_data() supports all key variants
# - All output is Steam2-normalized
# =============================================================================
