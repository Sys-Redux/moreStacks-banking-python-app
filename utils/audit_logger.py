"""
Security Audit Logger for moreStacks Banking Application.

This module provides comprehensive audit logging functionality for tracking
security events, user actions, and system activities.
"""

import json
from datetime import datetime
from typing import Optional, Dict, Any
from database.db_manager import DatabaseManager


class AuditSeverity:
    """Severity levels for audit log entries."""

    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class AuditCategory:
    """Categories for audit log entries."""

    AUTHENTICATION = "AUTHENTICATION"
    AUTHORIZATION = "AUTHORIZATION"
    TRANSACTION = "TRANSACTION"
    ACCOUNT = "ACCOUNT"
    SECURITY = "SECURITY"
    SYSTEM = "SYSTEM"
    DATA_ACCESS = "DATA_ACCESS"


class AuditEventType:
    """Event types for audit logging."""

    # Authentication events
    LOGIN_SUCCESS = "LOGIN_SUCCESS"
    LOGIN_FAILED = "LOGIN_FAILED"
    LOGOUT = "LOGOUT"
    SESSION_TIMEOUT = "SESSION_TIMEOUT"
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"
    ACCOUNT_UNLOCKED = "ACCOUNT_UNLOCKED"

    # Password events
    PASSWORD_CHANGED = "PASSWORD_CHANGED"
    PASSWORD_RESET = "PASSWORD_RESET"
    PASSWORD_EXPIRED = "PASSWORD_EXPIRED"
    PASSWORD_CHANGE_FAILED = "PASSWORD_CHANGE_FAILED"

    # Two-Factor Authentication events
    TWO_FA_ENABLED = "TWO_FA_ENABLED"
    TWO_FA_DISABLED = "TWO_FA_DISABLED"
    TWO_FA_SUCCESS = "TWO_FA_SUCCESS"
    TWO_FA_FAILED = "TWO_FA_FAILED"
    TWO_FA_BACKUP_USED = "TWO_FA_BACKUP_USED"
    TWO_FA_BACKUP_REGENERATED = "TWO_FA_BACKUP_REGENERATED"

    # Transaction events
    DEPOSIT = "DEPOSIT"
    WITHDRAWAL = "WITHDRAWAL"
    TRANSFER = "TRANSFER"
    INTEREST_APPLIED = "INTEREST_APPLIED"
    TRANSACTION_FAILED = "TRANSACTION_FAILED"

    # Account events
    ACCOUNT_CREATED = "ACCOUNT_CREATED"
    ACCOUNT_CLOSED = "ACCOUNT_CLOSED"
    ACCOUNT_MODIFIED = "ACCOUNT_MODIFIED"
    ACCOUNT_VIEW = "ACCOUNT_VIEW"

    # Security events
    SECURITY_SETTINGS_VIEWED = "SECURITY_SETTINGS_VIEWED"
    SECURITY_SETTINGS_CHANGED = "SECURITY_SETTINGS_CHANGED"
    SUSPICIOUS_ACTIVITY = "SUSPICIOUS_ACTIVITY"
    AUDIT_LOG_VIEWED = "AUDIT_LOG_VIEWED"
    AUDIT_LOG_EXPORTED = "AUDIT_LOG_EXPORTED"

    # System events
    SYSTEM_ERROR = "SYSTEM_ERROR"
    DATABASE_ERROR = "DATABASE_ERROR"
    PERMISSION_DENIED = "PERMISSION_DENIED"


