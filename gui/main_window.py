import tkinter as tk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from models.account import create_account
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

        # Window setup
        self.root.title("moreStacks Banking - Dashboard")
        self.root.geometry("900x750")
        self.root.resizable(False, False)

        # Colors
        self.primary_color = "#1a237e"
        self.secondary_color = "#3949ab"
        self.accent_color = "#00c853"
        self.bg_color = "#f5f5f5"
        self.white = "#ffffff"
        self.warning_color = "#ff9800"
        self.error_color = "#f44336"

        self.root.configure(bg=self.bg_color)

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
        """Create main interface widgets."""
        # Header
        header_frame = tk.Frame(self.root, bg=self.primary_color, height=80)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Left side - Logo
        logo_label = tk.Label(
            header_frame,
            text="moreStacks",
            font=("Helvetica", 24, "bold"),
            bg=self.primary_color,
            fg=self.white
        )
        logo_label.pack(side=tk.LEFT, padx=20, pady=20)

        # Right side - User info
        user_frame = tk.Frame(header_frame, bg=self.primary_color)
        user_frame.pack(side=tk.RIGHT, padx=20)

        welcome_label = tk.Label(
            user_frame,
            text=f"Welcome, {self.user_info['full_name']}",
            font=("Helvetica", 12),
            bg=self.primary_color,
            fg=self.white
        )
        welcome_label.pack(anchor=tk.E)

        logout_btn = tk.Button(
            user_frame,
            text="Logout",
            font=("Helvetica", 9),
            bg=self.secondary_color,
            fg=self.white,
            bd=0,
            padx=15,
            pady=5,
            cursor="hand2",
            command=self.logout
        )
        logout_btn.pack(anchor=tk.E, pady=(5, 0))

        # Main content area
        content_frame = tk.Frame(self.root, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left panel - Account selection and info
        left_panel = tk.Frame(content_frame, bg=self.white, width=280)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)

        self.create_left_panel(left_panel)

        # Right panel - Transactions
        right_panel = tk.Frame(content_frame, bg=self.white)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.create_right_panel(right_panel)

    def create_left_panel(self, parent):
        """Create left panel with account selection and operations."""
        # Account selection
        account_label = tk.Label(
            parent,
            text="My Accounts",
            font=("Helvetica", 14, "bold"),
            bg=self.white,
            fg=self.primary_color
        )
        account_label.pack(padx=15, pady=(15, 10), anchor=tk.W)

        # Account dropdown
        account_frame = tk.Frame(parent, bg=self.white)
        account_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        account_names = [f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                        for acc in self.accounts]

        self.account_var = tk.StringVar()
        if account_names:
            self.account_var.set(account_names[0])

        account_dropdown = ttk.Combobox(
            account_frame,
            textvariable=self.account_var,
            values=account_names,
            state="readonly",
            font=("Helvetica", 11)
        )
        account_dropdown.pack(fill=tk.X)
        account_dropdown.bind("<<ComboboxSelected>>", self.on_account_change)

        # Add new account button
        new_account_btn = tk.Button(
            parent,
            text="+ New Account",
            font=("Helvetica", 10),
            bg=self.secondary_color,
            fg=self.white,
            bd=0,
            pady=8,
            cursor="hand2",
            command=self.create_new_account
        )
        new_account_btn.pack(fill=tk.X, padx=15, pady=(0, 15))

        # Balance display
        balance_frame = tk.Frame(parent, bg="#e8eaf6", bd=1, relief=tk.SOLID)
        balance_frame.pack(fill=tk.X, padx=15, pady=(0, 15))

        balance_title = tk.Label(
            balance_frame,
            text="Current Balance",
            font=("Helvetica", 10),
            bg="#e8eaf6",
            fg="#666666"
        )
        balance_title.pack(pady=(10, 0))

        self.balance_label = tk.Label(
            balance_frame,
            text="$0.00",
            font=("Helvetica", 28, "bold"),
            bg="#e8eaf6",
            fg=self.accent_color
        )
        self.balance_label.pack(pady=(0, 10))

        # Account type info
        self.account_type_label = tk.Label(
            parent,
            text="",
            font=("Helvetica", 9),
            bg=self.white,
            fg="#666666"
        )
        self.account_type_label.pack(padx=15, pady=(0, 10))

        # Transaction form
        transaction_title = tk.Label(
            parent,
            text="New Transaction",
            font=("Helvetica", 12, "bold"),
            bg=self.white,
            fg=self.primary_color
        )
        transaction_title.pack(padx=15, pady=(15, 10), anchor=tk.W)

        # Amount entry
        amount_label = tk.Label(
            parent,
            text="Amount ($):",
            font=("Helvetica", 10),
            bg=self.white,
            fg=self.primary_color
        )
        amount_label.pack(padx=15, pady=(5, 2), anchor=tk.W)

        self.amount_entry = tk.Entry(
            parent,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID
        )
        self.amount_entry.pack(fill=tk.X, padx=15, ipady=6)

        # Category dropdown
        category_label = tk.Label(
            parent,
            text="Category:",
            font=("Helvetica", 10),
            bg=self.white,
            fg=self.primary_color
        )
        category_label.pack(padx=15, pady=(10, 2), anchor=tk.W)

        self.category_var = tk.StringVar(value="Uncategorized")
        category_dropdown = ttk.Combobox(
            parent,
            textvariable=self.category_var,
            values=self.TRANSACTION_CATEGORIES,
            state="readonly",
            font=("Helvetica", 10)
        )
        category_dropdown.pack(fill=tk.X, padx=15)

        # Buttons
        button_frame = tk.Frame(parent, bg=self.white)
        button_frame.pack(fill=tk.X, padx=15, pady=15)

        deposit_btn = tk.Button(
            button_frame,
            text="Deposit",
            font=("Helvetica", 11, "bold"),
            bg=self.accent_color,
            fg=self.white,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.deposit_money
        )
        deposit_btn.pack(fill=tk.X, pady=(0, 5))

        withdraw_btn = tk.Button(
            button_frame,
            text="Withdraw",
            font=("Helvetica", 11, "bold"),
            bg=self.secondary_color,
            fg=self.white,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.withdraw_money
        )
        withdraw_btn.pack(fill=tk.X, pady=(0, 5))

        transfer_btn = tk.Button(
            button_frame,
            text="Transfer",
            font=("Helvetica", 11, "bold"),
            bg=self.warning_color,
            fg=self.white,
            bd=0,
            pady=10,
            cursor="hand2",
            command=self.transfer_money
        )
        transfer_btn.pack(fill=tk.X)

        self.update_account_display()

    def create_right_panel(self, parent):
        """Create right panel with transaction history."""
        # Header with export button
        header_frame = tk.Frame(parent, bg=self.white)
        header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

        history_title = tk.Label(
            header_frame,
            text="Transaction History",
            font=("Helvetica", 14, "bold"),
            bg=self.white,
            fg=self.primary_color
        )
        history_title.pack(side=tk.LEFT)

        export_btn = tk.Button(
            header_frame,
            text="Export CSV",
            font=("Helvetica", 9),
            bg=self.white,
            fg=self.secondary_color,
            bd=1,
            relief=tk.SOLID,
            padx=10,
            pady=5,
            cursor="hand2",
            command=self.export_transactions
        )
        export_btn.pack(side=tk.RIGHT)

        # Filter frame
        filter_frame = tk.Frame(parent, bg=self.white)
        filter_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

        filter_label = tk.Label(
            filter_frame,
            text="Filter by:",
            font=("Helvetica", 10),
            bg=self.white,
            fg="#666666"
        )
        filter_label.pack(side=tk.LEFT, padx=(0, 10))

        self.filter_var = tk.StringVar(value="All")
        filter_options = ["All"] + self.TRANSACTION_CATEGORIES

        filter_dropdown = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_var,
            values=filter_options,
            state="readonly",
            font=("Helvetica", 9),
            width=15
        )
        filter_dropdown.pack(side=tk.LEFT)
        filter_dropdown.bind("<<ComboboxSelected>>", lambda e: self.update_transaction_history())

        # Transaction list with scrollbar
        list_frame = tk.Frame(parent, bg=self.white)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))

        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text = tk.Text(
            list_frame,
            font=("Courier", 9),
            bg="#fafafa",
            fg="#333333",
            bd=1,
            relief=tk.SOLID,
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
        self.load_accounts()
        self.update_account_display()
        self.update_transaction_history()

    def create_new_account(self):
        """Show dialog to create new account."""
        NewAccountDialog(self.root, self.user_id, self.db, self.on_new_account_created)

    def on_new_account_created(self):
        """Callback after new account creation."""
        self.load_accounts()
        # Update dropdown
        account_names = [f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                        for acc in self.accounts]
        self.account_var.set(account_names[-1])  # Select new account
        self.on_account_change()

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


class TransferDialog:
    """Dialog for transferring money between accounts."""

    def __init__(self, parent, from_account, all_accounts, db, on_success):
        self.from_account = from_account
        self.all_accounts = [acc for acc in all_accounts if acc.account_id != from_account.account_id]
        self.db = db
        self.on_success = on_success

        self.window = tk.Toplevel(parent)
        self.window.title("Transfer Money")
        self.window.geometry("400x350")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self.create_widgets()

    def create_widgets(self):
        """Create transfer dialog widgets."""
        main_frame = tk.Frame(self.window, bg="#ffffff", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            main_frame,
            text="Transfer Money",
            font=("Helvetica", 16, "bold"),
            bg="#ffffff"
        )
        title.pack(pady=(0, 20))

        # From account
        from_label = tk.Label(
            main_frame,
            text=f"From: {self.from_account.get_account_type()} - {self.from_account.account_number[-4:]}",
            font=("Helvetica", 11),
            bg="#ffffff"
        )
        from_label.pack(anchor=tk.W, pady=(0, 5))

        balance_label = tk.Label(
            main_frame,
            text=f"Available: {self.from_account.get_balance_formatted()}",
            font=("Helvetica", 10),
            bg="#ffffff",
            fg="#666666"
        )
        balance_label.pack(anchor=tk.W, pady=(0, 15))

        # To account
        to_label = tk.Label(
            main_frame,
            text="To Account:",
            font=("Helvetica", 11),
            bg="#ffffff"
        )
        to_label.pack(anchor=tk.W, pady=(0, 5))

        account_names = [f"{acc.get_account_type()} - {acc.account_number[-4:]}"
                        for acc in self.all_accounts]

        self.to_account_var = tk.StringVar()
        if account_names:
            self.to_account_var.set(account_names[0])

        to_dropdown = ttk.Combobox(
            main_frame,
            textvariable=self.to_account_var,
            values=account_names,
            state="readonly",
            font=("Helvetica", 11)
        )
        to_dropdown.pack(fill=tk.X, pady=(0, 15))

        # Amount
        amount_label = tk.Label(
            main_frame,
            text="Amount ($):",
            font=("Helvetica", 11),
            bg="#ffffff"
        )
        amount_label.pack(anchor=tk.W, pady=(0, 5))

        self.amount_entry = tk.Entry(
            main_frame,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID
        )
        self.amount_entry.pack(fill=tk.X, ipady=8, pady=(0, 20))

        # Buttons
        button_frame = tk.Frame(main_frame, bg="#ffffff")
        button_frame.pack(fill=tk.X)

        transfer_btn = tk.Button(
            button_frame,
            text="Transfer",
            font=("Helvetica", 12, "bold"),
            bg="#00c853",
            fg="#ffffff",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.do_transfer
        )
        transfer_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Helvetica", 12),
            bg="#f5f5f5",
            fg="#666666",
            bd=1,
            relief=tk.SOLID,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.window.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

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
                messagebox.showinfo("Success", "Transfer completed successfully!")
                self.window.destroy()
                self.on_success()
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

        self.window = tk.Toplevel(parent)
        self.window.title("Create New Account")
        self.window.geometry("400x300")
        self.window.resizable(False, False)
        self.window.transient(parent)
        self.window.grab_set()

        self.create_widgets()

    def create_widgets(self):
        """Create new account dialog widgets."""
        main_frame = tk.Frame(self.window, bg="#ffffff", padx=30, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        title = tk.Label(
            main_frame,
            text="Create New Account",
            font=("Helvetica", 16, "bold"),
            bg="#ffffff"
        )
        title.pack(pady=(0, 20))

        # Account type
        type_label = tk.Label(
            main_frame,
            text="Account Type:",
            font=("Helvetica", 11),
            bg="#ffffff"
        )
        type_label.pack(anchor=tk.W, pady=(0, 5))

        self.account_type_var = tk.StringVar(value="Checking")

        type_dropdown = ttk.Combobox(
            main_frame,
            textvariable=self.account_type_var,
            values=["Checking", "Savings", "Credit"],
            state="readonly",
            font=("Helvetica", 11)
        )
        type_dropdown.pack(fill=tk.X, pady=(0, 15))

        # Initial deposit
        deposit_label = tk.Label(
            main_frame,
            text="Initial Deposit ($):",
            font=("Helvetica", 11),
            bg="#ffffff"
        )
        deposit_label.pack(anchor=tk.W, pady=(0, 5))

        self.deposit_entry = tk.Entry(
            main_frame,
            font=("Helvetica", 12),
            bd=2,
            relief=tk.SOLID
        )
        self.deposit_entry.insert(0, "0")
        self.deposit_entry.pack(fill=tk.X, ipady=8, pady=(0, 20))

        # Buttons
        button_frame = tk.Frame(main_frame, bg="#ffffff")
        button_frame.pack(fill=tk.X)

        create_btn = tk.Button(
            button_frame,
            text="Create Account",
            font=("Helvetica", 12, "bold"),
            bg="#00c853",
            fg="#ffffff",
            bd=0,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.create_account
        )
        create_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        cancel_btn = tk.Button(
            button_frame,
            text="Cancel",
            font=("Helvetica", 12),
            bg="#f5f5f5",
            fg="#666666",
            bd=1,
            relief=tk.SOLID,
            padx=20,
            pady=10,
            cursor="hand2",
            command=self.window.destroy
        )
        cancel_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

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
                messagebox.showinfo("Success",
                    f"New {account_type} account created!\nAccount Number: {account_number}")
                self.window.destroy()
                self.on_success()
            else:
                messagebox.showerror("Error", "Failed to create account.")
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid deposit amount.")
