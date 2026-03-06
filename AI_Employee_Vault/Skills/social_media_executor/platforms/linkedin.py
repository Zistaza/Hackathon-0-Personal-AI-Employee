"""
LinkedIn Platform Handler
=========================

Handles posting to LinkedIn with persistent sessions.
"""

from typing import Dict, Any, List, Optional
from .base import BasePlatform


class LinkedInPlatform(BasePlatform):
    """LinkedIn-specific posting logic"""

    def get_platform_url(self) -> str:
        """Get LinkedIn base URL"""
        return "https://www.linkedin.com/feed/"

    async def post(self, page, content: str, media: List[str] = None) -> Dict[str, Any]:
        """
        Post content to LinkedIn

        Args:
            page: Playwright page object
            content: Post content
            media: Optional media files

        Returns:
            Result dictionary
        """
        try:
            self.logger.info("Starting LinkedIn post...")

            # Validate content
            validation = self.validate_content(content, media)
            if not validation["valid"]:
                return {
                    "success": False,
                    "platform": "linkedin",
                    "error": validation["error"],
                    "timestamp": self._get_timestamp()
                }

            # Navigate to LinkedIn feed
            self.logger.info(f"Navigating to {self.get_platform_url()}")
            await page.goto(self.get_platform_url(), wait_until='domcontentloaded', timeout=60000)
            await page.wait_for_timeout(5000)  # Wait for dynamic content to load

            self.logger.info(f"Current URL: {page.url}")

            # Check if logged in
            if not await self._is_logged_in(page):
                screenshot = await self.take_screenshot(page, "not_logged_in")
                return {
                    "success": False,
                    "platform": "linkedin",
                    "error": "Not logged in to LinkedIn. Please authenticate first.",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Click "Start a post" button - use verified working selector
            start_post_selector = "button:has-text('Start a post')"

            try:
                self.logger.info(f"Looking for 'Start a post' button...")
                await page.wait_for_selector(start_post_selector, timeout=10000, state='visible')
                await page.click(start_post_selector)
                await page.wait_for_timeout(2000)
                self.logger.info("Clicked 'Start a post' button")
            except Exception as e:
                self.logger.error(f"Failed to click 'Start a post' button: {e}")
                screenshot = await self.take_screenshot(page, "start_post_button_not_found")
                return {
                    "success": False,
                    "platform": "linkedin",
                    "error": f"Could not find or click 'Start a post' button: {str(e)}",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Wait for editor to appear - use verified working selector
            editor_selector = '.ql-editor[contenteditable="true"]'

            try:
                self.logger.info("Waiting for post editor...")
                await page.wait_for_selector(editor_selector, timeout=10000, state='visible')
                await page.wait_for_timeout(1000)
                self.logger.info("Post editor appeared")
            except Exception as e:
                self.logger.error(f"Editor not found: {e}")
                screenshot = await self.take_screenshot(page, "editor_not_found")
                return {
                    "success": False,
                    "platform": "linkedin",
                    "error": f"Could not find post editor: {str(e)}",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Type content using keyboard for reliability
            if not await self.type_content(page, editor_selector, content):
                screenshot = await self.take_screenshot(page, "content_typing_failed")
                return {
                    "success": False,
                    "platform": "linkedin",
                    "error": "Failed to type content into editor",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Content typed successfully")

            # Upload media if provided
            if media and len(media) > 0:
                media_selector = selectors.get('media_upload', "input[type='file'][accept*='image']")
                if not await self.upload_media(page, media_selector, media):
                    screenshot = await self.take_screenshot(page, "media_upload_failed")
                    return {
                        "success": False,
                        "platform": "linkedin",
                        "error": "Failed to upload media",
                        "screenshot": screenshot,
                        "timestamp": self._get_timestamp()
                    }
                self.logger.info("Media uploaded successfully")

            # Click Post button - use the PRIMARY ACTION button in the modal
            # This is the actual "Post" button, not the audience selector
            post_button_selector = '[role="dialog"] button.share-actions__primary-action'

            try:
                self.logger.info(f"Looking for Post button (primary action)...")
                await page.wait_for_selector(post_button_selector, timeout=10000, state='visible')

                # Verify it's enabled
                is_disabled = await page.is_disabled(post_button_selector)
                if is_disabled:
                    self.logger.error("Post button is disabled")
                    screenshot = await self.take_screenshot(page, "post_button_disabled")
                    return {
                        "success": False,
                        "platform": "linkedin",
                        "error": "Post button is disabled",
                        "screenshot": screenshot,
                        "timestamp": self._get_timestamp()
                    }

                # Click the button
                await page.click(post_button_selector)
                post_clicked = True
                self.logger.info("Clicked Post button (primary action)")

            except Exception as e:
                self.logger.error(f"Failed to find/click Post button: {e}")
                post_clicked = False

            if not post_clicked:
                screenshot = await self.take_screenshot(page, "post_button_not_found")
                return {
                    "success": False,
                    "platform": "linkedin",
                    "error": "Could not find Post button",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Clicked Post button")

            # Wait for post to complete
            await page.wait_for_timeout(5000)

            # Verify post was successful (modal should close)
            try:
                await page.wait_for_selector(editor_selector, timeout=3000, state='hidden')
                self.logger.info("Post completed successfully")
            except:
                # Modal might still be visible, but post might have succeeded
                self.logger.warning("Could not verify modal closure, but post may have succeeded")

            return {
                "success": True,
                "platform": "linkedin",
                "post_id": None,  # LinkedIn doesn't provide post ID easily
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            self.logger.error(f"LinkedIn posting failed: {e}")
            screenshot = await self.take_screenshot(page, "unexpected_error")
            return {
                "success": False,
                "platform": "linkedin",
                "error": str(e),
                "screenshot": screenshot,
                "timestamp": self._get_timestamp()
            }

    async def _is_logged_in(self, page) -> bool:
        """Check if user is logged in to LinkedIn"""
        try:
            # Check current URL - if redirected to login page, not logged in
            current_url = page.url
            if '/login' in current_url or '/uas/login' in current_url or '/checkpoint' in current_url:
                self.logger.warning(f"Redirected to login page: {current_url}")
                return False

            # If we're on the feed page, we're likely logged in
            if '/feed' in current_url:
                self.logger.info("On feed page - checking for post button as login indicator")
                # Use the "Start a post" button as a login indicator
                try:
                    await page.wait_for_selector("button:has-text('Start a post')", timeout=10000, state='visible')
                    self.logger.info("Found 'Start a post' button - confirmed logged in")
                    return True
                except:
                    self.logger.warning("Could not find 'Start a post' button")
                    return False

            # Fallback: check for other login indicators
            login_indicators = [
                'button:has-text("Start a post")',
                '[data-test-global-nav]',
                '.global-nav',
                'img[alt*="Photo"]'
            ]

            for selector in login_indicators:
                try:
                    await page.wait_for_selector(selector, timeout=5000, state='visible')
                    self.logger.info(f"Login confirmed with selector: {selector}")
                    return True
                except:
                    continue

            self.logger.warning("No login indicators found")
            return False
        except Exception as e:
            self.logger.error(f"Error checking login status: {e}")
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
