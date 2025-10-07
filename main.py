#!/usr/bin/env python3
"""
moreStacks Banking Application
A professional banking application with multiple account types,
transaction tracking, and data persistence.
"""

import tkinter as tk
from datetime import datetime
from gui.login_window import LoginWindow
from gui.main_window import MainBankingWindow
from database.db_manager import DatabaseManager
from config import SecurityConfig


class BankingApp:
    """Main application controller."""

    def __init__(self):
        self.root = tk.Tk()
        self.db = DatabaseManager()
        self.current_window = None
        self.cleanup_job_id = None

        # Start with login window
        self.show_login()

        # Start session cleanup background task
        self.start_session_cleanup()

    def show_login(self):
        """Show login window."""
        self.root.withdraw()  # Hide main window
        login_root = tk.Toplevel(self.root)
        LoginWindow(login_root, self.on_login_success)
        login_root.protocol("WM_DELETE_WINDOW", self.root.quit)

    def on_login_success(self, user_id, user_info, session_token):
        """Handle successful login."""
        # Close any existing toplevel windows
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()

        # Show main banking window with session token
        self.root.deiconify()
        MainBankingWindow(self.root, user_id, user_info, self.db, session_token)

    def start_session_cleanup(self):
        """Start periodic cleanup of expired sessions from database."""
        self.cleanup_expired_sessions()

    def cleanup_expired_sessions(self):
        """Remove expired sessions from the database."""
        current_time = datetime.now().isoformat()
        deleted_count = self.db.cleanup_expired_sessions(current_time)

        # Log cleanup if sessions were deleted (optional, for debugging)
        # if deleted_count > 0:
        #     print(f"Cleaned up {deleted_count} expired session(s)")

        # Schedule next cleanup
        cleanup_interval = (
            SecurityConfig.SESSION_CLEANUP_INTERVAL * 1000
        )  # Convert to milliseconds
        self.cleanup_job_id = self.root.after(
            cleanup_interval, self.cleanup_expired_sessions
        )

    def run(self):
        """Start the application."""
        self.root.mainloop()

        # Cancel cleanup job if it's running
        if self.cleanup_job_id:
            self.root.after_cancel(self.cleanup_job_id)

        self.db.close()


if __name__ == "__main__":
    app = BankingApp()
    app.run()
