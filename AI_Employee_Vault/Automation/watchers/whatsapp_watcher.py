#!/usr/bin/env python3
"""
WhatsApp Watcher
Monitors WhatsApp Web for new messages containing specific keywords
Uses Playwright for browser automation
"""

import asyncio
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

from base_watcher import BaseWatcher

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("Error: Playwright not installed")
    print("Install with: pip install playwright")
    print("Then run: playwright install chromium")
    exit(1)


class WhatsAppWatcher(BaseWatcher):
    """WhatsApp Web watcher implementation"""

    def __init__(
        self,
        user_data_dir: str = "./whatsapp_session",
        check_interval: int = 300,
        keywords: Optional[List[str]] = None,
        headless: bool = False,
        max_messages_per_chat: int = 20
    ):
        """
        Initialize WhatsApp watcher

        Args:
            user_data_dir: Directory to store browser session
            check_interval: Seconds between checks
            keywords: List of keywords to filter for
            headless: Run browser in headless mode
            max_messages_per_chat: Maximum messages to check per chat
        """
        # Initialize base watcher
        super().__init__(
            name="whatsapp",
            check_interval=check_interval,
            keywords=keywords or ["invoice", "urgent", "payment", "proposal"]
        )

        self.user_data_dir = Path(__file__).parent / user_data_dir.lstrip("./")
        self.headless = headless
        self.max_messages_per_chat = max_messages_per_chat

        # Browser objects
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def initialize(self) -> bool:
        """Initialize WhatsApp Web connection"""
        try:
            self.logger.info("Initializing WhatsApp Web connection...")

            # Run async initialization
            loop = asyncio.get_event_loop()
            success = loop.run_until_complete(self._async_initialize())

            return success

        except Exception as e:
            self.logger.error(f"Error initializing WhatsApp Web: {e}")
            return False

    async def _async_initialize(self) -> bool:
        """Async initialization of browser"""
        try:
            # Create user data directory
            self.user_data_dir.mkdir(parents=True, exist_ok=True)

            # Launch Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with persistent context
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )

            # Get or create page
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()

            # Navigate to WhatsApp Web
            self.logger.info("Navigating to WhatsApp Web...")
            await self.page.goto('https://web.whatsapp.com', wait_until='networkidle')

            # Wait for WhatsApp to load
            try:
                # Wait for either QR code or chat list
                await self.page.wait_for_selector(
                    'canvas[aria-label="Scan me!"], [data-testid="chat-list"]',
                    timeout=30000
                )

                # Check if QR code is present
                qr_code = await self.page.query_selector('canvas[aria-label="Scan me!"]')

                if qr_code:
                    self.logger.warning("QR code detected - please scan to login")
                    self.logger.info("Waiting for login (up to 2 minutes)...")
                    await self.page.wait_for_selector('[data-testid="chat-list"]', timeout=120000)
                    self.logger.info("Login successful!")
                else:
                    self.logger.info("Already logged in via saved session")

                # Additional wait for full load
                await self.page.wait_for_timeout(3000)

                self.logger.info("WhatsApp Web connection established")
                return True

            except Exception as e:
                self.logger.error(f"Failed to load WhatsApp Web: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error in async initialization: {e}")
            return False

    def check_for_events(self) -> List[Dict]:
        """Check for new WhatsApp messages"""
        try:
            # Run async check
            loop = asyncio.get_event_loop()
            events = loop.run_until_complete(self._async_check_for_events())
            return events

        except Exception as e:
            self.logger.error(f"Error checking for events: {e}")
            return []

    async def _async_check_for_events(self) -> List[Dict]:
        """Async check for new messages"""
        events = []

        try:
            self.logger.info("Scanning for unread chats...")

            # Get all chat containers
            chat_containers = await self.page.query_selector_all('[data-testid="cell-frame-container"]')

            unread_chats = []

            # Find chats with unread indicators
            for chat in chat_containers:
                try:
                    # Check for unread badge
                    unread_badge = await chat.query_selector('[data-testid="icon-unread-count"]')

                    if unread_badge:
                        # Get chat name
                        name_element = await chat.query_selector('[data-testid="cell-frame-title"]')
                        name = await name_element.text_content() if name_element else "Unknown"

                        # Get chat ID
                        chat_id = await chat.get_attribute('data-id') or f"chat_{datetime.utcnow().timestamp()}"

                        unread_chats.append({
                            'element': chat,
                            'id': chat_id,
                            'name': name.strip()
                        })

                except Exception as e:
                    continue

            self.logger.info(f"Found {len(unread_chats)} unread chat(s)")

            # Process each unread chat
            for chat in unread_chats:
                try:
                    chat_events = await self._process_chat(chat)
                    events.extend(chat_events)
                except Exception as e:
                    self.logger.error(f"Error processing chat {chat['name']}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error in async check: {e}")

        return events

    async def _process_chat(self, chat: Dict) -> List[Dict]:
        """Process a single chat"""
        events = []

        try:
            self.logger.info(f"Processing chat: {chat['name']}")

            # Click on chat
            await chat['element'].click()
            await self.page.wait_for_timeout(2000)

            # Get message containers
            message_elements = await self.page.query_selector_all('[data-testid="msg-container"]')

            # Process recent messages
            recent_messages = message_elements[-self.max_messages_per_chat:]

            for msg_element in recent_messages:
                try:
                    # Check if incoming message
                    is_incoming = await msg_element.query_selector('[data-testid="tail-in"]')
                    if not is_incoming:
                        continue

                    # Get message text
                    text_element = await msg_element.query_selector('[data-testid="conversation-text-content"]')
                    if not text_element:
                        continue

                    content = await text_element.text_content()
                    content = content.strip()

                    # Get timestamp
                    time_element = await msg_element.query_selector('[data-testid="msg-meta"]')
                    time_text = await time_element.text_content() if time_element else ""

                    # Create unique message ID
                    message_id = f"whatsapp_{chat['id']}_{hash(content)}"

                    # Create event
                    event = {
                        'id': message_id,
                        'content': content,
                        'metadata': {
                            'type': 'whatsapp',
                            'sender': chat['name'],
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'time_text': time_text.strip(),
                            'status': 'pending'
                        }
                    }

                    events.append(event)

                except Exception as e:
                    continue

        except Exception as e:
            self.logger.error(f"Error processing chat: {e}")

        return events

    def cleanup(self):
        """Cleanup browser resources"""
        try:
            self.logger.info("Cleaning up WhatsApp watcher...")

            # Run async cleanup
            loop = asyncio.get_event_loop()
            loop.run_until_complete(self._async_cleanup())

        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

    async def _async_cleanup(self):
        """Async cleanup"""
        try:
            if self.context:
                await self.context.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Error in async cleanup: {e}")


def main():
    """Main entry point"""
    # Configuration
    watcher = WhatsAppWatcher(
        check_interval=300,  # 5 minutes
        keywords=["invoice", "urgent", "payment", "proposal"],
        headless=False,  # Set to True for background operation
        max_messages_per_chat=20
    )

    # Run continuously
    watcher.run()


if __name__ == "__main__":
    main()
