#!/usr/bin/env python3
# =============================================================================
# CS2 Ancient Chinese Secrets – Carmack Edition GUI
# Version: Alpha v0.0005-FINAL | Fully Robust Dropdown Patch
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

class Banner(tk.Label):
    # (Keep your Banner class as-is)

    def __init__(self, parent, gray_path, gif_path, col_path, width, height):
        super().__init__(parent, bg="black")
        self.parent = parent
        self.width = width
        self.height = height
        self.running = False
        self.gray_tk = self._load_image(gray_path)
        self.col_tk = self._load_image(col_path)
        self.frames = self._load_gif_frames(gif_path)
        self.config(image=self.gray_tk)
        self.current_frame = 0

    def _load_image(self, path):
        try:
            img = Image.open(path).resize((self.width, self.height), Resampling.LANCZOS)
            return ImageTk.PhotoImage(img)
        except Exception as e:
            logger.warning(f"[WARN] Failed to load image: {path} → {e}")
            return None

    def _load_gif_frames(self, gif_path):
        try:
            img = Image.open(gif_path)
            frames = []
            for frame in range(img.n_frames):
                img.seek(frame)
                frame_resized = img.resize((self.width, self.height), Resampling.LANCZOS)
                frames.append(ImageTk.PhotoImage(frame_resized))
            return frames
        except Exception as e:
            logger.error(f"[ERROR] Failed to load gif frames from {gif_path}: {e}")
            return []

    def start(self):
        if not self.frames:
            return
        self.running = True
        self._animate()

    def stop(self):
        self.running = False
        self.config(image=self.col_tk)

    def _animate(self):
        if not self.running or not self.frames:
            return
        self.config(image=self.frames[self.current_frame])
        self.current_frame = (self.current_frame + 1) % len(self.frames)
        self.after(100, self._animate)

    def set_variant(self, variant="gray"):
        if variant == "gray":
            self.config(image=self.gray_tk)
        elif variant == "col":
            self.config(image=self.col_tk)
        elif variant == "fill":
            self.start()

from utils.dropdown_utils import build_player_dropdown as parse_player_dropdown
from utils.round_dropdown_utils import parse_round_dropdown
from utils.steam_utils import to_steam2
from utils.sanitizer_report import generate_sanitizer_report

from cs2_parser.chat_summary import display_chat_summary
from cs2_parser.stats_summary import display_stats_summary
from cs2_parser.event_log import event_log_tab_controller, generate_event_summary
# from cs2_parser.replay_round import replay_round  # Uncomment when ready

