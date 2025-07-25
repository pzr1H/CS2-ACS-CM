#!/usr/bin/env python3
# =============================================================================
# data_sanitizer.py — Patch & Validate JSON using .log file (Full Version)
# =============================================================================

import json
import re
from pathlib import Path
import argparse
import logging

log = logging.getLogger(__name__)


# =============================================================================
# Block 1: Log Parsing Layer
# =============================================================================
def parse_log_file(log_path):
    """
    Parse the .log file line-by-line into structured event dictionaries.
    Returns a list of parsed events with event 'type' and 'details'.
    """
    parsed_events = []
    log_path = Path(log_path)

    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            match = re.match(r'^(events\.[A-Za-z0-9_]+)', line)
            if match:
                event_type = match.group(1)
                parsed_events.append({
                    "type": event_type,
                    "details": {"string": line}
                })

    return parsed_events


# =============================================================================
# Block 2: JSON Structure Sanity Check + Event Reconciliation
# =============================================================================
def sanitize_json_with_log(json_data, log_events):
    """
    Compares and patches missing event types from the log into the parsed JSON.
    Returns: patched_json, list of inserted events, list of event types added.
    """
    if "events" not in json_data:
        log.error("❌ Missing 'events' block in JSON.")
        raise ValueError("Missing 'events' block in JSON.")

    if not isinstance(json_data["events"], list):
        log.error("❌ 'events' block must be a list.")
        raise ValueError("Invalid type for 'events'. Must be a list.")

    existing_types = set(event.get("type") for event in json_data["events"] if isinstance(event, dict))
    added_events = []
    added_types = set()

    for event in log_events:
        event_type = event.get("type")
        if event_type not in existing_types:
            added_events.append(event)
            added_types.add(event_type)

    if added_events:
        json_data["events"].extend(added_events)
        log.info(f"✅ Injected {len(added_events)} new event(s) into JSON from .log.")

    return json_data, added_events, added_types


# =============================================================================
# EOB2 — Event Reconciliation + Sanity Guard (TLOC: 76)
# =============================================================================
# =============================================================================
# Block 3: Metadata Schema Validator for playerStats, advancedStats, chat
# =============================================================================

from typing import Dict, Any

def sanitize_metadata(data: Dict[str, Any]) -> None:
    """
    Main hook for file_loader.py and other modules.
    Ensures playerStats, advancedStats, and chat blocks exist and are correct type.
    If missing or malformed, injects safe defaults and logs warnings.
    """
    if "playerStats" not in data:
        data["playerStats"] = {}
        log.warning("⚠️ Missing playerStats block. Injected empty dict.")

    elif not isinstance(data["playerStats"], dict):
        log.error("💥 playerStats must be a dict. Attempting to coerce.")
        try:
            coerced = {}
            for entry in data["playerStats"]:
                if isinstance(entry, dict) and "steamid" in entry:
                    coerced[entry["steamid"]] = entry
            data["playerStats"] = coerced
        except Exception as e:
            log.exception(f"💥 Failed to coerce playerStats: {e}")
            data["playerStats"] = {}

    if "advancedStats" not in data:
        data["advancedStats"] = {}
        log.info("ℹ️ Injected empty advancedStats block.")

    elif not isinstance(data["advancedStats"], dict):
        log.warning("⚠️ advancedStats malformed. Resetting to empty dict.")
        data["advancedStats"] = {}

    if "chat" not in data:
        data["chat"] = []
        log.info("ℹ️ Injected empty chat block.")

    elif not isinstance(data["chat"], list):
        log.warning("⚠️ chat malformed. Resetting to empty list.")
        data["chat"] = []