class AuditLogger:
    """
    Handles all audit logging operations for the banking application.

    Provides methods to log various security and operational events with
    appropriate severity levels and metadata.
    """

    def __init__(self, db_manager: DatabaseManager):
        """
        Initialize the AuditLogger.

        Args:
            db_manager: Database manager instance for logging operations
        """
        self.db = db_manager

    def _log_event(
        self,
        event_type: str,
        event_category: str,
        description: str,
        severity: str,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Internal method to log an event to the database.

        Args:
            event_type: Type of event (from AuditEventType)
            event_category: Category of event (from AuditCategory)
            description: Human-readable description of the event
            severity: Severity level (from AuditSeverity)
            user_id: User ID associated with the event
            username: Username associated with the event
            ip_address: IP address of the client
            user_agent: User agent string
            metadata: Additional event metadata as dictionary

        Returns:
            bool: True if logged successfully, False otherwise
        """
        try:
            metadata_json = json.dumps(metadata) if metadata else None
            return self.db.create_audit_log(
                user_id=user_id,
                username=username,
                event_type=event_type,
                event_category=event_category,
                description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                severity=severity,
                metadata=metadata_json,
            )
        except Exception as e:
            print(f"Error logging audit event: {e}")
            return False

    # Authentication Events

    def log_login_success(
        self,
        user_id: int,
        username: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        with_2fa: bool = False,
    ) -> bool:
        """
        Log a successful login attempt.

        Args:
            user_id: User ID
            username: Username
            ip_address: IP address of the client
            user_agent: User agent string
            with_2fa: Whether 2FA was used

        Returns:
            bool: True if logged successfully
        """
        description = f"User '{username}' logged in successfully"
        if with_2fa:
            description += " with 2FA"

        return self._log_event(
            event_type=AuditEventType.LOGIN_SUCCESS,
            event_category=AuditCategory.AUTHENTICATION,
            description=description,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"with_2fa": with_2fa},
        )

    def log_login_failed(
        self,
        username: str,
        reason: str,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> bool:
        """
        Log a failed login attempt.

        Args:
            username: Username attempted
            reason: Reason for failure
            ip_address: IP address of the client
            user_agent: User agent string

        Returns:
            bool: True if logged successfully
        """
        return self._log_event(
            event_type=AuditEventType.LOGIN_FAILED,
            event_category=AuditCategory.AUTHENTICATION,
            description=f"Failed login attempt for '{username}': {reason}",
            severity=AuditSeverity.WARNING,
            username=username,
            ip_address=ip_address,
            user_agent=user_agent,
            metadata={"reason": reason},
        )

    def log_logout(
        self,
        user_id: int,
        username: str,
        reason: str = "User initiated",
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Log a user logout.

        Args:
            user_id: User ID
            username: Username
            reason: Reason for logout
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        return self._log_event(
            event_type=AuditEventType.LOGOUT,
            event_category=AuditCategory.AUTHENTICATION,
            description=f"User '{username}' logged out: {reason}",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            metadata={"reason": reason},
        )

    def log_session_timeout(
        self, user_id: int, username: str, duration_minutes: Optional[int] = None
    ) -> bool:
        """
        Log a session timeout.

        Args:
            user_id: User ID
            username: Username
            duration_minutes: Session duration before timeout

        Returns:
            bool: True if logged successfully
        """
        description = f"Session timeout for user '{username}'"
        metadata = {}
        if duration_minutes:
            description += f" after {duration_minutes} minutes of inactivity"
            metadata["duration_minutes"] = duration_minutes

        return self._log_event(
            event_type=AuditEventType.SESSION_TIMEOUT,
            event_category=AuditCategory.AUTHENTICATION,
            description=description,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            metadata=metadata if metadata else None,
        )

    def log_account_locked(
        self,
        username: str,
        reason: str,
        duration_minutes: Optional[int] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Log an account lockout.

        Args:
            username: Username
            reason: Reason for lockout
            duration_minutes: Lockout duration
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        description = f"Account '{username}' locked: {reason}"
        metadata = {"reason": reason}
        if duration_minutes:
            description += f" for {duration_minutes} minutes"
            metadata["duration_minutes"] = duration_minutes

        return self._log_event(
            event_type=AuditEventType.ACCOUNT_LOCKED,
            event_category=AuditCategory.SECURITY,
            description=description,
            severity=AuditSeverity.CRITICAL,
            username=username,
            ip_address=ip_address,
            metadata=metadata,
        )

    # Password Events

    def log_password_changed(
        self,
        user_id: int,
        username: str,
        reason: str = "User initiated",
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Log a password change.

        Args:
            user_id: User ID
            username: Username
            reason: Reason for password change
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        return self._log_event(
            event_type=AuditEventType.PASSWORD_CHANGED,
            event_category=AuditCategory.SECURITY,
            description=f"Password changed for user '{username}': {reason}",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            metadata={"reason": reason},
        )

    def log_password_expired(
        self, user_id: int, username: str, days_since_change: Optional[int] = None
    ) -> bool:
        """
        Log a password expiration event.

        Args:
            user_id: User ID
            username: Username
            days_since_change: Days since last password change

        Returns:
            bool: True if logged successfully
        """
        description = f"Password expired for user '{username}'"
        metadata = {}
        if days_since_change:
            description += f" (last changed {days_since_change} days ago)"
            metadata["days_since_change"] = days_since_change

        return self._log_event(
            event_type=AuditEventType.PASSWORD_EXPIRED,
            event_category=AuditCategory.SECURITY,
            description=description,
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            metadata=metadata if metadata else None,
        )

    # Two-Factor Authentication Events

    def log_2fa_enabled(
        self, user_id: int, username: str, ip_address: Optional[str] = None
    ) -> bool:
        """
        Log 2FA enablement.

        Args:
            user_id: User ID
            username: Username
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        return self._log_event(
            event_type=AuditEventType.TWO_FA_ENABLED,
            event_category=AuditCategory.SECURITY,
            description=f"Two-Factor Authentication enabled for user '{username}'",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )

    def log_2fa_disabled(
        self, user_id: int, username: str, ip_address: Optional[str] = None
    ) -> bool:
        """
        Log 2FA disablement.

        Args:
            user_id: User ID
            username: Username
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        return self._log_event(
            event_type=AuditEventType.TWO_FA_DISABLED,
            event_category=AuditCategory.SECURITY,
            description=f"Two-Factor Authentication disabled for user '{username}'",
            severity=AuditSeverity.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )

    def log_2fa_verification(
        self,
        user_id: int,
        username: str,
        success: bool,
        method: str = "TOTP",
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Log a 2FA verification attempt.

        Args:
            user_id: User ID
            username: Username
            success: Whether verification succeeded
            method: Verification method (TOTP or backup code)
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        if success:
            event_type = AuditEventType.TWO_FA_SUCCESS
            severity = AuditSeverity.INFO
            description = f"2FA verification successful for '{username}' using {method}"
        else:
            event_type = AuditEventType.TWO_FA_FAILED
            severity = AuditSeverity.WARNING
            description = f"2FA verification failed for '{username}' using {method}"

        return self._log_event(
            event_type=event_type,
            event_category=AuditCategory.AUTHENTICATION,
            description=description,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            metadata={"method": method, "success": success},
        )

    def log_2fa_backup_used(
        self,
        user_id: int,
        username: str,
        remaining_codes: int,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Log usage of a 2FA backup code.

        Args:
            user_id: User ID
            username: Username
            remaining_codes: Number of backup codes remaining
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        severity = AuditSeverity.WARNING if remaining_codes < 3 else AuditSeverity.INFO
        description = (
            f"Backup code used by '{username}' ({remaining_codes} codes remaining)"
        )

        return self._log_event(
            event_type=AuditEventType.TWO_FA_BACKUP_USED,
            event_category=AuditCategory.SECURITY,
            description=description,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            metadata={"remaining_codes": remaining_codes},
        )

    def log_2fa_backup_regenerated(
        self, user_id: int, username: str, ip_address: Optional[str] = None
    ) -> bool:
        """
        Log regeneration of 2FA backup codes.

        Args:
            user_id: User ID
            username: Username
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        return self._log_event(
            event_type=AuditEventType.TWO_FA_BACKUP_REGENERATED,
            event_category=AuditCategory.SECURITY,
            description=f"Backup codes regenerated for user '{username}'",
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
        )

    # Transaction Events

    def log_transaction(
        self,
        user_id: int,
        username: str,
        transaction_type: str,
        amount: float,
        account_number: str,
        success: bool = True,
        error_message: Optional[str] = None,
    ) -> bool:
        """
        Log a financial transaction.

        Args:
            user_id: User ID
            username: Username
            transaction_type: Type of transaction
            amount: Transaction amount
            account_number: Account number
            success: Whether transaction succeeded
            error_message: Error message if failed

        Returns:
            bool: True if logged successfully
        """
        if success:
            description = (
                f"{transaction_type} of ${amount:.2f} for account {account_number}"
            )
            severity = AuditSeverity.INFO
            event_type = transaction_type.upper().replace(" ", "_")
        else:
            description = f"Failed {transaction_type} of ${amount:.2f}: {error_message}"
            severity = AuditSeverity.WARNING
            event_type = AuditEventType.TRANSACTION_FAILED

        return self._log_event(
            event_type=event_type,
            event_category=AuditCategory.TRANSACTION,
            description=description,
            severity=severity,
            user_id=user_id,
            username=username,
            metadata={
                "transaction_type": transaction_type,
                "amount": amount,
                "account_number": account_number,
                "success": success,
                "error_message": error_message,
            },
        )

    # Account Events

    def log_account_action(
        self,
        user_id: int,
        username: str,
        action: str,
        account_number: str,
        details: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log an account-related action.

        Args:
            user_id: User ID
            username: Username
            action: Action performed
            account_number: Account number
            details: Additional details

        Returns:
            bool: True if logged successfully
        """
        event_type = action.upper().replace(" ", "_")
        description = f"Account {action}: {account_number}"

        metadata = {"action": action, "account_number": account_number}
        if details:
            metadata.update(details)

        return self._log_event(
            event_type=event_type,
            event_category=AuditCategory.ACCOUNT,
            description=description,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            metadata=metadata,
        )

    # Security Events

    def log_security_event(
        self,
        event_type: str,
        description: str,
        severity: str = AuditSeverity.WARNING,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Log a general security event.

        Args:
            event_type: Type of security event
            description: Event description
            severity: Severity level
            user_id: User ID if applicable
            username: Username if applicable
            ip_address: IP address if applicable
            metadata: Additional metadata

        Returns:
            bool: True if logged successfully
        """
        return self._log_event(
            event_type=event_type,
            event_category=AuditCategory.SECURITY,
            description=description,
            severity=severity,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            metadata=metadata,
        )

    def log_audit_access(
        self,
        user_id: int,
        username: str,
        action: str,
        details: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> bool:
        """
        Log access to audit logs.

        Args:
            user_id: User ID
            username: Username
            action: Action performed (viewed, exported)
            details: Additional details
            ip_address: IP address of the client

        Returns:
            bool: True if logged successfully
        """
        event_type = (
            AuditEventType.AUDIT_LOG_EXPORTED
            if action == "exported"
            else AuditEventType.AUDIT_LOG_VIEWED
        )
        description = f"Audit logs {action} by '{username}'"
        if details:
            description += f": {details}"

        return self._log_event(
            event_type=event_type,
            event_category=AuditCategory.SECURITY,
            description=description,
            severity=AuditSeverity.INFO,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            metadata={"action": action, "details": details},
        )
