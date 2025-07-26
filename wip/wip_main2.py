#!/usr/bin/env python3
# =============================================================================
# main.py - CS2 ACS GUI - Patch: Banner Instantiation + Dropdown Sync + Widget Fixes
# TLOC: ~80 lines (blocks 1 & 2)
# =============================================================================

import os, sys, io, json, threading, time, logging
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
from PIL import Image, ImageTk

# -------------------------------------------------------------------------
# Constant Paths - Hardcoded
# -------------------------------------------------------------------------
ROOT_DIR    = "C:/Users/jerry/Downloads/CS2-ACS-CM"
ASSET_DIR   = os.path.join(ROOT_DIR, "asset")
PEWPEW_DIR  = os.path.join(ROOT_DIR, "pewpew")
BANNER_PATH = os.path.join(ASSET_DIR, "CS2-progress.png")
ICON_PATH   = os.path.join(ASSET_DIR, "CS2.png")

# -------------------------------------------------------------------------
# Module Path Insert
# -------------------------------------------------------------------------
sys.path.insert(0, os.path.join(ROOT_DIR, "utils"))
sys.path.insert(0, ROOT_DIR)

# -------------------------------------------------------------------------
# Logging Setup
# -------------------------------------------------------------------------
log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)

# -------------------------------------------------------------------------
# GUI Root Initialization
# -------------------------------------------------------------------------
root = tk.Tk()
root.title("CS2 Ancient Chinese Secrets – Carmack Edition GUI (Alpha v0.0004-PATCHED)")
root.geometry("1280x900")
root.configure(bg="#1e1e1e")
root.option_add("*Font", "Segoe UI 9")

try:
    root.iconphoto(True, tk.PhotoImage(file=ICON_PATH))
except Exception as e:
    log.warning(f"⚠️ Failed to load icon: {e}")

style = ttk.Style()
style.theme_use("clam")
style.configure(".", background="#1e1e1e", foreground="white", fieldbackground="#1e1e1e")
style.configure("TLabel", background="#1e1e1e", foreground="white")
style.configure("TButton", background="#333", foreground="white", padding=5)
style.configure("Treeview", background="#2e2e2e", fieldbackground="#2e2e2e",
                foreground="white", bordercolor="#444", font=("Segoe UI", 9))
style.map("TButton", background=[("active", "#555")])

# -------------------------------------------------------------------------
# Banner Class & Early Instantiation
# -------------------------------------------------------------------------
class Banner:
    def __init__(self, parent):
        try:
            self.gray = Image.open(BANNER_PATH)
            self.color = Image.open(BANNER_PATH.replace("progress", "color"))
            self.gif = Image.open(BANNER_PATH.replace("progress", "loading"))
        except Exception as e:
            log.warning(f"⚠️ Failed to load banner images: {e}")
            self.gray = self.color = self.gif = None

        self.label = ttk.Label(parent)
        self.label.pack(pady=5)
        self.banner_state = "gray"
        if self.gray:
            self.update_banner(self.gray)

        self.players = []
        self.rounds = []

    def update_banner(self, img):
        try:
            img = img.resize((960, 120))
            img_tk = ImageTk.PhotoImage(img)
            self.label.configure(image=img_tk)
            self.label.image = img_tk
        except Exception as e:
            log.warning(f"⚠️ Failed to update banner image: {e}")

    def start_loading(self):
        self.banner_state = "loading"
        try:
            if self.gif:
                self.gif.seek(0)
                self.update_banner(self.gif)
        except Exception as e:
            log.warning(f"⚠️ Failed to start animated banner: {e}")

    def finish_loading(self):
        self.banner_state = "color"
        if self.color:
            self.update_banner(self.color)

    def capture_event_players(self, players, rounds):
        self.players = players
        self.rounds = rounds
        log.info(f"🎯 Captured dropdowns: {len(players)} players, {len(rounds)} rounds")

# Instantiate banner early
banner = Banner(root)

# -------------------------------------------------------------------------
# Dropdown Variables and Menus (Fixed names)
# -------------------------------------------------------------------------
player_var = tk.StringVar()
round_var = tk.IntVar()

