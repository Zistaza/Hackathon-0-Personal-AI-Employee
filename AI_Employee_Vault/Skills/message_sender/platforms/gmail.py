"""
Gmail Platform Handler
======================

Handles email sending via Gmail API with OAuth2 authentication.
"""

import os
import base64
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Dict, Any, List, Optional

from .base import BaseMessagePlatform


class GmailPlatform(BaseMessagePlatform):
    """Gmail-specific message sending logic using Gmail API"""

    def __init__(self, config: Dict[str, Any], session_dir: Path, logs_dir: Path, logger):
        super().__init__(config, session_dir, logs_dir, logger)
        self.gmail_service = None
        self.credentials = None

    def _get_credentials_path(self) -> Path:
        """Get path to OAuth2 credentials file"""
        # Check in session directory first
        creds_file = self.config.get('credentials_file', 'credentials.json')
        creds_path = self.session_dir / creds_file

        # Fall back to base directory
        if not creds_path.exists():
            base_dir = self.session_dir.parent.parent
            creds_path = base_dir / creds_file

        return creds_path

    def _get_token_path(self) -> Path:
        """Get path to OAuth2 token file"""
        token_file = self.config.get('token_file', 'gmail_token.json')
        return self.session_dir / token_file

    async def initialize(self):
        """Initialize Gmail API client"""
        try:
            from google.auth.transport.requests import Request
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from googleapiclient.discovery import build

            creds = None
            token_path = self._get_token_path()
            creds_path = self._get_credentials_path()

            # Load existing token
            if token_path.exists():
                creds = Credentials.from_authorized_user_file(
                    str(token_path),
                    self.config.get('scopes', [])
                )

            # Refresh or get new token
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                    self.logger.info("Gmail token refreshed")
                else:
                    if not creds_path.exists():
                        raise Exception(f"Gmail credentials file not found: {creds_path}")

                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(creds_path),
                        self.config.get('scopes', [])
                    )
                    creds = flow.run_local_server(port=0)
                    self.logger.info("Gmail authentication completed")

                # Save token
                with open(token_path, 'w') as token:
                    token.write(creds.to_json())

            # Build Gmail service
            self.gmail_service = build('gmail', 'v1', credentials=creds)
            self.credentials = creds
            self.logger.info("Gmail API initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize Gmail API: {e}")
            raise

    def _create_message(self, to: str, subject: str, content: str,
                       attachments: List[str] = None) -> Dict[str, str]:
        """
        Create email message

        Args:
            to: Recipient email address
            subject: Email subject
            content: Email body
            attachments: List of attachment file paths

        Returns:
            Message dictionary for Gmail API
        """
        if attachments:
            message = MIMEMultipart()
        else:
            message = MIMEText(content)

        message['to'] = to
        message['subject'] = subject

        if attachments:
            # Add body
            message.attach(MIMEText(content, 'plain'))

            # Add attachments
            for attachment_path in attachments:
                try:
                    file_path = Path(attachment_path)
                    with open(file_path, 'rb') as f:
                        part = MIMEBase('application', 'octet-stream')
                        part.set_payload(f.read())
                        encoders.encode_base64(part)
                        part.add_header(
                            'Content-Disposition',
                            f'attachment; filename= {file_path.name}'
                        )
                        message.attach(part)
                except Exception as e:
                    self.logger.error(f"Failed to attach file {attachment_path}: {e}")

        # Encode message
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        return {'raw': raw_message}

    async def send_message(self, to: str, subject: str, content: str,
                          attachments: List[str] = None) -> Dict[str, Any]:
        """
        Send email via Gmail API

        Args:
            to: Recipient email address
            subject: Email subject
            content: Email body
            attachments: List of attachment file paths

        Returns:
            Result dictionary
        """
        try:
            self.logger.info(f"Sending Gmail message to: {to}")

            # Validate message
            validation = self.validate_message(to, content, attachments)
            if not validation["valid"]:
                return {
                    "success": False,
                    "platform": "gmail",
                    "error": validation["error"],
                    "timestamp": self._get_timestamp()
                }

            # Initialize Gmail API if not already done
            if not self.gmail_service:
                await self.initialize()

            # Create message
            message = self._create_message(to, subject, content, attachments)

            # Send message
            result = self.gmail_service.users().messages().send(
                userId='me',
                body=message
            ).execute()

            self.logger.info(f"Gmail message sent successfully: {result.get('id')}")

            return {
                "success": True,
                "platform": "gmail",
                "message_id": result.get('id'),
                "to": to,
                "subject": subject,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            self.logger.error(f"Gmail sending failed: {e}")
            return {
                "success": False,
                "platform": "gmail",
                "error": str(e),
                "to": to,
                "timestamp": self._get_timestamp()
            }
