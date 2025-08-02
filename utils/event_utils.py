# File: utils/event_utils.py

def is_weapon_fire_event(event: dict) -> bool:
    return event.get("type") == "weapon_fire"

def is_player_spotted_event(event: dict) -> bool:
    return event.get("type") == "player_spotted"

def is_player_hurt_event(event: dict) -> bool:
    return event.get("type") == "player_hurt"