def enrich_and_validate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optional secondary validator for enforcing schema defaults.
    Used when loading existing JSON that may be incomplete or malformed.
    """
    required_keys = ["playerStats", "advancedStats", "chat"]
    for key in required_keys:
        if key not in data:
            log.warning(f"⚠️ Key '{key}' missing. Injecting default.")
            data[key] = {} if "Stats" in key else []

    if not isinstance(data["playerStats"], dict):
        log.error("❌ playerStats must be dict. Overwriting.")
        data["playerStats"] = {}

    if not isinstance(data["advancedStats"], dict):
        log.error("❌ advancedStats must be dict. Overwriting.")
        data["advancedStats"] = {}

    if not isinstance(data["chat"], list):
        log.error("❌ chat must be list. Overwriting.")
        data["chat"] = []

    return data


# =============================================================================
# EOB3 — Metadata Schema Validator Injected (TLOC: 144f)
# =============================================================================
# =============================================================================
# Block 4: Final Scoreboard Reconciliation (from rounds/summary logic)
# =============================================================================

def reconcile_final_scoreboard(data: Dict[str, Any]) -> None:
    """
    Ensures a final scoreboard block exists by inspecting roundSummary or events.
    Adds 'finalScoreboard' block to JSON if not present.
    """
    if "finalScoreboard" in data:
        log.debug("🟢 finalScoreboard already present. Skipping injection.")
        return

    # Initialize fallback scoreboard
    scoreboard = {
        "team1": {"name": "Team 1", "score": 0},
        "team2": {"name": "Team 2", "score": 0}
    }

    rounds = data.get("roundSummary", [])
    if not isinstance(rounds, list):
        log.warning("⚠️ roundSummary not found or malformed. Skipping scoreboard.")
        return

    for r in rounds:
        winner = r.get("winningTeam")
        if winner == "team1":
            scoreboard["team1"]["score"] += 1
        elif winner == "team2":
            scoreboard["team2"]["score"] += 1

    # Attach to data
    data["finalScoreboard"] = scoreboard
    log.info(f"📊 Final Scoreboard Injected: {scoreboard}")
    #!/usr/bin/env python3
# =============================================================================
# data_sanitizer.py — Patch & Validate JSON using .log file (Full Version)
# =============================================================================

import json
import re
from pathlib import Path
import argparse
import logging

log = logging.getLogger(__name__)


# =============================================================================
# Block 1: Log Parsing Layer
# =============================================================================
def parse_log_file(log_path):
    """
    Parse the .log file line-by-line into structured event dictionaries.
    Returns a list of parsed events with event 'type' and 'details'.
    """
    parsed_events = []
    log_path = Path(log_path)

    if not log_path.exists():
        raise FileNotFoundError(f"Log file not found: {log_path}")

    with log_path.open("r", encoding="utf-8") as file:
        for line in file:
            line = line.strip()
            match = re.match(r'^(events\.[A-Za-z0-9_]+)', line)
            if match:
                event_type = match.group(1)
                parsed_events.append({
                    "type": event_type,
                    "details": {"string": line}
                })

    return parsed_events


# =============================================================================
# Block 2: JSON Structure Sanity Check + Event Reconciliation
# =============================================================================
def sanitize_json_with_log(json_data, log_events):
    """
    Compares and patches missing event types from the log into the parsed JSON.
    Returns: patched_json, list of inserted events, list of event types added.
    """
    if "events" not in json_data:
        log.error("❌ Missing 'events' block in JSON.")
        raise ValueError("Missing 'events' block in JSON.")

    if not isinstance(json_data["events"], list):
        log.error("❌ 'events' block must be a list.")
        raise ValueError("Invalid type for 'events'. Must be a list.")

    existing_types = set(event.get("type") for event in json_data["events"] if isinstance(event, dict))
    added_events = []
    added_types = set()

    for event in log_events:
        event_type = event.get("type")
        if event_type not in existing_types:
            added_events.append(event)
            added_types.add(event_type)

    if added_events:
        json_data["events"].extend(added_events)
        log.info(f"✅ Injected {len(added_events)} new event(s) into JSON from .log.")

    return json_data, added_events, added_types


# =============================================================================
# EOB2 — Event Reconciliation + Sanity Guard (TLOC: 76)
# =============================================================================
# =============================================================================
# Block 3: Metadata Schema Validator for playerStats, advancedStats, chat
# =============================================================================

from typing import Dict, Any

def sanitize_metadata(data: Dict[str, Any]) -> None:
    """
    Main hook for file_loader.py and other modules.
    Ensures playerStats, advancedStats, and chat blocks exist and are correct type.
    If missing or malformed, injects safe defaults and logs warnings.
    """
    if "playerStats" not in data:
        data["playerStats"] = {}
        log.warning("⚠️ Missing playerStats block. Injected empty dict.")

    elif not isinstance(data["playerStats"], dict):
        log.error("💥 playerStats must be a dict. Attempting to coerce.")
        try:
            coerced = {}
            for entry in data["playerStats"]:
                if isinstance(entry, dict) and "steamid" in entry:
                    coerced[entry["steamid"]] = entry
            data["playerStats"] = coerced
        except Exception as e:
            log.exception(f"💥 Failed to coerce playerStats: {e}")
            data["playerStats"] = {}

    if "advancedStats" not in data:
        data["advancedStats"] = {}
        log.info("ℹ️ Injected empty advancedStats block.")

    elif not isinstance(data["advancedStats"], dict):
        log.warning("⚠️ advancedStats malformed. Resetting to empty dict.")
        data["advancedStats"] = {}

    if "chat" not in data:
        data["chat"] = []
        log.info("ℹ️ Injected empty chat block.")

    elif not isinstance(data["chat"], list):
        log.warning("⚠️ chat malformed. Resetting to empty list.")
        data["chat"] = []
def enrich_and_validate(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Optional secondary validator for enforcing schema defaults.
    Used when loading existing JSON that may be incomplete or malformed.
    """
    required_keys = ["playerStats", "advancedStats", "chat"]
    for key in required_keys:
        if key not in data:
            log.warning(f"⚠️ Key '{key}' missing. Injecting default.")
            data[key] = {} if "Stats" in key else []

    if not isinstance(data["playerStats"], dict):
        log.error("❌ playerStats must be dict. Overwriting.")
        data["playerStats"] = {}

    if not isinstance(data["advancedStats"], dict):
        log.error("❌ advancedStats must be dict. Overwriting.")
        data["advancedStats"] = {}

    if not isinstance(data["chat"], list):
        log.error("❌ chat must be list. Overwriting.")
        data["chat"] = []

    return data


