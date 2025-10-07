import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from database.db_manager import DatabaseManager
from utils.password_validator import PasswordValidator
from utils.session_manager import SessionManager
from utils.password_expiration import PasswordExpirationManager
from utils.audit_logger import AuditLogger
from gui.change_password_dialog import ChangePasswordDialog
from gui.two_factor_verification_dialog import TwoFactorVerificationDialog
from config import SecurityConfig
from gui.gui_utils import (
    COLORS,
    FONTS,
    create_header_frame,
    create_labeled_entry,
    create_button,
    create_divider,
    create_modal_dialog,
    create_button_pair,
)


class LoginWindow:
    """Login and registration window for moreStacks Banking."""

    def __init__(self, root, on_login_success):
        self.root = root
        self.on_login_success = on_login_success
        self.db = DatabaseManager()
        self.audit_logger = AuditLogger(self.db)
        self.session_manager = SessionManager(
            timeout_minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES,
            warning_minutes=SecurityConfig.SESSION_WARNING_MINUTES,
        )
        self.password_expiration = PasswordExpirationManager()

        # Window setup
        self.root.title("moreStacks Banking - Login")
        self.root.geometry("450x700")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["background"])

        self.create_widgets()

    def create_widgets(self):
        """Create login interface widgets."""
        # Header
        create_header_frame(self.root, "moreStacks", "Banking Made Simple")

        # Main frame
        main_frame = tk.Frame(self.root, bg=COLORS["white"], padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Title
        login_title = tk.Label(
            main_frame,
            text="Sign In",
            font=FONTS["title_small"],
            bg=COLORS["white"],
            fg=COLORS["primary"],
        )
        login_title.pack(pady=(0, 20))

        # Username and Password entries
        self.username_entry = create_labeled_entry(main_frame, "Username:", pady_top=10)
        self.password_entry = create_labeled_entry(
            main_frame, "Password:", show="●", pady_top=15
        )

        # Bind Enter key to login
        self.password_entry.bind("<Return>", lambda e: self.login())

        # Login button
        create_button(
            main_frame,
            "Sign In",
            self.login,
            color_key="accent",
            fill=tk.X,
            pady=(25, 10),
        )

        # Divider
        create_divider(main_frame, "OR", pady=20)

        # New user prompt
        new_user_text = tk.Label(
            main_frame,
            text="Don't have an account?",
            font=FONTS["label"],
            bg=COLORS["white"],
            fg=COLORS["text_primary"],
        )
        new_user_text.pack(pady=(10, 5))

        # Register button
        create_button(
            main_frame,
            "Create New Account",
            self.show_register,
            color_key="secondary",
            fill=tk.X,
            pady=(5, 15),
            padx=5,
        )

        # Footer
        footer = tk.Label(
            self.root,
            text="© 2025 moreStacks Banking. All rights reserved.",
            font=FONTS["tiny"],
            bg=COLORS["background"],
            fg=COLORS["text_secondary"],
        )
        footer.pack(pady=10)

    def login(self):
        """Handle login attempt with account lockout protection, session creation, and password expiration checks."""
        username = self.username_entry.get().strip()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter both username and password.")
            return

        # Check if account is locked
        is_locked, unlock_time = self.db.is_account_locked(username)
        if is_locked:
            minutes_left = int((unlock_time - datetime.now()).total_seconds() / 60)
            # Log account locked attempt
            self.audit_logger.log_login_failed(
                username, f"Account locked ({minutes_left} minutes remaining)"
            )
            messagebox.showerror(
                "Account Locked",
                f"Account is locked due to multiple failed login attempts.\n"
                f"Please try again in {minutes_left} minute(s).",
            )
            return

        user_id = self.db.authenticate_user(username, password)

        if user_id:
            # Check password expiration status
            password_changed_at = self.db.get_password_changed_date(user_id)
            is_expired = self.password_expiration.is_password_expired(
                password_changed_at
            )

            if is_expired:
                # Force password change - user cannot proceed until password is changed
                messagebox.showwarning(
                    "Password Expired",
                    f"Your password has expired after {SecurityConfig.PASSWORD_EXPIRATION_DAYS} days.\n"
                    "You must change your password to continue.",
                )

                # Show change password dialog with force_change=True
                dialog = ChangePasswordDialog(
                    parent=self.root,
                    username=username,
                    db_manager=self.db,
                    on_success=None,
                    force_change=True,
                )

                success = dialog.show()

                if not success:
                    # User closed dialog without changing password - abort login
                    self.audit_logger.log_login_failed(
                        username, "Refused to change expired password"
                    )
                    messagebox.showerror(
                        "Login Cancelled",
                        "Login cancelled. You must change your password to access your account.",
                    )
                    return

                # Password changed successfully, continue with login
                self.audit_logger.log_password_changed(
                    user_id, username, "Expired password changed at login"
                )
                messagebox.showinfo(
                    "Success",
                    "Password changed successfully! You can now access your account.",
                )

            else:
                # Check if password is expiring soon and show warning
                should_warn = self.password_expiration.should_show_warning(
                    password_changed_at
                )

                if should_warn:
                    days_left = self.password_expiration.days_until_expiration(
                        password_changed_at
                    )
                    warning_level = self.password_expiration.get_warning_level(
                        password_changed_at
                    )
                    warning_message = self.password_expiration.get_expiration_message(
                        password_changed_at
                    )

                    # Show warning dialog with option to change password
                    response = messagebox.askyesno(
                        f"Password Expiration {warning_level.title()}",
                        f"{warning_message}\n\n"
                        f"Would you like to change your password now?",
                        icon=(
                            "warning"
                            if warning_level in ["critical", "expired"]
                            else "info"
                        ),
                    )

                    if response:
                        # User wants to change password now
                        dialog = ChangePasswordDialog(
                            parent=self.root,
                            username=username,
                            db_manager=self.db,
                            on_success=None,
                            force_change=False,
                        )
                        dialog.show()
                        # Continue with login regardless of password change outcome

            # Check if 2FA is enabled for this user
            if self.db.is_2fa_enabled(user_id):
                # Show 2FA verification dialog
                verification_dialog = TwoFactorVerificationDialog(
                    parent=self.root,
                    username=username,
                    user_id=user_id,
                    db_manager=self.db,
                )

                # Wait for 2FA verification
                if not verification_dialog.show():
                    # 2FA verification failed or was cancelled
                    self.audit_logger.log_2fa_verification(user_id, username, False)
                    messagebox.showerror(
                        "Login Failed",
                        "Two-factor authentication verification failed or was cancelled.",
                    )
                    return

                # 2FA verification successful - continue with login
                self.audit_logger.log_2fa_verification(user_id, username, True)

            # Create session for the authenticated user
            session_token = self.session_manager.create_session(user_id)

            # Store session in database for persistence
            session_info = self.session_manager.get_session_info(session_token)
            if session_info:
                self.db.create_session(
                    user_id,
                    session_token,
                    session_info["created_at"],
                    session_info["expires_at"],
                )

            user_info = self.db.get_user_info(user_id)

            # Log successful login with 2FA info
            has_2fa = self.db.is_2fa_enabled(user_id)
            self.audit_logger.log_login_success(user_id, username, with_2fa=has_2fa)

            self.on_login_success(user_id, user_info, session_token)
        else:
            # Log failed login
            self.audit_logger.log_login_failed(username, "Invalid credentials")
            messagebox.showerror(
                "Login Failed",
                "Invalid username or password.\n"
                "Note: Account will be locked for 15 minutes after 5 failed attempts.",
            )
            self.password_entry.delete(0, tk.END)

    def show_register(self):
        """Show registration window."""
        RegisterWindow(self.root, self.db, self.on_registration_success)

    def on_registration_success(self, user_id, user_info):
        """Handle successful registration with session creation."""
        messagebox.showinfo(
            "Success",
            f"Account created successfully!\nWelcome, {user_info['full_name']}!",
        )

        # Create session for new user
        session_token = self.session_manager.create_session(user_id)

        # Store session in database
        session_info = self.session_manager.get_session_info(session_token)
        if session_info:
            self.db.create_session(
                user_id,
                session_token,
                session_info["created_at"],
                session_info["expires_at"],
            )

        self.on_login_success(user_id, user_info, session_token)


class RegisterWindow:
    """Registration window for new users."""

    def __init__(self, parent, db, on_success):
        self.parent = parent
        self.db = db
        self.audit_logger = AuditLogger(db)
        self.on_success = on_success

        # Create new window
        self.window = create_modal_dialog(
            parent, "moreStacks Banking - Register", 450, 700
        )

        self.create_widgets()

    def create_widgets(self):
        """Create registration interface widgets."""
        # Header
        header_frame = tk.Frame(self.window, bg=COLORS["primary"], height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        title = tk.Label(
            header_frame,
            text="Create Account",
            font=FONTS["title_medium"],
            bg=COLORS["primary"],
            fg=COLORS["white"],
        )
        title.pack(pady=30)

        # Main frame
        main_frame = tk.Frame(self.window, bg=COLORS["white"], padx=40, pady=30)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)

        # Full Name, Username, Password, Confirm Password, Email
        self.full_name_entry = create_labeled_entry(
            main_frame, "Full Name:", pady_top=0
        )
        self.username_entry = create_labeled_entry(main_frame, "Username:")
        self.password_entry = create_labeled_entry(main_frame, "Password:", show="●")
        self.confirm_entry = create_labeled_entry(
            main_frame, "Confirm Password:", show="●"
        )
        self.email_entry = create_labeled_entry(main_frame, "Email (optional):")

        # Buttons
        create_button(
            main_frame,
            "Create Account",
            self.register,
            color_key="accent",
            fill=tk.X,
            pady=(25, 10),
        )

        cancel_btn = tk.Button(
            main_frame,
            text="Cancel",
            font=FONTS["label"],
            bg=COLORS["white"],
            fg=COLORS["text_secondary"],
            bd=0,
            cursor="hand2",
            command=self.window.destroy,
        )
        cancel_btn.pack()

    def register(self):
        """Handle registration with password strength validation."""
        full_name = self.full_name_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        confirm = self.confirm_entry.get()
        email = self.email_entry.get().strip()

        # Validation
        if not full_name or not username or not password:
            messagebox.showerror("Error", "Please fill in all required fields.")
            return

        if len(username) < 3:
            messagebox.showerror("Error", "Username must be at least 3 characters.")
            return

        # Validate password strength
        is_valid, message = PasswordValidator.validate_password(password)
        if not is_valid:
            messagebox.showerror(
                "Weak Password",
                f"{message}\n\nPassword Requirements:\n{PasswordValidator.get_requirements_text()}",
            )
            return

        if password != confirm:
            messagebox.showerror("Error", "Passwords do not match.")
            return

        # Show password strength feedback
        strength = PasswordValidator.get_password_strength(password)
        if strength == "Weak":
            if not messagebox.askyesno(
                "Weak Password",
                "Your password is weak. We recommend choosing a stronger password.\n\n"
                "Do you want to continue anyway?",
            ):
                return

        # Create user
        user_id = self.db.create_user(username, password, full_name, email)

        if user_id:
            # Log user registration
            self.audit_logger.log_security_event(
                event_type="USER_REGISTERED",
                description=f"New user '{username}' registered successfully",
                severity="INFO",
                user_id=user_id,
                username=username,
            )

            # Create default checking account
            account_id, account_number = self.db.create_account(user_id, "Checking", 0)

            # Log account creation
            self.audit_logger.log_account_action(
                user_id=user_id,
                username=username,
                action="created",
                account_number=account_number,
                details={"account_type": "Checking", "initial_balance": 0},
            )

            user_info = self.db.get_user_info(user_id)
            self.window.destroy()
            self.on_success(user_id, user_info)
        else:
            # Log failed registration
            self.audit_logger.log_security_event(
                event_type="USER_REGISTRATION_FAILED",
                description=f"Failed registration attempt for username '{username}' (already exists)",
                severity="WARNING",
                username=username,
            )
            messagebox.showerror(
                "Error", "Username already exists. Please choose another."
            )
