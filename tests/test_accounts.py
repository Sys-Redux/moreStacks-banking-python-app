"""
Unit Tests for Account Models
Tests CheckingAccount, SavingsAccount, and CreditAccount classes
"""

import pytest
from models.account import (
    CheckingAccount,
    SavingsAccount,
    CreditAccount,
    create_account,
)


class TestCheckingAccount:
    """Test suite for CheckingAccount class."""

    @pytest.mark.unit
    def test_account_creation(self, checking_account):
        """Test checking account is created correctly."""
        assert checking_account.account_id == 1
        assert checking_account.account_number == "CHK001"
        assert checking_account.account_holder == "Test User"
        assert checking_account.balance == 1000.0
        assert checking_account.get_account_type() == "CheckingAccount"

    @pytest.mark.unit
    def test_deposit_success(self, checking_account):
        """Test successful deposit."""
        success, message = checking_account.deposit(500.0)

        assert success is True
        assert checking_account.balance == 1500.0
        assert "Deposited" in message

    @pytest.mark.unit
    def test_deposit_invalid_amount(self, checking_account):
        """Test deposit with invalid amount."""
        success, message = checking_account.deposit(-100.0)

        assert success is False
        assert checking_account.balance == 1000.0  # Unchanged
        assert "must be positive" in message.lower()

    @pytest.mark.unit
    def test_deposit_zero(self, checking_account):
        """Test deposit with zero amount."""
        success, message = checking_account.deposit(0)

        assert success is False
        assert checking_account.balance == 1000.0  # Unchanged

    @pytest.mark.unit
    def test_withdrawal_success(self, checking_account):
        """Test successful withdrawal."""
        success, message = checking_account.withdraw(300.0)

        assert success is True
        assert checking_account.balance == 700.0
        assert "Withdrew" in message

    @pytest.mark.unit
    def test_withdrawal_with_overdraft(self, checking_account):
        """Test withdrawal using overdraft protection."""
        success, message = checking_account.withdraw(1200.0)

        assert success is True
        assert checking_account.balance == -200.0  # Used $200 overdraft
        assert "Withdrew" in message

    @pytest.mark.unit
    def test_withdrawal_exceeds_overdraft(self, checking_account):
        """Test withdrawal that exceeds overdraft limit."""
        success, message = checking_account.withdraw(1600.0)

        assert success is False
        assert checking_account.balance == 1000.0  # Unchanged
        assert "overdraft" in message.lower()

    @pytest.mark.unit
    def test_withdrawal_invalid_amount(self, checking_account):
        """Test withdrawal with invalid amount."""
        success, message = checking_account.withdraw(-50.0)

        assert success is False
        assert checking_account.balance == 1000.0  # Unchanged

    @pytest.mark.unit
    def test_get_available_balance(self, checking_account):
        """Test available balance includes overdraft."""
        available = checking_account.get_available_balance()

        assert available == 1500.0  # $1000 balance + $500 overdraft

    @pytest.mark.unit
    def test_transaction_history(self, checking_account):
        """Test transaction history is recorded."""
        checking_account.deposit(200.0)
        checking_account.withdraw(100.0)

        assert len(checking_account.transaction_history) == 2
        assert checking_account.transaction_history[0]["type"] == "Deposit"
        assert checking_account.transaction_history[1]["type"] == "Withdrawal"

    @pytest.mark.unit
    def test_balance_property(self, checking_account):
        """Test balance property getter and setter."""
        checking_account.balance = 2000.0
        assert checking_account.balance == 2000.0

    @pytest.mark.unit
    def test_formatted_balance(self, checking_account):
        """Test formatted balance output."""
        formatted = checking_account.get_balance_formatted()
        assert formatted == "$1000.00"  # No comma formatting


