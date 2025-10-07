"""
GUI Utilities Module
Shared functions and constants for consistent UI design (DRY principle)
Modern Dark Theme with professional appearance
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional


# Dark Theme Color Scheme
COLORS = {
    # Background colors
    "bg_dark": "#1a1a2e",  # Main dark background
    "bg_medium": "#16213e",  # Secondary background
    "bg_light": "#0f3460",  # Lighter panels
    "bg_card": "#1e2a3a",  # Card/panel background
    # Accent colors
    "accent_green": "#00ff88",  # Success/positive actions
    "accent_blue": "#00d4ff",  # Primary actions
    "accent_purple": "#a855f7",  # Secondary actions
    "accent_orange": "#ff6b35",  # Warning actions
    "accent_red": "#ff4757",  # Danger/delete actions
    "accent_yellow": "#ffd93d",  # Highlights
    # Text colors
    "text_primary": "#e8e8e8",  # Main text
    "text_secondary": "#a0a0a0",  # Secondary text
    "text_muted": "#6c757d",  # Muted text
    "text_bright": "#ffffff",  # Bright text
    # UI element colors
    "border": "#2d3748",  # Borders
    "hover": "#2a3f5f",  # Hover state
    "focus": "#00d4ff",  # Focus/active state
    "success": "#10b981",  # Success messages
    "error": "#ef4444",  # Error messages
    "warning": "#f59e0b",  # Warning messages
    # Legacy compatibility (for gradual migration)
    "primary": "#0f3460",
    "white": "#e8e8e8",
    "background": "#1a1a2e",
}

# Font configurations
FONTS = {
    "title_large": ("Segoe UI", 36, "bold"),
    "title_medium": ("Segoe UI", 24, "bold"),
    "title_small": ("Segoe UI", 20, "bold"),
    "heading": ("Segoe UI", 16, "bold"),
    "subheading": ("Segoe UI", 14, "bold"),
    "body": ("Segoe UI", 12),
    "body_bold": ("Segoe UI", 13, "bold"),
    "label": ("Segoe UI", 11),
    "small": ("Segoe UI", 10),
    "small_bold": ("Segoe UI", 10, "bold"),
    "tiny": ("Segoe UI", 9),
    "monospace": ("Consolas", 11),
}


def setup_dark_theme():
    """Configure dark theme for the entire application."""
    style = ttk.Style()

    # Try to use a theme that works well with dark backgrounds
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    # Configure TButton with dark theme
    style.configure(
        "TButton",
        background=COLORS["bg_light"],
        foreground=COLORS["text_primary"],
        borderwidth=0,
        focuscolor=COLORS["focus"],
        padding=(15, 10),
    )

    style.map(
        "TButton",
        background=[("active", COLORS["hover"]), ("pressed", COLORS["bg_medium"])],
        foreground=[("active", COLORS["text_bright"])],
    )

    # Green button (Success/Positive actions - Deposit, New Account)
    style.configure(
        "Green.TButton",
        background=COLORS["accent_green"],
        foreground=COLORS["bg_dark"],
        borderwidth=0,
        focuscolor="none",
        padding=(15, 10),
    )
    style.map(
        "Green.TButton",
        background=[("active", "#00ff9f"), ("pressed", "#00e67a")],
        foreground=[("active", COLORS["bg_dark"]), ("pressed", COLORS["bg_dark"])],
    )

    # Orange button (Warning - Withdraw, Transfer)
    style.configure(
        "Orange.TButton",
        background=COLORS["accent_orange"],
        foreground=COLORS["text_bright"],
        borderwidth=0,
        focuscolor="none",
        padding=(15, 10),
    )
    style.map(
        "Orange.TButton",
        background=[("active", "#ff7f50"), ("pressed", "#ff5722")],
        foreground=[
            ("active", COLORS["text_bright"]),
            ("pressed", COLORS["text_bright"]),
        ],
    )

    # Blue button (Primary actions)
    style.configure(
        "Blue.TButton",
        background=COLORS["accent_blue"],
        foreground=COLORS["bg_dark"],
        borderwidth=0,
        focuscolor="none",
        padding=(15, 10),
    )
    style.map(
        "Blue.TButton",
        background=[("active", "#1ae5ff"), ("pressed", "#00bfea")],
        foreground=[("active", COLORS["bg_dark"]), ("pressed", COLORS["bg_dark"])],
    )

    # Red button (Danger - Delete)
    style.configure(
        "Red.TButton",
        background=COLORS["accent_red"],
        foreground=COLORS["text_bright"],
        borderwidth=0,
        focuscolor="none",
        padding=(15, 10),
    )
    style.map(
        "Red.TButton",
        background=[("active", "#ff5c6d"), ("pressed", "#ff3345")],
        foreground=[
            ("active", COLORS["text_bright"]),
            ("pressed", COLORS["text_bright"]),
        ],
    )

    # Configure Combobox for dark theme
    style.configure(
        "TCombobox",
        fieldbackground=COLORS["bg_card"],
        background=COLORS["bg_light"],
        foreground=COLORS["text_primary"],
        borderwidth=1,
        relief="flat",
    )
    style.map(
        "TCombobox",
        fieldbackground=[("readonly", COLORS["bg_card"])],
        selectbackground=[("readonly", COLORS["bg_light"])],
        selectforeground=[("readonly", COLORS["text_primary"])],
    )


def create_header_frame(
    parent: tk.Widget, title: str, subtitle: str = None, height: int = 120
) -> tk.Frame:
    """Create a standardized dark theme header frame with title and optional subtitle."""
    header_frame = tk.Frame(parent, bg=COLORS["bg_medium"], height=height)
    header_frame.pack(fill=tk.X)
    header_frame.pack_propagate(False)

    title_label = tk.Label(
        header_frame,
        text=title,
        font=FONTS["title_large"],
        bg=COLORS["bg_medium"],
        fg=COLORS["text_bright"],
    )
    title_label.pack(pady=(20, 5) if subtitle else (20, 20))

    if subtitle:
        subtitle_label = tk.Label(
            header_frame,
            text=subtitle,
            font=FONTS["subheading"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_secondary"],
        )
        subtitle_label.pack(pady=(0, 15))

    return header_frame


def create_label(
    parent: tk.Widget,
    text: str,
    font_key: str = "label",
    color_key: str = "text_primary",
    bg: str = None,
    **pack_kwargs,
) -> tk.Label:
    """Create a standardized dark theme label."""
    bg_color = bg or COLORS["bg_dark"]
    fg_color = COLORS.get(color_key, COLORS["text_primary"])

    label = tk.Label(parent, text=text, font=FONTS[font_key], bg=bg_color, fg=fg_color)
    if pack_kwargs:
        label.pack(**pack_kwargs)
    return label


def create_entry(parent: tk.Widget, show: str = None, **pack_kwargs) -> tk.Entry:
    """Create a standardized dark theme entry field."""
    entry = tk.Entry(
        parent,
        bg=COLORS["bg_card"],
        fg=COLORS["text_primary"],
        font=FONTS["body"],
        insertbackground=COLORS["accent_blue"],  # Cursor color
        bd=1,
        relief=tk.SOLID,
        highlightthickness=1,
        highlightbackground=COLORS["border"],
        highlightcolor=COLORS["focus"],
    )
    if show:
        entry.config(show=show)
    if pack_kwargs:
        entry.pack(**pack_kwargs)
    return entry


def create_button(
    parent: tk.Widget,
    text: str,
    command: Callable,
    color_key: str = "accent",
    text_color: str = None,
    font_key: str = "body_bold",
    width: int = None,
    **pack_kwargs,
) -> ttk.Button:
    """Create a standardized dark theme ttk button."""
    # Map color_key to ttk style names (support both old and new naming)
    style_map = {
        "accent": "Green.TButton",
        "green": "Green.TButton",
        "primary": "Blue.TButton",
        "blue": "Blue.TButton",
        "secondary": "Blue.TButton",
        "warning": "Orange.TButton",
        "orange": "Orange.TButton",
        "error": "Red.TButton",
        "red": "Red.TButton",
    }

    style_name = style_map.get(color_key, "Green.TButton")

    button_config = {
        "text": text,
        "command": command,
        "style": style_name,
        "cursor": "hand2",
    }

    if width:
        button_config["width"] = width

    button = ttk.Button(parent, **button_config)

    if pack_kwargs:
        button.pack(**pack_kwargs)
    return button


def create_labeled_entry(
    parent: tk.Widget, label_text: str, show: str = None, pady_top: int = 15
) -> tk.Entry:
    """Create a label and entry field pair."""
    label = create_label(
        parent,
        label_text,
        font_key="label",
        color_key="primary",
        anchor=tk.W,
        pady=(pady_top, 5),
    )

    entry = create_entry(parent, show=show, fill=tk.X, ipady=8)
    return entry


def create_combobox(
    parent: tk.Widget,
    values: list,
    default: str = None,
    width: int = None,
    **pack_kwargs,
) -> tuple[tk.StringVar, ttk.Combobox]:
    """Create a standardized combobox with associated StringVar."""
    var = tk.StringVar()
    if default and default in values:
        var.set(default)
    elif values:
        var.set(values[0])

    combo = ttk.Combobox(
        parent, textvariable=var, values=values, state="readonly", font=FONTS["label"]
    )
    if width:
        combo.config(width=width)
    if pack_kwargs:
        combo.pack(**pack_kwargs)

    return var, combo


def create_modal_dialog(
    parent: tk.Widget, title: str, width: int = 400, height: int = 300
) -> tk.Toplevel:
    """Create a standardized dark theme modal dialog window."""
    window = tk.Toplevel(parent)
    window.title(title)
    window.geometry(f"{width}x{height}")
    window.resizable(False, False)
    window.configure(bg=COLORS["bg_dark"])
    window.transient(parent)
    window.grab_set()
    return window


def create_divider(parent: tk.Widget, text: str = "OR", pady: int = 20) -> tk.Frame:
    """Create a horizontal divider with optional text."""
    divider_frame = tk.Frame(parent, bg=COLORS["white"])
    divider_frame.pack(fill=tk.X, pady=pady)

    tk.Frame(divider_frame, bg=COLORS["border"], height=1).pack(
        side=tk.LEFT, fill=tk.X, expand=True
    )
    tk.Label(
        divider_frame,
        text=f" {text} ",
        bg=COLORS["white"],
        fg=COLORS["text_secondary"],
        font=FONTS["small_bold"],
    ).pack(side=tk.LEFT, padx=10)
    tk.Frame(divider_frame, bg=COLORS["border"], height=1).pack(
        side=tk.RIGHT, fill=tk.X, expand=True
    )

    return divider_frame


def create_button_pair(
    parent: tk.Widget,
    primary_text: str,
    primary_command: Callable,
    secondary_text: str,
    secondary_command: Callable,
    primary_color: str = "accent",
) -> tk.Frame:
    """Create a pair of buttons (primary and secondary/cancel)."""
    button_frame = tk.Frame(parent, bg=COLORS["white"])
    button_frame.pack(fill=tk.X)

    primary_btn = tk.Button(
        button_frame,
        text=primary_text,
        font=FONTS["body_bold"],
        bg=COLORS[primary_color],
        fg=COLORS["white"],
        bd=0,
        padx=20,
        pady=10,
        cursor="hand2",
        command=primary_command,
    )
    primary_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

    secondary_btn = tk.Button(
        button_frame,
        text=secondary_text,
        font=FONTS["body"],
        bg=COLORS["background"],
        fg=COLORS["text_secondary"],
        bd=1,
        relief=tk.SOLID,
        padx=20,
        pady=10,
        cursor="hand2",
        command=secondary_command,
    )
    secondary_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

    return button_frame
