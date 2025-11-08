from tkinter import ttk
import tkinter as tk

# Dark mode color scheme
DARK_BG = '#2b2b2b'
DARK_FG = '#e0e0e0'
DARK_FIELD_BG = '#3c3f41'
DARK_FIELD_FG = '#ffffff'
DARK_SELECT_BG = '#4a4a4a'
DARK_BORDER = '#555555'
DARK_BUTTON_BG = '#4a5f7f'
DARK_BUTTON_FG = '#ffffff'
DARK_HEADING_BG = '#3a3a3a'
DARK_TREE_SELECT = '#365880'
DARK_FRAME_BG = '#323232'

def apply_styles():
    style = ttk.Style()
    
    # Use 'clam' theme as base for better dark mode support
    style.theme_use('clam')
    
    # General widget styles
    style.configure(".", background=DARK_BG, foreground=DARK_FG, 
                   fieldbackground=DARK_FIELD_BG, bordercolor=DARK_BORDER)
    
    # Frame
    style.configure("TFrame", background=DARK_BG)
    
    # LabelFrame
    style.configure("TLabelframe", background=DARK_BG, foreground=DARK_FG, 
                   bordercolor=DARK_BORDER)
    style.configure("TLabelframe.Label", background=DARK_BG, foreground=DARK_FG,
                   font=('Arial', 10, 'bold'))
    
    # Label
    style.configure("TLabel", background=DARK_BG, foreground=DARK_FG, 
                   font=('Arial', 10))
    
    # Button
    style.configure("TButton", background=DARK_BUTTON_BG, foreground=DARK_BUTTON_FG,
                   font=('Arial', 10), bordercolor=DARK_BORDER, 
                   lightcolor=DARK_BUTTON_BG, darkcolor=DARK_BUTTON_BG)
    style.map("TButton",
             background=[('active', '#5a7fa0'), ('pressed', '#365880')],
             foreground=[('active', DARK_BUTTON_FG), ('pressed', DARK_BUTTON_FG)])
    
    # Help button
    style.configure("Help.TButton", font=('Arial', 12, 'bold'))
    
    # Entry
    style.configure("TEntry", fieldbackground=DARK_FIELD_BG, foreground=DARK_FIELD_FG,
                   insertcolor=DARK_FIELD_FG, bordercolor=DARK_BORDER)
    style.map("TEntry",
             fieldbackground=[('readonly', DARK_SELECT_BG)],
             foreground=[('readonly', DARK_FG)])
    
    # Combobox
    style.configure("TCombobox", fieldbackground=DARK_FIELD_BG, 
                   foreground=DARK_FIELD_FG, background=DARK_FIELD_BG,
                   selectbackground=DARK_TREE_SELECT, selectforeground=DARK_FIELD_FG,
                   arrowcolor=DARK_FG, bordercolor=DARK_BORDER)
    style.map("TCombobox",
             fieldbackground=[('readonly', DARK_FIELD_BG)],
             selectbackground=[('readonly', DARK_FIELD_BG)],
             foreground=[('readonly', DARK_FIELD_FG)],
             background=[('readonly', DARK_FIELD_BG)])
    
    # Radiobutton
    style.configure("TRadiobutton", background=DARK_BG, foreground=DARK_FG,
                   font=('Arial', 10))
    style.map("TRadiobutton",
             background=[('active', DARK_BG)],
             foreground=[('active', DARK_FG)])
    
    # Checkbutton
    style.configure("TCheckbutton", background=DARK_BG, foreground=DARK_FG,
                   font=('Arial', 10))
    style.map("TCheckbutton",
             background=[('active', DARK_BG)],
             foreground=[('active', DARK_FG)])
    
    # Notebook
    style.configure("TNotebook", background=DARK_BG, bordercolor=DARK_BORDER)
    style.configure("TNotebook.Tab", background=DARK_SELECT_BG, foreground=DARK_FG,
                   padding=[10, 2], bordercolor=DARK_BORDER)
    style.map("TNotebook.Tab",
             background=[('selected', DARK_BUTTON_BG)],
             foreground=[('selected', DARK_BUTTON_FG)],
             expand=[('selected', [1, 1, 1, 0])])
    
    # Treeview
    style.configure("Treeview", background=DARK_FIELD_BG, foreground=DARK_FIELD_FG,
                   fieldbackground=DARK_FIELD_BG, bordercolor=DARK_BORDER)
    style.configure("Treeview.Heading", background=DARK_HEADING_BG, 
                   foreground=DARK_FG, font=('Arial', 10, 'bold'),
                   bordercolor=DARK_BORDER)
    style.map("Treeview.Heading",
             background=[('active', DARK_SELECT_BG)])
    style.map("Treeview",
             background=[('selected', DARK_TREE_SELECT)],
             foreground=[('selected', DARK_FIELD_FG)])
    
    # Scrollbar
    style.configure("Vertical.TScrollbar", background=DARK_SELECT_BG,
                   troughcolor=DARK_BG, bordercolor=DARK_BORDER,
                   arrowcolor=DARK_FG)
    style.map("Vertical.TScrollbar",
             background=[('active', DARK_BUTTON_BG)])
    
    style.configure("Horizontal.TScrollbar", background=DARK_SELECT_BG,
                   troughcolor=DARK_BG, bordercolor=DARK_BORDER,
                   arrowcolor=DARK_FG)
    style.map("Horizontal.TScrollbar",
             background=[('active', DARK_BUTTON_BG)])
    
    # Progressbar
    style.configure("TProgressbar", background=DARK_BUTTON_BG, 
                   troughcolor=DARK_FIELD_BG, bordercolor=DARK_BORDER,
                   lightcolor=DARK_BUTTON_BG, darkcolor=DARK_BUTTON_BG)
    
    # Scale/Slider
    style.configure("TScale", background=DARK_BG, troughcolor=DARK_FIELD_BG,
                   bordercolor=DARK_BORDER)
    
    # Separator
    style.configure("TSeparator", background=DARK_BORDER)
    
    # Style for completed goals frame
    style.configure("Complete.TFrame", background='#2d4a2d')

def configure_text_widget(text_widget):
    """Configure a Text widget for dark mode"""
    text_widget.configure(
        background=DARK_FIELD_BG,
        foreground=DARK_FIELD_FG,
        insertbackground=DARK_FIELD_FG,  # Cursor color
        selectbackground=DARK_TREE_SELECT,
        selectforeground=DARK_FIELD_FG,
        borderwidth=1,
        relief='solid'
    )

def configure_canvas(canvas):
    """Configure a Canvas widget for dark mode"""
    canvas.configure(
        background=DARK_BG,
        highlightthickness=0
    )

def configure_toplevel(toplevel):
    """Configure a Toplevel window for dark mode"""
    toplevel.configure(background=DARK_BG)

def get_colors():
    """Return color scheme dictionary for other uses"""
    return {
        'bg': DARK_BG,
        'fg': DARK_FG,
        'field_bg': DARK_FIELD_BG,
        'field_fg': DARK_FIELD_FG,
        'select_bg': DARK_SELECT_BG,
        'border': DARK_BORDER,
        'button_bg': DARK_BUTTON_BG,
        'button_fg': DARK_BUTTON_FG,
        'heading_bg': DARK_HEADING_BG,
        'tree_select': DARK_TREE_SELECT,
        'frame_bg': DARK_FRAME_BG
    }