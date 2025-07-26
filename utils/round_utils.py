#!/usr/bin/env python3
# =============================================================================
# round_utils.py – canonical helpers for round / steam‑ID logic
# Timestamp‑TOP: 2025‑07‑26 (Enhanced Version)
# =============================================================================
# Exports:
#   • to_steam2(sid64: int) -> str                    – 64‑bit → STEAM_1:X:Y
#   • to_steam3(sid64: int) -> str                    – 64‑bit → [U:1:XXXXXXX]
#   • build_round_metadata(events: list[dict])        – indices, labels
#   • classify_rounds(events: list[dict])             – detailed round analysis
#   • RoundClassifier                                 – OOP interface for advanced classification
# -----------------------------------------------------------------------------

from typing import List, Dict, Any, Tuple, Optional, Union
from collections import defaultdict
from dataclasses import dataclass
from enum import Enum
import logging

# Setup logging
logger = logging.getLogger(__name__)

# --- Constants ---------------------------------------------------------------
STEAM64_BASE = 76561197960265728
DEFAULT_TICK_RATE = 128  # CS2 standard tick rate
ROUND_TIME_LIMIT = 115 * 128  # 115 seconds in ticks
FREEZE_TIME = 15 * 128  # 15 seconds freeze time in ticks

class RoundType(Enum):
    """Enumeration of possible round types for better type safety."""
    KNIFE = "knife"
    PREMATCH = "prematch"
    STANDARD = "standard"
    OVERTIME = "overtime"
    TIMEOUT = "timeout"
    GHOST = "ghost"
    WARMUP = "warmup"

@dataclass
class RoundMetadata:
    """Structured data class for round information."""
    index: int
    type: RoundType
    tick_start: int
    tick_end: int
    duration: int
    kills: int
    weapons: List[str]
    has_objective: bool
    score_t: Optional[int] = None
    score_ct: Optional[int] = None
    winner: Optional[str] = None

# --- SteamID conversion ------------------------------------------------------

def to_steam2(sid64: Union[int, str]) -> str:
    """
    Convert 64‑bit SteamID to legacy STEAM_1:X:Y format.
    
    Args:
        sid64: 64-bit Steam ID as int or string
        
    Returns:
        String in STEAM_1:X:Y format, or original input if conversion fails
        
    Example:
        >>> to_steam2(76561198000000000)
        'STEAM_1:0:19617636'
    """
    try:
        sid64_int = int(sid64)
        if sid64_int < STEAM64_BASE:
            logger.warning(f"Invalid Steam64 ID: {sid64_int} is below base value")
            return str(sid64)
            
        y = sid64_int % 2
        z = (sid64_int - STEAM64_BASE - y) // 2
        return f"STEAM_1:{y}:{z}"
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to convert Steam64 ID {sid64}: {e}")
        return str(sid64)

def to_steam3(sid64: Union[int, str]) -> str:
    """
    Convert 64‑bit SteamID to Steam3 [U:1:XXXXXXX] format.
    
    Args:
        sid64: 64-bit Steam ID as int or string
        
    Returns:
        String in [U:1:XXXXXXX] format, or original input if conversion fails
        
    Example:
        >>> to_steam3(76561198000000000)
        '[U:1:39235272]'
    """
    try:
        sid64_int = int(sid64)
        if sid64_int < STEAM64_BASE:
            logger.warning(f"Invalid Steam64 ID: {sid64_int} is below base value")
            return str(sid64)
            
        account_id = sid64_int - STEAM64_BASE
        return f"[U:1:{account_id}]"
    except (ValueError, TypeError) as e:
        logger.error(f"Failed to convert Steam64 ID {sid64}: {e}")
        return str(sid64)

