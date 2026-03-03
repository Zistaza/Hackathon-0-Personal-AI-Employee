#!/usr/bin/env python3
"""
LinkedIn Watcher
Monitors LinkedIn for new messages, notifications, and connection requests
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


class LinkedInWatcher(BaseWatcher):
    """LinkedIn watcher implementation"""

    def __init__(
        self,
        user_data_dir: str = "./linkedin_session",
        check_interval: int = 600,  # 10 minutes default (LinkedIn rate limiting)
        keywords: Optional[List[str]] = None,
        headless: bool = False,
        monitor_messages: bool = True,
        monitor_notifications: bool = True
    ):
        """
        Initialize LinkedIn watcher

        Args:
            user_data_dir: Directory to store browser session
            check_interval: Seconds between checks
            keywords: List of keywords to filter for
            headless: Run browser in headless mode
            monitor_messages: Monitor new messages
            monitor_notifications: Monitor notifications
        """
        # Initialize base watcher
        super().__init__(
            name="linkedin",
            check_interval=check_interval,
            keywords=keywords or ["job", "opportunity", "interview", "proposal", "project"]
        )

        self.user_data_dir = Path(__file__).parent / user_data_dir.lstrip("./")
        self.headless = headless
        self.monitor_messages = monitor_messages
        self.monitor_notifications = monitor_notifications

        # Browser objects
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    def initialize(self) -> bool:
        """Initialize LinkedIn connection"""
        try:
            self.logger.info("Initializing LinkedIn connection...")

            # Run async initialization
            loop = asyncio.get_event_loop()
            success = loop.run_until_complete(self._async_initialize())

            return success

        except Exception as e:
            self.logger.error(f"Error initializing LinkedIn: {e}")
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

            # Navigate to LinkedIn
            self.logger.info("Navigating to LinkedIn...")
            await self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=60000)

            # Wait for LinkedIn to load
            try:
                # Wait for page to load
                self.logger.info("Waiting for LinkedIn to load...")
                await asyncio.sleep(8)  # Give page time to render

                # Check current URL and title to determine if logged in
                current_url = self.page.url
                title = await self.page.title()

                self.logger.info(f"Current URL: {current_url}")
                self.logger.info(f"Page title: {title}")

                # If we're on the feed page, we're logged in
                if '/feed' in current_url and 'LinkedIn' in title:
                    # Verify by checking for navigation (which exists when logged in)
                    nav = await self.page.query_selector('nav')
                    if nav:
                        self.logger.info("Already logged in via saved session")
                        self.logger.info("LinkedIn connection established")
                        return True

                # Check if we got redirected to login page
                if '/login' in current_url or 'Sign In' in title or 'Join now' in title:
                    self.logger.warning("Login required - please login manually in the browser")
                    self.logger.info("Waiting for login (up to 5 minutes)...")

                    # Wait for successful login by checking URL change
                    for i in range(60):  # Check every 5 seconds for 5 minutes
                        await asyncio.sleep(5)
                        current_url = self.page.url
                        title = await self.page.title()

                        if '/feed' in current_url and 'LinkedIn' in title:
                            nav = await self.page.query_selector('nav')
                            if nav:
                                self.logger.info("Login successful!")
                                self.logger.info("LinkedIn connection established")
                                return True

                    self.logger.error("Login timeout - please try again")
                    return False

                # Try to find navigation as fallback check
                nav = await self.page.wait_for_selector('nav', timeout=10000)
                if nav:
                    self.logger.info("LinkedIn connection established")
                    return True

                self.logger.error("Could not verify LinkedIn login")
                return False

            except Exception as e:
                self.logger.error(f"Failed to load LinkedIn: {e}")
                return False

        except Exception as e:
            self.logger.error(f"Error in async initialization: {e}")
            return False

    def check_for_events(self) -> List[Dict]:
        """Check for new LinkedIn events"""
        try:
            # Run async check
            loop = asyncio.get_event_loop()
            events = loop.run_until_complete(self._async_check_for_events())
            return events

        except Exception as e:
            self.logger.error(f"Error checking for events: {e}")
            return []

    async def _async_check_for_events(self) -> List[Dict]:
        """Async check for new events"""
        events = []

        try:
            # Check messages
            if self.monitor_messages:
                message_events = await self._check_messages()
                events.extend(message_events)

            # Check notifications
            if self.monitor_notifications:
                notification_events = await self._check_notifications()
                events.extend(notification_events)

        except Exception as e:
            self.logger.error(f"Error in async check: {e}")

        return events

    async def _check_messages(self) -> List[Dict]:
        """Check for new messages"""
        events = []

        try:
            self.logger.info("Checking LinkedIn messages...")

            # Navigate to messaging
            await self.page.goto('https://www.linkedin.com/messaging/', wait_until='networkidle')
            await self.page.wait_for_timeout(2000)

            # Get unread message indicators
            unread_indicators = await self.page.query_selector_all('[class*="msg-conversation-card--unread"]')

            self.logger.info(f"Found {len(unread_indicators)} unread conversation(s)")

            # Process each unread conversation
            for indicator in unread_indicators[:5]:  # Limit to 5 most recent
                try:
                    # Click on conversation
                    await indicator.click()
                    await self.page.wait_for_timeout(1500)

                    # Get sender name
                    sender_element = await self.page.query_selector('[class*="msg-thread__link-to-profile"]')
                    sender = await sender_element.text_content() if sender_element else "Unknown"

                    # Get message content
                    message_elements = await self.page.query_selector_all('[class*="msg-s-event-listitem__body"]')

                    # Get last few messages
                    recent_messages = message_elements[-3:] if len(message_elements) > 3 else message_elements

                    for msg_element in recent_messages:
                        try:
                            # Get message text
                            text_element = await msg_element.query_selector('[class*="msg-s-event-listitem__message-bubble"]')
                            if not text_element:
                                continue

                            content = await text_element.text_content()
                            content = content.strip()

                            if not content:
                                continue

                            # Create unique message ID
                            message_id = f"linkedin_msg_{hash(sender + content)}"

                            # Create event
                            event = {
                                'id': message_id,
                                'content': f"**From:** {sender.strip()}\n\n**Message:**\n{content}",
                                'metadata': {
                                    'type': 'linkedin_message',
                                    'sender': sender.strip(),
                                    'timestamp': datetime.utcnow().isoformat() + 'Z',
                                    'status': 'pending'
                                }
                            }

                            events.append(event)

                        except Exception as e:
                            continue

                except Exception as e:
                    self.logger.error(f"Error processing conversation: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error checking messages: {e}")

        return events

    async def _check_notifications(self) -> List[Dict]:
        """Check for new notifications"""
        events = []

        try:
            self.logger.info("Checking LinkedIn notifications...")

            # Navigate to notifications
            await self.page.goto('https://www.linkedin.com/notifications/', wait_until='networkidle')
            await self.page.wait_for_timeout(2000)

            # Get notification items
            notification_items = await self.page.query_selector_all('[class*="notification-card"]')

            self.logger.info(f"Found {len(notification_items)} notification(s)")

            # Process recent notifications
            for item in notification_items[:10]:  # Limit to 10 most recent
                try:
                    # Check if unread
                    is_unread = await item.query_selector('[class*="notification-card--unread"]')
                    if not is_unread:
                        continue

                    # Get notification text
                    text_element = await item.query_selector('[class*="notification-card__text"]')
                    if not text_element:
                        continue

                    content = await text_element.text_content()
                    content = content.strip()

                    if not content:
                        continue

                    # Get timestamp
                    time_element = await item.query_selector('[class*="notification-card__time"]')
                    time_text = await time_element.text_content() if time_element else ""

                    # Create unique notification ID
                    notification_id = f"linkedin_notif_{hash(content)}"

                    # Create event
                    event = {
                        'id': notification_id,
                        'content': content,
                        'metadata': {
                            'type': 'linkedin_notification',
                            'timestamp': datetime.utcnow().isoformat() + 'Z',
                            'time_text': time_text.strip(),
                            'status': 'pending'
                        }
                    }

                    events.append(event)

                except Exception as e:
                    continue

        except Exception as e:
            self.logger.error(f"Error checking notifications: {e}")

        return events

    def cleanup(self):
        """Cleanup browser resources"""
        try:
            self.logger.info("Cleaning up LinkedIn watcher...")

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
    watcher = LinkedInWatcher(
        check_interval=600,  # 10 minutes (LinkedIn rate limiting)
        keywords=["job", "opportunity", "interview", "proposal", "project"],
        headless=False,  # Set to True for background operation
        monitor_messages=True,
        monitor_notifications=True
    )

    # Run continuously
    watcher.run()


if __name__ == "__main__":
    main()
