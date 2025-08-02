#!/usr/bin/env python3
# =============================================================================
# CS2 Ancient Chinese Secrets – Carmack Edition GUI - IMPROVED VERSION
# Version: Alpha v0.0010-IMPROVED | 
# =============================================================================

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import logging
import re
import json
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime
import traceback
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()



# Configure logging to handle Unicode properly
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('cs2_acs.log', encoding='utf-8')
    ]
)

# CS2-ACS v2 Binary Configuration
CS2_ACS_BINARY = "CS2-ACS-v2.exe"

# Enhanced PIL imports with fallback
try:
    from PIL import Image, ImageTk
    from PIL.Image import Resampling
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("Warning: PIL not available - banner images will be disabled")

# Environment and logging setup
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("Warning: python-dotenv not available")

# Setup logging
logger = logging.getLogger(__name__)

# Dynamic path setup
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
UTILS_DIR = os.path.join(ROOT_DIR, "utils")
ASSET_DIR = os.path.join(ROOT_DIR, "asset")
PEWPEW_DIR = os.path.join(ROOT_DIR, "pewpew")

# Add utils to path
if UTILS_DIR not in sys.path:
    sys.path.insert(0, UTILS_DIR)

# Asset paths
ICON_PATH = os.path.join(ASSET_DIR, "CS2.png")
BANNER_GRAY = os.path.join(ASSET_DIR, "CS2-gray.png")
BANNER_GIF = os.path.join(ASSET_DIR, "CS2-tb-fill.gif")
BANNER_COL = os.path.join(ASSET_DIR, "CS2-col.png")

# Import utilities with better error handling
# =============================================================================
# MAIN.PY IMPORT SECTION - FINAL CORRECTED VERSION
# Replace lines ~88-106 in your main.py with this:
# =============================================================================

# Import utilities with better error handling
def safe_import(module_name, fallback_func=None):
    """Safely import modules with fallback functions"""
    try:
        if module_name == "file_loader":
            from file_loader import load_file
            return load_file
        elif module_name == "utils.dropdown_utils":
            from utils.dropdown_utils import build_player_dropdown
            return build_player_dropdown
        elif module_name == "utils.round_dropdown_utils":
            from utils.round_dropdown_utils import parse_round_dropdown
            from utils.round_dropdown_utils import infer_round_labels
            return parse_round_dropdown
        elif module_name == "utils.steam_utils":
            from utils.steam_utils import to_steam2
            return to_steam2
        elif module_name == "utils.sanitizer_report":
            from utils.sanitizer_report import generate_sanitizer_report
            return generate_sanitizer_report
        elif module_name == "utils.gui.scout_report":
            from utils.gui.scout_report import generate_comprehensive_scout_report
            return generate_comprehensive_scout_report
        elif module_name == "cs2_parser.stats_builder":  # FIXED: Correct path
            from cs2_parser import stats_builder
            return stats_builder
        else:
            module = __import__(module_name)
            return module
    except ImportError as e:
        logger.warning(f"Failed to import {module_name}: {e}")
        return fallback_func

# Load utilities with fallbacks
load_file = safe_import("file_loader", lambda path, **kwargs: {"error": "file_loader not available"})
build_player_dropdown = safe_import("utils.dropdown_utils", lambda data: ([], {}))
parse_round_dropdown = safe_import("utils.round_dropdown_utils", lambda data: [])
to_steam2 = safe_import("utils.steam_utils", lambda steamid: f"STEAM_0:0:{steamid}")
generate_sanitizer_report = safe_import("utils.sanitizer_report", lambda data: print("Sanitizer not available"))
generate_scout_report = safe_import("utils.gui.scout_report", lambda data: {})
stats_builder = safe_import("cs2_parser.stats_builder")  # FIXED: Correct path

# CS2 parser module imports with fallbacks
def create_fallback_tab_func(tab_name):
    def fallback_func(tab_frame, data):
        ttk.Label(
            tab_frame,
            text=f"{tab_name} module not available\nThis feature requires additional dependencies",
            foreground="orange",
            background="black",
            font=("Consolas", 10)
        ).pack(pady=20)
    return fallback_func

# Import CS2 parser modules
try:
    from cs2_parser.chat_summary import generate_chat_summary
except ImportError:
    generate_chat_summary = create_fallback_tab_func("Chat Summary")

try:
    from cs2_parser.stats_summary import display_stats_summary
except ImportError:
    display_stats_summary = create_fallback_tab_func("Stats Summary")

try:
    from cs2_parser.event_log import event_log_tab_controller
except ImportError:
    event_log_tab_controller = create_fallback_tab_func("Event Log")

try:
    from cs2_parser.damage_summary import display_damage_summary
except ImportError:
    display_damage_summary = create_fallback_tab_func("Damage Summary")