# =============================================================================
# EOB3 — Metadata Schema Validator Injected (TLOC: 144f)
# =============================================================================
# =============================================================================
# Block 4: Final Scoreboard Reconciliation (from rounds/summary logic)
# =============================================================================

def reconcile_final_scoreboard(data: Dict[str, Any]) -> None:
    """
    Ensures a final scoreboard block exists by inspecting roundSummary or events.
    Adds 'finalScoreboard' block to JSON if not present.
    """
    if "finalScoreboard" in data:
        log.debug("🟢 finalScoreboard already present. Skipping injection.")
        return

    # Initialize fallback scoreboard
    scoreboard = {
        "team1": {"name": "Team 1", "score": 0},
        "team2": {"name": "Team 2", "score": 0}
    }

    rounds = data.get("roundSummary", [])
    if not isinstance(rounds, list):
        log.warning("⚠️ roundSummary not found or malformed. Skipping scoreboard.")
        return

    for r in rounds:
        winner = r.get("winningTeam")
        if winner == "team1":
            scoreboard["team1"]["score"] += 1
        elif winner == "team2":
            scoreboard["team2"]["score"] += 1

    # Attach to data
    data["finalScoreboard"] = scoreboard
    log.info(f"📊 Final Scoreboard Injected: {scoreboard}")
# =============================================================================
# Block 5: CLI Orchestration
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Patch and validate JSON using demo log file")
    parser.add_argument("--json", required=True, help="Path to parsed demo JSON file")
    parser.add_argument("--log", required=True, help="Path to demo .log file")
    parser.add_argument("--out", help="Path to save the sanitized output JSON")

    args = parser.parse_args()

    try:
        with open(args.json, "r", encoding="utf-8") as f:
            data = json.load(f)

        log_events = parse_log_file(args.log)
        data, added_events, added_types = sanitize_json_with_log(data, log_events)
        sanitize_metadata(data)
        reconcile_final_scoreboard(data)

        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            log.info(f"✅ Sanitized JSON saved to {args.out}")
        else:
            print(json.dumps(data, indent=2))

    except Exception as e:
        log.exception(f"💥 Error during sanitation: {e}")
        
