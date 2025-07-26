#!/usr/bin/env python3
# =============================================================================
# file_loader.py — CS2 ACS Data Loader (v0.0031-FIXED)
# Timestamp-TOP: 2025-07-26T14:30-EDT
# =============================================================================

import os
import json
import subprocess
import re
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from enum import Enum

from utils.logging_config import logger
from tkinter import filedialog

from utils.steam_utils import to_steam2
from cs2_parser.fallback_parser import inject_fallback_stats
from utils.data_sanitizer import sanitize_metadata, enforce_schema_safety, reconcile_final_scoreboard
from utils.scout_report import generate_stub_scout_report


# =============================================================================
# CONFIGURATION AND CONSTANTS
# =============================================================================

class FileType(Enum):
    """Supported file types for loading"""
    JSON = ".json"
    DEMO = ".dem"

@dataclass
class ParserConfig:
    """Configuration for the external parser"""
    exe_path: str = "C:/Users/jerry/Downloads/CS2-ACS-CM/CS2-ACSv1.exe"
    output_dir: str = "./pewpew"
    timeout: int = 300  # 5 minutes timeout
    
    def __post_init__(self):
        """Validate parser configuration"""
        if not os.path.exists(self.exe_path):
            logger.warning(f"⚠️ Parser executable not found: {self.exe_path}")
        
        # Ensure output directory exists
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

@dataclass
class LoadResult:
    """Result of file loading operation"""
    success: bool
    data: Optional[Dict] = None
    error_message: Optional[str] = None
    file_path: Optional[str] = None
    processing_time: Optional[float] = None

# =============================================================================
# ENHANCED FILE LOADER CLASS
# =============================================================================