class DataManager:
    """Centralized data management with v3.2.1-carmack compatibility"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all data structures"""
        # v3.2.1-carmack format fields
        self.parser_data: Dict = {}
        self.rounds: List[Dict] = []
        self.player_stats: List[Dict] = []
        self.events: List[Dict] = []
        self.metadata: Dict = {}
        self.anti_cheat_data: Dict = {}
        self.chat_data: Dict = {}
        
        # Legacy compatibility fields
        self.loaded_data: Dict = {}
        self.player_data: Dict = {}
        self.round_data: List[Dict] = []
        self.stats_data: Dict = {}
        
        # Status
        self.is_loaded: bool = False
        self.file_path: Optional[str] = None
    
    def load_parser_output(self, json_data: Dict, file_path: str = None):
        """Load and validate v3.2.1-carmack or legacy format data"""
        try:
            self.parser_data = json_data.copy()
            self.file_path = file_path
            self.loaded_data = json_data  # Set loaded_data immediately
            
            # Check if this is v3.2.1-carmack format
            if self._is_carmack_format(json_data):
                logger.info("✅ Processing v3.2.1-carmack format")
                self._load_carmack_format(json_data)
            else:
                logger.info("✅ Processing legacy format")
                self._load_legacy_format(json_data)
            
            self.is_loaded = True
            logger.info(f"✅ Data loaded: {len(self.player_stats)} players, {len(self.rounds)} rounds")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading parser output: {e}")
            return False
    
    def _is_carmack_format(self, data: Dict) -> bool:
        """Check if data is in v3.2.1-carmack format"""
        try:
            # Check for carmack-specific structure
            has_carmack_fields = all(field in data for field in ["rounds", "playerStats"])
            if has_carmack_fields:
                rounds = data.get("rounds", [])
                player_stats = data.get("playerStats", [])
                # Carmack format has arrays, legacy has objects
                return isinstance(rounds, list) and isinstance(player_stats, list)
            return False
        except:
            return False

    def _load_carmack_format(self, data: Dict):
        """Load v3.2.1-carmack format data"""
        try:
            # Extract v3.2.1-carmack fields
            self.rounds = data.get("rounds", [])
            self.player_stats = data.get("playerStats", [])
            self.events = data.get("events", [])
            self.metadata = data.get("metadata", {})
            self.anti_cheat_data = data.get("antiCheatData", {})
            self.chat_data = data.get("chat", {})
            
            # Create legacy compatibility fields
            self._create_legacy_player_data()
            self._create_legacy_round_data()
            self._create_legacy_stats_data()
            
            # Ensure required fields exist in loaded_data
            if "playerDropdown" not in self.loaded_data:
                self.loaded_data["playerDropdown"] = self._build_player_dropdown()
                
        except Exception as e:
            logger.error(f"❌ Error processing carmack format: {e}")
            raise
    
    def _load_legacy_format(self, data: Dict):
        """Load legacy format data"""
        try:
            # Extract using existing methods
            self._extract_player_data()
            self._extract_round_data()
            self._compute_statistics()
        except Exception as e:
            logger.error(f"❌ Error processing legacy format: {e}")
            raise

    def _create_legacy_player_data(self):
        """Create legacy-compatible player data from carmack format"""
        try:
            self.player_data = {}
            for player in self.player_stats:
                steamid = str(player.get("steam_id64", ""))
                self.player_data[steamid] = {
                    "name": player.get("name", "Unknown"),
                    "steamid": steamid,
                    "kills": player.get("kills", 0),
                    "deaths": player.get("deaths", 0),
                    "assists": player.get("assists", 0),
                    "score": player.get("score", 0)
                }
        except Exception as e:
            logger.error(f"❌ Error creating legacy player data: {e}")

    def _create_legacy_round_data(self):
        """Create legacy-compatible round data from carmack format"""
        try:
            self.round_data = []
            for round_info in self.rounds:
                round_number = round_info.get("number", 1)
                winner = round_info.get("winner", "")
                ct_score = round_info.get("ct_score")
                t_score = round_info.get("t_score")
                
                round_label = f"Round {round_number}"
                if winner:
                    round_label += f" ({winner} win)"
                if ct_score is not None and t_score is not None:
                    round_label += f" [{ct_score}-{t_score}]"
                
                self.round_data.append({
                    "number": round_number,
                    "label": round_label,
                    "winner": winner,
                    "ct_score": ct_score,
                    "t_score": t_score
                })
        except Exception as e:
            logger.error(f"❌ Error creating legacy round data: {e}")

    def _create_legacy_stats_data(self):
        """Create legacy-compatible stats data"""
        try:
            self.stats_data = {}
            for player in self.player_stats:
                steamid = str(player.get("steam_id64", ""))
                self.stats_data[steamid] = {
                    "name": player.get("name", "Unknown"),
                    "steamid": steamid,
                    "kills": player.get("kills", 0),
                    "deaths": player.get("deaths", 0),
                    "assists": player.get("assists", 0),
                    "damage": player.get("damage", 0),
                    "kd_ratio": player.get("kd_ratio", 0.0),
                    "adr": player.get("adr", 0.0),
                    "rating": player.get("rating", 0.0)
                }
        except Exception as e:
            logger.error(f"❌ Error creating legacy stats data: {e}")

    def _extract_player_data(self):
        """Extract player data from legacy format"""
        try:
            self.player_data = {}
            events = self.loaded_data.get("events", [])
            
            # Find all unique players from events
            players_found = set()
            for event in events:
                if isinstance(event, dict):
                    for key in ["attacker", "victim", "user", "player"]:
                        player = event.get(key)
                        if isinstance(player, dict) and "steamid" in player:
                            steamid = str(player["steamid"])
                            players_found.add(steamid)
                            if steamid not in self.player_data:
                                self.player_data[steamid] = {
                                    "name": player.get("name", "Unknown"),
                                    "steamid": steamid
                                }
        except Exception as e:
            logger.error(f"Round data extraction failed: {e}")

    def _extract_round_data(self):
        """Extract round data from events"""
        try:
            self.round_data = []
            events = self.loaded_data.get("events", [])
            
            # Simple round extraction - count round events
            round_count = 0
            for event in events:
                if isinstance(event, dict) and "round" in event.get("type", "").lower():
                    round_count += 1
            
            # Create basic round data
            for i in range(max(round_count, 1)):
                self.round_data.append({
                    "number": i + 1,
                    "label": f"Round {i + 1}"
                })
        except Exception as e:
            logger.error(f"Round data extraction failed: {e}")

    def _compute_statistics(self):
        """Basic statistics computation fallback"""
        try:
            events = self.loaded_data.get("events", [])
            player_stats = {}
            
            # Initialize stats for each player
            for steamid, player in self.player_data.items():
                player_stats[steamid] = {
                    "steamid": steamid,
                    "name": player["name"],
                    "kills": 0,
                    "deaths": 0,
                    "assists": 0,
                    "damage": 0,
                    "score": 0,
                    "kd_ratio": 0.0,
                    "adr": 0.0
                }
            
            # Process events
            for event in events:
                if not isinstance(event, dict):
                    continue
                    
                event_type = event.get("type", "")
                
                if "Death" in event_type or event_type == "player_death":
                    attacker = event.get("attacker") or event.get("killer")
                    victim = event.get("victim") or event.get("user")
                    
                    if isinstance(attacker, dict):
                        attacker_id = str(attacker.get("steamid", "0"))
                        if attacker_id in player_stats:
                            player_stats[attacker_id]["kills"] += 1
                    
                    if isinstance(victim, dict):
                        victim_id = str(victim.get("steamid", "0"))
                        if victim_id in player_stats:
                            player_stats[victim_id]["deaths"] += 1
                            
                elif "Damage" in event_type or event_type == "player_hurt":
                    attacker = event.get("attacker") or event.get("user")
                    damage = event.get("damage", 0) or event.get("dmg_health", 0)
                    
                    if isinstance(attacker, dict) and damage:
                        attacker_id = str(attacker.get("steamid", "0"))
                        if attacker_id in player_stats:
                            player_stats[attacker_id]["damage"] += damage
            
            # Calculate derived statistics
            for steamid, stats in player_stats.items():
                kills = stats["kills"]
                deaths = stats["deaths"]
                damage = stats["damage"]
                
                stats["kd_ratio"] = round(kills / deaths, 2) if deaths > 0 else kills
                stats["adr"] = round(damage / max(len(self.round_data), 1), 1)
                stats["score"] = kills * 2 + stats["assists"]
            
            self.stats_data = player_stats
            
        except Exception as e:
            logger.error(f"Basic stats computation failed: {e}")

    def _build_player_dropdown(self):
        """Build player dropdown data"""
        try:
            dropdown_data = []
            for player in self.player_stats:
                name = player.get("name", "Unknown")
                steamid = self._convert_steamid64_to_steam2(player.get("steam_id64"))
                dropdown_data.append(f"{name} ({steamid})")
            return dropdown_data
        except Exception as e:
            logger.error(f"Error building player dropdown: {e}")
            return []

        """Build round labels"""
        try:
            labels = []
            for round_info in self.rounds:
                number = round_info.get("number", 1)
                winner = round_info.get("winner", "")
                label = f"Round {number}"
                if winner:
                    label += f" ({winner})"
                labels.append(label)
            return labels
        except Exception as e:
            logger.error(f"Error building round labels: {e}")
            return []

    def _convert_steamid64_to_steam2(self, steamid64):
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

    # Legacy compatibility methods
    def load_from_dict(self, data: Dict, file_path: str = None):
        """Legacy method - redirect to new load_parser_output"""
        return self.load_parser_output(data, file_path)

