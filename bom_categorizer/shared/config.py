# -*- coding: utf-8 -*-
"""
Centralized configuration management for BOMCategorizer.

Provides consistent config loading/saving across all editions:
- Modern Edition (PySide6): config_qt.json
- Standard Edition (Tkinter): config.json
"""

import json
import os
import platform
import sys
from typing import Optional


def get_config_path(edition: str = "modern") -> str:
    """
    Determines the path to config file for given edition.
    
    Args:
        edition: "modern" for config_qt.json, "standard" for config.json
        
    Returns:
        str: Absolute path to config file
        
    Search order:
        1. For frozen .app bundle (macOS) - Application Support
        2. Project root (development mode)
        3. Platform-specific app data directories (installed mode)
    """
    config_name = "config_qt.json" if edition == "modern" else "config.json"
    app_folder = "BOMCategorizerModern" if edition == "modern" else "BOMCategorizer"
    
    # For .app bundle (frozen) - always use Application Support
    if getattr(sys, 'frozen', False) and platform.system() == 'Darwin':
        app_support = os.path.expanduser('~/Library/Application Support')
        installed_path = os.path.join(app_support, app_folder, config_name)
        installed_dir = os.path.dirname(installed_path)
        
        # Create directory if it doesn't exist
        if not os.path.exists(installed_dir):
            os.makedirs(installed_dir, exist_ok=True)
        
        # If config doesn't exist, copy from bundle (template)
        if not os.path.exists(installed_path):
            _copy_template_to_installed(installed_path, config_name)
        
        return installed_path
    
    # 1. Project root (development mode)
    # Works from any module depth - find project root by looking for markers
    project_root = _find_project_root()
    dev_path = os.path.join(project_root, config_name)
    if os.path.exists(dev_path):
        return dev_path
    
    # 2. Platform-specific app data directories (installed mode)
    if platform.system() == 'Windows':
        appdata = os.environ.get('APPDATA', os.path.expanduser('~'))
        installed_path = os.path.join(appdata, app_folder, config_name)
    elif platform.system() == 'Darwin':  # macOS
        app_support = os.path.expanduser('~/Library/Application Support')
        installed_path = os.path.join(app_support, app_folder, config_name)
    else:  # Linux
        config_home = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
        installed_path = os.path.join(config_home, app_folder, config_name)
    
    installed_dir = os.path.dirname(installed_path)
    
    # Check if installed directory exists or there's an install marker
    if os.path.exists(installed_dir) or os.path.exists(installed_path):
        return installed_path
    
    # Check for installed marker
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    installed_marker = os.path.join(base_dir, ".installed")
    if os.path.exists(installed_marker):
        os.makedirs(installed_dir, exist_ok=True)
        return installed_path
    
    # Default - development path
    return dev_path


def _find_project_root() -> str:
    """
    Finds the project root directory by looking for marker files.
    
    Returns:
        str: Absolute path to project root
    """
    # Start from this file and go up
    current = os.path.dirname(os.path.abspath(__file__))
    
    # Markers that indicate project root
    markers = ['config', 'bom_categorizer', 'app_qt.py', 'app.py', 'requirements.txt']
    
    for _ in range(5):  # Max 5 levels up
        current = os.path.dirname(current)
        # Check if this looks like project root
        matches = sum(1 for m in markers if os.path.exists(os.path.join(current, m)))
        if matches >= 2:
            return current
    
    # Fallback - go 3 levels up from this file (shared/config.py -> shared -> bom_categorizer -> root)
    return os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _copy_template_to_installed(installed_path: str, config_name: str):
    """
    Copies template to installed location for .app bundles.
    """
    import shutil
    
    bundle_dir = os.path.dirname(os.path.dirname(sys.executable))
    template_name = config_name + ".template" if not config_name.endswith('.template') else config_name
    
    possible_paths = [
        os.path.join(bundle_dir, "Resources", template_name),
        os.path.join(bundle_dir, "Resources", "config", template_name),
        os.path.join(bundle_dir, "Resources", config_name),  # Without .template
    ]
    
    for template_path in possible_paths:
        if os.path.exists(template_path):
            shutil.copy2(template_path, installed_path)
            return
    
    # If template not found, create minimal config
    fallback = _get_fallback_config(config_name)
    with open(installed_path, 'w', encoding='utf-8') as f:
        json.dump(fallback, f, indent=2, ensure_ascii=False)


def _get_fallback_config(config_name: str) -> dict:
    """
    Returns fallback config when file cannot be loaded.
    """
    if "qt" in config_name:
        return {
            "app_info": {
                "version": "dev",
                "edition": "Modern Edition",
                "description": "BOM Categorizer Modern Edition"
            }
        }
    else:
        return {
            "app_info": {
                "version": "dev",
                "edition": "Standard",
                "description": "BOM Categorizer"
            }
        }