class CS2ParserApp:
    def __init__(self, root):
        root.title("CS2 ACS – Carmack Edition Alpha v0.0005-FINAL")
        root.geometry("1100x750")
        root.configure(bg="black")

        if os.path.isfile(ICON_PATH):
            root.iconphoto(False, tk.PhotoImage(file=ICON_PATH))

        self.root = root
        self.data = {}
        self.rounds = []

        self.player_var = tk.StringVar()
        self.round_var = tk.StringVar()

        self._build_ui()
        self.set_progress(0)

    def _build_ui(self):
        self._style()
        self._banner()
        self._menu()
        self._tabs()
        self._bottom()

    def _style(self):
        s = ttk.Style()
        s.theme_use("default")
        s.configure("TNotebook", background="black")
        s.configure("TNotebook.Tab", background="#111", foreground="white", padding=(10, 5))
        s.map("TNotebook.Tab", background=[("selected", "#333")])
        s.configure("Treeview", background="black", foreground="white",
                    fieldbackground="black", rowheight=20)

    def _banner(self):
        self.banner = Banner(self.root, BANNER_GRAY, BANNER_GIF, BANNER_COL, 1075, 90)
        self.banner.pack(pady=(6, 0))

    def _menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open DEM/JSON", command=self.select_file)
        file_menu.add_command(label="Generate Sanitizer Report", command=self.trigger_sanitizer)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="About", command=self._show_about)
        menubar.add_cascade(label="Help", menu=help_menu)

        self.root.config(menu=menubar)

    def _show_about(self):
        about_msg = (
            "CS2 Ancient Chinese Secrets – Carmack Edition\n"
            "Version: Alpha v0.0005-FINAL\n"
            "Authors: Athlenia QA, pzr1H\n"
            "Project Start Date: July 1, 2025\n"
            "Description:\n"
            "Anti-cheat, Stat Analysis, and Demo Replay tools\n"
            "for CS2 – fully extensible, visual, and paranoid QA-grade."
        )
        messagebox.showinfo("About CS2 ACS", about_msg)

    def _tabs(self):
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

        self.console = ScrolledText(
            self.tabs["Console"], height=20,
            bg="black", fg="lime", insertbackground="white", wrap=tk.WORD
        )
        self.console.pack(expand=True, fill="both")

        ttk.Label(
            self.tabs["Scout Report"],
            text="⚔️ Scout Report will populate on load...",
            foreground="white", background="black", font=("Consolas", 10)
        ).pack(padx=12, pady=8, anchor="nw")

    def _bottom(self):
        bottom = tk.Frame(self.root, bg="black")
        bottom.pack(side="bottom", fill="x", pady=(2, 5))

        ttk.Label(bottom, text="Player:", foreground="white", background="black").pack(side="left", padx=5)
        self.player_menu = ttk.OptionMenu(bottom, self.player_var, "")
        self.player_menu.pack(side="left")

        ttk.Label(bottom, text="Round:", foreground="white", background="black").pack(side="left", padx=5)
        self.round_menu = ttk.OptionMenu(bottom, self.round_var, "")
        self.round_menu.pack(side="left")

        spacer = ttk.Label(bottom, text="", background="black")
        spacer.pack(side="left", padx=6)

        ttk.Button(bottom, text="📊 Generate Stats", command=self.stats).pack(side="left", padx=4)
        ttk.Button(bottom, text="🛠️ Debug", command=self.debug_json).pack(side="right", padx=6)

    def run_parse(self):
        filetypes = [("Supported files", "*.dem *.json")]
        file_path = filedialog.askopenfilename(filetypes=filetypes)

        if not file_path:
            return

        self.loaded_file_path = file_path
        self.set_progress(10)
        self._log(f"📂 File selected: {file_path}", "blue")
        self.banner.set_variant("fill")

        thread = threading.Thread(target=self.threaded_load)
        thread.daemon = True
        thread.start()

    def threaded_load(self):
        try:
            data = load_file(self.loaded_file_path)
            if not isinstance(data, dict):
                raise ValueError("Parsed data is not a dictionary")
            self.data = data
            self.root.after(0, self._post_parse_ui_update)
        except Exception as e:
            self.root.after(0, lambda: self._handle_parse_error(e))

    def _post_parse_ui_update(self):
        self._log(f"✅ Parsed file with {len(self.data.get('events', []))} events", "green")
        self._populate_tabs()
        self._refresh_dropdowns()
        self.banner.set_variant("green")
        self.set_progress(100)

    def _handle_parse_error(self, e):
        self._log(f"❌ Failed to parse file: {e}", "red")
        self.banner.set_variant("red")
        self.set_progress(0)

    def _refresh_dropdowns(self):
        try:
            if not self.data:
                self._log("⚠️ No data loaded for dropdowns", "yellow")
                return

            self._log(f"🔄 Refreshing dropdowns with {len(self.data.get('events', []))} events", "green")

            event_log_tab = self.tabs.get("Event Log")
            if not event_log_tab:
                self._log("⚠️ Event Log tab missing; cannot refresh dropdowns", "orange")
                return

            playerinfo_events = getattr(event_log_tab, "filtered_playerinfo_events", [])
            roundend_events = getattr(event_log_tab, "filtered_roundend_events", [])

            if not playerinfo_events:
                self._log("⚠️ No PlayerInfo events found; player dropdown will be empty", "orange")

            players_set = set()
            for idx, ev in enumerate(playerinfo_events):
                try:
                    details = ev.get("Details") or ev.get("details") or {}
                    if not isinstance(details, dict):
                        self._log(f"⚠️ PlayerInfo event[{idx}] 'Details' field missing or malformed", "orange")
                        continue
                    for key, player_obj in details.items():
                        info = player_obj.get("Info") or player_obj.get("info") or {}
                        if not isinstance(info, dict):
                            self._log(f"⚠️ PlayerInfo event[{idx}] player '{key}' 'Info' missing or malformed", "orange")
                            continue
                        name = info.get("Name") or info.get("name")
                        xuid = info.get("XUID") or info.get("xuid")
                        if name and xuid:
                            players_set.add(f"{name} ({xuid})")
                        else:
                            self._log(f"⚠️ PlayerInfo event[{idx}] player '{key}' missing Name or XUID", "orange")
                except Exception as e:
                    self._log(f"❌ Exception processing PlayerInfo event[{idx}]: {e}", "red")

            players_list = sorted(players_set)
            if players_list:
                self._log(f"✅ Extracted {len(players_list)} players for dropdown", "green")
            else:
                self._log("⚠️ Player list empty after extraction", "yellow")

            rounds_set = set()
            for idx, ev in enumerate(roundend_events):
                try:
                    round_num = ev.get("Round") or ev.get("round")
                    if isinstance(round_num, int):
                        rounds_set.add(round_num)
                    else:
                        self._log(f"⚠️ RoundEndOfficial event[{idx}] missing valid 'Round' int", "orange")
                except Exception as e:
                    self._log(f"❌ Exception processing RoundEndOfficial event[{idx}]: {e}", "red")

            rounds_list = [f"Round {r}" for r in sorted(rounds_set)]
            if rounds_list:
                self._log(f"✅ Extracted {len(rounds_list)} rounds for dropdown", "green")
            else:
                self._log("⚠️ Round list empty after extraction", "yellow")

            if players_list:
                self.player_menu["menu"].delete(0, "end")
                for player in players_list:
                    self.player_menu["menu"].add_command(label=player, command=tk._setit(self.player_var, player))
                self.player_var.set(players_list[0])
            else:
                self._log("⚠️ No player data available to populate dropdown", "yellow")

            if rounds_list:
                self.round_menu["menu"].delete(0, "end")
                for rnd in rounds_list:
                    self.round_menu["menu"].add_command(label=rnd, command=tk._setit(self.round_var, rnd))
                self.round_var.set(rounds_list[0])
            else:
                self._log("⚠️ No round data available to populate dropdown", "yellow")

        except Exception as e:
            self._log(f"❌ Unexpected error in _refresh_dropdowns: {e}", "red")

    def _log(self, message, color="white"):
        self.console.insert(tk.END, f"{message}\n")
        self.console.tag_config(color, foreground=color)
        self.console.tag_add(color, f"end-{len(message)+1}c", "end")
        self.console.see(tk.END)

    def select_file(self):
        file_path = filedialog.askopenfilename(
            title="Select Demo or JSON File",
            filetypes=[("Demo files", "*.dem"), ("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return

        self.set_progress(10)
        self._log(f"📂 File selected: {file_path}", "blue")
        try:
            data = load_file(file_path)
            if not data:
                raise ValueError("Parsed data is empty or None.")
            self.data = data
            self.loaded_data = data

            self._inject_dropdown_from_event_log()
            self._populate_tabs()
            self._log("✅ File parsed successfully.", "green")
        except Exception as e:
            self._log(f"❌ Failed to parse file: {e}", "red")
        finally:
            self.set_progress(100)

    def _inject_dropdown_from_event_log(self):
        # fallback method - can be simplified later
        from utils.steam_utils import to_steam2
        events = self.data.get("events", [])

        players_set = set()
        rounds_set = set()

        for event in events:
            if "player" in event:
                player = event.get("player", {})
                name = player.get("name") or player.get("Name")
                steamid = player.get("steamId") or player.get("SteamID")
                if name and steamid:
                    steam2 = to_steam2(steamid)
                    players_set.add(f"{name} ({steam2})")
            elif "steamId" in event:
                name = event.get("name")
                steamid = event.get("steamId")
                if name and steamid:
                    steam2 = to_steam2(steamid)
                    players_set.add(f"{name} ({steam2})")

            round_num = event.get("round")
            if isinstance(round_num, int):
                rounds_set.add(round_num)

        sorted_players = sorted(players_set)
        sorted_rounds = [f"Round {r}" for r in sorted(rounds_set)]

        self.player_menu["menu"].delete(0, "end")
        for player in sorted_players:
            self.player_menu["menu"].add_command(label=player, command=tk._setit(self.player_var, player))

        self.round_menu["menu"].delete(0, "end")
        for rnd in sorted_rounds:
            self.round_menu["menu"].add_command(label=rnd, command=tk._setit(self.round_var, rnd))

        if sorted_players:
            self.player_var.set(sorted_players[0])
        if sorted_rounds:
            self.round_var.set(sorted_rounds[0])

        self._log(f"👥 Injected {len(sorted_players)} players and {len(sorted_rounds)} rounds from Event Log (fallback)", "cyan")

    def _populate_tabs(self):
        try:
            display_chat_summary(self.tabs["Chat & Summary"], self.data)
            display_stats_summary(self.tabs["Advanced Stats"], self.data)
            event_log_tab_controller(self.tabs["Event Log"], self.data, banner=self.banner)

            # Dropdown refresh fallback
            try:
                if hasattr(self, '_refresh_dropdowns'):
                    self._refresh_dropdowns()
                    logger.info("🔄 Dropdowns refreshed successfully via banner fallback.")
                else:
                    logger.warning("⚠️ GUI object missing '_refresh_dropdowns' method.")
            except Exception as e:
                logger.error(f"🔥 Dropdown refresh failed: {e}")

        except Exception as e:
            self._log(f"⚠️ Error populating tabs: {e}", "red")

    def stats(self):
        try:
            display_stats_summary(self.tabs["Advanced Stats"], self.data)
            self._log("📊 Stats refreshed.", "green")
        except Exception as e:
            self._log(f"⚠️ Failed to render stats: {e}", "red")

    def debug_json(self):
        try:
            if hasattr(self, "loaded_data"):
                generate_sanitizer_report(self.loaded_data)
                self._log("🩺 Sanitizer report launched.", "green")
            else:
                self._log("⚠️ No loaded data available for audit.", "orange")
        except Exception as e:
            self._log(f"❌ Error during sanitizer report: {e}", "red")

    def trigger_sanitizer(self):
        self.debug_json()

    def set_progress(self, value):
        if value == 0:
            self.banner.config(image=self.banner.gray_tk)
        elif value < 100:
            self.banner.start()
        else:
            self.banner.stop()
        self.root.update_idletasks()

def main():
    root = tk.Tk()
    app = CS2ParserApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