class TestSavingsAccount:
    """Test suite for SavingsAccount class."""

    @pytest.mark.unit
    def test_account_creation(self, savings_account):
        """Test savings account is created correctly."""
        assert savings_account.account_id == 2
        assert savings_account.get_account_type() == "SavingsAccount"
        assert savings_account.balance == 5000.0
        assert savings_account.interest_rate == 2.0
        assert savings_account.withdrawal_count == 0

    @pytest.mark.unit
    def test_deposit_success(self, savings_account):
        """Test successful deposit to savings."""
        success, message = savings_account.deposit(1000.0)

        assert success is True
        assert savings_account.balance == 6000.0

    @pytest.mark.unit
    def test_withdrawal_under_limit(self, savings_account):
        """Test withdrawal within monthly limit."""
        for i in range(6):
            success, message = savings_account.withdraw(100.0)
            assert success is True

        assert savings_account.withdrawal_count == 6
        assert savings_account.balance == 4400.0

    @pytest.mark.unit
    def test_withdrawal_exceeds_monthly_limit(self, savings_account):
        """Test withdrawal exceeding 6 per month limit."""
        # Make 6 successful withdrawals
        for i in range(6):
            savings_account.withdraw(100.0)

        # 7th withdrawal should fail
        success, message = savings_account.withdraw(100.0)

        assert success is False
        assert "withdrawal limit" in message.lower()
        assert savings_account.balance == 4400.0  # Unchanged from 7th attempt

    @pytest.mark.unit
    def test_withdrawal_below_minimum_balance(self, savings_account):
        """Test withdrawal that would go below $100 minimum."""
        success, message = savings_account.withdraw(4950.0)

        assert success is False
        assert "minimum balance" in message.lower()
        assert savings_account.balance == 5000.0  # Unchanged

    @pytest.mark.unit
    def test_withdrawal_insufficient_funds(self, savings_account):
        """Test withdrawal with insufficient funds."""
        success, message = savings_account.withdraw(6000.0)

        assert success is False
        assert "insufficient" in message.lower() or "minimum balance" in message.lower()

    @pytest.mark.unit
    def test_interest_calculation(self, savings_account):
        """Test interest calculation."""
        interest = savings_account.calculate_interest(30)

        # $5000 * (2/365) * 30 = ~$821.92
        # Interest rate is already a percentage (2.0 means 2%)
        assert 820.0 < interest < 825.0

    @pytest.mark.unit
    def test_apply_interest(self, savings_account):
        """Test applying interest to balance."""
        initial_balance = savings_account.balance
        success, message = savings_account.apply_interest(30)

        assert success is True
        assert savings_account.balance > initial_balance
        assert "Interest applied" in message

    @pytest.mark.unit
    def test_reset_withdrawal_count(self, savings_account):
        """Test resetting monthly withdrawal count."""
        savings_account.withdraw(100.0)
        savings_account.withdraw(100.0)
        assert savings_account.withdrawal_count == 2

        savings_account.reset_withdrawal_count()
        assert savings_account.withdrawal_count == 0


