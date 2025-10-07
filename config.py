"""
Configuration file for moreStacks Banking Application
Centralizes all configurable values for easy maintenance and customization
"""

# Database Configuration
DATABASE_PATH = "moreStacks.db"


# Account Default Values
class AccountDefaults:
    """Default values for different account types."""

    # Checking Account
    CHECKING_OVERDRAFT_LIMIT = 500.0

    # Savings Account
    SAVINGS_INTEREST_RATE = 0.02  # 2% annual interest
    SAVINGS_MIN_BALANCE = 100.0
    SAVINGS_MAX_MONTHLY_WITHDRAWALS = 6

    # Credit Account
    CREDIT_LIMIT = 5000.0
    CREDIT_INTEREST_RATE = 0.18  # 18% APR


# Security Configuration
class SecurityConfig:
    """Security-related settings."""

    # Password Requirements
    PASSWORD_MIN_LENGTH = 8
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT = True
    PASSWORD_REQUIRE_SPECIAL = True

    # Account Lockout
    MAX_LOGIN_ATTEMPTS = 5
    LOCKOUT_DURATION_MINUTES = 15

    # bcrypt
    BCRYPT_ROUNDS = 10  # Number of hashing rounds

    # Session Management (NEW in v2.5)
    SESSION_TIMEOUT_MINUTES = 15  # Auto-logout after inactivity
    SESSION_WARNING_MINUTES = 1  # Warning before timeout
    SESSION_CLEANUP_INTERVAL = 60  # Cleanup expired sessions every 60 seconds

    # Password Expiration (NEW in v2.6)
    PASSWORD_EXPIRATION_DAYS = 90  # Password must be changed after 90 days
    PASSWORD_WARNING_DAYS = (7, 3, 1)  # Show warnings at these day thresholds
    PASSWORD_HISTORY_COUNT = 5  # Remember last 5 passwords to prevent reuse
    PASSWORD_GRACE_PERIOD_DAYS = 0  # Days to allow login after expiration (0 = none)


# Interest Automation
class InterestConfig:
    """Interest calculation settings."""

    INTEREST_CYCLE_DAYS = 30  # Apply interest every 30 days
    DAYS_PER_YEAR = 365  # For interest calculation


# Transaction Categories
TRANSACTION_CATEGORIES = [
    "Uncategorized",
    "Food & Dining",
    "Shopping",
    "Transportation",
    "Bills & Utilities",
    "Entertainment",
    "Healthcare",
    "Travel",
    "Personal",
    "Transfer",
    "Other",
]


# GUI Configuration
class GUIConfig:
    """GUI-related settings."""

    # Window Dimensions
    MAIN_WINDOW_WIDTH = 1200
    MAIN_WINDOW_HEIGHT = 750
    CHARTS_WINDOW_WIDTH = 1200
    CHARTS_WINDOW_HEIGHT = 800

    # Formatting
    CURRENCY_SYMBOL = "$"
    DECIMAL_PLACES = 2

    # Date Format
    DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    DATE_FORMAT_SHORT = "%Y-%m-%d"


# Export Configuration
class ExportConfig:
    """Export and reporting settings."""

    CSV_DELIMITER = ","
    CSV_ENCODING = "utf-8"

    # Default export directory (None = current directory)
    DEFAULT_EXPORT_DIR = None


# Testing Configuration
class TestConfig:
    """Testing-related settings."""

    TEST_DB_PATH = "test_bank.db"
    TEST_USER_PASSWORD = "TestPass123!"


# Application Metadata
APP_NAME = "moreStacks Banking"
APP_VERSION = "2.5"  # Updated with Session Management
APP_TAGLINE = "Banking Made Simple"
