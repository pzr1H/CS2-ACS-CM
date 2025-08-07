# """
# ==============================================================================
# 📦 ROUND LABEL FALLBACK + INFERENCE LOGIC (V2-Compatible)
# ==============================================================================
# This utility handles cases where demo data lacks explicit round structure.
# Since CS2-ACS v2 JSON format only contains tick-based positional data,
# the parser does not emit round metadata like winner, scores, or round number.

# To preserve UI compatibility, this utility:
# 1. Constructs dummy `round_data` structures when missing.
# 2. Infers `round_labels` from the `round_data` using fallback naming.
# 3. Supports GUI dropdowns with dynamic label rendering.

# Expected structure for dummy rounds:
# [
#   {"number": 1, "winner": null, "ct_score": null, "t_score": null},
#   ...
# ]

# Inferred label format:
# "Round 1", "Round 2", ..., or optionally "Round 1 (CT win) [10-5]"
# ==============================================================================
# """

def infer_round_labels(round_data):
    # """Build round_labels list from round_data dynamically."""
    round_labels = []
    for r in round_data:
        label = f"Round {r.get('number', 1)}"
        if r.get('winner'):
            label += f" ({r['winner']} win)"
        ct = r.get('ct_score')
        t = r.get('t_score')
        if ct is not None and t is not None:
            label += f" [{ct}-{t}]"
        round_labels.append(label)
    return round_labels


# =============================================================================
# utils/round_dropdown_utils.py - FIXED to work with any data format
# =============================================================================

import logging
from typing import List, Dict, Any, Tuple

log = logging.getLogger(__name__)

def extract_round_dropdown(data: Dict[str, Any]) -> Tuple[List[str], Dict[int, Dict[str, int]]]:
    # """
    # FIXED: Extract round information for dropdown/selection components
    # Works with any data format your parser outputs
    # """
    round_data = []
    round_metadata = {}
    
    try:
        log.info(f"🔍 Looking for round data in: {list(data.keys())}")
        
        # Method 1: Try standard v2 format
        if "round_data" in data and data["round_data"]:
            log.info("✅ Found round_data data")
            return _extract_from_rounds(data["round_data"])
        
        # Method 2: Try alternative round key names
        round_keys = ['round_data', 'match_rounds', 'game_rounds', 'rounds_info']
        for key in round_keys:
            if key in data and data[key]:
                log.info(f"✅ Found round data in '{key}'")
                return _extract_from_any_format(data[key], key)
        
        # Method 3: Try to extract from events
        if "events" in data and data["events"]:
            log.info("🔍 Trying to extract round_data from events...")
            return _extract_rounds_from_events(data["events"])
        
        # Method 4: Check metadata for round count
        if "metadata" in data or "header" in data or "info" in data:
            log.info("🔍 Checking metadata for round information...")
            return _extract_from_metadata(data)
        
        # Method 5: Search all data for round-like structures
        log.info("🔍 Searching all data for round-like structures...")
        for key, value in data.items():
            if isinstance(value, list) and value:
                first_item = value[0] if value else {}
                if isinstance(first_item, dict):
                    round_indicators = ['round', 'start_tick', 'end_tick', 'winner', 'score']
                    matching_fields = sum(1 for field in round_indicators if field in str(first_item).lower())
                    
                    if matching_fields >= 2:
                        log.info(f"✅ Found round-like data in '{key}'")
                        return _extract_from_any_format(value, key)
        
        # Method 6: Last resort - create dummy round_data
        log.warning("⚠️ No round data found - creating dummy round_data")
        return _create_dummy_rounds(data)
        
    except Exception as e:
        log.exception(f"❌ Failed to extract round dropdown: {e}")
        return [], {}


