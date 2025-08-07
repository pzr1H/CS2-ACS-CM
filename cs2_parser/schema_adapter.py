#!/usr/bin/env python3
"""
CS2 Schema Adapter - Enhanced GUI Compatible Version
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

log = logging.getLogger(__name__)

class SchemaAdapter:
    """Enhanced CS2 Data Schema Adapter for GUI compatibility"""
    
    def __init__(self):
        self.schema_version = "v3-gui-compatible"  # Changed from v3-nested-aware
        self.supported_formats = ["cs2_events", "demo_parser"]
    
    def adapt_cs2_data(self, data, source_format="cs2_events"):
        """Adapt CS2 data to GUI-compatible schema"""
        try:
            if not isinstance(data, dict):
                log.warning("Input data is not a dictionary")
                return self._create_empty_structure()
            
            # Process events first (needed for other processing)
            events = data.get("events", [])
            log.info(f"Processing {len(events)} events")
            
            # Extract and process player stats
            player_stats = self._extract_and_process_players(data, events)
            
            # Extract and process rounds
            rounds = self._extract_and_process_rounds(data, events)
            
            # Extract chat messages
            chat_messages = self._extract_chat_messages(events)
            
            # Build GUI-compatible structure
            adapted_data = {
                "events": events,
                "playerStats": player_stats,
                "rounds": rounds,
                "chatMessages": chat_messages,
                "playerDropdown": self._build_player_dropdown(player_stats),
                "roundDropdown": self._build_round_dropdown(rounds),
                "parser_version": self.schema_version,
                "total_events": len(events),
                "parsed_at": datetime.now().isoformat(),
                "demo_file": data.get("demo_file", "unknown.dem"),
                "metadata": {
                    "total_players": len(player_stats),
                    "total_rounds": len(rounds),
                    "total_chat_messages": len(chat_messages),
                    "parser_version": self.schema_version
                }
            }
            
            log.info(f"✅ Schema adaptation complete: {len(player_stats)} players, {len(rounds)} rounds, {len(chat_messages)} chat messages")
            return adapted_data
            
        except Exception as e:
            log.error(f"Schema adaptation failed: {e}")
            return self._create_empty_structure()
    
    def _extract_and_process_players(self, data, events):
        """Extract and process player data for GUI compatibility"""
        # Start with any existing playerStats
        existing_players = data.get("playerStats", [])
        
        # Convert existing players to proper format
        processed_players = []
        
        for player in existing_players:
            if isinstance(player, dict):
                # Ensure all required fields exist
                processed_player = {
                    "steam_id64": str(player.get("steam_id64", "0")),
                    "name": str(player.get("name", "Unknown")),
                    "team": player.get("team", "Unknown"),
                    "kills": int(player.get("kills", 0)),
                    "deaths": int(player.get("deaths", 0)),
                    "assists": int(player.get("assists", 0)),
                    "damage": float(player.get("damage", 0.0)),
                    "headshots": int(player.get("headshots", 0)),
                    "score": int(player.get("score", 0)),
                    "kd_ratio": float(player.get("kd_ratio", 0.0)),
                    "headshot_percentage": 0.0,
                    "accuracy": float(player.get("accuracy", 0.0)),
                    "mvps": int(player.get("mvps", 0)),
                    "adr": 0.0,  # Average Damage per Round
                    "rating": 0.0,
                    "active": True,
                    "connected": True
                }
                
                # Calculate derived stats
                if processed_player["kills"] > 0:
                    processed_player["headshot_percentage"] = (processed_player["headshots"] / processed_player["kills"]) * 100
                
                if processed_player["deaths"] > 0:
                    processed_player["kd_ratio"] = processed_player["kills"] / processed_player["deaths"]
                else:
                    processed_player["kd_ratio"] = float(processed_player["kills"])
                
                # Calculate rating (simplified)
                processed_player["rating"] = self._calculate_rating(processed_player)
                
                processed_players.append(processed_player)
        
        # If no players found, extract from events
        if not processed_players:
            processed_players = self._extract_players_from_events(events)
        
        return processed_players
    
    def _extract_players_from_events(self, events):
        """Extract player data from events if not in playerStats"""
        players_dict = {}
        
        for event in events:
            if not isinstance(event, dict):
                continue
                
            event_data = event.get("data", {})
            
            # Look for player objects in events
            player_fields = ["attacker", "victim", "user", "player"]
            
            for field in player_fields:
                player_obj = event_data.get(field)
                if isinstance(player_obj, dict):
                    steam_id = str(player_obj.get("steamid", player_obj.get("steam_id64", "0")))
                    name = player_obj.get("name", "Unknown")
                    
                    if steam_id != "0" and len(steam_id) > 5:
                        if steam_id not in players_dict:
                            players_dict[steam_id] = {
                                "steam_id64": steam_id,
                                "name": name,
                                "team": "Unknown",
                                "kills": 0,
                                "deaths": 0,
                                "assists": 0,
                                "damage": 0.0,
                                "headshots": 0,
                                "score": 0,
                                "kd_ratio": 0.0,
                                "headshot_percentage": 0.0,
                                "accuracy": 0.0,
                                "mvps": 0,
                                "adr": 0.0,
                                "rating": 0.0,
                                "active": True,
                                "connected": True
                            }
        
        return list(players_dict.values())
    
    def _extract_and_process_rounds(self, data, events):
        """Extract and process round data for GUI compatibility"""
        existing_rounds = data.get("rounds", [])
        processed_rounds = []
        
        for round_data in existing_rounds:
            if isinstance(round_data, dict):
                processed_round = {
                    "number": int(round_data.get("number", 1)),
                    "start_tick": int(round_data.get("start_tick", 0)),
                    "end_tick": int(round_data.get("end_tick", 1000)),
                    "winner": round_data.get("winner", "Unknown"),  # Required field
                    "reason": round_data.get("reason", "Unknown"),
                    "duration": float(round_data.get("duration", 0.0)),
                    "score_ct": int(round_data.get("score_ct", 0)),
                    "score_t": int(round_data.get("score_t", 0)),
                    "economy_ct": int(round_data.get("economy_ct", 0)),
                    "economy_t": int(round_data.get("economy_t", 0)),
                    "kills": [],
                    "clutches": [],
                    "defusals": []
                }
                
                processed_rounds.append(processed_round)
        
        # If no rounds, create default structure
        if not processed_rounds:
            for i in range(1, 17):  # Default 16 rounds
                processed_rounds.append({
                    "number": i,
                    "start_tick": i * 1000,
                    "end_tick": (i + 1) * 1000,
                    "winner": "Unknown",
                    "reason": "Unknown",
                    "duration": 120.0,
                    "score_ct": 0,
                    "score_t": 0,
                    "economy_ct": 0,
                    "economy_t": 0,
                    "kills": [],
                    "clutches": [],
                    "defusals": []
                })
        
        return processed_rounds
    
    def _extract_chat_messages(self, events):
        """Extract chat messages from events"""
        chat_messages = []
        
        for event in events:
            if not isinstance(event, dict):
                continue
                
            event_type = event.get("type", "").lower()
            
            if "chat" in event_type or "say" in event_type:
                event_data = event.get("data", {})
                
                chat_message = {
                    "tick": event.get("tick", 0),
                    "timestamp": event.get("timestamp", ""),
                    "player_name": event_data.get("player_name", "Unknown"),
                    "steam_id": str(event_data.get("steam_id", "0")),
                    "team": event_data.get("team", "All"),
                    "message": event_data.get("message", ""),
                    "is_team_chat": event_data.get("is_team_chat", False),
                    "round_number": event_data.get("round", 0)
                }
                
                chat_messages.append(chat_message)
        
        return chat_messages
    
    def _calculate_rating(self, player):
        """Calculate a simple player rating"""
        try:
            kills = player["kills"]
            deaths = max(player["deaths"], 1)
            assists = player["assists"]
            
            # Simplified rating calculation
            kd = kills / deaths
            kda = (kills + assists * 0.5) / deaths
            
            return round(kda, 2)
        except:
            return 0.0
    
    def _build_player_dropdown(self, players):
        """Build player dropdown for GUI"""
        dropdown = ["All Players"]
        
        for player in players:
            name = player.get("name", "Unknown")
            steam_id = player.get("steam_id64", "0")
            
            # Convert to Steam2 format for display
            try:
                steam_id_int = int(steam_id)
                steam_id_32 = steam_id_int - 76561197960265728
                steam2 = f"STEAM_0:{steam_id_32 % 2}:{steam_id_32 // 2}"
            except:
                steam2 = "STEAM_0:0:0"
            
            dropdown.append(f"{name} ({steam2})")
        
        return dropdown
    
    def _build_round_dropdown(self, rounds):
        """Build round dropdown for GUI"""
        dropdown = ["All Rounds"]
        
        for round_data in rounds:
            number = round_data.get("number", 1)
            winner = round_data.get("winner", "Unknown")
            dropdown.append(f"Round {number} ({winner})")
        
        return dropdown
    
    def _create_empty_structure(self):
        """Create empty GUI-compatible structure"""
        return {
            "events": [],
            "playerStats": [],
            "rounds": [],
            "chatMessages": [],
            "playerDropdown": ["All Players"],
            "roundDropdown": ["All Rounds"],
            "parser_version": self.schema_version,
            "total_events": 0,
            "parsed_at": datetime.now().isoformat(),
            "demo_file": "no_demo.dem",
            "metadata": {
                "total_players": 0,
                "total_rounds": 0,
                "total_chat_messages": 0,
                "parser_version": self.schema_version
            }
        }
    
    def validate_schema(self, data):
        """Validate data against GUI requirements"""
        try:
            if not isinstance(data, dict):
                return False
            
            required_keys = ["events", "playerStats", "rounds", "playerDropdown", "roundDropdown"]
            for key in required_keys:
                if key not in data:
                    log.error(f"Missing required key: {key}")
                    return False
            
            # Validate parser version
            if data.get("parser_version") != self.schema_version:
                log.warning(f"Parser version mismatch: {data.get('parser_version')} != {self.schema_version}")
            
            return True
            
        except Exception as e:
            log.error(f"Schema validation failed: {e}")
            return False


# Global instance
schema_adapter = SchemaAdapter()

# Convenience functions
def adapt_data(data, source_format="cs2_events"):
    """Adapt CS2 data to GUI-compatible schema"""
    return schema_adapter.adapt_cs2_data(data, source_format)

def validate_data(data):
    """Validate data against GUI schema"""
    return schema_adapter.validate_schema(data)

# Export list
__all__ = ["SchemaAdapter", "schema_adapter", "adapt_data", "validate_data"]
