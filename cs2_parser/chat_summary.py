#!/usr/bin/env python3
# =============================================================================
# chat_summary.py — GUI Display for In-Game Chat Logs
# =============================================================================

import logging
import tkinter as tk
from tkinter import ttk
from typing import List, Dict, Any

log = logging.getLogger(__name__)

CHAT_COLUMNS = ["tick", "player", "message"]

COLUMN_ALIASES = {
    "tick": "Tick",
    "player": "Player",
    "message": "Message"
}

# =============================================================================
# BLOCK 1: Chat Log Treeview Construction
# =============================================================================

def generate_chat_summary(parent_tab: ttk.Notebook, chat_data: List[Dict[str, Any]]):
    """
    Constructs the Chat Summary tab in the GUI.

    Args:
        parent_tab (ttk.Notebook): Notebook to attach the chat tab to.
        chat_data (List[Dict[str, Any]]): Parsed chat log entries.
    """
    log.info("💬 Building Chat Summary tab...")

    frame = ttk.Frame(parent_tab)
    parent_tab.add(frame, text="💬 Chat Summary")

    tree = ttk.Treeview(frame, columns=CHAT_COLUMNS, show="headings", height=20)
    scroll_y = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll_y.set)

    for col in CHAT_COLUMNS:
        header = COLUMN_ALIASES.get(col, col.title())
        width = 80 if col != "message" else 400
        tree.heading(col, text=header)
        tree.column(col, anchor="center", width=width)

    tree.grid(row=0, column=0, sticky="nsew")
    scroll_y.grid(row=0, column=1, sticky="ns")

    frame.grid_rowconfigure(0, weight=1)
    frame.grid_columnconfigure(0, weight=1)

    for entry in chat_data:
        values = [entry.get(col, "") for col in CHAT_COLUMNS]
        tree.insert("", "end", values=values)

    log.info(f"✅ Loaded {len(chat_data)} chat entries into Treeview.")

# =============================================================================
# BLOCK 2: Optional Tick Trace from Chat Logs
# =============================================================================

def bind_chat_tick_trace(tree: ttk.Treeview):
    """
    Binds event to print selected tick from chat logs — useful for replay alignment or highlighting.
    """
    def on_select(event):
        selected = tree.focus()
        if not selected:
            return
        values = tree.item(selected)["values"]
        tick = values[0] if values else None
        if tick:
            log.info(f"💬 Tick from selected chat entry: {tick}")
            print(f"[CHAT TRACE] Selected Tick: {tick}")

    tree.bind("<<TreeviewSelect>>", on_select)
