from abc import ABC, abstractmethod
from datetime import datetime
from typing import Tuple, List, Dict


class Account(ABC):
    """Abstract base class for all account types."""

    def __init__(
        self,
        account_id: int,
        account_number: str,
        account_holder: str,
        balance: float = 0,
    ):
        self.account_id = account_id
        self.account_number = account_number
        self.account_holder = account_holder
        self._balance = balance
        self.transaction_history: List[Dict] = []

    @property
    def balance(self) -> float:
        """Get current balance."""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Set balance."""
        self._balance = value

    def deposit(self, amount: float, category: str = None) -> Tuple[bool, str]:
        """Deposit money into account."""
        if amount <= 0:
            return False, "Deposit amount must be positive."

        self._balance += amount
        self._record_transaction("Deposit", amount, category)
        return True, f"Deposited ${amount:.2f}. New balance: ${self._balance:.2f}"

    @abstractmethod
    def withdraw(self, amount: float, category: str = None) -> Tuple[bool, str]:
        """Withdraw money from account. Must be implemented by subclasses."""
        pass

    def _record_transaction(
        self, transaction_type: str, amount: float, category: str = None
    ):
        """Record a transaction in history."""
        self.transaction_history.append(
            {
                "type": transaction_type,
                "amount": amount,
                "category": category,
                "balance": self._balance,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    def get_balance_formatted(self) -> str:
        """Get formatted balance string."""
        return f"${self._balance:.2f}"

    def get_account_type(self) -> str:
        """Get account type name."""
        return self.__class__.__name__

    def __str__(self):
        return f"{self.get_account_type()} - {self.account_number} - Balance: ${self._balance:.2f}"


class CheckingAccount(Account):
    """Checking account with overdraft protection."""

    def __init__(
        self,
        account_id: int,
        account_number: str,
        account_holder: str,
        balance: float = 0,
        overdraft_limit: float = 500,
    ):
        super().__init__(account_id, account_number, account_holder, balance)
        self.overdraft_limit = overdraft_limit

    def withdraw(self, amount: float, category: str = None) -> Tuple[bool, str]:
        """Withdraw with overdraft protection."""
        if amount <= 0:
            return False, "Withdrawal amount must be positive."

        # Check if withdrawal would exceed overdraft limit
        if self._balance - amount < -self.overdraft_limit:
            return (
                False,
                f"Insufficient funds. Overdraft limit: ${self.overdraft_limit:.2f}",
            )

        self._balance -= amount
        self._record_transaction("Withdrawal", amount, category)

        if self._balance < 0:
            return (
                True,
                f"Withdrew ${amount:.2f}. Warning: Overdraft balance: ${self._balance:.2f}",
            )

        return True, f"Withdrew ${amount:.2f}. New balance: ${self._balance:.2f}"

    def get_available_balance(self) -> float:
        """Get available balance including overdraft."""
        return self._balance + self.overdraft_limit


class SavingsAccount(Account):
    """Savings account with interest calculation."""

    def __init__(
        self,
        account_id: int,
        account_number: str,
        account_holder: str,
        balance: float = 0,
        interest_rate: float = 0.02,
        minimum_balance: float = 100,
    ):
        super().__init__(account_id, account_number, account_holder, balance)
        self.interest_rate = interest_rate  # Annual interest rate
        self.minimum_balance = minimum_balance
        self.withdrawal_count = 0
        self.monthly_withdrawal_limit = 6

    def withdraw(self, amount: float, category: str = None) -> Tuple[bool, str]:
        """Withdraw with minimum balance and monthly limit restrictions."""
        if amount <= 0:
            return False, "Withdrawal amount must be positive."

        # Check withdrawal limit
        if self.withdrawal_count >= self.monthly_withdrawal_limit:
            return (
                False,
                f"Monthly withdrawal limit ({self.monthly_withdrawal_limit}) reached.",
            )

        # Check minimum balance
        if self._balance - amount < self.minimum_balance:
            return (
                False,
                f"Withdrawal would violate minimum balance of ${self.minimum_balance:.2f}",
            )

        self._balance -= amount
        self.withdrawal_count += 1
        self._record_transaction("Withdrawal", amount, category)

        remaining_withdrawals = self.monthly_withdrawal_limit - self.withdrawal_count
        return True, (
            f"Withdrew ${amount:.2f}. New balance: ${self._balance:.2f}\n"
            f"Remaining withdrawals this month: {remaining_withdrawals}"
        )

    def calculate_interest(self, days: int = 30) -> float:
        """Calculate interest for specified number of days."""
        daily_rate = self.interest_rate / 365
        interest = self._balance * daily_rate * days
        return interest

    def apply_interest(self, days: int = 30) -> Tuple[bool, str]:
        """Apply interest to account."""
        interest = self.calculate_interest(days)
        if interest > 0:
            self._balance += interest
            self._record_transaction("Interest", interest, "Interest")
            return (
                True,
                f"Interest applied: ${interest:.2f}. New balance: ${self._balance:.2f}",
            )
        return False, "No interest to apply."

    def reset_withdrawal_count(self):
        """Reset monthly withdrawal count."""
        self.withdrawal_count = 0


class CreditAccount(Account):
    """Credit account with credit limit and interest on borrowed amounts."""

    def __init__(
        self,
        account_id: int,
        account_number: str,
        account_holder: str,
        balance: float = 0,
        credit_limit: float = 5000,
        interest_rate: float = 0.18,
    ):
        super().__init__(account_id, account_number, account_holder, balance)
        self.credit_limit = credit_limit
        self.interest_rate = interest_rate  # Annual interest rate
        # Note: balance is inherited from parent, negative balance means debt

    def withdraw(self, amount: float, category: str = None) -> Tuple[bool, str]:
        """Withdraw (borrow) money up to credit limit."""
        if amount <= 0:
            return False, "Amount must be positive."

        # Check if withdrawal would exceed credit limit
        if abs(self._balance - amount) > self.credit_limit:
            available = self.credit_limit - abs(self._balance)
            return False, f"Exceeds credit limit. Available credit: ${available:.2f}"

        self._balance -= amount
        self._record_transaction("Credit Purchase", amount, category)

        available_credit = self.credit_limit - abs(self._balance)
        return True, (
            f"Charged ${amount:.2f}. Current balance: ${self._balance:.2f}\n"
            f"Available credit: ${available_credit:.2f}"
        )

    def deposit(self, amount: float, category: str = None) -> Tuple[bool, str]:
        """Make a payment toward credit balance."""
        if amount <= 0:
            return False, "Payment amount must be positive."

        self._balance += amount
        self._record_transaction("Payment", amount, category)

        if self._balance > 0:
            return (
                True,
                f"Payment received: ${amount:.2f}. Credit balance: ${abs(self._balance):.2f} (overpaid)",
            )
        elif self._balance == 0:
            return True, f"Payment received: ${amount:.2f}. Account paid in full!"
        else:
            return (
                True,
                f"Payment received: ${amount:.2f}. Remaining balance: ${abs(self._balance):.2f}",
            )

    def get_available_credit(self) -> float:
        """Get available credit."""
        return self.credit_limit - abs(self._balance)

    def calculate_interest(self, days: int = 30) -> float:
        """Calculate interest on outstanding balance."""
        if self._balance >= 0:
            return 0  # No interest if no debt

        daily_rate = self.interest_rate / 365
        interest = abs(self._balance) * daily_rate * days
        return interest

    def apply_interest(self, days: int = 30) -> Tuple[bool, str]:
        """Apply interest charges to outstanding balance."""
        interest = self.calculate_interest(days)
        if interest > 0:
            self._balance -= interest  # Increase debt
            self._record_transaction("Interest Charge", interest, "Interest")
            return (
                True,
                f"Interest charged: ${interest:.2f}. New balance: ${self._balance:.2f}",
            )
        return False, "No interest charges."

    def get_balance_formatted(self) -> str:
        """Get formatted balance string."""
        if self._balance < 0:
            return f"-${abs(self._balance):.2f}"
        return f"${self._balance:.2f}"


def create_account(
    account_type: str,
    account_id: int,
    account_number: str,
    account_holder: str,
    balance: float = 0,
    interest_rate: float = 0,
    credit_limit: float = 0,
) -> Account:
    """Factory function to create appropriate account type."""
    account_type = account_type.lower()

    if account_type == "checking":
        return CheckingAccount(account_id, account_number, account_holder, balance)
    elif account_type == "savings":
        return SavingsAccount(
            account_id, account_number, account_holder, balance, interest_rate
        )
    elif account_type == "credit":
        return CreditAccount(
            account_id,
            account_number,
            account_holder,
            balance,
            credit_limit,
            interest_rate,
        )
    else:
        raise ValueError(f"Unknown account type: {account_type}")