class Banner(tk.Label):
    """Enhanced banner with better PIL handling"""
    def __init__(self, parent, gray_path, gif_path, col_path, width, height):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.width = width
        self.height = height
        self.running = False
        self.current_frame = 0
        self._animation_id = None
        
        if PIL_AVAILABLE:
            # Load images with better error handling
            self.gray_tk = self._load_image(gray_path)
            self.col_tk = self._load_image(col_path)
            self.frames = self._load_gif_frames(gif_path)
            
            # Set initial state
            self.config(image=self.gray_tk if self.gray_tk else None)
        else:
            # Fallback text banner
            self.config(
                text="CS2 Ancient Chinese Secrets – Carmack Edition",
                fg="white", bg="black", font=("Arial", 16, "bold"),
                height=3
            )

    def _load_image(self, path: str) -> Optional:
        if not PIL_AVAILABLE:
            return None
        try:
            if not os.path.exists(path):
                logger.warning(f"Image file not found: {path}")
                return None
            img = Image.open(path).resize((self.width, self.height), Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logger.warning(f"Failed to load image: {path} → {e}")
            return None

    def _load_gif_frames(self, gif_path: str) -> List:
        if not PIL_AVAILABLE:
            return []
        try:
            if not os.path.exists(gif_path):
                logger.warning(f"GIF file not found: {gif_path}")
                return []
            
            img = Image.open(gif_path)
            frames = []
            for frame in range(img.n_frames):
                img.seek(frame)
                frame_resized = img.resize((self.width, self.height), Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame_resized))
            return frames
        except Exception as e:
            logger.error(f"Failed to load gif frames from {gif_path}: {e}")
            return []

    def start(self):
        if not PIL_AVAILABLE or not self.frames:
            return
        self.running = True
        self.current_frame = 0
        self._animate()

    def stop(self):
        if not PIL_AVAILABLE:
            return
        self.running = False
        if self._animation_id:
            self.after_cancel(self._animation_id)
            self._animation_id = None
        if self.col_tk:
            self.config(image=self.col_tk)

    def _animate(self):
        if not self.running or not self.frames:
            return
        self.config(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self._animation_id = self.after(100, self._animate)

    def set_variant(self, variant: str = "gray"):
        """Set banner state"""
        if not PIL_AVAILABLE:
            # Update text banner
            text_variants = {
                "gray": "CS2 ACS - Ready",
                "fill": "CS2 ACS - Loading...",
                "green": "CS2 ACS - Data Loaded",
                "red": "CS2 ACS - Error"
            }
            self.config(text=text_variants.get(variant, "CS2 ACS"))
            return
        
        self.stop()
        
        if variant == "gray" and self.gray_tk:
            self.config(image=self.gray_tk)
        elif variant in ["col", "green"] and self.col_tk:
            self.config(image=self.col_tk)
        elif variant == "fill":
            self.start()
        elif variant == "red" and self.gray_tk:
            self.config(image=self.gray_tk)

class CS2ParserApp:
    """Main application class with improved error handling and v2 compatibility"""
    
    def __init__(self, root):
        root.title("CS2 ACS – Carmack Edition Alpha v0.0010")
        root.geometry("1200x800")
        root.configure(bg="black")
        root.minsize(800, 600)
        
        # Set icon if available
        if os.path.isfile(ICON_PATH):
            try:
                if PIL_AVAILABLE:
                    icon = ImageTk.PhotoImage(Image.open(ICON_PATH))
                    root.iconphoto(False, icon)
                else:
                    root.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
            except Exception as e:
                logger.warning(f"Failed to set icon: {e}")
        
        self.root = root
        self.data_manager = DataManager()
        self.loading_thread: Optional[threading.Thread] = None
        
        # GUI Variables
        self.player_var = tk.StringVar()
        self.round_var = tk.StringVar()
        self.status_var = tk.StringVar(value="⚪ Ready")
        
        # Build UI
        self._build_ui()
        logger.info("CS2 ACS Application initialized")

    def _build_ui(self):
        """Build the complete UI"""
        self._setup_styles()
        self._create_banner()
        self._create_menu()
        self._create_tabs()
        self._create_bottom_panel()

    def _setup_styles(self):
        """Configure ttk styles for dark theme"""
        s = ttk.Style()
        s.theme_use("default")
        
        # Configure notebook
        s.configure("TNotebook", background="black", borderwidth=0)
        s.configure("TNotebook.Tab",
                background="#2d2d2d",
                foreground="white",
                padding=(12, 8),
                focuscolor="none")
        s.map("TNotebook.Tab",
            background=[("selected", "#404040"), ("active", "#353535")])
        
        # Configure treeview
        s.configure("Treeview",
                background="#1a1a1a",
                foreground="white",
                fieldbackground="#1a1a1a",
                rowheight=25,
                borderwidth=0)
        s.configure("Treeview.Heading",
                background="#2d2d2d",
                foreground="white",
                relief="flat")
        
        # Configure buttons
        s.configure("TButton",
                background="#2d2d2d",
                foreground="white",
                borderwidth=1,
                focuscolor="none")
        s.map("TButton",
            background=[("active", "#404040")])

    def _create_banner(self):
        """Create banner with fallback"""
        self.banner = Banner(self.root, BANNER_GRAY, BANNER_GIF, BANNER_COL, 1075, 90)
        self.banner.pack(pady=(8, 0), fill="x")

    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root, bg="black", fg="white")
        
        # File menu
        file_menu = tk.Menu(menubar, tearoff=0, bg="black", fg="white")
        file_menu.add_command(label="Open DEM/JSON File", command=self.select_file)
        file_menu.add_separator()
        file_menu.add_command(label="Export Data as JSON", command=self.export_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0, bg="black", fg="white")
        tools_menu.add_command(label="Refresh Stats", command=self.refresh_stats)
        tools_menu.add_command(label="Generate Scout Report", command=self.generate_scout_report)
        tools_menu.add_separator()
        tools_menu.add_command(label="Validate Data", command=self.validate_data)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        
        # Debug menu
        debug_menu = tk.Menu(menubar, tearoff=0, bg="black", fg="white")
        debug_menu.add_command(label="Show Data Structure", command=self.debug_data_structure)
        debug_menu.add_command(label="Export Debug Log", command=self.export_debug_log)
        menubar.add_cascade(label="Debug", menu=debug_menu)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0, bg="black", fg="white")
        help_menu.add_command(label="About", command=self._show_about)
        help_menu.add_command(label="Keyboard Shortcuts", command=self._show_shortcuts)
        menubar.add_cascade(label="Help", menu=help_menu)
        
        self.root.config(menu=menubar)

    def _show_about(self):
        """Show about dialog"""
        about_msg = (
            "CS2 Ancient Chinese Secrets – Carmack Edition\n"
            "Version: Alpha v0.0010-IMPROVED\n"
            "Authors: Athlenia <3, pzr1H\n"
            "Project Start Date: July 1, 2025\n\n"
            "Description:\n"
            "Advanced Counter-Strike 2 demo analysis tool with:\n"
            "• Player statistics and performance metrics\n"
            "• Scout reports and threat assessment\n"
            "• Chat analysis and communication insights\n"
            "• Event timeline and damage tracking\n"
            "• Export capabilities for further analysis\n\n"
            "Supports both legacy and v2 JSON formats."
        )
        messagebox.showinfo("About CS2 ACS", about_msg)
    
    def _show_shortcuts(self):
        """Show keyboard shortcuts"""
        shortcuts_msg = (
            "Keyboard Shortcuts:\n\n"
            "Ctrl+O - Open File\n"
            "Ctrl+S - Export Data\n"
            "Ctrl+R - Refresh Stats\n"
            "F5 - Refresh Current Tab\n"
            "Ctrl+Q - Quit Application\n"
            "F1 - Show Help\n"
            "F12 - Debug Mode"
        )
        messagebox.showinfo("Keyboard Shortcuts", shortcuts_msg)

    def _create_tabs(self):
        """Create notebook tabs with improved organization"""
        main_container = tk.Frame(self.root, bg="black")
        main_container.pack(fill="both", expand=True, padx=8, pady=(12, 0))
        
        self.notebook = ttk.Notebook(main_container)
        self.tabs = {}

        tab_definitions = [
            ("Console", self._setup_console_tab),
            ("Overview", self._setup_overview_tab),
            ("Event Log", self._setup_event_log_tab),
            ("Player Stats", self._setup_stats_tab),
            ("Chat Analysis", self._setup_chat_tab),
            ("Damage Report", self._setup_damage_tab),
            ("Scout Intel", self._setup_scout_tab)
        ]

        for tab_name, setup_func in tab_definitions:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=tab_name)
            self.tabs[tab_name] = frame
            setup_func(frame)

        self.notebook.pack(expand=True, fill="both")
        
        # Bind tab change event
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    def _setup_console_tab(self, frame):
        """Setup console tab"""
        self.console = ScrolledText(
            frame, height=25,
            bg="#0a0a0a", fg="#00ff00", insertbackground="white",
            wrap=tk.WORD, font=("Consolas", 10),
            relief="flat", borderwidth=0
        )
        self.console.pack(expand=True, fill="both", padx=5, pady=5)
        
        # Add welcome message
        self._log("🚀 CS2 Ancient Chinese Secrets - Carmack Edition Started", "cyan")
        self._log("📁 Use File → Open to load a CS2 demo or JSON file", "white")

    def _setup_overview_tab(self, frame):
        """Setup overview tab"""
        # Main overview container
        overview_frame = tk.Frame(frame, bg="black")
        overview_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # File info section
        file_info_frame = tk.LabelFrame(
            overview_frame, text="File Information", 
            fg="cyan", bg="black", font=("Arial", 10, "bold")
        )
        file_info_frame.pack(fill="x", pady=(0, 10))
        
        self.file_info_text = tk.Text(
            file_info_frame, height=4, bg="#1a1a1a", fg="white",
            font=("Consolas", 9), relief="flat"
        )
        self.file_info_text.pack(fill="x", padx=5, pady=5)
        
        # Quick stats section
        stats_frame = tk.LabelFrame(
            overview_frame, text="Quick Statistics", 
            fg="cyan", bg="black", font=("Arial", 10, "bold")
        )
        stats_frame.pack(fill="both", expand=True)
        
        self.stats_text = tk.Text(
            stats_frame, bg="#1a1a1a", fg="white",
            font=("Consolas", 9), relief="flat"
        )
        self.stats_text.pack(fill="both", expand=True, padx=5, pady=5)

    def _setup_event_log_tab(self, frame):
        """Setup event log tab"""
        try:
            event_log_tab_controller(frame, self.data_manager.loaded_data)
        except Exception as e:
            self._create_placeholder_tab(frame, "Event Log", str(e))

    def _setup_stats_tab(self, frame):
        """Setup player stats tab"""
        try:
            display_stats_summary(frame, self.data_manager.loaded_data)
        except Exception as e:
            self._create_placeholder_tab(frame, "Player Stats", str(e))

    def _setup_chat_tab(self, frame):
        """Setup chat analysis tab"""
        try:
            generate_chat_summary(frame, self.data_manager.loaded_data)
        except Exception as e:
            self._create_placeholder_tab(frame, "Chat Analysis", str(e))

    def _setup_damage_tab(self, frame):
        """Setup damage report tab"""
        try:
            display_damage_summary(frame, self.data_manager.loaded_data)
        except Exception as e:
            self._create_placeholder_tab(frame, "Damage Report", str(e))

    def _setup_scout_tab(self, frame):
        """Setup scout intelligence tab"""
        self.scout_frame = frame
        self._create_placeholder_tab(frame, "Scout Intel", "Load a demo file to generate scout reports")

    def _create_placeholder_tab(self, frame, tab_name, message):
        """Create placeholder content for tabs"""
        container = tk.Frame(frame, bg="black")
        container.pack(fill="both", expand=True)
        
        # Icon and message
        icon_label = tk.Label(
            container, text="📊", fg="gray", bg="black", 
            font=("Arial", 48)
        )
        icon_label.pack(pady=(50, 20))
        
        title_label = tk.Label(
            container, text=f"{tab_name}", fg="white", bg="black",
            font=("Arial", 16, "bold")
        )
        title_label.pack(pady=(0, 10))
        
        message_label = tk.Label(
            container, text=message, fg="gray", bg="black",
            font=("Arial", 10), wraplength=400, justify="center"
        )
        message_label.pack(pady=(0, 20))

    def _create_bottom_panel(self):
        """Create enhanced bottom control panel"""
        bottom_frame = tk.Frame(self.root, bg="#1a1a1a", relief="raised", bd=1)
        bottom_frame.pack(side="bottom", fill="x")
        
        # Configure grid
        for i in range(6):
            bottom_frame.grid_columnconfigure(i, weight=1)
        
        # Status indicator
        status_frame = tk.Frame(bottom_frame, bg="#1a1a1a")
        status_frame.grid(row=0, column=0, sticky="w", padx=10, pady=8)
        
        self.status_label = tk.Label(
            status_frame, textvariable=self.status_var,
            fg="lime", bg="#1a1a1a", font=("Arial", 9, "bold")
        )
        self.status_label.pack()
        
        # Player selection
        player_frame = tk.LabelFrame(
            bottom_frame, text="Player Filter",
            fg="white", bg="#1a1a1a", font=("Arial", 8)
        )
        player_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.player_combo = ttk.Combobox(
            player_frame, textvariable=self.player_var,
            state="readonly", width=20
        )
        self.player_combo.pack(fill="x", padx=5, pady=2)
        
        # Round selection
        round_frame = tk.LabelFrame(
            bottom_frame, text="Round Filter",
            fg="white", bg="#1a1a1a", font=("Arial", 8)
        )
        round_frame.grid(row=0, column=2, padx=5, pady=5, sticky="ew")
        
        self.round_combo = ttk.Combobox(
            round_frame, textvariable=self.round_var,
            state="readonly", width=15
        )
        self.round_combo.pack(fill="x", padx=5, pady=2)
        
        # Control buttons
        button_frame = tk.Frame(bottom_frame, bg="#1a1a1a")
        button_frame.grid(row=0, column=3, padx=10, pady=5, sticky="e")
        
        self.refresh_btn = ttk.Button(
            button_frame, text="🔄 Refresh",
            command=self.refresh_stats, state="disabled"
        )
        self.refresh_btn.pack(side="left", padx=2)
        
        self.export_btn = ttk.Button(
            button_frame, text="💾 Export",
            command=self.export_data, state="disabled"
        )
        self.export_btn.pack(side="left", padx=2)
        
        # Progress bar (initially hidden)
        self.progress_bar = ttk.Progressbar(
            bottom_frame, mode='indeterminate', length=200
        )
        
        # File info
        self.file_info_label = tk.Label(
            bottom_frame, text="No file loaded",
            fg="gray", bg="#1a1a1a", font=("Arial", 8)
        )
        self.file_info_label.grid(row=0, column=4, padx=10, pady=8, sticky="e")

    def _on_tab_changed(self, event):
        """Handle tab change events"""
        try:
            selected_tab = self.notebook.tab(self.notebook.select(), "text")
            self._log(f"📋 Switched to {selected_tab} tab", "blue")
        except Exception as e:
            logger.debug(f"Tab change event failed: {e}")

    def _log(self, message: str, color: str = "white"):
        """Thread-safe logging to console with timestamps"""
        def _do_log():
            try:
                timestamp = datetime.now().strftime("%H:%M:%S")
                full_message = f"[{timestamp}] {message}\n"
                
                self.console.insert(tk.END, full_message)
                
                # Apply color
                if color != "white":
                    line_start = f"end-{len(full_message)}c"
                    self.console.tag_config(color, foreground=color)
                    self.console.tag_add(color, line_start, "end-1c")
                
                self.console.see(tk.END)
                self.root.update_idletasks()
                
                # Also log to file
                clean_message = self._clean_message_for_logging(message)
                logger.info(clean_message)
                
            except Exception as e:
                logger.error(f"Console logging failed: {e}")
        
        if threading.current_thread() == threading.main_thread():
            _do_log()
        else:
            self.root.after(0, _do_log)

    def _clean_message_for_logging(self, message: str) -> str:
        """Remove emojis and special Unicode characters for logging"""
        try:
            # Replace common emojis with text equivalents
            emoji_replacements = {
                '🚀': '[ROCKET]',
                '📁': '[FOLDER]',
                '📂': '[OPEN_FOLDER]',
                '📋': '[CLIPBOARD]',
                '⚠️': '[WARNING]',
                '❌': '[ERROR]',
                '✅': '[SUCCESS]',
                '🔄': '[LOADING]',
                '💬': '[CHAT]',
                '⚔️': '[DAMAGE]',
                '🧩': '[PUZZLE]',
                '📦': '[PACKAGE]',
                '🕵️': '[DETECTIVE]',
                '🔍': '[SEARCH]',
                '🎯': '[TARGET]',
                '📊': '[CHART]',
                '🛡️': '[SHIELD]',
                '🔧': '[WRENCH]',
                '💾': '[SAVE]',
                '🎬': '[MOVIE]',
                '🗺️': '[MAP]',
                '🔥': '[FIRE]',
                '📈': '[GRAPH]',
                '🎮': '[GAME]'
            }
            
            clean_message = message
            for emoji, replacement in emoji_replacements.items():
                clean_message = clean_message.replace(emoji, replacement)
            
            # Remove any remaining non-ASCII characters
            clean_message = clean_message.encode('ascii', 'ignore').decode('ascii')
            
            return clean_message
            
        except Exception:
            # Fallback: return ASCII-only version
            return message.encode('ascii', 'ignore').decode('ascii')

    def select_file(self):
        """Enhanced file selection with v2 format support"""
        file_path = filedialog.askopenfilename(
            title="Select CS2 Demo or JSON File",
            filetypes=[
                ("All supported", "*.dem *.json"),
                ("CS2 Demo files", "*.dem"),
                ("JSON files", "*.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        # Prevent multiple concurrent loads
        if self.loading_thread and self.loading_thread.is_alive():
            self._log("⚠️ File loading already in progress...", "yellow")
            return
        
        self._start_file_loading(file_path)

    def _start_file_loading(self, file_path: str):
        """Start file loading with improved progress indication"""
        self._log(f"📂 Loading file: {os.path.basename(file_path)}", "blue")
        
        # Update UI state
        self.banner.set_variant("fill")
        self._update_status("🔄 Loading file...")
        self._show_progress(True)
        
        # Disable controls
        self.refresh_btn.config(state="disabled")
        self.export_btn.config(state="disabled")
        
        # Reset data
        self.data_manager.reset()
        self._clear_dropdowns()
        
        # Update file info
        self.file_info_label.config(text=f"Loading: {os.path.basename(file_path)}")
        
        # Start loading thread
        self.loading_thread = threading.Thread(target=self._threaded_load, args=(file_path,))
        self.loading_thread.daemon = True
        self.loading_thread.start()

    def _threaded_load(self, file_path: str):
        """Load file in separate thread - updated for v3.2.1-carmack"""
        try:
            # Load file with progress callbacks
            if file_path.lower().endswith('.json'):
                # Direct JSON loading
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._log("✅ JSON file loaded directly", "green")
            else:
                # Use file_loader for .dem files - this will call CS2-ACS-v2.exe
                self._log("🎬 Parsing demo file with CS2-ACS-v2.exe...", "cyan")
                data = load_file(file_path)
            
            # NEW (flexible validation):
            if data is None:
                raise ValueError("Failed to load any data from file")
            # Allow empty players/rounds but log warnings
            player_data = self.data_manager.player_data
            round_data = self.data_manager.round_data
            if len(player_data) == 0:
                logging.warning("⚠️ No players found in data")
            round_data = self.data_manager.round_data
            if len(round_data) == 0:
                logging.warning("⚠️ No round data found")
                logging.warning("⚠️ No rounds found in data")            
            # Validate data structure
            self._log("🔍 Validating data structure...", "cyan")
            if not self._validate_data_structure_v3(data):
                self._log("⚠️ Data structure validation warnings (continuing anyway)", "orange")
            
            self.root.after(0, lambda: self._on_load_success_v3(data, file_path))
            
        except Exception as e:
            error_msg = f"Failed to load file: {str(e)}"
            logger.error(f"{error_msg}\n{traceback.format_exc()}")
            self.root.after(0, lambda: self._on_load_error(error_msg))

    def _validate_data_structure_v3(self, data: Dict) -> bool:
        """Validate loaded data structure for v3.2.1-carmack format"""
        try:
            warnings = []
            
            # Check for v3.2.1-carmack required fields
            required_fields = ["parser_version", "rounds", "playerStats", "events"]
            for field in required_fields:
                if field not in data:
                    warnings.append(f"Missing v3.2.1-carmack field: {field}")
            
            # Check parser version
            parser_version = data.get("parser_version", "")
            if parser_version and "carmack" not in parser_version.lower():
                warnings.append(f"Unexpected parser version: {parser_version}")
            
            # Check rounds structure (should be array)
            rounds = data.get("rounds", [])
            if not isinstance(rounds, list):
                warnings.append("Rounds field is not an array")
            elif rounds:
                sample_round = rounds[0]
                required_round_fields = ["number", "start_tick", "end_tick", "winner"]
                for field in required_round_fields:
                    if field not in sample_round:
                        warnings.append(f"Round missing field: {field}")
            
            # Check playerStats structure (should be array)
            player_stats = data.get("playerStats", [])
            if not isinstance(player_stats, list):
                warnings.append("PlayerStats field is not an array")
            elif player_stats:
                sample_player = player_stats[0]
                required_player_fields = ["steam_id64", "name", "kills", "deaths"]
                for field in required_player_fields:
                    if field not in sample_player:
                        warnings.append(f"Player missing field: {field}")
            
            # Check events structure
            events = data.get("events", [])
            if not isinstance(events, list):
                warnings.append("Events field is not an array")
            elif events:
                sample_event = events[0]
                if not isinstance(sample_event, dict) or "type" not in sample_event:
                    warnings.append("Events are not in expected format")
            
            # Log warnings
            for warning in warnings:
                self._log(f"⚠️ Validation: {warning}", "orange")
            
            return len(warnings) == 0
            
        except Exception as e:
            self._log(f"⚠️ Data validation failed: {e}", "orange")
            return False

    def _on_load_success_v3(self, data: Dict, file_path: str):
        """Handle successful file loading - updated for v3.2.1-carmack"""
        try:
            self._log("✅ File loaded successfully", "green")
            
            # Load data into manager using new method
            success = self.data_manager.load_parser_output(data, file_path)
            if not success:
                self._on_load_error("Failed to process v3.2.1-carmack data")
                return
            
            # Update UI
            self._update_dropdowns()
            self._populate_all_tabs()
            self._update_overview_tab()
            
            # Update UI state
            self.banner.set_variant("green")
            self._update_status("✅ Ready")
            self._show_progress(False)
            
            # Enable controls
            self.refresh_btn.config(state="normal")
            self.export_btn.config(state="normal")
            
            # Update file info
            filename = os.path.basename(file_path)
            self.file_info_label.config(text=f"Loaded: {filename}")
            
            # Log summary with v3.2.1-carmack specific info
            player_count = len(self.data_manager.player_stats)
            round_count = len(self.data_manager.rounds)
            event_count = len(self.data_manager.events)
            parser_version = data.get("parser_version", "unknown")
            
            self._log(f"📊 Summary: {player_count} players, {round_count} rounds, {event_count} events", "green")
            self._log(f"🔧 Parser: {parser_version}", "cyan")
            
            # Check for anti-cheat data
            if self.data_manager.anti_cheat_data:
                anticheat_keys = list(self.data_manager.anti_cheat_data.keys())
                self._log(f"🛡️ Anti-cheat data available: {', '.join(anticheat_keys)}", "cyan")
            
            # Check for chat data
            if self.data_manager.chat_data and self.data_manager.chat_data.get("messages"):
                chat_count = len(self.data_manager.chat_data["messages"])
                self._log(f"💬 Chat messages: {chat_count}", "cyan")
                
        except Exception as e:
            self._on_load_error(f"Post-processing failed: {e}")

    def _on_load_error(self, error_msg: str):
        """Handle file loading errors"""
        self._log(f"❌ {error_msg}", "red")
        self.banner.set_variant("red")
        self._update_status("❌ Load failed")
        self._show_progress(False)
        self.file_info_label.config(text="Load failed")

    def _update_status(self, status: str):
        """Update status with color coding"""
        self.status_var.set(status)
        if "Error" in status or "❌" in status:
            self.status_label.config(fg="red")
        elif "Loading" in status or "🔄" in status:
            self.status_label.config(fg="yellow")
        else:
            self.status_label.config(fg="lime")

    def _show_progress(self, show: bool):
        """Show/hide progress bar"""
        if show:
            self.progress_bar.grid(row=0, column=5, padx=10, pady=5, sticky="e")
            self.progress_bar.start()
        else:
            self.progress_bar.stop()
            self.progress_bar.grid_remove()

    def _update_dropdowns(self):
        """Update dropdown menus with loaded data"""
        try:
            # Player dropdown
            player_stats = self.data_manager.player_stats
            if player_stats:
                player_names = [
                    f"{p.get('name', 'Unknown')} ({self.data_manager._convert_steamid64_to_steam2(p.get('steam_id64'))})"
                    for p in player_stats
                ]
                self.player_combo['values'] = ["All Players"] + player_names
                self.player_var.set("All Players")
            else:
                self.player_combo['values'] = ["No players found"]
                self.player_var.set("No players found")
            
            # Round dropdown
            rounds = self.data_manager.rounds
            if rounds:
                round_labels = []
                for r in rounds:
                    label = f"Round {r.get('number', 1)}"
                    if r.get('winner'):
                        label += f" ({r['winner']} win)"
                    ct = r.get('ct_score')
                    t = r.get('t_score')
                    if ct is not None and t is not None:
                        label += f" [{ct}-{t}]"
                    round_labels.append(label)
                self.round_combo['values'] = ["All Rounds"] + round_labels
                self.round_var.set("All Rounds")
            else:
                self.round_combo['values'] = ["No rounds found"]
                self.round_var.set("No rounds found")
            
            self._log("✅ Dropdowns updated", "green")
            
        except Exception as e:
            self._log(f"⚠️ Dropdown update failed: {e}", "orange")

    def _clear_dropdowns(self):
        """Clear dropdown selections"""
        self.player_combo['values'] = ["Loading..."]
        self.round_combo['values'] = ["Loading..."]
        self.player_var.set("Loading...")
        self.round_var.set("Loading...")

    def _populate_all_tabs(self):
        """Populate all tabs with loaded data"""
        try:
            self._log("📋 Populating tabs with data...", "cyan")
            
            # Skip console and overview tabs as they're handled separately
            tab_functions = {
                "Event Log": lambda: event_log_tab_controller(self.tabs["Event Log"], self.data_manager.loaded_data),
                "Player Stats": lambda: display_stats_summary(self.tabs["Player Stats"], self.data_manager.loaded_data),
                "Chat Analysis": lambda: generate_chat_summary(self.tabs["Chat Analysis"], self.data_manager.loaded_data),
                "Damage Report": lambda: display_damage_summary(self.tabs["Damage Report"], self.data_manager.loaded_data),
                "Scout Intel": self._populate_scout_tab
            }
            
            for tab_name, populate_func in tab_functions.items():
                try:
                    populate_func()
                    self._log(f"✅ {tab_name} tab populated", "green")
                except Exception as e:
                    self._log(f"⚠️ {tab_name} tab failed: {e}", "orange")
                    self._create_placeholder_tab(self.tabs[tab_name], tab_name, f"Error: {str(e)}")
                    
        except Exception as e:
            self._log(f"❌ Tab population failed: {e}", "red")

    def _update_overview_tab(self):
        """Update overview tab with file and statistics information"""
        try:
            # File information
            file_info = []
            if self.data_manager.file_path:
                file_info.append(f"File: {os.path.basename(self.data_manager.file_path)}")
                file_info.append(f"Size: {os.path.getsize(self.data_manager.file_path):,} bytes")
                file_info.append(f"Modified: {datetime.fromtimestamp(os.path.getmtime(self.data_manager.file_path))}")
            
            self.file_info_text.config(state="normal")
            self.file_info_text.delete(1.0, tk.END)
            self.file_info_text.insert(1.0, "\n".join(file_info))
            self.file_info_text.config(state="disabled")
            
            # Statistics
            stats_info = []
            stats_info.append(f"Players: {len(self.data_manager.player_data)}")
            stats_info.append(f"Rounds: {len(self.data_manager.round_data)}")
            stats_info.append(f"Events: {len(self.data_manager.loaded_data.get('events', []))}")
            
            if self.data_manager.stats_data:
                # Add top performers
                sorted_players = sorted(
                    self.data_manager.stats_data.values(),
                    key=lambda x: x.get('kills', 0),
                    reverse=True
                )
                
                if sorted_players:
                    stats_info.append("\nTop Fraggers:")
                    for i, player in enumerate(sorted_players[:5]):
                        stats_info.append(f"  {i+1}. {player['name']}: {player['kills']} kills")
            
            self.stats_text.config(state="normal")
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(1.0, "\n".join(stats_info))
            self.stats_text.config(state="disabled")
            
        except Exception as e:
            logger.error(f"Overview update failed: {e}")

    def _populate_scout_tab(self):
        """Populate scout intelligence tab"""
        try:
            if not self.data_manager.is_loaded:
                return
            
            # Clear existing content
            for widget in self.scout_frame.winfo_children():
                widget.destroy()
            
            # Generate scout report
            scout_data = generate_scout_report(self.data_manager.loaded_data)
            if not scout_data:
                self._create_placeholder_tab(self.scout_frame, "Scout Intel", "No scout data available")
                return
            
            # Create scout report display
            self._display_scout_report(scout_data)
            
        except Exception as e:
            self._log(f"❌ Scout tab population failed: {e}", "red")
            self._create_placeholder_tab(self.scout_frame, "Scout Intel", f"Error: {str(e)}")

    def _display_scout_report(self, scout_data: Dict):
        """Display scout report in organized format"""
        try:
            # Create main container with scrollbar
            main_frame = tk.Frame(self.scout_frame, bg="black")
            main_frame.pack(fill="both", expand=True)
            
            canvas = tk.Canvas(main_frame, bg="black", highlightthickness=0)
            scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
            scrollable_frame = tk.Frame(canvas, bg="black")
            
            scrollable_frame.bind(
                "<Configure>",
                lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
            )
            
            canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
            canvas.configure(yscrollcommand=scrollbar.set)
            
            canvas.pack(side="left", fill="both", expand=True)
            scrollbar.pack(side="right", fill="y")
            
            # Add scout report content
            title_label = tk.Label(
                scrollable_frame, text="🕵️ PLAYER INTELLIGENCE REPORT",
                fg="cyan", bg="black", font=("Arial", 14, "bold")
            )
            title_label.pack(pady=(10, 20))
            
            # Display each player's scout data
            for i, (steamid, player_data) in enumerate(scout_data.items()):
                self._create_player_scout_card(scrollable_frame, player_data, i)
            
            # Bind mousewheel to canvas
            def _on_mousewheel(event):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            canvas.bind_all("<MouseWheel>", _on_mousewheel)
            
        except Exception as e:
            self._log(f"❌ Scout display failed: {e}", "red")

    def _create_player_scout_card(self, parent, player_data: Dict, index: int):
        """Create individual player scout card"""
        try:
            # Main card frame
            card_frame = tk.LabelFrame(
                parent,
                text=f"Player {index + 1}: {player_data.get('name', 'Unknown')}",
                fg="white", bg="black", font=("Arial", 11, "bold"),
                relief="solid", bd=1
            )
            card_frame.pack(fill="x", padx=10, pady=5)
            
            # Create two-column layout
            content_frame = tk.Frame(card_frame, bg="black")
            content_frame.pack(fill="x", padx=10, pady=10)
            
            left_frame = tk.Frame(content_frame, bg="black")
            left_frame.pack(side="left", fill="both", expand=True)
            
            right_frame = tk.Frame(content_frame, bg="black")
            right_frame.pack(side="right", fill="both", expand=True)
            
            # Left column - Performance metrics
            perf_data = [
                ("Kills", player_data.get("kills", 0)),
                ("Deaths", player_data.get("deaths", 0)),
                ("K/D Ratio", f"{player_data.get('kd_ratio', 0.0):.2f}"),
                ("ADR", f"{player_data.get('adr', 0.0):.1f}"),
                ("Rating", f"{player_data.get('rating', 0.0):.2f}")
            ]
            
            tk.Label(left_frame, text="Performance Metrics", fg="yellow", bg="black", font=("Arial", 9, "bold")).pack(anchor="w")
            for label, value in perf_data:
                row = tk.Frame(left_frame, bg="black")
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"{label}:", fg="gray", bg="black", width=10, anchor="w").pack(side="left")
                tk.Label(row, text=str(value), fg="white", bg="black", anchor="w").pack(side="left")
            
            # Right column - Intelligence data
            intel_data = [
                ("Threat Level", player_data.get("threat_level", "Unknown")),
                ("Experience", player_data.get("experience_level", "Unknown")),
                ("Playstyle", player_data.get("playstyle", "Unknown")),
                ("Team", player_data.get("team", "Unknown")),
                ("Steam ID", player_data.get("steamid", "Unknown"))
            ]
            
            tk.Label(right_frame, text="Intelligence Profile", fg="yellow", bg="black", font=("Arial", 9, "bold")).pack(anchor="w")
            for label, value in intel_data:
                row = tk.Frame(right_frame, bg="black")
                row.pack(fill="x", pady=1)
                tk.Label(row, text=f"{label}:", fg="gray", bg="black", width=12, anchor="w").pack(side="left")
                tk.Label(row, text=str(value), fg="white", bg="black", anchor="w").pack(side="left")
                
        except Exception as e:
            self._log(f"❌ Player card creation failed: {e}", "red")

    # Utility methods
    def refresh_stats(self):
        """Refresh statistics computation"""
        try:
            if not self.data_manager.is_loaded:
                self._log("⚠️ No data loaded to refresh", "yellow")
                return
            
            self._log("🔄 Refreshing statistics...", "cyan")
            self.data_manager._compute_statistics()
            self._populate_all_tabs()
            self._update_overview_tab()
            self._log("✅ Statistics refreshed", "green")
            
        except Exception as e:
            self._log(f"❌ Stats refresh failed: {e}", "red")

    def export_data(self):
        """Export processed data to JSON"""
        try:
            if not self.data_manager.is_loaded:
                self._log("⚠️ No data to export", "yellow")
                return
            
            export_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")],
                title="Export CS2 Data"
            )
            
            if export_path:
                # Prepare export data
                export_data = {
                    "metadata": {
                        "export_version": "1.0",
                        "export_timestamp": datetime.now().isoformat(),
                        "source_file": self.data_manager.file_path,
                        "cs2_acs_version": "v0.0010"
                    },
                    "raw_data": self.data_manager.loaded_data,
                    "processed_data": {
                        "players": self.data_manager.player_data,
                        "rounds": self.data_manager.round_data,
                        "statistics": self.data_manager.stats_data
                    }
                }
                
                with open(export_path, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, default=str, ensure_ascii=False)
                
                self._log(f"✅ Data exported to: {os.path.basename(export_path)}", "green")
                
        except Exception as e:
            self._log(f"❌ Export failed: {e}", "red")

    def generate_scout_report(self):
        """Manually trigger scout report generation"""
        try:
            if not self.data_manager.is_loaded:
                self._log("⚠️ No data loaded for scout report", "yellow")
                return
            
            self._log("🕵️ Generating scout report...", "cyan")
            self._populate_scout_tab()
            
            # Switch to scout tab
            for i in range(self.notebook.index("end")):
                if self.notebook.tab(i, "text") == "Scout Intel":
                    self.notebook.select(i)
                    break
            
        except Exception as e:
            self._log(f"❌ Scout report generation failed: {e}", "red")

    def validate_data(self):
        """Validate current data structure"""
        try:
            if not self.data_manager.is_loaded:
                self._log("⚠️ No data loaded to validate", "yellow")
                return
            
            self._log("🔍 Validating data structure...", "cyan")
            is_valid = self._validate_data_structure_v3(self.data_manager.loaded_data)
            
            if is_valid:
                self._log("✅ Data structure validation passed", "green")
            else:
                self._log("⚠️ Data structure validation found issues", "orange")
                
        except Exception as e:
            self._log(f"❌ Data validation failed: {e}", "red")

    def debug_data_structure(self):
        """Show debug information about data structure"""
        try:
            if not self.data_manager.is_loaded:
                self._log("⚠️ No data loaded for debugging", "yellow")
                return
            
            self._log("🔍 DEBUG: Data structure analysis", "cyan")
            
            data = self.data_manager.loaded_data
            self._log(f"Main keys: {list(data.keys())}", "white")
            
            if "events" in data:
                events = data["events"]
                self._log(f"Events count: {len(events)}", "white")
                if events:
                    sample_event = events[0]
                    self._log(f"Sample event keys: {list(sample_event.keys()) if isinstance(sample_event, dict) else 'Not dict'}", "white")
            
            self._log(f"Players: {len(self.data_manager.player_data)}", "white")
            self._log(f"Rounds: {len(self.data_manager.round_data)}", "white")
            self._log(f"Stats: {len(self.data_manager.stats_data)}", "white")
            
        except Exception as e:
            self._log(f"❌ Debug failed: {e}", "red")

    def export_debug_log(self):
        """Export debug log to file"""
        try:
            export_path = filedialog.asksaveasfilename(
                defaultextension=".log",
                filetypes=[("Log files", "*.log"), ("Text files", "*.txt"), ("All files", "*.*")],
                title="Export Debug Log"
            )
            
            if export_path:
                log_content = self.console.get(1.0, tk.END)
                with open(export_path, 'w', encoding='utf-8') as f:
                    f.write(f"CS2 ACS Debug Log\n")
                    f.write(f"Generated: {datetime.now().isoformat()}\n")
                    f.write("="*50 + "\n\n")
                    f.write(log_content)
                
                self._log(f"✅ Debug log exported to: {os.path.basename(export_path)}", "green")
                
        except Exception as e:
            self._log(f"❌ Debug log export failed: {e}", "red")

def main():
    """Application entry point with error handling"""
    try:
        # Setup root window
        root = tk.Tk()
        
        # Handle high DPI displays
        try:
            root.tk.call('tk', 'scaling', 1.2)
        except:
            pass
        
        # Create and run application
        app = CS2ParserApp(root)
        
        # Bind keyboard shortcuts
        root.bind('<Control-o>', lambda e: app.select_file())
        root.bind('<Control-s>', lambda e: app.export_data())
        root.bind('<Control-r>', lambda e: app.refresh_stats())
        root.bind('<F5>', lambda e: app.refresh_stats())
        root.bind('<Control-q>', lambda e: root.quit())
        root.bind('<F1>', lambda e: app._show_about())
        root.bind('<F12>', lambda e: app.debug_data_structure())
        
        # Start main loop
        root.mainloop()
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        messagebox.showerror("Startup Error", f"Failed to start CS2 ACS:\n{str(e)}")

if __name__ == "__main__":
    main()
