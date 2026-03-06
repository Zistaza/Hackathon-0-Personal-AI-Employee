"""
Base Message Platform Handler
==============================

Abstract base class for message sending platforms.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class BaseMessagePlatform(ABC):
    """Abstract base class for platform-specific message sending logic"""

    def __init__(self, config: Dict[str, Any], session_dir: Path, logs_dir: Path, logger):
        """
        Initialize platform handler

        Args:
            config: Platform-specific configuration
            session_dir: Directory for persistent sessions/tokens
            logs_dir: Directory for error screenshots
            logger: Logger instance
        """
        self.config = config
        self.session_dir = session_dir
        self.logs_dir = logs_dir
        self.logger = logger
        self.platform_name = self.__class__.__name__.replace('Platform', '').lower()

        # Ensure directories exist
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def send_message(self, to: str, subject: str, content: str,
                          attachments: List[str] = None) -> Dict[str, Any]:
        """
        Send a message

        Args:
            to: Recipient (email address or contact name)
            subject: Message subject (for email) or None (for chat)
            content: Message content/body
            attachments: List of attachment file paths (optional)

        Returns:
            Result dictionary with success status and details
        """
        pass

    def validate_message(self, to: str, content: str, attachments: List[str] = None) -> Dict[str, Any]:
        """
        Validate message before sending

        Args:
            to: Recipient
            content: Message content
            attachments: Attachment files

        Returns:
            Validation result with success status and error message
        """
        # Check if recipient is empty
        if not to or not to.strip():
            return {
                "valid": False,
                "error": "Recipient cannot be empty"
            }

        # Check if content is empty
        if not content or not content.strip():
            return {
                "valid": False,
                "error": "Message content cannot be empty"
            }

        # Validate attachments exist
        if attachments:
            for attachment_path in attachments:
                if not Path(attachment_path).exists():
                    return {
                        "valid": False,
                        "error": f"Attachment not found: {attachment_path}"
                    }

        return {"valid": True}

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        return datetime.utcnow().isoformat() + 'Z'
