#!/usr/bin/env python3
# =============================================================================
# file_loader.py — CS2 ACS Data Loader (Sanitized Fallback + Tablestakes)
# Timestamp‑TOP: 2025‑07‑25T23:30‑EDT | v0.0025‑REPOSTED
# =============================================================================

import os, json, logging, re
from tkinter import filedialog
from typing import Dict, List

# External Module Imports — Shared Util Stack
from utils.steam_utils import to_steam2
from cs2_parser.fallback_parser import inject_fallback_stats
from utils.data_sanitizer import sanitize_metadata  # Injected Sanitation Layer

log = logging.getLogger(__name__)

# Hardcoded Paths for Parser Executable and Output Folder
PARSER_EXE = "C:/Users/jerry/Downloads/CS2-ACS-CM/CS2-ACSv1.exe"
OUTPUT_DIR = "./pewpew"
# -----------------------------------------------------------------------------
# Load JSON or DEMO input and parse to dictionary
# -----------------------------------------------------------------------------

def load_input(file_path: str) -> Dict:
    """
    Attempts to load a .json or .dem file and return the parsed event dictionary.
    Executes external parser if .dem file is provided.
    Enriches data with fallback stats and sanitation.
    """
    log.info(f"🔍 load_input triggered: {file_path}")
    if not file_path:
        return None

    try:
        if file_path.endswith(".json"):
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

        elif file_path.endswith(".dem"):
            outname = os.path.basename(file_path).replace(".dem", "_parsed.json")
            outfile = os.path.join(OUTPUT_DIR, outname)
            os.makedirs(OUTPUT_DIR, exist_ok=True)

            cmd = f'"{PARSER_EXE}" "{file_path}" "{outfile}"'
            log.info(f"🚀 Running parser: {cmd}")
            os.system(cmd)

            with open(outfile, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            raise ValueError("Unsupported file format.")

        print_metadata(data)

        if not data.get("playerStats"):
            log.warning("⚠️  No playerStats computed. Injecting fallback stats.")
            inject_fallback_stats(data)

        enrich_metadata(data)
        sanitize_metadata(data)  # Schema cleanup and gap filler
        data = enforce_schema_safety(data)  # External validator

        log.debug(f"DEBUG-LEN playerStats → {len(data.get('playerStats', {}))}")
        return data

    except Exception as e:
        log.error(f"❌ load_input failed: {e}")
        return None
# -----------------------------------------------------------------------------
# Extract players using regex from GenericGameEvent
# -----------------------------------------------------------------------------

PLAYER_INFO_RE = re.compile(r'XUID:0x([0-9a-fA-F]+).*?Name:\\?\"([^\"]+)\"')

def extract_players_from_events(events: List[Dict]) -> List[Dict]:
    """
    Searches GenericGameEvent logs for player XUIDs and names.
    Builds a fallback dropdown block for player selector if needed.
    """
    found = {}
    for ev in events:
        if ev.get("type") != "events.GenericGameEvent":
            continue
        s = ev.get("details", {}).get("string", "")
        match = PLAYER_INFO_RE.search(s)
        if match:
            sid_hex, name = match.groups()
            sid64 = str(int(sid_hex, 16))
            steam2 = to_steam2(int(sid64))
            found[steam2] = {"steamid": sid64, "name": name}
    return list(found.values())
# -----------------------------------------------------------------------------
# Extract round metadata for dropdown
# -----------------------------------------------------------------------------

def extract_round_scores(data: Dict):
    """
    Extracts round numbers and end markers from event stream,
    then creates GUI-friendly round index and label metadata.
    """
    events = data.get("events", [])
    rounds = {}
    for ev in events:
        rnd = ev.get("round", -1)
        if rnd >= 0:
            rounds.setdefault(rnd, 0)
            if ev.get("type") == "events.RoundEnd":
                rounds[rnd] += 1
    data["round_indices"] = sorted(rounds.keys())
    data["round_labels"]  = [f"Round {r+1}" for r in data["round_indices"]]
# -----------------------------------------------------------------------------
# Enrichment — Tablestakes Metadata to Prepare for GUI & Debugging
# -----------------------------------------------------------------------------

def enrich_metadata(data: Dict):
    """
    Adds event count and flags indicating available stat types.
    Enables GUI modules to selectively activate views.
    """
    events = data.get("events", [])
    data["event_count"] = len(events)
    data["has_chat"] = any(ev.get("type") == "events.ChatMessage" for ev in events)
    data["has_rounds"] = any(ev.get("type") == "events.RoundEnd" for ev in events)
    data["has_player_hurt"] = any(ev.get("type") == "events.PlayerHurt" for ev in events)
    data["has_weapon_fire"] = any(ev.get("type") == "events.WeaponFire" for ev in events)
    data["has_bullet_impact"] = any(ev.get("type") == "events.BulletImpact" for ev in events)
# -----------------------------------------------------------------------------
# Optional Debug Blocks (Guarded by Logging)
# -----------------------------------------------------------------------------

def print_metadata(data: Dict):
    log.debug(f"▶ print_metadata: top-level keys = {list(data.keys())}")
    log.debug(f"▶ event count: {len(data.get('events', []))}")

def print_stat_keys(data: Dict):
    for key in ["playerStats", "advancedStats", "scoutStats"]:
        block = data.get(key, {})
        if isinstance(block, dict):
            log.debug(f"▶ {key} keys: {list(block.keys())}")
        elif isinstance(block, list):
            for i, p in enumerate(block):
                log.debug(f"▶ {key}[{i}] = {list(p.keys())}")

def validate_stats(data: Dict):
    player_stats = data.get("playerStats", {})
    if not player_stats:
        log.warning("⚠️  No playerStats after fallback.")
        return
    for sid, stats in player_stats.items():
        missing = []
        for key in ["kills", "adr", "hs_percent"]:
            if key not in stats:
                missing.append(key)
        if missing:
            log.warning(f"⚠️ Player {sid} missing: {missing}")
# -----------------------------------------------------------------------------
# Main entry for GUI file loading
# -----------------------------------------------------------------------------

def load_and_prepare():
    """
    Fallback GUI method using tkinter's file dialog.
    Triggers full parse + sanitation + dropdown prep.
    """
    path = filedialog.askopenfilename(
        title="Select CS2 demo or JSON file",
        filetypes=[("CS2 Files", "*.dem *.json")]
    )
    if not path:
        return None

    data = load_input(path)
    if not data:
        log.error("❌ Failed to load file or parse output.")
        return None

    if not data.get("playerDropdown"):
        player_block = extract_players_from_events(data.get("events", []))
        log.debug(f"[DEBUG] dropdown size: {len(player_block)}")
        data["playerDropdown"] = player_block

    extract_round_scores(data)
    print_stat_keys(data)
    validate_stats(data)

    return data
# -----------------------------------------------------------------------------
# CLI / GUI-shared loader
# -----------------------------------------------------------------------------

def load_file(file_path: str) -> Dict:
    """
    Preferred loader for programmatic use via main.py.
    Handles sanitation, dropdown fallbacks, and schema safety.
    """
    data = load_input(file_path)
    if not data:
        log.error("❌ load_file() — could not parse input.")
        return None

    if not data.get("playerDropdown"):
        data["playerDropdown"] = extract_players_from_events(data.get("events", []))

    extract_round_scores(data)
    print_stat_keys(data)
    validate_stats(data)

    return data
# 🔽 BLOCK 9 START — Schema Enrichment & Normalization via data_sanitizer

try:
    from data_sanitizer import enrich_and_validate
except ImportError:
    log.warning("⚠️ Failed to import enrich_and_validate from data_sanitizer")
    enrich_and_validate = None

def enforce_schema_safety(data):
    """
    Optional enforcement of schema consistency and fallbacks using data_sanitizer.
    This can be toggled per-match or globally.
    """
    if enrich_and_validate:
        try:
            enriched = enrich_and_validate(data)
            if isinstance(enriched, dict):
                log.debug("✅ Data sanitized and normalized successfully.")
                return enriched
            else:
                log.warning("⚠️ Sanitizer returned non-dict. Using original data.")
        except Exception as e:
            log.error(f"💥 Schema enrichment failed: {e}")
    else:
        log.debug("🔕 Schema enrichment skipped (function missing).")
    return data

# 🔼 BLOCK 9 END
# =============================================================================
# EOF <file_loader.py v0.0025-PATCHED | Full Sanitation + Main Compatibility>
# TLOC: 214 | pzr1H
