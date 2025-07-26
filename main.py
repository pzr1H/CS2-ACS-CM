#!/usr/bin/env python3
# =============================================================================
# CS2 Ancient Chinese Secrets – Carmack Edition GUI
# Version: Alpha v0.0006-ENHANCED | Robust Architecture
# =============================================================================

import os
import sys
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk
from PIL.Image import Resampling
import logging
from typing import Dict, List, Optional, Callable

from file_loader import load_file
from utils.logging_config import logger  # Centralized file logger

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'utils'))

ROOT_DIR = "C:/Users/jerry/Downloads/CS2-ACS-CM"
ASSET_DIR = os.path.join(ROOT_DIR, "asset")
PEWPEW_DIR = os.path.join(ROOT_DIR, "pewpew")

ICON_PATH = os.path.join(ASSET_DIR, "CS2.png")
BANNER_GRAY = os.path.join(ASSET_DIR, "CS2-gray.png")
BANNER_GIF = os.path.join(ASSET_DIR, "CS2-tb-fill.gif")
BANNER_COL = os.path.join(ASSET_DIR, "CS2-col.png")

class DropdownData:
    """Centralized container for dropdown data management"""
    def __init__(self):
        self.players: List[str] = []
        self.rounds: List[str] = []
        self.raw_player_data: List[Dict] = []
        self.raw_round_data: List[Dict] = []
    
    def clear(self):
        self.players.clear()
        self.rounds.clear()
        self.raw_player_data.clear()
        self.raw_round_data.clear()

