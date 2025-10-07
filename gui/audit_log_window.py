"""
Security Audit Log Viewer for moreStacks Banking Application.

Provides a comprehensive interface for viewing, filtering, and exporting audit logs.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from database.db_manager import DatabaseManager
from utils.audit_logger import AuditSeverity, AuditCategory, AuditEventType, AuditLogger
from gui.gui_utils import (
    COLORS,
    FONTS,
    create_header_frame,
    create_button,
    create_modal_dialog,
)


class AuditLogWindow:
    """Window for viewing and managing security audit logs."""

    def __init__(
        self, parent, user_id: int, username: str, db_manager: DatabaseManager
    ):
        """
        Initialize the Audit Log Viewer window.

        Args:
            parent: Parent window
            user_id: Current user ID
            username: Current username
            db_manager: Database manager instance
        """
        self.parent = parent
        self.user_id = user_id
        self.username = username
        self.db = db_manager
        self.audit_logger = AuditLogger(db_manager)

        # Pagination
        self.current_page = 1
        self.items_per_page = 50
        self.total_items = 0

        # Filter state
        self.filters = {}

        # Create the window
        self.window = create_modal_dialog(parent, "Security Audit Log", 1200, 700)
        self.create_widgets()
        self.load_logs()

        # Log that audit logs were viewed
        self.audit_logger.log_audit_access(
            user_id=self.user_id, username=self.username, action="viewed"
        )

    def create_widgets(self):
        """Create the audit log viewer interface."""
        # Header
        header_frame = tk.Frame(self.window, bg=COLORS["primary"], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title_label = tk.Label(
            header_frame,
            text="🔍 Security Audit Log",
            font=FONTS["title_medium"],
            bg=COLORS["primary"],
            fg=COLORS["white"],
        )
        title_label.pack(pady=20)

        # Main content frame
        content_frame = tk.Frame(self.window, bg=COLORS["background"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Filter panel
        self._create_filter_panel(content_frame)

        # Log display area
        self._create_log_display(content_frame)

        # Pagination and action buttons
        self._create_bottom_panel(content_frame)

    def _create_filter_panel(self, parent):
        """Create the filter panel."""
        filter_frame = tk.Frame(parent, bg=COLORS["white"], relief=tk.GROOVE, bd=1)
        filter_frame.pack(fill=tk.X, pady=(0, 10))

        # Title
        filter_title = tk.Label(
            filter_frame,
            text="🔎 Filters",
            font=FONTS["label_bold"],
            bg=COLORS["white"],
            fg=COLORS["text"],
        )
        filter_title.pack(anchor=tk.W, padx=10, pady=(10, 5))

        # Filter controls frame
        controls_frame = tk.Frame(filter_frame, bg=COLORS["white"])
        controls_frame.pack(fill=tk.X, padx=10, pady=(0, 10))

        # Row 1: Event Type, Category, Severity
        row1 = tk.Frame(controls_frame, bg=COLORS["white"])
        row1.pack(fill=tk.X, pady=5)

        # Event Type filter
        tk.Label(
            row1,
            text="Event Type:",
            font=FONTS["label"],
            bg=COLORS["white"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.event_type_var = tk.StringVar(value="All")
        event_types = [
            "All",
            "LOGIN_SUCCESS",
            "LOGIN_FAILED",
            "LOGOUT",
            "PASSWORD_CHANGED",
            "TWO_FA_ENABLED",
            "TWO_FA_DISABLED",
            "DEPOSIT",
            "WITHDRAWAL",
            "TRANSFER",
        ]
        event_type_combo = ttk.Combobox(
            row1,
            textvariable=self.event_type_var,
            values=event_types,
            state="readonly",
            width=20,
            font=FONTS["label"],
        )
        event_type_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Category filter
        tk.Label(
            row1,
            text="Category:",
            font=FONTS["label"],
            bg=COLORS["white"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.category_var = tk.StringVar(value="All")
        categories = [
            "All",
            "AUTHENTICATION",
            "SECURITY",
            "TRANSACTION",
            "ACCOUNT",
            "SYSTEM",
        ]
        category_combo = ttk.Combobox(
            row1,
            textvariable=self.category_var,
            values=categories,
            state="readonly",
            width=15,
            font=FONTS["label"],
        )
        category_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Severity filter
        tk.Label(
            row1,
            text="Severity:",
            font=FONTS["label"],
            bg=COLORS["white"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.severity_var = tk.StringVar(value="All")
        severities = ["All", "INFO", "WARNING", "CRITICAL"]
        severity_combo = ttk.Combobox(
            row1,
            textvariable=self.severity_var,
            values=severities,
            state="readonly",
            width=12,
            font=FONTS["label"],
        )
        severity_combo.pack(side=tk.LEFT)

        # Row 2: Date range
        row2 = tk.Frame(controls_frame, bg=COLORS["white"])
        row2.pack(fill=tk.X, pady=5)

        tk.Label(
            row2,
            text="Date Range:",
            font=FONTS["label"],
            bg=COLORS["white"],
            fg=COLORS["text"],
        ).pack(side=tk.LEFT, padx=(0, 5))

        self.date_range_var = tk.StringVar(value="Last 7 Days")
        date_ranges = [
            "Last 24 Hours",
            "Last 7 Days",
            "Last 30 Days",
            "Last 90 Days",
            "All Time",
        ]
        date_range_combo = ttk.Combobox(
            row2,
            textvariable=self.date_range_var,
            values=date_ranges,
            state="readonly",
            width=15,
            font=FONTS["label"],
        )
        date_range_combo.pack(side=tk.LEFT, padx=(0, 15))

        # Apply and Reset buttons
        apply_btn = create_button(
            row2, "Apply Filters", self.apply_filters, style="primary", width=15
        )
        apply_btn.pack(side=tk.LEFT, padx=(0, 10))

        reset_btn = create_button(
            row2, "Reset", self.reset_filters, style="secondary", width=12
        )
        reset_btn.pack(side=tk.LEFT)

    def _create_log_display(self, parent):
        """Create the log display area with treeview."""
        display_frame = tk.Frame(parent, bg=COLORS["white"], relief=tk.GROOVE, bd=1)
        display_frame.pack(fill=tk.BOTH, expand=True)

        # Results count
        self.results_label = tk.Label(
            display_frame,
            text="Loading logs...",
            font=FONTS["label"],
            bg=COLORS["white"],
            fg=COLORS["text_secondary"],
        )
        self.results_label.pack(anchor=tk.W, padx=10, pady=5)

        # Create treeview with scrollbars
        tree_frame = tk.Frame(display_frame, bg=COLORS["white"])
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Scrollbars
        y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)
        x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Configure treeview style
        style = ttk.Style()
        style.configure(
            "Audit.Treeview",
            background=COLORS["white"],
            foreground=COLORS["text"],
            fieldbackground=COLORS["white"],
            font=FONTS["label"],
        )
        style.configure(
            "Audit.Treeview.Heading",
            font=FONTS["label_bold"],
            background=COLORS["background"],
            foreground=COLORS["text"],
        )

        # Define columns
        columns = (
            "timestamp",
            "username",
            "event_type",
            "category",
            "severity",
            "description",
        )
        self.tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show="headings",
            yscrollcommand=y_scrollbar.set,
            xscrollcommand=x_scrollbar.set,
            style="Audit.Treeview",
            height=15,
        )

        # Configure column headings
        self.tree.heading("timestamp", text="Timestamp")
        self.tree.heading("username", text="User")
        self.tree.heading("event_type", text="Event Type")
        self.tree.heading("category", text="Category")
        self.tree.heading("severity", text="Severity")
        self.tree.heading("description", text="Description")

        # Configure column widths
        self.tree.column("timestamp", width=150, minwidth=150)
        self.tree.column("username", width=100, minwidth=100)
        self.tree.column("event_type", width=150, minwidth=150)
        self.tree.column("category", width=120, minwidth=120)
        self.tree.column("severity", width=80, minwidth=80)
        self.tree.column("description", width=400, minwidth=200)

        # Configure scrollbars
        y_scrollbar.config(command=self.tree.yview)
        x_scrollbar.config(command=self.tree.xview)

        self.tree.pack(fill=tk.BOTH, expand=True)

        # Bind double-click to show details
        self.tree.bind("<Double-Button-1>", self.show_log_details)

        # Tag configurations for severity colors
        self.tree.tag_configure("INFO", foreground=COLORS["text"])
        self.tree.tag_configure("WARNING", foreground=COLORS["warning"])
        self.tree.tag_configure("CRITICAL", foreground=COLORS["error"])

    def _create_bottom_panel(self, parent):
        """Create the bottom panel with pagination and actions."""
        bottom_frame = tk.Frame(parent, bg=COLORS["background"])
        bottom_frame.pack(fill=tk.X, pady=(10, 0))

        # Left side: Pagination
        pagination_frame = tk.Frame(bottom_frame, bg=COLORS["background"])
        pagination_frame.pack(side=tk.LEFT)

        self.page_label = tk.Label(
            pagination_frame,
            text="Page 1 of 1",
            font=FONTS["label"],
            bg=COLORS["background"],
            fg=COLORS["text"],
        )
        self.page_label.pack(side=tk.LEFT, padx=(0, 10))

        prev_btn = create_button(
            pagination_frame,
            "◀ Previous",
            self.previous_page,
            style="secondary",
            width=12,
        )
        prev_btn.pack(side=tk.LEFT, padx=(0, 5))

        next_btn = create_button(
            pagination_frame, "Next ▶", self.next_page, style="secondary", width=12
        )
        next_btn.pack(side=tk.LEFT)

        # Right side: Action buttons
        actions_frame = tk.Frame(bottom_frame, bg=COLORS["background"])
        actions_frame.pack(side=tk.RIGHT)

        export_btn = create_button(
            actions_frame,
            "📥 Export to CSV",
            self.export_logs,
            style="primary",
            width=15,
        )
        export_btn.pack(side=tk.LEFT, padx=(0, 10))

        refresh_btn = create_button(
            actions_frame, "🔄 Refresh", self.load_logs, style="secondary", width=12
        )
        refresh_btn.pack(side=tk.LEFT, padx=(0, 10))

        close_btn = create_button(
            actions_frame, "Close", self.window.destroy, style="secondary", width=10
        )
        close_btn.pack(side=tk.LEFT)

    def apply_filters(self):
        """Apply the selected filters and reload logs."""
        self.filters = {}

        # Event type filter
        if self.event_type_var.get() != "All":
            self.filters["event_type"] = self.event_type_var.get()

        # Category filter
        if self.category_var.get() != "All":
            self.filters["event_category"] = self.category_var.get()

        # Severity filter
        if self.severity_var.get() != "All":
            self.filters["severity"] = self.severity_var.get()

        # Date range filter
        date_range = self.date_range_var.get()
        now = datetime.now()

        if date_range == "Last 24 Hours":
            self.filters["start_date"] = (now - timedelta(days=1)).isoformat()
        elif date_range == "Last 7 Days":
            self.filters["start_date"] = (now - timedelta(days=7)).isoformat()
        elif date_range == "Last 30 Days":
            self.filters["start_date"] = (now - timedelta(days=30)).isoformat()
        elif date_range == "Last 90 Days":
            self.filters["start_date"] = (now - timedelta(days=90)).isoformat()
        # "All Time" has no date filter

        # Always filter by current user (not admin)
        self.filters["user_id"] = self.user_id

        # Reset to first page
        self.current_page = 1
        self.load_logs()

    def reset_filters(self):
        """Reset all filters to default values."""
        self.event_type_var.set("All")
        self.category_var.set("All")
        self.severity_var.set("All")
        self.date_range_var.set("Last 7 Days")
        self.filters = {}
        self.current_page = 1
        self.load_logs()

    def load_logs(self):
        """Load and display audit logs based on current filters and pagination."""
        # Clear existing items
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Calculate offset
        offset = (self.current_page - 1) * self.items_per_page

        # Get logs from database
        logs = self.db.search_audit_logs(
            filters=self.filters, limit=self.items_per_page, offset=offset
        )

        # Get total count for pagination
        self.total_items = self.db.get_audit_log_count(self.filters)

        # Display logs
        for log in logs:
            timestamp = self._format_timestamp(log.get("created_at", ""))
            username = log.get("username", "N/A")
            event_type = log.get("event_type", "N/A")
            category = log.get("event_category", "N/A")
            severity = log.get("severity", "INFO")
            description = log.get("description", "")

            # Insert with severity tag for color coding
            self.tree.insert(
                "",
                tk.END,
                values=(
                    timestamp,
                    username,
                    event_type,
                    category,
                    severity,
                    description,
                ),
                tags=(severity,),
            )

        # Update results label
        start_idx = offset + 1 if logs else 0
        end_idx = offset + len(logs)
        self.results_label.config(
            text=f"Showing {start_idx}-{end_idx} of {self.total_items} log entries"
        )

        # Update pagination label
        total_pages = max(
            1, (self.total_items + self.items_per_page - 1) // self.items_per_page
        )
        self.page_label.config(text=f"Page {self.current_page} of {total_pages}")

    def previous_page(self):
        """Go to the previous page of logs."""
        if self.current_page > 1:
            self.current_page -= 1
            self.load_logs()

    def next_page(self):
        """Go to the next page of logs."""
        total_pages = max(
            1, (self.total_items + self.items_per_page - 1) // self.items_per_page
        )
        if self.current_page < total_pages:
            self.current_page += 1
            self.load_logs()

    def show_log_details(self, event):
        """Show detailed information about a selected log entry."""
        selection = self.tree.selection()
        if not selection:
            return

        item = self.tree.item(selection[0])
        values = item["values"]

        if not values:
            return

        # Create details dialog
        details_window = create_modal_dialog(self.window, "Audit Log Details", 600, 400)

        # Content frame
        content_frame = tk.Frame(details_window, bg=COLORS["white"], padx=20, pady=20)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Title
        title_label = tk.Label(
            content_frame,
            text="📋 Log Entry Details",
            font=FONTS["title_small"],
            bg=COLORS["white"],
            fg=COLORS["primary"],
        )
        title_label.pack(anchor=tk.W, pady=(0, 20))

        # Details text
        details_text = tk.Text(
            content_frame,
            font=FONTS["label"],
            bg=COLORS["background"],
            fg=COLORS["text"],
            wrap=tk.WORD,
            height=15,
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        details_text.pack(fill=tk.BOTH, expand=True)

        # Format details
        details_content = f"""Timestamp: {values[0]}
