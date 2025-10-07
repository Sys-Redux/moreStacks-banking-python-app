"""
Password Expiration Management Module

This module handles password expiration policies, including:
- Checking if passwords have expired
- Calculating days until expiration
- Determining when to show warnings
- Password age tracking
"""

from datetime import datetime, timedelta
from typing import Optional
from config import SecurityConfig


class PasswordExpirationManager:
    """
    Manages password expiration policies and warnings.

    This class provides methods to check password age, calculate
    expiration status, and determine when to show warning messages.
    """

    def __init__(
        self,
        expiration_days: int = 90,
        warning_days: tuple = (7, 3, 1),
        history_count: int = 5,
        grace_period_days: int = 0,
    ):
        """
        Initialize the password expiration manager.

        Args:
            expiration_days: Number of days before password expires (default: 90)
            warning_days: Tuple of days before expiration to show warnings (default: 7, 3, 1)
            history_count: Number of previous passwords to track (default: 5)
            grace_period_days: Number of days grace period after expiration (default: 0)
        """
        self.expiration_days = expiration_days
        self.warning_days = warning_days  # Keep as tuple
        self.history_count = history_count
        self.grace_period_days = grace_period_days
        # Internal sorted list for logic
        self._warning_days_sorted = sorted(warning_days, reverse=True)

    def is_password_expired(self, password_changed_at: str) -> bool:
        """
        Check if a password has expired.

        Args:
            password_changed_at: ISO format timestamp when password was last changed

        Returns:
            True if password has expired, False otherwise
        """
        if not password_changed_at:
            # If no password change date, consider it expired (force change)
            return True

        try:
            changed_date = datetime.fromisoformat(password_changed_at)
            expiration_date = changed_date + timedelta(days=self.expiration_days)
            return datetime.now() >= expiration_date
        except (ValueError, TypeError):
            # Invalid date format, treat as expired for safety
            return True

    def days_until_expiration(self, password_changed_at: str) -> Optional[int]:
        """
        Calculate the number of days until password expires.

        Args:
            password_changed_at: ISO format timestamp when password was last changed

        Returns:
            Number of days until expiration, or None if invalid date
            Returns negative number if already expired
        """
        if not password_changed_at:
            return -1  # Already expired (changed from 0 for consistency)

        try:
            changed_date = datetime.fromisoformat(password_changed_at)
            expiration_date = changed_date + timedelta(days=self.expiration_days)

            # Normalize to dates (remove time component) for accurate day counting
            expiration_day = expiration_date.date()
            today = datetime.now().date()

            days_left = (expiration_day - today).days
            return days_left
        except (ValueError, TypeError):
            return None

    def should_show_warning(self, password_changed_at: str) -> bool:
        """
        Check if a password expiration warning should be displayed.

        Args:
            password_changed_at: ISO format timestamp when password was last changed

        Returns:
            True if warning should be displayed, False otherwise
        """
        days_left = self.days_until_expiration(password_changed_at)

        if days_left is None:
            return False

        # Show warning if expired
        if days_left <= 0:
            return True

        # Check if days remaining matches any warning threshold
        for warning_day in self._warning_days_sorted:
            if days_left <= warning_day:
                return True

        return False

    def get_warning_level(self, password_changed_at: str) -> str:
        """
        Get the warning level based on days until expiration.

        Args:
            password_changed_at: ISO format timestamp when password was last changed

        Returns:
            Warning level: 'expired', 'critical', 'warning', 'info', or 'ok'
        """
        days_left = self.days_until_expiration(password_changed_at)

        if days_left is None:
            return "expired"

        if days_left <= 0:
            return "expired"
        elif days_left <= 3:
            return "critical"
        elif days_left <= 7:
            return "warning"
        elif days_left <= 14:
            return "info"
        else:
            return "ok"

    def get_expiration_message(self, password_changed_at: str) -> str:
        """
        Get a user-friendly expiration warning message.

        Args:
            password_changed_at: ISO format timestamp when password was last changed

        Returns:
            Formatted warning message
        """
        days_left = self.days_until_expiration(password_changed_at)

        if days_left is None:
            return "Unable to determine password age. Please change your password."

        if days_left <= 0:
            return "Your password has expired. You must change it to continue."
        elif days_left == 1:
            return "⚠️ Your password expires tomorrow! Please change it soon."
        elif days_left <= 3:
            return (
                f"⚠️ Your password expires in {days_left} days. Please change it soon."
            )
        elif days_left <= 7:
            return f"Your password expires in {days_left} days. Consider changing it."
        else:
            return f"Your password expires in {days_left} days."

    def password_age_days(self, password_changed_at: str) -> Optional[int]:
        """
        Calculate the age of the password in days.

        Args:
            password_changed_at: ISO format timestamp when password was last changed

        Returns:
            Number of days since password was changed, or a large number (9999) if invalid/None date
        """
        if not password_changed_at:
            return 9999  # Treat as very old password

        try:
            changed_date = datetime.fromisoformat(password_changed_at)
            age = (datetime.now() - changed_date).days
            return age
        except (ValueError, TypeError):
            return 9999  # Treat as very old password

    def format_expiration_date(self, password_changed_at: str) -> str:
        """
        Format the expiration date as a readable string.

        Args:
            password_changed_at: ISO format timestamp when password was last changed

        Returns:
            Formatted expiration date (e.g., "January 15, 2025")
        """
        if not password_changed_at:
            return "Unknown"

        try:
            changed_date = datetime.fromisoformat(password_changed_at)
            expiration_date = changed_date + timedelta(days=self.expiration_days)
            return expiration_date.strftime("%B %d, %Y")
        except (ValueError, TypeError):
            return "Unknown"

    @staticmethod
    def get_current_timestamp() -> str:
        """
        Get the current timestamp in ISO format.

        Returns:
            Current timestamp as ISO format string
        """
        return datetime.now().isoformat()

    def is_within_grace_period(
        self, password_changed_at: str, grace_days: int = None
    ) -> bool:
        """
        Check if password is within grace period after expiration.

        This allows users to still login for a short period after expiration
        to change their password.

        Args:
            password_changed_at: ISO format timestamp when password was last changed
            grace_days: Number of days grace period (default: uses self.grace_period_days)

        Returns:
            True if within grace period, False otherwise
        """
        # Use instance grace_period_days if not provided
        if grace_days is None:
            grace_days = self.grace_period_days

        if not password_changed_at or grace_days == 0:
            return False

        try:
            changed_date = datetime.fromisoformat(password_changed_at)
            expiration_date = changed_date + timedelta(days=self.expiration_days)
            grace_end_date = expiration_date + timedelta(days=grace_days)

            now = datetime.now()
            return expiration_date <= now < grace_end_date
        except (ValueError, TypeError):
            return False
