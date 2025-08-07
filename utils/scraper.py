"""
Minimal scraper module for scout_report compatibility
"""

def default_scraper_function(*args, **kwargs):
    """Default fallback scraper function"""
    return {}

# Provide common scraper functions as fallbacks
steam_scraper = default_scraper_function
faceit_scraper = default_scraper_function
csst_scraper = default_scraper_function
legitproof_scraper = default_scraper_function
