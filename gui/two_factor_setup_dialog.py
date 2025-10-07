"""Two-Factor Authentication Setup Dialog."""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable
from PIL import Image, ImageTk
import io
from utils.totp_manager import TOTPManager
from database.db_manager import DatabaseManager
from gui.gui_utils import COLORS, FONTS


class TwoFactorSetupDialog:
    """Dialog for setting up Two-Factor Authentication."""

    def __init__(
        self,
        parent: tk.Tk,
        username: str,
        user_id: int,
        db_manager: DatabaseManager,
        on_success: Optional[Callable[[], None]] = None,
    ):
        """
        Initialize 2FA setup dialog.

        Args:
            parent: Parent window
            username: Username of the account
            user_id: User ID
            db_manager: Database manager instance
            on_success: Optional callback on successful setup
        """
        self.parent = parent
        self.username = username
        self.user_id = user_id
        self.db = db_manager
        self.on_success = on_success
        self.totp_manager = TOTPManager()

        # Generate secret and backup codes
        self.secret = self.totp_manager.generate_secret()
        self.backup_codes = self.totp_manager.generate_backup_codes(10)

        self.dialog: Optional[tk.Toplevel] = None
        self.result = False

        # Create dialog window
        self._create_dialog()

    def _create_dialog(self) -> None:
        """Create and configure the dialog window."""
        self.dialog = tk.Toplevel(self.parent)
        self.dialog.title("Enable Two-Factor Authentication")
        self.dialog.geometry("600x800")
        self.dialog.resizable(False, False)
        self.dialog.configure(bg="#2b2b2b")

        # Make dialog modal
        self.dialog.transient(self.parent)
        self.dialog.grab_set()

        # Center dialog
        self._center_dialog()

        # Create scrollable frame
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
        # Create scrollable frame
        canvas = tk.Canvas(self.dialog, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.dialog, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)

        scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Main container
        main_frame = ttk.Frame(scrollable_frame, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = ttk.Label(
            main_frame,
            text="Enable Two-Factor Authentication",
            font=("Arial", 16, "bold"),
            foreground="#ffffff",
        )
        title_label.pack(pady=(0, 20))

        # Step 1: Install Authenticator App
        self._create_step_section(
            main_frame,
            "Step 1: Install Authenticator App",
            "Download and install an authenticator app on your mobile device:\n\n"
            "• Google Authenticator (Android/iOS)\n"
            "• Microsoft Authenticator (Android/iOS)\n"
            "• Authy (Android/iOS/Desktop)\n"
            "• Any TOTP-compatible app",
        )

        # Step 2: Scan QR Code
        qr_frame = self._create_step_section(
            main_frame,
            "Step 2: Scan QR Code",
            "Open your authenticator app and scan this QR code:",
        )

        # Generate and display QR code
        self._display_qr_code(qr_frame)

        # Alternative: Manual entry
        manual_frame = ttk.Frame(qr_frame)
        manual_frame.pack(fill=tk.X, pady=(15, 0))

        ttk.Label(
            manual_frame,
            text="Can't scan? Enter this code manually:",
            font=("Arial", 9),
            foreground="#cccccc",
        ).pack(anchor=tk.W)

        formatted_secret = self.totp_manager.format_secret_for_display(self.secret)
        secret_text = tk.Text(
            manual_frame,
            height=2,
            width=50,
            font=("Courier", 10),
            bg="#3b3b3b",
            fg="#ffffff",
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=10,
            pady=10,
        )
        secret_text.insert("1.0", formatted_secret)
        secret_text.config(state=tk.DISABLED)
        secret_text.pack(fill=tk.X, pady=(5, 0))

        # Step 3: Verify Setup
        verify_frame = self._create_step_section(
            main_frame,
            "Step 3: Verify Setup",
            "Enter the 6-digit code from your authenticator app to verify:",
        )

        # Verification code entry
        code_frame = ttk.Frame(verify_frame)
        code_frame.pack(fill=tk.X, pady=(10, 0))

        self.code_var = tk.StringVar()
        self.code_var.trace_add("write", self._on_code_change)

        code_entry = ttk.Entry(
            code_frame,
            textvariable=self.code_var,
            font=("Arial", 16),
            width=10,
            justify=tk.CENTER,
        )
        code_entry.pack(side=tk.LEFT, padx=(0, 10))
        code_entry.focus()

        self.verify_btn = ttk.Button(
            code_frame, text="Verify Code", command=self._verify_code, state=tk.DISABLED
        )
        self.verify_btn.pack(side=tk.LEFT)

        # Verification status
        self.verify_status = ttk.Label(
            verify_frame, text="", font=("Arial", 9), foreground="#cccccc"
        )
        self.verify_status.pack(anchor=tk.W, pady=(5, 0))

        # Step 4: Save Backup Codes
        backup_frame = self._create_step_section(
            main_frame,
            "Step 4: Save Your Backup Codes",
            "⚠️ Important: Save these backup codes in a secure location.\n"
            "You can use them to access your account if you lose your phone.\n"
            "Each code can only be used once.",
        )

        # Backup codes display
        codes_text = tk.Text(
            backup_frame,
            height=12,
            width=50,
            font=("Courier", 10),
            bg="#3b3b3b",
            fg="#95e1d3",
            wrap=tk.WORD,
            relief=tk.FLAT,
            padx=15,
            pady=15,
        )

        codes_content = "\n".join(self.backup_codes)
        codes_text.insert("1.0", codes_content)
        codes_text.config(state=tk.DISABLED)
        codes_text.pack(fill=tk.X, pady=(10, 0))

        # Copy button
        copy_btn = ttk.Button(
            backup_frame, text="Copy to Clipboard", command=self._copy_backup_codes
        )
        copy_btn.pack(pady=(10, 0))

        # Final confirmation
        confirm_frame = ttk.Frame(main_frame)
        confirm_frame.pack(fill=tk.X, pady=(20, 0))

        self.confirm_var = tk.BooleanVar()
        confirm_check = ttk.Checkbutton(
            confirm_frame,
            text="I have saved my backup codes in a secure location",
            variable=self.confirm_var,
            command=self._on_confirm_change,
        )
        confirm_check.pack(anchor=tk.W)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(20, 0))

        self.enable_btn = ttk.Button(
            button_frame,
            text="Enable 2FA",
            command=self._enable_2fa,
            width=20,
            state=tk.DISABLED,
        )
        self.enable_btn.pack(side=tk.RIGHT, padx=(5, 0))

        cancel_btn = ttk.Button(
            button_frame, text="Cancel", command=self._on_cancel, width=15
        )
        cancel_btn.pack(side=tk.RIGHT)

        # Pack canvas and scrollbar
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def _create_step_section(
        self, parent: ttk.Frame, title: str, description: str
    ) -> ttk.Frame:
        """Create a step section with title and description."""
        section_frame = ttk.Frame(parent)
        section_frame.pack(fill=tk.X, pady=(0, 25))

        ttk.Label(
            section_frame, text=title, font=("Arial", 12, "bold"), foreground="#4ecdc4"
        ).pack(anchor=tk.W, pady=(0, 5))

        ttk.Label(
            section_frame,
            text=description,
            font=("Arial", 9),
            foreground="#cccccc",
            wraplength=550,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(0, 10))

        return section_frame

    def _display_qr_code(self, parent: ttk.Frame) -> None:
        """Generate and display QR code."""
        try:
            # Generate QR code image
            qr_image = self.totp_manager.generate_qr_code(self.secret, self.username)

            # Resize for display
            qr_image = qr_image.resize((250, 250), Image.Resampling.LANCZOS)

            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(qr_image)

            # Create label to display QR code
            qr_label = tk.Label(parent, image=photo, bg="#2b2b2b")
            qr_label.image = photo  # Keep reference
            qr_label.pack(pady=(10, 0))

        except Exception as e:
            error_label = ttk.Label(
                parent, text=f"Error generating QR code: {str(e)}", foreground="#ff6b6b"
            )
            error_label.pack(pady=(10, 0))

    def _on_code_change(self, *args) -> None:
        """Handle code entry changes."""
        code = self.code_var.get()

        # Enable verify button if code is 6 digits
        if code.isdigit() and len(code) == 6:
            self.verify_btn.config(state=tk.NORMAL)
        else:
            self.verify_btn.config(state=tk.DISABLED)

    def _verify_code(self) -> None:
        """Verify the entered TOTP code."""
        code = self.code_var.get()

        if self.totp_manager.verify_token(self.secret, code, window=2):
            self.verify_status.config(
                text="✓ Code verified successfully!", foreground="#95e1d3"
            )
            self.verified = True
            self._update_enable_button()
        else:
            self.verify_status.config(
                text="✗ Invalid code. Please try again.", foreground="#ff6b6b"
            )
            self.verified = False

    def _on_confirm_change(self) -> None:
        """Handle confirmation checkbox change."""
        self._update_enable_button()

    def _update_enable_button(self) -> None:
        """Update enable button state."""
        if hasattr(self, "verified") and self.verified and self.confirm_var.get():
            self.enable_btn.config(state=tk.NORMAL)
        else:
            self.enable_btn.config(state=tk.DISABLED)

    def _copy_backup_codes(self) -> None:
        """Copy backup codes to clipboard."""
        codes_text = "\n".join(self.backup_codes)
        self.dialog.clipboard_clear()
        self.dialog.clipboard_append(codes_text)
        messagebox.showinfo(
            "Copied", "Backup codes copied to clipboard!", parent=self.dialog
        )

    def _enable_2fa(self) -> None:
        """Enable Two-Factor Authentication."""
        try:
            success, message = self.db.enable_2fa(
                self.user_id, self.secret, self.backup_codes
            )

            if success:
                messagebox.showinfo(
                    "Success",
                    "Two-Factor Authentication has been enabled successfully!\n\n"
                    "You will need to enter a code from your authenticator app "
                    "each time you log in.",
                    parent=self.dialog,
                )

                self.result = True

                if self.on_success:
                    self.on_success()

                self._close_dialog()
            else:
                messagebox.showerror(
                    "Error", f"Failed to enable 2FA:\n{message}", parent=self.dialog
                )

        except Exception as e:
            messagebox.showerror(
                "Error", f"An error occurred:\n{str(e)}", parent=self.dialog
            )

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        if messagebox.askyesno(
            "Cancel Setup",
            "Are you sure you want to cancel Two-Factor Authentication setup?",
            parent=self.dialog,
        ):
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
            True if 2FA was enabled successfully, False otherwise
        """
        if self.dialog:
            self.dialog.wait_window()
        return self.result
