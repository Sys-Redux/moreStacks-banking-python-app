import tkinter as tk
from tkinter import messagebox, ttk
from datetime import datetime


class BankAccount:
    def __init__(self, account_holder, balance=0):
        self.account_holder = account_holder
        self.balance = balance
        self.transaction_history = []

    # Method to deposit money
    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.transaction_history.append({
                'type': 'Deposit',
                'amount': amount,
                'balance': self.balance,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return True, f"Deposited ${amount:.2f}. New balance: ${self.balance:.2f}"
        else:
            return False, "Deposit amount must be positive."

    # Method to withdraw money
    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.transaction_history.append({
                'type': 'Withdrawal',
                'amount': amount,
                'balance': self.balance,
                'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            return True, f"Withdrew ${amount:.2f}. New balance: ${self.balance:.2f}"
        else:
            return False, "Insufficient funds or invalid withdrawal amount."

    # Method to check balance
    def check_balance(self):
        return f"${self.balance:.2f}"


class BankGUI:
    def __init__(self, root, account):
        self.root = root
        self.account = account
        self.root.title("moreStacks Banking")
        self.root.geometry("600x700")
        self.root.resizable(False, False)

        # Color scheme - Professional banking colors
        self.primary_color = "#1a237e"  # Deep blue
        self.secondary_color = "#3949ab"  # Medium blue
        self.accent_color = "#00c853"  # Green for positive actions
        self.bg_color = "#f5f5f5"  # Light gray background
        self.white = "#ffffff"

        self.root.configure(bg=self.bg_color)

        self.create_widgets()

    def create_widgets(self):
        # Header Frame
        header_frame = tk.Frame(self.root, bg=self.primary_color, height=100)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)

        # Bank Logo/Name
        bank_name = tk.Label(
            header_frame,
            text="moreStacks",
            font=("Helvetica", 32, "bold"),
            bg=self.primary_color,
            fg=self.white
        )
        bank_name.pack(pady=20)

        # Account Info Frame
        info_frame = tk.Frame(self.root, bg=self.white, padx=20, pady=20)
        info_frame.pack(fill=tk.X, padx=20, pady=20)

        account_label = tk.Label(
            info_frame,
            text=f"Account Holder: {self.account.account_holder}",
            font=("Helvetica", 14),
            bg=self.white,
            fg=self.primary_color
        )
        account_label.pack(anchor=tk.W)

        # Balance Display
        balance_frame = tk.Frame(info_frame, bg=self.white)
        balance_frame.pack(fill=tk.X, pady=10)

        balance_text = tk.Label(
            balance_frame,
            text="Current Balance:",
            font=("Helvetica", 12),
            bg=self.white,
            fg="#666666"
        )
        balance_text.pack(side=tk.LEFT)

        self.balance_display = tk.Label(
            balance_frame,
            text=self.account.check_balance(),
            font=("Helvetica", 24, "bold"),
            bg=self.white,
            fg=self.accent_color
        )
        self.balance_display.pack(side=tk.RIGHT)

        # Transaction Frame
        transaction_frame = tk.Frame(self.root, bg=self.white, padx=20, pady=20)
        transaction_frame.pack(fill=tk.BOTH, padx=20, pady=(0, 20), expand=True)

        transaction_title = tk.Label(
            transaction_frame,
            text="Make a Transaction",
            font=("Helvetica", 16, "bold"),
            bg=self.white,
            fg=self.primary_color
        )
        transaction_title.pack(pady=(0, 15))

        # Amount Entry
        amount_frame = tk.Frame(transaction_frame, bg=self.white)
        amount_frame.pack(fill=tk.X, pady=10)

        amount_label = tk.Label(
            amount_frame,
            text="Amount ($):",
            font=("Helvetica", 12),
            bg=self.white,
            fg=self.primary_color
        )
        amount_label.pack(anchor=tk.W, pady=(0, 5))

        self.amount_entry = tk.Entry(
            amount_frame,
            font=("Helvetica", 14),
            bd=2,
            relief=tk.SOLID,
            highlightthickness=1,
            highlightcolor=self.secondary_color
        )
        self.amount_entry.pack(fill=tk.X, ipady=8)

        # Buttons Frame
        button_frame = tk.Frame(transaction_frame, bg=self.white)
        button_frame.pack(fill=tk.X, pady=20)

        # Deposit Button
        deposit_btn = tk.Button(
            button_frame,
            text="Deposit",
            font=("Helvetica", 12, "bold"),
            bg=self.accent_color,
            fg=self.white,
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self.deposit_money,
            activebackground="#00e676"
        )
        deposit_btn.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 5))

        # Withdraw Button
        withdraw_btn = tk.Button(
            button_frame,
            text="Withdraw",
            font=("Helvetica", 12, "bold"),
            bg=self.secondary_color,
            fg=self.white,
            bd=0,
            padx=30,
            pady=12,
            cursor="hand2",
            command=self.withdraw_money,
            activebackground="#5c6bc0"
        )
        withdraw_btn.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5, 0))

        # Transaction History
        history_label = tk.Label(
            transaction_frame,
            text="Recent Transactions",
            font=("Helvetica", 12, "bold"),
            bg=self.white,
            fg=self.primary_color
        )
        history_label.pack(anchor=tk.W, pady=(20, 10))

        # Scrollable Transaction List
        history_frame = tk.Frame(transaction_frame, bg=self.white)
        history_frame.pack(fill=tk.BOTH, expand=True)

        scrollbar = tk.Scrollbar(history_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.history_text = tk.Text(
            history_frame,
            font=("Courier", 10),
            bg="#fafafa",
            fg="#333333",
            bd=1,
            relief=tk.SOLID,
            yscrollcommand=scrollbar.set,
            height=8,
            state=tk.DISABLED
        )
        self.history_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=self.history_text.yview)

        # Footer
        footer = tk.Label(
            self.root,
            text="moreStacks Banking © 2025 | Secure & Reliable",
            font=("Helvetica", 9),
            bg=self.bg_color,
            fg="#666666"
        )
        footer.pack(pady=10)

    def deposit_money(self):
        try:
            amount = float(self.amount_entry.get())
            success, message = self.account.deposit(amount)

            if success:
                messagebox.showinfo("Success", message)
                self.update_display()
                self.amount_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")

    def withdraw_money(self):
        try:
            amount = float(self.amount_entry.get())
            success, message = self.account.withdraw(amount)

            if success:
                messagebox.showinfo("Success", message)
                self.update_display()
                self.amount_entry.delete(0, tk.END)
            else:
                messagebox.showerror("Error", message)
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid numeric amount.")

    def update_display(self):
        # Update balance
        self.balance_display.config(text=self.account.check_balance())

        # Update transaction history
        self.history_text.config(state=tk.NORMAL)
        self.history_text.delete(1.0, tk.END)

        if self.account.transaction_history:
            for trans in reversed(self.account.transaction_history[-10:]):  # Show last 10
                line = f"{trans['time']} | {trans['type']:12} | ${trans['amount']:8.2f} | Bal: ${trans['balance']:.2f}\n"
                self.history_text.insert(tk.END, line)
        else:
            self.history_text.insert(tk.END, "No transactions yet.")

        self.history_text.config(state=tk.DISABLED)


# Main execution
if __name__ == "__main__":
    # Creating an instance of BankAccount
    account = BankAccount("John Doe", 21050)

    # Create and run GUI
    root = tk.Tk()
    app = BankGUI(root, account)
    root.mainloop()