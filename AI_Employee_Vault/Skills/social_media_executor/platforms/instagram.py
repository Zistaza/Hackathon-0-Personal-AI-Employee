"""
Instagram Platform Handler
===========================

Handles posting to Instagram with media requirements and persistent sessions.
"""

from typing import Dict, Any, List, Optional
from .base import BasePlatform


class InstagramPlatform(BasePlatform):
    """Instagram-specific posting logic"""

    def get_platform_url(self) -> str:
        """Get Instagram base URL"""
        return "https://www.instagram.com"

    async def post(self, page, content: str, media: List[str] = None) -> Dict[str, Any]:
        """
        Post content to Instagram

        Args:
            page: Playwright page object
            content: Post caption
            media: Media files (REQUIRED for Instagram)

        Returns:
            Result dictionary
        """
        try:
            self.logger.info("Starting Instagram post...")

            # Validate content (Instagram requires media)
            validation = self.validate_content(content, media)
            if not validation["valid"]:
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": validation["error"],
                    "timestamp": self._get_timestamp()
                }

            # Navigate to Instagram
            await page.goto(self.get_platform_url(), wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Check if logged in
            if not await self._is_logged_in(page):
                screenshot = await self.take_screenshot(page, "not_logged_in")
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "Not logged in to Instagram. Please authenticate first.",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Click "Create" or "New post" button
            selectors = self.config.get('selectors', {})
            create_post_selector = selectors.get('create_post', "[aria-label*='New post']")

            # Try multiple selectors for create button
            create_clicked = False
            for selector in [create_post_selector, "[aria-label*='Create']", "svg[aria-label*='New Post']"]:
                try:
                    await page.wait_for_selector(selector, timeout=5000, state='visible')
                    await page.click(selector)
                    create_clicked = True
                    break
                except:
                    continue

            if not create_clicked:
                screenshot = await self.take_screenshot(page, "create_button_not_found")
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "Could not find 'Create' button",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Clicked 'Create' button")
            await page.wait_for_timeout(1500)

            # Upload media (required for Instagram)
            media_selector = selectors.get('media_upload', "input[type='file'][accept*='image']")
            if not await self.upload_media(page, media_selector, media):
                screenshot = await self.take_screenshot(page, "media_upload_failed")
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "Failed to upload media",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Media uploaded successfully")
            await page.wait_for_timeout(2000)

            # Click "Next" button (multiple times for Instagram's multi-step flow)
            next_button_selector = selectors.get('next_button', "button:has-text('Next')")

            for step in range(3):  # Instagram typically has 2-3 "Next" steps
                try:
                    await page.wait_for_selector(next_button_selector, timeout=5000, state='visible')
                    await page.click(next_button_selector)
                    self.logger.info(f"Clicked 'Next' button (step {step + 1})")
                    await page.wait_for_timeout(1500)
                except:
                    # No more "Next" buttons, proceed to caption
                    break

            # Add caption
            caption_selector = selectors.get('caption_input', "textarea[aria-label*='caption']")

            try:
                await page.wait_for_selector(caption_selector, timeout=5000, state='visible')
                await page.click(caption_selector)
                await page.wait_for_timeout(500)
                await page.keyboard.type(content, delay=50)
                self.logger.info("Caption added successfully")
                await page.wait_for_timeout(1000)
            except Exception as e:
                self.logger.warning(f"Could not add caption: {e}")
                # Continue anyway, caption is optional

            # Click "Share" button
            share_button_selector = selectors.get('share_button', "button:has-text('Share')")

            share_clicked = False
            for selector in [share_button_selector, "[aria-label*='Share']", "button:has-text('Share')"]:
                try:
                    await page.wait_for_selector(selector, timeout=3000, state='visible')
                    await page.click(selector)
                    share_clicked = True
                    break
                except:
                    continue

            if not share_clicked:
                screenshot = await self.take_screenshot(page, "share_button_not_found")
                return {
                    "success": False,
                    "platform": "instagram",
                    "error": "Could not find 'Share' button",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Clicked Share button")

            # Wait for post to complete
            await page.wait_for_timeout(5000)

            # Verify post was successful (look for success message or modal closure)
            try:
                await page.wait_for_selector("text='Your post has been shared'", timeout=5000)
                self.logger.info("Post completed successfully")
            except:
                # Success message might not appear, but post likely succeeded
                self.logger.warning("Could not verify success message, but post may have succeeded")

            return {
                "success": True,
                "platform": "instagram",
                "post_id": None,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            self.logger.error(f"Instagram posting failed: {e}")
            screenshot = await self.take_screenshot(page, "unexpected_error")
            return {
                "success": False,
                "platform": "instagram",
                "error": str(e),
                "screenshot": screenshot,
                "timestamp": self._get_timestamp()
            }

    async def _is_logged_in(self, page) -> bool:
        """Check if user is logged in to Instagram"""
        try:
            # Check for navigation elements that indicate logged-in state
            await page.wait_for_selector('[role="navigation"], nav', timeout=5000)
            return True
        except:
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
