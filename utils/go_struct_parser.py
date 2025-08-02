#!/usr/bin/env python3
# =============================================================================
# utils/go_struct_parser.py — Go Struct Parser Fallback
# =============================================================================

import logging
import re

log = logging.getLogger(__name__)

class CS2GoStructParser:
    """Fallback Go struct parser for CS2 data"""
    
    @staticmethod
    def parse_player_info(struct_string: str):
        """Parse player info from Go struct string"""
        try:
            # Extract XUID
            xuid_match = re.search(r'XUID:(0x[0-9a-fA-F]+)', struct_string)
            # Extract Name
            name_match = re.search(r'Name:"([^"]+)"', struct_string)
            
            if xuid_match and name_match:
                xuid = int(xuid_match.group(1), 16)
                name = name_match.group(1)
                
                # Convert to Steam2
                from utils.steam_utils import to_steam2
                steam2 = to_steam2(xuid)
                
                return {
                    'name': name,
                    'steamid': str(xuid),
                    'steam2': steam2
                }
            
            return None
            
        except Exception as e:
            log.warning(f"Go struct parsing failed: {e}")
            return None