bottom = ttk.Frame(root)
bottom.pack(side="bottom", fill="x", padx=10, pady=5)

ttk.Label(bottom, text="Player:").pack(side="left", padx=(10, 5))
player_menu = ttk.OptionMenu(bottom, player_var, "")
player_menu.pack(side="left")

ttk.Label(bottom, text="Round:").pack(side="left", padx=(10, 5))
round_menu = ttk.OptionMenu(bottom, round_var, 0)
round_menu.pack(side="left")

# -------------------------------------------------------------------------
# Console Text Widget & Logging Handler (Fixed console_text)
# -------------------------------------------------------------------------
console_frame = ttk.Frame(root)
console_frame.pack(fill="both", expand=True, padx=10, pady=5)

console_text = ScrolledText(console_frame, height=10, state="disabled", bg="black", fg="white")
console_text.pack(fill="both", expand=True)

class ConsoleHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        console_text.configure(state="normal")
        console_text.insert("end", msg + "\n")
        console_text.configure(state="disabled")
        console_text.yview_moveto(1.0)

handler = ConsoleHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
log.addHandler(handler)
log.info("📟 Console log panel initialized")

# -------------------------------------------------------------------------
# Dropdown Refresh Function (centralized)
# -------------------------------------------------------------------------
def refresh_dropdowns():
    player_menu["menu"].delete(0, "end")
    for player in banner.players:
        label = f'{player["name"]} ({player["steamid"]})' if player.get("steamid") else player["name"]
        player_menu["menu"].add_command(label=label, command=tk._setit(player_var, label))
    if banner.players:
        player_var.set(f'{banner.players[0]["name"]} ({banner.players[0]["steamid"]})')

    round_menu["menu"].delete(0, "end")
    for rnd in banner.rounds:
        round_menu["menu"].add_command(label=str(rnd), command=tk._setit(round_var, rnd))
    if banner.rounds:
        round_var.set(banner.rounds[0])

log.info("🔄 Dropdown refresh function initialized")

# EOF BLOCK 1 & 2 patch
# =============================================================================
# BLOCK 3: File Selection, Parsing, Dropdown Injection, and Logging
# =============================================================================

def select_and_parse_file():
    """
    Open file dialog for .dem or .json files,
    run parser, update dropdowns and logs, refresh banner state.
    """
    from file_loader import run_parser
    from utils.data_sanitizer import get_schema_status

    file_path = filedialog.askopenfilename(
        title="Select CS2 Demo or Parsed JSON",
        filetypes=[("Demo or JSON Files", "*.dem *.json")]
    )

    if not file_path:
        log.info("❎ File selection cancelled.")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    log.info(f"📁 Selected file: {file_name} ({file_size / 1024:.2f} KB)")

    console_text.configure(state="normal")
    console_text.insert(tk.END, f"\n🔁 Parsing started: {file_name}\n")
    console_text.insert(tk.END, f"📦 Size: {file_size / 1024:.2f} KB\n")
    console_text.configure(state="disabled")

    banner.start_loading()

    start_time = time.time()

    try:
        parsed_data = run_parser(file_path)
        duration = time.time() - start_time

        if not parsed_data:
            raise ValueError("Parsed data is empty or None")

        console_text.configure(state="normal")
        console_text.insert(tk.END, f"✅ Parsing completed in {duration:.2f}s\n")
        console_text.configure(state="disabled")

        # Schema validation status
        schema_ok, issues = get_schema_status(parsed_data)
        console_text.configure(state="normal")
        if schema_ok:
            console_text.insert(tk.END, "🧼 Schema validation passed\n")
        else:
            console_text.insert(tk.END, f"⚠️ Schema issues: {issues}\n")
        console_text.configure(state="disabled")

        # Inject dropdown options to banner (players, rounds)
        try:
            player_options = parse_player_dropdown(parsed_data.get("events", []))
            round_options = parse_round_dropdown(parsed_data.get("events", []))

            banner.capture_event_players(player_options, round_options)
            refresh_dropdowns()  # Update dropdown widgets from banner data

            log.info(f"🎯 Injected {len(player_options)} players and {len(round_options)} rounds into dropdowns")
            console_text.configure(state="normal")
            console_text.insert(tk.END, f"🎯 {len(player_options)} players | {len(round_options)} rounds injected\n")
            console_text.configure(state="disabled")

        except Exception as e:
            log.warning(f"⚠️ Failed to populate dropdowns: {e}")
            console_text.configure(state="normal")
            console_text.insert(tk.END, f"⚠️ Dropdown population failed: {e}\n")
            console_text.configure(state="disabled")

        banner.finish_loading()
        console_text.see(tk.END)

        # Save parsed_data to global or app scope (update as needed)
        global current_data
        current_data = parsed_data

    except Exception as e:
        log.error(f"❌ Parsing failed: {e}")
        console_text.configure(state="normal")
        console_text.insert(tk.END, f"❌ Parsing failed: {e}\n")
        console_text.configure(state="disabled")
        banner.finish_loading()
        console_text.see(tk.END)

