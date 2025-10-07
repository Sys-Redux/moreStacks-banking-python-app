"""
Audit Log Retention Policy Manager for moreStacks Banking Application.

Handles automatic cleanup and archiving of old audit logs based on
configurable retention policies.
"""

import os
import gzip
import json
from datetime import datetime, timedelta
from typing import Optional, Tuple, Dict
from database.db_manager import DatabaseManager


class AuditRetentionPolicy:
    """
    Manages audit log retention and cleanup policies.

    Features:
    - Configurable retention period
    - Automatic cleanup of old logs
    - Critical event preservation
    - Archive to compressed files (optional)
    - Statistics and reporting
    """

    # Default retention period in days
    DEFAULT_RETENTION_DAYS = 90

    # Critical events are never deleted
    CRITICAL_SEVERITY = "CRITICAL"

    def __init__(
        self,
        db_manager: DatabaseManager,
        retention_days: int = DEFAULT_RETENTION_DAYS,
        archive_enabled: bool = False,
        archive_path: Optional[str] = None,
    ):
        """
        Initialize the retention policy manager.

        Args:
            db_manager: Database manager instance
            retention_days: Number of days to retain audit logs
            archive_enabled: Whether to archive logs before deletion
            archive_path: Path to store archived logs
        """
        self.db = db_manager
        self.retention_days = retention_days
        self.archive_enabled = archive_enabled
        self.archive_path = archive_path or "audit_archives"

        if self.archive_enabled:
            self._ensure_archive_directory()

    def _ensure_archive_directory(self):
        """Ensure the archive directory exists."""
        if not os.path.exists(self.archive_path):
            os.makedirs(self.archive_path)

    def get_logs_for_cleanup(self, keep_critical: bool = True) -> list:
        """
        Get list of logs that are due for cleanup.

        Args:
            keep_critical: Whether to exclude critical logs from cleanup

        Returns:
            List of log dictionaries ready for cleanup
        """
        cutoff_date = (datetime.now() - timedelta(days=self.retention_days)).isoformat()

        filters = {"end_date": cutoff_date}

        if keep_critical:
            # Get all old logs that are NOT critical
            all_logs = self.db.search_audit_logs(filters, limit=100000)
            return [
                log for log in all_logs if log.get("severity") != self.CRITICAL_SEVERITY
            ]
        else:
            # Get all old logs
            return self.db.search_audit_logs(filters, limit=100000)

    def archive_logs(self, logs: list) -> Tuple[bool, str]:
        """
        Archive logs to compressed JSON file.

        Args:
            logs: List of log dictionaries to archive

        Returns:
            Tuple of (success, message/filepath)
        """
        if not logs:
            return (False, "No logs to archive")

        try:
            # Generate archive filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"audit_archive_{timestamp}.json.gz"
            filepath = os.path.join(self.archive_path, filename)

            # Prepare archive data
            archive_data = {
                "archived_at": datetime.now().isoformat(),
                "log_count": len(logs),
                "retention_days": self.retention_days,
                "logs": logs,
            }

            # Write compressed JSON
            with gzip.open(filepath, "wt", encoding="utf-8") as f:
                json.dump(archive_data, f, indent=2)

            return (True, filepath)

        except Exception as e:
            return (False, f"Error archiving logs: {str(e)}")

    def cleanup_old_logs(
        self, keep_critical: bool = True, archive_first: bool = None
    ) -> Tuple[bool, str]:
        """
        Clean up old audit logs based on retention policy.

        Args:
            keep_critical: Whether to preserve critical severity logs
            archive_first: Whether to archive logs before deletion (uses instance setting if None)

        Returns:
            Tuple of (success, message)
        """
        # Use instance setting if not specified
        if archive_first is None:
            archive_first = self.archive_enabled

        try:
            # Get logs for cleanup
            logs_to_cleanup = self.get_logs_for_cleanup(keep_critical)

            if not logs_to_cleanup:
                return (True, "No logs require cleanup")

            # Archive if enabled
            archive_path = None
            if archive_first:
                success, result = self.archive_logs(logs_to_cleanup)
                if success:
                    archive_path = result
                else:
                    return (False, f"Failed to archive logs: {result}")

            # Delete old logs from database
            success, message = self.db.delete_old_audit_logs(
                days_old=self.retention_days, keep_critical=keep_critical
            )

            if success:
                result_msg = message
                if archive_path:
                    result_msg += f"\nArchived to: {archive_path}"
                return (True, result_msg)
            else:
                return (False, message)

        except Exception as e:
            return (False, f"Error during cleanup: {str(e)}")

    def get_retention_statistics(self) -> Dict[str, any]:
        """
        Get statistics about log retention and cleanup.

        Returns:
            Dictionary containing retention statistics
        """
        try:
            stats = {}

            # Get total logs
            stats["total_logs"] = self.db.get_audit_log_count()

            # Get logs within retention period
            cutoff_date = (
                datetime.now() - timedelta(days=self.retention_days)
            ).isoformat()
            within_retention = self.db.search_audit_logs(
                filters={"start_date": cutoff_date}, limit=100000
            )
            stats["within_retention"] = len(within_retention)

            # Get logs beyond retention period
            beyond_retention = self.db.search_audit_logs(
                filters={"end_date": cutoff_date}, limit=100000
            )
            stats["beyond_retention"] = len(beyond_retention)

            # Critical logs beyond retention
            critical_beyond = [
                log
                for log in beyond_retention
                if log.get("severity") == self.CRITICAL_SEVERITY
            ]
            stats["critical_beyond_retention"] = len(critical_beyond)

            # Cleanup candidates (non-critical beyond retention)
            stats["cleanup_candidates"] = (
                stats["beyond_retention"] - stats["critical_beyond_retention"]
            )

            # Oldest log date
            all_logs = self.db.search_audit_logs(filters={}, limit=1)
            if all_logs:
                oldest_date = all_logs[0].get("created_at", "N/A")
                stats["oldest_log_date"] = oldest_date

                # Calculate age in days
                try:
                    oldest_dt = datetime.fromisoformat(oldest_date)
                    age = (datetime.now() - oldest_dt).days
                    stats["oldest_log_age_days"] = age
                except Exception:
                    stats["oldest_log_age_days"] = "N/A"
            else:
                stats["oldest_log_date"] = "N/A"
                stats["oldest_log_age_days"] = 0

            # Retention settings
            stats["retention_days"] = self.retention_days
            stats["archive_enabled"] = self.archive_enabled
            stats["archive_path"] = self.archive_path if self.archive_enabled else "N/A"

            # Archive statistics if enabled
            if self.archive_enabled and os.path.exists(self.archive_path):
                archives = [
                    f for f in os.listdir(self.archive_path) if f.endswith(".json.gz")
                ]
                stats["archive_count"] = len(archives)

                # Calculate total archive size
                total_size = 0
                for archive in archives:
                    archive_path = os.path.join(self.archive_path, archive)
                    total_size += os.path.getsize(archive_path)
                stats["archive_size_mb"] = round(total_size / (1024 * 1024), 2)
            else:
                stats["archive_count"] = 0
                stats["archive_size_mb"] = 0

            return stats

        except Exception as e:
            return {
                "error": f"Error getting statistics: {str(e)}",
                "total_logs": 0,
                "within_retention": 0,
                "beyond_retention": 0,
                "cleanup_candidates": 0,
            }

    def restore_from_archive(self, archive_filename: str) -> Tuple[bool, str]:
        """
        Restore logs from an archive file.

        Args:
            archive_filename: Name of the archive file to restore

        Returns:
            Tuple of (success, message)
        """
        try:
            filepath = os.path.join(self.archive_path, archive_filename)

            if not os.path.exists(filepath):
                return (False, f"Archive file not found: {archive_filename}")

            # Read compressed archive
            with gzip.open(filepath, "rt", encoding="utf-8") as f:
                archive_data = json.load(f)

            logs = archive_data.get("logs", [])

            if not logs:
                return (False, "Archive contains no logs")

            # Restore logs to database
            restored_count = 0
            for log in logs:
                # Create log entry (skip if already exists)
                try:
                    success = self.db.create_audit_log(
                        event_type=log.get("event_type"),
                        event_category=log.get("event_category"),
                        description=log.get("description"),
                        severity=log.get("severity"),
                        user_id=log.get("user_id"),
                        username=log.get("username"),
                        ip_address=log.get("ip_address"),
                        user_agent=log.get("user_agent"),
                        metadata=log.get("metadata"),
                    )
                    if success:
                        restored_count += 1
                except Exception:
                    continue  # Skip duplicates or errors

            return (
                True,
                f"Restored {restored_count} of {len(logs)} logs from {archive_filename}",
            )

        except Exception as e:
            return (False, f"Error restoring archive: {str(e)}")

    def list_archives(self) -> list:
        """
        List all available archive files.

        Returns:
            List of dictionaries containing archive information
        """
        if not os.path.exists(self.archive_path):
            return []

        archives = []
        for filename in os.listdir(self.archive_path):
            if not filename.endswith(".json.gz"):
                continue

            filepath = os.path.join(self.archive_path, filename)

            try:
                # Get file stats
                file_stats = os.stat(filepath)
                size_mb = round(file_stats.st_size / (1024 * 1024), 2)
                modified = datetime.fromtimestamp(file_stats.st_mtime)

                # Try to read log count from archive
                try:
                    with gzip.open(filepath, "rt", encoding="utf-8") as f:
                        archive_data = json.load(f)
                        log_count = archive_data.get("log_count", "Unknown")
                except Exception:
                    log_count = "Unknown"

                archives.append(
                    {
                        "filename": filename,
                        "size_mb": size_mb,
                        "modified": modified.isoformat(),
                        "log_count": log_count,
                    }
                )
            except Exception:
                continue

        # Sort by modified date (newest first)
        archives.sort(key=lambda x: x["modified"], reverse=True)

        return archives

    def cleanup_scheduler(self, schedule_type: str = "daily") -> Tuple[bool, str]:
        """
        Run scheduled cleanup based on schedule type.

        This is a placeholder for integration with a scheduling system.
        In production, this would be called by a cron job or scheduler.

        Args:
            schedule_type: Type of schedule (daily, weekly, monthly)

        Returns:
            Tuple of (success, message)
        """
        stats = self.get_retention_statistics()

        # Check if cleanup is needed
        if stats.get("cleanup_candidates", 0) == 0:
            return (True, f"No cleanup needed (schedule: {schedule_type})")

        # Run cleanup
        return self.cleanup_old_logs(
            keep_critical=True, archive_first=self.archive_enabled
        )

    def update_retention_days(self, new_retention_days: int) -> bool:
        """
        Update the retention period.

        Args:
            new_retention_days: New retention period in days

        Returns:
            True if updated successfully
        """
        if new_retention_days < 1:
            return False

        self.retention_days = new_retention_days
        return True

    def enable_archiving(self, archive_path: Optional[str] = None) -> bool:
        """
        Enable log archiving.

        Args:
            archive_path: Optional custom path for archives

        Returns:
            True if enabled successfully
        """
        if archive_path:
            self.archive_path = archive_path

        self.archive_enabled = True
        self._ensure_archive_directory()
        return True

    def disable_archiving(self) -> bool:
        """
        Disable log archiving.

        Returns:
            True if disabled successfully
        """
        self.archive_enabled = False
        return True
