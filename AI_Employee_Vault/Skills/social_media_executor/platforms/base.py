"""
Base Platform Handler
=====================

Abstract base class for social media platform posting logic.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime


class BasePlatform(ABC):
    """Abstract base class for platform-specific posting logic"""

    def __init__(self, config: Dict[str, Any], session_dir: Path, logs_dir: Path, logger):
        """
        Initialize platform handler

        Args:
            config: Platform-specific configuration
            session_dir: Directory for persistent browser session
            logs_dir: Directory for error screenshots
            logger: Logger instance
        """
        self.config = config
        self.session_dir = session_dir
        self.logs_dir = logs_dir
        self.logger = logger
        self.platform_name = self.__class__.__name__.replace('Platform', '').lower()

        # Ensure directories exist
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    @abstractmethod
    async def post(self, page, content: str, media: List[str] = None) -> Dict[str, Any]:
        """
        Post content to the platform

        Args:
            page: Playwright page object
            content: Post content/text
            media: List of media file paths (optional)

        Returns:
            Result dictionary with success status and details
        """
        pass

    @abstractmethod
    def get_platform_url(self) -> str:
        """Get the platform's base URL"""
        pass

    async def take_screenshot(self, page, error_context: str) -> Optional[str]:
        """
        Take screenshot on error

        Args:
            page: Playwright page object
            error_context: Context description for the screenshot

        Returns:
            Path to screenshot file or None
        """
        try:
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"{self.platform_name}_error_{error_context}_{timestamp}.png"
            screenshot_path = self.logs_dir / filename

            await page.screenshot(path=str(screenshot_path), full_page=True)
            self.logger.info(f"Screenshot saved: {screenshot_path}")

            return str(screenshot_path)

        except Exception as e:
            self.logger.error(f"Failed to take screenshot: {e}")
            return None

    async def wait_and_click(self, page, selector: str, timeout: int = 5000) -> bool:
        """
        Wait for element and click it

        Args:
            page: Playwright page object
            selector: CSS selector
            timeout: Timeout in milliseconds

        Returns:
            True if successful, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=timeout, state='visible')
            await page.click(selector)
            await page.wait_for_timeout(1000)  # Brief pause after click
            return True
        except Exception as e:
            self.logger.error(f"Failed to click {selector}: {e}")
            return False

    async def type_content(self, page, selector: str, content: str) -> bool:
        """
        Type content into an element using keyboard.type for reliability

        Args:
            page: Playwright page object
            selector: CSS selector
            content: Content to type

        Returns:
            True if successful, False otherwise
        """
        try:
            await page.wait_for_selector(selector, timeout=5000, state='visible')
            await page.click(selector)
            await page.wait_for_timeout(500)

            # Use keyboard.type for reliability
            await page.keyboard.type(content, delay=50)
            await page.wait_for_timeout(500)

            return True
        except Exception as e:
            self.logger.error(f"Failed to type content into {selector}: {e}")
            return False

    async def upload_media(self, page, selector: str, media_paths: List[str]) -> bool:
        """
        Upload media files

        Args:
            page: Playwright page object
            selector: File input selector
            media_paths: List of file paths to upload

        Returns:
            True if successful, False otherwise
        """
        try:
            if not media_paths:
                return True

            # Validate files exist
            for path in media_paths:
                if not Path(path).exists():
                    self.logger.error(f"Media file not found: {path}")
                    return False

            # Set files on input element
            await page.set_input_files(selector, media_paths)
            await page.wait_for_timeout(2000)  # Wait for upload processing

            self.logger.info(f"Uploaded {len(media_paths)} media file(s)")
            return True

        except Exception as e:
            self.logger.error(f"Failed to upload media: {e}")
            return False

    def validate_content(self, content: str, media: List[str] = None) -> Dict[str, Any]:
        """
        Validate content before posting

        Args:
            content: Post content
            media: Media files

        Returns:
            Validation result with success status and error message
        """
        # Check if content is empty
        if not content or not content.strip():
            return {
                "valid": False,
                "error": "Content cannot be empty"
            }

        # Check character limit if specified
        char_limit = self.config.get('char_limit')
        if char_limit and len(content) > char_limit:
            return {
                "valid": False,
                "error": f"Content exceeds {char_limit} character limit (current: {len(content)})"
            }

        # Check if media is required
        requires_media = self.config.get('requires_media', False)
        if requires_media and (not media or len(media) == 0):
            return {
                "valid": False,
                "error": f"{self.platform_name.title()} requires at least one media file"
            }

        return {"valid": True}
