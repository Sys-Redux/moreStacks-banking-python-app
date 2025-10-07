"""Change Password Dialog for password updates and expiration handling."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from utils.password_validator import PasswordValidator
from database.db_manager import DatabaseManager
from config import SecurityConfig


class ChangePasswordDialog:
    """Dialog for changing user passwords with validation and strength meter."""

    def __init__(
        self,
        parent: tk.Tk,
        username: str,
        db_manager: DatabaseManager,
        on_success: Optional[Callable[[], None]] = None,
        force_change: bool = False,
    ):
        """
        Initialize change password dialog.

        Args:
            parent: Parent window
            username: Username of the account
            db_manager: Database manager instance
            on_success: Optional callback function to run on successful password change
            force_change: If True, dialog cannot be closed until password is changed
        """
        self.parent = parent
        self.username = username
        self.db = db_manager
        self.on_success = on_success
        self.force_change = force_change
        self.dialog: Optional[tk.Toplevel] = None
        self.result = False

        # Create dialog window
        self._create_dialog()

    def _create_dialog(self) -> None:
        """Create and configure the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Change Password")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg="#2b2b2b")

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Disable close button if force_change is True
        if self.force_change:
            self.dialog.protocol("WM_DELETE_WINDOW", self._on_force_change_close)
        else:
            self.dialog.protocol("WM_DELETE_WINDOW", self._on_cancel)

        # Center dialog on parent
        self._center_dialog()

        # Create UI elements
        self._create_widgets()

    def _center_dialog(self) -> None:
        """Center the dialog on the parent window."""
        self.dialog.update_idletasks()

        # Get parent position and size
        parent_x = self.parent.winfo_x()
        parent_y = self.parent.winfo_y()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()

        # Get dialog size
        dialog_width = self.dialog.winfo_width()
        dialog_height = self.dialog.winfo_height()

        # Calculate center position
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2

        self.dialog.geometry(f"+{x}+{y}")

    def _create_widgets(self) -> None:
        """Create and layout all dialog widgets."""
        # Main container with padding
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_text = (
            "Password Expired - Change Required"
            if self.force_change
            else "Change Password"
        )
        title_label = ttk.Label(
            main_frame,
            text=title_text,
            font=("Arial", 16, "bold"),
            foreground="#ffffff",
        )
        title_label.pack(pady=(0, 10))

        # Info message if forced change
        if self.force_change:
            info_frame = ttk.Frame(main_frame)
            info_frame.pack(fill=tk.X, pady=(0, 15))

            info_label = ttk.Label(
                info_frame,
                text=f"Your password has expired after {SecurityConfig.PASSWORD_EXPIRATION_DAYS} days.\n"
                "Please change your password to continue.",
                font=("Arial", 10),
                foreground="#ff6b6b",
                justify=tk.CENTER,
                wraplength=450,
            )
            info_label.pack()

        # Username display
        username_frame = ttk.Frame(main_frame)
        username_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(username_frame, text="Username:", font=("Arial", 10, "bold")).pack(
            anchor=tk.W
        )

        ttk.Label(username_frame, text=self.username, font=("Arial", 10)).pack(
            anchor=tk.W, padx=(10, 0)
        )

        # Current password field
        current_pw_frame = ttk.Frame(main_frame)
        current_pw_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            current_pw_frame, text="Current Password:", font=("Arial", 10, "bold")
        ).pack(anchor=tk.W)

        self.current_password_var = tk.StringVar()
        self.current_password_entry = ttk.Entry(
            current_pw_frame,
            textvariable=self.current_password_var,
            show="*",
            font=("Arial", 10),
            width=40,
        )
        self.current_password_entry.pack(fill=tk.X, pady=(5, 0))
        self.current_password_entry.focus()

        # New password field
        new_pw_frame = ttk.Frame(main_frame)
        new_pw_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(new_pw_frame, text="New Password:", font=("Arial", 10, "bold")).pack(
            anchor=tk.W
        )

        self.new_password_var = tk.StringVar()
        self.new_password_var.trace_add("write", self._on_password_change)
        self.new_password_entry = ttk.Entry(
            new_pw_frame,
            textvariable=self.new_password_var,
            show="*",
            font=("Arial", 10),
            width=40,
        )
        self.new_password_entry.pack(fill=tk.X, pady=(5, 0))

        # Password strength meter
        strength_frame = ttk.Frame(main_frame)
        strength_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(strength_frame, text="Password Strength:", font=("Arial", 9)).pack(
            anchor=tk.W
        )

        # Strength bar container
        strength_bar_frame = tk.Frame(
            strength_frame, bg="#3b3b3b", height=20, relief=tk.SUNKEN, borderwidth=1
        )
        strength_bar_frame.pack(fill=tk.X, pady=(5, 0))
        strength_bar_frame.pack_propagate(False)

        # Strength bar fill
        self.strength_bar = tk.Frame(strength_bar_frame, bg="#666666", height=18)
        self.strength_bar.place(x=0, y=0, relwidth=0, height=18)

        # Strength label
        self.strength_label = ttk.Label(
            strength_frame, text="", font=("Arial", 9), foreground="#cccccc"
        )
        self.strength_label.pack(anchor=tk.W, pady=(5, 0))

        # Confirm password field
        confirm_pw_frame = ttk.Frame(main_frame)
        confirm_pw_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(
            confirm_pw_frame, text="Confirm New Password:", font=("Arial", 10, "bold")
        ).pack(anchor=tk.W)

        self.confirm_password_var = tk.StringVar()
        self.confirm_password_entry = ttk.Entry(
            confirm_pw_frame,
            textvariable=self.confirm_password_var,
            show="*",
            font=("Arial", 10),
            width=40,
        )
        self.confirm_password_entry.pack(fill=tk.X, pady=(5, 0))

        # Password requirements
        req_frame = ttk.Frame(main_frame)
        req_frame.pack(fill=tk.X, pady=(0, 20))

        ttk.Label(
            req_frame, text="Password Requirements:", font=("Arial", 9, "bold")
        ).pack(anchor=tk.W)

        requirements_text = PasswordValidator.get_requirements_text()
        ttk.Label(
            req_frame,
            text=requirements_text,
            font=("Arial", 8),
            foreground="#cccccc",
            justify=tk.LEFT,
        ).pack(anchor=tk.W, padx=(10, 0), pady=(5, 0))

        # Validation message label
        self.validation_label = ttk.Label(
            main_frame,
            text="",
            font=("Arial", 9),
            foreground="#ff6b6b",
            wraplength=450,
            justify=tk.LEFT,
        )
        self.validation_label.pack(fill=tk.X, pady=(0, 15))

        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))

        # Change Password button
        self.change_btn = ttk.Button(
            button_frame,
            text="Change Password",
            command=self._on_change_password,
            width=20,
        )
        self.change_btn.pack(side=tk.RIGHT, padx=(5, 0))

        # Cancel button (disabled if force_change)
        if not self.force_change:
            cancel_btn = ttk.Button(
                button_frame, text="Cancel", command=self._on_cancel, width=15
            )
            cancel_btn.pack(side=tk.RIGHT)

        # Bind Enter key
        self.dialog.bind("<Return>", lambda e: self._on_change_password())

    def _on_password_change(self, *args) -> None:
        """Update password strength meter when password changes."""
        password = self.new_password_var.get()

        if not password:
            # Reset strength meter
            self.strength_bar.place_configure(relwidth=0)
            self.strength_label.config(text="")
            return

        # Get password strength
        strength = PasswordValidator.get_password_strength(password)

        # Update strength bar
        strength_colors = {
            "Weak": ("#ff6b6b", 0.25),
            "Medium": ("#ffa500", 0.50),
            "Strong": ("#4ecdc4", 0.75),
            "Very Strong": ("#95e1d3", 1.0),
        }

        color, width = strength_colors.get(strength, ("#666666", 0))
        self.strength_bar.config(bg=color)
        self.strength_bar.place_configure(relwidth=width)
        self.strength_label.config(text=f"Strength: {strength}")

    def _on_change_password(self) -> None:
        """Handle password change button click."""
        current_password = self.current_password_var.get()
        new_password = self.new_password_var.get()
        confirm_password = self.confirm_password_var.get()

        # Clear previous validation message
        self.validation_label.config(text="")

        # Validate inputs
        if not current_password:
            self.validation_label.config(text="Please enter your current password.")
            self.current_password_entry.focus()
            return

        if not new_password:
            self.validation_label.config(text="Please enter a new password.")
            self.new_password_entry.focus()
            return

        if not confirm_password:
            self.validation_label.config(text="Please confirm your new password.")
            self.confirm_password_entry.focus()
            return

        # Check if passwords match
        if new_password != confirm_password:
            self.validation_label.config(text="New passwords do not match.")
            self.confirm_password_entry.focus()
            self.confirm_password_entry.selection_range(0, tk.END)
            return

        # Validate new password strength
        is_valid, message = PasswordValidator.validate_password(new_password)
        if not is_valid:
            self.validation_label.config(text=message)
            self.new_password_entry.focus()
            return

        # Attempt password change
        try:
            success, message = self.db.change_user_password_by_username(
                username=self.username,
                old_password=current_password,
                new_password=new_password,
            )

            if success:
                # Show success message
                messagebox.showinfo(
                    "Success", "Password changed successfully!", parent=self.dialog
                )

                self.result = True

                # Call success callback if provided
                if self.on_success:
                    self.on_success()

                # Close dialog
                self._close_dialog()
            else:
                # Show error message
                self.validation_label.config(text=message)

                # Focus appropriate field based on error
                if (
                    "current password" in message.lower()
                    or "incorrect" in message.lower()
                ):
                    self.current_password_entry.focus()
                    self.current_password_entry.selection_range(0, tk.END)
                else:
                    self.new_password_entry.focus()

        except Exception as e:
            messagebox.showerror(
                "Error",
                f"An error occurred while changing password:\n{str(e)}",
                parent=self.dialog,
            )

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if not self.force_change:
            self._close_dialog()

    def _on_force_change_close(self) -> None:
        """Handle window close attempt when force_change is True."""
        messagebox.showwarning(
            "Password Change Required",
            "You must change your password before continuing.\n"
            "Your password has expired and cannot be used anymore.",
            parent=self.dialog,
        )

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
            True if password was changed successfully, False otherwise
        """
        if self.dialog:
            self.dialog.wait_window()
        return self.result
