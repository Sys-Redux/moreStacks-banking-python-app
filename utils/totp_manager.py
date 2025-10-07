"""
Two-Factor Authentication (2FA) Management Module

This module handles TOTP (Time-based One-Time Password) generation, verification,
backup codes, and QR code generation for authenticator apps.
"""

import pyotp
import qrcode
import secrets
import io
import base64
from typing import Tuple, List, Optional
from PIL import Image


class TOTPManager:
    """
    Manages Two-Factor Authentication using TOTP (Time-based One-Time Password).

    This class provides methods to:
    - Generate TOTP secrets
    - Create QR codes for authenticator apps
    - Verify TOTP tokens
    - Generate and verify backup codes
    """

    def __init__(self, issuer_name: str = "moreStacks Banking"):
        """
        Initialize the TOTP Manager.

        Args:
            issuer_name: Name of the application (shown in authenticator apps)
        """
        self.issuer_name = issuer_name

    def generate_secret(self) -> str:
        """
        Generate a new TOTP secret key.

        Returns:
            Base32-encoded secret key (16 characters)
        """
        return pyotp.random_base32()

    def get_totp_uri(self, secret: str, username: str) -> str:
        """
        Generate TOTP provisioning URI for QR code generation.

        Args:
            secret: Base32-encoded TOTP secret
            username: User's username or email

        Returns:
            TOTP URI string (otpauth://totp/...)
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=self.issuer_name)

    def generate_qr_code(self, secret: str, username: str) -> Image.Image:
        """
        Generate QR code image for TOTP setup.

        Args:
            secret: Base32-encoded TOTP secret
            username: User's username or email

        Returns:
            PIL Image object containing QR code
        """
        uri = self.get_totp_uri(secret, username)

        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        return img

    def get_qr_code_base64(self, secret: str, username: str) -> str:
        """
        Generate QR code as base64-encoded string (for embedding in GUI).

        Args:
            secret: Base32-encoded TOTP secret
            username: User's username or email

        Returns:
            Base64-encoded PNG image string
        """
        img = self.generate_qr_code(secret, username)

        # Convert PIL Image to base64 string
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        img_str = base64.b64encode(buffer.getvalue()).decode()

        return img_str

    def verify_token(self, secret: str, token: str, window: int = 1) -> bool:
        """
        Verify a TOTP token against the secret.

        Args:
            secret: Base32-encoded TOTP secret
            token: 6-digit token from authenticator app
            window: Number of time windows to check (default: 1)
                   Allows for slight clock skew between devices

        Returns:
            True if token is valid, False otherwise
        """
        if not token or not token.isdigit() or len(token) != 6:
            return False

        try:
            totp = pyotp.TOTP(secret)
            return totp.verify(token, valid_window=window)
        except Exception:
            return False

    def get_current_token(self, secret: str) -> str:
        """
        Get the current TOTP token (for testing/debugging only).

        Args:
            secret: Base32-encoded TOTP secret

        Returns:
            Current 6-digit TOTP token
        """
        totp = pyotp.TOTP(secret)
        return totp.now()

    def generate_backup_codes(self, count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery.

        These codes can be used when the user doesn't have access to
        their authenticator app.

        Args:
            count: Number of backup codes to generate (default: 10)

        Returns:
            List of backup codes (format: XXXX-XXXX)
        """
        codes = []
        for _ in range(count):
            # Generate 8-digit code and format as XXXX-XXXX
            code = secrets.token_hex(4).upper()  # 8 hex characters
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes

    def verify_backup_code(
        self, provided_code: str, stored_codes: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code and return remaining codes if valid.

        Args:
            provided_code: Code entered by user
            stored_codes: List of valid backup codes

        Returns:
            Tuple of (is_valid, remaining_code_after_use)
            - is_valid: True if code matches
            - remaining_code_after_use: Code to remove from database (None if invalid)
        """
        # Normalize the provided code (remove spaces, dashes, convert to uppercase)
        normalized = provided_code.replace(" ", "").replace("-", "").upper()

        # Check each stored code
        for stored_code in stored_codes:
            stored_normalized = stored_code.replace("-", "").upper()
            if secrets.compare_digest(normalized, stored_normalized):
                return (True, stored_code)

        return (False, None)

    def format_secret_for_display(self, secret: str) -> str:
        """
        Format secret key for manual entry (groups of 4 characters).

        Args:
            secret: Base32-encoded TOTP secret

        Returns:
            Formatted secret (e.g., "ABCD EFGH IJKL MNOP")
        """
        # Split into groups of 4 characters
        groups = [secret[i : i + 4] for i in range(0, len(secret), 4)]
        return " ".join(groups)

    def get_time_remaining(self) -> int:
        """
        Get seconds remaining until next TOTP token generation.

        Returns:
            Number of seconds until current token expires
        """
        import time

        return 30 - (int(time.time()) % 30)

    def is_setup_complete(self, secret: str, test_token: str) -> bool:
        """
        Verify that 2FA setup is complete by validating a test token.

        Args:
            secret: Base32-encoded TOTP secret
            test_token: Token from user's authenticator app

        Returns:
            True if setup is valid, False otherwise
        """
        return self.verify_token(secret, test_token, window=2)

    @staticmethod
    def validate_secret_format(secret: str) -> bool:
        """
        Validate that a secret key is properly formatted Base32.

        Args:
            secret: Secret key to validate

        Returns:
            True if valid Base32 format, False otherwise
        """
        try:
            # Try to decode as Base32
            base64.b32decode(secret, casefold=True)
            return True
        except Exception:
            return False
