# scraper_dispatch.py
# =====================================================
# Combines results from all scraper modules under /scrapers
# Entry point: fetch_enriched_profile(steamid64: str) -> dict
# Uses fallback + merging + tagging of source reliability
# =====================================================

import logging
from scraper.faceitfinder_scraper import scrape_faceitfinder_profile
from scraper.csst_scraper import scrape_csst_profile
from scraper.legitproof_scraper import scrape_legitproof_profile
from scrapers.csgo_gg_scraper import scrape_csgo_gg_profile
from scraper.steam_scraper import scrape_steam_profile
from utils.scout_fallback_extractor import fallback_extract  # 🔁 Optional fallback

logger = logging.getLogger("scraper_dispatch")

SCRAPERS = [
    scrape_steam_profile,
    scrape_faceitfinder_profile,
    scrape_csst_profile,
    scrape_legitproof_profile,
    scrape_csgo_gg_scraper
]


def fetch_enriched_profile(steamid64: str, raw_data: dict = None, verbose: bool = False) -> dict:
    """
    Attempts to enrich scout data via scrapers.
    Falls back to local demo JSON data if scrapers fail.
    """
    final = {"steamid64": steamid64, "sources": [], "fallback_used": False}

    for scraper in SCRAPERS:
        try:
            result = scraper(steamid64)
            if "error" in result:
                if verbose:
                    logger.warning(f"{scraper.__name__} failed: {result['error']}")
                continue

            src = result.pop("source", scraper.__name__)
            final["sources"].append(src)
            final.update(result)
        except Exception as e:
            logger.error(f"Scraper {scraper.__name__} crashed: {e}")

    # 🛑 If nothing retrieved and we have raw demo data, attempt local fallback
    if len(final) <= 3 and raw_data:
        try:
            fallback = fallback_extract(raw_data)
            final.update({
                "metadata": fallback.get("metadata", {}),
                "playerStats": fallback.get("playerStats", {}),
                "fallback_used": True,
                "sources": final.get("sources", []) + ["fallback_extract"]
            })
        except Exception as e:
            logger.warning(f"⚠️ Fallback extract failed in dispatch: {e}")

    return final


if __name__ == "__main__":
    import sys
    import json
    if len(sys.argv) < 2:
        print("Usage: python scraper_dispatch.py <steamid64> [optional_json_file]")
    else:
        data = None
        if len(sys.argv) == 3:
            with open(sys.argv[2], 'r') as f:
                data = json.load(f)
        enriched = fetch_enriched_profile(sys.argv[1], raw_data=data, verbose=True)
        print(json.dumps(enriched, indent=2))