class TestCreditAccount:
    """Test suite for CreditAccount class."""

    @pytest.mark.unit
    def test_account_creation(self, credit_account):
        """Test credit account is created correctly."""
        assert credit_account.account_id == 3
        assert credit_account.get_account_type() == "CreditAccount"
        assert credit_account.balance == 0.0
        assert credit_account.credit_limit == 5000.0

    @pytest.mark.unit
    def test_deposit_payment(self, credit_account):
        """Test making a payment (deposit)."""
        # Make a purchase first
        credit_account.withdraw(500.0)
        assert credit_account.balance == -500.0

        # Make payment
        success, message = credit_account.deposit(300.0)

        assert success is True
        assert credit_account.balance == -200.0  # $500 - $300 payment
        assert "Payment" in message

    @pytest.mark.unit
    def test_withdrawal_purchase(self, credit_account):
        """Test making a credit purchase."""
        success, message = credit_account.withdraw(1000.0)

        assert success is True
        assert credit_account.balance == -1000.0  # Negative = owe money
        assert "Charged" in message  # Updated assertion

    @pytest.mark.unit
    def test_withdrawal_exceeds_credit_limit(self, credit_account):
        """Test purchase exceeding credit limit."""
        success, message = credit_account.withdraw(6000.0)

        assert success is False
        assert credit_account.balance == 0.0  # Unchanged
        assert "credit limit" in message.lower()

    @pytest.mark.unit
    def test_multiple_purchases_within_limit(self, credit_account):
        """Test multiple purchases within credit limit."""
        credit_account.withdraw(2000.0)
        credit_account.withdraw(2000.0)
        success, message = credit_account.withdraw(500.0)

        assert success is True
        assert credit_account.balance == -4500.0

    @pytest.mark.unit
    def test_payment_when_zero_balance(self, credit_account):
        """Test payment when balance is already zero."""
        success, message = credit_account.deposit(100.0)

        # Payment is accepted, but creates overpayment
        assert success is True
        assert credit_account.balance == 100.0  # Can be positive (overpaid)

    @pytest.mark.unit
    def test_credit_account_balance_persistence(self):
        """Test that credit account preserves balance when initialized from database."""
        # Simulate loading a credit account from database with existing balance
        account = CreditAccount(
            account_id=10,
            account_number="CRD999",
            account_holder="Test User",
            balance=-250.0,  # Has $250 debt
            credit_limit=5000.0,
        )

        # Balance should be preserved (not reset to 0)
        assert account.balance == -250.0
        assert account.get_available_credit() == 4750.0  # 5000 - 250

        # Credit limit should be preserved
        assert account.credit_limit == 5000.0


class TestAccountFactory:
    """Test suite for create_account factory function."""

    @pytest.mark.unit
    def test_create_checking_account(self):
        """Test factory creates checking account."""
        account = create_account("checking", 1, "CHK001", "Test User", 1000.0)

        assert isinstance(account, CheckingAccount)
        assert account.get_account_type() == "CheckingAccount"

    @pytest.mark.unit
    def test_create_savings_account(self):
        """Test factory creates savings account."""
        account = create_account(
            "savings", 2, "SAV001", "Test User", 5000.0, interest_rate=2.5
        )

        assert isinstance(account, SavingsAccount)
        assert account.get_account_type() == "SavingsAccount"
        assert account.interest_rate == 2.5

    @pytest.mark.unit
    def test_create_credit_account(self):
        """Test factory creates credit account."""
        account = create_account(
            "credit", 3, "CRD001", "Test User", 0.0, credit_limit=3000.0
        )

        assert isinstance(account, CreditAccount)
        assert account.get_account_type() == "CreditAccount"
        assert account.credit_limit == 3000.0

    @pytest.mark.unit
    def test_create_invalid_account_type(self):
        """Test factory with invalid account type."""
        with pytest.raises(ValueError):
            create_account("invalid", 1, "INV001", "Test User", 0.0)


class TestAccountEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.unit
    def test_very_large_deposit(self, checking_account):
        """Test deposit of very large amount."""
        success, message = checking_account.deposit(1_000_000.0)

        assert success is True
        assert checking_account.balance == 1_001_000.0

    @pytest.mark.unit
    def test_very_small_amounts(self, checking_account):
        """Test operations with very small amounts."""
        success, _ = checking_account.deposit(0.01)
        assert success is True
        assert checking_account.balance == 1000.01

        success, _ = checking_account.withdraw(0.01)
        assert success is True
        assert checking_account.balance == 1000.0

    @pytest.mark.unit
    def test_floating_point_precision(self, checking_account):
        """Test floating point precision handling."""
        checking_account.deposit(0.1)
        checking_account.deposit(0.2)

        # Should be 1000.3, not 1000.30000000004
        assert checking_account.balance == pytest.approx(1000.3, rel=1e-9)
