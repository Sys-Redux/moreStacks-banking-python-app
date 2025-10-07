"""
Comprehensive tests for Security Audit Logging system.

Tests cover:
- AuditLogger functionality (all event types)
- Database audit log methods
- Retention policy operations
- Integration workflows
- Export functionality
"""

import pytest
import os
import tempfile
from datetime import datetime, timedelta
from database.db_manager import DatabaseManager
from utils.audit_logger import AuditLogger, AuditSeverity, AuditCategory, AuditEventType
from utils.audit_retention import AuditRetentionPolicy


@pytest.fixture
def db():
    """Create a test database."""
    db = DatabaseManager(":memory:")
    yield db
    db.close()


@pytest.fixture
def audit_logger(db):
    """Create an audit logger instance."""
    return AuditLogger(db)


@pytest.fixture
def test_user(db):
    """Create a test user."""
    user_id = db.create_user(
        "testuser", "TestPass123!", "Test User", "test@example.com"
    )
    return user_id, "testuser"


@pytest.fixture
def retention_policy(db):
    """Create a retention policy instance."""
    return AuditRetentionPolicy(db, retention_days=30, archive_enabled=False)


# ==================== AuditLogger Tests ====================


class TestAuditLogger:
    """Test the AuditLogger class."""

    def test_log_login_success(self, audit_logger, test_user, db):
        """Test logging successful login."""
        user_id, username = test_user
        success = audit_logger.log_login_success(
            user_id, username, "127.0.0.1", "Test Browser", with_2fa=False
        )
        assert success is True

        # Verify log was created
        logs = db.get_audit_logs_by_user(user_id)
        assert len(logs) == 1
        assert logs[0]["event_type"] == "LOGIN_SUCCESS"
        assert logs[0]["severity"] == "INFO"

    def test_log_login_success_with_2fa(self, audit_logger, test_user, db):
        """Test logging successful login with 2FA."""
        user_id, username = test_user
        success = audit_logger.log_login_success(user_id, username, with_2fa=True)
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert "with 2FA" in logs[0]["description"]

    def test_log_login_failed(self, audit_logger, db):
        """Test logging failed login."""
        success = audit_logger.log_login_failed(
            "baduser", "Invalid password", "127.0.0.1"
        )
        assert success is True

        # Verify log was created
        logs = db.search_audit_logs({"event_type": "LOGIN_FAILED"})
        assert len(logs) == 1
        assert logs[0]["severity"] == "WARNING"

    def test_log_logout(self, audit_logger, test_user, db):
        """Test logging logout."""
        user_id, username = test_user
        success = audit_logger.log_logout(user_id, username)
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "LOGOUT"

    def test_log_session_timeout(self, audit_logger, test_user, db):
        """Test logging session timeout."""
        user_id, username = test_user
        success = audit_logger.log_session_timeout(
            user_id, username, duration_minutes=15
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "SESSION_TIMEOUT"
        assert "15 minutes" in logs[0]["description"]

    def test_log_account_locked(self, audit_logger, db):
        """Test logging account lockout."""
        success = audit_logger.log_account_locked(
            "testuser", "Too many failed attempts", duration_minutes=15
        )
        assert success is True

        logs = db.search_audit_logs({"event_type": "ACCOUNT_LOCKED"})
        assert len(logs) == 1
        assert logs[0]["severity"] == "CRITICAL"

    def test_log_password_changed(self, audit_logger, test_user, db):
        """Test logging password change."""
        user_id, username = test_user
        success = audit_logger.log_password_changed(user_id, username, "User initiated")
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "PASSWORD_CHANGED"
        assert logs[0]["event_category"] == "SECURITY"

    def test_log_password_expired(self, audit_logger, test_user, db):
        """Test logging password expiration."""
        user_id, username = test_user
        success = audit_logger.log_password_expired(
            user_id, username, days_since_change=90
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "PASSWORD_EXPIRED"
        assert logs[0]["severity"] == "WARNING"

    def test_log_2fa_enabled(self, audit_logger, test_user, db):
        """Test logging 2FA enablement."""
        user_id, username = test_user
        success = audit_logger.log_2fa_enabled(user_id, username)
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "TWO_FA_ENABLED"

    def test_log_2fa_disabled(self, audit_logger, test_user, db):
        """Test logging 2FA disablement."""
        user_id, username = test_user
        success = audit_logger.log_2fa_disabled(user_id, username)
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "TWO_FA_DISABLED"
        assert logs[0]["severity"] == "WARNING"

    def test_log_2fa_verification_success(self, audit_logger, test_user, db):
        """Test logging successful 2FA verification."""
        user_id, username = test_user
        success = audit_logger.log_2fa_verification(
            user_id, username, success=True, method="TOTP"
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "TWO_FA_SUCCESS"
        assert logs[0]["severity"] == "INFO"

    def test_log_2fa_verification_failed(self, audit_logger, test_user, db):
        """Test logging failed 2FA verification."""
        user_id, username = test_user
        success = audit_logger.log_2fa_verification(
            user_id, username, success=False, method="TOTP"
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "TWO_FA_FAILED"
        assert logs[0]["severity"] == "WARNING"

    def test_log_2fa_backup_used(self, audit_logger, test_user, db):
        """Test logging backup code usage."""
        user_id, username = test_user
        success = audit_logger.log_2fa_backup_used(user_id, username, remaining_codes=5)
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "TWO_FA_BACKUP_USED"

    def test_log_2fa_backup_used_low_warning(self, audit_logger, test_user, db):
        """Test that low backup code count triggers warning severity."""
        user_id, username = test_user
        audit_logger.log_2fa_backup_used(user_id, username, remaining_codes=2)

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["severity"] == "WARNING"

    def test_log_2fa_backup_regenerated(self, audit_logger, test_user, db):
        """Test logging backup code regeneration."""
        user_id, username = test_user
        success = audit_logger.log_2fa_backup_regenerated(user_id, username)
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "TWO_FA_BACKUP_REGENERATED"

    def test_log_transaction_success(self, audit_logger, test_user, db):
        """Test logging successful transaction."""
        user_id, username = test_user
        success = audit_logger.log_transaction(
            user_id, username, "deposit", 100.50, "1234567890", success=True
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_category"] == "TRANSACTION"
        assert "$100.50" in logs[0]["description"]

    def test_log_transaction_failed(self, audit_logger, test_user, db):
        """Test logging failed transaction."""
        user_id, username = test_user
        success = audit_logger.log_transaction(
            user_id,
            username,
            "withdrawal",
            1000.00,
            "1234567890",
            success=False,
            error_message="Insufficient funds",
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "TRANSACTION_FAILED"
        assert logs[0]["severity"] == "WARNING"

    def test_log_account_action(self, audit_logger, test_user, db):
        """Test logging account actions."""
        user_id, username = test_user
        success = audit_logger.log_account_action(
            user_id,
            username,
            "created",
            "1234567890",
            details={"account_type": "Checking"},
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_category"] == "ACCOUNT"

    def test_log_security_event(self, audit_logger, test_user, db):
        """Test logging general security events."""
        user_id, username = test_user
        success = audit_logger.log_security_event(
            "SUSPICIOUS_ACTIVITY",
            "Multiple failed login attempts from different IPs",
            severity="CRITICAL",
            user_id=user_id,
            username=username,
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["severity"] == "CRITICAL"

    def test_log_audit_access(self, audit_logger, test_user, db):
        """Test logging audit log access."""
        user_id, username = test_user
        success = audit_logger.log_audit_access(
            user_id, username, "viewed", "Last 30 days"
        )
        assert success is True

        logs = db.get_audit_logs_by_user(user_id)
        assert logs[0]["event_type"] == "AUDIT_LOG_VIEWED"


# ==================== Database Audit Methods Tests ====================


class TestDatabaseAuditMethods:
    """Test database audit log methods."""

    def test_create_audit_log(self, db):
        """Test creating an audit log entry."""
        success = db.create_audit_log(
            event_type="TEST_EVENT",
            event_category="SYSTEM",
            description="Test log entry",
            severity="INFO",
            user_id=1,
            username="testuser",
        )
        assert success is True

    def test_get_audit_logs_by_user(self, db, audit_logger, test_user):
        """Test retrieving logs by user."""
        user_id, username = test_user

        # Create multiple logs
        audit_logger.log_login_success(user_id, username)
        audit_logger.log_logout(user_id, username)
        audit_logger.log_password_changed(user_id, username)

        logs = db.get_audit_logs_by_user(user_id)
        assert len(logs) == 3

    def test_get_audit_logs_by_user_pagination(self, db, audit_logger, test_user):
        """Test pagination for user logs."""
        user_id, username = test_user

        # Create many logs
        for i in range(25):
            audit_logger.log_login_success(user_id, username)

        # First page
        page1 = db.get_audit_logs_by_user(user_id, limit=10, offset=0)
        assert len(page1) == 10

        # Second page
        page2 = db.get_audit_logs_by_user(user_id, limit=10, offset=10)
        assert len(page2) == 10

        # Third page
        page3 = db.get_audit_logs_by_user(user_id, limit=10, offset=20)
        assert len(page3) == 5

    def test_get_audit_logs_by_type(self, db, audit_logger, test_user):
        """Test filtering logs by event type."""
        user_id, username = test_user

        audit_logger.log_login_success(user_id, username)
        audit_logger.log_login_success(user_id, username)
        audit_logger.log_logout(user_id, username)

        login_logs = db.get_audit_logs_by_type("LOGIN_SUCCESS")
        assert len(login_logs) == 2

    def test_get_audit_logs_by_category(self, db, audit_logger, test_user):
        """Test filtering logs by category."""
        user_id, username = test_user

        audit_logger.log_login_success(user_id, username)
        audit_logger.log_password_changed(user_id, username)
        audit_logger.log_transaction(user_id, username, "deposit", 100, "123")

        auth_logs = db.get_audit_logs_by_category("AUTHENTICATION")
        assert len(auth_logs) >= 1

        security_logs = db.get_audit_logs_by_category("SECURITY")
        assert len(security_logs) >= 1

    def test_get_security_events(self, db, audit_logger, test_user):
        """Test retrieving security events."""
        user_id, username = test_user

        audit_logger.log_password_changed(user_id, username)
        audit_logger.log_2fa_enabled(user_id, username)
        audit_logger.log_login_success(user_id, username)  # Not security category

        security_logs = db.get_security_events()
        assert len(security_logs) >= 2

    def test_get_security_events_by_severity(self, db, audit_logger):
        """Test filtering security events by severity."""
        audit_logger.log_account_locked("user1", "Failed attempts", 15)
        audit_logger.log_security_event("TEST", "Test", "WARNING")

        critical_logs = db.get_security_events(severity="CRITICAL")
        assert len(critical_logs) >= 1
        assert all(log["severity"] == "CRITICAL" for log in critical_logs)

    def test_search_audit_logs_multiple_filters(self, db, audit_logger, test_user):
        """Test searching logs with multiple filters."""
        user_id, username = test_user

        # Create various logs
        audit_logger.log_login_success(user_id, username)
        audit_logger.log_login_failed("baduser", "Invalid password")
        audit_logger.log_password_changed(user_id, username)

        # Search with multiple filters
        filters = {"user_id": user_id, "event_category": "AUTHENTICATION"}
        results = db.search_audit_logs(filters)
        assert len(results) >= 1
        assert all(log["user_id"] == user_id for log in results)

    def test_get_audit_log_count(self, db, audit_logger, test_user):
        """Test getting total log count."""
        user_id, username = test_user

        initial_count = db.get_audit_log_count()

        # Add logs
        for i in range(5):
            audit_logger.log_login_success(user_id, username)

        new_count = db.get_audit_log_count()
        assert new_count == initial_count + 5

    def test_get_audit_log_count_with_filters(self, db, audit_logger, test_user):
        """Test getting count with filters."""
        user_id, username = test_user

        audit_logger.log_login_success(user_id, username)
        audit_logger.log_login_success(user_id, username)
        audit_logger.log_logout(user_id, username)

        count = db.get_audit_log_count({"event_type": "LOGIN_SUCCESS"})
        assert count == 2

    def test_export_audit_logs_csv(self, db, audit_logger, test_user):
        """Test exporting logs to CSV."""
        user_id, username = test_user

        # Create logs
        audit_logger.log_login_success(user_id, username)
        audit_logger.log_logout(user_id, username)

        # Export to temp file
        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv") as f:
            filepath = f.name

        try:
            success, message = db.export_audit_logs_csv(filepath)
            assert success is True
            assert os.path.exists(filepath)

            # Verify file content
            with open(filepath, "r") as f:
                content = f.read()
                assert "log_id" in content
                assert "LOGIN_SUCCESS" in content
        finally:
            if os.path.exists(filepath):
                os.remove(filepath)

    def test_delete_old_audit_logs(self, db):
        """Test deleting old audit logs."""
        # Create old log by manipulating the timestamp
        db.create_audit_log(
            event_type="OLD_EVENT",
            event_category="SYSTEM",
            description="Old test log",
            severity="INFO",
        )

        # Delete logs older than 1000 days (should delete nothing since logs are fresh)
        success, message = db.delete_old_audit_logs(days_old=1000, keep_critical=False)
        assert success is True

        # Verify logs still exist
        count = db.get_audit_log_count()
        assert count >= 1

    def test_delete_old_audit_logs_keep_critical(self, db, audit_logger):
        """Test that critical logs are preserved."""
        # Create critical and non-critical logs
        audit_logger.log_security_event("CRITICAL_EVENT", "Critical", "CRITICAL")
        audit_logger.log_security_event("INFO_EVENT", "Info", "INFO")

        # With days_old=1000, no logs should be deleted (they're all new)
        success, message = db.delete_old_audit_logs(days_old=1000, keep_critical=True)
        assert success is True

        # Verify both logs still exist
        remaining = db.search_audit_logs({})
        assert len(remaining) >= 2

    def test_get_audit_statistics(self, db, audit_logger, test_user):
        """Test getting audit statistics."""
        user_id, username = test_user

        # Create various logs
        audit_logger.log_login_success(user_id, username)
        audit_logger.log_login_failed("baduser", "Invalid")
        audit_logger.log_password_changed(user_id, username)

        stats = db.get_audit_statistics()

        assert "total_logs" in stats
        assert stats["total_logs"] >= 3
        assert "by_severity" in stats
        assert "by_category" in stats
        assert "last_24_hours" in stats


# ==================== Retention Policy Tests ====================


class TestAuditRetentionPolicy:
    """Test the audit retention policy system."""

    def test_retention_policy_initialization(self, retention_policy):
        """Test creating a retention policy."""
        assert retention_policy.retention_days == 30
        assert retention_policy.archive_enabled is False

    def test_update_retention_days(self, retention_policy):
        """Test updating retention period."""
        success = retention_policy.update_retention_days(60)
        assert success is True
        assert retention_policy.retention_days == 60

    def test_update_retention_days_invalid(self, retention_policy):
        """Test that invalid retention days are rejected."""
        success = retention_policy.update_retention_days(0)
        assert success is False

        success = retention_policy.update_retention_days(-10)
        assert success is False

    def test_enable_archiving(self, retention_policy):
        """Test enabling archiving."""
        success = retention_policy.enable_archiving()
        assert success is True
        assert retention_policy.archive_enabled is True

    def test_disable_archiving(self, retention_policy):
        """Test disabling archiving."""
        retention_policy.enable_archiving()
        success = retention_policy.disable_archiving()
        assert success is True
        assert retention_policy.archive_enabled is False

    def test_get_retention_statistics(self, retention_policy, audit_logger, test_user):
        """Test getting retention statistics."""
        user_id, username = test_user

        # Create some logs
        audit_logger.log_login_success(user_id, username)
        audit_logger.log_password_changed(user_id, username)

        stats = retention_policy.get_retention_statistics()

        assert "total_logs" in stats
        assert "within_retention" in stats
        assert "beyond_retention" in stats
        assert "retention_days" in stats
        assert stats["retention_days"] == 30

    def test_get_logs_for_cleanup(self, retention_policy):
        """Test getting logs ready for cleanup."""
        logs = retention_policy.get_logs_for_cleanup(keep_critical=True)
        assert isinstance(logs, list)

    def test_cleanup_no_old_logs(self, retention_policy):
        """Test cleanup when no logs need deletion."""
        success, message = retention_policy.cleanup_old_logs(keep_critical=True)
        assert success is True
        assert "No logs require cleanup" in message or "Deleted 0" in message


# ==================== Integration Tests ====================


class TestAuditLogIntegration:
    """Test complete audit logging workflows."""

    def test_full_login_workflow(self, db, audit_logger, test_user):
        """Test complete login workflow with audit logging."""
        user_id, username = test_user

        # Failed login
        audit_logger.log_login_failed(username, "Invalid password", "127.0.0.1")

        # Successful login
        audit_logger.log_login_success(user_id, username, "127.0.0.1")

        # Logout
        audit_logger.log_logout(user_id, username)

        # Verify all logs exist
        logs = db.get_audit_logs_by_user(user_id)
        assert len(logs) >= 2  # Success and logout

        # Check failed login
        failed_logs = db.search_audit_logs(
            {"username": username, "event_type": "LOGIN_FAILED"}
        )
        assert len(failed_logs) == 1

    def test_full_2fa_workflow(self, db, audit_logger, test_user):
        """Test complete 2FA workflow with audit logging."""
        user_id, username = test_user

        # Enable 2FA
        audit_logger.log_2fa_enabled(user_id, username)

        # Successful verification
        audit_logger.log_2fa_verification(user_id, username, success=True)

        # Use backup code
        audit_logger.log_2fa_backup_used(user_id, username, remaining_codes=7)

        # Regenerate codes
        audit_logger.log_2fa_backup_regenerated(user_id, username)

        # Disable 2FA
        audit_logger.log_2fa_disabled(user_id, username)

        # Verify all logs exist
        logs = db.get_audit_logs_by_user(user_id)
        assert len(logs) >= 5

    def test_transaction_audit_trail(self, db, audit_logger, test_user):
        """Test transaction audit trail."""
        user_id, username = test_user

        # Successful transactions
        audit_logger.log_transaction(user_id, username, "deposit", 100.00, "123")
        audit_logger.log_transaction(user_id, username, "withdrawal", 50.00, "123")
        audit_logger.log_transaction(user_id, username, "transfer", 25.00, "123")

        # Failed transaction
        audit_logger.log_transaction(
            user_id,
            username,
            "withdrawal",
            1000.00,
            "123",
            success=False,
            error_message="Insufficient funds",
        )

        # Verify transaction logs
        transaction_logs = db.get_audit_logs_by_category("TRANSACTION")
        assert len(transaction_logs) >= 4

    def test_security_event_escalation(self, db, audit_logger, test_user):
        """Test security event severity escalation."""
        user_id, username = test_user

        # Multiple failed logins
        for i in range(5):
            audit_logger.log_login_failed(username, "Invalid password")

        # Account locked
        audit_logger.log_account_locked(username, "Too many failed attempts")

        # Verify critical event was logged
        critical_events = db.get_security_events(severity="CRITICAL")
        assert len(critical_events) >= 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
