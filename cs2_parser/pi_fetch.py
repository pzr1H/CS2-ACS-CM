#!/usr/bin/env python3
"""
# pi_fetch.py (alias for scouting_report.py)

# Fetch external Steam data to augment player stats, including:
# - persona name
# - VAC, community, and game bans
# - economy bans
# - hours played for CS2
# - friend list and their ban statuses
# - profile comments and count of cheating-related comments
# Implements:
# - steamid64_to_steam2 conversion
# - fetch_scout_data(steam64_list, api_key)
# - simple file-based cache with TTL
# - fetch_profile_comments(sid64)
"""
import os
import json
import time
from typing import List, Dict
import requests
from bs4 import BeautifulSoup

# Cache settings
CACHE_DIR = os.path.join(os.path.dirname(__file__), 'cache')
CACHE_FILE = os.path.join(CACHE_DIR, 'steam_scout.json')
CACHE_TTL = 24 * 3600  # seconds

# Steam Web API endpoints
STEAM_SUMMARIES_URL = "https://api.steampowered.com/ISteamUser/GetPlayerSummaries/v2/"
STEAM_BANS_URL = "https://api.steampowered.com/ISteamUser/GetPlayerBans/v1/"
STEAM_OWNED_GAMES_URL = "https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/"
STEAM_FRIENDS_URL = "https://api.steampowered.com/ISteamUser/GetFriendList/v1/"
# Steam comment render endpoint
PROFILE_COMMENTS_URL = "https://steamcommunity.com/comment/Profile/render/{sid64}/?start={start}&count={count}&format=json"

# App ID for CS2 (same as CS:GO)
APP_ID_CS2 = 730
# Keywords for cheating comments
CHEAT_KEYWORDS = ['cheat', 'hack', 'wh', 'aimbot', 'wallhack', 'spinbot']


def steamid64_to_steam2(sid64_str: str) -> str:
    """
    Convert a 64-bit SteamID string to STEAM_1:Y:Z format.
    """
    STEAM64_BASE = 76561197960265728
    sid64 = int(sid64_str)
    y = sid64 % 2
    z = (sid64 - STEAM64_BASE - y) // 2
    return f"STEAM_1:{y}:{z}"


def _load_cache() -> Dict:
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save_cache(cache: Dict):
    os.makedirs(CACHE_DIR, exist_ok=True)
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


def fetch_profile_comments(sid64: str, max_comments: int = 20) -> List[str]:
    """
    Fetch recent profile comments for a Steam64 ID via SteamCommunity render JSON.
    Returns a list of comment texts.
    """
    url = PROFILE_COMMENTS_URL.format(sid64=sid64, start=0, count=max_comments)
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        data = resp.json()
        html = data.get('comments_html', '')
        soup = BeautifulSoup(html, 'html.parser')
        comments = []
        for div in soup.select('.commentthread_comment_text'):
            text = div.get_text(separator=' ', strip=True)
            comments.append(text)
        return comments
    except Exception:
        return []


def fetch_scout_data(steam64_list: List[str], api_key: str) -> Dict[str, Dict]:
    """
    Fetch profile, ban, playtime, friend-ban, and comment info for a list of Steam64 IDs.
    Returns mapping from STEAM_1 IDs to data dict:
      {
        'persona_name': str,
        'vac_banned': bool,
        'community_banned': bool,
        'game_bans': int,
        'economy_ban': str,
        'hours_played_cs2': float,
        'friends_vac_banned': int,
        'comments': List[str],
        'cheating_comments_count': int
      }
    Uses TTL-based caching to limit API calls.
    """
    cache = _load_cache()
    now = time.time()
    result: Dict[str, Dict] = {}
    to_fetch = []

    # Determine which IDs need fetching
    for sid64 in steam64_list:
        entry = cache.get(sid64)
        if entry and now - entry.get('cached_at', 0) < CACHE_TTL:
            data = entry['data']
            steam2 = steamid64_to_steam2(sid64)
            result[steam2] = data
        else:
            to_fetch.append(sid64)

    # Batch fetch summaries and bans
    for i in range(0, len(to_fetch), 100):
        batch = to_fetch[i:i+100]
        ids_param = ",".join(batch)
        # Player summaries
        resp = requests.get(STEAM_SUMMARIES_URL, params={'key': api_key, 'steamids': ids_param})
        resp.raise_for_status()
        players = resp.json().get('response', {}).get('players', [])

        # Player bans
        resp2 = requests.get(STEAM_BANS_URL, params={'key': api_key, 'steamids': ids_param})
        resp2.raise_for_status()
        bans = resp2.json().get('players', [])
        ban_map = {b['SteamId']: b for b in bans}

        # Process each player in batch
        for p in players:
            sid64 = str(p['steamid'])
            steam2 = steamid64_to_steam2(sid64)
            persona_name = p.get('personaname', '')
            ban_info = ban_map.get(sid64, {})
            vac_banned = ban_info.get('VACBanned', False)
            community_banned = ban_info.get('CommunityBanned', False)
            game_bans = ban_info.get('NumberOfGameBans', 0)
            economy_ban = ban_info.get('EconomyBan', 'none')

            # Hours played for CS2
            hours_played_cs2 = 0.0
            try:
                og = requests.get(STEAM_OWNED_GAMES_URL, params={
                    'key': api_key,
                    'steamid': sid64,
                    'include_appinfo': 'false',
                    'appids_filter': APP_ID_CS2
                })
                og.raise_for_status()
                games = og.json().get('response', {}).get('games', [])
                for g in games:
                    if g.get('appid') == APP_ID_CS2:
                        minutes = g.get('playtime_forever', 0)
                        hours_played_cs2 = round(minutes / 60.0, 2)
            except Exception:
                pass

            # Friends list and VAC bans among friends
            friends_vac = 0
            try:
                fr = requests.get(STEAM_FRIENDS_URL, params={'key': api_key, 'steamid': sid64, 'relationship': 'friend'})
                fr.raise_for_status()
                friends = fr.json().get('friendslist', {}).getitem('friends', [])
                friend_ids = [f['steamid'] for f in friends]
                for j in range(0, len(friend_ids), 100):
                    fbatch = friend_ids[j:j+100]
                    fbans = requests.get(STEAM_BANS_URL, params={'key': api_key, 'steamids': ",".join(fbatch)})
                    fbans.raise_for_status()
                    for fb in fbans.json().get('players', []):
                        if fb.get('VACBanned', False):
                            friends_vac += 1
            except Exception:
                pass

            # Profile comments and cheating-related comment count
            comments = fetch_profile_comments(sid64)
            cheating_comments = sum(1 for c in comments if any(k in c.lower() for k in CHEAT_KEYWORDS))

            data = {
                'persona_name': persona_name,
                'vac_banned': vac_banned,
                'community_banned': community_banned,
                'game_bans': game_bans,
                'economy_ban': economy_ban,
                'hours_played_cs2': hours_played_cs2,
                'friends_vac_banned': friends_vac,
                'comments': comments,
                'cheating_comments_count': cheating_comments
            }
            result[steam2] = data
            cache[sid64] = {'cached_at': now, 'data': data}

    _save_cache(cache)
    return result


if __name__ == "__main__":
    import os
    key = os.getenv("D39510F5F2FBA1F93A487C0D74AC1E6F")
    if not key:
        print("Please set STEAM_API_KEY environment variable.")
        exit(1)
    # Example usage
    ids = ["76561197960274194"]
    stats = fetch_scout_data(ids, key)
    print(json.dumps(stats, indent=2))
#217 pzr1H 8======D 