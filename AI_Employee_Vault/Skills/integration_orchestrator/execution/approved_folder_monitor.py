"""
Approved Folder Monitor - Automatic Execution
==============================================

Background monitor that automatically executes approved posts and messages.

Monitors /Approved folder and routes files to appropriate executors:
- POST_*.md → Social Media Executor v2
- MESSAGE_*.md → Message Sender v2

Features:
- Background thread monitoring (every 30 seconds)
- Automatic retry logic (3 attempts with exponential backoff)
- Success → /Done, Failure → /Failed
- Event publishing and audit logging
- Integration with Gold Tier infrastructure
"""

import asyncio
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime


class ApprovedFolderMonitor:
    """Background monitor for automatic execution of approved items"""

    def __init__(self, base_dir: Path, event_bus, audit_logger, folder_manager,
                 social_media_executor, message_sender, logger, check_interval: int = 30):
        """
        Initialize Approved Folder Monitor

        Args:
            base_dir: Base directory of the vault
            event_bus: EventBus instance
            audit_logger: AuditLogger instance
            folder_manager: FolderManager instance
            social_media_executor: SocialMediaExecutorV2 instance
            message_sender: MessageSenderV2 instance
            logger: Logger instance
            check_interval: Check interval in seconds (default: 30)
        """
        self.base_dir = base_dir
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        self.folder_manager = folder_manager
        self.social_media_executor = social_media_executor
        self.message_sender = message_sender
        self.logger = logger
        self.check_interval = check_interval

        self.approved_dir = base_dir / "Approved"
        self.running = False
        self.thread = None
        self.processed_files = set()  # Track processed files to avoid duplicates

        self.logger.info("ApprovedFolderMonitor initialized")

    def start(self):
        """Start monitoring in background thread"""
        if self.running:
            self.logger.warning("ApprovedFolderMonitor already running")
            return

        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()

        self.logger.info(f"ApprovedFolderMonitor started (checking every {self.check_interval}s)")

    def stop(self):
        """Stop monitoring"""
        if not self.running:
            return

        self.running = False
        if self.thread:
            self.thread.join(timeout=5)

        self.logger.info("ApprovedFolderMonitor stopped")

    def _monitor_loop(self):
        """Main monitoring loop - runs in background thread"""
        self.logger.info("ApprovedFolderMonitor loop started")

        while self.running:
            try:
                # Check for approved posts
                self._check_approved_posts()

                # Check for approved messages
                self._check_approved_messages()

                # Sleep until next check
                time.sleep(self.check_interval)

            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}", exc_info=True)
                time.sleep(self.check_interval)  # Continue monitoring even after error

    def _check_approved_posts(self):
        """Check for approved social media posts"""
        try:
            if not self.approved_dir.exists():
                return

            post_files = list(self.approved_dir.glob("POST_*.md"))

            if post_files:
                self.logger.info(f"Found {len(post_files)} approved post(s)")

                for post_file in post_files:
                    # Skip if already processed in this session
                    if str(post_file) in self.processed_files:
                        continue

                    self.logger.info(f"Processing approved post: {post_file.name}")

                    # Mark as processed to avoid duplicate execution
                    self.processed_files.add(str(post_file))

                    # Execute post in new event loop (async)
                    self._execute_post_sync(post_file)

        except Exception as e:
            self.logger.error(f"Error checking approved posts: {e}", exc_info=True)

    def _check_approved_messages(self):
        """Check for approved messages"""
        try:
            if not self.approved_dir.exists():
                return

            message_files = list(self.approved_dir.glob("MESSAGE_*.md"))

            if message_files:
                self.logger.info(f"Found {len(message_files)} approved message(s)")

                for message_file in message_files:
                    # Skip if already processed in this session
                    if str(message_file) in self.processed_files:
                        continue

                    self.logger.info(f"Processing approved message: {message_file.name}")

                    # Mark as processed to avoid duplicate execution
                    self.processed_files.add(str(message_file))

                    # Execute message in new event loop (async)
                    self._execute_message_sync(message_file)

        except Exception as e:
            self.logger.error(f"Error checking approved messages: {e}", exc_info=True)

    def _execute_post_sync(self, file_path: Path):
        """Execute social media post (synchronous wrapper for async executor)"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Parse post file
                post_data = self.social_media_executor.parse_post_file(file_path)

                if not post_data:
                    self.logger.error(f"Failed to parse post file: {file_path.name}")
                    self._handle_failure(file_path, "Failed to parse post file")
                    return

                # Publish start event
                if self.event_bus:
                    self.event_bus.publish('auto_execution.post.started', {
                        'file': file_path.name,
                        'platform': post_data.get('platform'),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                # Execute post with retry logic
                result = loop.run_until_complete(
                    self.social_media_executor.execute_post(post_data, file_path)
                )

                # Handle result
                if result.get('success'):
                    self._handle_success(file_path, 'post', result)
                else:
                    self._handle_failure(file_path, result.get('error', 'Unknown error'))

            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"Error executing post {file_path.name}: {e}", exc_info=True)
            self._handle_failure(file_path, str(e))

    def _execute_message_sync(self, file_path: Path):
        """Execute message (synchronous wrapper for async sender)"""
        try:
            # Create new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Parse message file
                message_data = self.message_sender.parse_message_file(file_path)

                if not message_data:
                    self.logger.error(f"Failed to parse message file: {file_path.name}")
                    self._handle_failure(file_path, "Failed to parse message file")
                    return

                # Publish start event
                if self.event_bus:
                    self.event_bus.publish('auto_execution.message.started', {
                        'file': file_path.name,
                        'platform': message_data.get('platform'),
                        'to': message_data.get('to'),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                # Execute message with retry logic
                result = loop.run_until_complete(
                    self.message_sender.send_message(message_data, file_path)
                )

                # Handle result
                if result.get('success'):
                    self._handle_success(file_path, 'message', result)
                else:
                    self._handle_failure(file_path, result.get('error', 'Unknown error'))

            finally:
                loop.close()

        except Exception as e:
            self.logger.error(f"Error executing message {file_path.name}: {e}", exc_info=True)
            self._handle_failure(file_path, str(e))

    def _handle_success(self, file_path: Path, item_type: str, result: Dict[str, Any]):
        """Handle successful execution"""
        try:
            filename = file_path.name

            # Move to Done
            if self.folder_manager:
                self.folder_manager.move_to_done(filename)
            else:
                # Fallback: manual move
                done_path = self.base_dir / "Done" / filename
                file_path.rename(done_path)

            # Publish success event
            if self.event_bus:
                self.event_bus.publish(f'auto_execution.{item_type}.completed', {
                    'file': filename,
                    'success': True,
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type='auto_execution',
                    actor='approved_folder_monitor',
                    action=f'execute_{item_type}',
                    resource=filename,
                    result='success',
                    metadata={'result': result}
                )

            self.logger.info(f"✅ Successfully executed: {filename}")

            # Remove from processed set (file is gone now)
            self.processed_files.discard(str(file_path))

        except Exception as e:
            self.logger.error(f"Error handling success for {file_path.name}: {e}", exc_info=True)

    def _handle_failure(self, file_path: Path, error: str):
        """Handle failed execution"""
        try:
            filename = file_path.name

            # Move to Failed
            if self.folder_manager:
                self.folder_manager.move_to_failed(filename, error)
            else:
                # Fallback: manual move with error
                failed_path = self.base_dir / "Failed" / filename
                file_path.rename(failed_path)

                # Append error to file
                with open(failed_path, 'a', encoding='utf-8') as f:
                    f.write(f"\n\n---\n## AUTO-EXECUTION FAILED\n\n**Timestamp:** {datetime.utcnow().isoformat()}Z\n\n**Error:**\n```\n{error}\n```\n")

            # Publish failure event
            if self.event_bus:
                self.event_bus.publish('auto_execution.failed', {
                    'file': filename,
                    'error': error,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

            # Log to audit
            if self.audit_logger:
                self.audit_logger.log_event(
                    event_type='auto_execution',
                    actor='approved_folder_monitor',
                    action='execute',
                    resource=filename,
                    result='failure',
                    metadata={'error': error}
                )

            self.logger.error(f"❌ Failed to execute: {filename} - {error}")

            # Remove from processed set (file is gone now)
            self.processed_files.discard(str(file_path))

        except Exception as e:
            self.logger.error(f"Error handling failure for {file_path.name}: {e}", exc_info=True)

    def get_status(self) -> Dict[str, Any]:
        """Get monitor status"""
        return {
            'running': self.running,
            'check_interval': self.check_interval,
            'processed_count': len(self.processed_files),
            'thread_alive': self.thread.is_alive() if self.thread else False
        }