Username: {values[1]}
Event Type: {values[2]}
Category: {values[3]}
Severity: {values[4]}

Description:
{values[5]}
"""

        details_text.insert("1.0", details_content)
        details_text.config(state=tk.DISABLED)

        # Close button
        close_btn = create_button(
            content_frame, "Close", details_window.destroy, style="secondary", width=12
        )
        close_btn.pack(pady=(10, 0))

    def export_logs(self):
        """Export current filtered logs to CSV file."""
        # Ask for save location
        filepath = filedialog.asksaveasfilename(
            parent=self.window,
            title="Export Audit Logs",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"audit_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        )

        if not filepath:
            return

        # Export logs
        success, message = self.db.export_audit_logs_csv(filepath, self.filters)

        if success:
            messagebox.showinfo("Export Successful", message)
            # Log the export
            self.audit_logger.log_audit_access(
                user_id=self.user_id,
                username=self.username,
                action="exported",
                details=f"Exported to {filepath}",
            )
        else:
            messagebox.showerror("Export Failed", message)

    def _format_timestamp(self, timestamp_str: str) -> str:
        """
        Format timestamp string for display.

        Args:
            timestamp_str: ISO format timestamp string

        Returns:
            Formatted timestamp string
        """
        try:
            dt = datetime.fromisoformat(timestamp_str)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return timestamp_str

    def show(self):
        """Show the audit log window."""
        self.window.wait_window()
