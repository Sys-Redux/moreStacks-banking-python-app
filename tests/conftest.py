"""
Pytest Configuration and Shared Fixtures
Provides reusable test fixtures for database, accounts, and test data
"""
import pytest
import os
import tempfile
from database.db_manager import DatabaseManager
from models.account import CheckingAccount, SavingsAccount, CreditAccount


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Create temporary database file
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    db = DatabaseManager(path)
    yield db

    # Cleanup
    db.close()
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def db_with_user(temp_db):
    """Create a database with a test user."""
    user_id = temp_db.create_user(
        username="testuser",
        password="testpass123",
        full_name="Test User",
        email="test@example.com"
    )

    return temp_db, user_id


@pytest.fixture
def db_with_accounts(db_with_user):
    """Create a database with user and multiple accounts."""
    db, user_id = db_with_user

    # Create checking account
    checking_id, checking_num = db.create_account(user_id, 'checking', 1000.0)

    # Create savings account
    savings_id, savings_num = db.create_account(user_id, 'savings', 5000.0)

    # Create credit account
    credit_id, credit_num = db.create_account(user_id, 'credit', 0.0)

    accounts = {
        'checking': {'id': checking_id, 'number': checking_num},
        'savings': {'id': savings_id, 'number': savings_num},
        'credit': {'id': credit_id, 'number': credit_num}
    }

    return db, user_id, accounts


@pytest.fixture
def checking_account():
    """Create a test checking account."""
    return CheckingAccount(
        account_id=1,
        account_number="CHK001",
        account_holder="Test User",
        balance=1000.0
    )


@pytest.fixture
def savings_account():
    """Create a test savings account."""
    return SavingsAccount(
        account_id=2,
        account_number="SAV001",
        account_holder="Test User",
        balance=5000.0,
        interest_rate=2.0
    )


@pytest.fixture
def credit_account():
    """Create a test credit account."""
    return CreditAccount(
        account_id=3,
        account_number="CRD001",
        account_holder="Test User",
        balance=0.0,
        credit_limit=5000.0
    )


@pytest.fixture
def sample_transactions():
    """Sample transaction data for testing."""
    return [
        {'type': 'Deposit', 'amount': 500.0, 'category': 'Salary'},
        {'type': 'Withdrawal', 'amount': 100.0, 'category': 'Food & Dining'},
        {'type': 'Withdrawal', 'amount': 50.0, 'category': 'Transportation'},
        {'type': 'Deposit', 'amount': 200.0, 'category': 'Other'},
        {'type': 'Withdrawal', 'amount': 75.0, 'category': 'Shopping'}
    ]