class EnhancedFileLoader:
    """Enhanced file loader with better error handling and architecture"""
    
    # Regex patterns
    PLAYER_INFO_RE = re.compile(r"\b([0-9a-fA-F]{8,}):(.+)")
    SUMMARY_PATH_RE = re.compile(r"Summary:\s*(.+\.json)", re.IGNORECASE)
    
    def __init__(self, config: Optional[ParserConfig] = None):
        """Initialize the enhanced file loader"""
        self.config = config or ParserConfig()
        self.last_load_time = None
        self.last_file_path = None
        
    def load_file_with_dialog(self) -> LoadResult:
        """Show file dialog and load selected file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select CS2 demo or JSON file",
                filetypes=[
                    ("CS2 Files", "*.dem *.json"),
                    ("Demo files", "*.dem"),
                    ("JSON files", "*.json"),
                    ("All files", "*.*")
                ]
            )
            
            if not file_path:
                return LoadResult(
                    success=False,
                    error_message="No file selected"
                )
            
            return self.load_file(file_path)
            
        except Exception as e:
            logger.error(f"❌ File dialog error: {e}")
            return LoadResult(
                success=False,
                error_message=f"File dialog error: {str(e)}"
            )
    
    def load_file(self, file_path: str, console_callback: Optional[callable] = None) -> LoadResult:
        """
        Load and process a file with comprehensive error handling
        
        Args:
            file_path: Path to the file to load
            console_callback: Optional callback for live output
            
        Returns:
            LoadResult with success status and data or error information
        """
        start_time = time.time()
        
        try:
            logger.info(f"🔍 Loading file: {file_path}")
            
            # Validate file path
            if not file_path or not os.path.exists(file_path):
                return LoadResult(
                    success=False,
                    error_message=f"File not found: {file_path}",
                    file_path=file_path
                )
            
            # Determine file type
            file_type = self._get_file_type(file_path)
            if not file_type:
                return LoadResult(
                    success=False,
                    error_message=f"Unsupported file type: {file_path}",
                    file_path=file_path
                )
            
            # Load file based on type
            if file_type == FileType.JSON:
                raw_data = self._load_json_file(file_path)
            elif file_type == FileType.DEMO:
                raw_data = self._load_demo_file(file_path, console_callback)
            else:
                return LoadResult(
                    success=False,
                    error_message=f"Unsupported file type: {file_type}",
                    file_path=file_path
                )
            
            if raw_data is None:
                return LoadResult(
                    success=False,
                    error_message="Failed to load raw data from file",
                    file_path=file_path
                )
            
            # Process and enrich the data
            processed_data = self._process_data(raw_data)
            
            processing_time = time.time() - start_time
            self.last_load_time = processing_time
            self.last_file_path = file_path
            
            logger.info(f"✅ File loaded successfully in {processing_time:.2f}s: {file_path}")
            
            return LoadResult(
                success=True,
                data=processed_data,
                file_path=file_path,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = f"Unexpected error loading {file_path}: {str(e)}"
            logger.error(f"❌ {error_msg}")
            
            return LoadResult(
                success=False,
                error_message=error_msg,
                file_path=file_path,
                processing_time=processing_time
            )
    
    def _get_file_type(self, file_path: str) -> Optional[FileType]:
        """Determine file type from extension"""
        try:
            extension = Path(file_path).suffix.lower()
            for file_type in FileType:
                if extension == file_type.value:
                    return file_type
            return None
        except Exception:
            return None
    
    def _load_json_file(self, file_path: str) -> Optional[Dict]:
        """Load JSON file with error handling"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            logger.info(f"📄 JSON file loaded: {file_path}")
            return data
        except json.JSONDecodeError as e:
            logger.error(f"❌ Invalid JSON format: {e}")
            return None
        except UnicodeDecodeError as e:
            logger.error(f"❌ Unicode decode error: {e}")
            return None
        except Exception as e:
            logger.error(f"❌ Error loading JSON file: {e}")
            return None
    
    def _load_demo_file(self, file_path: str, console_callback: Optional[callable] = None) -> Optional[Dict]:
        """Load demo file using external parser"""
        try:
            logger.info(f"🔧 Running parser on demo file: {file_path}")
            
            # Validate parser executable
            if not os.path.exists(self.config.exe_path):
                logger.error(f"❌ Parser executable not found: {self.config.exe_path}")
                return None
            
            # Run parser process
            parser_result = self._run_parser(file_path, console_callback)
            if not parser_result.success:
                logger.error(f"❌ Parser failed: {parser_result.error_message}")
                return None
            
            # Load the generated JSON
            summary_path = parser_result.data
            if not summary_path or not os.path.exists(summary_path):
                logger.error(f"❌ Parser output file not found: {summary_path}")
                return None
            
            return self._load_json_file(summary_path)
            
        except Exception as e:
            logger.error(f"❌ Error loading demo file: {e}")
            return None
    
    def _run_parser(self, demo_path: str, console_callback: Optional[callable] = None) -> LoadResult:
        """Run the external parser with comprehensive error handling"""
        try:
            cmd = [self.config.exe_path, "-demo", demo_path, "-outdir", self.config.output_dir]
            logger.info(f"🚀 Executing: {' '.join(cmd)}")
            
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
            
            stdout_lines = []
            stderr_lines = []
            
            # Read output with timeout
            start_time = time.time()
            while True:
                if time.time() - start_time > self.config.timeout:
                    process.kill()
                    return LoadResult(
                        success=False,
                        error_message=f"Parser timeout after {self.config.timeout}s"
                    )
                
                out_line = process.stdout.readline()
                if out_line:
                    stdout_lines.append(out_line)
                    if console_callback:
                        console_callback(out_line.strip())
                
                err_line = process.stderr.readline()
                if err_line:
                    stderr_lines.append(err_line)
                    if console_callback:
                        console_callback(f"[STDERR] {err_line.strip()}")
                
                if not out_line and not err_line and process.poll() is not None:
                    break
            
            process.wait()
            stdout = ''.join(stdout_lines)
            stderr = ''.join(stderr_lines)
            
            logger.debug(f"Parser stdout: {stdout}")
            if stderr:
                logger.debug(f"Parser stderr: {stderr}")
            
            if process.returncode != 0:
                return LoadResult(
                    success=False,
                    error_message=f"Parser failed with return code {process.returncode}"
                )
            
            # Find summary file path
            summary_path = self._find_summary_path(stdout)
            if not summary_path:
                return LoadResult(
                    success=False,
                    error_message="Could not locate parser output file"
                )
            
            return LoadResult(
                success=True,
                data=summary_path
            )
            
        except subprocess.SubprocessError as e:
            return LoadResult(
                success=False,
                error_message=f"Subprocess error: {str(e)}"
            )
        except Exception as e:
            return LoadResult(
                success=False,
                error_message=f"Parser execution error: {str(e)}"
            )
    
    def _find_summary_path(self, stdout: str) -> Optional[str]:
        """Find summary JSON path from parser output"""
        try:
            # Try to extract from stdout
            for line in stdout.splitlines():
                match = self.SUMMARY_PATH_RE.search(line)
                if match:
                    summary_path = os.path.normpath(match.group(1))
                    if os.path.exists(summary_path):
                        logger.info(f"📄 Found summary file: {summary_path}")
                        return summary_path
            
            # Fallback: find latest summary file
            summary_files = list(Path(self.config.output_dir).glob("summary-*.json"))
            if summary_files:
                latest_file = max(summary_files, key=lambda f: f.stat().st_mtime)
                logger.warning(f"⚠️ Using latest summary file: {latest_file}")
                return str(latest_file)
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Error finding summary path: {e}")
            return None
    
    def _process_data(self, raw_data: Dict) -> Dict:
        """Process and enrich raw data with comprehensive validation"""
        try:
            # Step 1: Start with a copy to avoid modifying original
            data = raw_data.copy() if raw_data else {}
            
            # Step 2: Sanitize metadata
            data = sanitize_metadata(data)
            
            # Step 3: Reconcile scoreboard
            data = reconcile_final_scoreboard(data)
            
            # Step 4: Ensure dropdown data exists
            data = self._ensure_dropdown_data(data)
            
            # Step 5: Extract round information
            self._extract_round_info(data)
            
            # Step 6: Enrich with metadata
            self._enrich_metadata(data)
            
            # Step 7: Inject fallback stats if needed
            self._inject_fallback_stats(data)
            
            # Step 8: Inject scout stats
            self._inject_scout_stats(data)
            
            # Step 9: Validate final data
            self._validate_processed_data(data)
            
            # Step 10: Enforce schema safety
            data = enforce_schema_safety(data)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Data processing error: {e}")
            # Return minimal safe data structure
            return self._create_fallback_data(raw_data)
    
    def _ensure_dropdown_data(self, data: Dict) -> Dict:
        """Ensure all dropdown menus have populated data with comprehensive fallbacks"""
        try:
            # Ensure playerDropdown exists and is populated
            if not data.get("playerDropdown"):
                logger.info("🔍 Extracting player dropdown data from events")
                players = self._extract_players_from_events(data.get("events", []))
                
                # If no players found from events, try playerStats
                if not players and data.get("playerStats"):
                    logger.info("🔍 Extracting players from playerStats")
                    players = self._extract_players_from_stats(data["playerStats"])
                
                # If still no players, create placeholder
                if not players:
                    logger.warning("⚠️ No players found, creating placeholder")
                    players = [{"steamid": "0", "steam2": "STEAM_0:0:0", "name": "Unknown Player", "display_name": "Unknown Player"}]
                
                data["playerDropdown"] = players
            
            # Ensure we have properly formatted event data
            events = data.get("events", [])
            if events:
                # Ensure events have proper structure for Event Log display
                formatted_events = []
                for i, event in enumerate(events):
                    formatted_event = self._format_event_for_display(event, i)
                    formatted_events.append(formatted_event)
                data["formatted_events"] = formatted_events
                logger.info(f"✅ Formatted {len(formatted_events)} events for display")
            
            # Ensure teamDropdown exists
            if not data.get("teamDropdown"):
                logger.info("🔍 Creating team dropdown data")
                data["teamDropdown"] = self._create_team_dropdown(data)
            
            # Ensure mapDropdown exists
            if not data.get("mapDropdown"):
                logger.info("🔍 Creating map dropdown data")
                data["mapDropdown"] = self._create_map_dropdown(data)
            
            # Ensure weaponDropdown exists
            if not data.get("weaponDropdown"):
                logger.info("🔍 Creating weapon dropdown data")
                data["weaponDropdown"] = self._create_weapon_dropdown(data)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Error ensuring dropdown data: {e}")
            return data
    
    def _extract_players_from_stats(self, player_stats: Dict) -> List[Dict]:
        """Extract players from playerStats when events don't contain player info"""
        players = []
        try:
            for steamid, stats in player_stats.items():
                if not isinstance(stats, dict):
                    continue
                    
                name = stats.get("name", stats.get("username", f"Player_{steamid[-4:]}"))
                try:
                    steam2 = to_steam2(int(steamid))
                except (ValueError, TypeError):
                    steam2 = f"STEAM_0:0:{steamid}"
                
                players.append({
                    "steamid": steamid,
                    "steam2": steam2,
                    "name": self._clean_player_name(name),
                    "display_name": self._clean_player_name(name)
                })
            
            logger.info(f"✅ Extracted {len(players)} players from playerStats")
            return players
        except Exception as e:
            logger.error(f"❌ Error extracting players from stats: {e}")
            return []
    
    def _format_event_for_display(self, event: Dict, index: int) -> Dict:
        """Format event for proper display in Event Log"""
        try:
            formatted = {
                "index": index,
                "type": event.get("type", "Unknown Event"),
                "round": event.get("round", -1),
                "tick": event.get("tick", 0),
                "time": event.get("time", 0.0),
                "details": event.get("details", {}),
                "raw_event": event  # Keep original for detailed view
            }
            
            # Add human-readable description
            event_type = event.get("type", "")
            if event_type == "events.PlayerDeath":
                attacker = event.get("attacker", {})
                victim = event.get("victim", {})
                weapon = event.get("weapon", "Unknown")
                
                attacker_name = "Unknown"
                victim_name = "Unknown"
                
                if isinstance(attacker, dict):
                    attacker_name = attacker.get("name", "Unknown")
                elif isinstance(attacker, str):
                    attacker_name = attacker
                    
                if isinstance(victim, dict):
                    victim_name = victim.get("name", "Unknown")
                elif isinstance(victim, str):
                    victim_name = victim
                    
                formatted["description"] = f"{attacker_name} killed {victim_name} with {weapon}"
                
            elif event_type == "events.RoundStart":
                formatted["description"] = "Round started"
            elif event_type == "events.RoundEnd":
                winner = event.get("winner", "Unknown")
                formatted["description"] = f"Round ended - Winner: {winner}"
            elif event_type == "events.BombPlanted":
                user = event.get("user", {})
                user_name = user.get("name", "Unknown") if isinstance(user, dict) else str(user)
                formatted["description"] = f"{user_name} planted the bomb"
            elif event_type == "events.BombDefused":
                user = event.get("user", {})
                user_name = user.get("name", "Unknown") if isinstance(user, dict) else str(user)
                formatted["description"] = f"{user_name} defused the bomb"
            else:
                formatted["description"] = event_type.replace("events.", "").replace("_", " ").title()
            
            return formatted
            
        except Exception as e:
            logger.warning(f"⚠️ Error formatting event {index}: {e}")
            return {
                "index": index,
                "type": "Malformed Event",
                "round": -1,
                "tick": 0,
                "time": 0.0,
                "description": "Error parsing event",
                "details": {},
                "raw_event": event
            }
    
    def _extract_players_from_events(self, events: List[Dict]) -> List[Dict]:
        """Extract player information from events with multiple extraction methods"""
        found_players = {}
        
        try:
            logger.info(f"🔍 Processing {len(events)} events for player extraction")
            
            # Method 1: Extract from GenericGameEvent strings
            for event in events:
                if event.get("type") == "events.GenericGameEvent":
                    event_string = event.get("details", {}).get("string", "")
                    match = self.PLAYER_INFO_RE.search(event_string)
                    
                    if match:
                        sid_hex, name = match.groups()
                        try:
                            sid64 = str(int(sid_hex, 16))
                            steam2 = to_steam2(int(sid64))
                            clean_name = self._clean_player_name(name)
                            
                            found_players[steam2] = {
                                "steamid": sid64,
                                "steam2": steam2,
                                "name": clean_name,
                                "display_name": clean_name
                            }
                        except (ValueError, TypeError) as e:
                            logger.warning(f"⚠️ Skipping invalid SteamID {sid_hex}: {e}")
            
            # Method 2: Extract from player-related events (kills, deaths, etc.)
            player_events = ["events.PlayerDeath", "events.PlayerHurt", "events.WeaponFire", "events.BombPlanted"]
            for event in events:
                if event.get("type") in player_events:
                    # Extract attacker info
                    if "attacker" in event:
                        attacker = event["attacker"]
                        if isinstance(attacker, dict) and "steamid" in attacker:
                            self._add_player_from_event_data(found_players, attacker)
                    
                    # Extract victim info
                    if "victim" in event:
                        victim = event["victim"]
                        if isinstance(victim, dict) and "steamid" in victim:
                            self._add_player_from_event_data(found_players, victim)
                    
                    # Extract user info (for generic events)
                    if "user" in event:
                        user = event["user"]
                        if isinstance(user, dict) and "steamid" in user:
                            self._add_player_from_event_data(found_players, user)
            
            # Method 3: Extract from event details/participants
            for event in events:
                details = event.get("details", {})
                if isinstance(details, dict):
                    for key, value in details.items():
                        if isinstance(value, dict) and "steamid" in value:
                            self._add_player_from_event_data(found_players, value)
            
            players_list = list(found_players.values())
            logger.info(f"✅ Extracted {len(players_list)} players from events")
            
            # Log sample of found players for debugging
            if players_list:
                sample_players = players_list[:3]
                logger.info(f"🎮 Sample players: {[p['name'] for p in sample_players]}")
            
            return players_list
            
        except Exception as e:
            logger.error(f"❌ Error extracting players from events: {e}")
            return []
    
    def _add_player_from_event_data(self, found_players: Dict, player_data: Dict):
        """Helper to add player from event data structure"""
        try:
            steamid = player_data.get("steamid")
            name = player_data.get("name", player_data.get("username", "Unknown"))
            
            if steamid:
                try:
                    steam2 = to_steam2(int(steamid))
                    clean_name = self._clean_player_name(name)
                    
                    found_players[steam2] = {
                        "steamid": str(steamid),
                        "steam2": steam2,
                        "name": clean_name,
                        "display_name": clean_name
                    }
                except (ValueError, TypeError):
                    pass  # Skip invalid steamid
        except Exception:
            pass  # Skip malformed player data
    
    def _create_team_dropdown(self, data: Dict) -> List[Dict]:
        """Create team dropdown data"""
        try:
            teams = set()
            
            # Extract teams from player stats
            player_stats = data.get("playerStats", {})
            for stats in player_stats.values():
                if isinstance(stats, dict):
                    team = stats.get("team")
                    if team:
                        teams.add(team)
            
            # Extract teams from events
            events = data.get("events", [])
            for event in events:
                if isinstance(event, dict) and hasattr(event, 'team'):
                    teams.add(event.team)
            
            # Create dropdown structure
            team_dropdown = []
            for i, team in enumerate(sorted(teams)):
                team_dropdown.append({
                    "id": i,
                    "name": team,
                    "display_name": f"Team {team}"
                })
            
            # Ensure at least one team exists
            if not team_dropdown:
                team_dropdown = [{"id": 0, "name": "Unknown", "display_name": "Unknown Team"}]
            
            logger.info(f"✅ Created team dropdown with {len(team_dropdown)} teams")
            return team_dropdown
            
        except Exception as e:
            logger.error(f"❌ Error creating team dropdown: {e}")
            return [{"id": 0, "name": "Unknown", "display_name": "Unknown Team"}]
    
    def _create_map_dropdown(self, data: Dict) -> List[Dict]:
        """Create map dropdown data"""
        try:
            map_name = data.get("mapName", "Unknown")
            return [{
                "id": 0,
                "name": map_name,
                "display_name": map_name
            }]
        except Exception as e:
            logger.error(f"❌ Error creating map dropdown: {e}")
            return [{"id": 0, "name": "Unknown", "display_name": "Unknown Map"}]
    
    def _create_weapon_dropdown(self, data: Dict) -> List[Dict]:
        """Create weapon dropdown data from events"""
        try:
            weapons = set()
            
            # Extract weapons from weapon fire events
            events = data.get("events", [])
            for event in events:
                if isinstance(event, dict) and event.get("type") == "events.WeaponFire":
                    weapon = event.get("weapon")
                    if weapon:
                        weapons.add(weapon)
            
            # Create dropdown structure
            weapon_dropdown = []
            for i, weapon in enumerate(sorted(weapons)):
                weapon_dropdown.append({
                    "id": i,
                    "name": weapon,
                    "display_name": weapon.replace("weapon_", "").title()
                })
            
            logger.info(f"✅ Created weapon dropdown with {len(weapon_dropdown)} weapons")
            return weapon_dropdown
            
        except Exception as e:
            logger.error(f"❌ Error creating weapon dropdown: {e}")
            return []
    
    def _clean_player_name(self, name: str) -> str:
        """Clean and validate player name"""
        if not name or not isinstance(name, str):
            return "Unknown Player"
        
        # Remove non-printable characters
        cleaned = ''.join(char for char in name if char.isprintable())
        
        # Limit length
        if len(cleaned) > 32:
            cleaned = cleaned[:32] + "..."
        
        return cleaned or "Unknown Player"
    
    def _extract_round_info(self, data: Dict):
        """Extract round indices and create round labels with common sense logic"""
        try:
            events = data.get("events", [])
            round_starts = set()
            round_ends = set()
            all_rounds = set()
            
            # First pass: collect all round numbers and specific events
            for event in events:
                if not isinstance(event, dict):
                    continue
                    
                round_num = event.get("round")
                event_type = event.get("type", "")
                
                # Collect any valid round number
                if isinstance(round_num, int) and round_num >= 0:
                    all_rounds.add(round_num)
                    
                    # Track round starts and ends
                    if event_type in ["events.RoundStart", "events.RoundFreezeEnd"]:
                        round_starts.add(round_num)
                    elif event_type in ["events.RoundEnd", "events.RoundWin"]:
                        round_ends.add(round_num)
            
            # Apply common sense logic
            if all_rounds:
                min_round = min(all_rounds)
                max_round = max(all_rounds)
                
                # Create continuous round sequence (common sense: rounds should be sequential)
                round_indices = list(range(min_round, max_round + 1))
                
                # Validate round sequence makes sense
                if len(round_indices) > 50:  # Sanity check: too many rounds
                    logger.warning(f"⚠️ Unusual round count: {len(round_indices)}, using detected rounds only")
                    round_indices = sorted(all_rounds)
                
            else:
                # Fallback: assume at least one round exists if we have events
                if events:
                    logger.warning("⚠️ No round numbers found, assuming single round")
                    round_indices = [0]
                else:
                    round_indices = []
            
            # Create labels with proper numbering (1-based for display)
            round_labels = []
            for i, round_idx in enumerate(round_indices):
                # Use 1-based numbering for display
                display_num = i + 1
                round_labels.append(f"Round {display_num}")
            
            data["round_indices"] = round_indices
            data["round_labels"] = round_labels
            
            # Add additional round metadata
            data["total_rounds"] = len(round_indices)
            data["round_starts_detected"] = len(round_starts)
            data["round_ends_detected"] = len(round_ends)
            
            logger.info(f"✅ Extracted {len(round_indices)} rounds (Range: {min(round_indices) if round_indices else 'N/A'}-{max(round_indices) if round_indices else 'N/A'})")
            
        except Exception as e:
            logger.error(f"❌ Error extracting round info: {e}")
            data["round_indices"] = [0]  # Fallback to single round
            data["round_labels"] = ["Round 1"]
            data["total_rounds"] = 1
    
    def _enrich_metadata(self, data: Dict):
        """Add comprehensive metadata about the match"""
        try:
            events = data.get("events", [])
            data["event_count"] = len(events)
            data["has_chat"] = any(ev.get("type") == "events.ChatMessage" for ev in events if isinstance(ev, dict))
            data["has_rounds"] = any(ev.get("round", -1) >= 0 for ev in events if isinstance(ev, dict))
            data["has_player_hurt"] = any(ev.get("type") == "events.PlayerHurt" for ev in events if isinstance(ev, dict))
            data["has_weapon_fire"] = any(ev.get("type") == "events.WeaponFire" for ev in events if isinstance(ev, dict))
            data["has_bullet_impact"] = any(ev.get("type") == "events.BulletImpact" for ev in events if isinstance(ev, dict))
            
            # Add processing metadata
            data["processing_timestamp"] = time.time()
            data["loader_version"] = "0.0031-FIXED"
            
        except Exception as e:
            logger.error(f"❌ Error enriching metadata: {e}")
    
    def _inject_fallback_stats(self, data: Dict):
        """Inject fallback statistics if needed"""
        try:
            if not data.get("playerStats"):
                logger.info("🔄 Injecting fallback stats")
                inject_fallback_stats(data)
        except Exception as e:
            logger.warning(f"⚠️ Fallback stats injection failed: {e}")
    
    def _inject_scout_stats(self, data: Dict):
        """Inject scout statistics"""
        try:
            player_data = data.get("playerDropdown", [])
            if player_data:
                data["scoutStats"] = generate_stub_scout_report(player_data)
                logger.info("🔍 Scout stats injected successfully")
            else:
                logger.warning("⚠️ Scout stats not generated — playerDropdown missing")
        except Exception as e:
            logger.warning(f"⚠️ Scout stats generation failed: {e}")
    
    def _validate_processed_data(self, data: Dict):
        """Validate the processed data and log warnings for missing fields"""
        try:
            # Validate player dropdown
            player_dropdown = data.get("playerDropdown", [])
            if not player_dropdown:
                logger.error("❌ CRITICAL: playerDropdown is empty after processing")
            else:
                logger.info(f"✅ playerDropdown populated with {len(player_dropdown)} players")
                # Log first few players for debugging
                for i, player in enumerate(player_dropdown[:3]):
                    if isinstance(player, dict):
                        logger.info(f"   Player {i+1}: {player.get('name', 'Unknown')} ({player.get('steamid', 'No ID')})")
            
            # Validate events
            events = data.get("events", [])
            formatted_events = data.get("formatted_events", [])
            if not events:
                logger.warning("⚠️ No events found in data")
            else:
                logger.info(f"✅ {len(events)} events loaded, {len(formatted_events)} formatted for display")
            
            # Validate rounds
            round_indices = data.get("round_indices", [])
            if not round_indices:
                logger.warning("⚠️ No rounds detected")
            else:
                logger.info(f"✅ {len(round_indices)} rounds detected: {round_indices}")
            
            # Validate player stats
            player_stats = data.get("playerStats", {})
            if not player_stats:
                logger.warning("⚠️ No playerStats after processing")
            else:
                logger.info(f"✅ playerStats available for {len(player_stats)} players")
                # Check for missing critical fields
                for sid, stats in player_stats.items():
                    if isinstance(stats, dict):
                        missing_fields = []
                        for field in ["kills", "adr", "hs_percent"]:
                            if field not in stats:
                                missing_fields.append(field)
                        
                        if missing_fields:
                            logger.warning(f"⚠️ Player {sid} missing fields: {missing_fields}")
            
            # Validate dropdown data
            required_dropdowns = ["playerDropdown", "teamDropdown", "mapDropdown"]
            for dropdown in required_dropdowns:
                dropdown_data = data.get(dropdown, [])
                if not dropdown_data:
                    logger.warning(f"⚠️ Missing {dropdown} data")
                else:
                    logger.info(f"✅ {dropdown}: {len(dropdown_data)} items")
            
        except Exception as e:
            logger.error(f"❌ Error validating processed data: {e}")
    
    def _create_fallback_data(self, raw_data: Dict) -> Dict:
        """Create minimal fallback data structure when processing fails"""
        try:
            fallback_data = {
                "events": [],
                "playerStats": {},
                "playerDropdown": [],
                "teamDropdown": [],
                "mapDropdown": [],
                "weaponDropdown": [],
                "round_indices": [],
                "round_labels": [],
                "event_count": 0,
                "has_chat": False,
                "has_rounds": False,
                "has_player_hurt": False,
                "has_weapon_fire": False,
                "has_bullet_impact": False,
                "processing_timestamp": time.time(),
                "loader_version": "0.0031-FIXED-FALLBACK"
            }
            
            # Try to preserve some data from raw_data if possible
            if raw_data and isinstance(raw_data, dict):
                for key in ["events", "playerStats", "mapName"]:
                    if key in raw_data:
                        fallback_data[key] = raw_data[key]
                        
                # Update event count if we have events
                if fallback_data["events"]:
                    fallback_data["event_count"] = len(fallback_data["events"])
            
            return fallback_data
            
        except Exception:
            return {
                "error": "Failed to create fallback data structure",
                "processing_timestamp": time.time(),
                "loader_version": "0.0031-FIXED-CRITICAL-FALLBACK"
            }


