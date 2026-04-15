"""
finance_tracker/ui/windowing.py

Helpers for stable Tk window show/close behavior across WSLg and desktop Tk.
"""

from __future__ import annotations

import tkinter as tk


def show_main_window(root: tk.Tk) -> None:
    """Show the root window using a conservative, WSLg-friendly sequence."""
    try:
        root.update_idletasks()
    except tk.TclError:
        return

    try:
        root.state("normal")
        root.deiconify()
    except tk.TclError:
        pass


def _managed_windows(root: tk.Misc) -> set[tk.Toplevel]:
    windows = getattr(root, "_managed_child_windows", None)
    if windows is None:
        windows = set()
        setattr(root, "_managed_child_windows", windows)
    return windows


def close_window(window: tk.Toplevel) -> None:
    """Close a managed child window and release its grab first when needed."""
    try:
        if not window.winfo_exists():
            return
    except tk.TclError:
        return

    if getattr(window, "_is_closing", False):
        return

    window._is_closing = True
    manager_root = getattr(window, "_manager_root", None)

    try:
        current_grab = window.grab_current()
    except tk.TclError:
        current_grab = None

    try:
        if current_grab and str(current_grab) == str(window):
            window.grab_release()
    except tk.TclError:
        pass

    try:
        window.destroy()
    except tk.TclError:
        pass
    finally:
        if manager_root is not None:
            _managed_windows(manager_root).discard(window)


def create_child_window(
    parent: tk.Misc,
    *,
    title: str,
    geometry: str | None = None,
    minsize: tuple[int, int] | None = None,
    modal: bool = False,
) -> tk.Toplevel:
    """Create a managed child window with consistent close and modal behavior."""
    owner = parent.winfo_toplevel()
    window = tk.Toplevel(owner)
    root = parent._root()
    owner = parent.winfo_toplevel()

    window._manager_root = root
    window.title(title)

    if geometry:
        window.geometry(geometry)
    if minsize:
        window.minsize(*minsize)

    _managed_windows(root).add(window)

    def handle_close(_event=None):
        close_window(window)

    def handle_destroy(event):
        if event.widget is window:
            _managed_windows(root).discard(window)

    window.protocol("WM_DELETE_WINDOW", handle_close)
    window.bind("<Escape>", handle_close, add="+")
    window.bind("<Destroy>", handle_destroy, add="+")

    if modal:
        window.transient(owner)

        def activate_modal():
            try:
                if not window.winfo_exists():
                    return
                window.update_idletasks()
                window.lift()
                window.grab_set()
                window.focus_set()
            except tk.TclError:
                pass

        window.after_idle(activate_modal)

    return window
