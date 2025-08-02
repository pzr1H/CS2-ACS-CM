#!/usr/bin/env python3
# =============================================================================
# utils/steam_utils.py — Steam ID Conversion and Utilities
# Handles conversion between SteamID formats for CS2 ACS
# =============================================================================

import re
from typing import Union, Optional

def to_steam2(steamid: Union[int, str]) -> str:
    """
    Convert SteamID64 to Steam2 format (STEAM_1:X:Y)
    
    Args:
        steamid: SteamID64 as integer or string
        
    Returns:
        Steam2 format string (STEAM_1:X:Y)
    """
    try:
        # Convert to integer if string
        if isinstance(steamid, str):
            steamid = int(steamid)
        
        # Validate range for SteamID64
        if steamid < 76561197960265728:  # Base SteamID64 value
            return "STEAM_0:0:0"
        
        # Calculate Steam2 components
        # SteamID64 = 76561197960265728 + (AccountID * 2) + AuthServer
        account_number = steamid - 76561197960265728
        auth_server = account_number % 2
        account_id = account_number // 2
        
        return f"STEAM_1:{auth_server}:{account_id}"
        
    except (ValueError, TypeError):
        return "STEAM_0:0:0"

def to_steam3(steamid: Union[int, str]) -> str:
    """
    Convert SteamID64 to Steam3 format ([U:1:XXXXXX])
    
    Args:
        steamid: SteamID64 as integer or string
        
    Returns:
        Steam3 format string ([U:1:XXXXXX])
    """
    try:
        if isinstance(steamid, str):
            steamid = int(steamid)
        
        if steamid < 76561197960265728:
            return "[U:1:0]"
        
        account_id = steamid - 76561197960265728
        return f"[U:1:{account_id}]"
        
    except (ValueError, TypeError):
        return "[U:1:0]"

def steam2_to_steam64(steam2: str) -> Optional[int]:
    """
    Convert Steam2 format to SteamID64
    
    Args:
        steam2: Steam2 format string (STEAM_X:Y:Z)
        
    Returns:
        SteamID64 as integer or None if invalid
    """
    try:
        # Match STEAM_X:Y:Z format
        match = re.match(r"STEAM_([0-5]):([01]):(\d+)", steam2)
        if not match:
            return None
        
        universe, auth_server, account_id = match.groups()
        auth_server = int(auth_server)
        account_id = int(account_id)
        
        # Calculate SteamID64
        steamid64 = 76561197960265728 + (account_id * 2) + auth_server
        return steamid64
        
    except (ValueError, TypeError):
        return None

def steam3_to_steam64(steam3: str) -> Optional[int]:
    """
    Convert Steam3 format to SteamID64
    
    Args:
        steam3: Steam3 format string ([U:1:XXXXXX])
        
    Returns:
        SteamID64 as integer or None if invalid
    """
    try:
        # Match [U:1:XXXXXX] format
        match = re.match(r"\[U:1:(\d+)\]", steam3)
        if not match:
            return None
        
        account_id = int(match.group(1))
        steamid64 = 76561197960265728 + account_id
        return steamid64
        
    except (ValueError, TypeError):
        return None

