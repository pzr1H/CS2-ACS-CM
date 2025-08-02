#!/usr/bin/env python3
# =============================================================================
# file_loader.py — V2 Native File Loader for CS2-ACS-v2 (FIXED VERSION)
# Wired for integration with main.py
# =============================================================================

import os
import sys
import json
import logging
import subprocess
import platform
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

log = logging.getLogger(__name__)

# Configuration
PEWPEW_DIR = Path("pewpew")
V2_EXECUTABLE = "CS2-ACS-v2.exe" if platform.system() == "Windows" else "./cs2-acs-v2"
DEFAULT_ENCODING = "utf-8"

# Fallback utility functions (in case utils modules don't exist)
def extract_player_dropdown_fallback(data):
    """Fallback function to extract player data"""
    try:
        players = []
        
        # Try v2 carmack format first
        if "playerStats" in data and isinstance(data["playerStats"], list):
            for player in data["playerStats"]:
                name = player.get("name", "Unknown")
                steamid = _convert_steamid64_to_steam2(player.get("steam_id64"))
                players.append(f"{name} ({steamid})")
        
        # Try legacy format
        elif "events" in data:
            player_set = set()
            for event in data["events"]:
                if isinstance(event, dict):
                    for key in ["attacker", "victim", "user", "player"]:
                        player = event.get(key)
                        if isinstance(player, dict) and "name" in player:
                            name = player["name"]
                            steamid = player.get("steamid", "Unknown")
                            player_set.add(f"{name} ({steamid})")
            players = list(player_set)
        
        log.info(f"✅ Extracted {len(players)} players (fallback)")
        return players
        
    except Exception as e:
        log.warning(f"Player extraction fallback failed: {e}")
        return []

def extract_round_dropdown_fallback(data):
    """Fallback function to extract round data"""
    try:
        round_labels = []
        round_meta = {}
        
        # Try v2 carmack format first
        if "rounds" in data and isinstance(data["rounds"], list):
            for i, round_info in enumerate(data["rounds"]):
                number = round_info.get("number", i + 1)
                winner = round_info.get("winner", "")
                ct_score = round_info.get("ct_score")
                t_score = round_info.get("t_score")
                
                label = f"Round {number}"
                if winner:
                    label += f" ({winner} win)"
                if ct_score is not None and t_score is not None:
                    label += f" [{ct_score}-{t_score}]"
                
                round_labels.append(label)
                round_meta[i] = {
                    "number": number,
                    "winner": winner,
                    "ct_score": ct_score or 0,
                    "t_score": t_score or 0
                }
        
        # Try to count rounds from events as fallback
        elif "events" in data:
            round_count = 0
            for event in data["events"]:
                if isinstance(event, dict) and "round" in event.get("type", "").lower():
                    round_count += 1
            
            for i in range(max(round_count, 1)):
                round_labels.append(f"Round {i + 1}")
                round_meta[i] = {"number": i + 1}
        
        log.info(f"✅ Extracted {len(round_labels)} rounds (fallback)")
        return round_labels, round_meta
        
    except Exception as e:
        log.warning(f"Round extraction fallback failed: {e}")
        return [], {}

def build_round_metadata_fallback(rounds):
    """Fallback for round metadata building"""
    try:
        round_labels = []
        round_indices = []
        round_metadata = []
        
        for i, round_data in enumerate(rounds):
            if isinstance(round_data, dict):
                number = round_data.get("number", i + 1)
                label = f"Round {number}"
                
                round_labels.append(label)
                round_indices.append(i)
                round_metadata.append(round_data)
        
        return {
            "round_labels": round_labels,
            "round_indices": round_indices,
            "round_metadata": round_metadata
        }
    except Exception as e:
        log.warning(f"Round metadata fallback failed: {e}")
        return {"round_labels": [], "round_indices": [], "round_metadata": []}

def _convert_steamid64_to_steam2(steamid64):
    """Convert SteamID64 to Steam2 format"""
    try:
        if not steamid64:
            return "STEAM_0:0:0"
        
        steamid64 = int(steamid64)
        steam_id = steamid64 - 76561197960265728
        
        if steam_id % 2 == 0:
            return f"STEAM_0:0:{steam_id // 2}"
        else:
            return f"STEAM_0:1:{steam_id // 2}"
    except:
        return "STEAM_0:0:0"

# Try to import utility modules, fallback to our implementations
try:
    from utils.dropdown_utils import extract_player_dropdown
    log.info("✅ Using utils.dropdown_utils")
except ImportError:
    extract_player_dropdown = extract_player_dropdown_fallback
    log.info("⚠️ Using fallback player dropdown extraction")

