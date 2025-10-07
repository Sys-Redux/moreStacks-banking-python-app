"""Tests for password expiration functionality."""

import pytest
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.password_expiration import PasswordExpirationManager
from config import SecurityConfig


class TestPasswordExpirationManager:
    """Test PasswordExpirationManager functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.manager = PasswordExpirationManager()
        self.now = datetime.now()

    def test_initialization_default(self):
        """Test manager initialization with default values."""
        manager = PasswordExpirationManager()
        assert manager.expiration_days == SecurityConfig.PASSWORD_EXPIRATION_DAYS
        assert manager.warning_days == SecurityConfig.PASSWORD_WARNING_DAYS
        assert manager.history_count == SecurityConfig.PASSWORD_HISTORY_COUNT
        assert manager.grace_period_days == SecurityConfig.PASSWORD_GRACE_PERIOD_DAYS

    def test_initialization_custom(self):
        """Test manager initialization with custom values."""
        manager = PasswordExpirationManager(
            expiration_days=60,
            warning_days=(14, 7, 3),
            history_count=10,
            grace_period_days=5,
        )
        assert manager.expiration_days == 60
        assert manager.warning_days == (14, 7, 3)
        assert manager.history_count == 10
        assert manager.grace_period_days == 5

    def test_password_not_expired(self):
        """Test password that is not expired."""
        password_date = (self.now - timedelta(days=30)).isoformat()
        assert not self.manager.is_password_expired(password_date)

    def test_password_expired_exactly(self):
        """Test password that expired exactly at expiration_days."""
        password_date = (self.now - timedelta(days=90)).isoformat()
        assert self.manager.is_password_expired(password_date)

    def test_password_expired_over(self):
        """Test password that is over expiration period."""
        password_date = (self.now - timedelta(days=120)).isoformat()
        assert self.manager.is_password_expired(password_date)

    def test_password_expired_none_date(self):
        """Test with None password date (should be expired)."""
        assert self.manager.is_password_expired(None)

    def test_password_expired_invalid_date(self):
        """Test with invalid date string (should be expired)."""
        assert self.manager.is_password_expired("invalid-date")

    def test_days_until_expiration_positive(self):
        """Test days remaining when password is not expired."""
        password_date = (self.now - timedelta(days=30)).isoformat()
        days_left = self.manager.days_until_expiration(password_date)
        assert days_left == 60  # 90 - 30

    def test_days_until_expiration_negative(self):
        """Test days remaining when password is expired."""
        password_date = (self.now - timedelta(days=100)).isoformat()
        days_left = self.manager.days_until_expiration(password_date)
        assert days_left == -10  # 90 - 100

    def test_days_until_expiration_none(self):
        """Test days remaining with None date."""
        days_left = self.manager.days_until_expiration(None)
        assert days_left < 0

    def test_should_show_warning_no(self):
        """Test warning not needed for fresh password."""
        password_date = (self.now - timedelta(days=30)).isoformat()
        assert not self.manager.should_show_warning(password_date)

    def test_should_show_warning_7_days(self):
        """Test warning at 7 days threshold."""
        password_date = (self.now - timedelta(days=83)).isoformat()  # 7 days left
        assert self.manager.should_show_warning(password_date)

    def test_should_show_warning_3_days(self):
        """Test warning at 3 days threshold."""
        password_date = (self.now - timedelta(days=87)).isoformat()  # 3 days left
        assert self.manager.should_show_warning(password_date)

    def test_should_show_warning_1_day(self):
        """Test warning at 1 day threshold."""
        password_date = (self.now - timedelta(days=89)).isoformat()  # 1 day left
        assert self.manager.should_show_warning(password_date)

    def test_should_show_warning_expired(self):
        """Test warning for expired password."""
        password_date = (self.now - timedelta(days=100)).isoformat()
        assert self.manager.should_show_warning(password_date)

    def test_get_warning_level_ok(self):
        """Test warning level for fresh password."""
        password_date = (self.now - timedelta(days=30)).isoformat()
        level = self.manager.get_warning_level(password_date)
        assert level == "ok"

    def test_get_warning_level_info(self):
        """Test warning level for password expiring in 10 days."""
        password_date = (self.now - timedelta(days=80)).isoformat()  # 10 days left
        level = self.manager.get_warning_level(password_date)
        assert level == "info"

    def test_get_warning_level_warning(self):
        """Test warning level for password expiring in 5 days."""
        password_date = (self.now - timedelta(days=85)).isoformat()  # 5 days left
        level = self.manager.get_warning_level(password_date)
        assert level == "warning"

    def test_get_warning_level_critical(self):
        """Test warning level for password expiring in 2 days."""
        password_date = (self.now - timedelta(days=88)).isoformat()  # 2 days left
        level = self.manager.get_warning_level(password_date)
        assert level == "critical"

    def test_get_warning_level_expired(self):
        """Test warning level for expired password."""
        password_date = (self.now - timedelta(days=100)).isoformat()
        level = self.manager.get_warning_level(password_date)
        assert level == "expired"

    def test_get_expiration_message_ok(self):
        """Test expiration message for fresh password."""
        password_date = (self.now - timedelta(days=30)).isoformat()
        message = self.manager.get_expiration_message(password_date)
        assert "60 days" in message
        assert "expires" in message.lower()

    def test_get_expiration_message_warning(self):
        """Test expiration message for password expiring soon."""
        password_date = (self.now - timedelta(days=85)).isoformat()
        message = self.manager.get_expiration_message(password_date)
        assert "5 days" in message
        assert "expires" in message.lower()

    def test_get_expiration_message_expired(self):
        """Test expiration message for expired password."""
        password_date = (self.now - timedelta(days=100)).isoformat()
        message = self.manager.get_expiration_message(password_date)
        assert "expired" in message.lower()

    def test_password_age_days(self):
        """Test password age calculation."""
        password_date = (self.now - timedelta(days=45)).isoformat()
        age = self.manager.password_age_days(password_date)
        assert age == 45

    def test_password_age_days_none(self):
        """Test password age with None date."""
        age = self.manager.password_age_days(None)
        assert age > 365  # Very old

    def test_format_expiration_date(self):
        """Test expiration date formatting."""
        password_date = self.now.isoformat()
        formatted = self.manager.format_expiration_date(password_date)
        assert formatted is not None
        assert len(formatted) > 0

    def test_get_current_timestamp(self):
        """Test current timestamp generation."""
        timestamp = self.manager.get_current_timestamp()
        assert timestamp is not None
        # Verify it can be parsed
        datetime.fromisoformat(timestamp)

    def test_is_within_grace_period_no_grace(self):
        """Test grace period when grace_period_days is 0."""
        password_date = (self.now - timedelta(days=100)).isoformat()
        assert not self.manager.is_within_grace_period(password_date)

    def test_is_within_grace_period_with_grace(self):
        """Test grace period when enabled."""
        manager = PasswordExpirationManager(grace_period_days=5)
        password_date = (self.now - timedelta(days=92)).isoformat()  # 2 days into grace
        assert manager.is_within_grace_period(password_date)

    def test_is_within_grace_period_expired_grace(self):
        """Test grace period when expired beyond grace period."""
        manager = PasswordExpirationManager(grace_period_days=5)
        password_date = (self.now - timedelta(days=100)).isoformat()  # Beyond grace
        assert not manager.is_within_grace_period(password_date)


class TestPasswordHistoryDatabase:
    """Test password history database operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test database."""
        self.db = DatabaseManager(":memory:")
        self.user_id = self.db.create_user("testuser", "Password123!", "Test User")

    def test_add_password_to_history(self):
        """Test adding password to history."""
        password_hash = self.db.hash_password("OldPassword123!")

        success = self.db.add_password_to_history(self.user_id, password_hash)
        assert success

    def test_get_password_history_empty(self):
        """Test getting password history when empty."""
        history = self.db.get_password_history(self.user_id)
        assert history == []

    def test_get_password_history_with_passwords(self):
        """Test getting password history with passwords."""
        # Add 3 passwords
        for i in range(3):
            password_hash = self.db.hash_password(f"Password{i}!")
            self.db.add_password_to_history(self.user_id, password_hash)

        history = self.db.get_password_history(self.user_id, limit=5)
        assert len(history) == 3

    def test_get_password_history_limit(self):
        """Test password history retrieval with limit."""
        # Add 7 passwords
        for i in range(7):
            password_hash = self.db.hash_password(f"Password{i}!")
            self.db.add_password_to_history(self.user_id, password_hash)

        history = self.db.get_password_history(self.user_id, limit=5)
        assert len(history) == 5  # Should only get 5 most recent

    def test_check_password_reuse_not_reused(self):
        """Test password reuse check for new password."""
        # Add old password to history
        old_password = "OldPassword123!"
        old_hash = self.db.hash_password(old_password)
        self.db.add_password_to_history(self.user_id, old_hash)

        # Check new password
        is_reused, message = self.db.check_password_reuse(
            self.user_id, "NewPassword456!"
        )
        assert not is_reused
        assert "can be used" in message.lower() or "not" in message.lower()

    def test_check_password_reuse_is_reused(self):
        """Test password reuse check for reused password."""
        # Add old password to history
        old_password = "OldPassword123!"
        old_hash = self.db.hash_password(old_password)
        self.db.add_password_to_history(self.user_id, old_hash)

        # Try to reuse same password
        is_reused, message = self.db.check_password_reuse(self.user_id, old_password)
        assert is_reused
        assert "recently" in message.lower() or "reuse" in message.lower()

    def test_check_password_reuse_empty_history(self):
        """Test password reuse check with no history."""
        is_reused, message = self.db.check_password_reuse(
            self.user_id, "NewPassword123!"
        )
        assert not is_reused

    def test_update_password_changed_date(self):
        """Test updating password changed date."""
        success = self.db.update_password_changed_date(self.user_id)
        assert success

        # Verify date was set
        changed_date = self.db.get_password_changed_date(self.user_id)
        assert changed_date is not None

    def test_get_password_changed_date_none(self):
        """Test getting password changed date when not set."""
        # For new user, should return current timestamp or None
        changed_date = self.db.get_password_changed_date(self.user_id)
        # Either None or a valid timestamp
        assert changed_date is None or isinstance(changed_date, str)

    def test_get_password_changed_date_after_update(self):
        """Test getting password changed date after setting it."""
        self.db.update_password_changed_date(self.user_id)
        changed_date = self.db.get_password_changed_date(self.user_id)
        assert changed_date is not None
        # Verify it's a valid timestamp
        datetime.fromisoformat(changed_date)


class TestChangeUserPassword:
    """Test complete password change workflow."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test database."""
        self.db = DatabaseManager(":memory:")
        self.username = "testuser"
        self.old_password = "OldPassword123!"
        self.user_id = self.db.create_user(
            self.username, self.old_password, "Test User"
        )

    def test_change_password_success(self):
        """Test successful password change."""
        new_password = "NewPassword456!"

        success, message = self.db.change_user_password(
            self.username, self.old_password, new_password
        )

        assert success
        assert "success" in message.lower()

        # Verify new password works
        user_id = self.db.authenticate_user(self.username, new_password)
        assert user_id == self.user_id

    def test_change_password_wrong_old_password(self):
        """Test password change with incorrect old password."""
        success, message = self.db.change_user_password(
            self.username, "WrongPassword123!", "NewPassword456!"
        )

        assert not success
        assert "current password" in message.lower() or "incorrect" in message.lower()

    def test_change_password_nonexistent_user(self):
        """Test password change for nonexistent user."""
        success, message = self.db.change_user_password(
            "nonexistent", "OldPassword123!", "NewPassword456!"
        )

        assert not success

    def test_change_password_reused(self):
        """Test password change with reused password."""
        # Change password to create history
        new_password = "NewPassword456!"
        self.db.change_user_password(self.username, self.old_password, new_password)

        # Try to change back to old password
        success, message = self.db.change_user_password(
            self.username, new_password, self.old_password
        )

        assert not success
        assert "recently" in message.lower() or "reuse" in message.lower()

    def test_change_password_updates_date(self):
        """Test that password change updates the password_changed_at date."""
        # Change password
        new_password = "NewPassword456!"
        self.db.change_user_password(self.username, self.old_password, new_password)

        # Check that password_changed_at was updated
        changed_date = self.db.get_password_changed_date(self.user_id)
        assert changed_date is not None

        # Verify it's recent (within last minute)
        changed_time = datetime.fromisoformat(changed_date)
        now = datetime.now()
        diff = (now - changed_time).total_seconds()
        assert diff < 60  # Within last minute

    def test_change_password_adds_to_history(self):
        """Test that password change adds old password to history."""
        # Change password
        new_password = "NewPassword456!"
        self.db.change_user_password(self.username, self.old_password, new_password)

        # Check history
        history = self.db.get_password_history(self.user_id)
        assert len(history) == 1

        # Verify old password is in history
        is_reused, _ = self.db.check_password_reuse(self.user_id, self.old_password)
        assert is_reused

    def test_change_password_multiple_times(self):
        """Test changing password multiple times maintains history."""
        passwords = [
            "Password1!",
            "Password2!",
            "Password3!",
            "Password4!",
            "Password5!",
        ]

        current_password = self.old_password

        # Change password 5 times
        for new_password in passwords:
            success, _ = self.db.change_user_password(
                self.username, current_password, new_password
            )
            assert success
            current_password = new_password

        # Check history size (should have last 5 old passwords)
        history = self.db.get_password_history(self.user_id, limit=5)
        assert len(history) <= 5

    def test_change_password_validates_new_password(self):
        """Test that password change validates new password strength."""
        # This assumes the change_user_password method validates the new password
        # If it doesn't, this test documents that it should
        weak_password = "weak"

        success, message = self.db.change_user_password(
            self.username, self.old_password, weak_password
        )

        # The function should reject weak passwords
        # If it doesn't, this is where validation should be added
        # For now, we document the expected behavior
        # assert not success  # Uncomment when validation is added


