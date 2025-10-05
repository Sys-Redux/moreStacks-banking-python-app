"""Interest calculation and scheduling utilities for savings accounts."""

from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional


class InterestScheduler:
    """Handles automated interest application for savings accounts."""

    # Interest application frequency (in days)
    INTEREST_PERIOD_DAYS = 30  # Monthly interest

    @staticmethod
    def calculate_days_since_last_interest(last_interest_date: Optional[str]) -> int:
        """
        Calculate the number of days since interest was last applied.

        Args:
            last_interest_date: ISO format date string or None

        Returns:
            Number of days since last interest application
        """
        if not last_interest_date:
            return float('inf')  # Never applied

        last_date = datetime.fromisoformat(last_interest_date)
        now = datetime.now()
        delta = now - last_date
        return delta.days

    @staticmethod
    def should_apply_interest(last_interest_date: Optional[str]) -> bool:
        """
        Determine if interest should be applied based on last application date.

        Args:
            last_interest_date: ISO format date string or None

        Returns:
            True if interest should be applied, False otherwise
        """
        if not last_interest_date:
            return True  # Never applied, should apply now

        days_since = InterestScheduler.calculate_days_since_last_interest(last_interest_date)
        return days_since >= InterestScheduler.INTEREST_PERIOD_DAYS

    @staticmethod
    def calculate_interest_amount(balance: float, annual_rate: float, days: int = 30) -> float:
        """
        Calculate interest amount for a given balance and rate.
        Uses simple interest calculation: Interest = Principal × Rate × Time

        Args:
            balance: Current account balance
            annual_rate: Annual interest rate (e.g., 0.02 for 2%)
            days: Number of days to calculate interest for (default 30)

        Returns:
            Interest amount
        """
        if balance <= 0 or annual_rate <= 0:
            return 0.0

        # Calculate interest for the period
        # Daily rate = annual_rate / 365
        # Interest = balance × (daily_rate × days)
        daily_rate = annual_rate / 365
        interest = balance * (daily_rate * days)

        return round(interest, 2)

    @staticmethod
    def get_next_interest_date(last_interest_date: Optional[str]) -> datetime:
        """
        Calculate the next interest application date.

        Args:
            last_interest_date: ISO format date string or None

        Returns:
            Datetime object representing next interest date
        """
        if not last_interest_date:
            # If never applied, next date is 30 days from now
            return datetime.now() + timedelta(days=InterestScheduler.INTEREST_PERIOD_DAYS)

        last_date = datetime.fromisoformat(last_interest_date)
        next_date = last_date + timedelta(days=InterestScheduler.INTEREST_PERIOD_DAYS)

        # If next date is in the past, calculate from current date
        if next_date < datetime.now():
            return datetime.now() + timedelta(days=InterestScheduler.INTEREST_PERIOD_DAYS)

        return next_date

    @staticmethod
    def format_next_interest_date(last_interest_date: Optional[str]) -> str:
        """
        Get a formatted string for the next interest application date.

        Args:
            last_interest_date: ISO format date string or None

        Returns:
            Formatted date string (e.g., "Nov 5, 2025")
        """
        next_date = InterestScheduler.get_next_interest_date(last_interest_date)
        return next_date.strftime("%b %d, %Y")

    @staticmethod
    def get_days_until_interest(last_interest_date: Optional[str]) -> int:
        """
        Calculate days remaining until next interest application.

        Args:
            last_interest_date: ISO format date string or None

        Returns:
            Number of days until interest is applied (0 if overdue)
        """
        next_date = InterestScheduler.get_next_interest_date(last_interest_date)
        now = datetime.now()
        delta = next_date - now

        return max(0, delta.days)

    @staticmethod
    def format_time_until_interest(last_interest_date: Optional[str]) -> str:
        """
        Get a human-readable string for time until interest.

        Args:
            last_interest_date: ISO format date string or None

        Returns:
            Formatted string (e.g., "5 days", "Due now", "Never applied")
        """
        if not last_interest_date:
            return "Due now (never applied)"

        days_until = InterestScheduler.get_days_until_interest(last_interest_date)

        if days_until == 0:
            return "Due now"
        elif days_until == 1:
            return "1 day"
        else:
            return f"{days_until} days"

    @staticmethod
    def get_interest_history_summary(transactions: List[Dict]) -> Dict:
        """
        Analyze transaction history to get interest application summary.

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Dictionary with interest statistics
        """
        interest_transactions = [
            t for t in transactions
            if t.get('category') == 'Interest' or 'interest' in t.get('description', '').lower()
        ]

        total_interest = sum(t.get('amount', 0) for t in interest_transactions)
        count = len(interest_transactions)

        last_interest = None
        if interest_transactions:
            # Transactions are sorted by timestamp DESC
            last_interest = interest_transactions[0].get('timestamp')

        return {
            'total_interest_earned': round(total_interest, 2),
            'interest_applications': count,
            'last_interest_date': last_interest,
            'average_interest': round(total_interest / count, 2) if count > 0 else 0
        }
