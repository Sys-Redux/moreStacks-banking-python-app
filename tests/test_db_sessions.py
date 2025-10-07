"""
Tests for database session management functionality.

This test suite validates the database layer for session persistence,
including creation, retrieval, updates, and cleanup operations.
"""

import pytest
import os
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager


@pytest.fixture
def db():
    """Create a test database instance."""
    test_db_path = "test_sessions.db"
    db_instance = DatabaseManager(test_db_path)
    yield db_instance
    db_instance.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)


@pytest.fixture
def test_user(db):
    """Create a test user for session tests."""
    username = "session_test_user"
    password = "TestPassword123!"
    email = "session@test.com"

    user_id = db.create_user(username, password, email)
    return user_id


class TestSessionCreation:
    """Test session creation in database."""

    def test_create_session_success(self, db, test_user):
        """Test successful session creation."""
        token = "test_token_123"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        result = db.create_session(test_user, token, created, expires)

        assert result is True

    def test_create_session_retrieval(self, db, test_user):
        """Test that created session can be retrieved."""
        token = "test_token_456"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        db.create_session(test_user, token, created, expires)
        session = db.get_session(token)

        assert session is not None
        assert session["user_id"] == test_user
        assert session["session_token"] == token
        assert session["created_at"] == created
        assert session["expires_at"] == expires

    def test_create_duplicate_token_fails(self, db, test_user):
        """Test that duplicate session tokens are rejected."""
        token = "duplicate_token"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        result1 = db.create_session(test_user, token, created, expires)
        result2 = db.create_session(test_user, token, created, expires)

        assert result1 is True
        assert result2 is False

    def test_create_multiple_sessions_same_user(self, db, test_user):
        """Test creating multiple sessions for the same user."""
        token1 = "token_1"
        token2 = "token_2"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        result1 = db.create_session(test_user, token1, created, expires)
        result2 = db.create_session(test_user, token2, created, expires)

        assert result1 is True
        assert result2 is True
        assert db.get_session(token1) is not None
        assert db.get_session(token2) is not None


class TestSessionRetrieval:
    """Test session retrieval operations."""

    def test_get_nonexistent_session(self, db):
        """Test retrieving a session that doesn't exist."""
        session = db.get_session("nonexistent_token")
        assert session is None

    def test_get_session_includes_all_fields(self, db, test_user):
        """Test that retrieved session includes all expected fields."""
        token = "full_fields_token"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        db.create_session(test_user, token, created, expires)
        session = db.get_session(token)

        assert "session_id" in session
        assert "user_id" in session
        assert "session_token" in session
        assert "created_at" in session
        assert "last_activity" in session
        assert "expires_at" in session


class TestSessionActivityUpdate:
    """Test session activity tracking updates."""

    def test_update_session_activity(self, db, test_user):
        """Test updating session activity timestamp."""
        token = "activity_token"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        db.create_session(test_user, token, created, expires)

        new_activity = (datetime.now() + timedelta(minutes=5)).isoformat()
        new_expires = (datetime.now() + timedelta(minutes=20)).isoformat()
        result = db.update_session_activity(token, new_activity, new_expires)

        assert result is True

        session = db.get_session(token)
        assert session["last_activity"] == new_activity
        assert session["expires_at"] == new_expires

    def test_update_nonexistent_session(self, db):
        """Test updating a session that doesn't exist."""
        new_activity = datetime.now().isoformat()
        new_expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        result = db.update_session_activity("fake_token", new_activity, new_expires)
        assert result is False

    def test_update_extends_expiration(self, db, test_user):
        """Test that activity update properly extends expiration."""
        token = "extend_token"
        created = datetime.now()
        original_expires = created + timedelta(minutes=15)

        db.create_session(
            test_user, token, created.isoformat(), original_expires.isoformat()
        )

        new_expires = datetime.now() + timedelta(minutes=30)
        db.update_session_activity(
            token, datetime.now().isoformat(), new_expires.isoformat()
        )

        session = db.get_session(token)
        assert session["expires_at"] == new_expires.isoformat()


