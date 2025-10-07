"""Comprehensive tests for Two-Factor Authentication functionality."""

import pytest
import time
from datetime import datetime, timedelta
from utils.totp_manager import TOTPManager
from database.db_manager import DatabaseManager


class TestTOTPManager:
    """Test TOTP Manager functionality."""

    def test_generate_secret(self):
        """Test secret generation."""
        manager = TOTPManager()
        secret = manager.generate_secret()

        assert secret is not None
        assert isinstance(secret, str)
        assert len(secret) == 32  # Base32 encoded secret
        # Base32 alphabet check
        assert all(c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567=" for c in secret)

    def test_generate_secret_uniqueness(self):
        """Test that generated secrets are unique."""
        manager = TOTPManager()
        secrets = [manager.generate_secret() for _ in range(10)]

        # All secrets should be unique
        assert len(secrets) == len(set(secrets))

    def test_get_totp_uri(self):
        """Test TOTP URI generation."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        username = "testuser"

        uri = manager.get_totp_uri(secret, username)

        assert uri.startswith("otpauth://totp/")
        assert "moreStacks%20Banking" in uri
        assert username in uri
        assert f"secret={secret}" in uri
        assert "issuer=moreStacks%20Banking" in uri

    def test_verify_token_valid(self):
        """Test TOTP token verification with valid code."""
        manager = TOTPManager()
        secret = manager.generate_secret()

        # Get current valid token
        current_token = manager.get_current_token(secret)

        # Verify it
        assert manager.verify_token(secret, current_token)

    def test_verify_token_invalid(self):
        """Test TOTP token verification with invalid code."""
        manager = TOTPManager()
        secret = manager.generate_secret()

        # Invalid token
        assert not manager.verify_token(secret, "000000")
        assert not manager.verify_token(secret, "999999")
        assert not manager.verify_token(secret, "123456")

    def test_verify_token_window(self):
        """Test TOTP token verification with time window."""
        manager = TOTPManager()
        secret = manager.generate_secret()

        # Get current token
        current_token = manager.get_current_token(secret)

        # Should work with window=1 (default)
        assert manager.verify_token(secret, current_token, window=1)

        # Should work with window=0 (strict)
        assert manager.verify_token(secret, current_token, window=0)

    def test_get_current_token_format(self):
        """Test that current token has correct format."""
        manager = TOTPManager()
        secret = manager.generate_secret()

        token = manager.get_current_token(secret)

        assert isinstance(token, str)
        assert len(token) == 6
        assert token.isdigit()

    def test_generate_backup_codes(self):
        """Test backup code generation."""
        manager = TOTPManager()
        codes = manager.generate_backup_codes()

        assert len(codes) == 10
        for code in codes:
            assert isinstance(code, str)
            assert len(code) == 9  # XXXX-XXXX format
            assert "-" in code
            parts = code.split("-")
            assert len(parts) == 2
            assert len(parts[0]) == 4
            assert len(parts[1]) == 4
            assert parts[0].isalnum()
            assert parts[1].isalnum()

    def test_generate_backup_codes_uniqueness(self):
        """Test that backup codes are unique within a set."""
        manager = TOTPManager()
        codes = manager.generate_backup_codes()

        # All codes should be unique
        assert len(codes) == len(set(codes))

    def test_verify_backup_code_valid(self):
        """Test backup code verification with valid code."""
        manager = TOTPManager()
        codes = manager.generate_backup_codes()

        # Test first code
        is_valid, used_code = manager.verify_backup_code(codes[0], codes)
        assert is_valid
        assert used_code == codes[0]

        # Test last code
        is_valid, used_code = manager.verify_backup_code(codes[-1], codes)
        assert is_valid
        assert used_code == codes[-1]

    def test_verify_backup_code_invalid(self):
        """Test backup code verification with invalid code."""
        manager = TOTPManager()
        codes = manager.generate_backup_codes()

        # Invalid codes
        is_valid, _ = manager.verify_backup_code("0000-0000", codes)
        assert not is_valid

        is_valid, _ = manager.verify_backup_code("XXXX-YYYY", codes)
        assert not is_valid

    def test_verify_backup_code_case_insensitive(self):
        """Test that backup code verification is case-insensitive."""
        manager = TOTPManager()
        codes = manager.generate_backup_codes()

        code = codes[0]

        # Test with different cases
        is_valid, _ = manager.verify_backup_code(code.lower(), codes)
        assert is_valid

        is_valid, _ = manager.verify_backup_code(code.upper(), codes)
        assert is_valid

    def test_format_secret_for_display(self):
        """Test secret formatting for manual entry."""
        manager = TOTPManager()
        secret = "ABCDEFGHIJ1234567890ABCD"

        formatted = manager.format_secret_for_display(secret)

        # Should be grouped in 4s
        parts = formatted.split()
        assert len(parts) == 6
        assert all(len(part) == 4 for part in parts)
        assert "".join(parts) == secret

    def test_get_time_remaining(self):
        """Test getting time remaining until next token."""
        manager = TOTPManager()

        remaining = manager.get_time_remaining()

        assert isinstance(remaining, int)
        assert 0 <= remaining <= 30

    def test_is_setup_complete_valid(self):
        """Test setup completion check with valid token."""
        manager = TOTPManager()
        secret = manager.generate_secret()

        # Get current token
        token = manager.get_current_token(secret)

        # Should be complete with valid token
        assert manager.is_setup_complete(secret, token)

    def test_is_setup_complete_invalid(self):
        """Test setup completion check with invalid token."""
        manager = TOTPManager()
        secret = manager.generate_secret()

        # Should not be complete with invalid token
        assert not manager.is_setup_complete(secret, "000000")

    def test_validate_secret_format_valid(self):
        """Test secret format validation with valid secrets."""
        manager = TOTPManager()

        # Valid Base32 secret (freshly generated)
        valid_secret = manager.generate_secret()
        assert manager.validate_secret_format(valid_secret)

        # Test that removing spaces works (formatted secrets)
        formatted = manager.format_secret_for_display(valid_secret)
        # The validator should handle spaces by removing them
        assert manager.validate_secret_format(formatted.replace(" ", ""))

    def test_validate_secret_format_invalid(self):
        """Test secret format validation with invalid secrets."""
        manager = TOTPManager()

        # Invalid secrets (not Base32)
        assert not manager.validate_secret_format("abc123!@#")
        assert not manager.validate_secret_format("123")


class TestDatabaseTwoFactor:
    """Test 2FA database operations."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        db = DatabaseManager(":memory:")
        yield db
        db.close()

    @pytest.fixture
    def user_id(self, db):
        """Create test user."""
        username = f"testuser_{int(time.time())}"
        user_id = db.create_user(
            username=username,
            password="TestPass123!",
            full_name="Test User",
            email="test@example.com",
            phone="1234567890",
        )
        return user_id

    def test_enable_2fa(self, db, user_id):
        """Test enabling 2FA for a user."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        success, message = db.enable_2fa(user_id, secret, backup_codes)

        assert success
        assert "enabled successfully" in message.lower()

    def test_is_2fa_enabled_false_initially(self, db, user_id):
        """Test that 2FA is disabled by default."""
        assert not db.is_2fa_enabled(user_id)

    def test_is_2fa_enabled_after_enabling(self, db, user_id):
        """Test that 2FA is enabled after setup."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        assert db.is_2fa_enabled(user_id)

    def test_get_2fa_secret(self, db, user_id):
        """Test retrieving 2FA secret."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        retrieved_secret = db.get_2fa_secret(user_id)
        assert retrieved_secret == secret

    def test_get_2fa_secret_when_disabled(self, db, user_id):
        """Test retrieving secret when 2FA is disabled."""
        secret = db.get_2fa_secret(user_id)
        assert secret is None

    def test_get_backup_codes(self, db, user_id):
        """Test retrieving backup codes."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        retrieved_codes = db.get_backup_codes(user_id)
        assert retrieved_codes == backup_codes
        assert len(retrieved_codes) == 10

    def test_get_backup_codes_when_disabled(self, db, user_id):
        """Test retrieving backup codes when 2FA is disabled."""
        codes = db.get_backup_codes(user_id)
        assert codes == []

    def test_use_backup_code(self, db, user_id):
        """Test using a backup code."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        # Use first code
        code_to_use = backup_codes[0]
        success, message = db.use_backup_code(user_id, code_to_use)

        assert success
        assert "9 backup codes remaining" in message

        # Verify code is removed
        remaining_codes = db.get_backup_codes(user_id)
        assert len(remaining_codes) == 9
        assert code_to_use not in remaining_codes

    def test_use_backup_code_all_codes(self, db, user_id):
        """Test using all backup codes."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        # Use all codes
        for i, code in enumerate(backup_codes):
            success, message = db.use_backup_code(user_id, code)
            assert success

            if i < 9:
                assert f"{9-i} backup codes remaining" in message
            else:
                assert "0 backup codes remaining" in message

        # Verify all codes are used
        remaining_codes = db.get_backup_codes(user_id)
        assert len(remaining_codes) == 0

    def test_use_invalid_backup_code(self, db, user_id):
        """Test using an invalid backup code."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        # Try invalid code
        success, message = db.use_backup_code(user_id, "0000-0000")

        assert not success
        assert "Invalid backup code" in message

    def test_update_2fa_last_used(self, db, user_id):
        """Test updating last used timestamp."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        success = db.update_2fa_last_used(user_id)

        assert success

    def test_get_2fa_status(self, db, user_id):
        """Test getting comprehensive 2FA status."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, backup_codes)

        status = db.get_2fa_status(user_id)

        assert status is not None
        assert status["enabled"] is True
        assert status["backup_codes_remaining"] == 10
        assert status["has_backup_codes"] is True
        assert status["created_at"] is not None
        assert "last_used" in status

    def test_get_2fa_status_when_disabled(self, db, user_id):
        """Test getting status when 2FA is disabled."""
        status = db.get_2fa_status(user_id)

        assert status is not None
        assert status["enabled"] is False

    def test_disable_2fa(self, db, user_id):
        """Test disabling 2FA."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        # Enable first
        db.enable_2fa(user_id, secret, backup_codes)
        assert db.is_2fa_enabled(user_id)

        # Then disable
        success, message = db.disable_2fa(user_id)

        assert success
        assert "disabled successfully" in message.lower()
        assert not db.is_2fa_enabled(user_id)

    def test_disable_2fa_removes_data(self, db, user_id):
        """Test that disabling 2FA removes secret and backup codes."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        # Enable first
        db.enable_2fa(user_id, secret, backup_codes)

        # Disable
        db.disable_2fa(user_id)

        # Verify data is removed
        assert db.get_2fa_secret(user_id) is None
        assert db.get_backup_codes(user_id) == []
        status = db.get_2fa_status(user_id)
        assert status is not None
        assert status["enabled"] is False

    def test_regenerate_backup_codes(self, db, user_id):
        """Test regenerating backup codes."""
        manager = TOTPManager()
        secret = manager.generate_secret()
        old_codes = manager.generate_backup_codes()

        db.enable_2fa(user_id, secret, old_codes)

        # Generate new codes
        new_codes = manager.generate_backup_codes()
        success, message = db.regenerate_backup_codes(user_id, new_codes)

        assert success
        assert "new backup codes" in message.lower()

        # Verify new codes are stored
        retrieved_codes = db.get_backup_codes(user_id)
        assert retrieved_codes == new_codes
        assert retrieved_codes != old_codes

    def test_enable_2fa_twice(self, db, user_id):
        """Test enabling 2FA twice (should update, not fail)."""
        manager = TOTPManager()

        # Enable first time
        secret1 = manager.generate_secret()
        codes1 = manager.generate_backup_codes()
        db.enable_2fa(user_id, secret1, codes1)

        # Enable second time with different secret
        secret2 = manager.generate_secret()
        codes2 = manager.generate_backup_codes()
        success, message = db.enable_2fa(user_id, secret2, codes2)

        assert success

        # Should have updated secret
        retrieved_secret = db.get_2fa_secret(user_id)
        assert retrieved_secret == secret2


class TestTwoFactorIntegration:
    """Test full 2FA workflow integration."""

    @pytest.fixture
    def db(self):
        """Create test database."""
        db = DatabaseManager(":memory:")
        yield db
        db.close()

    @pytest.fixture
    def user_id(self, db):
        """Create test user."""
        username = f"testuser_{int(time.time())}"
        user_id = db.create_user(
            username=username,
            password="TestPass123!",
            full_name="Test User",
            email="test@example.com",
            phone="1234567890",
        )
        return user_id

    def test_full_2fa_setup_workflow(self, db, user_id):
        """Test complete 2FA setup workflow."""
        manager = TOTPManager()

        # 1. Generate secret and backup codes
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()

        # 2. Verify secret is valid
        assert manager.validate_secret_format(secret)

        # 3. Get current token for verification
        token = manager.get_current_token(secret)

        # 4. Verify setup is complete
        assert manager.is_setup_complete(secret, token)

        # 5. Enable 2FA in database
        success, message = db.enable_2fa(user_id, secret, backup_codes)
        assert success

        # 6. Verify 2FA is enabled
        assert db.is_2fa_enabled(user_id)

        # 7. Verify secret can be retrieved
        assert db.get_2fa_secret(user_id) == secret

        # 8. Verify backup codes can be retrieved
        assert db.get_backup_codes(user_id) == backup_codes

    def test_full_2fa_login_workflow(self, db, user_id):
        """Test complete 2FA login workflow."""
        manager = TOTPManager()

        # Setup 2FA
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()
        db.enable_2fa(user_id, secret, backup_codes)

        # Simulate login:
        # 1. Check if 2FA is enabled
        assert db.is_2fa_enabled(user_id)

        # 2. Get secret from database
        stored_secret = db.get_2fa_secret(user_id)
        assert stored_secret == secret

        # 3. Get current token (user enters this)
        user_token = manager.get_current_token(secret)

        # 4. Verify token
        assert manager.verify_token(stored_secret, user_token)

        # 5. Update last used timestamp
        success = db.update_2fa_last_used(user_id)
        assert success

    def test_full_2fa_backup_code_workflow(self, db, user_id):
        """Test using backup code instead of TOTP."""
        manager = TOTPManager()

        # Setup 2FA
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()
        db.enable_2fa(user_id, secret, backup_codes)

        # Simulate login with backup code:
        # 1. Get backup codes from database
        stored_codes = db.get_backup_codes(user_id)

        # 2. User enters backup code
        user_backup_code = stored_codes[0]

        # 3. Verify backup code
        is_valid, used_code = manager.verify_backup_code(user_backup_code, stored_codes)
        assert is_valid

        # 4. Mark code as used in database
        success, message = db.use_backup_code(user_id, used_code)
        assert success

        # 5. Verify code is removed
        remaining_codes = db.get_backup_codes(user_id)
        assert len(remaining_codes) == 9
        assert used_code not in remaining_codes

    def test_full_2fa_disable_workflow(self, db, user_id):
        """Test complete 2FA disable workflow."""
        manager = TOTPManager()

        # Setup 2FA
        secret = manager.generate_secret()
        backup_codes = manager.generate_backup_codes()
        db.enable_2fa(user_id, secret, backup_codes)

        # Verify it's enabled
        assert db.is_2fa_enabled(user_id)

        # Disable 2FA
        success, message = db.disable_2fa(user_id)
        assert success

        # Verify it's disabled
        assert not db.is_2fa_enabled(user_id)

        # Verify all data is removed
        assert db.get_2fa_secret(user_id) is None
        assert db.get_backup_codes(user_id) == []
        status = db.get_2fa_status(user_id)
        assert status is not None
        assert status["enabled"] is False
