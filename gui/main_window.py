import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from models.account import create_account
from gui.gui_utils import COLORS, FONTS, create_button, create_labeled_entry, create_combobox, create_modal_dialog, create_button_pair, setup_dark_theme
from gui.charts_window import ChartsWindow
import csv


class MainBankingWindow:
    """Main banking application window with account management."""

    TRANSACTION_CATEGORIES = [
        "Uncategorized",
        "Food & Dining",
        "Shopping",
        "Transportation",
        "Bills & Utilities",
        "Entertainment",
        "Healthcare",
        "Travel",
        "Personal",
        "Transfer",
        "Other"
    ]

    def __init__(self, root, user_id, user_info, db):
        self.root = root
        self.user_id = user_id
        self.user_info = user_info
        self.db = db
        self.current_account = None
        self.accounts = []

        # Setup dark theme for modern appearance
        setup_dark_theme()

        # Window setup
        self.root.title("moreStacks Banking - Dashboard")
        self.root.geometry("900x750")
        self.root.resizable(False, False)
        self.root.configure(bg=COLORS['bg_dark'])

        self.load_accounts()
        self.create_widgets()

    def load_accounts(self):
        """Load user accounts from database."""
        account_data = self.db.get_user_accounts(self.user_id)
        self.accounts = []

        for acc_data in account_data:
            account = create_account(
                acc_data['account_type'],
                acc_data['account_id'],
                acc_data['account_number'],
                self.user_info['full_name'],
                acc_data['balance'],
                acc_data['interest_rate'],
                acc_data['credit_limit']
            )
            # Load transaction history
            transactions = self.db.get_transactions(acc_data['account_id'], limit=50)
            account.transaction_history = [
                {
                    'type': t['transaction_type'],
                    'amount': t['amount'],
                    'category': t['category'],
                    'balance': t['balance_after'],
                    'time': t['timestamp']
                }
                for t in transactions
            ]
            self.accounts.append(account)

        if self.accounts:
            self.current_account = self.accounts[0]

    def create_widgets(self):
        """Create main interface widgets with dark theme."""
        # Header
        header_frame = tk.Frame(self.root, bg=COLORS['bg_medium'], height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Left side - Logo
        logo_label = tk.Label(
            header_frame,
            text="moreStacks",
            font=FONTS['title_medium'],
            bg=COLORS['bg_medium'],
            fg=COLORS['accent_blue']
        )
        logo_label.pack(side=tk.LEFT, padx=20, pady=20)

        # Right side - User info
        user_frame = tk.Frame(header_frame, bg=COLORS['bg_medium'])
        user_frame.pack(side=tk.RIGHT, padx=20)

        welcome_label = tk.Label(
            user_frame,
            text=f"Welcome, {self.user_info['full_name']}",
            font=FONTS['body'],
            bg=COLORS['bg_medium'],
            fg=COLORS['text_primary']
        )
        welcome_label.pack(anchor=tk.E)

        logout_btn = tk.Button(
            user_frame,
            text="Logout",
            font=FONTS['tiny'],
            bg=COLORS['accent_red'],
            fg=COLORS['text_bright'],
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.logout
        )
        logout_btn.pack(anchor=tk.E, pady=(5, 0))

        # Analytics button
        analytics_btn = tk.Button(
            user_frame,
            text="📊 Analytics",
            font=FONTS['tiny'],
            bg=COLORS['accent_green'],
            fg=COLORS['bg_dark'],
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.show_analytics
        )
        analytics_btn.pack(anchor=tk.E, pady=(5, 0))

        # Main content area
        content_frame = tk.Frame(self.root, bg=COLORS['bg_dark'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left panel - Account selection and info
        left_panel = tk.Frame(content_frame, bg=COLORS['bg_card'], width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        self.create_left_panel(left_panel)

        # Right panel - Transactions
        right_panel = tk.Frame(content_frame, bg=COLORS['bg_card'])
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_right_panel(right_panel)

    def create_left_panel(self, parent):
        """Create left panel with account selection and operations."""
        # Account selection
        account_label = tk.Label(
            parent,
            text="My Accounts",
            font=FONTS['subheading'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_bright']
        )
        account_label.pack(padx=15, pady=(15, 10), anchor=tk.W)

        # Account dropdown
        self.account_frame = tk.Frame(parent, bg=COLORS['bg_card'])
        self.account_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        account_names = [f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                        for acc in self.accounts]

        self.account_var, self.account_dropdown = create_combobox(
            self.account_frame,
            account_names,
            default=account_names[0] if account_names else None,
            fill=tk.X
        )
        self.account_dropdown.bind("<<ComboboxSelected>>", self.on_account_change)

        # Add new account button
        create_button(
            parent,
            "➕ New Account",
            self.create_new_account,
            color_key='blue',
            font_key='small',
            fill=tk.X,
            padx=15,
            pady=(0, 5)
        )

        # Delete account button
        create_button(
            parent,
            "🗑 Delete Account",
            self.delete_current_account,
            color_key='red',
            font_key='small',
            fill=tk.X,
            padx=15,
            pady=(0, 15)
        )

        # Balance display
        balance_frame = tk.Frame(parent, bg=COLORS['bg_light'], bd=2, relief=tk.SOLID, highlightbackground=COLORS['accent_blue'], highlightthickness=1)
        balance_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        balance_title = tk.Label(
            balance_frame,
            text="Current Balance",
            font=FONTS['small'],
            bg=COLORS['bg_light'],
            fg=COLORS['text_secondary']
        )
        balance_title.pack(pady=(10, 0))

        self.balance_label = tk.Label(
            balance_frame,
            text="$0.00",
            font=('Segoe UI', 32, 'bold'),
            bg=COLORS['bg_light'],
            fg=COLORS['accent_green']
        )
        self.balance_label.pack(pady=(5, 10))

        # Account type info
        self.account_type_label = tk.Label(
            parent,
            text="",
            font=FONTS['tiny'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_secondary']
        )
        self.account_type_label.pack(padx=15, pady=(0, 10))

        # Transaction form
        transaction_title = tk.Label(
            parent,
            text="New Transaction",
            font=FONTS['body_bold'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_bright']
        )
        transaction_title.pack(padx=15, pady=(15, 10), anchor=tk.W)

        # Amount entry
        self.amount_entry = create_labeled_entry(parent, "Amount ($):", pady_top=5)
        self.amount_entry.master.pack(padx=15)

        # Category dropdown
        category_label = tk.Label(
            parent,
            text="Category:",
            font=FONTS['small'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_primary']
        )
        category_label.pack(padx=15, pady=(10, 2), anchor=tk.W)

        self.category_var, _ = create_combobox(
            parent,
            self.TRANSACTION_CATEGORIES,
            default="Uncategorized",
            fill=tk.X,
            padx=15
        )

        # Buttons
        button_frame = tk.Frame(parent, bg=COLORS['bg_card'])
        button_frame.pack(fill=tk.X, padx=15, pady=15)

        create_button(
            button_frame,
            "💰 Deposit",
            self.deposit_money,
            color_key='green',
            font_key='label',
            fill=tk.X,
            pady=(0, 5)
        )

        create_button(
            button_frame,
            "💸 Withdraw",
            self.withdraw_money,
            color_key='orange',
            font_key='label',
            fill=tk.X,
            pady=(0, 5)
        )

        create_button(
            button_frame,
            "💳 Transfer",
            self.transfer_money,
            color_key='orange',
            font_key='label',
            fill=tk.X,
            pady=(0, 5)
        )

        self.update_account_display()

    def create_right_panel(self, parent):
        """Create right panel with transaction history."""
        # Header with export button
        header_frame = tk.Frame(parent, bg=COLORS['bg_card'])
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        history_title = tk.Label(
            header_frame,
            text="Transaction History",
            font=FONTS['subheading'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_bright']
        )
        history_title.pack(side=tk.LEFT)

        export_btn = tk.Button(
            header_frame,
            text="📥 Export CSV",
            font=FONTS['tiny'],
            bg=COLORS['accent_blue'],
            fg=COLORS['bg_dark'],
            bd=0,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.export_transactions
        )
        export_btn.pack(side=tk.RIGHT)

        # Filter frame
        filter_frame = tk.Frame(parent, bg=COLORS['bg_card'])
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        filter_label = tk.Label(
            filter_frame,
            text="Filter by:",
            font=FONTS['small'],
            bg=COLORS['bg_card'],
            fg=COLORS['text_secondary']
        )
        filter_label.pack(side=tk.LEFT, padx=(0, 10))

        filter_options = ["All"] + self.TRANSACTION_CATEGORIES
        self.filter_var, filter_dropdown = create_combobox(
            filter_frame,
            filter_options,
            default="All",
            width=15,
            side=tk.LEFT
        )
        filter_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_transaction_history())

        # Transaction list with scrollbar
        list_frame = tk.Frame(parent, bg=COLORS['bg_card'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text = tk.Text(
            list_frame,
            font=FONTS['monospace'],
            bg=COLORS['bg_dark'],
            fg=COLORS['text_primary'],
            insertbackground=COLORS['accent_blue'],
            bd=1,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['focus'],
            yscrollcommand=scrollbar.set,
            state=tk.DISABLED,
            wrap=tk.WORD
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

        if hasattr(self.current_account, 'interest_rate'):
            info_text += f"\nInterest: {self.current_account.interest_rate*100:.2f}%"
        if hasattr(self.current_account, 'credit_limit'):
            info_text += f"\nCredit Limit: ${self.current_account.credit_limit:.2f}"
            info_text += f"\nAvailable: ${self.current_account.get_available_credit():.2f}"

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
            transactions = [t for t in transactions if t.get('category') == filter_category]

        if transactions:
            # Header
            header = f"{'Date & Time':<20} {'Type':<15} {'Category':<18} {'Amount':>10} {'Balance':>12}\n"
            self.history_text.insert(tk.END, header)
            self.history_text.insert(tk.END, "-" * 85 + "\n")

            for trans in transactions:
                category = trans.get('category', 'N/A') or 'N/A'
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
                self.db.update_balance(self.current_account.account_id, self.current_account.balance)
                self.db.add_transaction(
                    self.current_account.account_id,
                    'Deposit',
                    amount,
                    f"Deposit - {category}",
                    self.current_account.balance,
                    category
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
                self.db.update_balance(self.current_account.account_id, self.current_account.balance)
                self.db.add_transaction(
                    self.current_account.account_id,
                    'Withdrawal',
                    amount,
                    f"Withdrawal - {category}",
                    self.current_account.balance,
                    category
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
            messagebox.showinfo("Info", "You need at least 2 accounts to make a transfer.")
            return

        TransferDialog(self.root, self.current_account, self.accounts, self.db, self.on_transfer_complete)

    def on_transfer_complete(self):
        """Callback after successful transfer."""
        # Store current account ID
        current_acc_id = self.current_account.account_id if self.current_account else None

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
        account_names = [f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                        for acc in self.accounts]
        self.account_dropdown['values'] = account_names

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
            icon='warning'
        )

        if not confirm:
            return

        # Check if this is the last account
        if len(self.accounts) == 1:
            messagebox.showerror(
                "Cannot Delete",
                "You cannot delete your last account.\n"
                "Create a new account first before deleting this one."
            )
            return

        # Perform deletion
        success, message = self.db.delete_account(self.current_account.account_id)

        if success:
            messagebox.showinfo("Success", "Account deleted successfully.")

            # Reload accounts and select the first one
            self.load_accounts()

            if self.accounts:
                account_names = [f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                                for acc in self.accounts]
                self.account_dropdown['values'] = account_names
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
            initialfile=f"transactions_{self.current_account.account_number}_{datetime.now().strftime('%Y%m%d')}.csv"
        )

        if filename:
            try:
                with open(filename, 'w', newline='') as csvfile:
                    writer = csv.writer(csvfile)
                    writer.writerow(['Date & Time', 'Type', 'Category', 'Amount', 'Balance After'])

                    for trans in self.current_account.transaction_history:
                        writer.writerow([
                            trans['time'],
                            trans['type'],
                            trans.get('category', 'N/A'),
                            f"${trans['amount']:.2f}",
                            f"${trans['balance']:.2f}"
                        ])

                messagebox.showinfo("Success", f"Transactions exported to {filename}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to export: {str(e)}")

    def logout(self):
        """Logout and return to login screen."""
        if messagebox.askyesno("Logout", "Are you sure you want to logout?"):
            self.root.quit()

    def show_analytics(self):
        """Open analytics dashboard window."""
        ChartsWindow(self.root, self.user_id, self.db, self.accounts)


class TransferDialog:
    """Dialog for transferring money between accounts."""

    def __init__(self, parent, from_account, all_accounts, db, on_success):
        self.from_account = from_account
        self.all_accounts = [acc for acc in all_accounts if acc.account_id != from_account.account_id]
        self.db = db
        self.on_success = on_success

        self.window = create_modal_dialog(parent, "Transfer Money", 400, 350)
        self.create_widgets()

    def create_widgets(self):
        """Create transfer dialog widgets."""
        main_frame = tk.Frame(self.window, bg=COLORS['white'], padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            main_frame,
            text="Transfer Money",
            font=FONTS['heading'],
            bg=COLORS['white']
        )
        title.pack(pady=(0, 20))

        # From account
        from_label = tk.Label(
            main_frame,
            text=f"From: {self.from_account.get_account_type()} - {self.from_account.account_number[-4:]}",
            font=FONTS['label'],
            bg=COLORS['white']
        )
        from_label.pack(anchor=tk.W, pady=(0, 5))

        balance_label = tk.Label(
            main_frame,
            text=f"Available: {self.from_account.get_balance_formatted()}",
            font=FONTS['small'],
            bg=COLORS['white'],
            fg=COLORS['text_secondary']
        )
        balance_label.pack(anchor=tk.W, pady=(0, 15))

        # To account
        to_label = tk.Label(
            main_frame,
            text="To Account:",
            font=FONTS['label'],
            bg=COLORS['white']
        )
        to_label.pack(anchor=tk.W, pady=(0, 5))

        account_names = [f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                        for acc in self.all_accounts]

        self.to_account_var, _ = create_combobox(
            main_frame,
            account_names,
            default=account_names[0] if account_names else None,
            fill=tk.X,
            pady=(0, 15)
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
            primary_color='accent'
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
                if f"{acc.get_account_type()} - {acc.account_number[-4:]}" == selected_name:
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
                f"Transfer to {to_account.account_number}"
            )

            if success:
                # Close dialog first for instant feedback, then show success message
                self.window.destroy()
                self.on_success()  # Refresh displays
                messagebox.showinfo("Success", "Transfer completed successfully!")
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")


class NewAccountDialog:
    """Dialog for creating a new account."""

    def __init__(self, parent, user_id, db, on_success):
        self.user_id = user_id
        self.db = db
        self.on_success = on_success

        self.window = create_modal_dialog(parent, "Create New Account", 400, 300)
        self.create_widgets()

    def create_widgets(self):
        """Create new account dialog widgets."""
        main_frame = tk.Frame(self.window, bg=COLORS['white'], padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            main_frame,
            text="Create New Account",
            font=FONTS['heading'],
            bg=COLORS['white']
        )
        title.pack(pady=(0, 20))

        # Account type
        type_label = tk.Label(
            main_frame,
            text="Account Type:",
            font=FONTS['label'],
            bg=COLORS['white']
        )
        type_label.pack(anchor=tk.W, pady=(0, 5))

        self.account_type_var, _ = create_combobox(
            main_frame,
            ["Checking", "Savings", "Credit"],
            default="Checking",
            fill=tk.X,
            pady=(0, 15)
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
            primary_color='accent'
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
            interest_rate = 0.02 if account_type == 'savings' else 0
            credit_limit = 5000 if account_type == 'credit' else 0

            account_id, account_number = self.db.create_account(
                self.user_id,
                account_type,
                initial_deposit,
                interest_rate,
                credit_limit
            )

            if account_id:
                # Close dialog first for instant feedback, then show success message
                self.window.destroy()
                self.on_success()  # Refresh displays
                messagebox.showinfo("Success",
                    f"New {account_type} account created!\nAccount Number: {account_number}")
            else:
                messagebox.showerror("Error", "Failed to create account.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid deposit amount.")
