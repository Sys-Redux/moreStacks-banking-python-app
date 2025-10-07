"""
New Account Dialog Module

Dialog for creating a new bank account.
"""

import tkinter as tk
from tkinter import messagebox
from gui.gui_utils import (
    COLORS,
    FONTS,
    create_combobox,
    create_labeled_entry,
    create_modal_dialog,
    create_button_pair,
)


class NewAccountDialog:
    """Dialog for creating a new account."""

    def __init__(self, parent, user_id, db, on_success):
        """
        Initialize new account dialog.

        Args:
            parent: Parent window
            user_id: ID of the user creating the account
            db: Database manager instance
            on_success: Callback function to refresh displays after account creation
        """
        self.user_id = user_id
        self.db = db
        self.on_success = on_success

        self.window = create_modal_dialog(parent, "Create New Account", 400, 300)
        self.create_widgets()

    def create_widgets(self):
        """Create new account dialog widgets."""
        main_frame = tk.Frame(self.window, bg=COLORS["white"], padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            main_frame,
            text="Create New Account",
            font=FONTS["heading"],
            bg=COLORS["white"],
        )
        title.pack(pady=(0, 20))

        # Account type
        type_label = tk.Label(
            main_frame, text="Account Type:", font=FONTS["label"], bg=COLORS["white"]
        )
        type_label.pack(anchor=tk.W, pady=(0, 5))

        self.account_type_var, _ = create_combobox(
            main_frame,
            ["Checking", "Savings", "Credit"],
            default="Checking",
            fill=tk.X,
            pady=(0, 15),
        )

        # Initial deposit
        self.deposit_entry = create_labeled_entry(main_frame, "Initial Deposit ($):")
        self.deposit_entry.insert(0, "0")
        self.deposit_entry.master.pack(pady=(0, 20))

        # Buttons
        create_button_pair(
            main_frame,
            "Create Account",
            self.create_account,
            "Cancel",
            self.window.destroy,
            primary_color="accent",
        )

    def create_account(self):
        """Create the new account."""
        try:
            account_type = self.account_type_var.get().lower()
            initial_deposit = float(self.deposit_entry.get())

            if initial_deposit < 0:
                messagebox.showerror("Error", "Initial deposit cannot be negative.")
                return

            # Set default rates/limits
            interest_rate = 0.02 if account_type == "savings" else 0
            credit_limit = 5000 if account_type == "credit" else 0

            account_id, account_number = self.db.create_account(
                self.user_id, account_type, initial_deposit, interest_rate, credit_limit
            )

            if account_id:
                # Close dialog first for instant feedback, then show success message
                self.window.destroy()
                self.on_success()  # Refresh displays
                messagebox.showinfo(
                    "Success",
                    f"New {account_type} account created!\nAccount Number: {account_number}",
                )
            else:
                messagebox.showerror("Error", "Failed to create account.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid deposit amount.")