class Banner(tk.Label):
    """Enhanced banner with better state management"""
    
    def __init__(self, parent, gray_path, gif_path, col_path, width, height):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.width = width
        self.height = height
        self.running = False
        self.current_frame = 0
        self._animation_id = None
        
        # Load images with better error handling
        self.gray_tk = self._load_image(gray_path)
        self.col_tk = self._load_image(col_path)
        self.frames = self._load_gif_frames(gif_path)
        
        # Set initial state
        self.config(image=self.gray_tk if self.gray_tk else None)

    def _load_image(self, path: str) -> Optional[ImageTk.PhotoImage]:
        try:
            if not os.path.exists(path):
                logger.warning(f"Image file not found: {path}")
                return None
            img = Image.open(path).resize((self.width, self.height), Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logger.warning(f"Failed to load image: {path} → {e}")
            return None

    def _load_gif_frames(self, gif_path: str) -> List[ImageTk.PhotoImage]:
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
        if not self.frames:
            logger.warning("Cannot start animation - no frames loaded")
            return
        self.running = True
        self.current_frame = 0
        self._animate()

    def stop(self):
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
        """Set banner state: gray, col, fill, or green/red for status"""
        self.stop()  # Stop any current animation
        
        if variant == "gray" and self.gray_tk:
            self.config(image=self.gray_tk)
        elif variant in ["col", "green"] and self.col_tk:
            self.config(image=self.col_tk)
        elif variant == "fill":
            self.start()
        elif variant == "red" and self.gray_tk:
            # Use gray for error state if no red image available
            self.config(image=self.gray_tk)

# Import statements for parser modules
from utils.dropdown_utils import build_player_dropdown as parse_player_dropdown
from utils.round_dropdown_utils import parse_round_dropdown
from utils.steam_utils import to_steam2
from utils.sanitizer_report import generate_sanitizer_report

from cs2_parser.chat_summary import display_chat_summary
from cs2_parser.stats_summary import display_stats_summary
from cs2_parser.event_log import event_log_tab_controller, generate_event_summary

class CS2ParserApp:
    """Enhanced main application with improved architecture"""
    
    def __init__(self, root):
        root.title("CS2 ACS – Carmack Edition Alpha v0.0006-ENHANCED")
        root.geometry("1100x750")
        root.configure(bg="black")
        
        # Set icon if available
        if os.path.isfile(ICON_PATH):
            try:
                root.iconphoto(False, tk.PhotoImage(file=ICON_PATH))
            except Exception as e:
                logger.warning(f"Failed to set icon: {e}")

        self.root = root
        self.data: Dict = {}
        self.dropdown_data = DropdownData()
        self.loaded_file_path: Optional[str] = None
        self.loading_thread: Optional[threading.Thread] = None
        
        # GUI Variables
        self.player_var = tk.StringVar()
        self.round_var = tk.StringVar()
        
        # Build UI
        self._build_ui()
        self.set_progress(0)

    def _build_ui(self):
        """Build the complete UI"""
        self._setup_styles()
        self._create_banner()
        self._create_menu()
        self._create_tabs()
        self._create_bottom_panel()

    def _setup_styles(self):
        """Configure ttk styles"""
        s = ttk.Style()
        s.theme_use("default")
        s.configure("TNotebook", background="black")
        s.configure("TNotebook.Tab", background="#111", foreground="white", padding=(10, 5))
        s.map("TNotebook.Tab", background=[("selected", "#333")])
        s.configure("Treeview", background="black", foreground="white",
                    fieldbackground="black", rowheight=20)

    def _create_banner(self):
        """Create animated banner"""
        self.banner = Banner(self.root, BANNER_GRAY, BANNER_GIF, BANNER_COL, 1075, 90)
        self.banner.pack(pady=(6, 0))

    def _create_menu(self):
        """Create application menu"""
        menubar = tk.Menu(self.root)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open DEM/JSON", command=self.select_file)
        file_menu.add_command(label="Generate Sanitizer Report", command=self.trigger_sanitizer)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _show_about(self):
        """Show about dialog"""
        about_msg = (
            "CS2 Ancient Chinese Secrets – Carmack Edition\n"
            "Version: Alpha v0.0006-ENHANCED\n"
            "Authors: Athlenia QA, pzr1H\n"
            "Project Start Date: July 1, 2025\n\n"
            "Description:\n"
            "Anti-cheat, Stat Analysis, and Demo Replay tools\n"
            "for CS2 – fully extensible, visual, and paranoid QA-grade."
        )
        messagebox.showinfo("About CS2 ACS", about_msg)

    def _create_tabs(self):
        """Create notebook tabs"""
        self.notebook = ttk.Notebook(self.root)
        self.tabs = {}

        tab_names = [
            "Console",
            "Event Log", 
            "Advanced Stats",
            "Chat & Summary",
            "Damage Summary",
            "Scout Report"
        ]

        for name in tab_names:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=name)
            self.tabs[name] = frame

        self.notebook.pack(expand=1, fill="both", pady=10, padx=6)

        # Setup console tab
        self.console = ScrolledText(
            self.tabs["Console"], height=20,
            bg="black", fg="lime", insertbackground="white", wrap=tk.WORD
        )
        self.console.pack(expand=True, fill="both")

        # Setup scout report placeholder
        ttk.Label(
            self.tabs["Scout Report"],
            text="⚔️ Scout Report will populate on load...",
            foreground="white", background="black", font=("Consolas", 10)
        ).pack(padx=12, pady=8, anchor="nw")

    def _create_bottom_panel(self):
        """Create bottom control panel with dropdowns and buttons"""
        bottom = tk.Frame(self.root, bg="black")
        bottom.pack(side="bottom", fill="x", pady=(2, 5))

        # Player dropdown
        ttk.Label(bottom, text="Player:", foreground="white", background="black").pack(side="left", padx=5)
        self.player_menu = ttk.OptionMenu(bottom, self.player_var, "No data")
        self.player_menu.pack(side="left")

        # Round dropdown
        ttk.Label(bottom, text="Round:", foreground="white", background="black").pack(side="left", padx=5)
        self.round_menu = ttk.OptionMenu(bottom, self.round_var, "No data")
        self.round_menu.pack(side="left")

        # Spacer
        spacer = ttk.Label(bottom, text="", background="black")
        spacer.pack(side="left", padx=6)

        # Action buttons
        ttk.Button(bottom, text="📊 Generate Stats", command=self.generate_stats).pack(side="left", padx=4)
        ttk.Button(bottom, text="🛠️ Debug", command=self.debug_json).pack(side="right", padx=6)

    def _log(self, message: str, color: str = "white"):
        """Thread-safe logging to console"""
        def _do_log():
            try:
                self.console.insert(tk.END, f"{message}\n")
                if color != "white":
                    line_start = f"end-{len(message)+1}c"
                    self.console.tag_config(color, foreground=color)
                    self.console.tag_add(color, line_start, "end-1c")
                self.console.see(tk.END)
                self.root.update_idletasks()
            except Exception as e:
                logger.error(f"Console logging failed: {e}")
        
        if threading.current_thread() == threading.main_thread():
            _do_log()
        else:
            self.root.after(0, _do_log)

    def select_file(self):
        """File selection and loading with improved error handling"""
        file_path = filedialog.askopenfilename(
            title="Select Demo or JSON File",
            filetypes=[
                ("Demo files", "*.dem"), 
                ("JSON files", "*.json"), 
                ("All supported", "*.dem *.json"),
                ("All files", "*.*")
            ]
        )
        
        if not file_path:
            return

        # Prevent multiple concurrent loads
        if self.loading_thread and self.loading_thread.is_alive():
            self._log("⚠️ File loading already in progress...", "yellow")
            return

        self.loaded_file_path = file_path
        self._start_file_loading(file_path)

    def _start_file_loading(self, file_path: str):
        """Start file loading in background thread"""
        self.set_progress(10)
        self._log(f"📂 File selected: {file_path}", "blue")
        self.banner.set_variant("fill")
        
        # Clear previous data
        self.data.clear()
        self.dropdown_data.clear()
        self._clear_dropdowns()
        
        # Start loading thread
        self.loading_thread = threading.Thread(target=self._threaded_load, args=(file_path,))
        self.loading_thread.daemon = True
        self.loading_thread.start()

    def _threaded_load(self, file_path: str):
        """Background file loading with progress updates"""
        try:
            self._log("🔄 Starting file parse...", "cyan")
            
            # Load file with console callback for live updates
            data = load_file(file_path, console_callback=self._log)
            
            if not data or not isinstance(data, dict):
                raise ValueError("Parsed data is empty or invalid format")
            
            self.data = data
            self.root.after(0, self._on_load_success)
            
        except Exception as e:
            error_msg = f"Failed to parse file: {str(e)}"
            logger.error(error_msg)
            self.root.after(0, lambda: self._on_load_error(error_msg))

    def _on_load_success(self):
        """Handle successful file loading"""
        try:
            event_count = len(self.data.get("events", []))
            self._log(f"✅ File parsed successfully - {event_count} events", "green")
            
            # Populate UI tabs
            self._populate_tabs()
            
            # Extract and update dropdowns
            self._extract_dropdown_data()
            self._update_dropdowns()
            
            # Update banner and progress
            self.banner.set_variant("green")
            self.set_progress(100)
            
        except Exception as e:
            self._on_load_error(f"Post-processing failed: {e}")

    def _on_load_error(self, error_msg: str):
        """Handle file loading errors"""
        self._log(f"❌ {error_msg}", "red")
        self.banner.set_variant("red")
        self.set_progress(0)

    def _extract_dropdown_data(self):
        """Extract player and round data for dropdowns"""
        try:
            events = self.data.get("events", [])
            if not events:
                self._log("⚠️ No events found for dropdown extraction", "yellow")
                return

            # Extract players
            players_dict = {}
            rounds_set = set()

            for event in events:
                # Extract player information
                player_info = self._extract_player_from_event(event)
                if player_info:
                    key = f"{player_info['name']} ({player_info['steam2']})"
                    players_dict[key] = player_info

                # Extract round information
                round_num = event.get("round")
                if isinstance(round_num, int) and round_num >= 0:
                    rounds_set.add(round_num)

            # Store extracted data
            self.dropdown_data.players = sorted(players_dict.keys())
            self.dropdown_data.rounds = [f"Round {r+1}" for r in sorted(rounds_set)]
            self.dropdown_data.raw_player_data = list(players_dict.values())

            self._log(f"👥 Extracted {len(self.dropdown_data.players)} players, {len(self.dropdown_data.rounds)} rounds", "cyan")

        except Exception as e:
            logger.error(f"Dropdown extraction failed: {e}")
            self._log(f"⚠️ Dropdown extraction failed: {e}", "orange")

    def _extract_player_from_event(self, event: Dict) -> Optional[Dict]:
        """Extract player info from a single event"""
        try:
            # Try different event structures
            player_data = None
            
            # Method 1: Direct player field
            if "player" in event:
                player_data = event["player"]
            
            # Method 2: Direct fields in event
            elif "name" in event and ("steamId" in event or "steamID" in event):
                player_data = {
                    "name": event["name"],
                    "steamId": event.get("steamId") or event.get("steamID")
                }
            
            # Method 3: Details field (for PlayerInfo events)
            elif event.get("type") == "events.PlayerInfo" and "details" in event:
                details = event["details"]
                if isinstance(details, dict):
                    for key, player_obj in details.items():
                        info = player_obj.get("Info") or player_obj.get("info") or {}
                        if isinstance(info, dict):
                            name = info.get("Name") or info.get("name")
                            xuid = info.get("XUID") or info.get("xuid")
                            if name and xuid:
                                player_data = {"name": name, "steamId": str(xuid)}
                                break

            if player_data:
                name = player_data.get("name")
                steam_id = player_data.get("steamId")
                
                if name and steam_id:
                    try:
                        steam2 = to_steam2(int(steam_id))
                        return {
                            "name": name,
                            "steamId": steam_id,
                            "steam2": steam2
                        }
                    except (ValueError, TypeError):
                        logger.warning(f"Invalid steamId format: {steam_id}")

        except Exception as e:
            logger.debug(f"Player extraction error for event: {e}")
        
        return None

    def _update_dropdowns(self):
        """Update dropdown menus with extracted data"""
        try:
            # Update player dropdown
            self.player_menu["menu"].delete(0, "end")
            if self.dropdown_data.players:
                for player in self.dropdown_data.players:
                    self.player_menu["menu"].add_command(
                        label=player, 
                        command=tk._setit(self.player_var, player)
                    )
                self.player_var.set(self.dropdown_data.players[0])
            else:
                self.player_menu["menu"].add_command(label="No players found", state="disabled")
                self.player_var.set("No players found")

            # Update round dropdown
            self.round_menu["menu"].delete(0, "end")
            if self.dropdown_data.rounds:
                for round_label in self.dropdown_data.rounds:
                    self.round_menu["menu"].add_command(
                        label=round_label,
                        command=tk._setit(self.round_var, round_label)
                    )
                self.round_var.set(self.dropdown_data.rounds[0])
            else:
                self.round_menu["menu"].add_command(label="No rounds found", state="disabled")
                self.round_var.set("No rounds found")

        except Exception as e:
            logger.error(f"Dropdown update failed: {e}")
            self._log(f"⚠️ Dropdown update failed: {e}", "orange")

    def _clear_dropdowns(self):
        """Clear dropdown menus"""
        try:
            self.player_menu["menu"].delete(0, "end")
            self.round_menu["menu"].delete(0, "end")
            self.player_var.set("No data")
            self.round_var.set("No data")
        except Exception as e:
            logger.debug(f"Dropdown clear failed: {e}")

    def _populate_tabs(self):
        """Populate all tabs with data"""
        try:
            # Chat & Summary tab
            display_chat_summary(self.tabs["Chat & Summary"], self.data)
            
            # Advanced Stats tab
            display_stats_summary(self.tabs["Advanced Stats"], self.data)
            
            # Event Log tab (with callback for dropdown refresh)
            event_log_tab_controller(
                self.tabs["Event Log"], 
                self.data, 
                banner=self.banner,
                dropdown_callback=self._on_event_log_ready
            )
            
            self._log("📊 All tabs populated successfully", "green")
            
        except Exception as e:
            self._log(f"⚠️ Error populating tabs: {e}", "red")
            logger.error(f"Tab population failed: {e}")

    def _on_event_log_ready(self, event_log_data: Dict):
        """Callback when event log processing is complete"""
        try:
            # Use event log data to enhance dropdowns if needed
            if hasattr(event_log_data, 'get'):
                playerinfo_events = event_log_data.get('playerinfo_events', [])
                roundend_events = event_log_data.get('roundend_events', [])
                
                if playerinfo_events or roundend_events:
                    self._log("🔄 Enhancing dropdowns with Event Log data", "cyan")
                    # Additional dropdown enhancement logic could go here
                    
        except Exception as e:
            logger.debug(f"Event log callback failed: {e}")

    def generate_stats(self):
        """Generate and display statistics"""
        try:
            if not self.data:
                self._log("⚠️ No data loaded for stats generation", "yellow")
                return
                
            display_stats_summary(self.tabs["Advanced Stats"], self.data)
            self._log("📊 Stats refreshed successfully", "green")
            
        except Exception as e:
            self._log(f"⚠️ Failed to generate stats: {e}", "red")
            logger.error(f"Stats generation failed: {e}")

    def debug_json(self):
        """Generate sanitizer report for debugging"""
        try:
            if not self.data:
                self._log("⚠️ No data loaded for debug report", "yellow")
                return
                
            generate_sanitizer_report(self.data)
            self._log("🩺 Sanitizer report generated successfully", "green")
            
        except Exception as e:
            self._log(f"❌ Error during sanitizer report: {e}", "red")
            logger.error(f"Sanitizer report failed: {e}")

    def trigger_sanitizer(self):
        """Trigger sanitizer report from menu"""
        self.debug_json()

    def set_progress(self, value: int):
        """Set loading progress (0-100)"""
        try:
            if value == 0:
                self.banner.set_variant("gray")
            elif value < 100:
                self.banner.set_variant("fill")
            else:
                self.banner.set_variant("green")
            self.root.update_idletasks()
        except Exception as e:
            logger.debug(f"Progress update failed: {e}")

def main():
    """Application entry point"""
    try:
        root = tk.Tk()
        app = CS2ParserApp(root)
        root.mainloop()
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        print(f"Failed to start application: {e}")

if __name__ == "__main__":
    main()
#EOF TLOC 610 CLAUDE & pzr1H Jul 26 5:08pm ET wip_cmain.py