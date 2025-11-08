from typing import Literal
from dataclasses import dataclass

@dataclass
class ThemeColors:
    """Theme colors for light and dark modes"""
    # Background colors
    bg_primary: str
    bg_secondary: str
    bg_tertiary: str
    
    # Text colors
    text_primary: str
    text_secondary: str
    
    # Accent colors
    accent: str
    accent_hover: str
    
    # State colors
    success: str
    warning: str
    error: str
    
    # Special colors
    border: str
    highlight: str

# Light theme colors
LIGHT_THEME = ThemeColors(
    bg_primary='#ffffff',
    bg_secondary='#f5f5f5',
    bg_tertiary='#e0e0e0',
    text_primary='#000000',
    text_secondary='#616161',
    accent='#2196f3',
    accent_hover='#1976d2',
    success='#4caf50',
    warning='#ff9800',
    error='#f44336',
    border='#bdbdbd',
    highlight='#e3f2fd',
)

# Dark theme colors
DARK_THEME = ThemeColors(
    bg_primary='#1e1e1e',
    bg_secondary='#2d2d2d',
    bg_tertiary='#3c3c3c',
    text_primary='#e0e0e0',
    text_secondary='#a0a0a0',
    accent='#64b5f6',
    accent_hover='#42a5f5',
    success='#66bb6a',
    warning='#ffa726',
    error='#ef5350',
    border='#555555',
    highlight='#2c3e50',
)

def get_theme_colors(dark_mode: bool = True) -> ThemeColors:
    """Get the appropriate theme colors based on the current mode"""
    return DARK_THEME if dark_mode else LIGHT_THEME