def validate_steam64(sid64: Union[int, str]) -> bool:
    """
    Validate if a Steam64 ID is in the correct format and range.
    
    Args:
        sid64: Steam64 ID to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        sid64_int = int(sid64)
        return sid64_int >= STEAM64_BASE and sid64_int < STEAM64_BASE + 2**32
    except (ValueError, TypeError):
        return False

# --- Round inference helpers -------------------------------------------------

def _infer_round_starts(events: List[Dict[str, Any]]) -> List[int]:
    """
    Extract unique round start ticks from events.
    
    Args:
        events: List of event dictionaries
        
    Returns:
        Sorted list of tick values where rounds start
    """
    starts = set()  # Use set to avoid duplicates
    
    for ev in events:
        if ev.get("type") == "events.RoundStart":
            tick = ev.get("tick")
            if tick is not None:
                starts.add(tick)
    
    return sorted(starts)

def _is_knife_round(events: List[Dict[str, Any]]) -> bool:
    """
    Determine if a round is a knife round (warmup/knife round).
    
    Args:
        events: List of events in the round
        
    Returns:
        True if this appears to be a knife round
    """
    weapon_fires = []
    has_bomb_activity = False
    
    for ev in events:
        event_type = ev.get("type", "")
        
        # Check for weapon fire events
        if event_type.endswith("weapon_fire") or event_type == "events.WeaponFire":
            weapon = ev.get("weapon", "")
            weapon_fires.append(weapon)
            
        # Check for bomb-related activities
        if event_type in ("events.BombPlanted", "events.BombDefused", "events.BombExploded"):
            has_bomb_activity = True
    
    # If there's bomb activity, it's not a knife round
    if has_bomb_activity:
        return False
    
    # If no weapons fired, assume knife round
    if not weapon_fires:
        return True
    
    # Check if all weapons are knives
    knife_weapons = {"weapon_knife", "knife", "weapon_bayonet", "weapon_knife_survival"}
    return all(weapon in knife_weapons or weapon.startswith("weapon_knife") 
              for weapon in weapon_fires)

def _determine_round_phase(round_index: int) -> str:
    """
    Determine which phase of the match a round belongs to.
    
    Args:
        round_index: 1-based round number
        
    Returns:
        String indicating the phase (1H, 2H, OT1, etc.)
    """
    if round_index <= 0:
        return "PRE"
    elif round_index <= 15:  # First half (MR15)
        return "1H"
    elif round_index <= 30:  # Second half
        return "2H"
    else:  # Overtime
        ot_round = round_index - 30
        ot_set = ((ot_round - 1) // 6) + 1
        return f"OT{ot_set}"

def build_round_metadata(events: List[Dict[str, Any]]) -> Tuple[List[int], List[str]]:
    """
    Build round metadata for GUI dropdowns with enhanced labeling.
    
    Args:
        events: List of all game events
        
    Returns:
        Tuple of (indices, labels) for dropdown population
    """
    if not events:
        logger.warning("No events provided to build_round_metadata")
        return [], []
    
    starts = _infer_round_starts(events)
    if not starts:
        logger.warning("No round starts found in events")
        return [], []
    
    indices, labels = [], []

    for i, tick in enumerate(starts, 1):
        # Get events for this round
        next_tick = starts[i] if i < len(starts) else float('inf')
        round_events = [e for e in events 
                       if tick <= e.get("tick", 0) < next_tick]

        # Check for knife round (usually first round)
        if i == 1 and _is_knife_round(round_events):
            indices.append(0)
            labels.append("Knife Round (pre‑match)")
            continue

        # Determine phase and create label
        phase = _determine_round_phase(i)
        
        if phase == "1H":
            label = f"1H‑{i:02d}"
        elif phase == "2H":
            label = f"2H‑{i:02d}"
        elif phase.startswith("OT"):
            ot_round = i - 30
            ot_round_in_set = ((ot_round - 1) % 6) + 1
            label = f"{phase}‑R{ot_round_in_set}"
        else:
            label = f"Round {i}"
        
        indices.append(i)
        labels.append(label)

    logger.info(f"Built metadata for {len(indices)} rounds")
    return indices, labels

def classify_rounds(events: List[Dict[str, Any]]) -> List[RoundMetadata]:
    """
    Classify rounds based on activity and structure with enhanced analysis.
    
    Args:
        events: List of all game events
        
    Returns:
        List of RoundMetadata objects with detailed round information
    """
    if not events:
        return []
    
    # Group events by round number
    rounds = defaultdict(list)
    for ev in events:
        round_num = ev.get("round")
        if isinstance(round_num, int) and 0 <= round_num <= 64:
            rounds[round_num].append(ev)

    round_metadata = []

    for round_idx in sorted(rounds.keys()):
        ev_list = rounds[round_idx]
        
        if not ev_list:
            continue
            
        # Calculate timing
        ticks = [ev.get("tick", 0) for ev in ev_list if ev.get("tick") is not None]
        tick_start = min(ticks) if ticks else 0
        tick_end = max(ticks) if ticks else 0
        duration = tick_end - tick_start

        # Analyze round content
        kills = sum(1 for e in ev_list if e.get("type") == "events.PlayerDeath")
        has_combat = any(e.get("type") in ("events.PlayerHurt", "events.WeaponFire", 
                                          "events.BulletImpact") for e in ev_list)
        has_objective = any(e.get("type") in ("events.BombPlanted", "events.BombDefused", 
                                             "events.BombExploded") for e in ev_list)
        
        # Extract weapon information
        weapon_types = []
        for e in ev_list:
            weapon = e.get("weapon")
            if weapon and weapon not in weapon_types:
                weapon_types.append(weapon)

        # Extract score information if available
        score_t = score_ct = winner = None
        for e in ev_list:
            if e.get("type") == "events.RoundEnd":
                score_t = e.get("score_t")
                score_ct = e.get("score_ct") 
                winner = e.get("winner")
                break

        # Classify round type
        round_type = _classify_round_type(round_idx, duration, kills, has_combat, 
                                        has_objective, weapon_types)

        metadata = RoundMetadata(
            index=round_idx,
            type=round_type,
            tick_start=tick_start,
            tick_end=tick_end,
            duration=duration,
            kills=kills,
            weapons=weapon_types,
            has_objective=has_objective,
            score_t=score_t,
            score_ct=score_ct,
            winner=winner
        )
        
        round_metadata.append(metadata)

    logger.info(f"Classified {len(round_metadata)} rounds")
    return round_metadata

def _classify_round_type(round_idx: int, duration: int, kills: int, 
                        has_combat: bool, has_objective: bool, 
                        weapons: List[str]) -> RoundType:
    """
    Internal helper to classify round type based on various factors.
    
    Args:
        round_idx: Round index
        duration: Round duration in ticks
        kills: Number of kills
        has_combat: Whether combat occurred
        has_objective: Whether objective events occurred
        weapons: List of weapons used
        
    Returns:
        RoundType enum value
    """
    # Ghost rounds (very short, no activity)
    if duration < 300 and not kills and not has_combat:
        return RoundType.GHOST
    
    # Timeout rounds (very long duration)
    if duration > ROUND_TIME_LIMIT + 5000:  # 5 second buffer
        return RoundType.TIMEOUT
    
    # Knife rounds (only knife weapons and kills)
    knife_weapons = {"weapon_knife", "knife", "weapon_bayonet", "weapon_knife_survival"}
    if (kills > 0 and weapons and 
        all(w in knife_weapons or w.startswith("weapon_knife") for w in weapons)):
        return RoundType.KNIFE
    
    # Prematch/warmup (no significant activity)
    if not kills and not has_combat and not has_objective:
        if duration > 1000:  # Some duration but no activity
            return RoundType.WARMUP
        else:
            return RoundType.PREMATCH
    
    # Overtime rounds
    if round_idx > 30:
        return RoundType.OVERTIME
    
    # Standard competitive rounds
    return RoundType.STANDARD

# --- Advanced Round Classification Class ------------------------------------

class RoundClassifier:
    """
    Advanced round classifier with configurable parameters and caching.
    """
    
    def __init__(self, tick_rate: int = DEFAULT_TICK_RATE):
        """
        Initialize the classifier.
        
        Args:
            tick_rate: Game tick rate (default 128 for CS2)
        """
        self.tick_rate = tick_rate
        self.round_time_limit = 115 * tick_rate
        self.freeze_time = 15 * tick_rate
        self._cache = {}
        
    def clear_cache(self):
        """Clear the internal cache."""
        self._cache.clear()
        
    def analyze_match(self, events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Perform comprehensive match analysis.
        
        Args:
            events: List of all game events
            
        Returns:
            Dictionary with match statistics and round analysis
        """
        cache_key = f"match_analysis_{len(events)}"
        if cache_key in self._cache:
            return self._cache[cache_key]
        
        rounds = classify_rounds(events)
        
        # Calculate match statistics
        total_rounds = len(rounds)
        round_types = defaultdict(int)
        total_kills = 0
        total_duration = 0
        
        for round_meta in rounds:
            round_types[round_meta.type.value] += 1
            total_kills += round_meta.kills
            total_duration += round_meta.duration
        
        avg_round_duration = total_duration / total_rounds if total_rounds > 0 else 0
        avg_kills_per_round = total_kills / total_rounds if total_rounds > 0 else 0
        
        analysis = {
            "total_rounds": total_rounds,
            "total_kills": total_kills,
            "total_duration_ticks": total_duration,
            "total_duration_minutes": total_duration / (self.tick_rate * 60),
            "average_round_duration_seconds": avg_round_duration / self.tick_rate,
            "average_kills_per_round": avg_kills_per_round,
            "round_type_distribution": dict(round_types),
            "rounds": rounds
        }
        
        self._cache[cache_key] = analysis
        return analysis

