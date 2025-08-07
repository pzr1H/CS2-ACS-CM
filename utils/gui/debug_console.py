#!/usr/bin/env python3
# =============================================================================
# gui.debug_console.py — Centralized Logger + Future Log for Diagnostics
# Timestamp-TOP: 2025-07-25 | v1.0-PATCHED
# =============================================================================

import logging
import time
import inspect
import functools
from logging.handlers import RotatingFileHandler

# =============================================================================
# BLOCK 1 — Shared Logger Registry (Used Across Modules)
# =============================================================================

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.hasHandlers():
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            "%Y-%m-%d %H:%M:%S"
        )

        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)

        file_handler = RotatingFileHandler(
            filename="debug.log",
            maxBytes=1_000_000,  # 1MB
            backupCount=3
        )
        file_handler.setFormatter(formatter)

        logger.addHandler(stream_handler)
        logger.addHandler(file_handler)

    return logger

# ✅ Patched: global logger instance for this module
log = get_logger(__name__)

# =============================================================================
# BLOCK 2 — Decorator: Trace-Level Logging for Entry/Exit/Error
# =============================================================================

def trace(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        module = func.__module__
        func_name = func.__qualname__
        arg_str = ", ".join([repr(a) for a in args] +
                            [f"{k}={v!r}" for k, v in kwargs.items()])

        log.debug(f"🔍 ENTER: {module}.{func_name}({arg_str})")
        start = time.time()
        try:
            result = func(*args, **kwargs)
            elapsed = time.time() - start
            log.debug(f"✅ EXIT: {module}.{func_name} [Took {elapsed:.4f}s]")
            return result
        except Exception as e:
            log.exception(f"💥 ERROR in {module}.{func_name}: {e}")
            raise

    return wrapper

# =============================================================================
# BLOCK 3 — Lightweight Trace Logging (Minimal)
# =============================================================================

def trace_log(source, message):
    print(f"[{source.upper()}] {message}")


# =============================================================================
# BLOCK 4 — Future Log Hooks (Cross-Module Debugging Events)
# =============================================================================

_future_log = []

def future_log(message: str, level: str = "info", source: str = "external"):
    entry = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "level": level,
        "source": source,
        "message": message
    }
    _future_log.append(entry)

    if level == "debug":
        log.debug(f"[{source}] {message}")
    elif level == "warning":
        log.warning(f"[{source}] {message}")
    elif level == "error":
        log.error(f"[{source}] {message}")
    else:
        log.info(f"[{source}] {message}")

def get_future_log():
    return _future_log.copy()

def clear_future_log():
    _future_log.clear()

# =============================================================================
# BLOCK 5 — Exports
# =============================================================================
# 🔄 Decorator alias for legacy modules using @trace_log
trace_log = trace
__all__ = [
    "get_logger",
    "trace",
    "trace_log",
    "future_log",
    "get_future_log",
    "clear_future_log"
]

# =============================================================================
# EOF — gui.debug_console.py (v1.0-PATCHED)
# - ✅ Global logger shared across modules
# - ✅ trace and trace_log decorators for performance and lightweight tracing
# - ✅ future_log diagnostics with level/source metadata
# - ✅ Confirmed import compatibility and availability of `trace_log`
# =============================================================================
#LOC ~130 pzr1H jul 25 2025 - 10:30am ET