# =============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Global loader instance
_default_loader = EnhancedFileLoader()

def load_and_prepare() -> Optional[Dict]:
    """Legacy function: Show file dialog and load selected file"""
    try:
        result = _default_loader.load_file_with_dialog()
        if result.success:
            logger.info("✅ load_and_prepare() completed successfully")
            return result.data
        else:
            logger.error(f"❌ load_and_prepare() failed: {result.error_message}")
            return None
    except Exception as e:
        logger.error(f"❌ load_and_prepare() exception: {e}")
        return None

def load_file(file_path: str, console_callback: Optional[callable] = None) -> Optional[Dict]:
    """Legacy function: Load file with optional console callback"""
    try:
        result = _default_loader.load_file(file_path, console_callback)
        if result.success:
            logger.info("✅ load_file() completed successfully")
            return result.data
        else:
            logger.error(f"❌ load_file() failed: {result.error_message}")
            return None
    except Exception as e:
        logger.error(f"❌ load_file() exception: {e}")
        return None

def inject_scout_stats(data: Dict):
    """Legacy function: Inject scout stats into data"""
    try:
        if data and isinstance(data, dict):
            _default_loader._inject_scout_stats(data)
    except Exception as e:
        logger.error(f"❌ inject_scout_stats() failed: {e}")

