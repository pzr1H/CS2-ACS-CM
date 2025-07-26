#!/usr/bin/env python3
# =============================================================================
# file_loader.py — CS2 ACS Data Loader (v0.0030-ENHANCED)
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
            # Step 1: Sanitize metadata
            data = sanitize_metadata(raw_data)
            
            # Step 2: Reconcile scoreboard
            data = reconcile_final_scoreboard(data)
            
            # Step 3: Ensure dropdown data exists
            data = self._ensure_dropdown_data(data)
            
            # Step 4: Extract round information
            self._extract_round_info(data)
            
            # Step 5: Enrich with metadata
            self._enrich_metadata(data)
            
            # Step 6: Inject fallback stats if needed
            self._inject_fallback_stats(data)
            
            # Step 7: Inject scout stats
            self._inject_scout_stats(data)
            
            # Step 8: Validate final data
            self._validate_processed_data(data)
            
            # Step 9: Enforce schema safety
            data = enforce_schema_safety(data)
            
            return data
            
        except Exception as e:
            logger.error(f"❌ Data processing error: {e}")
            # Return minimal safe data structure
            return self._create_fallback_data(raw_data)
    
    def _ensure_dropdown_data(self, data: Dict) -> Dict:
        """Ensure all dropdown menus have populated data"""
        try:
            # Ensure playerDropdown exists and is populated
            if not data.get("playerDropdown"):
                logger.info("🔍 Extracting player dropdown data from events")
                data["playerDropdown"] = self._extract_players_from_events(data.get("events", []))
            
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
    
    def _extract_players_from_events(self, events: List[Dict]) -> List[Dict]:
        """Extract player information from events with enhanced validation"""
        found_players = {}
        
        try:
            for event in events:
                if event.get("type") != "events.GenericGameEvent":
                    continue
                
                event_string = event.get("details", {}).get("string", "")
                match = self.PLAYER_INFO_RE.search(event_string)
                
                if match:
                    sid_hex, name = match.groups()
                    try:
                        sid64 = str(int(sid_hex, 16))
                        steam2 = to_steam2(int(sid64))
                        
                        # Validate and clean player name
                        clean_name = self._clean_player_name(name)
                        
                        found_players[steam2] = {
                            "steamid": sid64,
                            "steam2": steam2,
                            "name": clean_name,
                            "display_name": clean_name
                        }
                    except (ValueError, TypeError) as e:
                        logger.warning(f"⚠️ Skipping invalid SteamID {sid_hex}: {e}")
            
            players_list = list(found_players.values())
            logger.info(f"✅ Extracted {len(players_list)} players from events")
            return players_list
            
        except Exception as e:
            logger.error(f"❌ Error extracting players from events: {e}")
            return []
    
    def _create_team_dropdown(self, data: Dict) -> List[Dict]:
        """Create team dropdown data"""
        try:
            teams = set()
            
            # Extract teams from player stats
            player_stats = data.get("playerStats", {})
            for stats in player_stats.values():
                team = stats.get("team")
                if team:
                    teams.add(team)
            
            # Extract teams from events
            events = data.get("events", [])
            for event in events:
                if hasattr(event, 'team'):
                    teams.add(event.team)
            
            # Create dropdown structure
            team_dropdown = []
            for i, team in enumerate(sorted(teams)):
                team_dropdown.append({
                    "id": i,
                    "name": team,
                    "display_name": f"Team {team}"
                })
            
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
                if event.get("type") == "events.WeaponFire":
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
        if not name:
            return "Unknown Player"
        
        # Remove non-printable characters
        cleaned = ''.join(char for char in name if char.isprintable())
        
        # Limit length
        if len(cleaned) > 32:
            cleaned = cleaned[:32] + "..."
        
        return cleaned or "Unknown Player"
    
    def _extract_round_info(self, data: Dict):
        """Extract round indices and create round labels"""
        try:
            events = data.get("events", [])
            rounds = {}
            
            for event in events:
                round_num = event.get("round", -1)
                if round_num >= 0:
                    rounds.setdefault(round_num, 0)
                    if event.get("type") == "events.RoundEnd":
                        rounds[round_num] += 1
            
            data["round_indices"] = sorted(rounds.keys())
            data["round_labels"] = [f"Round {r+1}" for r in data["round_indices"]]
            
            logger.info(f"✅ Extracted {len(data['round_indices'])} rounds")
            
        except Exception as e:
            logger.error(f"❌ Error extracting round info: {e}")
            data["round_indices"] = []
            data["round_labels"] = []
    
    def _enrich_metadata(self, data: Dict):
        """Add comprehensive metadata about the match"""
        try:
            events = data.get("events", [])
            data["event_count"] = len(events)
            data["has_chat"] = any(ev.get("type") == "events.ChatMessage" for ev in events)
            data["has_rounds"] = any(ev.get("round", -1) >= 0 for ev in events)
            data["has_player_hurt"] = any(ev.get("type") == "events.PlayerHurt" for ev in events)
            data["has_weapon_fire"] = any(ev.get("type") == "events.WeaponFire" for ev in events)
            data["has_bullet_impact"] = any(ev.get("type") == "events.BulletImpact" for ev in events)
            
            # Add processing metadata
            data["processing_timestamp"] = time.time()
            data["loader_version"] = "0.0030-ENHANCED"
            
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
            # Validate player stats
            player_stats = data.get("playerStats", {})
            if not player_stats:
                logger.warning("⚠️ No playerStats after processing")
                return
            
            for sid, stats in player_stats.items():
                missing_fields = []
                for field in ["kills", "adr", "hs_percent"]:
                    if field not in stats:
                        missing_fields.append(field)
                
                if missing_fields:
                    logger.warning(f"⚠️ Player {sid} missing fields: {missing_fields}")
            
            # Validate dropdown data
            required_dropdowns = ["playerDropdown", "teamDropdown", "mapDropdown"]
            for dropdown in required_dropdowns:
                if not data.get(dropdown):
                    logger.warning(f"⚠️ Missing {dropdown} data")
            
        except Exception as e:
            logger.error(f"❌ Error validating processed data: {e}")
    
    def _create_fallback_data(self, raw_data: Dict) -> Dict:
        """Create minimal fallback data structure when processing fails"""
        try:
            return {
                "events": raw_data.get("events", []),
                "playerStats": raw_data.get("playerStats", {}),
                "playerDropdown": [],
                "teamDropdown": [],
                "mapDropdown": [],
                "weaponDropdown": [],
                "round_indices": [],
                "round_labels": [],
                "event_count": len(raw_data.get("events", [])),
                "has_chat": False,
                "has_rounds": False,
                "has_player_hurt": False,
                "has_weapon_fire": False,
                "has_bullet_impact": False,
                "processing_timestamp": time.time(),
                "loader_version": "0.0030-ENHANCED-FALLBACK"
            }
        except Exception:
            return {"error": "Failed to create fallback data structure"}


# =============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Global loader instance
_default_loader = EnhancedFileLoader()

def load_and_prepare() -> Optional[Dict]:
    """Legacy function: Show file dialog and load selected file"""
    result = _default_loader.load_file_with_dialog()
    return result.data if result.success else None

def load_file(file_path: str, console_callback: Optional[callable] = None) -> Optional[Dict]:
    """Legacy function: Load file with optional console callback"""
    result = _default_loader.load_file(file_path, console_callback)
    return result.data if result.success else None

def inject_scout_stats(data: Dict):
    """Legacy function: Inject scout stats into data"""
    _default_loader._inject_scout_stats(data)


# =============================================================================
# EOF — file_loader.py v0.0030-ENHANCED | TLOC: 676+
# =============================================================================