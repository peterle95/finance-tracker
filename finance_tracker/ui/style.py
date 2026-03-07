"""
finance_tracker/ui/style.py

Defines and applies custom Tkinter styles for the application.
"""

import tkinter as tk
from tkinter import ttk

THEMES = {
    "dark": {
        "bg": "#1e1f25",
        "surface": "#272a33",
        "surface_alt": "#313540",
        "fg": "#f2f4f8",
        "muted_fg": "#a9b0bf",
        "accent": "#4c8dff",
        "accent_hover": "#3f7ae0",
        "entry_bg": "#22252e",
        "entry_fg": "#f2f4f8",
        "tree_alt": "#252934",
        "selection_bg": "#4c8dff",
        "selection_fg": "#ffffff",
        "complete_bg": "#24422f",
        "text_bg": "#1d212a",
        "text_fg": "#eef1f6",
        "shortcut_bg": "#323847",
        "section_fg": "#8ec5ff",
    },
    "light": {
        "bg": "#f6f8fc",
        "surface": "#ffffff",
        "surface_alt": "#eef2fb",
        "fg": "#1f2430",
        "muted_fg": "#58627a",
        "accent": "#2f6feb",
        "accent_hover": "#255bc2",
        "entry_bg": "#ffffff",
        "entry_fg": "#1f2430",
        "tree_alt": "#f5f7fc",
        "selection_bg": "#2f6feb",
        "selection_fg": "#ffffff",
        "complete_bg": "#e8f5e9",
        "text_bg": "#ffffff",
        "text_fg": "#1f2430",
        "shortcut_bg": "#edf1fa",
        "section_fg": "#0b5bd3",
    },
}

_current_theme = "dark"


def get_current_theme():
    return _current_theme


def get_theme_colors(theme_name=None):
    name = theme_name or _current_theme
    return THEMES[name]


def _apply_tk_widget_colors(widget, colors):
    if not isinstance(widget, tk.Widget):
        return

    cfg = widget.configure()
    if "background" in cfg:
        widget.configure(background=colors["bg"])
    if "foreground" in cfg:
        widget.configure(foreground=colors["fg"])
    if isinstance(widget, tk.Text):
        widget.configure(
            background=colors["text_bg"],
            foreground=colors["text_fg"],
            insertbackground=colors["text_fg"],
            selectbackground=colors["selection_bg"],
            selectforeground=colors["selection_fg"],
        )

    for child in widget.winfo_children():
        _apply_tk_widget_colors(child, colors)


def apply_styles(root, theme_name="dark"):
    global _current_theme
    _current_theme = theme_name
    colors = THEMES[theme_name]

    style = ttk.Style()
    style.theme_use("clam")

    style.configure(".", background=colors["bg"], foreground=colors["fg"])
    style.configure("TFrame", background=colors["bg"])
    style.configure("TLabel", font=("Arial", 10), background=colors["bg"], foreground=colors["fg"])

    style.configure(
        "TButton",
        font=("Arial", 10),
        background=colors["surface_alt"],
        foreground=colors["fg"],
        borderwidth=1,
        focusthickness=3,
        focuscolor=colors["accent"],
    )
    style.map(
        "TButton",
        background=[("active", colors["accent_hover"])],
        foreground=[("active", colors["selection_fg"])],
    )
    style.configure("Help.TButton", font=("Arial", 12, "bold"))

    style.configure("TRadiobutton", font=("Arial", 10), background=colors["bg"], foreground=colors["fg"])
    style.configure("TCheckbutton", background=colors["bg"], foreground=colors["fg"])

    style.configure("TLabelframe", background=colors["bg"], foreground=colors["fg"])
    style.configure("TLabelframe.Label", background=colors["bg"], foreground=colors["fg"])

    style.configure("TEntry", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"])
    style.configure("TCombobox", fieldbackground=colors["entry_bg"], foreground=colors["entry_fg"])
    style.map("TCombobox", fieldbackground=[("readonly", colors["entry_bg"])], foreground=[("readonly", colors["entry_fg"])])

    style.configure("Treeview", background=colors["surface"], foreground=colors["fg"], fieldbackground=colors["surface"], rowheight=24)
    style.configure("Treeview.Heading", font=("Arial", 10, "bold"), background=colors["surface_alt"], foreground=colors["fg"])
    style.map("Treeview", background=[("selected", colors["selection_bg"])], foreground=[("selected", colors["selection_fg"])])

    style.configure("TNotebook", background=colors["bg"], borderwidth=0)
    style.configure("TNotebook.Tab", background=colors["surface_alt"], foreground=colors["fg"], padding=(10, 5))
    style.map(
        "TNotebook.Tab",
        background=[("selected", colors["accent"]), ("active", colors["accent_hover"])],
        foreground=[("selected", colors["selection_fg"]), ("active", colors["selection_fg"])],
    )

    # Style for completed goals
    style.configure("Complete.TFrame", background=colors["complete_bg"])

    root.configure(bg=colors["bg"])
    root.option_add("*Background", colors["bg"])
    root.option_add("*Foreground", colors["fg"])
    root.option_add("*Text.background", colors["text_bg"])
    root.option_add("*Text.foreground", colors["text_fg"])
    root.option_add("*Text.insertBackground", colors["text_fg"])
    root.option_add("*Text.selectBackground", colors["selection_bg"])
    root.option_add("*Text.selectForeground", colors["selection_fg"])

    _apply_tk_widget_colors(root, colors)
