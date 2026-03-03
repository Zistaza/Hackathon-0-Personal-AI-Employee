#!/usr/bin/env python3
"""
EmailExecutor - Email Sending via MCP Server
=============================================

Executes email sending via MCP server using nodemailer.
Logs all email actions to daily log files.
"""

import json
import subprocess
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict


class EmailExecutor:
    """Executes email sending via MCP server"""

    def __init__(self, mcp_server_path: Path, logs_dir: Path, logger: logging.Logger):
        self.mcp_server_path = mcp_server_path
        self.logs_dir = logs_dir
        self.logger = logger

    def send_email(self, email_data: Dict) -> Dict:
        """Send email using nodemailer directly"""
        try:
            # Prepare email command
            to = email_data.get('to', '')
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')

            if not to or not subject or not body:
                return {
                    'success': False,
                    'error': 'Missing required email fields (to, subject, body)'
                }

            self.logger.info(f"Sending email to: {to}")
            self.logger.info(f"Subject: {subject}")

            # Use the test_email.js script with custom parameters
            test_script = self.mcp_server_path / "test_email.js"

            if not test_script.exists():
                return {
                    'success': False,
                    'error': f'Email script not found: {test_script}'
                }

            # Create temporary email data file
            temp_data_file = self.mcp_server_path / "temp_email_data.json"
            with open(temp_data_file, 'w') as f:
                json.dump(email_data, f, indent=2)

            # Execute email sending
            result = subprocess.run(
                ["node", str(test_script), to],
                cwd=str(self.mcp_server_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clean up temp file
            if temp_data_file.exists():
                temp_data_file.unlink()

            success = result.returncode == 0

            if success:
                self.logger.info(f"Email sent successfully to {to}")
                self._log_email_action('email_sent', email_data, result.stdout)
            else:
                self.logger.error(f"Email sending failed: {result.stderr}")
                self._log_email_action('email_failed', email_data, result.stderr)

            return {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        except subprocess.TimeoutExpired:
            self.logger.error("Email sending timed out")
            return {
                'success': False,
                'error': 'Email sending timeout'
            }
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _log_email_action(self, action: str, email_data: Dict, details: str):
        """Log email action to daily log file"""
        try:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            log_file = self.logs_dir / f"{today}.json"

            # Load existing logs
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []

            # Add new log entry
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'action': action,
                'to': email_data.get('to', ''),
                'subject': email_data.get('subject', ''),
                'details': details[:500]  # Limit details length
            }
            logs.append(log_entry)

            # Save logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error logging email action: {e}")
