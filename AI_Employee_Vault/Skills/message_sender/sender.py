#!/usr/bin/env python3
"""
Message Sender v2
=================

Unified message sending for Gmail and WhatsApp with HITL workflow.

Features:
- Email sending via Gmail API
- WhatsApp messaging via Playwright
- Persistent sessions/tokens
- Retry logic with exponential backoff
- Integration with Gold Tier infrastructure
- HITL workflow support
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("Warning: playwright not installed. WhatsApp messaging will not work.")

# Import platform handlers (support both relative and absolute imports)
try:
    from .platforms import GmailPlatform, WhatsAppPlatform
except ImportError:
    from platforms import GmailPlatform, WhatsAppPlatform


class MessageSenderV2:
    """Unified message sending executor"""

    def __init__(self, base_dir: Path, event_bus=None, audit_logger=None,
                 folder_manager=None, logger=None):
        """
        Initialize Message Sender

        Args:
            base_dir: Base directory of the vault
            event_bus: EventBus instance for publishing events
            audit_logger: AuditLogger instance for logging
            folder_manager: FolderManager instance for file operations
            logger: Logger instance
        """
        self.base_dir = base_dir
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        self.folder_manager = folder_manager
        self.logger = logger or self._setup_logger()

        # Load configuration
        self.config_file = Path(__file__).parent / "config.json"
        self.config = self._load_config()

        # Directories
        self.sessions_dir = base_dir / "Sessions"
        self.logs_dir = base_dir / "Logs"
        self.approved_dir = base_dir / "Approved"

        # Platform handlers
        self.platforms = {}
        self._initialize_platforms()

        # Playwright instances (for WhatsApp)
        self.playwright = None
        self.whatsapp_context = None

        self.logger.info("MessageSenderV2 initialized")

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger("message_sender")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
        ))
        logger.addHandler(handler)

        return logger

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    def _initialize_platforms(self):
        """Initialize platform handlers"""
        platform_configs = self.config.get('platforms', {})

        for platform_name, platform_config in platform_configs.items():
            if not platform_config.get('enabled', True):
                continue

            # Determine session directory
            if platform_name == 'gmail':
                session_dir = self.sessions_dir
            else:
                session_dir = self.sessions_dir / platform_config.get('session_dir', platform_name)

            # Map platform names to handler classes
            platform_classes = {
                'gmail': GmailPlatform,
                'whatsapp': WhatsAppPlatform
            }

            handler_class = platform_classes.get(platform_name)
            if handler_class:
                self.platforms[platform_name] = handler_class(
                    config=platform_config,
                    session_dir=session_dir,
                    logs_dir=self.logs_dir,
                    logger=self.logger
                )
                self.logger.info(f"Initialized {platform_name} platform handler")

    async def initialize_browser(self):
        """Initialize Playwright for WhatsApp"""
        if not PLAYWRIGHT_AVAILABLE:
            self.logger.warning("Playwright not available, WhatsApp messaging disabled")
            return

        try:
            self.playwright = await async_playwright().start()
            self.logger.info("Playwright initialized for WhatsApp")
        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright: {e}")
            raise

    async def get_whatsapp_context(self) -> Optional[BrowserContext]:
        """Get or create persistent browser context for WhatsApp"""
        try:
            if self.whatsapp_context:
                return self.whatsapp_context

            if not PLAYWRIGHT_AVAILABLE or not self.playwright:
                return None

            whatsapp_handler = self.platforms.get('whatsapp')
            if not whatsapp_handler:
                return None

            browser_config = self.config.get('browser', {})

            self.whatsapp_context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(whatsapp_handler.session_dir),
                headless=browser_config.get('headless', False),
                viewport=browser_config.get('viewport', {'width': 1280, 'height': 720}),
                user_agent=browser_config.get('user_agent')
            )

            self.logger.info("Created persistent context for WhatsApp")
            return self.whatsapp_context

        except Exception as e:
            self.logger.error(f"Failed to create WhatsApp context: {e}")
            return None

    async def close_browser(self):
        """Close browser and contexts"""
        try:
            if self.whatsapp_context:
                await self.whatsapp_context.close()
                self.logger.info("Closed WhatsApp context")

            if self.playwright:
                await self.playwright.stop()

            self.logger.info("Browser closed")

        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")

    def parse_message_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse markdown file with YAML frontmatter

        Args:
            file_path: Path to markdown file

        Returns:
            Parsed message data or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split frontmatter and content
            if not content.startswith('---'):
                self.logger.error(f"Invalid file format: {file_path.name}")
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                self.logger.error(f"Invalid frontmatter: {file_path.name}")
                return None

            # Parse YAML frontmatter
            import yaml
            frontmatter = yaml.safe_load(parts[1])

            # Get content (strip leading/trailing whitespace)
            message_content = parts[2].strip()

            return {
                'platform': frontmatter.get('platform', '').lower(),
                'type': frontmatter.get('type', 'message'),
                'to': frontmatter.get('to', ''),
                'subject': frontmatter.get('subject', ''),
                'content': frontmatter.get('content', message_content),
                'attachments': frontmatter.get('attachments', []),
                'metadata': frontmatter
            }

        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path.name}: {e}")
            return None

    async def send_message(self, message_data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """
        Send a message with retry logic

        Args:
            message_data: Parsed message data
            file_path: Path to original file

        Returns:
            Execution result
        """
        platform = message_data.get('platform')
        to = message_data.get('to')
        subject = message_data.get('subject', '')
        content = message_data.get('content')
        attachments = message_data.get('attachments', [])

        # Validate platform
        if platform not in self.platforms:
            return {
                'success': False,
                'platform': platform,
                'error': f'Unsupported platform: {platform}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        # Initialize browser if needed for WhatsApp
        if platform == 'whatsapp' and not self.playwright:
            try:
                await self.initialize_browser()
            except Exception as e:
                return {
                    'success': False,
                    'platform': platform,
                    'error': f'Failed to initialize browser: {str(e)}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

        # Publish start event
        if self.event_bus:
            self.event_bus.publish('message.send.started', {
                'platform': platform,
                'to': to,
                'file': file_path.name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Get retry configuration
        retry_config = self.config.get('retry', {})
        max_attempts = retry_config.get('max_attempts', 3)
        initial_delay = retry_config.get('initial_delay', 5000) / 1000
        backoff_multiplier = retry_config.get('backoff_multiplier', 2)

        # Retry loop
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"Attempt {attempt}/{max_attempts} for {platform} message")

                platform_handler = self.platforms[platform]

                # Handle platform-specific sending
                if platform == 'gmail':
                    result = await platform_handler.send_message(to, subject, content, attachments)

                elif platform == 'whatsapp':
                    # WhatsApp requires Playwright
                    context = await self.get_whatsapp_context()
                    if not context:
                        raise Exception("Failed to create WhatsApp browser context")

                    pages = context.pages
                    page = pages[0] if pages else await context.new_page()

                    result = await platform_handler.send_message_with_page(page, to, content)

                else:
                    raise Exception(f"Unknown platform: {platform}")

                if result.get('success'):
                    self.logger.info(f"Message sent successfully on {platform}")

                    # Publish success event
                    if self.event_bus:
                        self.event_bus.publish('message.send.completed', {
                            'platform': platform,
                            'to': to,
                            'file': file_path.name,
                            'success': True,
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        })

                    # Log to audit
                    if self.audit_logger:
                        self.audit_logger.log_event(
                            event_type='message_sent',
                            actor='message_sender',
                            action='send',
                            resource=platform,
                            result='success',
                            metadata={'file': file_path.name, 'to': to}
                        )

                    return result

                else:
                    last_error = result.get('error', 'Unknown error')
                    self.logger.warning(f"Attempt {attempt} failed: {last_error}")

                    if attempt < max_attempts:
                        delay = initial_delay * (backoff_multiplier ** (attempt - 1))
                        self.logger.info(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)

            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Attempt {attempt} error: {e}")

                if attempt < max_attempts:
                    delay = initial_delay * (backoff_multiplier ** (attempt - 1))
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)

        # All attempts failed
        self.logger.error(f"All {max_attempts} attempts failed for {platform} message")

        # Publish failure event
        if self.event_bus:
            self.event_bus.publish('message.send.failed', {
                'platform': platform,
                'to': to,
                'file': file_path.name,
                'error': last_error,
                'attempts': max_attempts,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Log to audit
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type='message_sent',
                actor='message_sender',
                action='send',
                resource=platform,
                result='failure',
                metadata={
                    'file': file_path.name,
                    'to': to,
                    'error': last_error,
                    'attempts': max_attempts
                }
            )

        return {
            'success': False,
            'platform': platform,
            'error': last_error,
            'attempts': max_attempts,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    async def process_approved_messages(self) -> Dict[str, Any]:
        """
        Process all approved messages from /Approved folder

        Returns:
            Summary of processing results
        """
        try:
            # Initialize browser for WhatsApp if needed
            if 'whatsapp' in self.platforms:
                await self.initialize_browser()

            # Get approved files (MESSAGE_*.md)
            if self.folder_manager:
                approved_files = [f for f in self.folder_manager.list_approved()
                                 if f.name.startswith('MESSAGE_')]
            else:
                approved_files = list(self.approved_dir.glob('MESSAGE_*.md'))

            self.logger.info(f"Found {len(approved_files)} approved message(s)")

            results = {
                'total': len(approved_files),
                'successful': 0,
                'failed': 0,
                'details': []
            }

            for file_path in approved_files:
                self.logger.info(f"Processing: {file_path.name}")

                # Parse message file
                message_data = self.parse_message_file(file_path)
                if not message_data:
                    self.logger.error(f"Failed to parse: {file_path.name}")
                    results['failed'] += 1
                    continue

                # Send message
                result = await self.send_message(message_data, file_path)

                # Move file based on result
                if result.get('success'):
                    if self.folder_manager:
                        self.folder_manager.move_to_done(file_path.name)
                    results['successful'] += 1
                else:
                    if self.folder_manager:
                        error_msg = result.get('error', 'Unknown error')
                        self.folder_manager.move_to_failed(file_path.name, error_msg)
                    results['failed'] += 1

                results['details'].append({
                    'file': file_path.name,
                    'platform': message_data.get('platform'),
                    'to': message_data.get('to'),
                    'success': result.get('success'),
                    'error': result.get('error')
                })

            await self.close_browser()

            self.logger.info(f"Processing complete: {results['successful']} successful, {results['failed']} failed")

            return results

        except Exception as e:
            self.logger.error(f"Error processing approved messages: {e}")
            await self.close_browser()
            raise


async def main():
    """Main entry point for standalone execution"""
    # Determine base directory
    base_dir = Path(__file__).parent.parent.parent

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger("message_sender")

    # Initialize sender
    sender = MessageSenderV2(
        base_dir=base_dir,
        logger=logger
    )

    # Process approved messages
    results = await sender.process_approved_messages()

    # Print summary
    print("\n" + "=" * 60)
    print("MESSAGE SENDER - RESULTS")
    print("=" * 60)
    print(f"Total: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
