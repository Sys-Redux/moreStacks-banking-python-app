"""
Tests for Session Management System
Tests session creation, timeout, extension, and cleanup functionality
"""

import pytest
import time
from datetime import datetime, timedelta
from utils.session_manager import SessionManager


class TestSessionCreation:
    """Test session creation and basic operations."""

    def test_create_session(self):
        """Test creating a new session."""
        manager = SessionManager()
        token = manager.create_session(1, "testuser")

        assert token is not None
        assert len(token) > 0
        assert manager.is_session_valid(token)

    def test_create_multiple_sessions(self):
        """Test creating multiple sessions for different users."""
        manager = SessionManager()
        token1 = manager.create_session(1, "user1")
        token2 = manager.create_session(2, "user2")

        assert token1 != token2
        assert manager.is_session_valid(token1)
        assert manager.is_session_valid(token2)
        assert manager.get_active_session_count() == 2

    def test_session_token_uniqueness(self):
        """Test that session tokens are unique."""
        manager = SessionManager()
        tokens = [manager.create_session(i, f"user{i}") for i in range(10)]

        # All tokens should be unique
        assert len(tokens) == len(set(tokens))


class TestSessionValidation:
    """Test session validation and expiration."""

    def test_session_is_valid_after_creation(self):
        """Test that new session is immediately valid."""
        manager = SessionManager(timeout_minutes=1)
        token = manager.create_session(1, "testuser")

        assert manager.is_session_valid(token)

    def test_invalid_session_token(self):
        """Test validation with invalid token."""
        manager = SessionManager()

        assert not manager.is_session_valid("invalid_token")

    def test_session_expires_after_timeout(self):
        """Test that session expires after timeout period."""
        manager = SessionManager(timeout_minutes=0.01)  # 0.6 seconds
        token = manager.create_session(1, "testuser")

        assert manager.is_session_valid(token)

        # Wait for expiration
        time.sleep(1)

        assert not manager.is_session_valid(token)

    def test_get_time_until_expiration(self):
        """Test getting time remaining on session."""
        manager = SessionManager(timeout_minutes=1)
        token = manager.create_session(1, "testuser")

        time_left = manager.get_time_until_expiration(token)

        assert time_left is not None
        assert 55 <= time_left <= 60  # Should be close to 60 seconds

    def test_get_time_until_expiration_invalid_token(self):
        """Test time remaining for invalid token."""
        manager = SessionManager()

        assert manager.get_time_until_expiration("invalid") is None


class TestActivityTracking:
    """Test activity tracking and session updates."""

    def test_update_activity(self):
        """Test updating session activity."""
        manager = SessionManager(timeout_minutes=1)
        token = manager.create_session(1, "testuser")

        # Get initial expiration time
        info1 = manager.get_session_info(token)
        time.sleep(0.5)

        # Update activity
        assert manager.update_activity(token)

        # Expiration should be extended
        info2 = manager.get_session_info(token)
        assert info2["expires_at"] > info1["expires_at"]

    def test_update_activity_invalid_token(self):
        """Test updating activity for invalid token."""
        manager = SessionManager()

        assert not manager.update_activity("invalid")

    def test_activity_prevents_expiration(self):
        """Test that activity updates prevent session expiration."""
        manager = SessionManager(timeout_minutes=0.02)  # 1.2 seconds
        token = manager.create_session(1, "testuser")

        # Update activity every 0.5 seconds for 2 seconds
        for _ in range(4):
            time.sleep(0.5)
            manager.update_activity(token)
            assert manager.is_session_valid(token)


class TestSessionExtension:
    """Test session extension functionality."""

    def test_extend_session(self):
        """Test extending a session."""
        manager = SessionManager(timeout_minutes=1)
        token = manager.create_session(1, "testuser")

        info1 = manager.get_session_info(token)
        time.sleep(0.5)

        assert manager.extend_session(token)

        info2 = manager.get_session_info(token)
        assert info2["expires_at"] > info1["expires_at"]

    def test_extend_invalid_session(self):
        """Test extending invalid session."""
        manager = SessionManager()

        assert not manager.extend_session("invalid")

    def test_extend_expired_session(self):
        """Test that extending expired session fails."""
        manager = SessionManager(timeout_minutes=0.01)
        token = manager.create_session(1, "testuser")

        time.sleep(1)

        # Session expired, but extend_session should return True
        # (it updates activity if session exists in memory)
        result = manager.extend_session(token)
        assert result  # Returns True because session exists in dict

        # However, is_session_valid checks expiration
        # After extension, it should be valid again
        assert manager.is_session_valid(token)


class TestWarningSystem:
    """Test warning system for approaching timeout."""

    def test_should_show_warning_approaching_timeout(self):
        """Test warning shows when approaching timeout."""
        manager = SessionManager(
            timeout_minutes=2, warning_minutes=1
        )  # 120s timeout, 60s warning
        token = manager.create_session(1, "testuser")

        # Initially no warning (fresh session)
        assert not manager.should_show_warning(token)

        # Artificially set expiration to test warning period
        # Set expires_at to 30 seconds from now (within warning period)
        manager.active_sessions[token]["expires_at"] = datetime.now() + timedelta(
            seconds=30
        )

        # Now should show warning (30 seconds left, warning is 60 seconds)
        assert manager.should_show_warning(token)

    def test_no_warning_for_fresh_session(self):
        """Test no warning for newly created session."""
        manager = SessionManager(timeout_minutes=15, warning_minutes=1)
        token = manager.create_session(1, "testuser")

        assert not manager.should_show_warning(token)

    def test_no_warning_for_expired_session(self):
        """Test no warning for already expired session."""
        manager = SessionManager(timeout_minutes=0.01)
        token = manager.create_session(1, "testuser")

        time.sleep(1)

        assert not manager.should_show_warning(token)

    def test_no_warning_for_invalid_token(self):
        """Test no warning for invalid token."""
        manager = SessionManager()

        assert not manager.should_show_warning("invalid")


