#!/usr/bin/env python3
# =============================================================================
# CS2 Ancient Chinese Secrets – Carmack Edition GUI  (Alpha v0.0004-PATCHED)
# Fully patched with animated banner + dropdown utilities + debug logging
# Timestamp-TOP: 2025-07-25
# =============================================================================

# =============================================================================
# Block 1: Core Imports and Setup
# =============================================================================
import os, sys, json, logging, threading, re
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Force subfolder modules to be importable
sys.path.insert(0, os.path.join(ROOT_DIR, "cs2_parser"))
sys.path.insert(0, os.path.join(ROOT_DIR, "utils"))

# =============================================================================
# Block 2: Local Imports — Modules and Utilities
# =============================================================================

# Core logic modules
from file_loader               import load_file
from cs2_parser.chat_summary   import display_chat_summary
from cs2_parser.stats_summary  import display_stats_summary
from cs2_parser.event_log      import display_event_log
from cs2_parser.damage_summary import display_damage_summary
from cs2_parser.replay_round   import init_replay_tab as replay_round
from cs2_parser.sanitizer_report import generate_sanitizer_report

# UI / Utility logic
from utils.dropdown_utils import parse_player_dropdown
from utils.round_dropdown_utils  import parse_round_dropdown
from utils.cross_module_debugging import trace_log

# =============================================================================
# Block 3: Banner Asset Paths and Logging Setup
# =============================================================================

PCT_RE      = re.compile(r"(\d{1,3})%")
ASSET_DIR   = os.path.join(ROOT_DIR, "asset")
ICON_PATH   = os.path.join(ASSET_DIR, "CS2.png")
BANNER_GRAY = os.path.join(ASSET_DIR, "CS2-gray.png")
BANNER_GIF  = os.path.join(ASSET_DIR, "CS2-tb-fill.gif")
BANNER_COL  = os.path.join(ASSET_DIR, "CS2-col.png")

logging.basicConfig(level=logging.DEBUG, format="%(asctime)s %(levelname)s: %(message)s")
log = logging.getLogger(__name__)


# =============================================================================
# Block 2: Banner Class
# =============================================================================
class Banner(tk.Label):
    def __init__(self, master, gray, gif, color, w, h, delay=100, **kw):
        super().__init__(master, **kw)
        self.gray_tk  = ImageTk.PhotoImage(Image.open(gray).resize((w, h), Image.LANCZOS))
        self.color_tk = ImageTk.PhotoImage(Image.open(color).resize((w, h), Image.LANCZOS))
        self.frames   = []

        gif_img = Image.open(gif)
        for f in range(getattr(gif_img, "n_frames", 1)):
            try:
                gif_img.seek(f)
                frm = gif_img.copy().convert("RGBA").resize((w, h), Image.LANCZOS)
                self.frames.append(ImageTk.PhotoImage(frm))
            except EOFError:
                break

        self.config(image=self.gray_tk)
        self._delay = delay
        self._animating = False
        self._idx = 0

    def start(self):
        if self.frames and not self._animating:
            self._animating = True
            self._idx = 0
            self._animate()

    def _animate(self):
        if not self._animating:
            return
        self.config(image=self.frames[self._idx])
        self._idx = (self._idx + 1) % len(self.frames)
        self.after(self._delay, self._animate)

    def stop(self):
        self._animating = False
        self.config(image=self.color_tk)

