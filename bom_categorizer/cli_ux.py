# -*- coding: utf-8 -*-
"""
UX helpers for the in-app Interactive CLI.

Pure functions (no Qt): command-line parsing, fuzzy suggestions, palettes, usage hints.
"""

from __future__ import annotations

import shlex
from typing import Dict, Iterable, List, Optional, Sequence, Tuple


# Static argument completions: command_name -> list of suggestions
ARG_COMPLETIONS: Dict[str, List[str]] = {
    "theme": ["dark", "light"],
    "aiprovider": ["telegram", "anthropic", "openai"],
    "provider": ["telegram", "anthropic", "openai"],
    "aimodels": ["anthropic", "openai"],
    "models": ["anthropic", "openai"],
}


PALETTES: Dict[str, Dict[str, str]] = {
    "dark": {
        "bg": "#1e1e2e",
        "bg_input": "#313244",
        "border": "#45475a",
        "border_focus": "#89b4fa",
        "fg": "#cdd6f4",
        "prompt": "#89b4fa",
        "command": "#f9e2af",
        "success": "#a6e3a1",
        "error": "#f38ba8",
        "hint": "#6c7086",
        "popup_bg": "#1e1e2e",
        "popup_selected_bg": "#45475a",
        "popup_selected_fg": "#f5c2e7",
        "popup_hover": "#313244",
        "button_bg": "#89b4fa",
        "button_fg": "#1e1e2e",
        "button_hover": "#a6c9ff",
    },
    "light": {
        "bg": "#eff1f5",
        "bg_input": "#ffffff",
        "border": "#ccd0da",
        "border_focus": "#1e66f5",
        "fg": "#4c4f69",
        "prompt": "#1e66f5",
        "command": "#df8e1d",
        "success": "#40a02b",
        "error": "#d20f39",
        "hint": "#9ca0b0",
        "popup_bg": "#ffffff",
        "popup_selected_bg": "#ccd0da",
        "popup_selected_fg": "#8839ef",
        "popup_hover": "#e6e9ef",
        "button_bg": "#1e66f5",
        "button_fg": "#ffffff",
        "button_hover": "#4a82f7",
    },
}


def get_palette(theme: str) -> Dict[str, str]:
    """Return color palette for theme ('dark' or 'light')."""
    key = (theme or "dark").lower()
    return PALETTES.get(key, PALETTES["dark"]).copy()


def parse_command_line(line: str) -> Tuple[Optional[List[str]], Optional[str]]:
    """
    Parse a CLI line with quoted paths support.

    Returns:
        (parts, None) on success, or (None, error_message) on failure.
    """
    if line is None:
        return None, "Пустая команда"
    text = str(line).strip()
    if not text:
        return None, "Пустая команда"
    try:
        # posix=False: backslashes are literal (Windows paths)
        parts = shlex.split(text, posix=False)
    except ValueError as e:
        return None, f"Не удалось разобрать команду (проверьте кавычки): {e}"
    if not parts:
        return None, "Пустая команда"
    # shlex with posix=False may keep surrounding quotes on tokens — strip them
    cleaned = []
    for p in parts:
        if len(p) >= 2 and ((p[0] == p[-1] == '"') or (p[0] == p[-1] == "'")):
            cleaned.append(p[1:-1])
        else:
            cleaned.append(p)
    return cleaned, None


def _levenshtein(a: str, b: str) -> int:
    """Classic Levenshtein distance."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            ins = cur[j - 1] + 1
            delete = prev[j] + 1
            sub = prev[j - 1] + (0 if ca == cb else 1)
            cur.append(min(ins, delete, sub))
        prev = cur
    return prev[-1]


def suggest_commands(
    unknown: str,
    known: Iterable[str],
    *,
    limit: int = 3,
    max_distance: int = 2,
) -> List[str]:
    """
    Suggest closest command names for a typo.

    Prefers prefix matches, then Levenshtein distance <= max_distance.
    """
    query = (unknown or "").strip().lower()
    if not query:
        return []

    names = sorted({str(n).strip() for n in known if str(n).strip()})
    if not names:
        return []

    prefix = [n for n in names if n.lower().startswith(query) and n.lower() != query]
    if prefix:
        return prefix[:limit]

    scored: List[Tuple[int, str]] = []
    for name in names:
        dist = _levenshtein(query, name.lower())
        if dist <= max_distance:
            scored.append((dist, name))
    scored.sort(key=lambda x: (x[0], x[1]))
    return [name for _, name in scored[:limit]]


def format_usage_hint(usage: str, example: str = "") -> str:
    """Format a short usage/example block for error messages."""
    lines = []
    usage = (usage or "").strip()
    example = (example or "").strip()
    if usage:
        lines.append(f"Использование: {usage}")
    if example:
        lines.append(f"Пример: {example}")
    return "\n".join(lines)


def completion_candidates(
    text: str,
    command_names: Sequence[str],
    arg_completions: Optional[Dict[str, List[str]]] = None,
) -> List[str]:
    """
    Build completer candidates for current input text.

    - First token: filter command names
    - Later tokens: filter ARG_COMPLETIONS for that command
    """
    arg_completions = arg_completions if arg_completions is not None else ARG_COMPLETIONS
    raw = (text or "").strip()
    if not raw:
        return sorted(set(command_names))

    parts, err = parse_command_line(raw)
    if err or not parts:
        # Fallback: prefix filter on raw first word
        q = raw.split()[0].lower() if raw.split() else raw.lower()
        return sorted({c for c in command_names if c.lower().startswith(q)})

    ends_with_space = text.rstrip() != text and bool(text)
    # If user typed "theme " (trailing space) → suggest args
    if ends_with_space or len(parts) >= 2:
        cmd = parts[0].lower()
        args = arg_completions.get(cmd, [])
        if not args:
            return []
        prefix = parts[1].lower() if len(parts) >= 2 and not ends_with_space else ""
        if prefix:
            return [a for a in args if a.lower().startswith(prefix)]
        return list(args)

    q = parts[0].lower()
    return sorted({c for c in command_names if c.lower().startswith(q)})
