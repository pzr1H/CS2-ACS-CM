#!/usr/bin/env python3
# =============================================================================
# event_log.py — CS2 ACS Event Log Renderer with Filtering + Export + Banner Injection
# Timestamp: 2025‑07‑26 | Author: Athlenia QA + pzr1H | PATCHED v2.3-R3
# =============================================================================

import logging
log = logging.getLogger(__name__)
import tkinter as tk
from tkinter import ttk

# =============================================================================
# Block 0: Logging + Trace Setup
# =============================================================================
try:
    from cross_module_debugging import trace_log
except ImportError:
    def trace_log(func):
        return func

log = logging.getLogger(__name__)
log.info("📋 Event Log module initialized")  # ✅ Replaced invalid trace_log()

# =============================================================================
# Block 1: Controller — Full Tab Layout with Dropdown and Export
# =============================================================================

def event_log_tab_controller(parent: tk.Frame, data: dict, banner=None) -> None:
    """
    Creates the event log tab UI, including filter dropdown, Treeview, and export buttons.
    Accepts optional banner for fallback dropdown injection.
    """
    for widget in parent.winfo_children():
        widget.destroy()

    all_events = data.get("events", [])
    event_types = sorted(set(ev.get("type", "Unknown") for ev in all_events))
    event_types.insert(0, "All")  # Add 'All' option

    top_frame = ttk.Frame(parent)
    top_frame.grid(row=0, column=0, sticky="ew", pady=5)
    parent.grid_columnconfigure(0, weight=1)

    selected_type = tk.StringVar(value="All")
    ttk.Label(top_frame, text="Filter by Event Type:").pack(side="left", padx=(10, 5))
    filter_dropdown = ttk.OptionMenu(top_frame, selected_type, "All", *event_types)
    filter_dropdown.pack(side="left")

    tree = ttk.Treeview(parent)
    tree.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
    parent.grid_rowconfigure(1, weight=1)

    vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    vsb.grid(row=1, column=1, sticky="ns")
    tree.configure(yscrollcommand=vsb.set)

    def refresh_tree(*args):
        selected = selected_type.get()
        filtered = [ev for ev in all_events if selected == "All" or ev.get("type") == selected]
        _render_event_tree(tree, filtered)

    selected_type.trace_add("write", refresh_tree)

    _render_event_tree(tree, all_events)

    # Inject player/round capture from TreeView
    try:
        from utils.dropdown_utils import parse_player_dropdown
        players = extract_players_from_event_tree(tree)
        rounds = extract_rounds_from_event_tree(tree)
        if banner and hasattr(banner, "capture_event_players"):
            banner.capture_event_players(parse_player_dropdown(players), rounds)
        else:
            log.debug("⚠️ No banner object passed to controller. Skipping capture.")
    except Exception as e:
        log.warning(f"⚠️ Failed to capture dropdown data from TreeView: {e}")

    # Export controls
    export_frame = ttk.Frame(parent)
    export_frame.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)
    export_frame.grid_columnconfigure(0, weight=1)

    def export_csv():
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[["CSV Files", "*.csv"]])
        if not path:
            return
        try:
            import csv
            with open(path, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Tick", "Round", "Type", "Name", "Detail"])
                for row in tree.get_children():
                    writer.writerow(tree.item(row)["values"])
            log.info(f"✅ Exported events to CSV: {path}")
        except Exception as e:
            log.error(f"❌ Failed to export CSV: {e}")

    def export_json():
        from tkinter import filedialog
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[["JSON Files", "*.json"]])
        if not path:
            return
        try:
            import json
            export = []
            for row in tree.get_children():
                vals = tree.item(row)["values"]
                export.append({
                    "tick": vals[0], "round": vals[1], "type": vals[2],
                    "name": vals[3], "detail": vals[4]
                })
            with open(path, "w", encoding='utf-8') as f:
                json.dump(export, f, indent=2)
            log.info(f"✅ Exported events to JSON: {path}")
        except Exception as e:
            log.error(f"❌ Failed to export JSON: {e}")

    ttk.Button(export_frame, text="💾 Export to CSV", command=export_csv).pack(side="left", padx=10)
    ttk.Button(export_frame, text="💾 Export to JSON", command=export_json).pack(side="left")