# =============================================================================
# Block 3: CS2ParserApp Class
# =============================================================================
class CS2ParserApp:
    def __init__(self, root):
        root.title("CS2 ACS – Carmack Edition Alpha v0.0004-PATCHED")
        root.geometry("1100x750")
        root.configure(bg="black")

        if os.path.isfile(ICON_PATH):
            root.iconphoto(False, tk.PhotoImage(file=ICON_PATH))

        self.root = root
        self.json_data = {}
        self.rounds = []

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
        self.root.config(menu=menubar)

    def _tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.tabs = {}

        for name in ["Console", "Event Log", "Advanced Stats", "Chat & Summary", "Damage Summary"]:
            frame = ttk.Frame(self.notebook)
            self.notebook.add(frame, text=name)
            self.tabs[name] = frame

        self.notebook.pack(expand=1, fill="both", pady=10, padx=6)

        self.console = ScrolledText(self.tabs["Console"], height=20, bg="black", fg="lime",
                                    insertbackground="white", wrap=tk.WORD)
        self.console.pack(expand=True, fill="both")

    def _bottom(self):
        bottom = tk.Frame(self.root, bg="black")
        bottom.pack(side="bottom", fill="x", pady=(2, 5))

        self.player_var = tk.StringVar()
        self.round_var  = tk.StringVar()

        ttk.Label(bottom, text="Player:", foreground="white", background="black").pack(side="left", padx=5)
        self.player_menu = ttk.OptionMenu(bottom, self.player_var, "")
        self.player_menu.pack(side="left")

        ttk.Label(bottom, text="Round:", foreground="white", background="black").pack(side="left", padx=5)
        self.round_menu = ttk.OptionMenu(bottom, self.round_var, "")
        self.round_menu.pack(side="left")

        ttk.Button(bottom, text="Replay Round", command=self.replay).pack(side="left", padx=8)
        ttk.Button(bottom, text="Generate Stats", command=self.stats).pack(side="left", padx=4)
        ttk.Button(bottom, text="Debug", command=self.debug_json).pack(side="right", padx=6)

    def select_file(self):
        file_path = filedialog.askopenfilename(title="Select Demo or JSON File",
                    filetypes=[("Demo files", "*.dem"), ("JSON files", "*.json"), ("All files", "*.*")])
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
            self._refresh_dropdowns()
            self._populate_tabs()
            self._log("✅ File parsed successfully.", "green")
        except Exception as e:
            self._log(f"❌ Failed to parse file: {e}", "red")
        finally:
            self.set_progress(100)

    def _populate_tabs(self):
        try:
            display_chat_summary(self.tabs["Chat & Summary"], self.data)
            display_stats_summary(self.tabs["Advanced Stats"], self.data)
            display_event_log(self.tabs["Event Log"], self.data)
            display_damage_summary(self.tabs["Damage Summary"], self.data)
        except Exception as e:
            self._log(f"⚠️ Error populating tabs: {e}", "red")

    def _refresh_dropdowns(self):
        try:
            players = parse_player_dropdown(self.data)
            rounds  = parse_round_dropdown(self.data)

            self.player_menu['menu'].delete(0, 'end')
            self.round_menu['menu'].delete(0, 'end')

            for p in players:
                self.player_menu['menu'].add_command(label=p, command=tk._setit(self.player_var, p))
            for r in rounds:
                self.round_menu['menu'].add_command(label=r, command=tk._setit(self.round_var, r))

            if players:
                self.player_var.set(players[0])
            if rounds:
                self.round_var.set(rounds[0])

            self._log(f"🔄 Dropdowns refreshed — Players: {len(players)}, Rounds: {len(rounds)}", "cyan")
        except Exception as e:
            self._log(f"⚠️ Failed to refresh dropdowns: {e}", "red")

    def _log(self, msg, color="white"):
        trace_log("main", msg)
        self.console.tag_config(color, foreground=color)
        self.console.insert("end", f"{msg}\n", color)
        self.console.see("end")

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

    def replay(self):
        try:
            round_selected = self.round_var.get()
            player_selected = self.player_var.get()
            self._log(f"▶ Replay triggered — Player: {player_selected}, Round: {round_selected}", "cyan")
            replay_round(round_selected, player_selected, self.data)
        except Exception as e:
            self._log(f"❌ Replay trigger failed: {e}", "red")

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

# =============================================================================
# Launch Entry Point
# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = CS2ParserApp(root)
    root.mainloop()
#EOF — TLOC 272 — ✅ Final Canonical Patch Validated Jul 25 5:03pm ET by pzr1H
