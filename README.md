UPDATE README TO V3 INT

## CS2-ACS-v2-A2M Forensic Inspection & Audit

### File Structure (with TLOC, Functions, and Responsibilities):
```
CS2-ACS-v2/
│
├── CS2-ACS-v2.exe                            # Pre-compiled v2 parser binary
├── file_loader.py (466 TLOC, 14 functions)   # Loads demo output files, manages V2/V3/legacy support, SteamID conversion
├── log_utils.py (11 TLOC, 1 function)         # Centralized logging configuration
├── main.py (1392 TLOC, 69 functions)          # Tkinter GUI logic, tab routing, user interaction, dropdowns, scout reporting
├── trace_debug.py (20 TLOC, 1 function)       # Debugging utility for logging snapshots
├── trace_debug_gui.py (13 TLOC, 2 functions)  # Simple debug overlay window with logging pane
│
├── asset/                                     # GUI assets and legacy backups
│   ├── CS2-col.png, CS2-gray.png, CS2.png      # Logo variants
│   ├── CS2-tb-fill.gif                         # Animated banner
│   ├── file structure.png, image.png           # Diagrams/screenshots
│   └── old.main.py (230 TLOC)                 # Legacy main.py snapshot
│
├── cs2_parser/                                # Core parsing and visualization logic
│   ├── chat_summary.py (61 TLOC, 3 functions)         # Chat log rendering and trace binding
│   ├── damage_summary.py (70 TLOC, 3 functions)       # Damage timeline tab with click-to-jump
│   ├── event_log.py (163 TLOC, 8 functions)           # Central event log tab with filters and export
│   ├── fallback_parser.py (106 TLOC, 2 functions)     # Generates stat estimates if parsing fails
│   ├── replay_round.py (900 TLOC, 24 functions)       # Round replay tab logic and tactical breakdowns
│   ├── stats_builder.py (136 TLOC, 4 functions)       # Derives player statistics from event streams
│   └── stats_summary.py (49 TLOC, 1 function)         # Builds player stat overview tab
│
└── utils/
    ├── avatar_downloader.py (21 TLOC, 1 function)      # Downloads Steam avatars
    ├── cross_module_debugging.py (105 TLOC, 7 functions) # Cross-module trace hooks, forward logs
    ├── data_sanitizer.py (566 TLOC, 16 functions)       # Validates, repairs, and normalizes demo output
    ├── dropdown_utils.py (176 TLOC, 5 functions)        # Player dropdown extraction from various formats
    ├── event_utils.py (7 TLOC, 3 functions)             # Lightweight event type helpers
    ├── go_struct_parser.py (32 TLOC, 1 function)        # Parses Go struct text dumps for debugging
    ├── logging_config.py (38 TLOC, 1 function)          # Alternate logger setup
    ├── navmesh_utils.py (139 TLOC, 8 functions)         # Exports movement and aim sequences
    ├── pi_fetch.py (211 TLOC, 5 functions)              # API + cache fetch for scout profiles
    ├── risk_score.py (16 TLOC, 2 functions)             # Threat tiering from profile stats
    ├── round_dropdown_utils.py (314 TLOC, 9 functions)  # Builds round dropdown and metadata
    ├── round_utils.py (44 TLOC, 1 function)             # Converts round metadata to playback form
    ├── sanitizer_report.py (481 TLOC, 12 functions)     # Generates logs, reports, patched output
    ├── scraper_dispatch.py (64 TLOC, 1 function)        # Entry point for profile fetch and merge
    ├── steam_utils.py (315 TLOC, 12 functions)          # Steam ID conversions and analysis
    ├── tickrate.py (5 TLOC, 1 function)                 # Extracts tickrate from metadata
    ├── gui/
    │   ├── debug_console.py (105 TLOC, 7 functions)     # GUI logger window (possibly redundant)
    │   ├── enhanced_profile_block.py (40 TLOC, 1 function) # Builds GUI profile card
    │   └── scout_report.py (102 TLOC, 4 functions)       # Profile assessment, threat level logic
    └── scrapers/
        ├── csst_scraper.py (50 TLOC, 1 function)        # Scrapes CSST player page
        ├── faceitfinder_scraper.py (55 TLOC, 1 function)# Scrapes FaceitFinder page
        ├── legitproof_scraper.py (55 TLOC, 1 function)  # Scrapes LegitProof player data
        ├── scout_fallback_extractor.py (142 TLOC, 6 functions) # Rebuilds partial profiles from events
        └── steam_scraper.py (51 TLOC, 1 function)       # Extracts Steam public profile data
```

### Data Flow Diagram:
```
User selects .dem file
   ↓
file_loader.py parses JSON via CS2-ACS-v2.exe
   ↓
file_loader returns dict → passed to main.py
   ↓
main.py uses:
    → cs2_parser modules to populate tabs
    → utils modules for sanitization + fallback
    → gui/scout_report.py for profile scoring
   ↓
All output routed into Tkinter UI (main.py)
```

### Checklist:
- [ ] Validate each scraper module and error fallback logic
- [ ] Confirm dropdown generation works with legacy + v2
- [ ] Stress test `replay_round.py` for out-of-bounds events
- [ ] Conduct runtime memory footprint analysis (Tkinter threads)
- [ ] Trace GUI tab build order for load performance
- [ ] Ensure all JSON formats have valid fallback mode
- [ ] Confirm debug logging is scoped correctly and not leaking

### Challenges:
- 🔄 Parsing must gracefully degrade across v1, v2, fallback, partial
- 🔐 Anti-cheat logic must not be spoofable — audit profile spoof defenses
- 🧩 Steam ID conversion logic must be 100% reliable, or profile mapping will break
- 🕵️ Replay event binding must match metadata (tick, round, player)

### Knowledge Transfer Brief:
This repo is a high-integrity parser frontend for Counter-Strike 2 matches. It leverages a compiled Go-based parser (CS2-ACS-v2.exe) to emit JSON, then post-processes this via Python. The Python GUI provides forensic-level inspection of match data, using a modular parser suite and enriched online profile fetchers. Scrapers are used to compute scouting reports for every player, and all modules are audited for fallback and validation.

### Next Steps:
1. [ ] Validate Steam profile parsing with offline cache disabled
2. [ ] Confirm correct population of dropdowns for all demo types
3. [ ] Expand `risk_score.py` to include match behavior, not just profile stats
4. [ ] Re-enable `trace_debug_gui.py` in safe testing mode with toggle
5. [ ] Test failover scenarios in air-gapped and spoofed data conditions

### Onboarding Recommendations:
- Start from `main.py`, trace dropdown + file loading logic
- Open a `.dem` file and observe logging/output behavior
- Review all `cs2_parser` tab builders for UI data rendering
- Check fallback handling in `file_loader.py` and `data_sanitizer.py`
- Validate a full match walkthrough using replay_round and export