def _extract_from_rounds(round_data: List[Dict[str, Any]]) -> Tuple[List[str], Dict[int, Dict[str, int]]]:
    # """Extract round_data from standard round_data format"""
    round_data = []
    round_metadata = {}
    
    try:
        for i, round_data in enumerate(round_data):
            round_num = i + 1
            
            if isinstance(round_data, dict):
                winner = round_data.get('winner', '')
                reason = round_data.get('reason', '')
                
                # Build label
                label = f"Round {round_num}"
                if winner:
                    label += f" ({winner} wins"
                    if reason:
                        reason_clean = reason.replace('_', ' ').title()
                        label += f" - {reason_clean}"
                    label += ")"
                
                # Build metadata
                metadata = {
                    "start_tick": round_data.get('start_tick', 0),
                    "end_tick": round_data.get('end_tick', 0),
                    "winner": winner,
                    "reason": reason
                }
                
                # Add score if available
                if 'score_ct' in round_data:
                    metadata["score_ct"] = round_data['score_ct']
                if 'score_t' in round_data:
                    metadata["score_t"] = round_data['score_t']
                
            else:
                label = f"Round {round_num}"
                metadata = {}
            
            round_data.append(label)
            round_metadata[round_num] = metadata
        
        log.info(f"✅ Extracted {len(round_data)} round_data from standard format")
        return round_data, round_metadata
        
    except Exception as e:
        log.exception(f"❌ Failed to extract from round_data: {e}")
        return [], {}


def _extract_from_any_format(data: Any, source_key: str) -> Tuple[List[str], Dict[int, Dict[str, int]]]:
    # """Extract round_data from any data format"""
    round_data = []
    round_metadata = {}
    
    try:
        if isinstance(data, list):
            # List of round objects
            for i, item in enumerate(data):
                round_num = i + 1
                
                if isinstance(item, dict):
                    label, metadata = _normalize_round_dict(item, round_num)
                else:
                    label = f"Round {round_num}"
                    metadata = {}
                
                round_data.append(label)
                round_metadata[round_num] = metadata
        
        elif isinstance(data, dict):
            # Single round or nested structure
            if any(field in str(data).lower() for field in ['round', 'winner', 'tick']):
                # Single round
                label, metadata = _normalize_round_dict(data, 1)
                round_data.append(label)
                round_metadata[1] = metadata
            else:
                # Nested structure
                for key, value in data.items():
                    if isinstance(value, list):
                        sub_labels, sub_meta = _extract_from_any_format(value, f"{source_key}.{key}")
                        round_data.extend(sub_labels)
                        round_metadata.update(sub_meta)
        
        log.info(f"✅ Extracted {len(round_data)} round_data from {source_key}")
        return round_data, round_metadata
        
    except Exception as e:
        log.exception(f"❌ Failed to extract from {source_key}: {e}")
        return [], {}


def _normalize_round_dict(round_dict: Dict[str, Any], round_num: int) -> Tuple[str, Dict[str, int]]:
    # """Normalize a round dictionary to standard format"""
    try:
        # Extract winner
        winner_fields = ['winner', 'winning_team', 'result']
        winner = ""
        for field in winner_fields:
            if field in round_dict and round_dict[field]:
                winner = str(round_dict[field])
                break
        
        # Extract reason
        reason_fields = ['reason', 'end_reason', 'how', 'method']
        reason = ""
        for field in reason_fields:
            if field in round_dict and round_dict[field]:
                reason = str(round_dict[field])
                break
        
        # Build label
        label = f"Round {round_num}"
        if winner:
            label += f" ({winner} wins"
            if reason:
                reason_clean = reason.replace('_', ' ').title()
                label += f" - {reason_clean}"
            label += ")"
        
        # Build metadata
        metadata = {
            "start_tick": _safe_int(round_dict.get('start_tick', 0)),
            "end_tick": _safe_int(round_dict.get('end_tick', 0)),
            "winner": winner,
            "reason": reason
        }
        
        # Add optional fields
        optional_fields = ['score_ct', 'score_t', 'duration', 'round_number']
        for field in optional_fields:
            if field in round_dict:
                metadata[field] = _safe_int(round_dict[field])
        
        return label, metadata
        
    except Exception as e:
        log.warning(f"Failed to normalize round dict: {e}")
        return f"Round {round_num}", {}


