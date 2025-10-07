"""Two-Factor Authentication Verification Dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Tuple
from utils.totp_manager import TOTPManager
from database.db_manager import DatabaseManager
from gui.gui_utils import COLORS, FONTS


class TwoFactorVerificationDialog:
    """Dialog for verifying TOTP codes during login."""

    def __init__(
        self, parent: tk.Tk, username: str, user_id: int, db_manager: DatabaseManager
    ):
        """
        Initialize 2FA verification dialog.

        Args:
            parent: Parent window
            username: Username of the account
            user_id: User ID
            db_manager: Database manager instance
        """
        self.parent = parent
        self.username = username
        self.user_id = user_id
        self.db = db_manager
        self.totp_manager = TOTPManager()

        self.dialog: Optional[tk.Toplevel] = None
        self.result = False
        self.attempts = 0
        self.max_attempts = 3
        self.using_backup_code = False

        # Create dialog window
        self._create_dialog()

    def _create_dialog(self) -> None:
        """Create and configure the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Two-Factor Authentication")
        self.dialog.geometry("450x400")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg="#2b2b2b")

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Disable close button (must verify or cancel)
        self.dialog.protocol("WM_DELETE_WINDOW", self._on_close_attempt)

        # Center dialog
        self._center_dialog()

        # Create widgets
        self._create_widgets()

    def _center_dialog(self) -> None:
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()

        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create and layout all dialog widgets."""
        # Main container
        main_frame = ttk.Frame(self.dialog, padding="30")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Icon/Title section
        title_label = ttk.Label(
            main_frame,
            text="🔐 Two-Factor Authentication",
            font=("Arial", 16, "bold"),
            foreground="#4ecdc4",
        )
        title_label.pack(pady=(0, 10))

        # Username display
        username_label = ttk.Label(
            main_frame,
            text=f"Account: {self.username}",
            font=("Arial", 10),
            foreground="#cccccc",
        )
        username_label.pack(pady=(0, 20))

        # Instructions
        self.instruction_label = ttk.Label(
            main_frame,
            text="Enter the 6-digit code from your authenticator app:",
            font=("Arial", 10),
            foreground="#ffffff",
            wraplength=380,
            justify=tk.CENTER,
        )
        self.instruction_label.pack(pady=(0, 20))

        # Code entry frame
        code_frame = ttk.Frame(main_frame)
        code_frame.pack(pady=(0, 10))

        self.code_var = tk.StringVar()
        self.code_var.trace_add("write", self._on_code_change)

        self.code_entry = ttk.Entry(
            code_frame,
            textvariable=self.code_var,
            font=("Arial", 24, "bold"),
            width=10,
            justify=tk.CENTER,
        )
        self.code_entry.pack()
        self.code_entry.focus()

        # Status message
        self.status_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 9),
            foreground="#cccccc",
            wraplength=380,
            justify=tk.CENTER,
        )
        self.status_label.pack(pady=(5, 0))

        # Attempts counter
        self.attempts_label = ttk.Label(
            main_frame, text="", font=("Arial", 8), foreground="#999999"
        )
        self.attempts_label.pack(pady=(5, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        self.verify_btn = ttk.Button(
            button_frame,
            text="Verify",
            command=self._verify_code,
            width=15,
            state=tk.DISABLED,
        )
        self.verify_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ttk.Button(
            button_frame, text="Cancel", command=self._on_cancel, width=12
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Divider
        separator = ttk.Separator(main_frame, orient="horizontal")
        separator.pack(fill=tk.X, pady=20)

        # Backup code option
        backup_frame = ttk.Frame(main_frame)
        backup_frame.pack(fill=tk.X)

        ttk.Label(
            backup_frame,
            text="Lost your device?",
            font=("Arial", 9),
            foreground="#cccccc",
        ).pack(anchor=tk.W, pady=(0, 5))

        self.backup_btn = ttk.Button(
            backup_frame,
            text="Use Backup Code Instead",
            command=self._switch_to_backup_code,
            width=25,
        )
        self.backup_btn.pack(anchor=tk.W)

        # Bind Enter key
        self.dialog.bind("<Return>", lambda e: self._verify_code())

    def _on_code_change(self, *args) -> None:
        """Handle code entry changes."""
        code = self.code_var.get()

        # Limit to 8 characters (for backup codes with dash)
        if len(code) > 9:
            self.code_var.set(code[:9])
            return

        # Enable verify button based on mode
        if self.using_backup_code:
            # Backup codes are 8 chars + dash: XXXX-XXXX
            if len(code) >= 8:
                self.verify_btn.config(state=tk.NORMAL)
            else:
                self.verify_btn.config(state=tk.DISABLED)
        else:
            # TOTP codes are exactly 6 digits
            if code.isdigit() and len(code) == 6:
                self.verify_btn.config(state=tk.NORMAL)
            else:
                self.verify_btn.config(state=tk.DISABLED)

    def _verify_code(self) -> None:
        """Verify the entered code (TOTP or backup)."""
        code = self.code_var.get().strip()

        if not code:
            return

        self.attempts += 1

        if self.using_backup_code:
            self._verify_backup_code(code)
        else:
            self._verify_totp_code(code)

    def _verify_totp_code(self, code: str) -> None:
        """Verify TOTP code."""
        # Get user's secret
        secret = self.db.get_2fa_secret(self.user_id)

        if not secret:
            self._show_error("2FA is not properly configured for this account.")
            return

        # Verify the code
        if self.totp_manager.verify_token(secret, code, window=1):
            # Update last used timestamp
            self.db.update_2fa_last_used(self.user_id)

            self.status_label.config(
                text="✓ Code verified successfully!", foreground="#95e1d3"
            )
            self.result = True
            self.dialog.after(500, self._close_dialog)
        else:
            self._handle_failed_attempt("Invalid code. Please try again.")

    def _verify_backup_code(self, code: str) -> None:
        """Verify backup code."""
        # Get backup codes
        backup_codes = self.db.get_backup_codes(self.user_id)

        if not backup_codes:
            self._show_error("No backup codes found for this account.")
            return

        # Verify the backup code
        is_valid, used_code = self.totp_manager.verify_backup_code(code, backup_codes)

        if is_valid:
            # Mark code as used
            success, message = self.db.use_backup_code(self.user_id, used_code)

            if success:
                self.status_label.config(
                    text=f"✓ Backup code accepted!\n{message}", foreground="#95e1d3"
                )
                self.result = True
                self.dialog.after(1000, self._close_dialog)
            else:
                self._show_error(f"Error using backup code: {message}")
        else:
            self._handle_failed_attempt("Invalid backup code. Please try again.")

    def _handle_failed_attempt(self, message: str) -> None:
        """Handle a failed verification attempt."""
        remaining = self.max_attempts - self.attempts

        if remaining > 0:
            self.status_label.config(text=f"✗ {message}", foreground="#ff6b6b")
            self.attempts_label.config(
                text=f"Attempts remaining: {remaining}",
                foreground="#ff6b6b" if remaining == 1 else "#999999",
            )
            self.code_var.set("")
            self.code_entry.focus()
        else:
            # Max attempts reached
            self._show_error(
                "Maximum verification attempts exceeded.\n"
                "Please try logging in again."
            )
            self.result = False
            self._close_dialog()

    def _switch_to_backup_code(self) -> None:
        """Switch to backup code entry mode."""
        self.using_backup_code = True

        # Update UI
        self.instruction_label.config(
            text="Enter one of your backup codes:\n(Format: XXXX-XXXX)"
        )

        self.code_entry.config(font=("Arial", 16))
        self.code_var.set("")
        self.code_entry.focus()

        self.backup_btn.config(
            text="Use Authenticator App Instead", command=self._switch_to_totp
        )

        self.status_label.config(text="", foreground="#cccccc")

        # Check if backup codes are available
        backup_codes = self.db.get_backup_codes(self.user_id)
        if not backup_codes:
            self.status_label.config(
                text="⚠️ No backup codes available. Please use your authenticator app.",
                foreground="#ffa500",
            )
            self.code_entry.config(state=tk.DISABLED)
            self.verify_btn.config(state=tk.DISABLED)
        else:
            self.status_label.config(
                text=f"{len(backup_codes)} backup code(s) remaining",
                foreground="#4ecdc4",
            )

    def _switch_to_totp(self) -> None:
        """Switch back to TOTP code entry mode."""
        self.using_backup_code = False

        # Update UI
        self.instruction_label.config(
            text="Enter the 6-digit code from your authenticator app:"
        )

        self.code_entry.config(font=("Arial", 24, "bold"), state=tk.NORMAL)
        self.code_var.set("")
        self.code_entry.focus()

        self.backup_btn.config(
            text="Use Backup Code Instead", command=self._switch_to_backup_code
        )

        self.status_label.config(text="", foreground="#cccccc")

    def _show_error(self, message: str) -> None:
        """Show error message."""
        messagebox.showerror("Verification Error", message, parent=self.dialog)

    def _on_close_attempt(self) -> None:
        """Handle window close attempt."""
        self._on_cancel()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if messagebox.askyesno(
            "Cancel Login",
            "Are you sure you want to cancel login?\n"
            "You will need to enter your username and password again.",
            parent=self.dialog,
        ):
            self.result = False
            self._close_dialog()

    def _close_dialog(self) -> None:
        """Close the dialog window."""
        if self.dialog:
            self.dialog.grab_release()
            self.dialog.destroy()
            self.dialog = None

    def show(self) -> bool:
        """
        Show the dialog and wait for it to close.

        Returns:
            True if verification successful, False otherwise
        """
        if self.dialog:
            self.dialog.wait_window()
        return self.result
