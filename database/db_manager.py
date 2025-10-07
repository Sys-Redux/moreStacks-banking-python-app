import sqlite3
import bcrypt
import os
from datetime import datetime, timedelta
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

    def get_connection(self):
        """
        Get the database connection.

        Returns:
            sqlite3.Connection: The database connection object
        """
        return self.conn

    def create_tables(self):
        """Create all necessary database tables."""
        # Users table
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                full_name TEXT NOT NULL,
                email TEXT,
                phone TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT,
                failed_login_attempts INTEGER DEFAULT 0,
                account_locked_until TEXT
            )
        """
        )

        # Accounts table
        self.cursor.execute(
            """
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
                last_interest_date TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        )

        # Transactions table
        self.cursor.execute(
            """
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
        """
        )

        # Transfers table
        self.cursor.execute(
            """
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
        """
        )

        # Sessions table for session timeout management
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS sessions (
                session_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                session_token TEXT UNIQUE NOT NULL,
                created_at TEXT NOT NULL,
                last_activity TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        )

        # Password history table for password expiration management
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS password_history (
                history_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """
        )

        # TOTP secrets table for Two-Factor Authentication
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS totp_secrets (
                totp_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER UNIQUE NOT NULL,
                secret_key TEXT NOT NULL,
                backup_codes TEXT,
                enabled INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_used TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
            )
        """
        )

        # Audit logs table for Security Audit Trail
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS audit_logs (
                log_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                username TEXT,
                event_type TEXT NOT NULL,
                event_category TEXT NOT NULL,
                description TEXT NOT NULL,
                ip_address TEXT,
                user_agent TEXT,
                severity TEXT NOT NULL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE SET NULL
            )
        """
        )

        # Create indexes for audit logs performance
        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_user_id ON audit_logs(user_id)
        """
        )
        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_event_type ON audit_logs(event_type)
        """
        )
        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_severity ON audit_logs(severity)
        """
        )
        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_created_at ON audit_logs(created_at)
        """
        )
        self.cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_audit_category ON audit_logs(event_category)
        """
        )

        self.conn.commit()
        self._migrate_existing_tables()

    def _migrate_existing_tables(self):
        """Add new columns to existing tables if they don't exist."""
        try:
            # Check if failed_login_attempts column exists in users table
            self.cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in self.cursor.fetchall()]

            if "failed_login_attempts" not in columns:
                self.cursor.execute(
                    """
                    ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0
                """
                )

            if "account_locked_until" not in columns:
                self.cursor.execute(
                    """
                    ALTER TABLE users ADD COLUMN account_locked_until TEXT
                """
                )

            if "password_changed_at" not in columns:
                self.cursor.execute(
                    """
                    ALTER TABLE users ADD COLUMN password_changed_at TEXT DEFAULT CURRENT_TIMESTAMP
                """
                )

            if "totp_enabled" not in columns:
                self.cursor.execute(
                    """
                    ALTER TABLE users ADD COLUMN totp_enabled INTEGER DEFAULT 0
                """
                )

            # Check if last_interest_date column exists in accounts table
            self.cursor.execute("PRAGMA table_info(accounts)")
            columns = [column[1] for column in self.cursor.fetchall()]

            if "last_interest_date" not in columns:
                self.cursor.execute(
                    """
                    ALTER TABLE accounts ADD COLUMN last_interest_date TEXT
                """
                )

            self.conn.commit()
        except Exception as e:
            # Columns already exist or other error
            pass

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password as a string
        """
        # Generate salt and hash password
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """
        Verify a password against a hashed password.

        Args:
            password: Plain text password to verify
            hashed_password: Hashed password to verify against

        Returns:
            True if password matches, False otherwise
        """
        try:
            return bcrypt.checkpw(
                password.encode("utf-8"), hashed_password.encode("utf-8")
            )
        except Exception:
            return False

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        email: str = None,
        phone: str = None,
    ) -> Optional[int]:
        """Create a new user account."""
        try:
            password_hash = self.hash_password(password)
            self.cursor.execute(
                """
                INSERT INTO users (username, password_hash, full_name, email, phone)
                VALUES (?, ?, ?, ?, ?)
            """,
                (username, password_hash, full_name, email, phone),
            )
            self.conn.commit()
            return self.cursor.lastrowid
        except sqlite3.IntegrityError:
            return None  # Username already exists

    def authenticate_user(self, username: str, password: str) -> Optional[int]:
        """
        Authenticate a user and return user_id if successful.
        Implements account lockout after 5 failed attempts (15 minute lockout).

        Args:
            username: User's username
            password: User's plain text password

        Returns:
            user_id if authentication successful, None otherwise
        """
        # Get user data including lockout information
        self.cursor.execute(
            """
            SELECT user_id, password_hash, failed_login_attempts, account_locked_until
            FROM users
            WHERE username = ?
        """,
            (username,),
        )
        result = self.cursor.fetchone()

        if not result:
            return None  # User not found

        user_id, password_hash, failed_attempts, locked_until = result

        # Check if account is locked
        if locked_until:
            lockout_time = datetime.fromisoformat(locked_until)
            if datetime.now() < lockout_time:
                # Account is still locked
                return None
            else:
                # Lockout period expired, reset counters
                self.cursor.execute(
                    """
                    UPDATE users
                    SET failed_login_attempts = 0, account_locked_until = NULL
                    WHERE user_id = ?
                """,
                    (user_id,),
                )
                self.conn.commit()
                failed_attempts = 0

        # Verify password using bcrypt
        if self.verify_password(password, password_hash):
            # Successful login - reset failed attempts and update last login
            self.cursor.execute(
                """
                UPDATE users
                SET last_login = ?, failed_login_attempts = 0, account_locked_until = NULL
                WHERE user_id = ?
            """,
                (datetime.now().isoformat(), user_id),
            )
            self.conn.commit()
            return user_id
        else:
            # Failed login - increment counter
            failed_attempts += 1

            if failed_attempts >= 5:
                # Lock account for 15 minutes
                lockout_until = datetime.now() + timedelta(minutes=15)
                self.cursor.execute(
                    """
                    UPDATE users
                    SET failed_login_attempts = ?, account_locked_until = ?
                    WHERE user_id = ?
                """,
                    (failed_attempts, lockout_until.isoformat(), user_id),
                )
            else:
                # Just increment failed attempts
                self.cursor.execute(
                    """
                    UPDATE users
                    SET failed_login_attempts = ?
                    WHERE user_id = ?
                """,
                    (failed_attempts, user_id),
                )

            self.conn.commit()
            return None

    def is_account_locked(self, username: str) -> Tuple[bool, Optional[datetime]]:
        """
        Check if a user account is locked.

        Args:
            username: User's username

        Returns:
            Tuple of (is_locked, unlock_time)
        """
        self.cursor.execute(
            """
            SELECT account_locked_until, failed_login_attempts
            FROM users
            WHERE username = ?
        """,
            (username,),
        )
        result = self.cursor.fetchone()

        if not result:
            return False, None

        locked_until, failed_attempts = result

        if not locked_until:
            return False, None

        lockout_time = datetime.fromisoformat(locked_until)
        if datetime.now() < lockout_time:
            return True, lockout_time

        return False, None

    def get_user_info(self, user_id: int) -> Optional[Dict]:
        """Get user information."""
        self.cursor.execute(
            """
            SELECT user_id, username, full_name, email, phone, created_at, last_login
            FROM users WHERE user_id = ?
        """,
            (user_id,),
        )
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def create_account(
        self,
        user_id: int,
        account_type: str,
        initial_balance: float = 0,
        interest_rate: float = 0,
        credit_limit: float = 0,
    ) -> Tuple[Optional[int], str]:
        """Create a new bank account for a user."""
        try:
            # Generate unique account number
            account_number = self._generate_account_number()

            self.cursor.execute(
                """
                INSERT INTO accounts (user_id, account_number, account_type,
                                    balance, interest_rate, credit_limit)
                VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    account_number,
                    account_type,
                    initial_balance,
                    interest_rate,
                    credit_limit,
                ),
            )
            self.conn.commit()

            account_id = self.cursor.lastrowid

            # Record initial deposit if balance > 0
            if initial_balance > 0:
                self.add_transaction(
                    account_id,
                    "Deposit",
                    initial_balance,
                    "Initial Deposit",
                    initial_balance,
                )

            return account_id, account_number
        except Exception as e:
            return None, str(e)

    def _generate_account_number(self) -> str:
        """Generate a unique account number."""
        import random

        while True:
            account_number = f"{random.randint(1000000000, 9999999999)}"
            self.cursor.execute(
                """
                SELECT account_id FROM accounts WHERE account_number = ?
            """,
                (account_number,),
            )
            if not self.cursor.fetchone():
                return account_number

    def get_user_accounts(self, user_id: int) -> List[Dict]:
        """Get all accounts for a user."""
        self.cursor.execute(
            """
            SELECT account_id, account_number, account_type, balance,
                   interest_rate, credit_limit, status, created_at
            FROM accounts
            WHERE user_id = ? AND status = 'active'
            ORDER BY created_at DESC
        """,
            (user_id,),
        )
        return [dict(row) for row in self.cursor.fetchall()]

    def get_account(self, account_id: int) -> Optional[Dict]:
        """Get account details."""
        self.cursor.execute(
            """
            SELECT account_id, user_id, account_number, account_type, balance,
                   interest_rate, credit_limit, status, created_at, last_interest_date
            FROM accounts WHERE account_id = ?
        """,
            (account_id,),
        )
        result = self.cursor.fetchone()
        return dict(result) if result else None

    def update_balance(self, account_id: int, new_balance: float) -> bool:
        """Update account balance."""
        try:
            self.cursor.execute(
                """
                UPDATE accounts SET balance = ? WHERE account_id = ?
            """,
                (new_balance, account_id),
            )
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
            self.cursor.execute(
                "DELETE FROM transactions WHERE account_id = ?", (account_id,)
            )

            # Delete associated transfers
            self.cursor.execute(
                """
                DELETE FROM transfers
                WHERE from_account_id = ? OR to_account_id = ?
            """,
                (account_id, account_id),
            )

            # Delete the account
            self.cursor.execute(
                "DELETE FROM accounts WHERE account_id = ?", (account_id,)
            )

            self.conn.commit()
            return True, "Account deleted successfully"
        except Exception as e:
            self.conn.rollback()
            return False, f"Error deleting account: {str(e)}"

    def add_transaction(
        self,
        account_id: int,
        transaction_type: str,
        amount: float,
        description: str,
        balance_after: float,
        category: str = None,
    ) -> int:
        """Add a transaction record."""
        self.cursor.execute(
            """
            INSERT INTO transactions (account_id, transaction_type, amount,
                                    category, description, balance_after)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (
                account_id,
                transaction_type,
                amount,
                category,
                description,
                balance_after,
            ),
        )
        self.conn.commit()
        return self.cursor.lastrowid

    def get_transactions(
        self,
        account_id: int,
        limit: int = None,
        category: str = None,
        start_date: str = None,
        end_date: str = None,
    ) -> List[Dict]:
        """Get transactions for an account with optional filters."""
        query = """
            SELECT transaction_id, transaction_type, amount, category,
                   description, balance_after, timestamp
            FROM transactions
            WHERE account_id = ?
        """
        params = [account_id]

        if category:
            query += " AND category = ?"
            params.append(category)

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC, transaction_id DESC"

        if limit:
            query += f" LIMIT {limit}"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def create_transfer(
        self,
        from_account_id: int,
        to_account_id: int,
        amount: float,
        description: str = None,
    ) -> Tuple[bool, str]:
        """Transfer money between accounts."""
        try:
            # Get account balances
            from_account = self.get_account(from_account_id)
            to_account = self.get_account(to_account_id)

            if not from_account or not to_account:
                return False, "Invalid account"

            if from_account["balance"] < amount:
                return False, "Insufficient funds"

            # Update balances
            new_from_balance = from_account["balance"] - amount
            new_to_balance = to_account["balance"] + amount

            self.update_balance(from_account_id, new_from_balance)
            self.update_balance(to_account_id, new_to_balance)

            # Record transfer
            self.cursor.execute(
                """
                INSERT INTO transfers (from_account_id, to_account_id, amount, description)
                VALUES (?, ?, ?, ?)
            """,
                (from_account_id, to_account_id, amount, description),
            )

            # Record transactions
            self.add_transaction(
                from_account_id,
                "Transfer Out",
                amount,
                f"Transfer to account {to_account['account_number']}",
                new_from_balance,
                "Transfer",
            )
            self.add_transaction(
                to_account_id,
                "Transfer In",
                amount,
                f"Transfer from account {from_account['account_number']}",
                new_to_balance,
                "Transfer",
            )

            self.conn.commit()
            return True, "Transfer successful"
        except Exception as e:
            self.conn.rollback()
            return False, str(e)

    def get_account_statistics(self, account_id: int) -> Dict:
        """Get statistics for an account."""
        self.cursor.execute(
            """
            SELECT
                COUNT(*) as total_transactions,
                SUM(CASE WHEN transaction_type = 'Deposit' THEN amount ELSE 0 END) as total_deposits,
                SUM(CASE WHEN transaction_type = 'Withdrawal' THEN amount ELSE 0 END) as total_withdrawals,
                SUM(CASE WHEN transaction_type = 'Transfer In' THEN amount ELSE 0 END) as total_transfers_in,
                SUM(CASE WHEN transaction_type = 'Transfer Out' THEN amount ELSE 0 END) as total_transfers_out
            FROM transactions
            WHERE account_id = ?
        """,
            (account_id,),
        )

        result = self.cursor.fetchone()
        return dict(result) if result else {}

    def get_spending_by_category(
        self, account_id: int, start_date: str = None
    ) -> List[Dict]:
        """Get spending grouped by category."""
        query = """
            SELECT category, SUM(amount) as total, COUNT(*) as count
            FROM transactions
            WHERE account_id = ?
            AND transaction_type IN ('Withdrawal', 'Transfer Out')
            AND category IS NOT NULL
        """
        params = [account_id]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        query += " GROUP BY category ORDER BY total DESC"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    def update_last_interest_date(self, account_id: int, date: str = None) -> bool:
        """
        Update the last interest application date for an account.

        Args:
            account_id: ID of the account
            date: ISO format date string (defaults to now)

        Returns:
            True if successful, False otherwise
        """
        try:
            if date is None:
                date = datetime.now().isoformat()

            self.cursor.execute(
                """
                UPDATE accounts SET last_interest_date = ? WHERE account_id = ?
            """,
                (date, account_id),
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def get_savings_accounts_for_interest(self, user_id: int = None) -> List[Dict]:
        """
        Get all savings accounts that may be eligible for interest.

        Args:
            user_id: Optional user ID to filter by specific user

        Returns:
            List of account dictionaries with interest information
        """
        query = """
            SELECT account_id, user_id, account_number, balance,
                   interest_rate, last_interest_date, created_at
            FROM accounts
            WHERE account_type = 'Savings' AND status = 'active'
        """
        params = []

        if user_id:
            query += " AND user_id = ?"
            params.append(user_id)

        query += " ORDER BY last_interest_date ASC NULLS FIRST"

        self.cursor.execute(query, params)
        return [dict(row) for row in self.cursor.fetchall()]

    # ============================================================================
    # Session Management Methods
    # ============================================================================

    def create_session(
        self, user_id: int, session_token: str, created_at: str, expires_at: str
    ) -> bool:
        """
        Create a new session record in the database.

        Args:
            user_id: ID of the user
            session_token: Unique session token
            created_at: ISO format timestamp
            expires_at: ISO format timestamp

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO sessions (user_id, session_token, created_at,
                                    last_activity, expires_at)
                VALUES (?, ?, ?, ?, ?)
            """,
                (user_id, session_token, created_at, created_at, expires_at),
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def get_session(self, session_token: str) -> Optional[Dict]:
        """
        Retrieve session information by token.

        Args:
            session_token: Session token to look up

        Returns:
            Session dictionary or None if not found
        """
        try:
            self.cursor.execute(
                """
                SELECT session_id, user_id, session_token, created_at,
                       last_activity, expires_at
                FROM sessions
                WHERE session_token = ?
            """,
                (session_token,),
            )
            row = self.cursor.fetchone()
            return dict(row) if row else None
        except Exception:
            return None

    def update_session_activity(
        self, session_token: str, last_activity: str, expires_at: str
    ) -> bool:
        """
        Update session activity timestamp and expiration.

        Args:
            session_token: Session token to update
            last_activity: New activity timestamp (ISO format)
            expires_at: New expiration timestamp (ISO format)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                UPDATE sessions
                SET last_activity = ?, expires_at = ?
                WHERE session_token = ?
            """,
                (last_activity, expires_at, session_token),
            )
            self.conn.commit()
            return self.cursor.rowcount > 0
        except Exception:
            return False

    def delete_session(self, session_token: str) -> bool:
        """
        Delete a session from the database.

        Args:
            session_token: Session token to delete

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                DELETE FROM sessions WHERE session_token = ?
            """,
                (session_token,),
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def delete_user_sessions(self, user_id: int) -> bool:
        """
        Delete all sessions for a specific user.

        Args:
            user_id: User ID to delete sessions for

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                DELETE FROM sessions WHERE user_id = ?
            """,
                (user_id,),
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def cleanup_expired_sessions(self, current_time: str) -> int:
        """
        Delete all expired sessions from the database.

        Args:
            current_time: Current timestamp (ISO format)

        Returns:
            Number of sessions deleted
        """
        try:
            self.cursor.execute(
                """
                DELETE FROM sessions WHERE expires_at < ?
            """,
                (current_time,),
            )
            self.conn.commit()
            return self.cursor.rowcount
        except Exception:
            return 0

    # ============================================================================
    # Password History & Expiration Methods
    # ============================================================================

    def add_password_to_history(self, user_id: int, password_hash: str) -> bool:
        """
        Add a password to the user's password history.

        Args:
            user_id: ID of the user
            password_hash: Hashed password to store

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO password_history (user_id, password_hash, created_at)
                VALUES (?, ?, ?)
            """,
                (user_id, password_hash, datetime.now().isoformat()),
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def get_password_history(self, user_id: int, limit: int = 5) -> List[Dict]:
        """
        Get the user's password history (most recent first).

        Args:
            user_id: ID of the user
            limit: Maximum number of passwords to return (default: 5)

        Returns:
            List of password history dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT history_id, user_id, password_hash, created_at
                FROM password_history
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            """,
                (user_id, limit),
            )
            return [dict(row) for row in self.cursor.fetchall()]
        except Exception:
            return []

    def check_password_reuse(
        self, user_id: int, new_password: str, history_count: int = 5
    ) -> Tuple[bool, str]:
        """
        Check if a new password has been used recently.

        Args:
            user_id: ID of the user
            new_password: Plain text password to check
            history_count: Number of previous passwords to check (default: 5)

        Returns:
            Tuple of (is_reused, message)
        """
        try:
            history = self.get_password_history(user_id, history_count)

            for entry in history:
                if self.verify_password(new_password, entry["password_hash"]):
                    return (
                        True,
                        f"Password has been used recently. Please choose a different password.",
                    )  # Password was used before

            return (
                False,
                "Password is acceptable and not recently used.",
            )  # Password is new
        except Exception as e:
            return (False, f"Error checking password history: {str(e)}")

    def update_password_changed_date(
        self, user_id: int, changed_at: str = None
    ) -> bool:
        """
        Update the password_changed_at timestamp for a user.

        Args:
            user_id: ID of the user
            changed_at: ISO format timestamp (defaults to now)

        Returns:
            True if successful, False otherwise
        """
        try:
            if changed_at is None:
                changed_at = datetime.now().isoformat()

            self.cursor.execute(
                """
                UPDATE users SET password_changed_at = ? WHERE user_id = ?
            """,
                (changed_at, user_id),
            )
            self.conn.commit()
            return True
        except Exception:
            return False

    def get_password_changed_date(self, user_id: int) -> Optional[str]:
        """
        Get the date when the user's password was last changed.

        Args:
            user_id: ID of the user

        Returns:
            ISO format timestamp or None if not found
        """
        try:
            self.cursor.execute(
                """
                SELECT password_changed_at FROM users WHERE user_id = ?
            """,
                (user_id,),
            )
            result = self.cursor.fetchone()
            return result["password_changed_at"] if result else None
        except Exception:
            return None

    def change_user_password(
        self,
        user_identifier,
        old_password: str,
        new_password: str,
        history_count: int = 5,
    ) -> Tuple[bool, str]:
        """
        Change a user's password with validation.

        Validates old password, checks password history for reuse,
        updates password hash, adds to history, and updates change date.

        Args:
            user_identifier: User ID (int) or username (str)
            old_password: Current password (plain text)
            new_password: New password (plain text)
            history_count: Number of previous passwords to check (default: 5)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Handle both user_id (int) and username (str)
            if isinstance(user_identifier, str):
                # It's a username, authenticate to get user_id
                user_id = self.authenticate_user(user_identifier, old_password)
                if not user_id:
                    return (False, "Current password is incorrect")
            else:
                # It's a user_id
                user_id = user_identifier

            # Get current password hash
            self.cursor.execute(
                """
                SELECT password_hash FROM users WHERE user_id = ?
            """,
                (user_id,),
            )
            result = self.cursor.fetchone()

            if not result:
                return (False, "User not found")

            # Verify old password (only if we didn't already authenticate via username)
            if not isinstance(user_identifier, str):
                if not self.verify_password(old_password, result["password_hash"]):
                    return (False, "Current password is incorrect")

            # Check if new password was used recently
            is_reused, reuse_message = self.check_password_reuse(
                user_id, new_password, history_count
            )
            if is_reused:
                return (False, reuse_message)

            # Hash new password
            new_hash = self.hash_password(new_password)

            # Update password
            self.cursor.execute(
                """
                UPDATE users SET password_hash = ?, password_changed_at = ?
                WHERE user_id = ?
            """,
                (new_hash, datetime.now().isoformat(), user_id),
            )

            # Add old password to history
            self.add_password_to_history(user_id, result["password_hash"])

            self.conn.commit()
            return (True, "Password changed successfully")

        except Exception as e:
            return (False, f"Error changing password: {str(e)}")

    def change_user_password_by_username(
        self,
        username: str,
        old_password: str,
        new_password: str,
        history_count: int = 5,
    ) -> Tuple[bool, str]:
        """
        Change a user's password using username instead of user_id.

        Args:
            username: Username of the user
            old_password: Current password (plain text)
            new_password: New password (plain text)
            history_count: Number of previous passwords to check (default: 5)

        Returns:
            Tuple of (success, message)
        """
        try:
            # Get user_id from username
            user_id = self.authenticate_user(username, old_password)

            if not user_id:
                return (False, "Current password is incorrect")

            # Call the main change_user_password method
            return self.change_user_password(
                user_id, old_password, new_password, history_count
            )

        except Exception as e:
            return (False, f"Error changing password: {str(e)}")

    # ==================== Two-Factor Authentication Methods ====================

    def enable_2fa(
        self, user_id: int, secret_key: str, backup_codes: List[str]
    ) -> Tuple[bool, str]:
        """
        Enable Two-Factor Authentication for a user.

        Args:
            user_id: ID of the user
            secret_key: Base32-encoded TOTP secret
            backup_codes: List of backup codes (will be stored as JSON)

        Returns:
            Tuple of (success, message)
        """
        try:
            import json

            # Store backup codes as JSON string
            backup_codes_json = json.dumps(backup_codes)

            # Check if user already has 2FA record
            self.cursor.execute(
                """
                SELECT totp_id FROM totp_secrets WHERE user_id = ?
            """,
                (user_id,),
            )
            existing = self.cursor.fetchone()

            if existing:
                # Update existing record
                self.cursor.execute(
                    """
                    UPDATE totp_secrets
                    SET secret_key = ?, backup_codes = ?, enabled = 1,
                        created_at = CURRENT_TIMESTAMP
                    WHERE user_id = ?
                """,
                    (secret_key, backup_codes_json, user_id),
                )
            else:
                # Insert new record
                self.cursor.execute(
                    """
                    INSERT INTO totp_secrets (user_id, secret_key, backup_codes, enabled)
                    VALUES (?, ?, ?, 1)
                """,
                    (user_id, secret_key, backup_codes_json),
                )

            # Update user table
            self.cursor.execute(
                """
                UPDATE users SET totp_enabled = 1 WHERE user_id = ?
            """,
                (user_id,),
            )

            self.conn.commit()
            return (True, "Two-Factor Authentication enabled successfully")

        except Exception as e:
            return (False, f"Error enabling 2FA: {str(e)}")

    def disable_2fa(self, user_id: int) -> Tuple[bool, str]:
        """
        Disable Two-Factor Authentication for a user.

        Args:
            user_id: ID of the user

        Returns:
            Tuple of (success, message)
        """
        try:
            # Update totp_secrets table
            self.cursor.execute(
                """
                UPDATE totp_secrets SET enabled = 0 WHERE user_id = ?
            """,
                (user_id,),
            )

            # Update user table
            self.cursor.execute(
                """
                UPDATE users SET totp_enabled = 0 WHERE user_id = ?
            """,
                (user_id,),
            )

            self.conn.commit()
            return (True, "Two-Factor Authentication disabled successfully")

        except Exception as e:
            return (False, f"Error disabling 2FA: {str(e)}")

    def is_2fa_enabled(self, user_id: int) -> bool:
        """
        Check if Two-Factor Authentication is enabled for a user.

        Args:
            user_id: ID of the user

        Returns:
            True if 2FA is enabled, False otherwise
        """
        try:
            self.cursor.execute(
                """
                SELECT enabled FROM totp_secrets WHERE user_id = ?
            """,
                (user_id,),
            )
            result = self.cursor.fetchone()

            if result and result["enabled"] == 1:
                return True

            # Also check user table as backup
            self.cursor.execute(
                """
                SELECT totp_enabled FROM users WHERE user_id = ?
            """,
                (user_id,),
            )
            user_result = self.cursor.fetchone()

            return user_result and user_result["totp_enabled"] == 1

        except Exception:
            return False

    def get_2fa_secret(self, user_id: int) -> Optional[str]:
        """
        Get the TOTP secret key for a user.

        Args:
            user_id: ID of the user

        Returns:
            TOTP secret key or None if not found
        """
        try:
            self.cursor.execute(
                """
                SELECT secret_key FROM totp_secrets
                WHERE user_id = ? AND enabled = 1
            """,
                (user_id,),
            )
            result = self.cursor.fetchone()

            return result["secret_key"] if result else None

        except Exception:
            return None

    def get_backup_codes(self, user_id: int) -> List[str]:
        """
        Get backup codes for a user.

        Args:
            user_id: ID of the user

        Returns:
            List of backup codes or empty list if not found
        """
        try:
            import json

            self.cursor.execute(
                """
                SELECT backup_codes FROM totp_secrets
                WHERE user_id = ? AND enabled = 1
            """,
                (user_id,),
            )
            result = self.cursor.fetchone()

            if result and result["backup_codes"]:
                return json.loads(result["backup_codes"])

            return []

        except Exception:
            return []

    def use_backup_code(self, user_id: int, used_code: str) -> Tuple[bool, str]:
        """
        Mark a backup code as used by removing it from the list.

        Args:
            user_id: ID of the user
            used_code: The backup code that was used

        Returns:
            Tuple of (success, message)
        """
        try:
            import json

            # Get current backup codes
            current_codes = self.get_backup_codes(user_id)

            if used_code not in current_codes:
                return (False, "Invalid backup code")

            # Remove the used code
            current_codes.remove(used_code)

            # Update database
            backup_codes_json = json.dumps(current_codes)
            self.cursor.execute(
                """
                UPDATE totp_secrets
                SET backup_codes = ?, last_used = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """,
                (backup_codes_json, user_id),
            )

            self.conn.commit()

            remaining = len(current_codes)
            return (True, f"Backup code accepted. {remaining} backup codes remaining.")

        except Exception as e:
            return (False, f"Error using backup code: {str(e)}")

    def update_2fa_last_used(self, user_id: int) -> bool:
        """
        Update the last used timestamp for 2FA.

        Args:
            user_id: ID of the user

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                UPDATE totp_secrets
                SET last_used = CURRENT_TIMESTAMP
                WHERE user_id = ?
            """,
                (user_id,),
            )

            self.conn.commit()
            return True

        except Exception:
            return False

    def get_2fa_status(self, user_id: int) -> Dict[str, any]:
        """
        Get comprehensive 2FA status for a user.

        Args:
            user_id: ID of the user

        Returns:
            Dictionary with 2FA status information
        """
        try:
            self.cursor.execute(
                """
                SELECT enabled, created_at, last_used
                FROM totp_secrets
                WHERE user_id = ?
            """,
                (user_id,),
            )
            result = self.cursor.fetchone()

            if result:
                backup_codes = self.get_backup_codes(user_id)
                return {
                    "enabled": result["enabled"] == 1,
                    "created_at": result["created_at"],
                    "last_used": result["last_used"],
                    "backup_codes_remaining": len(backup_codes),
                    "has_backup_codes": len(backup_codes) > 0,
                }

            return {
                "enabled": False,
                "created_at": None,
                "last_used": None,
                "backup_codes_remaining": 0,
                "has_backup_codes": False,
            }

        except Exception:
            return {
                "enabled": False,
                "created_at": None,
                "last_used": None,
                "backup_codes_remaining": 0,
                "has_backup_codes": False,
            }

    def regenerate_backup_codes(
        self, user_id: int, new_backup_codes: List[str]
    ) -> Tuple[bool, str]:
        """
        Regenerate backup codes for a user.

        Args:
            user_id: ID of the user
            new_backup_codes: New list of backup codes

        Returns:
            Tuple of (success, message)
        """
        try:
            import json

            # Check if 2FA is enabled
            if not self.is_2fa_enabled(user_id):
                return (False, "2FA is not enabled for this user")

            # Update backup codes
            backup_codes_json = json.dumps(new_backup_codes)
            self.cursor.execute(
                """
                UPDATE totp_secrets
                SET backup_codes = ?
                WHERE user_id = ?
            """,
                (backup_codes_json, user_id),
            )

            self.conn.commit()
            return (True, f"Generated {len(new_backup_codes)} new backup codes")

        except Exception as e:
            return (False, f"Error regenerating backup codes: {str(e)}")

    # ==================== End of 2FA Methods ====================

    # ==================== Audit Log Methods ====================

    def create_audit_log(
        self,
        event_type: str,
        event_category: str,
        description: str,
        severity: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[str] = None,
    ) -> bool:
        """
        Create a new audit log entry.

        Args:
            event_type: Type of event
            event_category: Category of event
            description: Description of the event
            severity: Severity level (INFO, WARNING, CRITICAL)
            user_id: User ID (optional)
            username: Username (optional)
            ip_address: IP address (optional)
            user_agent: User agent string (optional)
            metadata: JSON metadata (optional)

        Returns:
            True if successful, False otherwise
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO audit_logs (
                    user_id, username, event_type, event_category,
                    description, ip_address, user_agent, severity, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    user_id,
                    username,
                    event_type,
                    event_category,
                    description,
                    ip_address,
                    user_agent,
                    severity,
                    metadata,
                ),
            )
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Error creating audit log: {e}")
            return False

    def get_audit_logs_by_user(
        self, user_id: int, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        Get audit logs for a specific user.

        Args:
            user_id: User ID
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT log_id, user_id, username, event_type, event_category,
                       description, ip_address, user_agent, severity, metadata, created_at
                FROM audit_logs
                WHERE user_id = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (user_id, limit, offset),
            )

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching user audit logs: {e}")
            return []

    def get_audit_logs_by_date_range(
        self, start_date: str, end_date: str, limit: int = 1000, offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        Get audit logs within a date range.

        Args:
            start_date: Start date (ISO format)
            end_date: End date (ISO format)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT log_id, user_id, username, event_type, event_category,
                       description, ip_address, user_agent, severity, metadata, created_at
                FROM audit_logs
                WHERE created_at BETWEEN ? AND ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (start_date, end_date, limit, offset),
            )

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching audit logs by date range: {e}")
            return []

    def get_audit_logs_by_type(
        self, event_type: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        Get audit logs by event type.

        Args:
            event_type: Event type to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT log_id, user_id, username, event_type, event_category,
                       description, ip_address, user_agent, severity, metadata, created_at
                FROM audit_logs
                WHERE event_type = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (event_type, limit, offset),
            )

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching audit logs by type: {e}")
            return []

    def get_audit_logs_by_category(
        self, category: str, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        Get audit logs by category.

        Args:
            category: Category to filter by
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log dictionaries
        """
        try:
            self.cursor.execute(
                """
                SELECT log_id, user_id, username, event_type, event_category,
                       description, ip_address, user_agent, severity, metadata, created_at
                FROM audit_logs
                WHERE event_category = ?
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
            """,
                (category, limit, offset),
            )

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching audit logs by category: {e}")
            return []

    def get_security_events(
        self, severity: Optional[str] = None, limit: int = 100, offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        Get security-related audit logs.

        Args:
            severity: Filter by severity (INFO, WARNING, CRITICAL)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log dictionaries
        """
        try:
            if severity:
                self.cursor.execute(
                    """
                    SELECT log_id, user_id, username, event_type, event_category,
                           description, ip_address, user_agent, severity, metadata, created_at
                    FROM audit_logs
                    WHERE event_category = 'SECURITY' AND severity = ?
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """,
                    (severity, limit, offset),
                )
            else:
                self.cursor.execute(
                    """
                    SELECT log_id, user_id, username, event_type, event_category,
                           description, ip_address, user_agent, severity, metadata, created_at
                    FROM audit_logs
                    WHERE event_category = 'SECURITY'
                    ORDER BY created_at DESC
                    LIMIT ? OFFSET ?
                """,
                    (limit, offset),
                )

            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error fetching security events: {e}")
            return []

    def search_audit_logs(
        self, filters: Dict[str, any], limit: int = 100, offset: int = 0
    ) -> List[Dict[str, any]]:
        """
        Search audit logs with multiple filters.

        Args:
            filters: Dictionary of filter criteria
                - user_id: int
                - username: str
                - event_type: str
                - event_category: str
                - severity: str
                - start_date: str (ISO format)
                - end_date: str (ISO format)
            limit: Maximum number of records to return
            offset: Number of records to skip

        Returns:
            List of audit log dictionaries
        """
        try:
            query = """
                SELECT log_id, user_id, username, event_type, event_category,
                       description, ip_address, user_agent, severity, metadata, created_at
                FROM audit_logs
                WHERE 1=1
            """
            params = []

            if "user_id" in filters and filters["user_id"]:
                query += " AND user_id = ?"
                params.append(filters["user_id"])

            if "username" in filters and filters["username"]:
                query += " AND username LIKE ?"
                params.append(f"%{filters['username']}%")

            if "event_type" in filters and filters["event_type"]:
                query += " AND event_type = ?"
                params.append(filters["event_type"])

            if "event_category" in filters and filters["event_category"]:
                query += " AND event_category = ?"
                params.append(filters["event_category"])

            if "severity" in filters and filters["severity"]:
                query += " AND severity = ?"
                params.append(filters["severity"])

            if "start_date" in filters and filters["start_date"]:
                query += " AND created_at >= ?"
                params.append(filters["start_date"])

            if "end_date" in filters and filters["end_date"]:
                query += " AND created_at <= ?"
                params.append(filters["end_date"])

            query += " ORDER BY created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            self.cursor.execute(query, params)
            rows = self.cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error searching audit logs: {e}")
            return []

    def get_audit_log_count(self, filters: Optional[Dict[str, any]] = None) -> int:
        """
        Get total count of audit logs matching filters.

        Args:
            filters: Optional dictionary of filter criteria

        Returns:
            Total count of matching records
        """
        try:
            if not filters:
                self.cursor.execute("SELECT COUNT(*) FROM audit_logs")
                return self.cursor.fetchone()[0]

            query = "SELECT COUNT(*) FROM audit_logs WHERE 1=1"
            params = []

            if "user_id" in filters and filters["user_id"]:
                query += " AND user_id = ?"
                params.append(filters["user_id"])

            if "event_type" in filters and filters["event_type"]:
                query += " AND event_type = ?"
                params.append(filters["event_type"])

            if "event_category" in filters and filters["event_category"]:
                query += " AND event_category = ?"
                params.append(filters["event_category"])

            if "severity" in filters and filters["severity"]:
                query += " AND severity = ?"
                params.append(filters["severity"])

            if "start_date" in filters and filters["start_date"]:
                query += " AND created_at >= ?"
                params.append(filters["start_date"])

            if "end_date" in filters and filters["end_date"]:
                query += " AND created_at <= ?"
                params.append(filters["end_date"])

            self.cursor.execute(query, params)
            return self.cursor.fetchone()[0]
        except Exception:
            return 0

    def export_audit_logs_csv(
        self, filepath: str, filters: Optional[Dict[str, any]] = None
    ) -> Tuple[bool, str]:
        """
        Export audit logs to CSV file.

        Args:
            filepath: Path to save CSV file
            filters: Optional dictionary of filter criteria

        Returns:
            Tuple of (success, message)
        """
        try:
            import csv

            logs = self.search_audit_logs(filters or {}, limit=100000)

            if not logs:
                return (False, "No logs found to export")

            with open(filepath, "w", newline="", encoding="utf-8") as csvfile:
                fieldnames = [
                    "log_id",
                    "created_at",
                    "user_id",
                    "username",
                    "event_type",
                    "event_category",
                    "severity",
                    "description",
                    "ip_address",
                    "user_agent",
                    "metadata",
                ]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

                writer.writeheader()
                for log in logs:
                    writer.writerow(log)

            return (True, f"Exported {len(logs)} audit logs to {filepath}")
        except Exception as e:
            return (False, f"Error exporting audit logs: {str(e)}")

    def delete_old_audit_logs(
        self, days_old: int = 90, keep_critical: bool = True
    ) -> Tuple[bool, str]:
        """
        Delete audit logs older than specified days.

        Args:
            days_old: Number of days to keep
            keep_critical: Whether to keep CRITICAL severity logs

        Returns:
            Tuple of (success, message)
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()

            if keep_critical:
                self.cursor.execute(
                    """
                    DELETE FROM audit_logs
                    WHERE created_at < ? AND severity != 'CRITICAL'
                """,
                    (cutoff_date,),
                )
            else:
                self.cursor.execute(
                    """
                    DELETE FROM audit_logs
                    WHERE created_at < ?
                """,
                    (cutoff_date,),
                )

            deleted_count = self.cursor.rowcount
            self.conn.commit()

            return (True, f"Deleted {deleted_count} old audit logs")
        except Exception as e:
            return (False, f"Error deleting old audit logs: {str(e)}")

    def get_audit_statistics(self) -> Dict[str, any]:
        """
        Get statistics about audit logs.

        Returns:
            Dictionary containing audit log statistics
        """
        try:
            stats = {}

            # Total logs
            self.cursor.execute("SELECT COUNT(*) FROM audit_logs")
            stats["total_logs"] = self.cursor.fetchone()[0]

            # Logs by severity
            self.cursor.execute(
                """
                SELECT severity, COUNT(*) as count
                FROM audit_logs
                GROUP BY severity
            """
            )
            stats["by_severity"] = {
                row["severity"]: row["count"] for row in self.cursor.fetchall()
            }

            # Logs by category
            self.cursor.execute(
                """
                SELECT event_category, COUNT(*) as count
                FROM audit_logs
                GROUP BY event_category
            """
            )
            stats["by_category"] = {
                row["event_category"]: row["count"] for row in self.cursor.fetchall()
            }

            # Recent activity (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM audit_logs WHERE created_at >= ?
            """,
                (yesterday,),
            )
            stats["last_24_hours"] = self.cursor.fetchone()[0]

            # Recent activity (last 7 days)
            last_week = (datetime.now() - timedelta(days=7)).isoformat()
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM audit_logs WHERE created_at >= ?
            """,
                (last_week,),
            )
            stats["last_7_days"] = self.cursor.fetchone()[0]

            # Failed login attempts (last 24 hours)
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM audit_logs
                WHERE event_type = 'LOGIN_FAILED' AND created_at >= ?
            """,
                (yesterday,),
            )
            stats["failed_logins_24h"] = self.cursor.fetchone()[0]

            # Critical events (last 7 days)
            self.cursor.execute(
                """
                SELECT COUNT(*) FROM audit_logs
                WHERE severity = 'CRITICAL' AND created_at >= ?
            """,
                (last_week,),
            )
            stats["critical_events_7d"] = self.cursor.fetchone()[0]

            return stats
        except Exception as e:
            print(f"Error getting audit statistics: {e}")
            return {}

    # ==================== End of Audit Log Methods ====================

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()

    def __del__(self):
        """Cleanup database connection."""
        self.close()