def _read_json_file(path: str) -> Optional[dict]:
    try:
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _get_bundle_resources_dir() -> Optional[str]:
    """
    Returns macOS .app bundle Resources directory when frozen.
    """
    try:
        if getattr(sys, "frozen", False) and platform.system() == "Darwin":
            # sys.executable -> .../Contents/MacOS/<binary>
            return os.path.join(os.path.dirname(os.path.dirname(sys.executable)), "Resources")
    except Exception:
        pass
    return None


def _get_template_paths(edition: str) -> list[str]:
    """
    Returns possible locations of template config for given edition.
    """
    template_name = "config_qt.json.template" if edition == "modern" else "config.json.template"

    paths: list[str] = []

    # Dev mode (repo)
    project_root = _find_project_root()
    paths.append(os.path.join(project_root, "config", template_name))

    # Frozen bundle (macOS)
    resources_dir = _get_bundle_resources_dir()
    if resources_dir:
        paths.append(os.path.join(resources_dir, template_name))
        paths.append(os.path.join(resources_dir, "config", template_name))

    return paths


def _load_template_config(edition: str) -> Optional[dict]:
    for p in _get_template_paths(edition):
        cfg = _read_json_file(p)
        if cfg:
            return cfg
    return None


def _sync_app_info_from_template(config: dict, template: dict, edition: str) -> bool:
    """
    Overwrites ONLY app metadata fields from template into config,
    preserving user settings (ui/window/api_keys/etc).

    Returns True if config was changed.
    """
    if not template:
        return False

    changed = False
    cfg_app = config.get("app_info") if isinstance(config.get("app_info"), dict) else {}
    tpl_app = template.get("app_info") if isinstance(template.get("app_info"), dict) else {}

    # Authoritative keys
    keys = [
        "version",
        "edition",
        "description",
        "description_en",
        "developer",
        "developer_en",
        "release_date",
        "last_updated",
    ]

    new_app = dict(cfg_app)
    for k in keys:
        if k in tpl_app and new_app.get(k) != tpl_app.get(k):
            new_app[k] = tpl_app.get(k)
            changed = True

    if changed:
        config["app_info"] = new_app

    # Also sync APP_ID for Modern Edition for compatibility (doesn't touch keys themselves)
    if edition == "modern":
        tpl_app_id = (
            (template.get("telegram_security") or {}).get("app_id")
            or (template.get("api_keys") or {}).get("app_id")
        )
        if tpl_app_id:
            for section_name in ("telegram_security", "api_keys"):
                section = config.get(section_name)
                if not isinstance(section, dict):
                    section = {}
                    config[section_name] = section
                    changed = True
                if section.get("app_id") != tpl_app_id:
                    section["app_id"] = tpl_app_id
                    changed = True

    return changed


def load_config(edition: str = "modern") -> dict:
    """
    Loads configuration from config file.
    
    Args:
        edition: "modern" for config_qt.json, "standard" for config.json
        
    Returns:
        dict: Configuration dictionary
    """
    config_name = "config_qt.json" if edition == "modern" else "config.json"
    cfg_path = get_config_path(edition)
    
    if os.path.exists(cfg_path):
        try:
            with open(cfg_path, "r", encoding="utf-8") as f:
                cfg = json.load(f)

            # Make app version/date unambiguous across machines:
            # Always take app_info from template shipped with the app/repo,
            # but keep user settings intact.
            template_cfg = _load_template_config(edition)
            if template_cfg and isinstance(cfg, dict):
                if _sync_app_info_from_template(cfg, template_cfg, edition):
                    save_config(cfg, edition)

            return cfg
        except Exception:
            pass
    
    return _get_fallback_config(config_name)


def save_config(config: dict, edition: str = "modern") -> bool:
    """
    Saves configuration to config file.
    
    Args:
        config: Configuration dictionary to save
        edition: "modern" for config_qt.json, "standard" for config.json
        
    Returns:
        bool: True if successful, False otherwise
    """
    cfg_path = get_config_path(edition)
    
    try:
        # Ensure directory exists
        cfg_dir = os.path.dirname(cfg_path)
        if cfg_dir and not os.path.exists(cfg_dir):
            os.makedirs(cfg_dir, exist_ok=True)
        
        with open(cfg_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


# Convenience functions for backwards compatibility

def load_config_modern() -> dict:
    """Loads Modern Edition config (config_qt.json)."""
    return load_config("modern")


def load_config_standard() -> dict:
    """Loads Standard Edition config (config.json)."""
    return load_config("standard")
