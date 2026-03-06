"""
Facebook Platform Handler
==========================

Handles posting to Facebook with multi-step flow and persistent sessions.
"""

from typing import Dict, Any, List, Optional
from .base import BasePlatform


class FacebookPlatform(BasePlatform):
    """Facebook-specific posting logic"""

    def get_platform_url(self) -> str:
        """Get Facebook base URL"""
        return "https://www.facebook.com"

    async def post(self, page, content: str, media: List[str] = None) -> Dict[str, Any]:
        """
        Post content to Facebook

        Args:
            page: Playwright page object
            content: Post content
            media: Optional media files

        Returns:
            Result dictionary
        """
        try:
            self.logger.info("Starting Facebook post...")

            # Validate content
            validation = self.validate_content(content, media)
            if not validation["valid"]:
                return {
                    "success": False,
                    "platform": "facebook",
                    "error": validation["error"],
                    "timestamp": self._get_timestamp()
                }

            # Navigate to Facebook
            await page.goto(self.get_platform_url(), wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Check if logged in
            if not await self._is_logged_in(page):
                screenshot = await self.take_screenshot(page, "not_logged_in")
                return {
                    "success": False,
                    "platform": "facebook",
                    "error": "Not logged in to Facebook. Please authenticate first.",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Click "What's on your mind?" or "Create post" area
            selectors = self.config.get('selectors', {})
            create_post_selector = selectors.get('create_post', "[aria-label*='Create a post']")

            # Try multiple selectors for the create post button
            create_clicked = False
            for selector in [create_post_selector, "[role='button']:has-text('What')", "[placeholder*='mind']"]:
                try:
                    await page.wait_for_selector(selector, timeout=5000, state='visible')
                    await page.click(selector)
                    create_clicked = True
                    break
                except:
                    continue

            if not create_clicked:
                screenshot = await self.take_screenshot(page, "create_post_not_found")
                return {
                    "success": False,
                    "platform": "facebook",
                    "error": "Could not find 'Create post' button",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Clicked 'Create post' button")

            # Wait for editor modal to appear
            editor_selector = selectors.get('editor', "[role='textbox'][contenteditable='true']")
            await page.wait_for_selector(editor_selector, timeout=5000, state='visible')
            await page.wait_for_timeout(1500)

            # Type content using keyboard for reliability
            if not await self.type_content(page, editor_selector, content):
                screenshot = await self.take_screenshot(page, "content_typing_failed")
                return {
                    "success": False,
                    "platform": "facebook",
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
                        "platform": "facebook",
                        "error": "Failed to upload media",
                        "screenshot": screenshot,
                        "timestamp": self._get_timestamp()
                    }
                self.logger.info("Media uploaded successfully")
                await page.wait_for_timeout(2000)  # Wait for media processing

            # Handle multi-step flow: Check for "Next" button
            next_button_selector = selectors.get('next_button', "[aria-label*='Next']")
            try:
                next_button = await page.wait_for_selector(next_button_selector, timeout=3000, state='visible')
                if next_button:
                    await page.click(next_button_selector)
                    self.logger.info("Clicked 'Next' button")
                    await page.wait_for_timeout(2000)
            except:
                # No "Next" button found, proceed to Post
                self.logger.info("No 'Next' button found, proceeding to Post")

            # Click Post/Share button
            post_button_selector = selectors.get('post_button', "[aria-label*='Post']")

            # Try multiple possible selectors for the post button
            post_clicked = False
            for selector in [post_button_selector, "[aria-label*='Share']", "button:has-text('Post')"]:
                try:
                    await page.wait_for_selector(selector, timeout=3000, state='visible')
                    await page.click(selector)
                    post_clicked = True
                    break
                except:
                    continue

            if not post_clicked:
                screenshot = await self.take_screenshot(page, "post_button_not_found")
                return {
                    "success": False,
                    "platform": "facebook",
                    "error": "Could not find Post/Share button",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Clicked Post button")

            # Wait for post to complete
            await page.wait_for_timeout(5000)

            # Verify post was successful (modal should close)
            try:
                await page.wait_for_selector(editor_selector, timeout=5000, state='hidden')
                self.logger.info("Post completed successfully")
            except:
                # Modal might still be visible, but post might have succeeded
                self.logger.warning("Could not verify modal closure, but post may have succeeded")

            return {
                "success": True,
                "platform": "facebook",
                "post_id": None,  # Facebook doesn't provide post ID easily
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            self.logger.error(f"Facebook posting failed: {e}")
            screenshot = await self.take_screenshot(page, "unexpected_error")
            return {
                "success": False,
                "platform": "facebook",
                "error": str(e),
                "screenshot": screenshot,
                "timestamp": self._get_timestamp()
            }

    async def _is_logged_in(self, page) -> bool:
        """Check if user is logged in to Facebook"""
        try:
            # Check for navigation elements that indicate logged-in state
            await page.wait_for_selector('[role="navigation"], [aria-label*="Facebook"]', timeout=5000)
            return True
        except:
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
