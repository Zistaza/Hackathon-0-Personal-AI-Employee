#!/usr/bin/env python3
"""
Instagram Watcher
Monitors Instagram for new notifications and direct messages
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


class InstagramWatcher(BaseWatcher):
    """Instagram watcher implementation"""

    def __init__(
        self,
        user_data_dir: str = "./instagram_session",
        check_interval: int = 600,  # 10 minutes default
        keywords: Optional[List[str]] = None,
        headless: bool = False,
        monitor_notifications: bool = True,
        monitor_messages: bool = True
    ):
        """
        Initialize Instagram watcher

        Args:
            user_data_dir: Directory to store browser session
            check_interval: Seconds between checks
            keywords: List of keywords to filter for
            headless: Run browser in headless mode
            monitor_notifications: Monitor notifications
            monitor_messages: Monitor direct messages
        """
        # Initialize base watcher
        super().__init__(
            name="instagram",
            check_interval=check_interval,
            keywords=keywords or ["urgent", "important", "collab", "partnership", "business"]
        )

        self.user_data_dir = Path(__file__).parent / user_data_dir.lstrip("./")
        self.headless = headless
        self.monitor_notifications = monitor_notifications
        self.monitor_messages = monitor_messages

        # Browser objects
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def initialize(self) -> bool:
        """Initialize Instagram connection"""
        try:
            self.logger.info("Initializing Instagram connection...")

            # Run async initialization
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                success = loop.run_until_complete(self._async_initialize())
                return success
            finally:
                # Don't close the loop, we'll reuse it
                pass

        except Exception as e:
            self.logger.error(f"Error initializing Instagram: {e}")
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
                self.logger.error("NO INSTAGRAM SESSION FOUND")
                self.logger.error("Cannot run in headless mode without an existing session.")
                self.logger.error("Please run with headless=False first to authenticate.")
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
                    '--disable-setuid-sandbox'
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

            # Navigate to Instagram
            self.logger.info("Navigating to Instagram...")
            await self.page.goto('https://www.instagram.com/', wait_until='domcontentloaded', timeout=60000)
            await asyncio.sleep(5)

            # Check if logged in
            try:
                # Wait for page to load
                self.logger.info("Checking login status...")
                await asyncio.sleep(3)

                # Check for logged-in indicators
                logged_in_selectors = [
                    'svg[aria-label="Home"]',  # Home icon in nav
                    'a[href*="/direct/inbox"]',  # Messages link
                    'svg[aria-label="New post"]',  # New post button
                    'img[alt*="profile picture"]',  # Profile picture
                ]

                logged_in = False
                for selector in logged_in_selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        self.logger.info(f"Found logged-in element: {selector}")
                        logged_in = True
                        break

                if logged_in:
                    self.logger.info("Already logged in via saved session")
                    self.logger.info("Instagram connection established")
                    return True

                # Check for login form
                login_selectors = [
                    'input[name="username"]',
                    'input[type="text"][aria-label*="username"]',
                    'button[type="submit"]'
                ]

                login_form_found = False
                for selector in login_selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        self.logger.info(f"Found login form element: {selector}")
                        login_form_found = True
                        break

                if login_form_found:
                    self.logger.warning("=" * 80)
                    self.logger.warning("LOGIN REQUIRED")
                    self.logger.warning("Please log in to Instagram in the browser window")
                    self.logger.warning("The browser window should be visible now")
                    self.logger.warning("After logging in, the watcher will continue automatically")
                    self.logger.warning("You have 5 minutes to complete login...")
                    self.logger.warning("=" * 80)

                    # Wait for login to complete
                    for i in range(180):  # Check every 5 seconds for 15 minutes
                        await asyncio.sleep(5)

                        # Check if logged in
                        for selector in logged_in_selectors:
                            element = await self.page.query_selector(selector)
                            if element:
                                self.logger.info("Login successful!")
                                self.logger.info("Instagram connection established")
                                return True

                        if i % 6 == 0:  # Log every 30 seconds
                            self.logger.info(f"Still waiting for login... ({(i+1)*5} seconds elapsed)")

                    self.logger.error("Login timeout - please try again")
                    return False

                # If we can't determine state, wait and check again
                self.logger.warning("Could not determine login state clearly")
                self.logger.info("Waiting 10 seconds and checking again...")
                await asyncio.sleep(10)

                # Final check
                for selector in logged_in_selectors:
                    element = await self.page.query_selector(selector)
                    if element:
                        self.logger.info("Instagram connection established")
                        return True

                self.logger.error("Could not establish Instagram connection")
                return False

            except Exception as e:
                self.logger.error(f"Failed to verify Instagram login: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error in async initialization: {e}")
            return False

    def check_for_events(self) -> List[Dict]:
        """Check for new Instagram events"""
        try:
            # Run async check
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
        """Async check for new events"""
        events = []

        try:
            # Check notifications
            if self.monitor_notifications:
                notification_events = await self._check_notifications()
                events.extend(notification_events)

            # Check messages
            if self.monitor_messages:
                message_events = await self._check_messages()
                events.extend(message_events)

        except Exception as e:
            self.logger.error(f"Error in async check: {e}")

        return events

    async def _check_notifications(self) -> List[Dict]:
        """Check for new notifications"""
        events = []

        try:
            self.logger.info("Checking Instagram notifications...")

            # Navigate to home page first
            await self.page.goto('https://www.instagram.com/', wait_until='domcontentloaded')
            await asyncio.sleep(2)

            # Click on notifications icon
            notification_icon_selectors = [
                'svg[aria-label="Notifications"]',
                'a[href="#"]',  # Notifications link
            ]

            clicked = False
            for selector in notification_icon_selectors:
                try:
                    element = await self.page.query_selector(selector)
                    if element:
                        await element.click()
                        await asyncio.sleep(2)
                        clicked = True
                        self.logger.info(f"Clicked notifications using: {selector}")
                        break
                except:
                    continue

            if not clicked:
                self.logger.warning("Could not open notifications panel")
                return events

            # Get notification items
            notification_selectors = [
                'div[role="menuitem"]',
                'div[class*="notification"]',
                'a[href*="/p/"]',  # Post links in notifications
            ]

            notification_items = []
            for selector in notification_selectors:
                items = await self.page.query_selector_all(selector)
                if items and len(items) > 0:
                    notification_items = items
                    self.logger.info(f"Found {len(items)} notifications using: {selector}")
                    break

            # Process recent notifications (limit to 10)
            for item in notification_items[:10]:
                try:
                    # Get notification text
                    text_content = await item.text_content()
                    if not text_content:
                        continue

                    content = text_content.strip()
                    if not content or len(content) < 5:
                        continue

                    # Create unique notification ID
                    notification_id = f"instagram_notif_{hash(content)}"

                    # Skip if already processed
                    if self.is_processed(notification_id):
                        continue

                    # Create event
                    event = {
                        'id': notification_id,
                        'content': content,
                        'metadata': {
                            'type': 'instagram_notification',
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'status': 'pending'
                        }
                    }

                    events.append(event)

                except Exception as e:
                    self.logger.debug(f"Error processing notification: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking notifications: {e}")

        return events

    async def _check_messages(self) -> List[Dict]:
        """Check for new direct messages"""
        events = []

        try:
            self.logger.info("Checking Instagram direct messages...")

            # Navigate to direct messages
            await self.page.goto('https://www.instagram.com/direct/inbox/', wait_until='domcontentloaded')
            await asyncio.sleep(3)

            # Get message threads
            thread_selectors = [
                'div[role="listitem"]',
                'a[role="link"]',
                'div[class*="thread"]'
            ]

            threads = []
            for selector in thread_selectors:
                items = await self.page.query_selector_all(selector)
                if items and len(items) > 0:
                    threads = items
                    self.logger.info(f"Found {len(items)} message threads using: {selector}")
                    break

            self.logger.info(f"Found {len(threads)} message thread(s)")

            # Process recent threads (limit to 5)
            for thread in threads[:5]:
                try:
                    # Click on thread
                    await thread.click()
                    await asyncio.sleep(2)

                    # Get sender name
                    sender_selectors = [
                        'header a',
                        'div[class*="username"]',
                        'span[class*="username"]'
                    ]

                    sender = "Unknown"
                    for selector in sender_selectors:
                        sender_element = await self.page.query_selector(selector)
                        if sender_element:
                            sender_text = await sender_element.text_content()
                            if sender_text and len(sender_text.strip()) > 0:
                                sender = sender_text.strip()
                                break

                    # Get recent messages
                    message_selectors = [
                        'div[role="row"]',
                        'div[class*="message"]',
                        'div[dir="auto"]'
                    ]

                    messages = []
                    for selector in message_selectors:
                        msg_elements = await self.page.query_selector_all(selector)
                        if msg_elements and len(msg_elements) > 0:
                            messages = msg_elements[-5:]  # Last 5 messages
                            break

                    for msg_element in messages:
                        try:
                            content = await msg_element.text_content()
                            if not content:
                                continue

                            content = content.strip()
                            if not content or len(content) < 2:
                                continue

                            # Create unique message ID
                            message_id = f"instagram_msg_{hash(sender + content)}"

                            # Skip if already processed
                            if self.is_processed(message_id):
                                continue

                            # Create event
                            event = {
                                'id': message_id,
                                'content': f"**From:** {sender}\n\n**Message:**\n{content}",
                                'metadata': {
                                    'type': 'instagram_message',
                                    'sender': sender,
                                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                                    'status': 'pending'
                                }
                            }

                            events.append(event)

                        except Exception as e:
                            continue

                except Exception as e:
                    self.logger.debug(f"Error processing thread: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking messages: {e}")

        return events

    def cleanup(self):
        """Cleanup browser resources"""
        try:
            self.logger.info("Cleaning up Instagram watcher...")

            # Run async cleanup
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
    watcher = InstagramWatcher(
        check_interval=600,  # 10 minutes
        keywords=["urgent", "important", "collab", "partnership", "business"],
        headless=False,  # Set to True for background operation after first login
        monitor_notifications=True,
        monitor_messages=True
    )

    # Run continuously
    watcher.run()


if __name__ == "__main__":
    main()
