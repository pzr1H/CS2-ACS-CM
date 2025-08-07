import os
import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../cs2_parser")))
import os
import requests
from PIL import Image
from io import BytesIO

CACHE_DIR = os.path.join(os.path.dirname(__file__), "cache", "avatars")
os.makedirs(CACHE_DIR, exist_ok=True)

def download_avatar(steamid, url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        img = Image.open(BytesIO(response.content))
        path = os.path.join(CACHE_DIR, f"{steamid}.png")
        img.save(path)
        return path
    except Exception as e:
        print(f"[Avatar Fetch Fail] {steamid}: {e}")
        return None