def debug_data_structure(data: Dict) -> Dict:
    """Debug function to analyze and log data structure for troubleshooting"""
    try:
        if not data:
            logger.error("❌ debug_data_structure: No data provided")
            return {}
        
        debug_info = {
            "total_keys": len(data.keys()) if isinstance(data, dict) else 0,
            "main_sections": list(data.keys()) if isinstance(data, dict) else [],
            "events_count": len(data.get("events", [])),
            "player_dropdown_count": len(data.get("playerDropdown", [])),
            "formatted_events_count": len(data.get("formatted_events", [])),
            "round_indices": data.get("round_indices", []),
            "has_player_stats": bool(data.get("playerStats")),
            "player_stats_count": len(data.get("playerStats", {})),
        }
        
        logger.info("🔧 DATA STRUCTURE DEBUG:")
        for key, value in debug_info.items():
            logger.info(f"   {key}: {value}")
        
        # Check for callback-related issues
        if not data.get("playerDropdown"):
            logger.error("❌ CALLBACK ISSUE: playerDropdown is empty - this will cause dropdown_callback errors")
        
        if not data.get("events") and not data.get("formatted_events"):
            logger.error("❌ EVENT LOG ISSUE: No events data - Event Log tab will be empty")
        
        return debug_info
        
    except Exception as e:
        logger.error(f"❌ debug_data_structure() failed: {e}")
        return {"error": str(e)}