# =============================================================================
# Treeview Renderer — Just Content
# =============================================================================

def _render_event_tree(tree: ttk.Treeview, events: list) -> None:
    """
    Populate the given Treeview widget with structured CS2 event data.
    """
    log.debug(f"▶︎ _render_event_tree called, events count={len(events)}")
    tree.delete(*tree.get_children())

    columns = ["tick", "round", "type", "name", "detail"]
    tree.configure(columns=columns, show="headings")

    for col in columns:
        tree.heading(col, text=col.capitalize())
        tree.column(col, width=100, anchor="center")

    for ev in events:
        try:
            ev_type = ev.get('type', 'Unknown')
            tick = ev.get('tick', 0)
            rnd = ev.get('round', -1)
            name = ev.get('user_name') or ev.get('name') or ''
            details = ev.get('details', {})
            detail_str = details.get("string", str(details)) if isinstance(details, dict) else str(details)
            row = [tick, rnd, ev_type, name, detail_str]
            tree.insert('', 'end', values=row)
        except Exception as e:
            log.warning(f"⚠️ Event parsing error: {e}")
            tree.insert('', 'end', values=["", "", "ERROR", "", str(e)])

# =============================================================================
# Player Extractor for TreeView → Dropdown
# =============================================================================

def extract_players_from_event_tree(tree: ttk.Treeview) -> list:
    log.info("🔍 Extracting players from TreeView")
    seen = set()
    players = []

    for row_id in tree.get_children():
        try:
            values = tree.item(row_id)["values"]
            if len(values) < 4:
                continue
            name = values[3].strip()
            detail = values[4]

            import re
            sid_match = re.search(r"(STEAM_[0-5]:[01]:\d+|7656\d{13,})", str(detail))
            steamid = sid_match.group(1) if sid_match else ""

            key = f"{name}-{steamid}"
            if name and key not in seen:
                players.append({"name": name, "steamid": steamid})
                seen.add(key)
        except Exception as e:
            log.warning(f"⚠️ Failed TreeView player extraction: {e}")

    log.info(f"✅ Found {len(players)} players from event log")
    return players

# =============================================================================
# Round Extractor for TreeView → Dropdown
# =============================================================================

def extract_rounds_from_event_tree(tree: ttk.Treeview) -> list:
    log.info("🧪 Extracting rounds from TreeView")
    seen = set()
    rounds = []

    for row_id in tree.get_children():
        try:
            values = tree.item(row_id)["values"]
            if len(values) < 2:
                continue
            rnd = int(values[1])
            if rnd not in seen:
                seen.add(rnd)
                rounds.append(rnd)
        except Exception as e:
            log.warning(f"⚠️ Failed to extract round: {e}")

    log.info(f"✅ Found {len(rounds)} rounds from event log")
    return sorted(rounds)

# =============================================================================
# Export Alias for main.py
# =============================================================================
display_event_log = event_log_tab_controller
# event_log.py or utils/event_summary.py

def generate_event_summary(data):
    if not data or "events" not in data:
        return ["⚠️ No events found in data to summarize"]

    events = data["events"]
    total_events = len(events)
    event_type_counts = {}

    for event in events:
        etype = event.get("type", "Unknown")
        event_type_counts[etype] = event_type_counts.get(etype, 0) + 1

    lines = [f"✅ Parsed file with {total_events} events total", "Event Type Counts:"]
    for etype, count in sorted(event_type_counts.items()):
        lines.append(f"  • {etype}: {count}")

    return lines
# =============================================================================
# EOF — event_log.py | PATCHED v2.3-R3 | TLOC: 216 pzr1H
# =============================================================================
