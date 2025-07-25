#!/usr/bin/env python3
# =============================================================================
# chat_summary.py — Chat Log Parser for CS2 ACS GUI
# Timestamp‑TOP: 2025‑07‑25 | v1.2‑SANITIZED‑CANONICAL
# =============================================================================

import tkinter as tk
from tkinter import ttk
import logging
from utils.steam_utils import to_steam2

log = logging.getLogger(__name__)

def display_chat_summary(parent, data):
    """
    Populates the `parent` frame with chat messages pulled from event data.
    Columns: Mode | Sender | Message | Tick
    """
    for w in parent.winfo_children():
        w.destroy()

    columns = ("mode", "sender", "message", "tick")
    tree = ttk.Treeview(parent, columns=columns, show="headings", height=20)

    for col in columns:
        tree.heading(col, text=col.capitalize())

    tree.column("mode", width=60, anchor="center")
    tree.column("sender", width=160, anchor="center")
    tree.column("message", width=480, anchor="w")
    tree.column("tick", width=80, anchor="e")

    vsb = ttk.Scrollbar(parent, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=vsb.set)

    tree.grid(row=0, column=0, sticky="nsew")
    vsb.grid(row=0, column=1, sticky="ns")

    parent.grid_rowconfigure(0, weight=1)
    parent.grid_columnconfigure(0, weight=1)

    chat_events = [ev for ev in data.get("events", []) if ev.get("type") == "chat_message"]
    log.debug(f"▶ display_chat_summary called, chatEvents count = {len(chat_events)}")

    # Build mapping from Steam2 ID to display names
    steamid_to_name = {}
    for ev in data.get("events", []):
        if ev.get("type") == "events.PlayerInfo":
            sid = ev.get("steamid") or ev.get("steamid64")
            name = ev.get("name") or ev.get("player_name")
            if sid and name:
                try:
                    steamid_to_name[to_steam2(int(sid))] = name
                except Exception as e:
                    log.warning(f"⚠️ SteamID parse failed for PlayerInfo: {sid} — {e}")

    for ev in chat_events:
        mode = ev.get("mode", "all").capitalize()
        sender_id = ev.get("sender_steamid64") or ev.get("sender_steamid") or "?"
        message = ev.get("message", "").strip()
        tick = ev.get("tick", 0)

        steam2 = to_steam2(int(sender_id)) if sender_id.isdigit() else "?"
        sender_name = steamid_to_name.get(steam2, ev.get("sender_name", "<unknown>"))

        tree.insert("", "end", values=(mode, sender_name, message, tick))

    log.debug("✅ display_chat_summary complete.")

# =============================================================================
# EOF — chat_summary.py (v1.2-SANITIZED-CANONICAL)
# - Fully patched version w/ ID fallback and trace logging
# - Columns: Mode | Sender | Message | Tick
# - Vertical scrollbar added; Grid layout enforced
# - Steam2 name mapping via PlayerInfo
# TLOC = 77
# =============================================================================
