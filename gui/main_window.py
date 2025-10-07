import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from models.account import create_account
from gui.gui_utils import (
    COLORS,
    FONTS,
    create_button,
    create_labeled_entry,
    create_combobox,
    create_modal_dialog,
    create_button_pair,
    setup_dark_theme,
)
from gui.charts_window import ChartsWindow
from gui.two_factor_setup_dialog import TwoFactorSetupDialog
from gui.audit_log_window import AuditLogWindow
from gui.transfer_dialog import TransferDialog
from gui.new_account_dialog import NewAccountDialog
from utils.interest_scheduler import InterestScheduler
from utils.session_manager import SessionManager
from utils.audit_logger import AuditLogger
from config import TRANSACTION_CATEGORIES, SecurityConfig
import csv


class MainBankingWindow:
    """Main banking application window with account management."""

    def __init__(self, root, user_id, user_info, db, session_token):
        self.root = root
        self.user_id = user_id
        self.user_info = user_info
        self.db = db
        self.session_token = session_token
        self.current_account = None
        self.accounts = []

        # Initialize session manager
        self.session_manager = SessionManager(
            timeout_minutes=SecurityConfig.SESSION_TIMEOUT_MINUTES,
            warning_minutes=SecurityConfig.SESSION_WARNING_MINUTES,
        )

        # Initialize audit logger
        self.audit_logger = AuditLogger(self.db)

        # Track last activity update time to throttle database updates
        self.last_activity_update = datetime.now()
        self.activity_update_interval = timedelta(seconds=5)  # Update every 5 seconds

        # Session validation state
        self.session_check_id = None
        self.warning_dialog = None
        self.is_logged_out = False

        # Setup dark theme for modern appearance
        setup_dark_theme()

        # Window setup
        self.root.title("moreStacks Banking - Dashboard")
        self.root.geometry("900x750")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS["bg_dark"])

        self.load_accounts()
        self.create_widgets()
        self.setup_activity_tracking()
        self.start_session_monitoring()

    def load_accounts(self):
        """Load user accounts from database."""
        account_data = self.db.get_user_accounts(self.user_id)
        self.accounts = []

        for acc_data in account_data:
            account = create_account(
                acc_data["account_type"],
                acc_data["account_id"],
                acc_data["account_number"],
                self.user_info["full_name"],
                acc_data["balance"],
                acc_data["interest_rate"],
                acc_data["credit_limit"],
            )
            # Load transaction history
            transactions = self.db.get_transactions(acc_data["account_id"], limit=50)
            account.transaction_history = [
                {
                    "type": t["transaction_type"],
                    "amount": t["amount"],
                    "category": t["category"],
                    "balance": t["balance_after"],
                    "time": t["timestamp"],
                }
                for t in transactions
            ]
            self.accounts.append(account)

        if self.accounts:
            self.current_account = self.accounts[0]

    def setup_activity_tracking(self):
        """Set up event bindings to track user activity."""
        # Bind mouse and keyboard events to track activity
        self.root.bind("<Motion>", self.on_user_activity)
        self.root.bind("<ButtonPress>", self.on_user_activity)
        self.root.bind("<KeyPress>", self.on_user_activity)

    def on_user_activity(self, event=None):
        """Handle user activity events and update session."""
        if self.is_logged_out:
            return

        # Throttle activity updates to avoid excessive database writes
        now = datetime.now()
        if now - self.last_activity_update >= self.activity_update_interval:
            # Update session manager
            self.session_manager.update_activity(self.session_token)

            # Update database
            session_info = self.session_manager.get_session_info(self.session_token)
            if session_info:
                self.db.update_session_activity(
                    self.session_token,
                    session_info["last_activity"],
                    session_info["expires_at"],
                )

            self.last_activity_update = now

            # Close warning dialog if it's open
            if self.warning_dialog and self.warning_dialog.winfo_exists():
                self.warning_dialog.destroy()
                self.warning_dialog = None

    def start_session_monitoring(self):
        """Start periodic session validation checks."""
        self.check_session_validity()

    def check_session_validity(self):
        """Check if session is still valid and handle expiration/warnings."""
        if self.is_logged_out:
            return

        # Check if session is still valid
        if not self.session_manager.is_session_valid(self.session_token):
            self.handle_session_expiration()
            return

        # Check if we should show a warning
        if self.session_manager.should_show_warning(self.session_token):
            if not self.warning_dialog or not self.warning_dialog.winfo_exists():
                self.show_session_warning()

        # Schedule next check (every 10 seconds)
        self.session_check_id = self.root.after(10000, self.check_session_validity)

    def show_session_warning(self):
        """Show warning dialog when session is about to expire."""
        if self.warning_dialog and self.warning_dialog.winfo_exists():
            return

        self.warning_dialog = create_modal_dialog(
            self.root, "Session Expiring Soon", 400, 200
        )

        # Main frame
        main_frame = tk.Frame(self.warning_dialog, bg=COLORS["white"], padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Warning icon and message
        warning_label = tk.Label(
            main_frame,
            text="⚠️ Your session will expire soon",
            font=FONTS["body_bold"],
            bg=COLORS["white"],
            fg=COLORS["accent_orange"],
        )
        warning_label.pack(pady=(0, 10))

        # Countdown display
        time_remaining = self.session_manager.get_time_until_expiration(
            self.session_token
        )
        time_text = self.session_manager.format_time_remaining(time_remaining)

        self.countdown_label = tk.Label(
            main_frame,
            text=f"Time remaining: {time_text}",
            font=FONTS["body"],
            bg=COLORS["white"],
            fg=COLORS["text_primary"],
        )
        self.countdown_label.pack(pady=(0, 20))

        # Update countdown every second
        self.update_countdown()

        # Buttons
        button_frame = tk.Frame(main_frame, bg=COLORS["white"])
        button_frame.pack()

        extend_btn = tk.Button(
            button_frame,
            text="Extend Session",
            font=FONTS["label"],
            bg=COLORS["accent_blue"],
            fg=COLORS["white"],
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.extend_session,
        )
        extend_btn.pack(side=tk.LEFT, padx=5)

        logout_btn = tk.Button(
            button_frame,
            text="Logout Now",
            font=FONTS["label"],
            bg=COLORS["text_secondary"],
            fg=COLORS["white"],
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.logout,
        )
        logout_btn.pack(side=tk.LEFT, padx=5)

    def update_countdown(self):
        """Update the countdown display in the warning dialog."""
        if not self.warning_dialog or not self.warning_dialog.winfo_exists():
            return

        time_remaining = self.session_manager.get_time_until_expiration(
            self.session_token
        )

        if time_remaining <= 0:
            self.handle_session_expiration()
            return

        time_text = self.session_manager.format_time_remaining(time_remaining)
        self.countdown_label.config(text=f"Time remaining: {time_text}")

        # Schedule next update in 1 second
        self.root.after(1000, self.update_countdown)

    def extend_session(self):
        """Extend the current session."""
        self.session_manager.extend_session(self.session_token)

        # Update database
        session_info = self.session_manager.get_session_info(self.session_token)
        if session_info:
            self.db.update_session_activity(
                self.session_token,
                session_info["last_activity"],
                session_info["expires_at"],
            )

        # Close warning dialog
        if self.warning_dialog and self.warning_dialog.winfo_exists():
            self.warning_dialog.destroy()
            self.warning_dialog = None

        messagebox.showinfo("Session Extended", "Your session has been extended.")

    def handle_session_expiration(self):
        """Handle session expiration by logging out the user."""
        if self.is_logged_out:
            return

        self.is_logged_out = True

        # Cancel session monitoring
        if self.session_check_id:
            self.root.after_cancel(self.session_check_id)

        # Close warning dialog if open
        if self.warning_dialog and self.warning_dialog.winfo_exists():
            self.warning_dialog.destroy()

        # Clean up session
        self.session_manager.destroy_session(self.session_token)
        self.db.delete_session(self.session_token)

        # Show expiration message
        messagebox.showwarning(
            "Session Expired",
            "Your session has expired due to inactivity.\nPlease log in again.",
        )

        # Logout
        self.root.quit()

    def create_widgets(self):
        """Create main interface widgets with dark theme."""
        # Header
        header_frame = tk.Frame(self.root, bg=COLORS["bg_medium"], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Left side - Logo
        logo_label = tk.Label(
            header_frame,
            text="moreStacks",
            font=FONTS["title_medium"],
            bg=COLORS["bg_medium"],
            fg=COLORS["accent_blue"],
        )
        logo_label.pack(side=tk.LEFT, padx=20, pady=20)

        # Right side - User info
        user_frame = tk.Frame(header_frame, bg=COLORS["bg_medium"])
        user_frame.pack(side=tk.RIGHT, padx=20)

        welcome_label = tk.Label(
            user_frame,
            text=f"Welcome, {self.user_info['full_name']}",
            font=FONTS["body"],
            bg=COLORS["bg_medium"],
            fg=COLORS["text_primary"],
        )
        welcome_label.pack(anchor=tk.E)

        logout_btn = tk.Button(
            user_frame,
            text="Logout",
            font=FONTS["tiny"],
            bg=COLORS["accent_red"],
            fg=COLORS["text_bright"],
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.logout,
        )
        logout_btn.pack(anchor=tk.E, pady=(5, 0))

        # Analytics button
        analytics_btn = tk.Button(
            user_frame,
            text="📊 Analytics",
            font=FONTS["tiny"],
            bg=COLORS["accent_green"],
            fg=COLORS["bg_dark"],
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.show_analytics,
        )
        analytics_btn.pack(anchor=tk.E, pady=(5, 0))

        # 2FA Security Settings button
        security_btn = tk.Button(
            user_frame,
            text="🔐 Security",
            font=FONTS["tiny"],
            bg=COLORS["accent_purple"] if "accent_purple" in COLORS else "#9b59b6",
            fg=COLORS["text_bright"],
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.show_security_settings,
        )
        security_btn.pack(anchor=tk.E, pady=(5, 0))

        # Main content area
        content_frame = tk.Frame(self.root, bg=COLORS["bg_dark"])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left panel - Account selection and info
        left_panel = tk.Frame(content_frame, bg=COLORS["bg_card"], width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        self.create_left_panel(left_panel)

        # Right panel - Transactions
        right_panel = tk.Frame(content_frame, bg=COLORS["bg_card"])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_right_panel(right_panel)

    def create_left_panel(self, parent):
        """Create left panel with account selection and operations."""
        # Account selection
        account_label = tk.Label(
            parent,
            text="My Accounts",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_bright"],
        )
        account_label.pack(padx=15, pady=(15, 10), anchor=tk.W)

        # Account dropdown
        self.account_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        self.account_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        account_names = [
            f"{acc.get_account_type()} - {acc.account_number[-4:]}"
            for acc in self.accounts
        ]

        self.account_var, self.account_dropdown = create_combobox(
            self.account_frame,
            account_names,
            default=account_names[0] if account_names else None,
            fill=tk.X,
        )
        self.account_dropdown.bind("<<ComboboxSelected>>", self.on_account_change)

        # Add new account button
        create_button(
            parent,
            "➕ New Account",
            self.create_new_account,
            color_key="blue",
            font_key="small",
            fill=tk.X,
            padx=15,
            pady=(0, 5),
        )

        # Delete account button
        create_button(
            parent,
            "🗑 Delete Account",
            self.delete_current_account,
            color_key="red",
            font_key="small",
            fill=tk.X,
            padx=15,
            pady=(0, 15),
        )

        # Balance display
        balance_frame = tk.Frame(
            parent,
            bg=COLORS["bg_light"],
            bd=2,
            relief=tk.SOLID,
            highlightbackground=COLORS["accent_blue"],
            highlightthickness=1,
        )
        balance_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        balance_title = tk.Label(
            balance_frame,
            text="Current Balance",
            font=FONTS["small"],
            bg=COLORS["bg_light"],
            fg=COLORS["text_secondary"],
        )
        balance_title.pack(pady=(10, 0))

        self.balance_label = tk.Label(
            balance_frame,
            text="$0.00",
            font=("Segoe UI", 32, "bold"),
            bg=COLORS["bg_light"],
            fg=COLORS["accent_green"],
        )
        self.balance_label.pack(pady=(5, 10))

        # Account type info
        self.account_type_label = tk.Label(
            parent,
            text="",
            font=FONTS["tiny"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
        )
        self.account_type_label.pack(padx=15, pady=(0, 10))

        # Transaction form
        transaction_title = tk.Label(
            parent,
            text="New Transaction",
            font=FONTS["body_bold"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_bright"],
        )
        transaction_title.pack(padx=15, pady=(15, 10), anchor=tk.W)

        # Amount entry
        self.amount_entry = create_labeled_entry(parent, "Amount ($):", pady_top=5)
        self.amount_entry.master.pack(padx=15)

        # Category dropdown
        category_label = tk.Label(
            parent,
            text="Category:",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_primary"],
        )
        category_label.pack(padx=15, pady=(10, 2), anchor=tk.W)

        self.category_var, _ = create_combobox(
            parent, TRANSACTION_CATEGORIES, default="Uncategorized", fill=tk.X, padx=15
        )

        # Buttons
        button_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        button_frame.pack(fill=tk.X, padx=15, pady=15)

        create_button(
            button_frame,
            "💰 Deposit",
            self.deposit_money,
            color_key="green",
            font_key="label",
            fill=tk.X,
            pady=(0, 5),
        )

        create_button(
            button_frame,
            "💸 Withdraw",
            self.withdraw_money,
            color_key="orange",
            font_key="label",
            fill=tk.X,
            pady=(0, 5),
        )

        create_button(
            button_frame,
            "💳 Transfer",
            self.transfer_money,
            color_key="orange",
            font_key="label",
            fill=tk.X,
            pady=(0, 5),
        )

        # Apply Interest button (only for Savings accounts)
        self.interest_button = create_button(
            button_frame,
            "💵 Apply Interest",
            self.apply_interest_to_account,
            color_key="green",
            font_key="label",
            fill=tk.X,
            pady=(0, 5),
        )
        self.interest_button.pack_forget()  # Hide by default

        self.update_account_display()

    def create_right_panel(self, parent):
        """Create right panel with transaction history."""
        # Header with export button
        header_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        history_title = tk.Label(
            header_frame,
            text="Transaction History",
            font=FONTS["subheading"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_bright"],
        )
        history_title.pack(side=tk.LEFT)

        export_btn = tk.Button(
            header_frame,
            text="📥 Export CSV",
            font=FONTS["tiny"],
            bg=COLORS["accent_blue"],
            fg=COLORS["bg_dark"],
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.export_transactions,
        )
        export_btn.pack(side=tk.RIGHT)

        # Filter frame
        filter_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        filter_label = tk.Label(
            filter_frame,
            text="Filter by:",
            font=FONTS["small"],
            bg=COLORS["bg_card"],
            fg=COLORS["text_secondary"],
        )
        filter_label.pack(side=tk.LEFT, padx=(0, 10))

        filter_options = ["All"] + TRANSACTION_CATEGORIES
        self.filter_var, filter_dropdown = create_combobox(
            filter_frame, filter_options, default="All", width=15, side=tk.LEFT
        )
        filter_dropdown.bind(
            "<<ComboboxSelected>>", lambda e: self.update_transaction_history()
        )

        # Transaction list with scrollbar
        list_frame = tk.Frame(parent, bg=COLORS["bg_card"])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text = tk.Text(
            list_frame,
            font=FONTS["monospace"],
            bg=COLORS["bg_dark"],
            fg=COLORS["text_primary"],
            insertbackground=COLORS["accent_blue"],
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["focus"],
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,
            wrap=tk.WORD,
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_text.yview)

        self.update_transaction_history()

    def on_account_change(self, event=None):
        """Handle account selection change."""
        selected_index = self.account_var.get()
        for i, acc in enumerate(self.accounts):
            account_name = f"{acc.get_account_type()} - {acc.account_number[-4:]}"
            if account_name == selected_index:
                self.current_account = acc
                break

        # Show/hide interest button based on account type
        if hasattr(self, "interest_button"):
            if (
                self.current_account
                and self.current_account.get_account_type() == "Savings"
            ):
                self.interest_button.pack(fill=tk.X, pady=(0, 5))
            else:
                self.interest_button.pack_forget()

        self.update_account_display()
        self.update_transaction_history()

    def update_account_display(self):
        """Update balance and account info display."""
        if not self.current_account:
            return

        self.balance_label.config(text=self.current_account.get_balance_formatted())

        # Update account type info
        info_text = f"Account: {self.current_account.account_number}\n"
        info_text += f"Type: {self.current_account.get_account_type()}"

        if hasattr(self.current_account, "interest_rate"):
            info_text += f"\nInterest: {self.current_account.interest_rate*100:.2f}%"

            # For Savings accounts, show interest schedule info
            if self.current_account.get_account_type() == "Savings":
                # Get last interest date from database
                account_data = self.db.get_account(self.current_account.account_id)
                last_interest = (
                    account_data.get("last_interest_date") if account_data else None
                )

                # Check if interest should be applied
                if InterestScheduler.should_apply_interest(last_interest):
                    days_since = InterestScheduler.calculate_days_since_last_interest(
                        last_interest
                    )
                    if days_since == float("inf"):
                        info_text += f"\n⚠️  Interest due (never applied)"
                    else:
                        info_text += f"\n⚠️  Interest due ({days_since} days overdue)"

                    # Calculate and show pending interest
                    pending = InterestScheduler.calculate_interest_amount(
                        self.current_account.get_balance(),
                        self.current_account.interest_rate,
                        min(days_since, 30) if days_since != float("inf") else 30,
                    )
                    if pending > 0:
                        info_text += f"\nPending Interest: ${pending:.2f}"
                else:
                    # Show next interest date
                    next_date = InterestScheduler.format_next_interest_date(
                        last_interest
                    )
                    days_until = InterestScheduler.get_days_until_interest(
                        last_interest
                    )
                    info_text += f"\nNext Interest: {next_date} ({days_until} days)"

        if hasattr(self.current_account, "credit_limit"):
            info_text += f"\nCredit Limit: ${self.current_account.credit_limit:.2f}"
            info_text += (
                f"\nAvailable: ${self.current_account.get_available_credit():.2f}"
            )

        self.account_type_label.config(text=info_text)

    def update_transaction_history(self):
        """Update transaction history display."""
        if not self.current_account:
            return

        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)

        filter_category = self.filter_var.get()
        transactions = self.current_account.transaction_history

        # Filter transactions
        if filter_category != "All":
            transactions = [
                t for t in transactions if t.get("category") == filter_category
            ]

        if transactions:
            # Header
            header = f"{'Date & Time':<20} {'Type':<15} {'Category':<18} {'Amount':>10} {'Balance':>12}\n"
            self.history_text.insert(tk.END, header)
            self.history_text.insert(tk.END, "-" * 85 + "\n")

            for trans in transactions:
                category = trans.get("category", "N/A") or "N/A"
                line = f"{trans['time']:<20} {trans['type']:<15} {category:<18} ${trans['amount']:>9.2f} ${trans['balance']:>11.2f}\n"
                self.history_text.insert(tk.END, line)
        else:
            self.history_text.insert(tk.END, "No transactions found.")

        self.history_text.config(state=tk.DISABLED)

    def deposit_money(self):
        """Handle deposit transaction."""
        if not self.current_account:
            messagebox.showerror("Error", "No account selected.")
            return

        try:
            amount = float(self.amount_entry.get())
            category = self.category_var.get()

            success, message = self.current_account.deposit(amount, category)

            if success:
                # Update database
                self.db.update_balance(
                    self.current_account.account_id, self.current_account.balance
                )
                self.db.add_transaction(
                    self.current_account.account_id,
                    "Deposit",
                    amount,
                    f"Deposit - {category}",
                    self.current_account.balance,
                    category,
                )

                # Log the transaction
                self.audit_logger.log_transaction(
                    user_id=self.user_id,
                    transaction_type="deposit",
                    amount=amount,
                    account_id=self.current_account.account_id,
                    details={
                        "category": category,
                        "balance_after": self.current_account.balance,
                    },
                )

                messagebox.showinfo("Success", message)
                self.amount_entry.delete(0, tk.END)
                self.update_account_display()
                self.update_transaction_history()
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")

    def withdraw_money(self):
        """Handle withdrawal transaction."""
        if not self.current_account:
            messagebox.showerror("Error", "No account selected.")
            return

        try:
            amount = float(self.amount_entry.get())
            category = self.category_var.get()

            success, message = self.current_account.withdraw(amount, category)

            if success:
                # Update database
                self.db.update_balance(
                    self.current_account.account_id, self.current_account.balance
                )
                self.db.add_transaction(
                    self.current_account.account_id,
                    "Withdrawal",
                    amount,
                    f"Withdrawal - {category}",
                    self.current_account.balance,
                    category,
                )

                # Log the transaction
                self.audit_logger.log_transaction(
                    user_id=self.user_id,
                    transaction_type="withdrawal",
                    amount=amount,
                    account_id=self.current_account.account_id,
                    details={
                        "category": category,
                        "balance_after": self.current_account.balance,
                    },
                )

                messagebox.showinfo("Success", message)
                self.amount_entry.delete(0, tk.END)
                self.update_account_display()
                self.update_transaction_history()
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")

    def transfer_money(self):
        """Handle transfer between accounts."""
        if len(self.accounts) < 2:
            messagebox.showinfo(
                "Info", "You need at least 2 accounts to make a transfer."
            )
            return

        TransferDialog(
            self.root,
            self.current_account,
            self.accounts,
            self.db,
            self.on_transfer_complete,
            self.user_id,
            self.audit_logger,
        )

    def apply_interest_to_account(self):
        """Apply monthly interest to the current savings account."""
        if (
            not self.current_account
            or self.current_account.get_account_type() != "Savings"
        ):
            return

        # Get account data from database
        account_data = self.db.get_account(self.current_account.account_id)
        last_interest = account_data.get("last_interest_date") if account_data else None

        # Calculate days since last interest
        if last_interest:
            days_since = InterestScheduler.calculate_days_since_last_interest(
                last_interest
            )
        else:
            days_since = 30  # Default to 30 days if never applied

        # Apply interest
        success, message = self.current_account.apply_interest(days=min(days_since, 30))

        if success:
            # Update balance in database
            self.db.update_balance(
                self.current_account.account_id, self.current_account.get_balance()
            )

            # Update last interest date
            self.db.update_last_interest_date(
                self.current_account.account_id, datetime.now().isoformat()
            )

            # Reload account to update transaction history
            self.on_transfer_complete()

            messagebox.showinfo("Interest Applied", message)
        else:
            messagebox.showwarning("No Interest", message)

    def on_transfer_complete(self):
        """Callback after successful transfer."""
        # Store current account ID
        current_acc_id = (
            self.current_account.account_id if self.current_account else None
        )

        # Reload all accounts from database
        self.load_accounts()

        # Find and set the current account again
        if current_acc_id:
            for acc in self.accounts:
                if acc.account_id == current_acc_id:
                    self.current_account = acc
                    break

        self.update_account_display()
        self.update_transaction_history()

    def create_new_account(self):
        """Show dialog to create new account."""
        NewAccountDialog(self.root, self.user_id, self.db, self.on_new_account_created)

    def on_new_account_created(self):
        """Callback after new account creation."""
        # Reload accounts from database
        self.load_accounts()

        # Update dropdown with new account list
        account_names = [
            f"{acc.get_account_type()} - {acc.account_number[-4:]}"
            for acc in self.accounts
        ]
        self.account_dropdown["values"] = account_names

        # Select the newly created account (last in list)
        if account_names:
            self.account_var.set(account_names[-1])
            self.current_account = self.accounts[-1]

        # Update displays
        self.update_account_display()
        self.update_transaction_history()

    def delete_current_account(self):
        """Delete the currently selected account."""
        if not self.current_account:
            messagebox.showwarning("Warning", "No account selected.")
            return

        # Confirm deletion
        account_info = f"{self.current_account.get_account_type()} - {self.current_account.account_number}"
        balance = self.current_account.get_balance_formatted()

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete this account?\n\n"
            f"Account: {account_info}\n"
            f"Balance: {balance}\n\n"
            f"This action cannot be undone.\n"
            f"All transaction history will be permanently deleted.",
            icon="warning",
        )

        if not confirm:
            return

        # Check if this is the last account
        if len(self.accounts) == 1:
            messagebox.showerror(
                "Cannot Delete",
                "You cannot delete your last account.\n"
                "Create a new account first before deleting this one.",
            )
            return

        # Perform deletion
        success, message = self.db.delete_account(self.current_account.account_id)

        if success:
            messagebox.showinfo("Success", "Account deleted successfully.")

            # Reload accounts and select the first one
            self.load_accounts()

            if self.accounts:
                account_names = [
                    f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                    for acc in self.accounts
                ]
                self.account_dropdown["values"] = account_names
                self.account_var.set(account_names[0])
                self.current_account = self.accounts[0]
                self.update_account_display()
                self.update_transaction_history()
            else:
                # No accounts left (shouldn't happen due to check above)
                self.current_account = None
                self.update_account_display()
        else:
            messagebox.showerror("Error", f"Failed to delete account:\n{message}")

    def export_transactions(self):
        """Export transactions to CSV file."""
        if not self.current_account or not self.current_account.transaction_history:
            messagebox.showinfo("Info", "No transactions to export.")
            return

        filename = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialfile=f"transactions_{self.current_account.account_number}_{datetime.now().strftime('%Y%m%d')}.csv",
        )

        if filename:
            try:
                with open(filename, "w", newline="") as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(
                        ["Date & Time", "Type", "Category", "Amount", "Balance After"]
                    )

                    for trans in self.current_account.transaction_history:
                        writer.writerow(
                            [
                                trans["time"],
                                trans["type"],
                                trans.get("category", "N/A"),
                                f"${trans['amount']:.2f}",
                                f"${trans['balance']:.2f}",
                            ]
                        )

                messagebox.showinfo("Success", f"Transactions exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def logout(self):
        """Logout and return to login screen with session cleanup."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.is_logged_out = True

            # Cancel session monitoring
            if self.session_check_id:
                self.root.after_cancel(self.session_check_id)

            # Clean up session
            self.session_manager.destroy_session(self.session_token)
            self.db.delete_session(self.session_token)

            self.root.quit()

    def _open_audit_log(self, parent_dialog):
        """Open the audit log viewer window."""
        # Log the audit access event
        self.audit_logger.log_audit_access(
            user_id=self.user_id,
            action="viewed",
            details={"source": "security_settings"},
        )

        # Close the security settings dialog
        parent_dialog.destroy()

        # Open the audit log window
        AuditLogWindow(
            parent=self.root,
            user_id=self.user_id,
            db_manager=self.db,
            audit_logger=self.audit_logger,
        )

    def show_analytics(self):
        """Open analytics dashboard window."""
        ChartsWindow(self.root, self.user_id, self.db, self.accounts)

    def show_security_settings(self):
        """Show security settings dialog with 2FA management and audit log access."""
        dialog = tk.Toplevel(self.root)
        dialog.title("Security Settings")
        dialog.geometry("500x600")
        dialog.resizable(False, False)
        dialog.configure(bg="#2b2b2b")

        # Make dialog modal
        dialog.transient(self.root)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = (
            self.root.winfo_y()
            + (self.root.winfo_height() - dialog.winfo_height()) // 2
        )
        dialog.geometry(f"+{x}+{y}")

        # Main frame
        main_frame = tk.Frame(dialog, bg="#2b2b2b", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        title_label = tk.Label(
            main_frame,
            text="🔐 Security Settings",
            font=("Arial", 18, "bold"),
            bg="#2b2b2b",
            fg="#4ecdc4",
        )
        title_label.pack(pady=(0, 20))

        # 2FA Section
        twofa_frame = tk.Frame(main_frame, bg="#333333", padx=20, pady=20)
        twofa_frame.pack(fill=tk.X, pady=(0, 10))

        twofa_title = tk.Label(
            twofa_frame,
            text="Two-Factor Authentication (2FA)",
            font=("Arial", 12, "bold"),
            bg="#333333",
            fg="#ffffff",
        )
        twofa_title.pack(anchor=tk.W, pady=(0, 10))

        # Check current 2FA status
        is_enabled = self.db.is_2fa_enabled(self.user_id)
        status = self.db.get_2fa_status(self.user_id)

        # Status display
        status_frame = tk.Frame(twofa_frame, bg="#333333")
        status_frame.pack(fill=tk.X, pady=(0, 15))

        status_label = tk.Label(
            status_frame,
            text=f"Status: {'✓ Enabled' if is_enabled else '✗ Disabled'}",
            font=("Arial", 10),
            bg="#333333",
            fg="#95e1d3" if is_enabled else "#999999",
        )
        status_label.pack(anchor=tk.W)

        if is_enabled and status:
            backup_codes_remaining = len(status.get("backup_codes", []))
            backup_label = tk.Label(
                status_frame,
                text=f"Backup codes remaining: {backup_codes_remaining}",
                font=("Arial", 9),
                bg="#333333",
                fg="#cccccc",
            )
            backup_label.pack(anchor=tk.W, pady=(5, 0))

            if status.get("last_used"):
                last_used_label = tk.Label(
                    status_frame,
                    text=f"Last used: {status['last_used']}",
                    font=("Arial", 9),
                    bg="#333333",
                    fg="#cccccc",
                )
                last_used_label.pack(anchor=tk.W, pady=(2, 0))

        # Description
        desc_text = (
            "Two-factor authentication adds an extra layer of security to your account.\n"
            "You'll need both your password and a code from your authenticator app to login."
        )
        desc_label = tk.Label(
            twofa_frame,
            text=desc_text,
            font=("Arial", 9),
            bg="#333333",
            fg="#cccccc",
            wraplength=400,
            justify=tk.LEFT,
        )
        desc_label.pack(anchor=tk.W, pady=(0, 15))

        # Buttons
        button_frame = tk.Frame(twofa_frame, bg="#333333")
        button_frame.pack(fill=tk.X)

        if not is_enabled:
            # Enable 2FA button
            enable_btn = tk.Button(
                button_frame,
                text="Enable 2FA",
                font=("Arial", 10, "bold"),
                bg="#4ecdc4",
                fg="#2b2b2b",
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: self._enable_2fa(dialog),
            )
            enable_btn.pack(side=tk.LEFT)
        else:
            # Disable 2FA button
            disable_btn = tk.Button(
                button_frame,
                text="Disable 2FA",
                font=("Arial", 10),
                bg="#ff6b6b",
                fg="#ffffff",
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: self._disable_2fa(dialog),
            )
            disable_btn.pack(side=tk.LEFT, padx=(0, 10))

            # Regenerate backup codes button
            regen_btn = tk.Button(
                button_frame,
                text="Regenerate Backup Codes",
                font=("Arial", 10),
                bg="#ffa500",
                fg="#2b2b2b",
                bd=0,
                padx=20,
                pady=10,
                cursor="hand2",
                command=lambda: self._regenerate_backup_codes(dialog),
            )
            regen_btn.pack(side=tk.LEFT)

        # Audit Log Section
        audit_frame = tk.Frame(main_frame, bg="#333333", padx=20, pady=20)
        audit_frame.pack(fill=tk.X, pady=(10, 0))

        audit_title = tk.Label(
            audit_frame,
            text="Security Audit Log",
            font=("Arial", 12, "bold"),
            bg="#333333",
            fg="#ffffff",
        )
        audit_title.pack(anchor=tk.W, pady=(0, 10))

        audit_desc_text = (
            "View comprehensive security event logs including login attempts,\n"
            "password changes, 2FA activities, and account modifications."
        )
        audit_desc_label = tk.Label(
            audit_frame,
            text=audit_desc_text,
            font=("Arial", 9),
            bg="#333333",
            fg="#cccccc",
            wraplength=400,
            justify=tk.LEFT,
        )
        audit_desc_label.pack(anchor=tk.W, pady=(0, 15))

        # View Audit Log button
        audit_btn = tk.Button(
            audit_frame,
            text="📋 View Audit Log",
            font=("Arial", 10, "bold"),
            bg="#4ecdc4",
            fg="#2b2b2b",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=lambda: self._open_audit_log(dialog),
        )
        audit_btn.pack(anchor=tk.W)

        # Close button
        close_btn = tk.Button(
            main_frame,
            text="Close",
            font=("Arial", 10),
            bg="#666666",
            fg="#ffffff",
            bd=0,
            padx=30,
            pady=10,
            cursor="hand2",
            command=dialog.destroy,
        )
        close_btn.pack(pady=(20, 0))

    def _enable_2fa(self, parent_dialog):
        """Launch 2FA setup wizard."""
        parent_dialog.destroy()  # Close settings dialog

        setup_dialog = TwoFactorSetupDialog(
            parent=self.root,
            username=self.user_info["username"],
            user_id=self.user_id,
            db_manager=self.db,
        )

        if setup_dialog.show():
            messagebox.showinfo(
                "Success",
                "Two-factor authentication has been enabled successfully!\n\n"
                "Make sure you've saved your backup codes in a safe place.",
                parent=self.root,
            )

    def _disable_2fa(self, parent_dialog):
        """Disable 2FA after confirmation."""
        response = messagebox.askyesno(
            "Disable Two-Factor Authentication",
            "Are you sure you want to disable two-factor authentication?\n\n"
            "This will make your account less secure.\n\n"
            "Your backup codes will be deleted.",
            icon="warning",
            parent=parent_dialog,
        )

        if response:
            success, message = self.db.disable_2fa(self.user_id)

            if success:
                messagebox.showinfo(
                    "Success",
                    "Two-factor authentication has been disabled.",
                    parent=parent_dialog,
                )
                parent_dialog.destroy()
                # Reopen settings to show updated status
                self.show_security_settings()
            else:
                messagebox.showerror(
                    "Error", f"Failed to disable 2FA: {message}", parent=parent_dialog
                )

    def _regenerate_backup_codes(self, parent_dialog):
        """Regenerate backup codes."""
        response = messagebox.askyesno(
            "Regenerate Backup Codes",
            "This will replace all your existing backup codes with new ones.\n\n"
            "Any unused codes will be invalidated.\n\n"
            "Continue?",
            icon="warning",
            parent=parent_dialog,
        )

        if response:
            from utils.totp_manager import TOTPManager

            totp_manager = TOTPManager()

            # Generate new backup codes
            new_codes = totp_manager.generate_backup_codes()

            # Update in database
            success, message = self.db.regenerate_backup_codes(self.user_id, new_codes)

            if success:
                # Show new backup codes
                codes_window = tk.Toplevel(parent_dialog)
                codes_window.title("New Backup Codes")
                codes_window.geometry("400x500")
                codes_window.configure(bg="#2b2b2b")
                codes_window.transient(parent_dialog)
                codes_window.grab_set()

                # Center window
                codes_window.update_idletasks()
                x = (
                    parent_dialog.winfo_x()
                    + (parent_dialog.winfo_width() - codes_window.winfo_width()) // 2
                )
                y = (
                    parent_dialog.winfo_y()
                    + (parent_dialog.winfo_height() - codes_window.winfo_height()) // 2
                )
                codes_window.geometry(f"+{x}+{y}")

                frame = tk.Frame(codes_window, bg="#2b2b2b", padx=30, pady=20)
                frame.pack(fill=tk.BOTH, expand=True)

                tk.Label(
                    frame,
                    text="🔑 New Backup Codes",
                    font=("Arial", 16, "bold"),
                    bg="#2b2b2b",
                    fg="#4ecdc4",
                ).pack(pady=(0, 10))

                tk.Label(
                    frame,
                    text="Save these codes in a safe place.\nEach code can only be used once.",
                    font=("Arial", 10),
                    bg="#2b2b2b",
                    fg="#cccccc",
                    justify=tk.CENTER,
                ).pack(pady=(0, 15))

                # Codes display
                codes_text = tk.Text(
                    frame,
                    height=12,
                    width=15,
                    font=("Courier", 12),
                    bg="#333333",
                    fg="#ffffff",
                    bd=0,
                    padx=10,
                    pady=10,
                )
                codes_text.pack(pady=(0, 15))
                codes_text.insert("1.0", "\n".join(new_codes))
                codes_text.config(state=tk.DISABLED)

                # Copy button
                def copy_codes():
                    self.root.clipboard_clear()
                    self.root.clipboard_append("\n".join(new_codes))
                    messagebox.showinfo(
                        "Copied",
                        "Backup codes copied to clipboard!",
                        parent=codes_window,
                    )

                tk.Button(
                    frame,
                    text="📋 Copy to Clipboard",
                    font=("Arial", 10),
                    bg="#4ecdc4",
                    fg="#2b2b2b",
                    bd=0,
                    padx=20,
                    pady=8,
                    cursor="hand2",
                    command=copy_codes,
                ).pack(pady=(0, 10))

                tk.Button(
                    frame,
                    text="Close",
                    font=("Arial", 10),
                    bg="#666666",
                    fg="#ffffff",
                    bd=0,
                    padx=30,
                    pady=8,
                    cursor="hand2",
                    command=codes_window.destroy,
                ).pack()
            else:
                messagebox.showerror(
                    "Error",
                    f"Failed to regenerate backup codes: {message}",
                    parent=parent_dialog,
                )