log.info("📂 File selection and parsing function initialized")
# =============================================================================
# BLOCK 4: Buttons and Stats/Replay Wiring
# =============================================================================

def on_generate_stats():
    """
    Generate stats summary for selected player and round.
    """
    from cs2_parser.stats_summary import display_stats_summary

    player = player_var.get()
    round_ = round_var.get()

    log.info(f"📊 Generating stats for player: {player}, round: {round_}")
    console_text.configure(state="normal")
    console_text.insert(tk.END, f"📊 Generating stats for: {player}, Round: {round_}\n")
    console_text.configure(state="disabled")
    console_text.see(tk.END)

    try:
        display_stats_summary(stats_tab, current_data, player, round_)
    except Exception as e:
        log.error(f"❌ Stats generation failed: {e}")
        console_text.configure(state="normal")
        console_text.insert(tk.END, f"❌ Stats generation failed: {e}\n")
        console_text.configure(state="disabled")
        console_text.see(tk.END)


def on_replay_round():
    """
    Stub function to trigger replay of the selected round.
    """
    round_ = round_var.get()
    player = player_var.get()

    log.info(f"🎬 Replay requested for player: {player}, round: {round_}")
    console_text.configure(state="normal")
    console_text.insert(tk.END, f"🎬 Replay round requested: Player={player}, Round={round_} (stub)\n")
    console_text.configure(state="disabled")
    console_text.see(tk.END)

    # TODO: Implement replay logic here


def on_debug_view():
    """
    Stub function for debug overlay or trace log.
    """
    log.info("🧠 Debug view activated")
    console_text.configure(state="normal")
    console_text.insert(tk.END, "🧠 Debug view activated (stub)\n")
    console_text.configure(state="disabled")
    console_text.see(tk.END)


# Wire buttons on the bottom control panel
generate_stats_button = ttk.Button(bottom, text="🎯 Generate Stats", command=on_generate_stats)
generate_stats_button.pack(side="right", padx=10)

replay_round_button = ttk.Button(bottom, text="🎬 Replay Round", command=on_replay_round)
replay_round_button.pack(side="right")

debug_button = ttk.Button(bottom, text="🧠 Debug", command=on_debug_view)
debug_button.pack(side="right", padx=10)

log.info("🎮 Stats, Replay, Debug buttons wired")
# =============================================================================
# BLOCK 5: Menu Bar (File, Export, Help)
# =============================================================================

def show_about():
    from tkinter import messagebox
    about_text = (
        "CS2 Ancient Chinese Secrets – Carmack Edition\n"
        "Version: Alpha v0.0005-PATCHED\n"
        "Authors: Athlenia QA, pzr1H\n"
        "Project Start Date: July 1, 2025\n"
        "Description:\n"
        "Anti-cheat, Stat Analysis, and Demo Replay tools for CS2."
    )
    messagebox.showinfo("About CS2 ACS", about_text)


menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

# --- File Menu ---
file_menu = tk.Menu(menu_bar, tearoff=0)
file_menu.add_command(label="📂 Load Demo or JSON", command=select_and_parse_file)
file_menu.add_separator()
file_menu.add_command(label="❌ Exit", command=root.quit)
menu_bar.add_cascade(label="File", menu=file_menu)

