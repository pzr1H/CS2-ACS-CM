#!/usr/bin/env python3
# =============================================================================
# data_sanitizer.py — Enhanced Data Sanitization with Debug Logging
# =============================================================================

import logging
import json
from typing import Dict, Any, List, Optional
from collections import defaultdict

log = logging.getLogger(__name__)

def sanitize_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enhanced sanitization with comprehensive debug logging and CS2-ACS binary output handling
    
    Args:
        data: Data dictionary to sanitize
        
    Returns:
        Sanitized data dictionary
    """
    try:
        log.info("🔍 Starting enhanced data sanitization with debug logging")
        
        if not isinstance(data, dict):
            log.error("❌ Data must be a dictionary for sanitization")
            return {}
        
        # Debug: Log the actual data structure received
        log.info(f"📊 Raw data keys: {list(data.keys())}")
        log.info(f"📊 Data structure analysis:")
        for key, value in data.items():
            if isinstance(value, (list, dict)):
                log.info(f"  • {key}: {type(value).__name__} with {len(value)} items")
            else:
                log.info(f"  • {key}: {type(value).__name__} = {str(value)[:100]}...")
        
        # Add parsing completeness assessment
        completeness = assess_parsing_completeness(data)
        log.info(f"📊 Parsing completeness assessment: {completeness}")
        
        # Enhanced data structure mapping for CS2-ACS binary output
        sanitized_data = _map_cs2_acs_structure(data)
        
        # Ensure required top-level keys exist with proper types
        required_keys = {
            'events': list,
            'playerStats': dict,
            'playerDropdown': list,
            'round_labels': list,
            'round_indices': list,
            'metadata': dict,
            'chat': list,
            'advancedStats': dict,
            'formatted_events': list
        }
        
        for key, expected_type in required_keys.items():
            if key not in sanitized_data:
                sanitized_data[key] = expected_type()
                log.warning(f"⚠️ Added missing key: {key}")
            elif not isinstance(sanitized_data[key], expected_type):
                log.warning(f"⚠️ Key {key} has wrong type {type(sanitized_data[key])}, converting to {expected_type.__name__}")
                sanitized_data[key] = _convert_to_type(sanitized_data[key], expected_type)
        
        # Enhanced event validation and processing
        sanitized_data['events'] = _sanitize_events(sanitized_data.get('events', []))
        
        # Enhanced player data processing
        sanitized_data['playerDropdown'] = _sanitize_player_dropdown(sanitized_data.get('playerDropdown', []), sanitized_data.get('events', []))
        
        # Enhanced chat processing
        sanitized_data['chat'] = _sanitize_chat_data(sanitized_data.get('chat', []), sanitized_data.get('events', []))
        
        # Generate round data if missing
        if not sanitized_data['round_labels'] or not sanitized_data['round_indices']:
            sanitized_data['round_labels'], sanitized_data['round_indices'] = _generate_round_data(sanitized_data.get('events', []))
        
        # Generate player stats if missing
        if not sanitized_data['playerStats']:
            sanitized_data['playerStats'] = _generate_fallback_player_stats(sanitized_data.get('events', []), sanitized_data.get('playerDropdown', []))
        
        # Generate metadata if missing
        if not sanitized_data['metadata']:
            sanitized_data['metadata'] = _generate_metadata(sanitized_data)
        
        log.info("✅ Enhanced data sanitization completed successfully")
        log.info(f"📊 Final data structure: {len(sanitized_data)} top-level keys")
        log.info(f"  • Events: {len(sanitized_data.get('events', []))}")
        log.info(f"  • Players: {len(sanitized_data.get('playerDropdown', []))}")
        log.info(f"  • Chat messages: {len(sanitized_data.get('chat', []))}")
        log.info(f"  • Player stats: {len(sanitized_data.get('playerStats', {}))}")
        
        return sanitized_data
        
    except Exception as e:
        log.error(f"❌ Enhanced data sanitization failed: {e}")
        log.exception("Full error traceback:")
        return data

def assess_parsing_completeness(data: Dict[str, Any]) -> Dict[str, Any]:
    """Assess how complete the demo parsing was"""
    try:
        assessment = {
            "overall_score": 0,
            "has_events": False,
            "has_players": False,
            "has_rounds": False,
            "has_stats": False,
            "has_chat": False,
            "estimated_completeness": "Unknown",
            "issues": [],
            "recommendations": []
        }
        
        score = 0
        
        # Check for events (most critical)
        events = data.get('events', [])
        if events and len(events) > 0:
            assessment["has_events"] = True
            score += 40
            if len(events) > 100:  # Reasonable number of events
                score += 10
        else:
            assessment["issues"].append("No events found - core parsing likely failed")
            assessment["recommendations"].append("Check CS2-ACS binary execution and demo file validity")
        
        # Check for players
        players = data.get('playerDropdown', data.get('players', []))
        if players and len(players) > 0:
            assessment["has_players"] = True
            score += 20
            if len(players) >= 2:  # At least 2 players expected
                score += 5
        else:
            assessment["issues"].append("No players found")
        
        # Check for rounds
        rounds = data.get('round_labels', data.get('rounds', []))
        if rounds and len(rounds) > 0:
            assessment["has_rounds"] = True
            score += 15
        else:
            assessment["issues"].append("No rounds found")
        
        # Check for stats
        stats = data.get('playerStats', {})
        if stats and len(stats) > 0:
            assessment["has_stats"] = True
            score += 10
        else:
            assessment["issues"].append("No player statistics computed")
        
        # Check for chat
        chat = data.get('chat', [])
        if chat and len(chat) > 0:
            assessment["has_chat"] = True
            score += 5
        
        assessment["overall_score"] = score
        
        # Determine completeness level
        if score >= 80:
            assessment["estimated_completeness"] = "Excellent (80%+)"
        elif score >= 60:
            assessment["estimated_completeness"] = "Good (60-79%)"
        elif score >= 40:
            assessment["estimated_completeness"] = "Partial (40-59%)"
        elif score >= 20:
            assessment["estimated_completeness"] = "Poor (20-39%)"
        else:
            assessment["estimated_completeness"] = "Failed (0-19%)"
            assessment["recommendations"].append("Demo parsing completely failed - check binary and demo file")
        
        return assessment
        
    except Exception as e:
        return {"error": f"Assessment failed: {str(e)}"}

def _map_cs2_acs_structure(data: Dict[str, Any]) -> Dict[str, Any]:
    """Map CS2-ACS binary output structure to expected format"""
    try:
        log.info("🔄 Mapping CS2-ACS binary output structure")
        
        mapped_data = data.copy()
        
        # Common CS2-ACS output mappings
        structure_mappings = {
            # Events mappings
            'Events': 'events',
            'GameEvents': 'events',
            'event_data': 'events',
            'demo_events': 'events',
            
            # Player mappings
            'Players': 'playerDropdown',
            'PlayerData': 'playerDropdown',
            'player_info': 'playerDropdown',
            'participants': 'playerDropdown',
            
            # Stats mappings
            'PlayerStats': 'playerStats',
            'Statistics': 'playerStats',
            'player_statistics': 'playerStats',
            'stats': 'playerStats',
            
            # Chat mappings
            'Chat': 'chat',
            'ChatMessages': 'chat',
            'chat_data': 'chat',
            'messages': 'chat',
            
            # Round mappings
            'Rounds': 'round_indices',
            'RoundData': 'round_indices',
            'round_info': 'round_indices',
            
            # Metadata mappings
            'Header': 'metadata',
            'DemoInfo': 'metadata',
            'demo_header': 'metadata',
            'match_info': 'metadata'
        }
        
        # Apply mappings
        for old_key, new_key in structure_mappings.items():
            if old_key in data and new_key not in mapped_data:
                mapped_data[new_key] = data[old_key]
                log.info(f"🔄 Mapped {old_key} -> {new_key}")
        
        # Handle nested structures
        if 'demo' in data and isinstance(data['demo'], dict):
            for key, value in data['demo'].items():
                if key.lower() in ['events', 'players', 'chat', 'stats']:
                    target_key = structure_mappings.get(key, key.lower())
                    if target_key not in mapped_data:
                        mapped_data[target_key] = value
                        log.info(f"🔄 Mapped nested demo.{key} -> {target_key}")
        
        return mapped_data
        
    except Exception as e:
        log.error(f"❌ CS2-ACS structure mapping failed: {e}")
        return data

def _convert_to_type(value: Any, target_type: type) -> Any:
    """Convert value to target type with fallbacks"""
    try:
        if target_type == list:
            if isinstance(value, dict):
                return list(value.values()) if value else []
            elif isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, list) else [parsed]
                except:
                    return [value] if value else []
            else:
                return list(value) if hasattr(value, '__iter__') else [value]
        
        elif target_type == dict:
            if isinstance(value, list):
                return {i: item for i, item in enumerate(value)}
            elif isinstance(value, str):
                try:
                    parsed = json.loads(value)
                    return parsed if isinstance(parsed, dict) else {'data': parsed}
                except:
                    return {'data': value}
            else:
                return dict(value) if hasattr(value, 'items') else {'data': value}
        
        else:
            return target_type(value)
            
    except Exception as e:
        log.warning(f"⚠️ Type conversion failed: {e}")
        return target_type()

def _sanitize_events(events: List[Any]) -> List[Dict[str, Any]]:
    """Enhanced event sanitization with CS2-ACS format support"""
    try:
        if not events:
            log.warning("⚠️ No events to sanitize")
            return []
        
        log.info(f"🔄 Sanitizing {len(events)} events")
        
        sanitized_events = []
        event_types = defaultdict(int)
        
        for i, event in enumerate(events):
            try:
                if not isinstance(event, dict):
                    # Try to convert string events (JSON format)
                    if isinstance(event, str):
                        try:
                            event = json.loads(event)
                        except:
                            log.warning(f"⚠️ Could not parse event {i} as JSON")
                            continue
                    else:
                        log.warning(f"⚠️ Event {i} is not a dict: {type(event)}")
                        continue
                
                # Ensure event has required fields
                sanitized_event = {
                    'type': event.get('type', event.get('event_type', event.get('name', 'unknown'))),
                    'tick': event.get('tick', event.get('game_tick', event.get('time', 0))),
                    'round': event.get('round', event.get('round_number', event.get('round_num', -1))),
                    'timestamp': event.get('timestamp', event.get('time', event.get('tick', 0)))
                }
                
                # Copy all other fields
                for key, value in event.items():
                    if key not in sanitized_event:
                        sanitized_event[key] = value
                
                # Validate event type
                if sanitized_event['type'] and sanitized_event['type'] != 'unknown':
                    sanitized_events.append(sanitized_event)
                    event_types[sanitized_event['type']] += 1
                else:
                    log.warning(f"⚠️ Event {i} has no valid type")
                    
            except Exception as e:
                log.warning(f"⚠️ Failed to sanitize event {i}: {e}")
        
        log.info(f"✅ Sanitized {len(sanitized_events)} events")
        log.info(f"📊 Event types found: {dict(list(event_types.items())[:10])}")  # Show top 10
        
        return sanitized_events
        
    except Exception as e:
        log.error(f"❌ Event sanitization failed: {e}")
        return []

def _sanitize_player_dropdown(players: List[Any], events: List[Dict]) -> List[Dict[str, Any]]:
    """Enhanced player dropdown sanitization with event extraction fallback"""
    try:
        log.info(f"🔄 Sanitizing player dropdown with {len(players)} initial players")
        
        sanitized_players = []
        seen_steamids = set()
        
        # Process existing player data
        for player in players:
            try:
                if not isinstance(player, dict):
                    continue
                
                steamid = player.get('steamid', player.get('steam_id', player.get('id', '')))
                name = player.get('name', player.get('player_name', player.get('username', '')))
                
                if steamid and name and steamid not in seen_steamids:
                    sanitized_player = {
                        'steamid': str(steamid),
                        'name': str(name),
                        'steam2': player.get('steam2', _steamid64_to_steam2(steamid)),
                        'team': player.get('team', player.get('team_name', 'Unknown')),
                        'display_name': f"{name} ({_steamid64_to_steam2(steamid)})"
                    }
                    sanitized_players.append(sanitized_player)
                    seen_steamids.add(steamid)
                    
            except Exception as e:
                log.warning(f"⚠️ Failed to sanitize player: {e}")
        
        # Extract additional players from events if needed
        if len(sanitized_players) < 2:  # Minimum expected players
            log.info("🔍 Extracting additional players from events")
            event_players = _extract_players_from_events(events)
            
            for player in event_players:
                steamid = player.get('steamid', '')
                if steamid and steamid not in seen_steamids:
                    sanitized_players.append(player)
                    seen_steamids.add(steamid)
        
        log.info(f"✅ Sanitized {len(sanitized_players)} players")
        return sanitized_players
        
    except Exception as e:
        log.error(f"❌ Player dropdown sanitization failed: {e}")
        return []

def _sanitize_chat_data(chat: List[Any], events: List[Dict]) -> List[Dict[str, Any]]:
    """Enhanced chat data sanitization with event extraction"""
    try:
        log.info(f"🔄 Sanitizing chat data with {len(chat)} initial messages")
        
        sanitized_chat = []
        
        # Process existing chat data
        for msg in chat:
            try:
                if isinstance(msg, dict) and msg.get('text'):
                    sanitized_msg = {
                        'text': str(msg.get('text', '')),
                        'player': msg.get('player', msg.get('sender', 'Unknown')),
                        'tick': msg.get('tick', msg.get('time', 0)),
                        'round': msg.get('round', -1),
                        'is_team_message': msg.get('is_team_message', False)
                    }
                    sanitized_chat.append(sanitized_msg)
            except Exception as e:
                log.warning(f"⚠️ Failed to sanitize chat message: {e}")
        
        # Extract chat from events if needed
        if len(sanitized_chat) == 0:
            log.info("🔍 Extracting chat messages from events")
            event_chat = _extract_chat_from_events(events)
            sanitized_chat.extend(event_chat)
        
        log.info(f"✅ Sanitized {len(sanitized_chat)} chat messages")
        return sanitized_chat
        
    except Exception as e:
        log.error(f"❌ Chat data sanitization failed: {e}")
        return []

def _generate_round_data(events: List[Dict]) -> tuple:
    """Generate round labels and indices from events"""
    try:
        rounds = set()
        for event in events:
            round_num = event.get('round', -1)
            if isinstance(round_num, int) and round_num >= 0:
                rounds.add(round_num)
        
        if not rounds:
            log.warning("⚠️ No valid rounds found, creating default")
            return ["Round 1"], [0]
        
        sorted_rounds = sorted(rounds)
        round_labels = [f"Round {r + 1}" for r in sorted_rounds]
        
        log.info(f"✅ Generated {len(round_labels)} round labels")
        return round_labels, sorted_rounds
        
    except Exception as e:
        log.error(f"❌ Round data generation failed: {e}")
        return ["Round 1"], [0]

def _generate_fallback_player_stats(events: List[Dict], players: List[Dict]) -> Dict[str, Any]:
    """Generate fallback player statistics from events"""
    try:
        log.info("🔄 Generating fallback player statistics from events")
        
        player_stats = {}
        
        # Initialize stats for known players
        for player in players:
            steamid = player.get('steamid', '')
            if steamid:
                player_stats[steamid] = {
                    'steamid': steamid,
                    'name': player.get('name', 'Unknown'),
                    'steam2': player.get('steam2', ''),
                    'team': player.get('team', 'Unknown'),
                    'kills': 0,
                    'deaths': 0,
                    'assists': 0,
                    'damage': 0,
                    'shots_fired': 0,
                    'headshots': 0,
                    'adr': 0.0,
                    'kd_ratio': 0.0,
                    'rating': 0.0
                }
        
        # Process events to calculate stats
        for event in events:
            event_type = event.get('type', '').lower()
            
            if 'death' in event_type or 'kill' in event_type:
                attacker = event.get('attacker', {})
                victim = event.get('victim', {})
                
                attacker_id = attacker.get('steamid') if isinstance(attacker, dict) else None
                victim_id = victim.get('steamid') if isinstance(victim, dict) else None
                
                if attacker_id and attacker_id in player_stats:
                    player_stats[attacker_id]['kills'] += 1
                    if event.get('headshot', False):
                        player_stats[attacker_id]['headshots'] += 1
                
                if victim_id and victim_id in player_stats:
                    player_stats[victim_id]['deaths'] += 1
            
            elif 'hurt' in event_type or 'damage' in event_type:
                attacker = event.get('attacker', {})
                damage = event.get('health_damage', event.get('damage', 0))
                
                attacker_id = attacker.get('steamid') if isinstance(attacker, dict) else None
                if attacker_id and attacker_id in player_stats:
                    player_stats[attacker_id]['damage'] += damage
            
            elif 'fire' in event_type or 'shot' in event_type:
                user = event.get('user', {})
                user_id = user.get('steamid') if isinstance(user, dict) else None
                
                if user_id and user_id in player_stats:
                    player_stats[user_id]['shots_fired'] += 1
        
        # Calculate derived stats
        for steamid, stats in player_stats.items():
            if stats['deaths'] > 0:
                stats['kd_ratio'] = round(stats['kills'] / stats['deaths'], 2)
            else:
                stats['kd_ratio'] = float(stats['kills'])
            
            # Simple ADR calculation (damage per death as approximation)
            if stats['deaths'] > 0:
                stats['adr'] = round(stats['damage'] / stats['deaths'], 1)
            else:
                stats['adr'] = stats['damage']
            
            # Simple rating calculation
            stats['rating'] = round((stats['kills'] * 0.6 + stats['damage'] * 0.002), 3)
        
        log.info(f"✅ Generated fallback stats for {len(player_stats)} players")
        return player_stats
        
    except Exception as e:
        log.error(f"❌ Fallback player stats generation failed: {e}")
        return {}

def _generate_metadata(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate metadata from available data"""
    try:
        metadata = {
            'source': 'CS2-ACS',
            'processed_at': str(log.info.__module__),  # Timestamp placeholder
            'total_events': len(data.get('events', [])),
            'total_players': len(data.get('playerDropdown', [])),
            'total_rounds': len(data.get('round_labels', [])),
            'has_chat': len(data.get('chat', [])) > 0,
            'has_player_stats': len(data.get('playerStats', {})) > 0
        }
        
        log.info("✅ Generated metadata")
        return metadata
        
    except Exception as e:
        log.error(f"❌ Metadata generation failed: {e}")
        return {}