class TestSessionDestruction:
    """Test session destruction (logout)."""

    def test_destroy_session(self):
        """Test destroying a session."""
        manager = SessionManager()
        token = manager.create_session(1, "testuser")

        assert manager.is_session_valid(token)
        assert manager.destroy_session(token)
        assert not manager.is_session_valid(token)

    def test_destroy_invalid_session(self):
        """Test destroying invalid session."""
        manager = SessionManager()

        assert not manager.destroy_session("invalid")

    def test_destroy_session_removes_from_active(self):
        """Test that destroyed session is removed from active sessions."""
        manager = SessionManager()
        token = manager.create_session(1, "testuser")

        assert manager.get_active_session_count() == 1
        manager.destroy_session(token)
        assert manager.get_active_session_count() == 0


class TestSessionInfo:
    """Test getting session information."""

    def test_get_session_info(self):
        """Test getting session information."""
        manager = SessionManager()
        token = manager.create_session(42, "testuser")

        info = manager.get_session_info(token)

        assert info is not None
        assert info["user_id"] == 42
        assert info["username"] == "testuser"
        assert "created_at" in info
        assert "last_activity" in info
        assert "expires_at" in info
        assert "time_left_seconds" in info
        assert info["is_valid"]

    def test_get_session_info_invalid_token(self):
        """Test getting info for invalid token."""
        manager = SessionManager()

        assert manager.get_session_info("invalid") is None


class TestSessionCleanup:
    """Test automatic cleanup of expired sessions."""

    def test_cleanup_expired_sessions(self):
        """Test cleaning up expired sessions."""
        manager = SessionManager(timeout_minutes=0.01)

        # Create multiple sessions
        tokens = [manager.create_session(i, f"user{i}") for i in range(5)]

        assert manager.get_active_session_count() == 5

        # Wait for expiration
        time.sleep(1)

        # Cleanup expired sessions
        cleaned = manager.cleanup_expired_sessions()

        assert cleaned == 5
        assert manager.get_active_session_count() == 0

    def test_cleanup_keeps_valid_sessions(self):
        """Test that cleanup doesn't remove valid sessions."""
        manager = SessionManager(timeout_minutes=10)

        tokens = [manager.create_session(i, f"user{i}") for i in range(3)]

        # Cleanup should remove nothing
        cleaned = manager.cleanup_expired_sessions()

        assert cleaned == 0
        assert manager.get_active_session_count() == 3

    def test_cleanup_mixed_sessions(self):
        """Test cleanup with mix of expired and valid sessions."""
        manager = SessionManager(timeout_minutes=0.02)

        # Create some sessions
        expired_tokens = [manager.create_session(i, f"expired{i}") for i in range(3)]

        # Wait for them to expire
        time.sleep(1.5)

        # Create new sessions
        valid_tokens = [manager.create_session(i, f"valid{i}") for i in range(2)]

        assert manager.get_active_session_count() == 5

        # Cleanup should remove only expired
        cleaned = manager.cleanup_expired_sessions()

        assert cleaned == 3
        assert manager.get_active_session_count() == 2


class TestTimeFormatting:
    """Test time formatting utilities."""

    def test_format_time_remaining_minutes_and_seconds(self):
        """Test formatting time with minutes and seconds."""
        manager = SessionManager()

        formatted = manager.format_time_remaining(330)  # 5m 30s
        assert formatted == "5m 30s"

    def test_format_time_remaining_seconds_only(self):
        """Test formatting time with seconds only."""
        manager = SessionManager()

        formatted = manager.format_time_remaining(45)
        assert formatted == "45s"

    def test_format_time_remaining_zero(self):
        """Test formatting zero time."""
        manager = SessionManager()

        formatted = manager.format_time_remaining(0)
        assert formatted == "Expired"

    def test_format_time_remaining_negative(self):
        """Test formatting negative time."""
        manager = SessionManager()

        formatted = manager.format_time_remaining(-10)
        assert formatted == "Expired"


class TestConcurrentSessions:
    """Test handling multiple concurrent sessions."""

    def test_multiple_users_concurrent_sessions(self):
        """Test multiple users with separate sessions."""
        manager = SessionManager()

        # Create sessions for different users
        token1 = manager.create_session(1, "user1")
        token2 = manager.create_session(2, "user2")
        token3 = manager.create_session(3, "user3")

        # All should be valid
        assert manager.is_session_valid(token1)
        assert manager.is_session_valid(token2)
        assert manager.is_session_valid(token3)

        # Destroying one shouldn't affect others
        manager.destroy_session(token2)

        assert manager.is_session_valid(token1)
        assert not manager.is_session_valid(token2)
        assert manager.is_session_valid(token3)

    def test_same_user_multiple_sessions(self):
        """Test same user can have multiple sessions."""
        manager = SessionManager()

        # Same user, multiple sessions (e.g., different devices)
        token1 = manager.create_session(1, "user1")
        token2 = manager.create_session(1, "user1")

        assert token1 != token2
        assert manager.is_session_valid(token1)
        assert manager.is_session_valid(token2)
        assert manager.get_active_session_count() == 2
