# -*- coding: utf-8 -*-
"""
Centralized font utilities for BOMCategorizer.

Provides consistent font selection across different platforms and UI frameworks.
"""

import platform


def get_system_font() -> str:
    """
    Returns appropriate system font for current OS (for PySide6/Qt).
    
    Returns:
        str: Font name suitable for Qt applications
    """
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        return '.AppleSystemUIFont'
    elif system == 'Windows':
        return 'Segoe UI'
    else:  # Linux and others
        return 'DejaVu Sans'


def get_system_fonts() -> dict:
    """
    Returns appropriate fonts for current OS (for Tkinter).
    
    Returns:
        dict: Dictionary with font types:
            - default: Primary system font
            - default_fallback: Fallback font
            - monospace: Monospace font
            - monospace_fallback: Fallback monospace font
    """
    system = platform.system()
    
    if system == 'Darwin':  # macOS
        return {
            'default': 'SF Pro Text',
            'default_fallback': 'Helvetica Neue',
            'monospace': 'Menlo',
            'monospace_fallback': 'Monaco'
        }
    elif system == 'Windows':
        return {
            'default': 'Segoe UI',
            'default_fallback': 'Arial',
            'monospace': 'Consolas',
            'monospace_fallback': 'Courier New'
        }
    else:  # Linux and others
        return {
            'default': 'DejaVu Sans',
            'default_fallback': 'Sans',
            'monospace': 'DejaVu Sans Mono',
            'monospace_fallback': 'Monospace'
        }


def get_monospace_font() -> str:
    """
    Returns appropriate monospace font for current OS.
    
    Returns:
        str: Monospace font name
    """
    fonts = get_system_fonts()
    return fonts['monospace']