# =============================================================================
# Block 6: Exported API Hook — generate_sanitizer_report()
# =============================================================================

def generate_sanitizer_report(json_path: str, log_path: str, out_path: str = None) -> Dict[str, Any]:
    """
    Loads demo JSON and log file, reconciles events, validates schema,
    and returns sanitized data. Optionally writes to disk if out_path provided.
    """
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        log_events = parse_log_file(log_path)
        data, _, _ = sanitize_json_with_log(data, log_events)
        sanitize_metadata(data)
        reconcile_final_scoreboard(data)

        if out_path:
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            log.info(f"✅ Sanitized report written to: {out_path}")

        return data

    except Exception as e:
        log.exception(f"💥 generate_sanitizer_report failed: {e}")
        return {}

        # =============================================================================
# EOF — data_sanitizer.py v1.0 | LOC: ~241
# =============================================================================
# ✔ Functions Implemented:
#   - parse_log_file()
#   - sanitize_json_with_log()
#   - sanitize_metadata()
#   - enrich_and_validate()
#   - reconcile_final_scoreboard()
#   - CLI orchestration block (__main__)
#
# ✔ Structural Guarantees:
#   - All key blocks (events, playerStats, advancedStats, chat) enforced
#   - FinalScoreboard derived from roundSummary
#   - .log event injection for reconciliation
#
# ✔ Logging + Fault Tolerance:
#   - Logging at WARN/INFO/ERROR level
#   - Fallback coercion logic for malformed dicts
#
# 🚧 Next Patch Candidates:
#   [1] 🔍 Add `gap_marker=True` to all injected .log events (for traceability)
#   [2] 🧪 Add test suite: test_data_sanitizer.py
#   [3] 🧠 Add schema validator per event-type (e.g., bullet_impact, player_hurt)
#   [4] 📈 Hook into file_loader.py for real-time usage
# =============================================================================
# EOB5 — CLI Bootstrap + EOF Marker
# =============================================================================

# =============================================================================
# Block 5: CLI Orchestration
# =============================================================================
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    parser = argparse.ArgumentParser(description="Patch and validate JSON using demo log file")
    parser.add_argument("--json", required=True, help="Path to parsed demo JSON file")
    parser.add_argument("--log", required=True, help="Path to demo .log file")
    parser.add_argument("--out", help="Path to save the sanitized output JSON")

    args = parser.parse_args()

    try:
        with open(args.json, "r", encoding="utf-8") as f:
            data = json.load(f)

        log_events = parse_log_file(args.log)
        data, added_events, added_types = sanitize_json_with_log(data, log_events)
        sanitize_metadata(data)
        reconcile_final_scoreboard(data)

        if args.out:
            with open(args.out, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            log.info(f"✅ Sanitized JSON saved to {args.out}")
        else:
            print(json.dumps(data, indent=2))

    except Exception as e:
        log.exception(f"💥 Error during sanitation: {e}")
        
__all__ = ["generate_sanitizer_report"]

        # =============================================================================
# EOF — data_sanitizer.py v1.0 | LOC: ~491
# =============================================================================
# ✔ Functions Implemented:
#   - parse_log_file()
#   - sanitize_json_with_log()
#   - sanitize_metadata()
#   - enrich_and_validate()
#   - reconcile_final_scoreboard()
#   - CLI orchestration block (__main__)
#
# ✔ Structural Guarantees:
#   - All key blocks (events, playerStats, advancedStats, chat) enforced
#   - FinalScoreboard derived from roundSummary
#   - .log event injection for reconciliation
#
# ✔ Logging + Fault Tolerance:
#   - Logging at WARN/INFO/ERROR level
#   - Fallback coercion logic for malformed dicts
#
# 🚧 Next Patch Candidates:
#   [1] 🔍 Add `gap_marker=True` to all injected .log events (for traceability)
#   [2] 🧪 Add test suite: test_data_sanitizer.py
#   [3] 🧠 Add schema validator per event-type (e.g., bullet_impact, player_hurt)
#   [4] 📈 Hook into file_loader.py for real-time usage
# =============================================================================
# EOB5 — CLI Bootstrap + EOF Marker
# =============================================================================