def _extract_rounds_from_events(events: List[Dict[str, Any]]) -> Tuple[List[str], Dict[int, Dict[str, int]]]:
    # """Extract round information from events list"""
    round_data = []
    round_metadata = {}
    current_round = 0
    round_start_tick = None
    
    try:
        for event in events:
            if not isinstance(event, dict):
                continue
            
            event_name = str(event.get("name", "")).lower()
            event_type = str(event.get("type", "")).lower()
            tick = _safe_int(event.get("tick", 0))
            
            # Look for round start events
            round_start_indicators = ['round_start', 'round_officially_ended', 'begin_new_match']
            if any(indicator in event_name or indicator in event_type for indicator in round_start_indicators):
                if round_start_tick is not None and current_round > 0:
                    # End previous round
                    if current_round in round_metadata:
                        round_metadata[current_round]["end_tick"] = tick
                
                # Start new round
                current_round += 1
                round_start_tick = tick
                round_data.append(f"Round {current_round}")
                round_metadata[current_round] = {"start_tick": tick}
            
            # Look for round end events
            round_end_indicators = ['round_end', 'round_officially_ended']
            if any(indicator in event_name or indicator in event_type for indicator in round_end_indicators):
                if current_round > 0:
                    winner = event.get("winner", "") or event.get("team", "")
                    reason = event.get("reason", "") or event.get("how", "")
                    
                    if winner:
                        round_data[current_round - 1] = f"Round {current_round} ({winner} wins)"
                        round_metadata[current_round]["winner"] = winner
                    
                    if reason:
                        round_metadata[current_round]["reason"] = reason
                    
                    round_metadata[current_round]["end_tick"] = tick
        
        if round_data:
            log.info(f"✅ Extracted {len(round_data)} round_data from events")
        else:
            log.warning("⚠️ No round_data found in events")
        
        return round_data, round_metadata
        
    except Exception as e:
        log.exception(f"❌ Failed to extract round_data from events: {e}")
        return [], {}


def _extract_from_metadata(data: Dict[str, Any]) -> Tuple[List[str], Dict[int, Dict[str, int]]]:
    # """Extract round information from metadata"""
    round_data = []
    round_metadata = {}
    
    try:
        # Check different metadata locations
        metadata_sources = ['metadata', 'header', 'info', 'match_info']
        metadata = {}
        
        for source in metadata_sources:
            if source in data and isinstance(data[source], dict):
                metadata = data[source]
                break
        
        if not metadata:
            return [], {}
        
        # Look for round count
        round_count_fields = ['round_data', 'total_rounds', 'round_count', 'max_rounds']
        round_count = 0
        
        for field in round_count_fields:
            if field in metadata:
                round_count = _safe_int(metadata[field])
                if round_count > 0:
                    break
        
        # Create round_data based on count
        if round_count > 0:
            for i in range(min(round_count, 30)):  # Cap at 30 round_data
                round_num = i + 1
                round_data.append(f"Round {round_num}")
                round_metadata[round_num] = {}
            
            log.info(f"✅ Created {len(round_data)} round_data from metadata")
        
        return round_data, round_metadata
        
    except Exception as e:
        log.exception(f"❌ Failed to extract from metadata: {e}")
        return [], {}


def _create_dummy_rounds(data: Dict[str, Any]) -> Tuple[List[str], Dict[int, Dict[str, int]]]:
    # """Create dummy round_data if no real round data found"""
    try:
        # Default to common match lengths
        round_count = 16  # Default for a short match
        
        # Try to infer from data size or other clues
        if "events" in data and isinstance(data["events"], list):
            event_count = len(data["events"])
            if event_count > 1000:
                round_count = 30  # Longer match
            elif event_count > 500:
                round_count = 24
            elif event_count < 100:
                round_count = 8   # Very short match
        
        # Create dummy round_data
        round_data = []
        round_metadata = {}
        
        for i in range(round_count):
            round_num = i + 1
            round_data.append(f"Round {round_num}")
            round_metadata[round_num] = {}
        
        log.info(f"📝 Created {len(round_data)} dummy round_data")
        return round_data, round_metadata
        
    except Exception as e:
        log.warning(f"Failed to create dummy round_data: {e}")
        return ["Round 1"], {1: {}}


def _safe_int(value: Any) -> int:
    # """Safely convert value to int"""
    try:
        if isinstance(value, (int, float)):
            return int(value)
        elif isinstance(value, str) and value.isdigit():
            return int(value)
        else:
            return 0
    except:
        return 0

def parse_round_dropdown(data):
    """Parse round dropdown for GUI compatibility - wrapper for extract_round_dropdown"""
    try:
        # Use existing extract_round_dropdown function
        round_labels, round_meta = extract_round_dropdown(data)
        return round_labels
        
    except Exception as e:
        log.error(f"Error in parse_round_dropdown: {e}")
        return ["Error loading rounds"]
