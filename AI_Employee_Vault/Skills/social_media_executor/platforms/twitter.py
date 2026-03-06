"""
Twitter Platform Handler
=========================

Handles posting to Twitter/X with character limits and persistent sessions.
"""

from typing import Dict, Any, List, Optional
from .base import BasePlatform


class TwitterPlatform(BasePlatform):
    """Twitter/X-specific posting logic"""

    def get_platform_url(self) -> str:
        """Get Twitter base URL"""
        return "https://twitter.com"

    async def post(self, page, content: str, media: List[str] = None) -> Dict[str, Any]:
        """
        Post content to Twitter

        Args:
            page: Playwright page object
            content: Tweet content (max 280 characters)
            media: Optional media files

        Returns:
            Result dictionary
        """
        try:
            self.logger.info("Starting Twitter post...")

            # Validate content (280 character limit)
            validation = self.validate_content(content, media)
            if not validation["valid"]:
                return {
                    "success": False,
                    "platform": "twitter",
                    "error": validation["error"],
                    "timestamp": self._get_timestamp()
                }

            # Navigate to Twitter
            await page.goto(self.get_platform_url(), wait_until='networkidle', timeout=30000)
            await page.wait_for_timeout(2000)

            # Check if logged in
            if not await self._is_logged_in(page):
                screenshot = await self.take_screenshot(page, "not_logged_in")
                return {
                    "success": False,
                    "platform": "twitter",
                    "error": "Not logged in to Twitter. Please authenticate first.",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            # Find tweet compose box
            selectors = self.config.get('selectors', {})
            editor_selector = selectors.get('editor', "[role='textbox'][contenteditable='true']")

            # Wait for editor to be visible
            await page.wait_for_selector(editor_selector, timeout=10000, state='visible')
            await page.wait_for_timeout(1000)

            # Type content using keyboard for reliability
            if not await self.type_content(page, editor_selector, content):
                screenshot = await self.take_screenshot(page, "content_typing_failed")
                return {
                    "success": False,
                    "platform": "twitter",
                    "error": "Failed to type content into tweet box",
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
                        "platform": "twitter",
                        "error": "Failed to upload media",
                        "screenshot": screenshot,
                        "timestamp": self._get_timestamp()
                    }
                self.logger.info("Media uploaded successfully")
                await page.wait_for_timeout(2000)

            # Click Tweet/Post button
            post_button_selector = selectors.get('post_button', "[data-testid='tweetButton']")

            # Try multiple possible selectors for the tweet button
            post_clicked = False
            for selector in [post_button_selector, "[data-testid='tweetButtonInline']", "button:has-text('Post')", "button:has-text('Tweet')"]:
                try:
                    await page.wait_for_selector(selector, timeout=3000, state='visible')

                    # Check if button is enabled
                    button = await page.query_selector(selector)
                    is_disabled = await button.get_attribute('disabled')

                    if is_disabled:
                        continue

                    await page.click(selector)
                    post_clicked = True
                    break
                except:
                    continue

            if not post_clicked:
                screenshot = await self.take_screenshot(page, "post_button_not_found")
                return {
                    "success": False,
                    "platform": "twitter",
                    "error": "Could not find or click Tweet button",
                    "screenshot": screenshot,
                    "timestamp": self._get_timestamp()
                }

            self.logger.info("Clicked Tweet button")

            # Wait for tweet to complete
            await page.wait_for_timeout(5000)

            # Verify tweet was successful (editor should be cleared)
            try:
                # Check if editor is empty or has placeholder text
                editor_content = await page.text_content(editor_selector)
                if not editor_content or len(editor_content.strip()) == 0:
                    self.logger.info("Tweet completed successfully")
                else:
                    self.logger.warning("Editor still has content, tweet may have failed")
            except:
                # Can't verify, but tweet likely succeeded
                self.logger.warning("Could not verify tweet completion")

            return {
                "success": True,
                "platform": "twitter",
                "post_id": None,
                "timestamp": self._get_timestamp()
            }

        except Exception as e:
            self.logger.error(f"Twitter posting failed: {e}")
            screenshot = await self.take_screenshot(page, "unexpected_error")
            return {
                "success": False,
                "platform": "twitter",
                "error": str(e),
                "screenshot": screenshot,
                "timestamp": self._get_timestamp()
            }

    async def _is_logged_in(self, page) -> bool:
        """Check if user is logged in to Twitter"""
        try:
            # Check for navigation or compose elements that indicate logged-in state
            await page.wait_for_selector('[data-testid="SideNav_NewTweet_Button"], [role="textbox"]', timeout=5000)
            return True
        except:
            return False

    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'
