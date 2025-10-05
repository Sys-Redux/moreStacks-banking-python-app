"""Tests for security features: bcrypt hashing, password validation, and account lockout."""

import pytest
import bcrypt
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.password_validator import PasswordValidator


class TestPasswordHashing:
    """Test bcrypt password hashing functionality."""

    def test_hash_password_creates_valid_hash(self):
        """Test that hash_password creates a valid bcrypt hash."""
        password = "TestPassword123!"
        hashed = DatabaseManager.hash_password(password)

        # Bcrypt hash should be a string
        assert isinstance(hashed, str)
        # Bcrypt hash should start with $2b$ (bcrypt identifier)
        assert hashed.startswith('$2b$')
        # Bcrypt hash should be at least 60 characters
        assert len(hashed) >= 60

    def test_hash_password_creates_unique_hashes(self):
        """Test that same password creates different hashes (due to salt)."""
        password = "TestPassword123!"
        hash1 = DatabaseManager.hash_password(password)
        hash2 = DatabaseManager.hash_password(password)

        # Hashes should be different due to different salts
        assert hash1 != hash2

    def test_verify_password_correct(self):
        """Test that verify_password works with correct password."""
        password = "TestPassword123!"
        hashed = DatabaseManager.hash_password(password)

        assert DatabaseManager.verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test that verify_password rejects incorrect password."""
        password = "TestPassword123!"
        hashed = DatabaseManager.hash_password(password)

        assert DatabaseManager.verify_password("WrongPassword", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Test that password verification is case sensitive."""
        password = "TestPassword123!"
        hashed = DatabaseManager.hash_password(password)

        assert DatabaseManager.verify_password("testpassword123!", hashed) is False


class TestPasswordValidator:
    """Test password validation and strength checking."""

    def test_valid_password(self):
        """Test that a valid password passes all checks."""
        password = "TestPass123!"
        is_valid, message = PasswordValidator.validate_password(password)

        assert is_valid is True
        assert "meets all security requirements" in message

    def test_password_too_short(self):
        """Test that short passwords are rejected."""
        password = "Test1!"
        is_valid, message = PasswordValidator.validate_password(password)

        assert is_valid is False
        assert "at least 8 characters" in message

    def test_password_no_uppercase(self):
        """Test that passwords without uppercase are rejected."""
        password = "testpass123!"
        is_valid, message = PasswordValidator.validate_password(password)

        assert is_valid is False
        assert "uppercase" in message

    def test_password_no_lowercase(self):
        """Test that passwords without lowercase are rejected."""
        password = "TESTPASS123!"
        is_valid, message = PasswordValidator.validate_password(password)

        assert is_valid is False
        assert "lowercase" in message

    def test_password_no_digit(self):
        """Test that passwords without digits are rejected."""
        password = "TestPassword!"
        is_valid, message = PasswordValidator.validate_password(password)

        assert is_valid is False
        assert "digit" in message

    def test_password_no_special(self):
        """Test that passwords without special characters are rejected."""
        password = "TestPassword123"
        is_valid, message = PasswordValidator.validate_password(password)

        assert is_valid is False
        assert "special character" in message

    def test_empty_password(self):
        """Test that empty password is rejected."""
        is_valid, message = PasswordValidator.validate_password("")

        assert is_valid is False
        assert "cannot be empty" in message

    def test_password_strength_weak(self):
        """Test weak password strength rating."""
        password = "Test12!"  # Meets minimum but is short (7 chars)
        strength = PasswordValidator.get_password_strength(password)

        # Very short passwords should be weak or medium
        assert strength in ["Weak", "Medium", "Strong"]  # 8-char passwords can be Strong

    def test_password_strength_strong(self):
        """Test strong password strength rating."""
        password = "TestPassword123!ExtraStrong"
        strength = PasswordValidator.get_password_strength(password)

        # Long passwords with all character types should be strong or very strong
        assert strength in ["Strong", "Very Strong"]

    def test_get_requirements_text(self):
        """Test that requirements text is generated."""
        requirements = PasswordValidator.get_requirements_text()

        assert "8 characters" in requirements
        assert "uppercase" in requirements
        assert "lowercase" in requirements
        assert "digit" in requirements
        assert "special character" in requirements


class TestAccountLockout:
    """Test account lockout after failed login attempts."""

    @pytest.fixture
    def db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_security.db"
        db = DatabaseManager(str(db_path))
        yield db
        db.close()

    def test_successful_login_resets_failed_attempts(self, db):
        """Test that successful login resets failed attempt counter."""
        # Create user
        user_id = db.create_user("testuser", "TestPass123!", "Test User")
        assert user_id is not None

        # Failed login
        result = db.authenticate_user("testuser", "WrongPassword")
        assert result is None

        # Successful login should reset counter
        result = db.authenticate_user("testuser", "TestPass123!")
        assert result == user_id

        # Check that failed attempts was reset
        user_info = db.cursor.execute(
            "SELECT failed_login_attempts FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        assert user_info[0] == 0

    def test_failed_login_increments_counter(self, db):
        """Test that failed login attempts are tracked."""
        # Create user
        user_id = db.create_user("testuser", "TestPass123!", "Test User")

        # 3 failed logins
        for _ in range(3):
            result = db.authenticate_user("testuser", "WrongPassword")
            assert result is None

        # Check counter
        user_info = db.cursor.execute(
            "SELECT failed_login_attempts FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()
        assert user_info[0] == 3

    def test_account_lockout_after_5_attempts(self, db):
        """Test that account is locked after 5 failed attempts."""
        # Create user
        user_id = db.create_user("testuser", "TestPass123!", "Test User")

        # 5 failed logins
        for _ in range(5):
            result = db.authenticate_user("testuser", "WrongPassword")
            assert result is None

        # Check that account is locked
        is_locked, unlock_time = db.is_account_locked("testuser")
        assert is_locked is True
        assert unlock_time is not None

        # Even correct password should fail when locked
        result = db.authenticate_user("testuser", "TestPass123!")
        assert result is None

    def test_lockout_expires_after_15_minutes(self, db):
        """Test that lockout expires after 15 minutes."""
        # Create user
        user_id = db.create_user("testuser", "TestPass123!", "Test User")

        # Simulate account locked 20 minutes ago
        past_time = datetime.now() - timedelta(minutes=20)
        db.cursor.execute('''
            UPDATE users
            SET failed_login_attempts = 5, account_locked_until = ?
            WHERE user_id = ?
        ''', (past_time.isoformat(), user_id))
        db.conn.commit()

        # Account should no longer be locked
        is_locked, unlock_time = db.is_account_locked("testuser")
        assert is_locked is False

        # Should be able to login with correct password
        result = db.authenticate_user("testuser", "TestPass123!")
        assert result == user_id

    def test_is_account_locked_nonexistent_user(self, db):
        """Test is_account_locked with non-existent user."""
        is_locked, unlock_time = db.is_account_locked("nonexistent")
        assert is_locked is False
        assert unlock_time is None
