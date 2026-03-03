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

            # Run async initialization with new event loop
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(self._async_initialize())
                return success
            finally:
                # Don't close the loop, we'll reuse it
                pass

        except Exception as e:
            self.logger.error(f"Error initializing WhatsApp Web: {e}")
            return False

    async def _async_initialize(self) -> bool:
        """Async initialization of browser"""
        try:
            # Create user data directory
            self.user_data_dir.mkdir(parents=True, exist_ok=True)

            # Check if session exists
            session_exists = (self.user_data_dir / "Default").exists()

            if not session_exists and self.headless:
                self.logger.error("=" * 80)
                self.logger.error("NO WHATSAPP SESSION FOUND")
                self.logger.error("Cannot run in headless mode without an existing session.")
                self.logger.error("Please run the authentication script first:")
                self.logger.error("  python debug_whatsapp.py")
                self.logger.error("Or run the watcher with headless=False to authenticate.")
                self.logger.error("=" * 80)
                return False

            # Launch Playwright
            self.playwright = await async_playwright().start()

            # Launch browser with persistent context and anti-detection flags
            self.context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                viewport={'width': 1280, 'height': 720},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
                args=[
                    '--disable-blink-features=AutomationControlled',
                    '--disable-dev-shm-usage',
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-web-security',
                    '--disable-features=IsolateOrigins,site-per-process'
                ]
            )

            # Get or create page
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = await self.context.new_page()

            # Hide automation indicators
            await self.page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)

            # Navigate to WhatsApp Web
            self.logger.info("Navigating to WhatsApp Web...")

            # Try loading multiple times if needed
            for attempt in range(3):
                try:
                    await self.page.goto('https://web.whatsapp.com', wait_until='load', timeout=60000)
                    await asyncio.sleep(5)

                    # Check if page has any content
                    body_content = await self.page.content()
                    if len(body_content) > 1000:  # Page has substantial content
                        break

                    self.logger.warning(f"Page seems empty, attempt {attempt + 1}/3")
                    if attempt < 2:
                        await self.page.reload()
                except Exception as e:
                    self.logger.warning(f"Load attempt {attempt + 1} failed: {e}")
                    if attempt < 2:
                        await asyncio.sleep(3)

            # Wait for WhatsApp to load
            try:
                # Wait for page to load
                self.logger.info("Waiting for WhatsApp to load...")

                # First wait for the main app container
                await self.page.wait_for_selector('[id="app"]', timeout=30000)
                self.logger.info("WhatsApp app container loaded")

                # Give WhatsApp extra time to render content (it loads very slowly)
                self.logger.info("Waiting for WhatsApp content to render (20 seconds)...")
                await asyncio.sleep(20)

                # Now check what's on the page - try multiple selectors
                # Check for chat pane (means logged in)
                chat_selectors = [
                    '[id="pane-side"]',
                    '[data-testid="chat-list"]',
                    'div[role="grid"]',  # Chat list grid
                    'div[aria-label*="Chat"]',
                ]

                chat_found = False
                for selector in chat_selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        self.logger.info(f"Found chat element: {selector}")
                        chat_found = True
                        break

                if chat_found:
                    self.logger.info("Already logged in via saved session")
                    self.logger.info("WhatsApp Web connection established")
                    return True

                # If no chat pane, look for QR code or login area
                self.logger.info("No chat pane found, checking for QR code...")

                # Check for QR code with multiple methods
                qr_selectors = [
                    'canvas',
                    'div[data-ref]',
                    'div[role="button"][data-icon="qr"]',
                ]

                qr_found = False
                for selector in qr_selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        try:
                            is_visible = await element.is_visible()
                            if is_visible:
                                self.logger.info(f"Found QR code element: {selector}")
                                qr_found = True
                                break
                        except:
                            continue

                if qr_found:
                    self.logger.warning("QR code detected - please scan with your phone NOW")
                    self.logger.info("Waiting for login (up to 3 minutes)...")

                    # Poll for chat pane to appear (indicates successful login)
                    for i in range(36):  # Check every 5 seconds for 3 minutes
                        await asyncio.sleep(5)

                        # Check all chat selectors
                        for selector in chat_selectors:
                            element = await self.page.query_selector(selector)
                            if element:
                                self.logger.info("Login successful!")
                                self.logger.info("WhatsApp Web connection established")
                                return True

                    self.logger.error("Login timeout - please scan QR code and try again")
                    return False

                # If we can't find chat pane or QR code, wait longer and take a screenshot
                self.logger.warning("Could not detect WhatsApp login state clearly")
                self.logger.info("Waiting additional 15 seconds for QR code to fully render...")
                await asyncio.sleep(15)

                self.logger.info("Taking screenshot for debugging...")
                screenshot_path = self.user_data_dir / "auth_debug.png"
                await self.page.screenshot(path=str(screenshot_path))
                self.logger.info(f"Screenshot saved to: {screenshot_path}")
                self.logger.info("=" * 80)
                self.logger.info("SCAN THE QR CODE NOW!")
                self.logger.info(f"Location: {screenshot_path}")
                self.logger.info("Open WhatsApp on your phone -> Settings -> Linked Devices -> Link a Device")
                self.logger.info("You have 2 minutes to scan the code...")
                self.logger.info("=" * 80)

                # Poll for login every 5 seconds for 2 minutes
                for i in range(24):  # 24 * 5 = 120 seconds
                    await asyncio.sleep(5)

                    # Check if logged in
                    for selector in chat_selectors:
                        element = await self.page.query_selector(selector)
                        if element:
                            self.logger.info("✓ Login successful!")
                            self.logger.info("WhatsApp Web connection established")
                            return True

                    if i % 6 == 0:  # Log every 30 seconds
                        self.logger.info(f"Still waiting... ({(i+1)*5} seconds elapsed)")

                # Final check with all selectors
                for selector in chat_selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        self.logger.info("WhatsApp Web connection established")
                        return True

                self.logger.error("Could not establish WhatsApp connection")
                return False

            except Exception as e:
                self.logger.error(f"Failed to load WhatsApp Web: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error in async initialization: {e}")
            return False

    def check_for_events(self) -> List[Dict]:
        """Check for new WhatsApp messages"""
        try:
            # Run async check with existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
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

            # Run async cleanup with existing event loop
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                loop.run_until_complete(self._async_cleanup())
            except Exception as e:
                self.logger.error(f"Error in async cleanup: {e}")

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