# --- Export Menu ---
export_menu = tk.Menu(menu_bar, tearoff=0)
export_menu.add_command(label="💾 Export CSV", command=lambda: log.info("📤 Export CSV (stub)"))
export_menu.add_command(label="🧾 Export JSON", command=lambda: log.info("📤 Export JSON (stub)"))
export_menu.add_command(label="📑 Export PDF", command=lambda: log.info("📤 Export PDF (stub)"))
export_menu.add_command(label="🧠 Export Debug Log", command=lambda: log.info("📤 Export Debug Log (stub)"))
menu_bar.add_cascade(label="Export", menu=export_menu)

# --- Help Menu ---
help_menu = tk.Menu(menu_bar, tearoff=0)
help_menu.add_command(label="❓ About", command=show_about)
menu_bar.add_cascade(label="Help", menu=help_menu)

log.info("📋 Menu bar created with File, Export, Help")

# =============================================================================
# BLOCK 6: Console Output Logging Panel (Real-Time Log Capture)
# =============================================================================

console_frame = ttk.Frame(root)
console_frame.pack(fill="both", expand=True, padx=10, pady=5)

console_output = ScrolledText(console_frame, height=10, state="disabled", bg="black", fg="white")
console_output.pack(fill="both", expand=True)

class ConsoleHandler(logging.Handler):
    def emit(self, record):
        msg = self.format(record)
        console_output.configure(state="normal")
        console_output.insert("end", msg + "\n")
        console_output.configure(state="disabled")
        console_output.yview_moveto(1.0)

handler = ConsoleHandler()
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%H:%M:%S'))
log.addHandler(handler)
log.setLevel(logging.DEBUG)
log.info("📟 Console log panel initialized")

# =============================================================================
# BLOCK 7: File Selection + Parser Trigger + Dropdown Injection
# =============================================================================

def select_and_parse_file():
    """
    Opens file dialog, runs parser or JSON loader, updates GUI elements and logs.
    """
    from file_loader import run_parser
    from utils.data_sanitizer import get_schema_status

    file_path = filedialog.askopenfilename(
        title="Select CS2 Demo or Parsed JSON",
        filetypes=[("Demo or JSON Files", "*.dem *.json")]
    )

    if not file_path:
        log.info("❎ File selection cancelled.")
        return

    file_name = os.path.basename(file_path)
    file_size = os.path.getsize(file_path)
    log.info(f"📁 Selected file: {file_name} ({file_size / 1024:.2f} KB)")

    console_output.configure(state="normal")
    console_output.insert(tk.END, f"\n🔁 Parsing started: {file_name}\n")
    console_output.insert(tk.END, f"📦 Size: {file_size / 1024:.2f} KB\n")
    console_output.configure(state="disabled")
    console_output.see(tk.END)

    start_time = time.time()

    try:
        parsed_data = run_parser(file_path)
        duration = time.time() - start_time

        if not parsed_data:
            raise ValueError("Parsed data is empty or None")

        console_output.configure(state="normal")
        console_output.insert(tk.END, f"✅ Parsing completed in {duration:.2f}s\n")
        console_output.configure(state="disabled")

        # Check schema status
        schema_ok, issues = get_schema_status(parsed_data)
        console_output.configure(state="normal")
        if schema_ok:
            console_output.insert(tk.END, "🧼 Schema validation passed\n")
        else:
            console_output.insert(tk.END, f"⚠️ Schema issues: {issues}\n")
        console_output.configure(state="disabled")
        console_output.see(tk.END)

        # Inject dropdowns + log summary
        try:
            player_options = parse_player_dropdown(parsed_data.get("events", []))
            round_options = parse_round_dropdown(parsed_data.get("events", []))

            player_dropdown["menu"].delete(0, "end")
            round_dropdown["menu"].delete(0, "end")

            for player in player_options:
                player_dropdown["menu"].add_command(label=player, command=tk._setit(selected_player, player))

            for rnd in round_options:
                round_dropdown["menu"].add_command(label=rnd, command=tk._setit(selected_round, rnd))

            log.info(f"🎯 Injected {len(player_options)} players and {len(round_options)} rounds to dropdowns")
            console_output.configure(state="normal")
            console_output.insert(tk.END, f"🎯 {len(player_options)} players | {len(round_options)} rounds injected\n")
            console_output.configure(state="disabled")

        except Exception as e:
            log.warning(f"⚠️ Failed to populate dropdowns: {e}")
            console_output.configure(state="normal")
            console_output.insert(tk.END, f"⚠️ Dropdown population failed: {e}\n")
            console_output.configure(state="disabled")

        banner.finish_loading()  # ✅ Switch banner to color mode

    except Exception as e:
        log.error(f"❌ Parsing failed: {e}")
        console_output.configure(state="normal")
        console_output.insert(tk.END, f"❌ Parsing failed: {e}\n")
        console_output.configure(state="disabled")
        console_output.see(tk.END)

