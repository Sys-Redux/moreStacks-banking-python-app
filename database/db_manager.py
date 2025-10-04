import sqlite3
import hashlib
import os
from datetime import datetime
from typing import Optional, List, Dict, Tuple


class DatabaseManager:
    """Manages all database operations for the moreStacks banking application."""

    def __init__(self, db_path: str = "moreStacks.db"):
        """Initialize database connection and create tables if they don't exist."""
        self.db_path = db_path
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()

    def connect(self):
        """Establish database connection."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Access columns by name
        self.cursor = self.conn.cursor()

    def create_tables(self):
        """Create all necessary database tables."""
        # Users table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
        ''')

        # Accounts table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS accounts (
                account_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                account_number TEXT UNIQUE NOT NULL,
                account_type TEXT NOT NULL,
                balance REAL NOT NULL DEFAULT 0,
                interest_rate REAL DEFAULT 0,
                credit_limit REAL DEFAULT 0,
                status TEXT DEFAULT 'active',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Transactions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                account_id INTEGER NOT NULL,
                transaction_type TEXT NOT NULL,
                amount REAL NOT NULL,
                category TEXT,
                description TEXT,
                balance_after REAL NOT NULL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (account_id) REFERENCES accounts(account_id)
            )
        ''')

        # Transfers table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transfers (
                transfer_id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_account_id INTEGER NOT NULL,
                to_account_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                description TEXT,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_account_id) REFERENCES accounts(account_id),
                FOREIGN KEY (to_account_id) REFERENCES accounts(account_id)
            )
        ''')

        self.conn.commit()

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()

    def create_user(self, username: str, password: str, full_name: str,
                   email: str = None, phone: str = None) -> Optional[int]:
        """Create a new user account."""
        try:
            password_hash = self.hash_password(password)
            self.cursor.execute('''
                INSERT INTO users (username, password_hash, full_name, email, phone)
                VALUES (?, ?, ?, ?, ?)
            ''', (username, password_hash, full_name, email, phone))
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Username already exists

    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        """Authenticate a user and return user_id if successful."""
        password_hash = self.hash_password(password)
        self.cursor.execute('''
            SELECT user_id FROM users
            WHERE username = ? AND password_hash = ?
        ''', (username, password_hash))
        result = self.cursor.fetchone()

        if result:
            user_id = result[0]
            # Update last login
            self.cursor.execute('''
                UPDATE users SET last_login = ? WHERE user_id = ?
            ''', (datetime.now().isoformat(), user_id))
            self.conn.commit()
            return user_id
        return None

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information."""
        self.cursor.execute('''
            SELECT user_id, username, full_name, email, phone, created_at, last_login
            FROM users WHERE user_id = ?
        ''', (user_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def create_account(self, user_id: int, account_type: str,
                      initial_balance: float = 0, interest_rate: float = 0,
                      credit_limit: float = 0) -> Tuple[Optional[int], str]:
        """Create a new bank account for a user."""
        try:
            # Generate unique account number
            account_number = self._generate_account_number()

            self.cursor.execute('''
                INSERT INTO accounts (user_id, account_number, account_type,
                                    balance, interest_rate, credit_limit)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, account_number, account_type, initial_balance,
                 interest_rate, credit_limit))
            self.conn.commit()

            account_id = self.cursor.lastrowid

            # Record initial deposit if balance > 0
            if initial_balance > 0:
                self.add_transaction(account_id, 'Deposit', initial_balance,
                                   'Initial Deposit', initial_balance)

            return account_id, account_number
        except Exception as e:
            return None, str(e)

    def _generate_account_number(self) -> str:
        """Generate a unique account number."""
        import random
        while True:
            account_number = f"{random.randint(1000000000, 9999999999)}"
            self.cursor.execute('''
                SELECT account_id FROM accounts WHERE account_number = ?
            ''', (account_number,))
            if not self.cursor.fetchone():
                return account_number

    def get_user_accounts(self, user_id: int) -> List[Dict]:
        """Get all accounts for a user."""
        self.cursor.execute('''
            SELECT account_id, account_number, account_type, balance,
                   interest_rate, credit_limit, status, created_at
            FROM accounts
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
        ''', (user_id,))
        return [dict(row) for row in self.cursor.fetchall()]

    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get account details."""
        self.cursor.execute('''
            SELECT account_id, user_id, account_number, account_type, balance,
                   interest_rate, credit_limit, status, created_at
            FROM accounts WHERE account_id = ?
        ''', (account_id,))
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def update_balance(self, account_id: int, new_balance: float) -> bool:
        """Update account balance."""
        try:
            self.cursor.execute('''
                UPDATE accounts SET balance = ? WHERE account_id = ?
            ''', (new_balance, account_id))
            self.conn.commit()
            return True
        except Exception:
            return False

    def delete_account(self, account_id: int) -> Tuple[bool, str]:
        """Delete an account and all associated data."""
        try:
            # Check if account exists
            account = self.get_account(account_id)
            if not account:
                return False, "Account not found"

            # Delete associated transactions
            self.cursor.execute('DELETE FROM transactions WHERE account_id = ?', (account_id,))

            # Delete associated transfers
            self.cursor.execute('''
                DELETE FROM transfers
                WHERE from_account_id = ? OR to_account_id = ?
            ''', (account_id, account_id))

            # Delete the account
            self.cursor.execute('DELETE FROM accounts WHERE account_id = ?', (account_id,))

            self.conn.commit()
            return True, "Account deleted successfully"
        except Exception as e:
            self.conn.rollback()
            return False, f"Error deleting account: {str(e)}"

    def add_transaction(self, account_id: int, transaction_type: str,
                       amount: float, description: str, balance_after: float,
                       category: str = None) -> int:
        """Add a transaction record."""
        self.cursor.execute('''
            INSERT INTO transactions (account_id, transaction_type, amount,
                                    category, description, balance_after)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (account_id, transaction_type, amount, category, description, balance_after))
        self.conn.commit()
        return self.cursor.lastrowid

    def get_transactions(self, account_id: int, limit: int = None,
                        category: str = None, start_date: str = None,
                        end_date: str = None) -> List[Dict]:
        """Get transactions for an account with optional filters."""
        query = '''
            SELECT transaction_id, transaction_type, amount, category,
                   description, balance_after, timestamp
            FROM transactions
            WHERE account_id = ?
        '''
        params = [account_id]

        if category:
            query += ' AND category = ?'
            params.append(category)

        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND timestamp <= ?'
            params.append(end_date)

        query += ' ORDER BY timestamp DESC, transaction_id DESC'

        if limit:
            query += f' LIMIT {limit}'

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def create_transfer(self, from_account_id: int, to_account_id: int,
                       amount: float, description: str = None) -> Tuple[bool, str]:
        """Transfer money between accounts."""
        try:
            # Get account balances
            from_account = self.get_account(from_account_id)
            to_account = self.get_account(to_account_id)

            if not from_account or not to_account:
                return False, "Invalid account"

            if from_account['balance'] < amount:
                return False, "Insufficient funds"

            # Update balances
            new_from_balance = from_account['balance'] - amount
            new_to_balance = to_account['balance'] + amount

            self.update_balance(from_account_id, new_from_balance)
            self.update_balance(to_account_id, new_to_balance)

            # Record transfer
            self.cursor.execute('''
                INSERT INTO transfers (from_account_id, to_account_id, amount, description)
                VALUES (?, ?, ?, ?)
            ''', (from_account_id, to_account_id, amount, description))

            # Record transactions
            self.add_transaction(from_account_id, 'Transfer Out', amount,
                               f"Transfer to account {to_account['account_number']}",
                               new_from_balance, 'Transfer')
            self.add_transaction(to_account_id, 'Transfer In', amount,
                               f"Transfer from account {from_account['account_number']}",
                               new_to_balance, 'Transfer')

            self.conn.commit()
            return True, "Transfer successful"
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def get_account_statistics(self, account_id: int) -> Dict:
        """Get statistics for an account."""
        self.cursor.execute('''
            SELECT
                COUNT(*) as total_transactions,
                SUM(CASE WHEN transaction_type = 'Deposit' THEN amount ELSE 0 END) as total_deposits,
                SUM(CASE WHEN transaction_type = 'Withdrawal' THEN amount ELSE 0 END) as total_withdrawals,
                SUM(CASE WHEN transaction_type = 'Transfer In' THEN amount ELSE 0 END) as total_transfers_in,
                SUM(CASE WHEN transaction_type = 'Transfer Out' THEN amount ELSE 0 END) as total_transfers_out
            FROM transactions
            WHERE account_id = ?
        ''', (account_id,))

        result = self.cursor.fetchone()
        return dict(result) if result else {}

    def get_spending_by_category(self, account_id: int,
                                 start_date: str = None) -> List[Dict]:
        """Get spending grouped by category."""
        query = '''
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM transactions
            WHERE account_id = ?
            AND transaction_type IN ('Withdrawal', 'Transfer Out')
            AND category IS NOT NULL
        '''
        params = [account_id]

        if start_date:
            query += ' AND timestamp >= ?'
            params.append(start_date)

        query += ' GROUP BY category ORDER BY total DESC'

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Cleanup database connection."""
        self.close()