def validate_steamid64(steamid: Union[int, str]) -> bool:
    """
    Validate if a SteamID64 is in the correct format and range
    
    Args:
        steamid: SteamID64 to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        if isinstance(steamid, str):
            if not steamid.isdigit():
                return False
            steamid = int(steamid)
        
        # Check if it's in the valid SteamID64 range
        # Minimum value: 76561197960265728 (STEAM_1:0:0)
        # Maximum reasonable value: ~76561202255233023 (allowing for ~4 billion accounts)
        return 76561197960265728 <= steamid <= 76561202255233023
        
    except (ValueError, TypeError):
        return False

def validate_steam2(steam2: str) -> bool:
    """
    Validate Steam2 format
    
    Args:
        steam2: Steam2 string to validate
        
    Returns:
        True if valid format, False otherwise
    """
    try:
        if not isinstance(steam2, str):
            return False
        
        # Check STEAM_X:Y:Z format where X=0-5, Y=0-1, Z is positive integer
        pattern = r"^STEAM_[0-5]:[01]:\d+$"
        return bool(re.match(pattern, steam2))
        
    except:
        return False

def normalize_steamid(steamid: Union[int, str]) -> dict:
    """
    Convert a SteamID to all common formats
    
    Args:
        steamid: SteamID in any format (SteamID64, Steam2, Steam3)
        
    Returns:
        Dictionary with all formats or None values if invalid
    """
    try:
        result = {
            "steamid64": None,
            "steam2": None,
            "steam3": None,
            "valid": False
        }
        
        steamid_str = str(steamid)
        
        # Try to determine input format and convert
        if steamid_str.isdigit():
            # Assume SteamID64
            steamid64 = int(steamid_str)
            if validate_steamid64(steamid64):
                result["steamid64"] = steamid64
                result["steam2"] = to_steam2(steamid64)
                result["steam3"] = to_steam3(steamid64)
                result["valid"] = True
                
        elif steamid_str.startswith("STEAM_"):
            # Steam2 format
            if validate_steam2(steamid_str):
                steamid64 = steam2_to_steam64(steamid_str)
                if steamid64:
                    result["steamid64"] = steamid64
                    result["steam2"] = steamid_str
                    result["steam3"] = to_steam3(steamid64)
                    result["valid"] = True
                    
        elif steamid_str.startswith("[U:1:"):
            # Steam3 format
            steamid64 = steam3_to_steam64(steamid_str)
            if steamid64:
                result["steamid64"] = steamid64
                result["steam2"] = to_steam2(steamid64)
                result["steam3"] = steamid_str
                result["valid"] = True
        
        return result
        
    except:
        return {
            "steamid64": None,
            "steam2": None, 
            "steam3": None,
            "valid": False
        }

def extract_steamids_from_text(text: str) -> list:
    """
    Extract all valid SteamIDs from a text string
    
    Args:
        text: Text to search for SteamIDs
        
    Returns:
        List of dictionaries with found SteamIDs in all formats
    """
    try:
        found_ids = []
        
        # Look for SteamID64 (17-digit numbers starting with 765)
        steamid64_pattern = r'\b765\d{14}\b'
        for match in re.finditer(steamid64_pattern, text):
            steamid64 = int(match.group())
            if validate_steamid64(steamid64):
                normalized = normalize_steamid(steamid64)
                if normalized["valid"]:
                    found_ids.append(normalized)
        
        # Look for Steam2 format
        steam2_pattern = r'\bSTEAM_[0-5]:[01]:\d+\b'
        for match in re.finditer(steam2_pattern, text):
            steam2 = match.group()
            normalized = normalize_steamid(steam2)
            if normalized["valid"]:
                found_ids.append(normalized)
        
        # Look for Steam3 format
        steam3_pattern = r'\[U:1:\d+\]'
        for match in re.finditer(steam3_pattern, text):
            steam3 = match.group()
            normalized = normalize_steamid(steam3)
            if normalized["valid"]:
                found_ids.append(normalized)
        
        # Remove duplicates based on steamid64
        unique_ids = []
        seen_steamids = set()
        for steamid_data in found_ids:
            steamid64 = steamid_data["steamid64"]
            if steamid64 not in seen_steamids:
                seen_steamids.add(steamid64)
                unique_ids.append(steamid_data)
        
        return unique_ids
        
    except:
        return []

def get_account_age_estimate(steamid: Union[int, str]) -> str:
    """
    Estimate account creation period based on SteamID64
    
    Args:
        steamid: SteamID64 to analyze
        
    Returns:
        Estimated time period string
    """
    try:
        if isinstance(steamid, str):
            steamid = int(steamid)
        
        if not validate_steamid64(steamid):
            return "Invalid SteamID"
        
        account_number = steamid - 76561197960265728
        
        # Very rough estimates based on Steam account creation patterns
        if account_number < 10000000:  # ~10M
            return "2003-2007 (Very Old)"
        elif account_number < 50000000:  # ~50M
            return "2007-2012 (Old)"
        elif account_number < 150000000:  # ~150M
            return "2012-2017 (Established)"
        elif account_number < 300000000:  # ~300M
            return "2017-2020 (Recent)"
        else:
            return "2020+ (New)"
            
    except:
        return "Unknown"

def is_likely_alt_account(steamid: Union[int, str], hours_threshold: int = 100) -> dict:
    """
    Analyze if account characteristics suggest it might be an alt/smurf
    
    Args:
        steamid: SteamID64 to analyze
        hours_threshold: Hour threshold for new account consideration
        
    Returns:
        Dictionary with analysis results
    """
    try:
        age_estimate = get_account_age_estimate(steamid)
        
        # This is a basic heuristic - would need additional data for accuracy
        result = {
            "account_age_estimate": age_estimate,
            "likely_alt": False,
            "confidence": "Low",
            "reasons": []
        }
        
        if "New" in age_estimate or "Recent" in age_estimate:
            result["reasons"].append("Relatively new account")
            result["likely_alt"] = True
            result["confidence"] = "Medium"
        
        # Additional checks would require game hours, friend count, etc.
        # which aren't available just from SteamID
        
        return result
        
    except:
        return {
            "account_age_estimate": "Unknown",
            "likely_alt": False,
            "confidence": "None",
            "reasons": ["Analysis failed"]
        }

# Utility functions for common operations
def format_steamid_for_display(steamid: Union[int, str], format_type: str = "steam2") -> str:
    """
    Format SteamID for display purposes
    
    Args:
        steamid: SteamID in any format
        format_type: Desired output format ("steam2", "steam3", "steamid64")
        
    Returns:
        Formatted SteamID string
    """
    try:
        normalized = normalize_steamid(steamid)
        if not normalized["valid"]:
            return "Invalid SteamID"
        
        if format_type.lower() == "steam2":
            return normalized["steam2"]
        elif format_type.lower() == "steam3":
            return normalized["steam3"]
        elif format_type.lower() == "steamid64":
            return str(normalized["steamid64"])
        else:
            return normalized["steam2"]  # Default to Steam2
            
    except:
        return "Error"

# Batch processing utilities
def process_steamid_list(steamids: list) -> list:
    """
    Process a list of SteamIDs and normalize them
    
    Args:
        steamids: List of SteamIDs in various formats
        
    Returns:
        List of normalized SteamID dictionaries
    """
    try:
        results = []
        for steamid in steamids:
            normalized = normalize_steamid(steamid)
            if normalized["valid"]:
                results.append(normalized)
        return results
    except:
        return []