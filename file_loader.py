#!/usr/bin/env python3
# =============================================================================
# file_loader.py — CS2 Nested Data Structure Fix
# Event structure: ['type', 'tick', 'timestamp', 'data']
# =============================================================================

import os
import sys
import json
import logging
import subprocess
import platform
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
def _build_nested_aware_structure(events):
    """
    Fallback builder: wrap raw events in a dict and pass to enhancer.
    This ensures _load_json_nested_aware never NameErrors.
    """
    data = {"events": events}
    return _enhance_nested_data(data)

# Optional chardet import
try:
    import chardet
    HAS_CHARDET = True
except ImportError:
    HAS_CHARDET = False
    chardet = None

log = logging.getLogger(__name__)

# Configuration
PEWPEW_DIR = Path("pewpew")
V3_EXECUTABLE = "CS2-ACS-v3.exe" if platform.system() == "Windows" else "./cs2-acs-v3"
DEFAULT_ENCODING = "utf-8"

class FileLoadError(Exception):
    """Custom exception for file loading errors"""
    pass

def load_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Main entry point with nested data structure support"""
    if not filepath:
        log.error("❌ No filepath provided")
        return None
        
    path_obj = Path(filepath)
    if not path_obj.exists():
        log.error(f"❌ File not found: {filepath}")
        return None

    ext = path_obj.suffix.lower()
    
    try:
        if ext == ".json":
            log.info("📄 Loading JSON with nested structure support")
            return _load_json_nested_aware(filepath)
        elif ext == ".dem":
            log.info("🎮 Parsing demo with V3 parser")
            return _parse_demo_nested_aware(filepath)
        else:
            log.warning(f"⚠️ Unsupported file type: {ext}")
            return None
            
    except Exception as e:
        log.exception(f"❌ Load file failed: {e}")
        return None

def _detect_encoding(filepath: str) -> str:
    """Detect file encoding using chardet (if available)"""
    if not HAS_CHARDET:
        log.info("📦 chardet not available, using default encoding")
        return DEFAULT_ENCODING
    
    try:
        with open(filepath, 'rb') as f:
            raw_data = f.read(10000)  # Read first 10KB for detection
            
        result = chardet.detect(raw_data)
        encoding = result.get('encoding', DEFAULT_ENCODING)
        confidence = result.get('confidence', 0)
        
        log.info(f"🔍 Detected encoding: {encoding} (confidence: {confidence:.2f})")
        
        # Fallback to utf-8 if confidence is too low
        if confidence < 0.7:
            log.warning(f"⚠️ Low confidence encoding, using {DEFAULT_ENCODING}")
            encoding = DEFAULT_ENCODING
            
        return encoding
    except Exception as e:
        log.warning(f"⚠️ Encoding detection failed: {e}, using {DEFAULT_ENCODING}")
        return DEFAULT_ENCODING

def _load_json_nested_aware(json_path: str) -> Optional[Dict[str, Any]]:
    """Load JSON with awareness of nested data structures and robust encoding handling"""
    try:
        # First, detect the encoding
        detected_encoding = _detect_encoding(json_path)
        
        # Try multiple encoding strategies
        encodings_to_try = [
            detected_encoding,
            'utf-8-sig',  # UTF-8 with BOM
            'utf-8',
            'latin1',     # Can decode any byte sequence
            'cp1252',     # Windows encoding
        ]
        
        content = None
        content = None
        used_encoding = None
        
        for encoding in encodings_to_try:
            try:
                with open(json_path, 'r', encoding=encoding, errors='replace') as f:
                    content = f.read()
                used_encoding = encoding
                log.info(f"✅ Successfully read file with encoding: {encoding}")
                break
            except UnicodeDecodeError as e:
                log.warning(f"⚠️ Failed to read with {encoding}: {e}")
                continue
        
        if content is None:
            raise FileLoadError(f"Could not read file with any encoding")
        
        # Clean content
        content = content.strip()
        if content.startswith('\ufeff'):  # Remove BOM
            content = content[1:]
        
        # Parse JSON
        if content.startswith('['):
            events = json.loads(content)
            log.info(f"✅ Loaded {len(events)} events")
            return _build_nested_aware_structure(events)
        elif content.startswith('{'):
            data = json.loads(content)
            log.info(f"✅ Loaded JSON object")
            return _enhance_nested_data(data)
        else:
            log.error("❌ Unknown JSON format - content doesn't start with '[' or '{'")
            return None
            
    except json.JSONDecodeError as e:
        log.error(f"❌ JSON parsing failed: {e}")
        return None
    except Exception as e:
        log.exception(f"❌ JSON load failed: {e}")
        return None

def _parse_demo_nested_aware(demo_path: str) -> Optional[Dict[str, Any]]:
    """Parse demo with nested structure awareness"""
    v3_executable = _find_v3_executable()
    if not v3_executable:
        log.error("❌ CS2-ACS-v3 executable not found")
        log.info("💡 Please ensure CS2-ACS-v3.exe is in the project directory")
        return None

    output_path = PEWPEW_DIR
    output_path.mkdir(parents=True, exist_ok=True)
    demo_abspath = str(Path(demo_path).resolve())
    
    # Check if demo file exists and is readable
    if not Path(demo_abspath).exists():
        log.error(f"❌ Demo file not found: {demo_abspath}")
        return None
    
    command = [
        v3_executable,
        "--demo", demo_abspath,
        "--output-dir", str(output_path),
        "--disable-ndjson",
        "--batch-size", "10000"
    ]
    
    log.info(f"🚀 Parser command: {' '.join(command)}")
    
    try:
        result = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            timeout=300,
            cwd=Path.cwd()  # Ensure we run from current directory
        )
        
        if result.returncode == 0:
            log.info("✅ Parser successful")
            log.info(f"📤 Parser stdout: {result.stdout[:200]}...")
            
            json_files = list(output_path.glob("*.json"))
            if json_files:
                latest_file = max(json_files, key=lambda p: p.stat().st_mtime)
                log.info(f"📁 Loading parsed file: {latest_file}")
                return _load_json_nested_aware(str(latest_file))
            else:
                log.error("❌ No JSON files found in output directory")
        else:
            log.error(f"❌ Parser failed (code {result.returncode})")
            log.error(f"📥 Parser stderr: {result.stderr}")
            log.error(f"📤 Parser stdout: {result.stdout}")
            
    except subprocess.TimeoutExpired:
        log.error("❌ Parser timed out after 300 seconds")
    except Exception as e:
        log.error(f"❌ Parser exception: {e}")
    
    return None


def _extract_v3_players(events: List[Dict]) -> List[Dict]:
    """
    Pull unique player IDs from v3 events under data.shooter and data.victim
    and wrap them into dicts for downstream processing.
    """
    ids = set()
    for ev in events:
        data = ev.get("data", {})
        for key in ("shooter", "victim"):
            val = data.get(key)
            if isinstance(val, int):
                ids.add(val)

    players = []
    for pid in sorted(ids):
        players.append({"id": pid})
    log.info(f"✅ V3 player extraction: {len(players)} unique players")
    return players

    
    
    players = {}
    
    log.info("🔍 Scanning events for nested player data...")
    
    # Sample some events to understand the structure
    sample_event = events[0] if events else {}
    log.info(f"📋 Sample event keys: {list(sample_event.keys()) if sample_event else 'No events'}")
    
    if sample_event and 'data' in sample_event:
        data_sample = sample_event['data']
        if isinstance(data_sample, dict):
            log.info(f"📋 Sample data keys: {list(data_sample.keys())}")
        else:
            log.info(f"📋 Sample data type: {type(data_sample)}")
    
    player_extraction_stats = {
        "events_processed": 0,
        "events_with_data": 0,
        "player_objects_found": 0
    }
    
    for event in events:
        if not isinstance(event, dict):
            continue
        
        player_extraction_stats["events_processed"] += 1
        
        # Strategy 1: Look in event.data for player objects
        event_data = event.get("data", {})
        if isinstance(event_data, dict):
            player_extraction_stats["events_with_data"] += 1
            
            # Common CS2 player fields in data
            player_fields = ["attacker", "victim", "user", "player", "killer", "assister", "thrower", "defuser"]
            
            for field in player_fields:
                player_obj = event_data.get(field)
                if isinstance(player_obj, dict):
                    player_extraction_stats["player_objects_found"] += 1
                    _process_nested_player_object(player_obj, players)
            
            # Strategy 2: Look for direct player fields in event root
            for field in player_fields:
                player_obj = event.get(field)
                if isinstance(player_obj, dict):
                    player_extraction_stats["player_objects_found"] += 1
                    _process_nested_player_object(player_obj, players)
            
            # Strategy 3: Look for steamid patterns anywhere in the data
            _scan_for_steamid_patterns(event_data, players)
    
    log.info(f"📊 Extraction stats: {player_extraction_stats}")
    
    # Convert to list and calculate statistics
    player_list = list(players.values())
    
    # Calculate game statistics from events
    _calculate_nested_statistics(player_list, events)
    
    log.info(f"✅ Nested player extraction: {len(player_list)} unique players")
    return player_list

def _process_nested_player_object(player_obj: Dict, players: Dict):
    """Process a nested player object"""
    if not isinstance(player_obj, dict):
        return
    
    # Extract ID using multiple patterns
    steamid = None
    for id_field in ["steamid", "steam_id", "steam_id64", "user_id", "id", "accountid"]:
        if id_field in player_obj:
            steamid = str(player_obj[id_field])
            break
    
    # Extract name using multiple patterns
    name = "Unknown"
    for name_field in ["name", "player_name", "username", "displayname"]:
        if name_field in player_obj:
            name = str(player_obj[name_field])
            break
    
    # Only add if we have valid data
    if steamid and steamid != "0" and len(steamid) > 5 and name != "Unknown":
        if steamid not in players:
            players[steamid] = {
                "steam_id64": steamid,
                "name": name,
                "kills": 0, 
                "deaths": 0, 
                "assists": 0, 
                "damage": 0,
                "headshots": 0,
                "score": 0
            }

def _scan_for_steamid_patterns(data: Any, players: Dict):
    """Scan for steamid patterns in nested data"""
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, str) and len(value) == 17 and value.startswith('7656119'):
                # Found a potential SteamID64
                name = data.get("name") or data.get("player_name") or "Unknown"
                if name != "Unknown":
                    if value not in players:
                        players[value] = {
                            "steam_id64": value,
                            "name": name,
                            "kills": 0, 
                            "deaths": 0, 
                            "assists": 0, 
                            "damage": 0,
                            "headshots": 0,
                            "score": 0
                        }
            elif isinstance(value, (dict, list)):
                _scan_for_steamid_patterns(value, players)
    elif isinstance(data, list):
        for item in data:
            _scan_for_steamid_patterns(item, players)

def _calculate_nested_statistics(players: List[Dict], events: List[Dict]):
    """Calculate statistics from events with nested structure"""
    if not players or not events:
        return
    
    log.info("📊 Calculating statistics from nested events...")
    
    player_lookup = {p["steam_id64"]: p for p in players}
    
    stats = {
        "kill_events": 0,
        "damage_events": 0,
        "assist_events": 0,
        "headshot_events": 0
    }
    
    for event in events:
        if not isinstance(event, dict):
            continue
        
        event_type = event.get("type", "").lower()
        event_data = event.get("data", {})
        
        # Handle kill/death events
        if any(keyword in event_type for keyword in ["kill", "death", "elimination", "frag"]):
            stats["kill_events"] += 1
            
            # Look in both event root and data
            attacker = event_data.get("attacker") or event.get("attacker")
            victim = event_data.get("victim") or event.get("victim")
            headshot = event_data.get("headshot") or event.get("headshot", False)
            
            if isinstance(attacker, dict):
                attacker_id = str(attacker.get("steamid", attacker.get("steam_id64", "0")))
                if attacker_id in player_lookup:
                    player_lookup[attacker_id]["kills"] += 1
                    if headshot:
                        player_lookup[attacker_id]["headshots"] += 1
                        stats["headshot_events"] += 1
            
            if isinstance(victim, dict):
                victim_id = str(victim.get("steamid", victim.get("steam_id64", "0")))
                if victim_id in player_lookup:
                    player_lookup[victim_id]["deaths"] += 1
        
        # Handle damage events
        elif any(keyword in event_type for keyword in ["damage", "hurt", "hit"]):
            stats["damage_events"] += 1
            
            attacker = event_data.get("attacker") or event.get("attacker")
            damage = event_data.get("damage") or event.get("damage", 0)
            
            if isinstance(attacker, dict) and isinstance(damage, (int, float)):
                attacker_id = str(attacker.get("steamid", attacker.get("steam_id64", "0")))
                if attacker_id in player_lookup:
                    player_lookup[attacker_id]["damage"] += damage
        
        # Handle assist events
        elif "assist" in event_type:
            stats["assist_events"] += 1
            
            assister = event_data.get("assister") or event.get("assister")
            if isinstance(assister, dict):
                assister_id = str(assister.get("steamid", assister.get("steam_id64", "0")))
                if assister_id in player_lookup:
                    player_lookup[assister_id]["assists"] += 1
    
    # Calculate K/D ratio and score for each player
    for player in players:
        kills = player["kills"]
        deaths = player["deaths"]
        assists = player["assists"]
        
        # Calculate K/D ratio
        player["kd_ratio"] = kills / max(deaths, 1)
        
        # Calculate score (simple formula)
        player["score"] = kills * 2 + assists - deaths
    
    log.info(f"📊 Event processing stats: {stats}")

def _extract_smart_rounds(events: List[Dict]) -> List[Dict]:
    """Smart round extraction with better logic"""
    if not events:
        return []
    
    rounds = []
    round_events = []
    
    # Find round-related events
    round_keywords = ["round_start", "round_end", "round_freeze", "round_announce", "round_prestart"]
    
    for event in events:
        if isinstance(event, dict):
            event_type = event.get("type", "").lower()
            if any(keyword in event_type for keyword in round_keywords):
                round_events.append(event)
    
    log.info(f"🎯 Found {len(round_events)} round-related events")
    
    # Extract round numbers from events
    round_numbers = set()
    for event in round_events:
        event_data = event.get("data", {})
        
        # Look for round number in various places
        for field in ["round", "round_number", "round_phase", "current_round"]:
            round_num = event_data.get(field) or event.get(field)
            if isinstance(round_num, int) and 1 <= round_num <= 30:
                round_numbers.add(round_num)
    
    # If we found specific round numbers, use them
    if round_numbers:
        max_round = max(round_numbers)
        log.info(f"🎯 Found specific round numbers, max round: {max_round}")
        
        for round_num in sorted(round_numbers):
            rounds.append({
                "number": round_num,
                "start_tick": round_num * 1000,
                "end_tick": (round_num + 1) * 1000
            })
    else:
        # Estimate from round events (each round_start/round_end pair = 1 round)
        estimated_rounds = len(round_events) // 2 if round_events else 16
        estimated_rounds = max(estimated_rounds, 16)  # Minimum 16
        estimated_rounds = min(estimated_rounds, 30)  # Maximum 30
        
        log.info(f"🎯 Estimated {estimated_rounds} rounds from {len(round_events)} round events")
        
        for i in range(1, estimated_rounds + 1):
            rounds.append({
                "number": i,
                "start_tick": i * 1000,
                "end_tick": (i + 1) * 1000
            })
    
    return rounds

def _enhance_nested_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """Enhance data with GUI requirements"""
    try:
        # Ensure required keys exist
        if "playerStats" not in data:
            data["playerStats"] = []
        if "rounds" not in data:
            data["rounds"] = []
        if "events" not in data:
            data["events"] = []
        
        # Build dropdowns
        data["playerDropdown"] = _build_player_dropdown(data.get("playerStats", []))
        data["roundDropdown"] = _build_round_dropdown(data.get("rounds", []))
        
        # Add metadata
        data["metadata"] = {
            "total_players": len(data.get("playerStats", [])),
            "total_rounds": len(data.get("rounds", [])),
            "total_events": len(data.get("events", [])),
            "parser_version": data.get("parser_version", "v3-nested-aware"),
            "parsed_at": data.get("parsed_at", datetime.now().isoformat())
        }
        
        # Log final summary
        players = len(data.get("playerStats", []))
        rounds = len(data.get("rounds", []))
        events = len(data.get("events", []))
        
        log.info(f"✅ Nested-aware data enhanced: {players} players, {rounds} rounds, {events} events")
        
        return data
        
    except Exception as e:
        log.error(f"❌ Data enhancement failed: {e}")
        return data

def _build_player_dropdown(players: List[Dict]) -> List[str]:
    """Build player dropdown"""
    dropdown = ["All Players"]
    
    for player in players:
        name = player.get("name", "Unknown")
        steamid = player.get("steam_id64", "0")
        steam2 = _convert_steamid64_to_steam2(steamid)
        dropdown.append(f"{name} ({steam2})")
    
    return dropdown

def _build_round_dropdown(rounds: List[Dict]) -> List[str]:
    """Build round dropdown"""
    dropdown = ["All Rounds"]
    
    for round_data in rounds:
        number = round_data.get("number", 1)
        dropdown.append(f"Round {number}")
    
    return dropdown

def _convert_steamid64_to_steam2(steamid64: Union[str, int]) -> str:
    """Convert SteamID64 to Steam2"""
    try:
        if not steamid64 or steamid64 == "0":
            return "STEAM_0:0:0"
        steamid64 = int(steamid64)
        steam_id = steamid64 - 76561197960265728
        return f"STEAM_0:{steam_id % 2}:{steam_id // 2}"
    except (ValueError, TypeError):
        return "STEAM_0:0:0"

def _find_v3_executable() -> Optional[str]:
    """Find V3 executable"""
    possible_paths = [
        "CS2-ACS-v3.exe",
        "bin/CS2-ACS-v3.exe", 
        "./cs2-acs-v3",
        "cs2-acs-v3",
        Path.cwd() / "CS2-ACS-v3.exe",
        Path.cwd() / "bin" / "CS2-ACS-v3.exe"
    ]
    
    for path in possible_paths:
        path_obj = Path(path)
        if path_obj.exists() and path_obj.is_file():
            log.info(f"✅ Found V3 executable: {path_obj.absolute()}")
            return str(path_obj)
    
    log.warning("⚠️ V3 executable not found in any of these locations:")
    for path in possible_paths:
        log.warning(f"  - {Path(path).absolute()}")
    
    return None

# Test functions for development
def test_json_loading():
    """Test JSON loading functionality"""
    test_data = {
        "events": [
            {
                "type": "player_kill",
                "tick": 1000,
                "data": {
                    "attacker": {"steamid": "76561198000000001", "name": "Player1"},
                    "victim": {"steamid": "76561198000000002", "name": "Player2"}
                }
            }
        ]
    }
    
    # Create test file
    test_file = "test_data.json"
    with open(test_file, 'w') as f:
        json.dump(test_data, f)
    
    # Test loading
    result = load_file(test_file)
    
    # Cleanup
    Path(test_file).unlink(missing_ok=True)
    
    return result is not None

if __name__ == "__main__":
    # Simple test
    logging.basicConfig(level=logging.INFO)
    print("🧪 Testing file_loader module...")
    
    if test_json_loading():
        print("✅ JSON loading test passed")
    else:
        print("❌ JSON loading test failed")

__all__ = ["load_file", "FileLoadError"]