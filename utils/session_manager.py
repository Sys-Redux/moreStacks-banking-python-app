"""
Session Management Module
Handles user session tracking, timeout, and auto-logout functionality
"""

import secrets
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple


class SessionManager:
    """
    Manages user sessions with automatic timeout and activity tracking.

    Features:
    - Auto-logout after configurable inactivity period (default: 15 minutes)
    - Warning dialog 1 minute before timeout
    - Session extension capability
    - Secure session token generation
    """

    def __init__(self, timeout_minutes: int = 15, warning_minutes: int = 1):
        """
        Initialize session manager.

        Args:
            timeout_minutes: Minutes of inactivity before auto-logout
            warning_minutes: Minutes before timeout to show warning
        """
        self.timeout_seconds = timeout_minutes * 60
        self.warning_seconds = warning_minutes * 60
        self.active_sessions: Dict[str, Dict] = {}

    def create_session(self, user_id: int, username: str) -> str:
        """
        Create a new session for a user.

        Args:
            user_id: User's database ID
            username: Username for logging

        Returns:
            Session token (secure random string)
        """
        session_token = secrets.token_urlsafe(32)
        now = datetime.now()

        self.active_sessions[session_token] = {
            "user_id": user_id,
            "username": username,
            "created_at": now,
            "last_activity": now,
            "expires_at": now + timedelta(seconds=self.timeout_seconds),
        }

        return session_token

    def update_activity(self, session_token: str) -> bool:
        """
        Update the last activity timestamp for a session.

        Args:
            session_token: Session token to update

        Returns:
            True if session exists and was updated, False otherwise
        """
        if session_token not in self.active_sessions:
            return False

        now = datetime.now()
        session = self.active_sessions[session_token]
        session["last_activity"] = now
        session["expires_at"] = now + timedelta(seconds=self.timeout_seconds)

        return True

    def extend_session(self, session_token: str) -> bool:
        """
        Extend a session's expiration time (reset timeout).

        Args:
            session_token: Session token to extend

        Returns:
            True if session exists and was extended, False otherwise
        """
        return self.update_activity(session_token)

    def is_session_valid(self, session_token: str) -> bool:
        """
        Check if a session is still valid (not expired).

        Args:
            session_token: Session token to check

        Returns:
            True if session exists and hasn't expired, False otherwise
        """
        if session_token not in self.active_sessions:
            return False

        session = self.active_sessions[session_token]
        return datetime.now() < session["expires_at"]

    def get_time_until_expiration(self, session_token: str) -> Optional[int]:
        """
        Get seconds until session expires.

        Args:
            session_token: Session token to check

        Returns:
            Seconds until expiration, or None if session doesn't exist
        """
        if session_token not in self.active_sessions:
            return None

        session = self.active_sessions[session_token]
        time_left = (session["expires_at"] - datetime.now()).total_seconds()

        return max(0, int(time_left))

    def should_show_warning(self, session_token: str) -> bool:
        """
        Check if warning should be displayed (approaching timeout).

        Args:
            session_token: Session token to check

        Returns:
            True if warning should be shown, False otherwise
        """
        time_left = self.get_time_until_expiration(session_token)

        if time_left is None:
            return False

        return 0 < time_left <= self.warning_seconds

    def destroy_session(self, session_token: str) -> bool:
        """
        Destroy a session (logout).

        Args:
            session_token: Session token to destroy

        Returns:
            True if session existed and was destroyed, False otherwise
        """
        if session_token in self.active_sessions:
            del self.active_sessions[session_token]
            return True
        return False

    def get_session_info(self, session_token: str) -> Optional[Dict]:
        """
        Get session information.

        Args:
            session_token: Session token to get info for

        Returns:
            Dictionary with session info, or None if session doesn't exist
        """
        if session_token not in self.active_sessions:
            return None

        session = self.active_sessions[session_token]
        time_left = self.get_time_until_expiration(session_token)

        return {
            "user_id": session["user_id"],
            "username": session["username"],
            "created_at": session["created_at"],
            "last_activity": session["last_activity"],
            "expires_at": session["expires_at"],
            "time_left_seconds": time_left,
            "is_valid": self.is_session_valid(session_token),
        }

    def cleanup_expired_sessions(self) -> int:
        """
        Remove all expired sessions.

        Returns:
            Number of sessions cleaned up
        """
        now = datetime.now()
        expired_tokens = [
            token
            for token, session in self.active_sessions.items()
            if now >= session["expires_at"]
        ]

        for token in expired_tokens:
            del self.active_sessions[token]

        return len(expired_tokens)

    def get_active_session_count(self) -> int:
        """
        Get count of active sessions.

        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)

    def format_time_remaining(self, seconds: int) -> str:
        """
        Format seconds into human-readable time remaining.

        Args:
            seconds: Seconds to format

        Returns:
            Formatted string (e.g., "5m 30s", "45s")
        """
        if seconds <= 0:
            return "Expired"

        minutes = seconds // 60
        remaining_seconds = seconds % 60

        if minutes > 0:
            return f"{minutes}m {remaining_seconds}s"
        else:
            return f"{remaining_seconds}s"
