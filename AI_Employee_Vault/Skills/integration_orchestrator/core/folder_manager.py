"""
Folder Manager - Gold Tier HITL Architecture
=============================================

Manages unified folder structure for social media automation with Human-in-the-Loop workflow.

Folder Flow:
    /Pending_Approval → /Approved → /Done (success)
                                  → /Failed (after retries)

Session Storage:
    /Sessions/{platform}/ - Persistent browser sessions
"""

import shutil
from pathlib import Path
from typing import List, Optional, Dict, Any
from datetime import datetime


class FolderManager:
    """Manages HITL folder architecture for social media automation"""

    def __init__(self, base_dir: Path, event_bus=None, audit_logger=None, logger=None):
        """
        Initialize FolderManager

        Args:
            base_dir: Base directory of the vault
            event_bus: EventBus instance for publishing events
            audit_logger: AuditLogger instance for logging operations
            logger: Logger instance
        """
        self.base_dir = base_dir
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        self.logger = logger

        # Define folder paths
        self.pending_approval_dir = base_dir / "Pending_Approval"
        self.approved_dir = base_dir / "Approved"
        self.done_dir = base_dir / "Done"
        self.failed_dir = base_dir / "Failed"
        self.sessions_dir = base_dir / "Sessions"
        self.logs_dir = base_dir / "Logs"

        # Session platform subdirectories
        self.session_platforms = ["linkedin", "facebook", "instagram", "twitter", "whatsapp"]

        # Ensure all folders exist
        self._ensure_folders_exist()

        if self.logger:
            self.logger.info("FolderManager initialized with HITL architecture")

    def _ensure_folders_exist(self):
        """Ensure all required folders exist"""
        folders = [
            self.pending_approval_dir,
            self.approved_dir,
            self.done_dir,
            self.failed_dir,
            self.sessions_dir,
            self.logs_dir
        ]

        # Create main folders
        for folder in folders:
            folder.mkdir(parents=True, exist_ok=True)

        # Create session platform subfolders
        for platform in self.session_platforms:
            platform_dir = self.sessions_dir / platform
            platform_dir.mkdir(parents=True, exist_ok=True)

        if self.logger:
            self.logger.info(f"Verified {len(folders)} main folders and {len(self.session_platforms)} session folders")

    def list_pending(self) -> List[Path]:
        """
        List all files in Pending_Approval folder

        Returns:
            List of Path objects for pending files
        """
        try:
            if not self.pending_approval_dir.exists():
                return []

            files = [
                f for f in self.pending_approval_dir.iterdir()
                if f.is_file() and f.suffix in ['.md', '.txt']
            ]

            return sorted(files, key=lambda x: x.stat().st_mtime)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing pending files: {e}")
            return []

    def list_approved(self) -> List[Path]:
        """
        List all files in Approved folder

        Returns:
            List of Path objects for approved files
        """
        try:
            if not self.approved_dir.exists():
                return []

            files = [
                f for f in self.approved_dir.iterdir()
                if f.is_file() and f.suffix in ['.md', '.txt']
            ]

            return sorted(files, key=lambda x: x.stat().st_mtime)

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error listing approved files: {e}")
            return []

    def move_to_approved(self, file: str) -> bool:
        """
        Move file from Pending_Approval to Approved

        Args:
            file: Filename or full path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle both filename and full path
            if isinstance(file, str):
                file = Path(file)

            if not file.is_absolute():
                source_path = self.pending_approval_dir / file.name
            else:
                source_path = file

            if not source_path.exists():
                if self.logger:
                    self.logger.error(f"Source file not found: {source_path}")
                return False

            dest_path = self.approved_dir / source_path.name

            # Move file
            shutil.move(str(source_path), str(dest_path))

            # Publish event
            if self.event_bus:
                self.event_bus.publish("file.moved.to.approved", {
                    "filename": source_path.name,
                    "source": str(source_path),
                    "destination": str(dest_path),
                    "timestamp": datetime.utcnow().isoformat() + 'Z'
                })

            # Log operation
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type="file_moved",
                    actor="folder_manager",
                    action="move_to_approved",
                    resource=source_path.name,
                    result="success",
                    metadata={
                        "from": "Pending_Approval",
                        "to": "Approved"
                    }
                )

            if self.logger:
                self.logger.info(f"Moved to Approved: {source_path.name}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error moving file to approved: {e}")
            return False

    def move_to_done(self, file: str) -> bool:
        """
        Move file to Done folder (successful execution)

        Args:
            file: Filename or full path

        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle both filename and full path
            if isinstance(file, str):
                file = Path(file)

            # Try to find file in Approved or Pending_Approval
            if not file.is_absolute():
                if (self.approved_dir / file.name).exists():
                    source_path = self.approved_dir / file.name
                elif (self.pending_approval_dir / file.name).exists():
                    source_path = self.pending_approval_dir / file.name
                else:
                    if self.logger:
                        self.logger.error(f"Source file not found: {file.name}")
                    return False
            else:
                source_path = file

            if not source_path.exists():
                if self.logger:
                    self.logger.error(f"Source file not found: {source_path}")
                return False

            dest_path = self.done_dir / source_path.name

            # Move file
            shutil.move(str(source_path), str(dest_path))

            # Publish event
            if self.event_bus:
                self.event_bus.publish("file.moved.to.done", {
                    "filename": source_path.name,
                    "source": str(source_path),
                    "destination": str(dest_path),
                    "timestamp": datetime.utcnow().isoformat() + 'Z'
                })

            # Log operation
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type="file_moved",
                    actor="folder_manager",
                    action="move_to_done",
                    resource=source_path.name,
                    result="success",
                    metadata={
                        "to": "Done"
                    }
                )

            if self.logger:
                self.logger.info(f"Moved to Done: {source_path.name}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error moving file to done: {e}")
            return False

    def move_to_failed(self, file: str, error: str) -> bool:
        """
        Move file to Failed folder (after max retries)

        Args:
            file: Filename or full path
            error: Error message to append to file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Handle both filename and full path
            if isinstance(file, str):
                file = Path(file)

            # Try to find file in Approved or Pending_Approval
            if not file.is_absolute():
                if (self.approved_dir / file.name).exists():
                    source_path = self.approved_dir / file.name
                elif (self.pending_approval_dir / file.name).exists():
                    source_path = self.pending_approval_dir / file.name
                else:
                    if self.logger:
                        self.logger.error(f"Source file not found: {file.name}")
                    return False
            else:
                source_path = file

            if not source_path.exists():
                if self.logger:
                    self.logger.error(f"Source file not found: {source_path}")
                return False

            dest_path = self.failed_dir / source_path.name

            # Read original content
            try:
                with open(source_path, 'r', encoding='utf-8') as f:
                    original_content = f.read()
            except Exception:
                original_content = ""

            # Move file
            shutil.move(str(source_path), str(dest_path))

            # Append error information
            error_footer = f"\n\n---\n## EXECUTION FAILED\n\n**Timestamp:** {datetime.utcnow().isoformat()}Z\n\n**Error:**\n```\n{error}\n```\n"

            try:
                with open(dest_path, 'a', encoding='utf-8') as f:
                    f.write(error_footer)
            except Exception as e:
                if self.logger:
                    self.logger.warning(f"Could not append error to file: {e}")

            # Publish event
            if self.event_bus:
                self.event_bus.publish("file.moved.to.failed", {
                    "filename": source_path.name,
                    "source": str(source_path),
                    "destination": str(dest_path),
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat() + 'Z'
                })

            # Log operation
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type="file_moved",
                    actor="folder_manager",
                    action="move_to_failed",
                    resource=source_path.name,
                    result="failed",
                    metadata={
                        "to": "Failed",
                        "error": error
                    }
                )

            if self.logger:
                self.logger.warning(f"Moved to Failed: {source_path.name} - {error}")

            return True

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error moving file to failed: {e}")
            return False

    def get_session_path(self, platform: str) -> Path:
        """
        Get session storage path for a platform

        Args:
            platform: Platform name (linkedin, facebook, instagram, twitter, whatsapp)

        Returns:
            Path to platform session directory
        """
        platform = platform.lower()

        if platform not in self.session_platforms:
            if self.logger:
                self.logger.warning(f"Unknown platform: {platform}, returning generic session path")

        session_path = self.sessions_dir / platform
        session_path.mkdir(parents=True, exist_ok=True)

        return session_path

    def get_stats(self) -> Dict[str, Any]:
        """
        Get folder statistics

        Returns:
            Dictionary with folder counts
        """
        try:
            stats = {
                "pending_approval": len(self.list_pending()),
                "approved": len(self.list_approved()),
                "done": len(list(self.done_dir.glob("*.md"))) if self.done_dir.exists() else 0,
                "failed": len(list(self.failed_dir.glob("*.md"))) if self.failed_dir.exists() else 0,
                "timestamp": datetime.utcnow().isoformat() + 'Z'
            }
            return stats
        except Exception as e:
            if self.logger:
                self.logger.error(f"Error getting folder stats: {e}")
            return {}

    def cleanup_old_files(self, folder: str, days: int = 30) -> int:
        """
        Clean up old files from a folder

        Args:
            folder: Folder name (done, failed)
            days: Delete files older than this many days

        Returns:
            Number of files deleted
        """
        try:
            folder_map = {
                "done": self.done_dir,
                "failed": self.failed_dir
            }

            if folder not in folder_map:
                if self.logger:
                    self.logger.error(f"Invalid folder for cleanup: {folder}")
                return 0

            target_dir = folder_map[folder]
            if not target_dir.exists():
                return 0

            cutoff_time = datetime.utcnow().timestamp() - (days * 86400)
            deleted_count = 0

            for file in target_dir.glob("*.md"):
                if file.stat().st_mtime < cutoff_time:
                    file.unlink()
                    deleted_count += 1

            if self.logger and deleted_count > 0:
                self.logger.info(f"Cleaned up {deleted_count} old files from {folder}")

            return deleted_count

        except Exception as e:
            if self.logger:
                self.logger.error(f"Error during cleanup: {e}")
            return 0
