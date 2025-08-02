#!/usr/bin/env python3
# =============================================================================
# logging_config.py — Centralized Logging Setup for CS2 ACS Project
# Timestamp: 2025-07-26 | Author: Athlenia QA + pzr1H
# =============================================================================

import logging
import logging.handlers
import os

LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'cs2_acs.log')

def setup_logging(level=logging.WARNING):
    """Set up centralized rotating file logger with console fallback (console minimal)."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILE, maxBytes=5*1024*1024, backupCount=5, encoding='utf-8'
    )
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)-8s | %(name)s | %(message)s', '%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    logger.addHandler(file_handler)

    # Minimal console handler to show warnings and errors only
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)

    logger.info(f"Logging initialized. Log file: {LOG_FILE}")
    return logger

# Initialize on import with WARNING level by default
logger = setup_logging()
