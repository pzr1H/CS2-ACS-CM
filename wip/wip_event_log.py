#!/usr/bin/env python3
# =============================================================================
# event_log.py — CS2 ACS Event Log Renderer with Filtering + Export
# Timestamp: 2025‑07‑26 | Author: Athlenia QA + pzr1H | PATCHED v1
# =============================================================================

import logging
import tkinter as tk
from tkinter import ttk

# =============================================================================
# Block 0: Logging + Trace Setup
# =============================================================================
try:
    from cross_module_debugging import trace_log
except ImportError:
    def trace_log(func): return func

log = logging.getLogger(__name__)  # ✅ FIXED: restore scoped logger
log.info("📋 Event Log module initialized")

# =============================================================================
# Block 1: Controller — Full Tab Layout with Dropdown and Export
# =============================================================================

@trace_log
def event_log_tab_controller(parent: tk.Frame, data: dict, banner=None) -> None:
    """
    Creates the event log tab UI, including Treeview for all events,
    and updates dropdowns for player/rounds by parsing Treeview nodes.
    """
    for widget in parent.winfo_children():
        widget.destroy()

    tree = ttk.Treeview(parent, columns=("timestamp", "type", "steamid", "name", "event"), show="tree headings")
    tree.heading("#0", text="Event")
    tree.heading("timestamp", text="Timestamp")
    tree.heading("type", text="Type")
    tree.heading("steamid", text="SteamID")
    tree.heading("name", text="Name")
    tree.heading("event", text="Event Detail")

    # Populate Treeview
    try:
        events = data.get("events", [])
        rounds = {}
        for event in events:
            round_number = event.get("round", 0)
            if round_number not in rounds:
                rounds[round_number] = tree.insert("", "end", text=f"Round {round_number}", open=True)
            parent_node = rounds[round_number]

            steam_id = event.get("steam_id", "")
            name = event.get("name", "")
            timestamp = event.get("seconds", 0)
            event_type = event.get("type", "unknown")
            event_text = str(event)

            tree.insert(parent_node, "end", values=(timestamp, event_type, steam_id, name, event_text))

        tree.pack(fill="both", expand=True)
        log.info(f"🧩 Event Log loaded with {len(events)} events")

    except Exception as e:
        log.exception("❌ Failed to populate event log")

    # =============================================================================
    # Post-Population: Extract Players + Rounds → Pass back to parent GUI for dropdowns
    # =============================================================================

    try:
        from utils.dropdown_utils import extract_players_from_treeview, extract_rounds_from_treeview

        players = extract_players_from_treeview(tree)
        rounds = extract_rounds_from_treeview(tree)

        log.info(f"🎯 Extracted Players from Event Log: {players}")
        log.info(f"🎯 Extracted Rounds from Event Log: {rounds}")

        if hasattr(parent.master, "update_dropdowns_from_tree"):
            parent.master.update_dropdowns_from_tree(players, rounds)

    except Exception as e:
        log.exception("❌ Failed to extract player/rounds from event log")

# =============================================================================
# EOF — TLOC: 88 | v1 PATCHED — Dropdowns + Tree Integration | Athlenia QA
# =============================================================================
