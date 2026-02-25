#!/usr/bin/env python3
"""
Gmail Watcher
Monitors Gmail inbox for new emails containing specific keywords
Uses Gmail API for reliable, efficient monitoring
"""

import os
import pickle
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime, timedelta

from base_watcher import BaseWatcher

try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
except ImportError:
    print("Error: Google API libraries not installed")
    print("Install with: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client")
    exit(1)


class GmailWatcher(BaseWatcher):
    """Gmail watcher implementation"""

    # Gmail API scopes
    SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

    def __init__(
        self,
        credentials_file: str = "../../credentials.json",
        token_file: str = "./gmail_token.pickle",
        check_interval: int = 300,
        keywords: Optional[List[str]] = None,
        max_results: int = 10
    ):
        """
        Initialize Gmail watcher

        Args:
            credentials_file: Path to Gmail API credentials.json
            token_file: Path to store authentication token
            check_interval: Seconds between checks
            keywords: List of keywords to filter for
            max_results: Maximum emails to fetch per check
        """
        # Initialize base watcher
        super().__init__(
            name="gmail",
            check_interval=check_interval,
            keywords=keywords or ["invoice", "urgent", "payment", "proposal"]
        )

        self.credentials_file = Path(__file__).parent.parent.parent / credentials_file.lstrip("../../")
        self.token_file = Path(__file__).parent / token_file.lstrip("./")
        self.max_results = max_results
        self.service = None
        self.last_check_time = None

    def _authenticate(self) -> Optional[Credentials]:
        """Authenticate with Gmail API"""
        creds = None

        # Load existing token
        if self.token_file.exists():
            try:
                with open(self.token_file, 'rb') as token:
                    creds = pickle.load(token)
                self.logger.info("Loaded existing credentials")
            except Exception as e:
                self.logger.warning(f"Error loading token: {e}")

        # Refresh or get new credentials
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    self.logger.info("Refreshed credentials")
                except Exception as e:
                    self.logger.error(f"Error refreshing credentials: {e}")
                    creds = None

            if not creds:
                if not self.credentials_file.exists():
                    self.logger.error(f"Credentials file not found: {self.credentials_file}")
                    return None

                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_file), self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                    self.logger.info("Obtained new credentials")
                except Exception as e:
                    self.logger.error(f"Error getting credentials: {e}")
                    return None

            # Save credentials
            try:
                with open(self.token_file, 'wb') as token:
                    pickle.dump(creds, token)
                self.logger.info("Saved credentials")
            except Exception as e:
                self.logger.warning(f"Error saving token: {e}")

        return creds

    def initialize(self) -> bool:
        """Initialize Gmail API connection"""
        try:
            self.logger.info("Initializing Gmail API connection...")

            # Authenticate
            creds = self._authenticate()
            if not creds:
                return False

            # Build service
            self.service = build('gmail', 'v1', credentials=creds)
            self.logger.info("Gmail API connection established")

            # Set initial check time to 24 hours ago
            self.last_check_time = datetime.utcnow() - timedelta(hours=24)

            return True

        except Exception as e:
            self.logger.error(f"Error initializing Gmail API: {e}")
            return False

    def _get_message_details(self, message_id: str) -> Optional[Dict]:
        """Get full message details"""
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Extract headers
            headers = message['payload']['headers']
            subject = next((h['value'] for h in headers if h['name'].lower() == 'subject'), 'No Subject')
            sender = next((h['value'] for h in headers if h['name'].lower() == 'from'), 'Unknown')
            date = next((h['value'] for h in headers if h['name'].lower() == 'date'), '')

            # Extract body
            body = ""
            if 'parts' in message['payload']:
                for part in message['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        if 'data' in part['body']:
                            import base64
                            body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                            break
            elif 'body' in message['payload'] and 'data' in message['payload']['body']:
                import base64
                body = base64.urlsafe_b64decode(message['payload']['body']['data']).decode('utf-8')

            return {
                'id': message_id,
                'subject': subject,
                'sender': sender,
                'date': date,
                'body': body,
                'snippet': message.get('snippet', '')
            }

        except Exception as e:
            self.logger.error(f"Error getting message details: {e}")
            return None

    def check_for_events(self) -> List[Dict]:
        """Check for new emails"""
        events = []

        try:
            # Build query for unread messages since last check
            query = 'is:unread'

            # Get messages
            results = self.service.users().messages().list(
                userId='me',
                q=query,
                maxResults=self.max_results
            ).execute()

            messages = results.get('messages', [])
            self.logger.info(f"Found {len(messages)} unread message(s)")

            # Process each message
            for message in messages:
                message_id = message['id']

                # Get full message details
                details = self._get_message_details(message_id)
                if not details:
                    continue

                # Create event
                event = {
                    'id': f"gmail_{message_id}",
                    'content': f"**Subject:** {details['subject']}\n\n**From:** {details['sender']}\n\n**Message:**\n{details['body'] or details['snippet']}",
                    'metadata': {
                        'type': 'gmail',
                        'sender': details['sender'],
                        'subject': details['subject'],
                        'date': details['date'],
                        'message_id': message_id,
                        'timestamp': datetime.utcnow().isoformat() + 'Z',
                        'status': 'pending'
                    }
                }

                events.append(event)

            # Update last check time
            self.last_check_time = datetime.utcnow()

        except Exception as e:
            self.logger.error(f"Error checking for emails: {e}")

        return events

    def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up Gmail watcher...")
        self.service = None


def main():
    """Main entry point"""
    # Configuration
    watcher = GmailWatcher(
        check_interval=300,  # 5 minutes
        keywords=["invoice", "urgent", "payment", "proposal"],
        max_results=10
    )

    # Run continuously
    watcher.run()


if __name__ == "__main__":
    main()
