"""
Transfer Dialog Module

Dialog for transferring money between accounts.
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


class TransferDialog:
    """Dialog for transferring money between accounts."""

    def __init__(
        self,
        parent,
        from_account,
        all_accounts,
        db,
        on_success,
        user_id=None,
        audit_logger=None,
    ):
        """
        Initialize transfer dialog.

        Args:
            parent: Parent window
            from_account: Account to transfer from
            all_accounts: List of all user accounts
            db: Database manager instance
            on_success: Callback function to refresh displays after transfer
            user_id: User ID for audit logging (optional)
            audit_logger: Audit logger instance (optional)
        """
        self.from_account = from_account
        self.all_accounts = [
            acc for acc in all_accounts if acc.account_id != from_account.account_id
        ]
        self.db = db
        self.on_success = on_success
        self.user_id = user_id
        self.audit_logger = audit_logger

        self.window = create_modal_dialog(parent, "Transfer Money", 400, 350)
        self.create_widgets()

    def create_widgets(self):
        """Create transfer dialog widgets."""
        main_frame = tk.Frame(self.window, bg=COLORS["white"], padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            main_frame, text="Transfer Money", font=FONTS["heading"], bg=COLORS["white"]
        )
        title.pack(pady=(0, 20))

        # From account
        from_label = tk.Label(
            main_frame,
            text=f"From: {self.from_account.get_account_type()} - {self.from_account.account_number[-4:]}",
            font=FONTS["label"],
            bg=COLORS["white"],
        )
        from_label.pack(anchor=tk.W, pady=(0, 5))

        balance_label = tk.Label(
            main_frame,
            text=f"Available: {self.from_account.get_balance_formatted()}",
            font=FONTS["small"],
            bg=COLORS["white"],
            fg=COLORS["text_secondary"],
        )
        balance_label.pack(anchor=tk.W, pady=(0, 15))

        # To account
        to_label = tk.Label(
            main_frame, text="To Account:", font=FONTS["label"], bg=COLORS["white"]
        )
        to_label.pack(anchor=tk.W, pady=(0, 5))

        account_names = [
            f"{acc.get_account_type()} - {acc.account_number[-4:]}"
            for acc in self.all_accounts
        ]

        self.to_account_var, _ = create_combobox(
            main_frame,
            account_names,
            default=account_names[0] if account_names else None,
            fill=tk.X,
            pady=(0, 15),
        )

        # Amount
        self.amount_entry = create_labeled_entry(main_frame, "Amount ($):")
        self.amount_entry.master.pack(pady=(0, 20))

        # Buttons
        create_button_pair(
            main_frame,
            "Transfer",
            self.do_transfer,
            "Cancel",
            self.window.destroy,
            primary_color="accent",
        )

    def do_transfer(self):
        """Execute the transfer."""
        try:
            amount = float(self.amount_entry.get())

            if amount <= 0:
                messagebox.showerror("Error", "Amount must be positive.")
                return

            # Find selected account
            selected_name = self.to_account_var.get()
            to_account = None
            for acc in self.all_accounts:
                if (
                    f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                    == selected_name
                ):
                    to_account = acc
                    break

            if not to_account:
                messagebox.showerror("Error", "Please select a destination account.")
                return

            # Perform transfer in database
            success, message = self.db.create_transfer(
                self.from_account.account_id,
                to_account.account_id,
                amount,
                f"Transfer to {to_account.account_number}",
            )

            if success:
                # Log the transfer
                if self.audit_logger and self.user_id:
                    self.audit_logger.log_transaction(
                        user_id=self.user_id,
                        transaction_type="transfer",
                        amount=amount,
                        account_id=self.from_account.account_id,
                        details={
                            "from_account": self.from_account.account_number,
                            "to_account": to_account.account_number,
                            "to_account_id": to_account.account_id,
                        },
                    )

                # Close dialog first for instant feedback, then show success message
                self.window.destroy()
                self.on_success()  # Refresh displays
                messagebox.showinfo("Success", "Transfer completed successfully!")
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")
