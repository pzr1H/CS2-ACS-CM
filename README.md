# CS2-ACS (Carmack Edition)

## Overview

CS2-ACS is a comprehensive pipeline for parsing Counter-Strike 2 demo files using a Go-based parser (`CS2-ACS-v3.exe`), extracting structured event data, and visualizing the results via a Python GUI. The project integrates demoinfocs-golang v5 for demo parsing and provides anti-cheat analytics, performance summaries, and customizable snapshot intervals.

## Table of Contents

1. [Features](#features)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Usage](#usage)
   - [CLI Parser](#cli-parser)
   - [Python GUI](#python-gui)
5. [Configuration & Flags](#configuration--flags)
6. [Project Structure](#project-structure)
7. [Module Descriptions](#module-descriptions)
8. [Known Issues](#known-issues)
9. [Roadmap & To-Do](#roadmap--to-do)
10. [Contributing](#contributing)
11. [License](#license)

---

## Features

- **High-fidelity parsing** of CS2 demo files with demoinfocs-golang v5
- **Streaming & batched JSON output** with adjustable batch size
- **Python GUI** for event visualization, stats summaries, and anti-cheat reporting
- **Customizable snapshot intervals** that auto-adjust based on tickrate or suspicious behavior
- **Silent logging** of suspicious events, with debug export and in-GUI debugging tab

## Prerequisites

- Windows, macOS, or Linux
- Go 1.20+ (for rebuilding parser)
- Python 3.10+ with the following packages (see `requirements.txt`):
  - `PyQt5` or `tkinter` (depending on GUI)
  - `pandas`, `matplotlib`
  - `demoinfocs-golang` (if rebuilding from source)

> **Note:** A `requirements.txt` is not present—please generate one to capture Python dependencies.

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/pzr1H/CS2-ACS-CM.git
   cd CS2-ACS-CM
   ```

2. **Build or download the parser executable**:
   - Precompiled: `CS2-ACS-v3.exe` is included in the root directory.
   #LIES- Build from source (requires Go):
     ```bash
     cd cs2_parser
     go build -o ../CS2-ACS-v3.exe
     ```#LIES ^^
3. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### CLI Parser

```bash
# Produce streaming NDJSON
./CS2-ACS-v3.exe --demo ./demos/your_demo.dem | jq -s '.' > full_output.json

# Batched JSON arrays
./CS2-ACS-v3.exe --demo ./demos/your_demo.dem --disable-ndjson --batch-size 500 --output-dir pewpew
```

### Python GUI

```bash
cd utils/gui
python main.py --input-json ../pewpew/your_demo.json --snapshot-interval 0.5
```

> **Tip:** Use the `--log-level debug` flag on the parser to diagnose schema issues.

## Configuration & Flags

| Flag                | Description                                          | Default      |
| ------------------- | ---------------------------------------------------- | ------------ |
| `--demo`            | Path to `.dem` file                                  | *(required)* |
| `--batch-size`      | Number of events per JSON batch                      | `1000`       |
| `--capture-packets` | Include raw packet data in PCAP format               | `false`      |
| `--disable-ndjson`  | Disable streaming NDJSON (use batched output)        | `false`      |
| `--output-dir`      | Directory for parser output files                    | `pewpew/`    |
| `--schema-dir`      | Directory containing JSON schema definitions         | `schemas/`   |
| `--log-level`       | Logging verbosity (`debug`, `info`, `warn`, `error`) | `info`       |

## Project Structure

```
CS2-ACS-CM/
├── CS2-ACS-v3.exe         # Precompiled parser executable
├── asset/                 # Images and GUI assets
├── cs2_parser/            # Go parser source (demoinfocs-golang integration)
├── file_loader.py         # CLI and Python loader for JSON parsing
├── main.py                # Python GUI entry point
├── parserv3.md            # Parser design notes and schema references
├── utils/                 # Utility scripts and modules
│   ├── gui/               # GUI modules (scout_report, summaries, etc.)
│   └── ...                # Other utilities (downloaders, sanitizers)
└── pewpew/                # Default output directory for parser JSON
```

## Module Descriptions

- **cs2\_parser/**: Contains Go modules for event handling and schema adaptation.
- **file\_loader.py**: Loads parser JSON, handles nested structures, and dispatches to GUI.
- **main.py**: Initializes GUI, sets up tabs (Event Log, Stats, Scout Report, Anti-Cheat).
- **utils/gui/**: Python modules:
  - `scout_report.py` – generates per-player threat assessments
  - `stats_summary.py` & `damage_summary.py` – aggregate player and round stats
  - `chat_summary.py` – extracts chat events

## Known Issues

1. ``** undefined** in `file_loader.py` (*NameError on nested JSON loading*).
2. **Missing **`` – Python dependencies are not captured.
3. **No CI or tests** – automated tests and continuous integration are not configured.
4. ``** directory** is accidentally tracked in Git; should be ignored or removed.
5. **GUI asset loading** can fail if paths contain spaces or special characters.

## Roadmap & To-Do

-

## Contributing

1. Fork the repository.
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Make your changes, ensuring all new code paths are tested.
4. Commit and push: `git commit -m "feat: add ..." && git push origin feature/my-feature`
5. Open a Pull Request and reference any related issues.

## License

*The project is currently unlicensed.*

> **Recommendation:** Add a `LICENSE` file (e.g., MIT or Apache 2.0) to clarify usage rights.