def _extract_players_from_events(events: List[Dict]) -> List[Dict[str, Any]]:
    """Extract player information from events"""
    try:
        players = {}
        
        for event in events:
            # Check various player fields
            for field in ['attacker', 'victim', 'user', 'player']:
                player_data = event.get(field, {})
                if isinstance(player_data, dict):
                    steamid = player_data.get('steamid')
                    name = player_data.get('name')
                    
                    if steamid and name and steamid not in players:
                        players[steamid] = {
                            'steamid': str(steamid),
                            'name': str(name),
                            'steam2': _steamid64_to_steam2(steamid),
                            'team': player_data.get('team', 'Unknown'),
                            'display_name': f"{name} ({_steamid64_to_steam2(steamid)})"
                        }
        
        return list(players.values())
        
    except Exception as e:
        log.error(f"❌ Player extraction from events failed: {e}")
        return []

def _extract_chat_from_events(events: List[Dict]) -> List[Dict[str, Any]]:
    """Extract chat messages from events"""
    try:
        chat_messages = []
        
        for event in events:
            event_type = event.get('type', '').lower()
            if 'chat' in event_type or 'message' in event_type or 'say' in event_type:
                text = event.get('text', event.get('message', ''))
                if text:
                    chat_messages.append({
                        'text': str(text),
                        'player': event.get('player', {}).get('name', 'Unknown'),
                        'tick': event.get('tick', 0),
                        'round': event.get('round', -1),
                        'is_team_message': event.get('is_team_message', False)
                    })
        
        return chat_messages
        
    except Exception as e:
        log.error(f"❌ Chat extraction from events failed: {e}")
        return []

