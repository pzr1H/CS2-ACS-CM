#!/usr/bin/env python3
# =============================================================================
# navmesh_utils.py — Navmesh & Pathing Utility Toolkit
# Timestamp‑TOP: 2025‑07‑14T | v0.1‑stub
# =============================================================================

import logging
from typing import List, Dict, Tuple, Optional

log = logging.getLogger(__name__)

# =============================================================================
# NAVMESH STRUCTURE STUBS
# =============================================================================

class PathNode:
    """
    Represents a point in a navmesh path.
    Each node includes position, tick timestamp, and optional action label.
    """
    def __init__(self, x: float, y: float, z: float, tick: int, label: str = ""):
        self.x = x
        self.y = y
        self.z = z
        self.tick = tick
        self.label = label

    def to_dict(self):
        return {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "tick": self.tick,
            "label": self.label
        }

    def __repr__(self):
        return f"PathNode(x={self.x}, y={self.y}, z={self.z}, tick={self.tick}, label='{self.label}')"
#EOB 1 LOC 39 PZR1H
# ----------------------------------------------------------------------
# Movement Path Extractor
# ----------------------------------------------------------------------

def extract_movement_sequence(events: list, round_num: int, player_id: str) -> list:
    """
    Extracts the ordered (tick, position) movement path for the given player in the selected round.
    Returns a list of dictionaries: { tick, x, y, z, velocity }.
    """
    path = []
    for ev in events:
        if ev.get("type") == "player_position" and \
           ev.get("round") == round_num and \
           ev.get("steam_id") == player_id:
            path.append({
                "tick": ev.get("tick"),
                "x": ev.get("x"),
                "y": ev.get("y"),
                "z": ev.get("z"),
                "velocity": ev.get("velocity", 0)
            })
    return path

# ----------------------------------------------------------------------
# Aim Trace Generator (for hitgroup / POV tracing)
# ----------------------------------------------------------------------

def extract_aim_trace(events: list, round_num: int, player_id: str) -> list:
    """
    Generates a timeline of crosshair angles and bullet impacts (if any).
    Returns a list of (tick, yaw, pitch, impact_position).
    """
    trace = []
    for ev in events:
        if ev.get("type") == "view_angles" and \
           ev.get("round") == round_num and \
           ev.get("steam_id") == player_id:
            trace.append({
                "tick": ev.get("tick"),
                "yaw": ev.get("yaw"),
                "pitch": ev.get("pitch"),
                "impact": None
            })

        elif ev.get("type") == "bullet_impact" and \
             ev.get("round") == round_num and \
             ev.get("steam_id") == player_id:
            trace.append({
                "tick": ev.get("tick"),
                "yaw": None,
                "pitch": None,
                "impact": {
                    "x": ev.get("x"),
                    "y": ev.get("y"),
                    "z": ev.get("z")
                }
            })

    return trace

# ----------------------------------------------------------------------
# Input Stream Extractor (keys/mouse timeline)
# ----------------------------------------------------------------------

def extract_input_stream(events: list, round_num: int, player_id: str) -> list:
    """
    Extracts a list of input events (keys, mouse actions) for replay or overlay generation.
    Returns a list of { tick, action, value }.
    """
    inputs = []
    for ev in events:
        if ev.get("round") == round_num and ev.get("steam_id") == player_id:
            if ev.get("type") in ("keypress", "mouse_click", "jump", "duck", "move"):
                inputs.append({
                    "tick": ev.get("tick"),
                    "action": ev.get("type"),
                    "value": ev.get("value", ev.get("key", ev.get("button", "")))
                })
    return inputs
#EOB2 119 LOC - pzr1H
# ----------------------------------------------------------------------
# Navmesh Exporter (Final Payload Builder)
# ----------------------------------------------------------------------

def export_navmesh_payload(movement, aim_trace, inputs, metadata=None) -> dict:
    """
    Combines movement, aim, and input into a structured navmesh payload.
    Optionally includes metadata (player name, round, steamID, match hash).
    """
    return {
        "meta": metadata or {},
        "movement_sequence": _sanitize_movement_sequence(movement),
        "aim_trace": aim_trace,
        "input_stream": inputs,
        "version": "1.0.0"
    }

# ----------------------------------------------------------------------
# Sanitize or Deduplicate Movement Sequence
# ----------------------------------------------------------------------

def _sanitize_movement_sequence(movement: list) -> list:
    """
    Remove redundant positions, sort by tick, and smooth glitches if needed.
    """
    if not movement:
        return []

    cleaned = []
    seen = set()
    for m in movement:
        ident = (m["x"], m["y"], m["z"], m["tick"])
        if ident not in seen:
            cleaned.append(m)
            seen.add(ident)

    return sorted(cleaned, key=lambda x: x["tick"])
#EOB3 LOC 157 pzr1h

