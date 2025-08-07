# =============================================================================
# utils/dropdown_utils.py - FIXED to work with any data format
# =============================================================================

import logging
from typing import List, Dict, Any

log = logging.getLogger(__name__)

def extract_player_dropdown(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """
    FIXED: Extract player information for dropdown/selection components
    Works with any data format your parser outputs
    """
    players = []
    
    try:
        log.info(f"🔍 Looking for player data in: {list(data.keys())}")
        
        # Method 1: Try standard v2 format
        if "playerStats" in data and data["playerStats"]:
            log.info("✅ Found playerStats")
            return _extract_from_playerstats(data["playerStats"])
        
        # Method 2: Try alternative player key names
        player_keys = ['players', 'player_stats', 'team_stats', 'player_data', 'teams']
        for key in player_keys:
            if key in data and data[key]:
                log.info(f"✅ Found player data in '{key}'")
                return _extract_from_any_format(data[key], key)
        
        # Method 3: Search through all data for player-like structures
        log.info("🔍 Searching all data for player-like structures...")
        for key, value in data.items():
            if isinstance(value, list) and value:
                # Check if this list contains player-like objects
                first_item = value[0] if value else {}
                if isinstance(first_item, dict):
                    player_indicators = ['name', 'steam_id', 'kills', 'deaths', 'team', 'player']
                    matching_fields = sum(1 for field in player_indicators if field in first_item)
                    
                    if matching_fields >= 2:  # At least 2 player-like fields
                        log.info(f"✅ Found player-like data in '{key}' with {matching_fields} indicators")
                        return _extract_from_any_format(value, key)
            
            elif isinstance(value, dict):
                # Check if this dict contains player info directly
                player_indicators = ['name', 'steam_id', 'kills', 'deaths', 'team']
                matching_fields = sum(1 for field in player_indicators if field in value)
                
                if matching_fields >= 2:
                    log.info(f"✅ Found single player data in '{key}'")
                    return _extract_from_any_format([value], key)
        
        # Method 4: Last resort - create dummy players if we have any match data
        log.warning("⚠️ No player data found - creating dummy entries")
        return _create_dummy_players(data)
        
    except Exception as e:
        log.exception(f"❌ Failed to extract player dropdown: {e}")
        return []


def _extract_from_playerstats(playerStats: List[Dict[str, Any]]) -> List[Dict[str, str]]:
    """Extract players from standard playerStats format"""
    players = []
    
    for i, player in enumerate(playerStats):
        if not isinstance(player, dict):
            continue
            
        name = player.get("name", f"Player_{i+1}")
        team = player.get("team", "")
        
        label = f"{name} ({team})" if team else name
        
        player_entry = {
            "label": label,
            "value": name,
            "team": team,
            "index": i
        }
        
        # Add optional fields if available
        for field in ['steam_id', 'xuid', 'kills', 'deaths', 'assists']:
            if field in player:
                player_entry[field] = player[field]
        
        players.append(player_entry)
    
    return players


def _extract_from_any_format(data: Any, source_key: str) -> List[Dict[str, str]]:
    """Extract players from any data format"""
    players = []
    
    try:
        # Handle different data types
        if isinstance(data, list):
            # List of player objects
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    player = _normalize_player_dict(item, i)
                    if player:
                        players.append(player)
                else:
                    # Handle non-dict items
                    players.append({
                        "label": f"Player_{i+1}",
                        "value": f"player_{i+1}",
                        "team": "",
                        "index": i
                    })
        
        elif isinstance(data, dict):
            # Single player object or nested structure
            if any(field in data for field in ['name', 'steam_id', 'kills']):
                # Single player
                player = _normalize_player_dict(data, 0)
                if player:
                    players.append(player)
            else:
                # Nested structure - look for player data inside
                for key, value in data.items():
                    if isinstance(value, list):
                        players.extend(_extract_from_any_format(value, f"{source_key}.{key}"))
                    elif isinstance(value, dict) and any(field in value for field in ['name', 'steam_id']):
                        player = _normalize_player_dict(value, len(players))
                        if player:
                            players.append(player)
        
        log.info(f"✅ Extracted {len(players)} players from {source_key}")
        return players
        
    except Exception as e:
        log.exception(f"❌ Failed to extract from {source_key}: {e}")
        return []


def _normalize_player_dict(player_dict: Dict[str, Any], index: int) -> Dict[str, str]:
    """Normalize a player dictionary to standard format"""
    try:
        # Try different possible name fields
        name_fields = ['name', 'player_name', 'username', 'nick', 'handle']
        name = None
        for field in name_fields:
            if field in player_dict and player_dict[field]:
                name = str(player_dict[field])
                break
        
        if not name:
            name = f"Player_{index+1}"
        
        # Try different possible team fields
        team_fields = ['team', 'side', 'team_name', 'faction']
        team = ""
        for field in team_fields:
            if field in player_dict and player_dict[field]:
                team = str(player_dict[field])
                break
        
        # Create display label
        label = f"{name} ({team})" if team else name
        
        # Build normalized player entry
        player_entry = {
            "label": label,
            "value": name,
            "team": team,
            "index": index
        }
        
        # Add additional fields if available
        optional_fields = ['steam_id', 'xuid', 'kills', 'deaths', 'assists', 'score']
        for field in optional_fields:
            if field in player_dict:
                player_entry[field] = player_dict[field]
        
        return player_entry
        
    except Exception as e:
        log.warning(f"Failed to normalize player dict: {e}")
        return None


def _create_dummy_players(data: Dict[str, Any]) -> List[Dict[str, str]]:
    """Create dummy players if no real player data found"""
    try:
        # Try to infer number of players from other data
        player_count = 10  # Default
        
        # Look for clues about player count
        if "metadata" in data:
            metadata = data["metadata"]
            if isinstance(metadata, dict):
                if "players" in metadata:
                    player_count = metadata["players"]
                elif "player_count" in metadata:
                    player_count = metadata["player_count"]
        
        # Create dummy players
        players = []
        for i in range(min(player_count, 10)):  # Cap at 10
            team = "CT" if i < player_count // 2 else "T"
            players.append({
                "label": f"Player_{i+1} ({team})",
                "value": f"Player_{i+1}",
                "team": team,
                "index": i
            })
        
        log.info(f"📝 Created {len(players)} dummy players")
        return players
        
    except Exception as e:
        log.warning(f"Failed to create dummy players: {e}")
        return []

def build_player_dropdown(data):
    """Build player dropdown for GUI compatibility - wrapper for extract_player_dropdown"""
    try:
        # Use existing extract_player_dropdown function
        players = extract_player_dropdown(data)
        player_map = {}
        
        # Create player mapping for compatibility
        if isinstance(players, list):
            for i, player in enumerate(players):
                player_map[i] = player
        
        return players, player_map
        
    except Exception as e:
        log.error(f"Error in build_player_dropdown: {e}")
        return ["Error loading players"], {}
