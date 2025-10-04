"""
Integration Tests
Tests complete workflows combining multiple components
"""
import pytest
from models.account import create_account
from database.db_manager import DatabaseManager


class TestUserRegistrationWorkflow:
    """Test complete user registration workflow."""

    @pytest.mark.integration
    def test_complete_registration_flow(self, temp_db):
        """Test user can register and create default account."""
        # Step 1: Create user
        user_id = temp_db.create_user(
            username="newuser",
            password="password123",
            full_name="New User",
            email="new@example.com"
        )

        assert user_id is not None

        # Step 2: Create default checking account
        account_id, account_number = temp_db.create_account(user_id, 'checking', 0.0)

        assert account_id is not None

        # Step 3: Verify user can authenticate
        authenticated_id = temp_db.authenticate_user("newuser", "password123")
        assert authenticated_id == user_id

        # Step 4: Verify account exists
        accounts = temp_db.get_user_accounts(user_id)
        assert len(accounts) == 1
        assert accounts[0]['account_type'] == 'checking'


class TestBankingOperationsWorkflow:
    """Test complete banking operations workflow."""

    @pytest.mark.integration
    def test_deposit_withdraw_workflow(self, db_with_accounts):
        """Test deposit and withdrawal workflow."""
        db, user_id, accounts = db_with_accounts

        checking_id = accounts['checking']['id']

        # Get initial balance
        account = db.get_account(checking_id)
        initial_balance = account['balance']

        # Create account object
        checking_account = create_account(
            'checking',
            checking_id,
            accounts['checking']['number'],
            "Test User",
            initial_balance
        )

        # Step 1: Make a deposit
        success, message = checking_account.deposit(500.0)
        assert success is True

        # Update database
        db.update_balance(checking_id, checking_account.balance)
        db.add_transaction(checking_id, 'Deposit', 500.0, 'Salary', checking_account.balance)

        # Step 2: Make a withdrawal
        success, message = checking_account.withdraw(200.0)
        assert success is True

        # Update database
        db.update_balance(checking_id, checking_account.balance)
        db.add_transaction(checking_id, 'Withdrawal', 200.0, 'Shopping', checking_account.balance)

        # Step 3: Verify final balance
        account = db.get_account(checking_id)
        expected_balance = initial_balance + 500.0 - 200.0
        assert account['balance'] == expected_balance

        # Step 4: Verify transaction history
        transactions = db.get_transactions(checking_id)
        assert len(transactions) >= 2

    @pytest.mark.integration
    def test_transfer_workflow(self, db_with_accounts):
        """Test transfer workflow between accounts."""
        db, user_id, accounts = db_with_accounts

        from_id = accounts['checking']['id']
        to_id = accounts['savings']['id']

        # Get initial balances
        from_account = db.get_account(from_id)
        to_account = db.get_account(to_id)

        initial_from = from_account['balance']
        initial_to = to_account['balance']

        # Perform transfer
        transfer_amount = 300.0
        success, message = db.create_transfer(from_id, to_id, transfer_amount)

        assert success is True
        assert "successful" in message.lower()

        # Verify balances
        from_account = db.get_account(from_id)
        to_account = db.get_account(to_id)

        assert from_account['balance'] == initial_from - transfer_amount
        assert to_account['balance'] == initial_to + transfer_amount

        # Verify transaction records
        from_transactions = db.get_transactions(from_id)
        to_transactions = db.get_transactions(to_id)

        assert any(t['transaction_type'] == 'Transfer Out' for t in from_transactions)
        assert any(t['transaction_type'] == 'Transfer In' for t in to_transactions)


