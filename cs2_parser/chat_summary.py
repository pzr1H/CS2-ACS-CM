#!/usr/bin/env python3
# =============================================================================
# chat_summary.py — Chat Message Extractor + Summary Renderer
# Timestamp-TOP: 2025-07-26T12:10-EDT | Version: v0.0001-LOCKED
# Source of Truth: parsed_data["events"] → event["type"] == "chat_message"
# =============================================================================

import logging
log = logging.getLogger(__name__)
from typing import List, Dict, Any

try:
    from cross_module_debugging import trace_log
except ImportError:
    def trace_log(func): return func

log = logging.getLogger(__name__)
log.info("💬 chat_summary.py loaded")

# =============================================================================
# BLOCK 1: Extract Chat Messages
# =============================================================================
@trace_log
def extract_chat_messages(event_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filters chat_message events and returns cleaned chat dicts.
    """
    messages = []

    for event in event_data:
        if event.get("type") != "chat_message":
            continue

        msg = {
            "time": event.get("seconds", 0),
            "player": event.get("player", {}).get("name", "Unknown"),
            "team": event.get("player", {}).get("team", "Unknown"),
            "text": event.get("text", ""),
        }
        messages.append(msg)

    if not messages:
        log.warning("📭 No chat messages found")
    return messages

# =============================================================================
# BLOCK 2: Format Chat as Plain Text
# =============================================================================
@trace_log
def format_chat_log(chat_messages: List[Dict[str, Any]]) -> str:
    """
    Returns formatted plain text chat log.
    """
    lines = []
    for msg in chat_messages:
        ts = f"[{msg['time']:>5.1f}s]"
        lines.append(f"{ts} {msg['player']} ({msg['team']}): {msg['text']}")

    return "\n".join(lines)
# =============================================================================
# BLOCK 3: GUI Controller for Chat Tab
# =============================================================================
@trace_log
def display_chat_summary(parent, data: Dict[str, Any]) -> None:
    """
    GUI controller to render chat summary in a tabbed ScrolledText box.
    Injects formatted chat if available; otherwise warns.
    """
    from tkinter.scrolledtext import ScrolledText
    for widget in parent.winfo_children():
        widget.destroy()

    events = data.get("events", [])
    chat_messages = extract_chat_messages(events)

    scrolled = ScrolledText(parent, wrap="word", font=("Courier", 10))
    scrolled.pack(fill="both", expand=True)

    if not chat_messages:
        scrolled.insert("end", "📭 No chat messages found in this match.\n")
    else:
        scrolled.insert("end", format_chat_log(chat_messages))

    scrolled.configure(state="disabled")  # Make it read-only
# =============================================================================
# EOF: chat_summary.py — TLOC: 86 | PATCHED v0.0002 | Author: Athlenia QA
# =============================================================================