# =============================================================================
# BLOCK 8: Replay, Stats & Debug Buttons — Wireup + Console Logging
# =============================================================================

def replay_round():
    """
    Stub: Trigger navmesh or round replay overlay.
    """
    log.info("🎮 Replay round triggered")
    console_output.configure(state="normal")
    console_output.insert(tk.END, "🎮 Replay round requested (stub logic)\n")
    console_output.configure(state="disabled")
    console_output.see(tk.END)


def generate_stats():
    """
    Calls display_stats_summary from stats_summary.py using selected player and round.
    """
    from stats_summary import display_stats_summary

    try:
        player = selected_player.get()
        round_ = selected_round.get()

        log.info(f"📊 Generate stats: {player}, Round {round_}")
        console_output.configure(state="normal")
        console_output.insert(tk.END, f"📊 Generating stats for: {player}, Round {round_}\n")
        console_output.configure(state="disabled")
        console_output.see(tk.END)

        display_stats_summary(stats_tab, parsed_data, player, round_)

    except Exception as e:
        log.error(f"❌ Stats generation failed: {e}")
        console_output.configure(state="normal")
        console_output.insert(tk.END, f"❌ Stats generation failed: {e}\n")
        console_output.configure(state="disabled")
        console_output.see(tk.END)


def trigger_debug_view():
    """
    Stub for debug overlay / trace log.
    """
    log.info("🧠 Debug view activated")
    console_output.configure(state="normal")
    console_output.insert(tk.END, "🧠 Debug view activated (stub)\n")
    console_output.configure(state="disabled")
    console_output.see(tk.END)

# =============================================================================
# BLOCK 9: Dropdowns, Vars, Control Panel UI Setup (Player/Round Selectors + Buttons)
# =============================================================================

control_panel = ttk.Frame(root)
control_panel.pack(side="bottom", fill="x", padx=10, pady=5)

selected_player = tk.StringVar()
selected_round = tk.StringVar()

ttk.Label(control_panel, text="Player:").pack(side="left", padx=(10, 5))
player_dropdown = ttk.OptionMenu(control_panel, selected_player, "")
player_dropdown.pack(side="left")

ttk.Label(control_panel, text="Round:").pack(side="left", padx=(10, 5))
round_dropdown = ttk.OptionMenu(control_panel, selected_round, "")
round_dropdown.pack(side="left")

ttk.Button(control_panel, text="🎯 Generate Stats", command=generate_stats).pack(side="right", padx=10)
ttk.Button(control_panel, text="🎬 Replay Round", command=replay_round).pack(side="right")

ttk.Button(control_panel, text="🧠 Debug", command=trigger_debug_view).pack(side="right", padx=10)

# =============================================================================
# BLOCK 10: Final Setup — Tab Injection, Banner, Mainloop
# =============================================================================

try:
    display_event_log(event_log_tab, parsed_data, banner=banner)
    display_chat_summary(chat_tab, parsed_data)
    display_stats_summary(stats_tab, parsed_data)
    display_damage_summary(damage_tab, parsed_data)
except Exception as e:
    log.warning(f"⚠️ Tab injection failed: {e}")

log.info("🚀 GUI launch complete.")
root.mainloop()
# =============================================================================
# EOF Final Setup — Tab Injection, Banner, Mainloop = TLOC 567 pzr1H
# =============================================================================