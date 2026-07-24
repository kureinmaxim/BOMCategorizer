# -*- coding: utf-8 -*-
"""Unit tests for bom_categorizer.cli_ux (no Qt)."""
import pytest
from bom_categorizer.cli_ux import (
    ARG_COMPLETIONS,
    completion_candidates,
    format_usage_hint,
    get_palette,
    parse_command_line,
    suggest_commands,
)


class TestParseCommandLine:
    def test_simple(self):
        parts, err = parse_command_line("help theme")
        assert err is None
        assert parts == ["help", "theme"]

    def test_quoted_path_with_spaces(self):
        parts, err = parse_command_line('add "C:\\My Files\\bom.xlsx"')
        assert err is None
        assert parts[0] == "add"
        assert parts[1] == r"C:\My Files\bom.xlsx"

    def test_unbalanced_quotes(self):
        parts, err = parse_command_line('add "C:\\broken')
        assert parts is None
        assert err is not None
        assert "кавыч" in err.lower() or "разобрать" in err.lower()

    def test_empty(self):
        parts, err = parse_command_line("   ")
        assert parts is None
        assert err is not None


class TestSuggestCommands:
    def test_typo_close(self):
        known = ["help", "list", "status", "theme", "process"]
        suggestions = suggest_commands("tehme", known)
        assert "theme" in suggestions

    def test_prefix(self):
        known = ["dbsearch", "dbstats", "dbexport", "dbbackup"]
        suggestions = suggest_commands("db", known)
        assert suggestions[0].startswith("db")
        assert len(suggestions) <= 3

    def test_no_match(self):
        assert suggest_commands("zzzzz", ["help", "list"]) == []


class TestPalette:
    def test_dark_and_light(self):
        dark = get_palette("dark")
        light = get_palette("light")
        assert dark["bg"] != light["bg"]
        assert "success" in dark and "error" in light

    def test_unknown_falls_back_to_dark(self):
        assert get_palette("neon") == get_palette("dark")


class TestUsageAndCompletions:
    def test_usage_hint(self):
        text = format_usage_hint("theme [dark|light]", "theme dark")
        assert "Использование: theme [dark|light]" in text
        assert "Пример: theme dark" in text

    def test_completion_commands(self):
        names = ["theme", "help", "list"]
        assert "theme" in completion_candidates("th", names)

    def test_completion_args(self):
        names = list(ARG_COMPLETIONS.keys())
        cands = completion_candidates("theme ", names)
        assert "dark" in cands and "light" in cands