class TestSavingsAccountWorkflow:
    """Test savings account specific workflows."""

    @pytest.mark.integration
    def test_savings_withdrawal_limit_workflow(self, db_with_accounts):
        """Test savings account withdrawal limit over time."""
        db, user_id, accounts = db_with_accounts

        savings_id = accounts['savings']['id']
        account_data = db.get_account(savings_id)

        # Create savings account object
        savings = create_account(
            'savings',
            savings_id,
            accounts['savings']['number'],
            "Test User",
            account_data['balance'],
            interest_rate=2.0
        )

        # Make 6 withdrawals (monthly limit)
        for i in range(6):
            success, message = savings.withdraw(100.0)
            assert success is True

            db.update_balance(savings_id, savings.balance)
            db.add_transaction(savings_id, 'Withdrawal', 100.0, 'Other', savings.balance)

        # 7th withdrawal should fail
        success, message = savings.withdraw(100.0)
        assert success is False
        assert "withdrawal limit" in message.lower() or "(6)" in message

        # Reset monthly limit
        savings.reset_withdrawal_count()

        # Should be able to withdraw again
        success, message = savings.withdraw(100.0)
        assert success is True

    @pytest.mark.integration
    def test_interest_application_workflow(self, db_with_accounts):
        """Test applying interest to savings account."""
        db, user_id, accounts = db_with_accounts

        savings_id = accounts['savings']['id']
        account_data = db.get_account(savings_id)

        # Create savings account object
        savings = create_account(
            'savings',
            savings_id,
            accounts['savings']['number'],
            "Test User",
            account_data['balance'],
            interest_rate=2.0
        )

        initial_balance = savings.balance

        # Apply 30 days of interest
        success, message = savings.apply_interest(30)
        assert success is True

        # Update database
        interest_amount = savings.balance - initial_balance
        db.update_balance(savings_id, savings.balance)
        db.add_transaction(savings_id, 'Interest', interest_amount, 'Interest', savings.balance)

        # Verify balance increased
        account_data = db.get_account(savings_id)
        assert account_data['balance'] > initial_balance


class TestCreditAccountWorkflow:
    """Test credit account specific workflows."""

    @pytest.mark.integration
    def test_credit_purchase_and_payment_workflow(self, db_with_accounts):
        """Test making purchases and payments on credit account."""
        db, user_id, accounts = db_with_accounts

        credit_id = accounts['credit']['id']
        account_data = db.get_account(credit_id)

        # Create credit account object
        credit = create_account(
            'credit',
            credit_id,
            accounts['credit']['number'],
            "Test User",
            account_data['balance'],
            credit_limit=5000.0
        )

        # Step 1: Make a purchase
        success, message = credit.withdraw(1000.0)
        assert success is True
        assert credit.balance == -1000.0

        db.update_balance(credit_id, credit.balance)
        db.add_transaction(credit_id, 'Credit Purchase', 1000.0, 'Shopping', credit.balance)

        # Step 2: Make another purchase
        success, message = credit.withdraw(500.0)
        assert success is True
        assert credit.balance == -1500.0

        db.update_balance(credit_id, credit.balance)
        db.add_transaction(credit_id, 'Credit Purchase', 500.0, 'Entertainment', credit.balance)

        # Step 3: Make a payment
        success, message = credit.deposit(750.0)
        assert success is True
        assert credit.balance == -750.0

        db.update_balance(credit_id, credit.balance)
        db.add_transaction(credit_id, 'Payment', 750.0, 'Payment', credit.balance)

        # Verify final balance
        account_data = db.get_account(credit_id)
        assert account_data['balance'] == -750.0

        # Verify transaction history
        transactions = db.get_transactions(credit_id)
        assert len(transactions) >= 3


class TestMultiAccountWorkflow:
    """Test workflows involving multiple accounts."""

    @pytest.mark.integration
    def test_managing_multiple_accounts(self, db_with_user):
        """Test user managing multiple accounts simultaneously."""
        db, user_id = db_with_user

        # Create multiple accounts
        checking1_id, checking1_num = db.create_account(user_id, 'checking', 1000.0)
        checking2_id, checking2_num = db.create_account(user_id, 'checking', 2000.0)
        savings_id, savings_num = db.create_account(user_id, 'savings', 5000.0)

        # Verify all accounts exist
        accounts = db.get_user_accounts(user_id)
        assert len(accounts) == 3

        # Perform operations on each account
        db.add_transaction(checking1_id, 'Deposit', 500.0, 'Salary', 1500.0, category='Income')
        db.update_balance(checking1_id, 1500.0)

        db.add_transaction(checking2_id, 'Withdrawal', 200.0, 'Shopping', 1800.0, category='Shopping')
        db.update_balance(checking2_id, 1800.0)

        db.add_transaction(savings_id, 'Deposit', 1000.0, 'Savings', 6000.0, category='Savings')
        db.update_balance(savings_id, 6000.0)

        # Transfer between accounts
        success, message = db.create_transfer(checking1_id, savings_id, 400.0)
        assert success is True

        # Verify final state
        accounts = db.get_user_accounts(user_id)
        total_balance = sum(acc['balance'] for acc in accounts)

        # Total should be: 1500 - 400 + 1800 + 6000 + 400 = 9300
        assert total_balance == 9300.0


