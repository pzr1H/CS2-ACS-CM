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


def generate_chat_summary(tab_frame, data):
    """Working chat summary display"""
    try:
        import tkinter as tk
        from tkinter import ttk
        
        # Clear the frame
        for widget in tab_frame.winfo_children():
            widget.destroy()
        
        # Create main container
        main_frame = tk.Frame(tab_frame, bg="black")
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Title
        title_label = tk.Label(main_frame, text="Chat Analysis", 
                             fg="cyan", bg="black", font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Create text widget for chat
        text_frame = tk.Frame(main_frame, bg="black")
        text_frame.pack(fill="both", expand=True)
        
        text_widget = tk.Text(text_frame, bg="#1a1a1a", fg="white", 
                            font=("Consolas", 10), wrap=tk.WORD)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient="vertical", command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        # Pack
        text_widget.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Look for chat events
        chat_events = []
        events = data.get("events", []) if isinstance(data, dict) else []
        
        for event in events:
            if isinstance(event, dict):
                event_type = event.get("type", "")
                if "chat" in event_type.lower() or "say" in event_type.lower():
                    chat_events.append(event)
        
        # Populate chat
        if chat_events:
            for event in chat_events:
                user = event.get("user", {})
                message = event.get("message", "")
                time_val = event.get("tick", "")
                
                if isinstance(user, dict):
                    name = user.get("name", "Unknown")
                else:
                    name = "Unknown"
                
                text_widget.insert(tk.END, f"[{time_val}] {name}: {message}")
        else:
            text_widget.insert(tk.END, "No chat messages found in demo.")
            text_widget.insert(tk.END, "This may be because:")
            text_widget.insert(tk.END, "• Demo has no chat activity")
            text_widget.insert(tk.END, "• Chat events not captured by parser")
        
        text_widget.config(state="disabled")
        
        log.info(f"✅ Chat summary populated with {len(chat_events)} messages")
        
    except Exception as e:
        import tkinter as tk
        log.error(f"Chat summary error: {e}")
        error_label = tk.Label(tab_frame, text=f"Chat Error: {str(e)}", 
                             fg="red", bg="black")
        error_label.pack(pady=20)

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