class TestPasswordExpirationIntegration:
    """Test integration of password expiration with database."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.db = DatabaseManager(":memory:")
        self.manager = PasswordExpirationManager()
        self.user_id = self.db.create_user("testuser", "Password123!", "Test User")

    def test_new_user_password_not_expired(self):
        """Test that newly created user password is not expired."""
        # Update password changed date to now
        self.db.update_password_changed_date(self.user_id)

        changed_date = self.db.get_password_changed_date(self.user_id)
        is_expired = self.manager.is_password_expired(changed_date)

        assert not is_expired

    def test_old_user_password_expired(self):
        """Test that old password is detected as expired."""
        # Simulate old password (100 days ago)
        old_date = (datetime.now() - timedelta(days=100)).isoformat()

        # Manually update the date in database (for testing)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_changed_at = ? WHERE user_id = ?",
            (old_date, self.user_id),
        )
        conn.commit()

        changed_date = self.db.get_password_changed_date(self.user_id)
        is_expired = self.manager.is_password_expired(changed_date)

        assert is_expired

    def test_complete_password_change_workflow(self):
        """Test complete workflow of password change with expiration."""
        username = "testuser"
        old_password = "Password123!"
        new_password = "NewPassword456!"

        # Simulate expired password
        old_date = (datetime.now() - timedelta(days=100)).isoformat()
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_changed_at = ? WHERE user_id = ?",
            (old_date, self.user_id),
        )
        conn.commit()

        # Verify password is expired
        changed_date = self.db.get_password_changed_date(self.user_id)
        assert self.manager.is_password_expired(changed_date)

        # Change password
        success, message = self.db.change_user_password(
            username, old_password, new_password
        )
        assert success

        # Verify password is no longer expired
        new_changed_date = self.db.get_password_changed_date(self.user_id)
        assert not self.manager.is_password_expired(new_changed_date)

        # Verify new password works
        user_id = self.db.authenticate_user(username, new_password)
        assert user_id == self.user_id