class TestSessionDeletion:
    """Test session deletion operations."""

    def test_delete_session(self, db, test_user):
        """Test deleting a single session."""
        token = "delete_token"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        db.create_session(test_user, token, created, expires)
        assert db.get_session(token) is not None

        result = db.delete_session(token)
        assert result is True
        assert db.get_session(token) is None

    def test_delete_nonexistent_session(self, db):
        """Test deleting a session that doesn't exist."""
        result = db.delete_session("nonexistent_token")
        assert result is True  # No error, just no rows affected

    def test_delete_user_sessions(self, db, test_user):
        """Test deleting all sessions for a user."""
        tokens = ["user_token_1", "user_token_2", "user_token_3"]
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        for token in tokens:
            db.create_session(test_user, token, created, expires)

        result = db.delete_user_sessions(test_user)
        assert result is True

        for token in tokens:
            assert db.get_session(token) is None

    def test_delete_user_sessions_multiple_users(self, db, test_user):
        """Test that deleting one user's sessions doesn't affect others."""
        # Create second user
        user2_id = db.create_user("user2", "Password123!", "user2@test.com")

        token1 = "user1_token"
        token2 = "user2_token"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        db.create_session(test_user, token1, created, expires)
        db.create_session(user2_id, token2, created, expires)

        db.delete_user_sessions(test_user)

        assert db.get_session(token1) is None
        assert db.get_session(token2) is not None


class TestExpiredSessionCleanup:
    """Test cleanup of expired sessions."""

    def test_cleanup_expired_sessions(self, db, test_user):
        """Test removing expired sessions."""
        now = datetime.now()

        # Create expired session
        expired_token = "expired_token"
        expired_time = (now - timedelta(minutes=10)).isoformat()
        db.create_session(test_user, expired_token, expired_time, expired_time)

        # Create valid session
        valid_token = "valid_token"
        valid_expires = (now + timedelta(minutes=15)).isoformat()
        db.create_session(test_user, valid_token, now.isoformat(), valid_expires)

        # Cleanup expired sessions
        deleted_count = db.cleanup_expired_sessions(now.isoformat())

        assert deleted_count == 1
        assert db.get_session(expired_token) is None
        assert db.get_session(valid_token) is not None

    def test_cleanup_no_expired_sessions(self, db, test_user):
        """Test cleanup when no sessions are expired."""
        now = datetime.now()
        token = "valid_token"
        expires = (now + timedelta(minutes=15)).isoformat()

        db.create_session(test_user, token, now.isoformat(), expires)

        deleted_count = db.cleanup_expired_sessions(now.isoformat())
        assert deleted_count == 0
        assert db.get_session(token) is not None

    def test_cleanup_multiple_expired_sessions(self, db, test_user):
        """Test cleanup of multiple expired sessions."""
        now = datetime.now()
        expired_time = (now - timedelta(minutes=10)).isoformat()

        expired_tokens = ["expired_1", "expired_2", "expired_3"]
        for token in expired_tokens:
            db.create_session(test_user, token, expired_time, expired_time)

        valid_token = "valid_token"
        valid_expires = (now + timedelta(minutes=15)).isoformat()
        db.create_session(test_user, valid_token, now.isoformat(), valid_expires)

        deleted_count = db.cleanup_expired_sessions(now.isoformat())

        assert deleted_count == 3
        for token in expired_tokens:
            assert db.get_session(token) is None
        assert db.get_session(valid_token) is not None


class TestSessionPersistence:
    """Test session data persistence across operations."""

    def test_session_data_integrity(self, db, test_user):
        """Test that session data maintains integrity through multiple operations."""
        token = "integrity_token"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        # Create session
        db.create_session(test_user, token, created, expires)
        session1 = db.get_session(token)

        # Update activity
        new_activity = (datetime.now() + timedelta(minutes=5)).isoformat()
        new_expires = (datetime.now() + timedelta(minutes=20)).isoformat()
        db.update_session_activity(token, new_activity, new_expires)
        session2 = db.get_session(token)

        # Verify integrity
        assert session1["session_id"] == session2["session_id"]
        assert session1["user_id"] == session2["user_id"]
        assert session1["session_token"] == session2["session_token"]
        assert session1["created_at"] == session2["created_at"]
        assert session2["last_activity"] == new_activity
        assert session2["expires_at"] == new_expires

    def test_multiple_operations_on_same_session(self, db, test_user):
        """Test performing multiple operations on the same session."""
        token = "multi_op_token"
        created = datetime.now().isoformat()
        expires = (datetime.now() + timedelta(minutes=15)).isoformat()

        # Create
        assert db.create_session(test_user, token, created, expires) is True

        # Read
        session = db.get_session(token)
        assert session is not None

        # Update
        new_activity = (datetime.now() + timedelta(minutes=5)).isoformat()
        new_expires = (datetime.now() + timedelta(minutes=20)).isoformat()
        assert db.update_session_activity(token, new_activity, new_expires) is True

        # Read again
        updated_session = db.get_session(token)
        assert updated_session["last_activity"] == new_activity

        # Delete
        assert db.delete_session(token) is True

        # Verify deleted
        assert db.get_session(token) is None
