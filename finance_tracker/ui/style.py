import tkinter as tk
from tkinter import ttk
from .theme_manager import theme_manager
from .theme import get_theme_colors

def _configure_theme(style, colors):
    """Configure the ttk style with the given color scheme"""
    # Configure colors
    style.configure('.',
                  background=colors.bg_primary,
                  foreground=colors.text_primary,
                  fieldbackground=colors.bg_primary,
                  troughcolor=colors.bg_secondary,
                  selectbackground=colors.accent,
                  selectforeground=colors.text_primary,
                  insertcolor=colors.text_primary,
                  highlightthickness=0,
                  borderwidth=1)

    # Configure main styles
    style.configure('TFrame', background=colors.bg_primary)
    style.configure('TLabel', background=colors.bg_primary, foreground=colors.text_primary)
    style.configure('TButton',
                   background=colors.bg_secondary,
                   foreground=colors.text_primary,
                   borderwidth=1,
                   relief='flat')
    style.map('TButton',
             background=[('active', colors.bg_tertiary)],
             foreground=[('active', colors.text_primary)])
    
    # Treeview styles
    style.configure('Treeview',
                   background=colors.bg_primary,
                   foreground=colors.text_primary,
                   fieldbackground=colors.bg_primary,
                   borderwidth=0)
    style.map('Treeview', background=[('selected', colors.accent)])
    
    style.configure('Treeview.Heading',
                   font=('Arial', 10, 'bold'),
                   background=colors.bg_secondary,
                   foreground=colors.text_primary,
                   relief='flat')
    style.map('Treeview.Heading',
             background=[('active', colors.bg_tertiary)])
    
    # Entry and Combobox
    style.configure('TEntry',
                   fieldbackground=colors.bg_secondary,
                   foreground=colors.text_primary,
                   insertcolor=colors.text_primary)
    style.map('TEntry',
             fieldbackground=[('readonly', colors.bg_primary)])
    
    style.configure('TCombobox',
                   fieldbackground=colors.bg_secondary,
                   background=colors.bg_primary,
                   foreground=colors.text_primary,
                   arrowcolor=colors.text_primary)
    style.map('TCombobox',
             fieldbackground=[('readonly', colors.bg_primary)])
    
    # Notebook style
    style.configure('TNotebook', background=colors.bg_primary)
    style.configure('TNotebook.Tab',
                   background=colors.bg_secondary,
                   foreground=colors.text_primary,
                   padding=[10, 5],
                   font=('Arial', 10))
    style.map('TNotebook.Tab',
             background=[('selected', colors.bg_primary)],
             foreground=[('selected', colors.text_primary)])
    
    # Scrollbar
    style.configure('Vertical.TScrollbar',
                   background=colors.bg_secondary,
                   troughcolor=colors.bg_primary,
                   bordercolor=colors.bg_primary,
                   arrowcolor=colors.text_primary)
    style.configure('Horizontal.TScrollbar',
                   background=colors.bg_secondary,
                   troughcolor=colors.bg_primary,
                   bordercolor=colors.bg_primary,
                   arrowcolor=colors.text_primary)
    
    # Special styles
    style.configure('Help.TButton',
                   font=('Arial', 12, 'bold'),
                   background=colors.accent,
                   foreground=colors.text_primary)
    style.map('Help.TButton',
             background=[('active', colors.accent_hover)])
    
    # Style for completed goals
    style.configure('Complete.TFrame', background=colors.success + '40')  # 40 = 25% opacity
    
    # Custom styles
    style.configure('Accent.TButton',
                   background=colors.accent,
                   foreground=colors.text_primary)
    style.map('Accent.TButton',
             background=[('active', colors.accent_hover)])
    
    style.configure('Error.TLabel', foreground=colors.error)
    style.configure('Success.TLabel', foreground=colors.success)
    style.configure('Warning.TLabel', foreground=colors.warning)

def apply_styles(root=None):
    """Apply styles to the application"""
    style = ttk.Style()
    
    # Set the theme to 'default' as a base
    style.theme_use('default')
    
    # Get current theme colors
    colors = theme_manager.get_colors()
    
    # Configure the theme
    _configure_theme(style, colors)
    
    # Configure root window background if provided
    if root:
        root.configure(background=colors.bg_primary)
    
    return style