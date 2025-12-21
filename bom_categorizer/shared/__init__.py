# -*- coding: utf-8 -*-
"""
Shared package for common utilities used across BOMCategorizer.

This package contains centralized implementations of commonly used
functions to avoid code duplication.
"""

from .config import get_config_path, load_config, save_config
from .fonts import get_system_font, get_system_fonts

__all__ = [
    'get_config_path',
    'load_config', 
    'save_config',
    'get_system_font',
    'get_system_fonts',
]