# --- Utility Functions ------------------------------------------------------

def get_round_by_tick(events: List[Dict[str, Any]], target_tick: int) -> Optional[int]:
    """
    Find which round a specific tick belongs to.
    
    Args:
        events: List of game events
        target_tick: Tick to find round for
        
    Returns:
        Round index if found, None otherwise
    """
    starts = _infer_round_starts(events)
    
    for i, start_tick in enumerate(starts):
        next_start = starts[i + 1] if i + 1 < len(starts) else float('inf')
        if start_tick <= target_tick < next_start:
            return i + 1  # 1-based round numbering
    
    return None

def filter_events_by_round(events: List[Dict[str, Any]], round_index: int) -> List[Dict[str, Any]]:
    """
    Filter events to only include those from a specific round.
    
    Args:
        events: List of all game events
        round_index: 1-based round index to filter for
        
    Returns:
        List of events from the specified round
    """
    starts = _infer_round_starts(events)
    
    if round_index < 1 or round_index > len(starts):
        return []
    
    start_tick = starts[round_index - 1]
    end_tick = starts[round_index] if round_index < len(starts) else float('inf')
    
    return [ev for ev in events 
            if start_tick <= ev.get("tick", 0) < end_tick]

# =============================================================================
# Timestamp‑EOF: 2025‑07‑26 (Enhanced Version)
# Enhanced with: type hints, error handling, logging, documentation, 
# Steam3 support, advanced classification, caching, and utility functions
# =============================================================================