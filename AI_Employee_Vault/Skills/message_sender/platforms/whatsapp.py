"""
WhatsApp Platform Handler
==========================

Handles WhatsApp messaging via WhatsApp Web automation using Playwright.
"""

from typing import Dict, Any, List, Optional
from .base import BaseMessagePlatform


class WhatsAppPlatform(BaseMessagePlatform):
    """WhatsApp-specific message sending logic using Playwright"""

    async def send_message(self, to: str, subject: str, content: str,
                          attachments: List[str] = None) -> Dict[str, Any]:
        """
        Send WhatsApp message via WhatsApp Web

        Args:
            to: Contact name (as it appears in WhatsApp)
            subject: Not used for WhatsApp (ignored)
            content: Message content
            attachments: Not supported yet (ignored)

        Returns:
            Result dictionary
        """
        # Note: This method expects a Playwright page object to be passed
        # The actual implementation will be called from the main sender
        raise NotImplementedError("Use send_message_with_page() instead")

    async def send_message_with_page(self, page, to: str, content: str) -> Dict[str, Any]:
        """
        Send WhatsApp message using existing Playwright page

        Args:
            page: Playwright page object
            to: Contact name
            content: Message content

        Returns:
            Result dictionary
        """
        try:
            self.logger.info(f"Sending WhatsApp message to: {to}")

            # Validate message
            validation = self.validate_message(to, content)
            if not validation["valid"]:
                return {
                    "success": False,
                    "platform": "whatsapp",
                    "error": validation["error"],
                    "timestamp": self._get_timestamp()
                }

            # Navigate to WhatsApp Web
            whatsapp_url = self.config.get('url', 'https://web.whatsapp.com')
            await page.goto(whatsapp_url, wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Check if logged in
            if not await self._is_logged_in(page):
                screenshot = await self._take_screenshot(page, "not_logged_in")
                return {
                    "success": False,
                    "platform": "whatsapp",
                    "error": "Not logged in to WhatsApp Web. Please scan QR code.",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Search for contact
            selectors = self.config.get('selectors', {})
            search_box_selector = selectors.get('search_box', "[data-testid='chat-list-search']")

            # Click search box
            try:
                await page.wait_for_selector(search_box_selector, timeout=10000, state='visible')
                await page.click(search_box_selector)
                await page.wait_for_timeout(500)
            except Exception as e:
                screenshot = await self._take_screenshot(page, "search_box_not_found")
                return {
                    "success": False,
                    "platform": "whatsapp",
                    "error": f"Could not find search box: {e}",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Type contact name
            await page.keyboard.type(to, delay=100)
            await page.wait_for_timeout(2000)  # Wait for search results

            # Click on first matching contact
            chat_item_selector = selectors.get('chat_item', "[data-testid='cell-frame-container']")
            try:
                # Wait for search results
                await page.wait_for_selector(chat_item_selector, timeout=5000, state='visible')

                # Click first result
                await page.click(f"{chat_item_selector}:first-child")
                await page.wait_for_timeout(1500)

                self.logger.info(f"Opened chat with: {to}")
            except Exception as e:
                screenshot = await self._take_screenshot(page, "contact_not_found")
                return {
                    "success": False,
                    "platform": "whatsapp",
                    "error": f"Contact not found: {to}",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Type message
            message_box_selector = selectors.get('message_box', "[data-testid='conversation-compose-box-input']")
            try:
                await page.wait_for_selector(message_box_selector, timeout=5000, state='visible')
                await page.click(message_box_selector)
                await page.wait_for_timeout(500)

                # Type message using keyboard for reliability
                await page.keyboard.type(content, delay=50)
                await page.wait_for_timeout(500)

                self.logger.info("Message typed successfully")
            except Exception as e:
                screenshot = await self._take_screenshot(page, "message_typing_failed")
                return {
                    "success": False,
                    "platform": "whatsapp",
                    "error": f"Failed to type message: {e}",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Click send button
            send_button_selector = selectors.get('send_button', "[data-testid='send']")
            try:
                # Try multiple possible selectors for send button
                send_clicked = False
                for selector in [send_button_selector, "button[aria-label*='Send']", "[data-icon='send']"]:
                    try:
                        await page.wait_for_selector(selector, timeout=2000, state='visible')
                        await page.click(selector)
                        send_clicked = True
                        break
                    except:
                        continue

                if not send_clicked:
                    # Fallback: press Enter key
                    await page.keyboard.press('Enter')
                    self.logger.info("Sent message using Enter key")
                else:
                    self.logger.info("Clicked send button")

                await page.wait_for_timeout(2000)

            except Exception as e:
                screenshot = await self._take_screenshot(page, "send_failed")
                return {
                    "success": False,
                    "platform": "whatsapp",
                    "error": f"Failed to send message: {e}",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("WhatsApp message sent successfully")

            return {
                "success": True,
                "platform": "whatsapp",
                "to": to,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            self.logger.error(f"WhatsApp sending failed: {e}")
            screenshot = await self._take_screenshot(page, "unexpected_error")
            return {
                "success": False,
                "platform": "whatsapp",
                "error": str(e),
                "screenshot": screenshot,
                "to": to,
                "timestamp": self._get_timestamp()
            }

    async def _is_logged_in(self, page) -> bool:
        """Check if user is logged in to WhatsApp Web"""
        try:
            # Check for chat list which indicates logged-in state
            await page.wait_for_selector('[data-testid="chat-list"]', timeout=5000)
            return True
        except:
            return False

    async def _take_screenshot(self, page, error_context: str) -> Optional[str]:
        """Take screenshot on error"""
        try:
            from datetime import datetime
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"whatsapp_error_{error_context}_{timestamp}.png"
            screenshot_path = self.logs_dir / filename

            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"Screenshot saved: {screenshot_path}")

            return str(screenshot_path)

        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None