def get_safe_data_for_callbacks(data: Dict) -> Dict:
    """Return data structure safe for GUI callbacks with all required fields"""
    try:
        if not data or not isinstance(data, dict):
            return create_minimal_safe_data()
        
        safe_data = data.copy()
        
        # Ensure all required dropdown fields exist
        if not safe_data.get("playerDropdown"):
            safe_data["playerDropdown"] = [{"steamid": "0", "name": "No Players", "display_name": "No Players Found"}]
        
        if not safe_data.get("teamDropdown"):
            safe_data["teamDropdown"] = [{"id": 0, "name": "Unknown", "display_name": "Unknown Team"}]
        
        if not safe_data.get("mapDropdown"):
            safe_data["mapDropdown"] = [{"id": 0, "name": "Unknown", "display_name": "Unknown Map"}]
        
        if not safe_data.get("round_indices"):
            safe_data["round_indices"] = [0]
            safe_data["round_labels"] = ["Round 1"]
        
        # Ensure formatted events exist for Event Log
        if not safe_data.get("formatted_events") and safe_data.get("events"):
            loader = EnhancedFileLoader()
            formatted_events = []
            events = safe_data.get("events", [])
            for i, event in enumerate(events):
                if isinstance(event, dict):
                    formatted_events.append(loader._format_event_for_display(event, i))
            safe_data["formatted_events"] = formatted_events
        
        logger.info(f"✅ Safe data prepared for callbacks with {len(safe_data.get('playerDropdown', []))} players")
        return safe_data
        
    except Exception as e:
        logger.error(f"❌ get_safe_data_for_callbacks() failed: {e}")
        return create_minimal_safe_data()