try:
    from utils.round_dropdown_utils import extract_round_dropdown
    log.info("✅ Using utils.round_dropdown_utils")
except ImportError:
    extract_round_dropdown = extract_round_dropdown_fallback
    log.info("⚠️ Using fallback round dropdown extraction")

try:
    from utils.round_utils import build_round_metadata
    log.info("✅ Using utils.round_utils")
except ImportError:
    build_round_metadata = build_round_metadata_fallback
    log.info("⚠️ Using fallback round metadata building")

# =============================================================================
# V2 Format Validation
# =============================================================================

def _validate_v2_format(data: Dict[str, Any]) -> bool:
    """Simple validation that works with any data structure"""
    try:
        if not isinstance(data, dict) or len(data) == 0:
            log.warning("Data is empty or not a dictionary")
            return False
        
        log.info(f"📊 Data loaded with keys: {list(data.keys())}")
        
        # Check for v2 carmack format indicators
        if "parser_version" in data and "carmack" in data.get("parser_version", "").lower():
            log.info("✅ Detected v2 carmack format")
        elif "playerStats" in data and isinstance(data["playerStats"], list):
            log.info("✅ Detected v2 format (playerStats array)")
        elif "events" in data and isinstance(data["events"], list):
            log.info("✅ Detected event-based format")
        else:
            log.info("⚠️ Unknown format, proceeding with fallback processing")
        
        return True
    except Exception as e:
        log.exception(f"❌ Validation error: {e}")
        return True  # Continue even if validation fails

# =============================================================================
# Main Entry Point - MODIFIED for main.py compatibility
# =============================================================================

def load_file(filepath: str) -> Optional[Dict[str, Any]]:
    """
    Main entry point for main.py - returns just the data dict for compatibility
    
    Args:
        filepath: Path to .dem or .json file
        
    Returns:
        Dict containing parsed data, or None if failed
    """
    if not filepath or not Path(filepath).exists():
        log.error(f"❌ File not found: {filepath}")
        return None

    ext = Path(filepath).suffix.lower()
    
    try:
        if ext == ".json":
            log.info("📄 Detected JSON file — loading v2 format directly.")
            return _load_v2_json_output(filepath)
        elif ext == ".dem":
            log.info("🎮 Detected .dem file — launching v2 parser.")
            return _parse_and_load_v2_demo(filepath)
        else:
            log.warning(f"⚠️ Unsupported file type: {ext}")
            return None
            
    except Exception as e:
        log.exception(f"❌ Load file failed: {e}")
        return None

def load_file_with_metadata(filepath: str) -> tuple:
    """
    Extended version that returns the full tuple (for advanced use)
    
    Returns:
        (data_dict, player_list, round_labels, round_metadata)
    """
    if not filepath or not Path(filepath).exists():
        log.error(f"❌ File not found: {filepath}")
        return None, [], [], {}

    ext = Path(filepath).suffix.lower()
    
    try:
        if ext == ".json":
            log.info("📄 Detected JSON file — loading v2 format directly.")
            return _load_v2_json_with_metadata(filepath)
        elif ext == ".dem":
            log.info("🎮 Detected .dem file — launching v2 parser.")
            return _parse_and_load_v2_demo_with_metadata(filepath)
        else:
            log.warning(f"⚠️ Unsupported file type: {ext}")
            return None, [], [], {}
            
    except Exception as e:
        log.exception(f"❌ Load file with metadata failed: {e}")
        return None, [], [], {}

# =============================================================================
# V2 JSON Loader
# =============================================================================

def _load_v2_json_output(json_path: str) -> Optional[Dict[str, Any]]:
    """Load v2 JSON and return just the data dict"""
    try:
        with open(json_path, "r", encoding=DEFAULT_ENCODING) as f:
            parsed = json.load(f)
    except Exception as e:
        log.exception(f"❌ Failed to load v2 JSON: {json_path} — {e}")
        return None

    if not parsed or not isinstance(parsed, dict):
        log.warning("⚠️ Parsed JSON is empty or malformed.")
        return None

    # Log what v2 data structure we received
    log.info(f"📊 V2 JSON structure: {list(parsed.keys())}")
    
    # Validate v2 format
    if not _validate_v2_format(parsed):
        log.warning("⚠️ JSON validation failed, continuing anyway...")

    # Enhance data with dropdown info for compatibility
    try:
        if "playerDropdown" not in parsed:
            players = extract_player_dropdown(parsed)
            parsed["playerDropdown"] = players
            log.info(f"✅ Added playerDropdown: {len(players)} entries")
        
        if "roundDropdown" not in parsed:
            round_labels, round_meta = extract_round_dropdown(parsed)
            parsed["roundDropdown"] = round_labels
            parsed["roundMetadata"] = round_meta
            log.info(f"✅ Added roundDropdown: {len(round_labels)} entries")
            
    except Exception as e:
        log.warning(f"⚠️ Dropdown enhancement failed: {e}")

    return parsed