class TestDataPersistenceWorkflow:
    """Test data persistence across sessions."""

    @pytest.mark.integration
    @pytest.mark.slow
    def test_data_persists_across_sessions(self, temp_db):
        """Test data persists when database is reopened."""
        # Session 1: Create user and account
        user_id = temp_db.create_user("persist_test", "password", "Persist User", "persist@test.com")
        account_id, account_num = temp_db.create_account(user_id, 'checking', 1000.0)
        temp_db.add_transaction(account_id, 'Deposit', 500.0, 'Salary', 1500.0, category='Income')
        temp_db.update_balance(account_id, 1500.0)  # Update actual account balance

        # Get database path before closing
        db_path = temp_db.conn.execute("PRAGMA database_list").fetchone()[2]

        # Close connection
        temp_db.close()

        # Session 2: Reopen database
        db2 = DatabaseManager(db_path)

        # Verify data persists
        authenticated = db2.authenticate_user("persist_test", "password")
        assert authenticated == user_id

        accounts = db2.get_user_accounts(user_id)
        assert len(accounts) == 1
        assert accounts[0]['balance'] == 1500.0

        transactions = db2.get_transactions(account_id)
        assert len(transactions) >= 1

        db2.close()


class TestErrorHandlingWorkflow:
    """Test error handling in complete workflows."""

    @pytest.mark.integration
    def test_insufficient_funds_workflow(self, db_with_accounts):
        """Test workflow when operations fail due to insufficient funds."""
        db, user_id, accounts = db_with_accounts

        checking_id = accounts['checking']['id']
        savings_id = accounts['savings']['id']

        # Try to transfer more than available
        success, message = db.create_transfer(checking_id, savings_id, 5000.0)

        assert success is False
        assert "insufficient" in message.lower()

        # Verify balances unchanged
        checking = db.get_account(checking_id)
        savings = db.get_account(savings_id)

        assert checking['balance'] == 1000.0
        assert savings['balance'] == 5000.0

    @pytest.mark.integration
    def test_invalid_operation_workflow(self, db_with_accounts):
        """Test workflow with invalid operations."""
        db, user_id, accounts = db_with_accounts

        savings_id = accounts['savings']['id']
        account_data = db.get_account(savings_id)

        # Create savings account
        savings = create_account(
            'savings',
            savings_id,
            accounts['savings']['number'],
            "Test User",
            account_data['balance'],
            interest_rate=2.0
        )

        # Try to withdraw below minimum balance
        success, message = savings.withdraw(4950.0)

        assert success is False
        assert "minimum balance" in message.lower()

        # Verify balance unchanged
        assert savings.balance == 5000.0


class TestReportingWorkflow:
    """Test reporting and analytics workflows."""

    @pytest.mark.integration
    def test_spending_analysis_workflow(self, db_with_accounts):
        """Test analyzing spending patterns."""
        db, user_id, accounts = db_with_accounts

        checking_id = accounts['checking']['id']

        # Add varied spending transactions
        db.add_transaction(checking_id, 'Withdrawal', 100.0, 'Food purchase', 900.0, category='Food & Dining')
        db.add_transaction(checking_id, 'Withdrawal', 150.0, 'Restaurant', 750.0, category='Food & Dining')
        db.add_transaction(checking_id, 'Withdrawal', 75.0, 'Store purchase', 675.0, category='Shopping')
        db.add_transaction(checking_id, 'Withdrawal', 50.0, 'Gas', 625.0, category='Transportation')
        db.add_transaction(checking_id, 'Deposit', 500.0, 'Salary', 1125.0, category='Income')

        # Get statistics
        stats = db.get_account_statistics(checking_id)

        # Note: Account was created with 1000.0 initial deposit, plus 500.0 = 1500.0 total
        assert stats['total_deposits'] == 1500.0
        assert stats['total_withdrawals'] == 375.0
        assert stats['total_transactions'] == 6  # 1 initial + 5 added

        # Get spending by category
        spending = db.get_spending_by_category(checking_id)

        food_spending = next((s for s in spending if s['category'] == 'Food & Dining'), None)
        assert food_spending is not None
        assert food_spending['total'] == 250.0

        # Get transaction history
        transactions = db.get_transactions(checking_id, category='Food & Dining')
        assert len(transactions) == 2