def create_minimal_safe_data() -> Dict:
    """Create minimal safe data structure when no data is available"""
    return {
        "events": [],
        "formatted_events": [],
        "playerStats": {},
        "playerDropdown": [{"steamid": "0", "name": "No Data", "display_name": "No Data Loaded"}],
        "teamDropdown": [{"id": 0, "name": "Unknown", "display_name": "No Team Data"}],
        "mapDropdown": [{"id": 0, "name": "Unknown", "display_name": "No Map Data"}],
        "weaponDropdown": [],
        "round_indices": [0],
        "round_labels": ["No Rounds"],
        "event_count": 0,
        "has_chat": False,
        "has_rounds": False,
        "has_player_hurt": False,
        "has_weapon_fire": False,
        "has_bullet_impact": False,
        "processing_timestamp": time.time(),
        "loader_version": "0.0031-FIXED-SAFE"
    }


# =============================================================================
# ADDITIONAL UTILITY FUNCTIONS
# =============================================================================

def validate_file_path(file_path: str) -> bool:
    """Validate if a file path exists and is accessible"""
    try:
        return file_path and os.path.exists(file_path) and os.path.isfile(file_path)
    except Exception:
        return False

def get_loader_stats() -> Dict:
    """Get statistics about the global loader instance"""
    try:
        return {
            "last_load_time": _default_loader.last_load_time,
            "last_file_path": _default_loader.last_file_path,
            "config_exe_path": _default_loader.config.exe_path,
            "config_output_dir": _default_loader.config.output_dir,
            "exe_exists": os.path.exists(_default_loader.config.exe_path)
        }
    except Exception as e:
        logger.error(f"❌ get_loader_stats() failed: {e}")
        return {"error": str(e)}

def reset_loader_config(exe_path: Optional[str] = None, output_dir: Optional[str] = None):
    """Reset the global loader configuration"""
    try:
        global _default_loader
        config = ParserConfig()
        
        if exe_path:
            config.exe_path = exe_path
        if output_dir:
            config.output_dir = output_dir
            
        _default_loader = EnhancedFileLoader(config)
        logger.info("✅ Loader configuration reset")
        
    except Exception as e:
        logger.error(f"❌ reset_loader_config() failed: {e}")


# =============================================================================
# EOF — file_loader.py v0.0031-FIXED | TLOC: 1109+
# =============================================================================