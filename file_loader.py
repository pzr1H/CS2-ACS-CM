#!/usr/bin/env python3
# =============================================================================
# file_loader.py — CS2 ACS Data Loader (v0.0029-PATCHED)
# Timestamp-TOP: 2025-07-26T14:30-EDT
# =============================================================================

import os
import json
import subprocess
import re
from typing import Dict, List, Optional

from utils.logging_config import logger  # Centralized logger

from tkinter import filedialog

from utils.steam_utils import to_steam2
from cs2_parser.fallback_parser import inject_fallback_stats
from utils.data_sanitizer import sanitize_metadata, enforce_schema_safety, reconcile_final_scoreboard
from utils.scout_report import generate_stub_scout_report

PARSER_EXE = "C:/Users/jerry/Downloads/CS2-ACS-CM/CS2-ACSv1.exe"
OUTPUT_DIR = "./pewpew"

# Regex for parsing fallback player info string from events
PLAYER_INFO_RE = re.compile(r"\b([0-9a-fA-F]{8,}):(.+)")

# -----------------------------------------------------------------------------
# load_input: Load JSON or DEMO file, invoke external parser if needed
# -----------------------------------------------------------------------------
def load_input(file_path: str, console_callback: Optional[callable] = None) -> Optional[Dict]:
    """
    Load and parse a .json or .dem file.
    For .dem files, runs external parser executable to produce JSON.
    Logs process and routes subprocess output optionally to GUI console.

    Args:
        file_path (str): Path to input .json or .dem file
        console_callback (callable, optional): Function to receive live parser output lines

    Returns:
        dict or None: Parsed JSON data dictionary or None on failure
    """
    logger.info(f"🔍 load_input triggered: {file_path}")
    if not file_path:
        logger.warning("No file path provided to load_input()")
        return None

    try:
        if file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"Loaded JSON file: {file_path}")
            return data

        elif file_path.endswith(".dem"):
            if not os.path.exists(OUTPUT_DIR):
                os.makedirs(OUTPUT_DIR, exist_ok=True)

            logger.info(f"🔧 Running parser: {PARSER_EXE} -demo {file_path} -outdir {OUTPUT_DIR}")

            process = subprocess.Popen(
                [PARSER_EXE, "-demo", file_path, "-outdir", OUTPUT_DIR],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )

            stdout_lines = []
            stderr_lines = []

            # Read stdout and stderr line-by-line
            while True:
                out_line = process.stdout.readline()
                if out_line:
                    stdout_lines.append(out_line)
                    if console_callback:
                        console_callback(out_line.strip())
                err_line = process.stderr.readline()
                if err_line:
                    stderr_lines.append(err_line)
                    if console_callback:
                        console_callback(err_line.strip())
                if not out_line and not err_line and process.poll() is not None:
                    break

            process.wait()
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)

            logger.debug(f"✅ Parser stdout: {stdout}")
            logger.debug(f"⚠️ Parser stderr: {stderr}")

            if process.returncode != 0:
                logger.error(f"🚫 Parser failed with code {process.returncode}")
                return None

            # Attempt to extract summary JSON path from stdout lines
            summary_path = None
            for line in stdout.splitlines():
                if "Summary:" in line and ".json" in line:
                    summary_file = line.split("Summary:")[-1].strip().replace("\\", "/")
                    summary_path = os.path.normpath(summary_file)
                    break

            if not summary_path or not os.path.exists(summary_path):
                # Fallback: use latest summary-*.json in OUTPUT_DIR
                summaries = sorted(
                    [f for f in os.listdir(OUTPUT_DIR) if f.startswith("summary-") and f.endswith(".json")],
                    key=lambda f: os.path.getmtime(os.path.join(OUTPUT_DIR, f)),
                    reverse=True
                )
                if summaries:
                    summary_path = os.path.join(OUTPUT_DIR, summaries[0])
                    logger.warning(f"⚠️ Falling back to latest summary JSON: {summary_path}")
                else:
                    raise FileNotFoundError("❌ No parsed JSON output file detected from parser stdout or fallback.")

            logger.info(f"📄 Loading parsed file: {summary_path}")
            with open(summary_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data

        else:
            logger.warning(f"Unsupported file extension for loading: {file_path}")
            return None

    except Exception as e:
        logger.error(f"❌ load_input failed: {e}")
        if console_callback:
            console_callback(f"[ERROR] {e}")
        return None

# -----------------------------------------------------------------------------
# extract_players_from_events: Extract player names and Steam2 IDs from fallback events
# -----------------------------------------------------------------------------
def extract_players_from_events(events: List[Dict]) -> List[Dict]:
    """
    Parse GenericGameEvent strings to extract player name and SteamID.

    Args:
        events (List[Dict]): List of parsed event dicts.

    Returns:
        List[Dict]: List of dicts with keys 'steamid' and 'name'.
    """
    found = {}
    for ev in events:
        if ev.get("type") != "events.GenericGameEvent":
            continue
        s = ev.get("details", {}).get("string", "")
        match = PLAYER_INFO_RE.search(s)
        if match:
            sid_hex, name = match.groups()
            try:
                sid64 = str(int(sid_hex, 16))
                steam2 = to_steam2(int(sid64))
                found[steam2] = {"steamid": sid64, "name": name}
            except ValueError:
                logger.warning(f"⚠️ Skipping malformed sid_hex: {sid_hex} from string: {s}")
    return list(found.values())

# -----------------------------------------------------------------------------
# extract_round_scores: Detect round indices and labels
# -----------------------------------------------------------------------------
def extract_round_scores(data: Dict):
    """
    Extracts round indices and creates round labels.

    Modifies:
        data["round_indices"]: List[int]
        data["round_labels"]: List[str]
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
    data["round_labels"] = [f"Round {r+1}" for r in data["round_indices"]]

# -----------------------------------------------------------------------------
# enrich_metadata: Add summary metadata flags for downstream processing
# -----------------------------------------------------------------------------
def enrich_metadata(data: Dict):
    """
    Adds summary flags to data for event types presence.
    """
    events = data.get("events", [])
    data["event_count"] = len(events)
    data["has_chat"] = any(ev.get("type") == "events.ChatMessage" for ev in events)
    data["has_rounds"] = any(ev.get("round", -1) >= 0 for ev in events)
    data["has_player_hurt"] = any(ev.get("type") == "events.PlayerHurt" for ev in events)
    data["has_weapon_fire"] = any(ev.get("type") == "events.WeaponFire" for ev in events)
    data["has_bullet_impact"] = any(ev.get("type") == "events.BulletImpact" for ev in events)

# -----------------------------------------------------------------------------
# print_stat_keys: Debug utility to log keys of nested dict/list blocks
# -----------------------------------------------------------------------------
def print_stat_keys(data: Dict):
    """
    Debug function: logs keys of dict/list elements in data.
    """
    for key, block in data.items():
        if isinstance(block, dict):
            logger.debug(f"🧩 {key} keys: {list(block.keys())}")
        elif isinstance(block, list):
            for i, p in enumerate(block):
                if isinstance(p, dict):
                    logger.debug(f"🧩 {key}[{i}] = {list(p.keys())}")

# -----------------------------------------------------------------------------
# validate_stats: Check for missing critical player stats fields
# -----------------------------------------------------------------------------
def validate_stats(data: Dict):
    """
    Warn if critical stats are missing from playerStats.
    """
    player_stats = data.get("playerStats", {})
    if not player_stats:
        logger.warning("⚠️ No playerStats after fallback.")
        return
    for sid, stats in player_stats.items():
        missing = [key for key in ["kills", "adr", "hs_percent"] if key not in stats]
        if missing:
            logger.warning(f"⚠️ Player {sid} missing: {missing}")

# -----------------------------------------------------------------------------
# load_and_prepare: GUI file picker, load, and sanitize data
# -----------------------------------------------------------------------------
def load_and_prepare() -> Optional[Dict]:
    """
    Show file dialog, load selected file, sanitize and prepare data for UI.

    Returns:
        Dict or None: Prepared data dict or None on failure.
    """
    path = filedialog.askopenfilename(
        title="Select CS2 demo or JSON file",
        filetypes=[("CS2 Files", "*.dem *.json")]
    )
    if not path:
        return None

    data = load_input(path)
    if not data:
        logger.error("❌ Failed to load file or parse.")
        return None

    data = sanitize_metadata(data)
    data = reconcile_final_scoreboard(data)

    if not data.get("playerDropdown"):
        data["playerDropdown"] = extract_players_from_events(data.get("events", []))

    extract_round_scores(data)
    print_stat_keys(data)
    validate_stats(data)

    return enforce_schema_safety(data)

# -----------------------------------------------------------------------------
# load_file: Load file with optional console callback, sanitize and prepare data
# -----------------------------------------------------------------------------
def load_file(file_path: str, console_callback: Optional[callable] = None) -> Optional[Dict]:
    """
    Load and parse file at file_path, optionally reporting parser output to callback.
    Sanitize and prepare data for UI consumption.

    Args:
        file_path (str): Path to file
        console_callback (callable, optional): Function receiving live parser output lines

    Returns:
        Dict or None: Prepared data dictionary or None on failure
    """
    logger.info(f"[MAIN] 📂 File selected: {file_path}")
    data = load_input(file_path, console_callback)
    if not data:
        logger.error("❌ load_file() — could not parse input.")
        return None

    data = sanitize_metadata(data)
    data = reconcile_final_scoreboard(data)

    if not data.get("playerDropdown"):
        data["playerDropdown"] = extract_players_from_events(data.get("events", []))

    extract_round_scores(data)
    print_stat_keys(data)
    validate_stats(data)

    return enforce_schema_safety(data)

# -----------------------------------------------------------------------------
# inject_scout_stats: Inject scoutStats data using playerDropdown metadata
# -----------------------------------------------------------------------------
def inject_scout_stats(data: Dict):
    """
    Generate stub scout stats from playerDropdown info and inject into data.

    Args:
        data (Dict): Parsed and sanitized data dictionary
    """
    try:
        player_data = data.get("playerDropdown", [])
        if player_data:
            data["scoutStats"] = generate_stub_scout_report(player_data)
            logger.info("🔍 scoutStats injected successfully.")
        else:
            logger.warning("⚠️ scoutStats not generated — playerDropdown missing.")
    except Exception as e:
        logger.warning(f"⚠️ scoutStats generation failed: {e}")


# =============================================================================
# EOF — file_loader.py v0.0029-PATCHED | TLOC: 209
# =============================================================================
