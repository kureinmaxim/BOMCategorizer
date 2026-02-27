# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

BOM Categorizer is a desktop application that automatically sorts electronic components from BOMs (Bills of Materials) into categories (Resistors, Capacitors, ICs, etc.). It has two GUI editions sharing the same core engine:

- **Modern Edition** (v5.x) — PySide6/Qt, entry point: `app_qt.py`
- **Standard Edition** (v3.x) — Tkinter, entry point: `app.py`

Primary language: Python 3.13+. Primary platform: Windows. Documentation and UI strings are in Russian.

## Common Commands

```bash
# Run the app
python app_qt.py                        # Modern Edition (recommended)
python app.py                           # Standard Edition

# Tests
python run_tests.py                     # All tests (pytest)
python run_tests.py --quick             # Unit tests only
python run_tests.py --coverage          # With coverage report
python run_tests.py -k <keyword>        # Filter tests by keyword

# Version management
python tools/update_version.py status   # Check current versions
python tools/update_version.py sync     # Sync versions across all files
python scripts/bump_version.py --bump patch  # Bump version

# Build installers
python deployment/build_installer.py    # Windows (Inno Setup)
./deployment/build_macos.sh             # macOS (py2app)

# Setup after clone
python tools/init_project.py            # Create local configs from templates
pip install -r requirements.txt
```

## Architecture

### Processing Pipeline

```
Input Files (.xlsx/.xls/.docx/.txt)
  → parsers.py (parse into DataFrames)
  → formatters.py (normalize, clean, extract values)
  → classifiers.py (regex + heuristics, 14+ categories)
  → excel_writer.py / txt_writer.py / pdf_exporter.py (output)
```

### Classification Cascade

1. **Database lookup** — exact match from `component_database.json`
2. **Regex patterns** — technical characteristics in `classifiers.py`
3. **User-defined rules** — `rules.json`
4. **AI classification** — via TelegramHelper API or direct Anthropic/OpenAI

### Core Modules (`bom_categorizer/`)

| Module | Purpose |
|--------|---------|
| `main.py` | CLI orchestrator for the processing pipeline |
| `classifiers.py` | Regex + heuristics classification engine |
| `formatters.py` | Data cleaning, prefix removal, unit normalization |
| `parsers.py` | Input file readers (.txt, .docx, .xlsx) |
| `component_database.py` | JSON knowledge base with hash-based versioning |
| `excel_writer.py` | Styled Excel output with charts and source tracking |
| `pdf_exporter.py` | ReportLab PDF with Cyrillic support |
| `tru_merger.py` | BOM + supply reference file merging |
| `encryption.py` | AES-256-GCM encryption for API data |
| `utils.py` | Shared regex patterns and column normalization helpers |
| `shared/config.py` | Centralized config loading (dev/installed modes) |

### GUI Modern Edition (`bom_categorizer/gui/`)

Uses a **mixin architecture** — `main_window.py` composes behavior from:
- `file_handlers.py` — file open/save
- `database_handlers.py` — database CRUD
- `processing_handlers.py` — BOM/TRU processing
- `help_dialogs.py` — help and documentation

Long-running operations use **QThread workers** (`workers.py`: ProcessingWorker, ComparisonWorker, TruRkmWorker) to keep the UI responsive.

## Configuration System

- **Templates** (Git-tracked, source of truth): `config/config_qt.json.template`, `config/config.json.template`
- **Local configs** (Git-ignored, user-specific): `config_qt.json`, `config.json`
- Templates are copied to local configs on first run via `config_manager.py`
- `app_info` section is always synced from template; personal settings (theme, API keys, window size) are preserved
- After changing version in templates, always run `python tools/update_version.py sync`

## Key Conventions

- **Config changes go to templates first**, then sync to local configs and installer files
- **Version sources of truth** are only the template files; everything else is derived
- **DataFrame columns** are normalized to lowercase for lookups; original case preserved for output
- **Component text blob** for classification combines: description + value + partname + note + group_type
- **Database changes** are tracked with SHA256 hash history (blockchain-like versioning)
- **Naming**: snake_case functions/files, PascalCase classes, UPPER_SNAKE_CASE constants
- **Docstrings** in English; inline business-logic comments in Russian
- **Never commit**: `config.json`, `config_qt.json`, `component_database.json`, API keys, or `_build_meta.json`

## Test Structure

Tests live in `tests/` using pytest. Key test files:
- `test_classifiers.py` — classification regex and heuristics
- `test_formatters.py` — data cleaning logic
- `test_database.py` — database CRUD and versioning
- `test_integration.py` — end-to-end pipeline

## Dependencies

Core: pandas, openpyxl, xlrd, python-docx, PySide6 (>=6.6.0), requests, reportlab, cryptography (>=42.0.0). Full list in `requirements.txt`.