def _load_v2_json_with_metadata(json_path: str) -> tuple:
    """Load v2 JSON and return full metadata tuple"""
    try:
        with open(json_path, "r", encoding=DEFAULT_ENCODING) as f:
            parsed = json.load(f)
    except Exception as e:
        log.exception(f"❌ Failed to load v2 JSON: {json_path} — {e}")
        return None, [], [], {}

    if not parsed or not isinstance(parsed, dict):
        log.warning("⚠️ Parsed JSON is empty or malformed.")
        return None, [], [], {}

    # Validate v2 format
    if not _validate_v2_format(parsed):
        log.warning("⚠️ JSON doesn't appear to be v2 format, continuing anyway...")

    # Extract metadata using utility modules
    try:
        players = extract_player_dropdown(parsed)
        round_labels, round_meta = extract_round_dropdown(parsed)
        
        log.info(f"✅ Extracted {len(players)} players, {len(round_labels)} rounds")
        return parsed, players, round_labels, round_meta
        
    except Exception as e:
        log.exception(f"❌ V2 data extraction failed: {e}")
        return parsed, [], [], {}

# =============================================================================
# Demo Parser Integration
# =============================================================================

def _parse_and_load_v2_demo(demo_path: str) -> Optional[Dict[str, Any]]:
    """Parse .dem file with v2 parser and return data dict"""
    result = _parse_and_load_v2_demo_with_metadata(demo_path)
    if result[0] is not None:
        return result[0]  # Return just the data dict
    return None

def _parse_and_load_v2_demo_with_metadata(demo_path: str) -> tuple:
    """Parse .dem file with v2 parser and return full metadata tuple"""
    
    # Check if v2 parser exists
    v2_path = Path(V2_EXECUTABLE)
    if not v2_path.exists():
        # Try different locations
        possible_paths = [
            Path("CS2-ACS-v2.exe"),
            Path("bin/CS2-ACS-v2.exe"),
            Path("parser/CS2-ACS-v2.exe"),
            Path("./cs2-acs-v2"),
            Path("bin/cs2-acs-v2")
        ]
        
        for path in possible_paths:
            if path.exists():
                # Remove the global declaration from here
                V2_EXECUTABLE = str(path)
                log.info(f"✅ Found v2 parser at: {V2_EXECUTABLE}")
                break
        else:
            log.error(f"❌ V2 parser executable not found in any of: {[str(p) for p in possible_paths]}")
            return None, [], [], {}

    # Rest of your function continues unchanged...
    # Ensure output directory exists
    output_path = PEWPEW_DIR
    output_path.mkdir(parents=True, exist_ok=True)

    demo_abspath = str(Path(demo_path).resolve())
    log.info(f"🚀 Launching v2 parser: {V2_EXECUTABLE} {demo_abspath}")

    try:
        result = subprocess.run(
            [V2_EXECUTABLE, demo_abspath],
            capture_output=True,
            text=True,
            timeout=300,  # 5 minute timeout
            cwd=str(Path.cwd())  # Ensure proper working directory
        )
        
        if result.returncode != 0:
            log.error(f"⚠️ V2 parser failed (exit code {result.returncode}):")
            log.error(f"STDERR: {result.stderr}")
            log.error(f"STDOUT: {result.stdout}")
            return None, [], [], {}
        else:
            log.info("✅ V2 parser completed successfully.")
            if result.stdout.strip():
                log.debug(f"V2 parser output: {result.stdout}")
                
    except subprocess.TimeoutExpired:
        log.error("❌ V2 parser timed out after 5 minutes")
        return None, [], [], {}
    except FileNotFoundError:
        log.error(f"❌ V2 parser executable not found: {V2_EXECUTABLE}")
        return None, [], [], {}
    except Exception as e:
        log.exception(f"❌ Exception running v2 parser: {e}")
        return None, [], [], {}

    # Find the most recent JSON output file
    json_files = list(output_path.glob("*.json"))
    if not json_files:
        log.error("❌ No output JSON files found in pewpew/")
        # List directory contents for debugging
        try:
            contents = list(output_path.iterdir())
            log.info(f"Directory contents: {[f.name for f in contents]}")
        except:
            pass
        return None, [], [], {}

    # Get the most recently modified JSON file
    latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
    log.info(f"📦 Using v2 parsed file: {latest_file}")
    
    return _load_v2_json_with_metadata(str(latest_file))
