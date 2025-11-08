import json
import os
from pathlib import Path
from typing import Callable, List

from .theme import get_theme_colors, ThemeColors

class ThemeManager:
    _instance = None
    _callbacks: List[Callable[[bool], None]] = []
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ThemeManager, cls).__new__(cls)
            cls._instance._dark_mode = True  # Default to dark mode
            cls._instance._load_settings()
        return cls._instance
    
    def _get_config_path(self) -> Path:
        """Get the path to the theme config file"""
        config_dir = Path.home() / ".config" / "finance-tracker"
        config_dir.mkdir(parents=True, exist_ok=True)
        return config_dir / "theme_config.json"
    
    def _load_settings(self):
        """Load theme settings from config file"""
        config_path = self._get_config_path()
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    self._dark_mode = config.get('dark_mode', True)
            except (json.JSONDecodeError, KeyError):
                # If there's an error reading the config, use default values
                self._dark_mode = True
    
    def _save_settings(self):
        """Save current theme settings to config file"""
        config_path = self._get_config_path()
        with open(config_path, 'w') as f:
            json.dump({'dark_mode': self._dark_mode}, f)
    
    @property
    def dark_mode(self) -> bool:
        """Get current theme mode"""
        return self._dark_mode
    
    @dark_mode.setter
    def dark_mode(self, value: bool):
        """Set theme mode and notify all callbacks"""
        if self._dark_mode != value:
            self._dark_mode = value
            self._save_settings()
            self._notify_callbacks()
    
    def toggle_theme(self):
        """Toggle between dark and light mode"""
        self.dark_mode = not self._dark_mode
    
    def get_colors(self) -> ThemeColors:
        """Get current theme colors"""
        return get_theme_colors(self._dark_mode)
    
    def register_callback(self, callback: Callable[[bool], None]):
        """Register a callback to be called when theme changes"""
        if callback not in self._callbacks:
            self._callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable[[bool], None]):
        """Unregister a callback"""
        if callback in self._callbacks:
            self._callbacks.remove(callback)
    
    def _notify_callbacks(self):
        """Notify all registered callbacks of theme change"""
        for callback in self._callbacks[:]:  # Use a slice copy to handle callbacks that might unregister themselves
            try:
                callback(self._dark_mode)
            except Exception as e:
                print(f"Error in theme change callback: {e}")

# Global theme manager instance
theme_manager = ThemeManager()