def _steamid64_to_steam2(steamid64: Any) -> str:
    """Convert SteamID64 to Steam2 format"""
    try:
        if isinstance(steamid64, str):
            steamid64 = int(steamid64)
        
        if steamid64 > 76561197960265728:
            auth_server = steamid64 % 2
            account_id = (steamid64 - 76561197960265728) // 2
            return f"STEAM_1:{auth_server}:{account_id}"
        else:
            return "STEAM_0:0:0"
    except:
        return "STEAM_0:0:0"

def validate_data_integrity(data: Dict[str, Any]) -> List[str]:
    """
    Validate data integrity and return list of issues
    
    Args:
        data: Data dictionary to validate
        
    Returns:
        List of validation issues found
    """
    try:
        issues = []
        
        if not isinstance(data, dict):
            issues.append("Data is not a dictionary")
            return issues
        
        # Check for required keys
        required_keys = ['events', 'playerDropdown', 'round_labels']
        for key in required_keys:
            if key not in data:
                issues.append(f"Missing required key: {key}")
        
        # Validate events
        events = data.get('events', [])
        if not isinstance(events, list):
            issues.append("Events must be a list")
        elif len(events) == 0:
            issues.append("No events found")
        
        # Validate players
        players = data.get('playerDropdown', [])
        if not isinstance(players, list):
            issues.append("playerDropdown must be a list")
        elif len(players) == 0:
            issues.append("No players found")
        
        # Validate rounds
        rounds = data.get('round_labels', [])
        if not isinstance(rounds, list):
            issues.append("round_labels must be a list")
        elif len(rounds) == 0:
            issues.append("No rounds found")
        
        return issues
        
    except Exception as e:
        log.error(f"❌ Data integrity validation failed: {e}")
        return [f"Validation error: {str(e)}"]

def enforce_schema_safety(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Legacy function name - calls sanitize_metadata for compatibility
    """
    return sanitize_metadata(data)

def reconcile_final_scoreboard(data: Dict[str, Any]) -> None:
    """
    Legacy function - adds final scoreboard if missing
    """
    try:
        if "finalScoreboard" in data:
            return
        
        # Create basic scoreboard
        data["finalScoreboard"] = {
            "team1": {"name": "Team 1", "score": 0},
            "team2": {"name": "Team 2", "score": 0}
        }
        
        log.info("📊 Added basic final scoreboard")
        
    except Exception as e:
        log.error(f"❌ Failed to reconcile final scoreboard: {e}")