# =============================================================================
# Live Parser with Console Output
# =============================================================================

def launch_v2_parser_live(demo_path: str, log_callback=None) -> Optional[str]:
    """
    Launch v2 parser and stream live output to GUI console.
    Returns path to generated JSON if successful.
    """
    if not Path(demo_path).exists():
        log.error(f"❌ DEM file not found: {demo_path}")
        return None
    
    if not Path(V2_EXECUTABLE).exists():
        log.error("❌ CS2-ACS-v2 parser not found.")
        return None

    output_path = PEWPEW_DIR
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        process = subprocess.Popen(
            [V2_EXECUTABLE, demo_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # Line buffered for live output
            universal_newlines=True
        )

        json_output_path = None
        
        # Stream stdout in real-time
        while True:
            output = process.stdout.readline()
            if output == '' and process.poll() is not None:
                break
            if output:
                line = output.strip()
                if log_callback:
                    log_callback(f"[V2 Parser] {line}")
                else:
                    print(f"[V2 Parser] {line}")

        # Get any remaining output and errors
        stdout, stderr = process.communicate(timeout=30)
        
        if process.returncode != 0:
            error_msg = f"⚠️ V2 parser stderr:\n{stderr}"
            log.error(error_msg)
            if log_callback:
                log_callback(error_msg)
            return None

        # After success, find newest output in pewpew/
        json_files = list(output_path.glob("*.json"))
        if json_files:
            json_output_path = str(max(json_files, key=lambda f: f.stat().st_mtime))
            log.info(f"✅ V2 parser generated: {json_output_path}")

        return json_output_path

    except subprocess.TimeoutExpired:
        log.error("❌ V2 parser communication timeout")
        try:
            process.kill()
        except:
            pass
        return None
    except Exception as e:
        log.exception(f"❌ Live v2 parser execution failed: {e}")
        return None

# =============================================================================
# Debug and Utility Functions
# =============================================================================

def debug_v2_data_structure(data: Dict[str, Any]) -> None:
    """Debug helper to inspect v2 data structure."""
    log.info("🔍 V2 Data Structure Debug:")
    log.info(f"Main keys: {list(data.keys())}")
    
    if "playerStats" in data:
        player_stats = data["playerStats"]
        log.info(f"PlayerStats: {len(player_stats)} players")
        if player_stats and isinstance(player_stats, list):
            sample_player = player_stats[0]
            log.info(f"Sample player keys: {list(sample_player.keys())}")
    
    if "events" in data:
        events = data["events"]
        log.info(f"Events: {len(events)} events")
        if events and isinstance(events, list):
            sample_event = events[0]
            if isinstance(sample_event, dict):
                log.info(f"Sample event keys: {list(sample_event.keys())}")
    
    if "rounds" in data:
        rounds = data["rounds"]
        log.info(f"Rounds: {len(rounds)} rounds")
        if rounds and isinstance(rounds, list):
            sample_round = rounds[0]
            if isinstance(sample_round, dict):
                log.info(f"Sample round keys: {list(sample_round.keys())}")
    
    if "metadata" in data:
        metadata = data["metadata"]
        log.info(f"Metadata keys: {list(metadata.keys())}")

def get_v2_parser_info() -> Dict[str, Any]:
    """Get information about the v2 parser setup."""
    info = {
        "executable_path": str(Path(V2_EXECUTABLE).resolve()),
        "executable_exists": Path(V2_EXECUTABLE).exists(),
        "output_directory": str(PEWPEW_DIR.resolve()),
        "output_dir_exists": PEWPEW_DIR.exists(),
        "platform": platform.system(),
        "utilities_available": {
            "dropdown_utils": extract_player_dropdown != extract_player_dropdown_fallback,
            "round_dropdown_utils": extract_round_dropdown != extract_round_dropdown_fallback,
            "round_utils": build_round_metadata != build_round_metadata_fallback
        }
    }
    
    if info["executable_exists"]:
        try:
            stat = Path(V2_EXECUTABLE).stat()
            info["executable_size"] = stat.st_size
            info["executable_modified"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except:
            pass
    
    return info

# Export main functions
__all__ = [
    "load_file",
    "load_file_with_metadata",
    "launch_v2_parser_live", 
    "debug_v2_data_structure",
    "get_v2_parser_info"
]