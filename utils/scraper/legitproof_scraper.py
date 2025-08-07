# legitproof_scraper.py
# =======================================================
# Scraper for LegitProof.com profiles
# Purpose: Extract VAC status, risk level, alias history, time since last ban
# Target URL: https://legitproof.com/profile/{steamid64}
# =======================================================

import requests
from bs4 import BeautifulSoup
import logging

logger = logging.getLogger("legitproof_scraper")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                  " (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
}

BASE_URL = "https://legitproof.com/profile/"


def scrape_legitproof_profile(steamid64: str) -> dict:
    url = f"{BASE_URL}{steamid64}"
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        if resp.status_code != 200:
            logger.warning(f"LegitProof returned {resp.status_code} for {steamid64}")
            return {"error": f"HTTP {resp.status_code}"}

        soup = BeautifulSoup(resp.text, "html.parser")
        result = {"source": "legitproof"}

        # Risk Level (e.g., Low Risk, Medium Risk)
        risk_tag = soup.find("div", class_="risk-level")
        if risk_tag:
            result["risk_level"] = risk_tag.get_text(strip=True)

        # VAC / Ban status (delay-based timeline)
        vac_div = soup.find("div", class_="ban-indicator")
        if vac_div:
            result["ban_status"] = vac_div.get_text(strip=True)

        # Alias history
        alias_list = []
        alias_section = soup.find("div", class_="alias-history")
        if alias_section:
            for li in alias_section.find_all("li"):
                alias_list.append(li.get_text(strip=True))
            result["aliases"] = alias_list

        # Time since last ban (if shown)
        time_ban = soup.find(string=lambda s: s and "last ban" in s.lower())
        if time_ban:
            result["last_ban_timing"] = time_ban.strip()

        return result if len(result) > 1 else {"error": "No LegitProof data parsed"}

    except Exception as e:
        logger.error(f"LegitProof scraping failed: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 2:
        print("Usage: python legitproof_scraper.py <steamid64>")
    else:
        output = scrape_legitproof_profile(sys.argv[1])
        print(json.dumps(output, indent=2))
