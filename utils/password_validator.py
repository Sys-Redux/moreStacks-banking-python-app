"""Password validation and strength checking utilities."""

import re
from typing import Tuple


class PasswordValidator:
    """Validates password strength and enforces security requirements."""

    # Password requirements
    MIN_LENGTH = 8
    REQUIRE_UPPERCASE = True
    REQUIRE_LOWERCASE = True
    REQUIRE_DIGIT = True
    REQUIRE_SPECIAL = True

    SPECIAL_CHARACTERS = "!@#$%^&*()_+-=[]{}|;:,.<>?"

    @classmethod
    def validate_password(cls, password: str) -> Tuple[bool, str]:
        """
        Validate password against security requirements.

        Args:
            password: The password to validate

        Returns:
            Tuple of (is_valid, message)
            - is_valid: True if password meets all requirements
            - message: Descriptive message about validation result
        """
        if not password:
            return False, "Password cannot be empty"

        # Check minimum length
        if len(password) < cls.MIN_LENGTH:
            return False, f"Password must be at least {cls.MIN_LENGTH} characters long"

        # Check for uppercase letter
        if cls.REQUIRE_UPPERCASE and not re.search(r"[A-Z]", password):
            return False, "Password must contain at least one uppercase letter"

        # Check for lowercase letter
        if cls.REQUIRE_LOWERCASE and not re.search(r"[a-z]", password):
            return False, "Password must contain at least one lowercase letter"

        # Check for digit
        if cls.REQUIRE_DIGIT and not re.search(r"\d", password):
            return False, "Password must contain at least one digit"

        # Check for special character
        if cls.REQUIRE_SPECIAL:
            special_pattern = f"[{re.escape(cls.SPECIAL_CHARACTERS)}]"
            if not re.search(special_pattern, password):
                return (
                    False,
                    f"Password must contain at least one special character ({cls.SPECIAL_CHARACTERS})",
                )

        # All checks passed
        return True, "Password meets all security requirements"

    @classmethod
    def get_password_strength(cls, password: str) -> str:
        """
        Calculate password strength rating.

        Args:
            password: The password to evaluate

        Returns:
            String rating: 'Weak', 'Medium', 'Strong', or 'Very Strong'
        """
        if not password:
            return "Weak"

        strength_score = 0

        # Length scoring
        if len(password) >= 8:
            strength_score += 1
        if len(password) >= 12:
            strength_score += 1
        if len(password) >= 16:
            strength_score += 1

        # Character type scoring
        if re.search(r"[a-z]", password):
            strength_score += 1
        if re.search(r"[A-Z]", password):
            strength_score += 1
        if re.search(r"\d", password):
            strength_score += 1
        if re.search(f"[{re.escape(cls.SPECIAL_CHARACTERS)}]", password):
            strength_score += 1

        # Variety scoring (multiple character types)
        char_types = sum(
            [
                bool(re.search(r"[a-z]", password)),
                bool(re.search(r"[A-Z]", password)),
                bool(re.search(r"\d", password)),
                bool(re.search(f"[{re.escape(cls.SPECIAL_CHARACTERS)}]", password)),
            ]
        )

        if char_types >= 3:
            strength_score += 1
        if char_types == 4:
            strength_score += 1

        # Map score to rating
        if strength_score <= 3:
            return "Weak"
        elif strength_score <= 5:
            return "Medium"
        elif strength_score <= 7:
            return "Strong"
        else:
            return "Very Strong"

    @classmethod
    def get_requirements_text(cls) -> str:
        """Get a formatted string describing password requirements."""
        requirements = [f"• At least {cls.MIN_LENGTH} characters long"]

        if cls.REQUIRE_UPPERCASE:
            requirements.append("• At least one uppercase letter (A-Z)")
        if cls.REQUIRE_LOWERCASE:
            requirements.append("• At least one lowercase letter (a-z)")
        if cls.REQUIRE_DIGIT:
            requirements.append("• At least one digit (0-9)")
        if cls.REQUIRE_SPECIAL:
            requirements.append(
                f"• At least one special character ({cls.SPECIAL_CHARACTERS})"
            )

        return "\n".join(requirements)
