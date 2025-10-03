#!/usr/bin/env python3
"""
moreStacks Banking Application
A professional banking application with multiple account types,
transaction tracking, and data persistence.
"""

import tkinter as tk
from gui.login_window import LoginWindow
from gui.main_window import MainBankingWindow
from database.db_manager import DatabaseManager


class BankingApp:
    """Main application controller."""

    def __init__(self):
        self.root = tk.Tk()
        self.db = DatabaseManager()
        self.current_window = None

        # Start with login window
        self.show_login()

    def show_login(self):
        """Show login window."""
        self.root.withdraw()  # Hide main window
        login_root = tk.Toplevel(self.root)
        LoginWindow(login_root, self.on_login_success)
        login_root.protocol("WM_DELETE_WINDOW", self.root.quit)

    def on_login_success(self, user_id, user_info):
        """Handle successful login."""
        # Close any existing toplevel windows
        for widget in self.root.winfo_children():
            if isinstance(widget, tk.Toplevel):
                widget.destroy()

        # Show main banking window
        self.root.deiconify()
        MainBankingWindow(self.root, user_id, user_info, self.db)

    def run(self):
        """Start the application."""
        self.root.mainloop()
        self.db.close()


if __name__ == "__main__":
    app = BankingApp()
    app.run()
