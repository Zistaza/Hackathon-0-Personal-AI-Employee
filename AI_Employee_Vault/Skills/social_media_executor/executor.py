#!/usr/bin/env python3
"""
Social Media Executor v2
========================

Unified social media posting executor with HITL workflow and persistent sessions.

Features:
- Cross-platform posting (LinkedIn, Facebook, Instagram, Twitter)
- Persistent browser sessions
- Retry logic with exponential backoff
- Integration with Gold Tier infrastructure
- HITL workflow support
"""

import sys
import json
import asyncio
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page
except ImportError:
    print("Error: playwright not installed")
    print("Install with: pip install playwright && playwright install chromium")
    sys.exit(1)

# Import platform handlers (support both relative and absolute imports)
try:
    from .platforms import (
        LinkedInPlatform,
        FacebookPlatform,
        InstagramPlatform,
        TwitterPlatform
    )
except ImportError:
    from platforms import (
        LinkedInPlatform,
        FacebookPlatform,
        InstagramPlatform,
        TwitterPlatform
    )


class SocialMediaExecutorV2:
    """Unified social media posting executor"""

    def __init__(self, base_dir: Path, event_bus=None, audit_logger=None,
                 folder_manager=None, logger=None):
        """
        Initialize Social Media Executor

        Args:
            base_dir: Base directory of the vault
            event_bus: EventBus instance for publishing events
            audit_logger: AuditLogger instance for logging
            folder_manager: FolderManager instance for file operations
            logger: Logger instance
        """
        self.base_dir = base_dir
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        self.folder_manager = folder_manager
        self.logger = logger or self._setup_logger()

        # Load configuration
        self.config_file = Path(__file__).parent / "config.json"
        self.config = self._load_config()

        # Directories
        self.sessions_dir = base_dir / "Sessions"
        self.logs_dir = base_dir / "Logs"
        self.approved_dir = base_dir / "Approved"

        # Platform handlers
        self.platforms = {}
        self._initialize_platforms()

        # Playwright instances
        self.playwright = None
        self.contexts = {}  # Platform-specific persistent contexts

        self.logger.info("SocialMediaExecutorV2 initialized")

    def _setup_logger(self) -> logging.Logger:
        """Setup default logger"""
        logger = logging.getLogger("social_media_executor")
        logger.setLevel(logging.INFO)

        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s'
        ))
        logger.addHandler(handler)

        return logger

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        try:
            with open(self.config_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            self.logger.error(f"Failed to load config: {e}")
            return {}

    def _initialize_platforms(self):
        """Initialize platform handlers"""
        platform_configs = self.config.get('platforms', {})

        for platform_name, platform_config in platform_configs.items():
            if not platform_config.get('enabled', True):
                continue

            session_dir = self.sessions_dir / platform_config.get('session_dir', platform_name)

            # Map platform names to handler classes
            platform_classes = {
                'linkedin': LinkedInPlatform,
                'facebook': FacebookPlatform,
                'instagram': InstagramPlatform,
                'twitter': TwitterPlatform
            }

            handler_class = platform_classes.get(platform_name)
            if handler_class:
                self.platforms[platform_name] = handler_class(
                    config=platform_config,
                    session_dir=session_dir,
                    logs_dir=self.logs_dir,
                    logger=self.logger
                )
                self.logger.info(f"Initialized {platform_name} platform handler")

    async def initialize_browser(self):
        """Initialize Playwright (browser contexts created per-platform)"""
        try:
            self.playwright = await async_playwright().start()
            self.logger.info("Playwright initialized")

        except Exception as e:
            self.logger.error(f"Failed to initialize Playwright: {e}")
            raise

    async def get_context(self, platform: str) -> Optional[BrowserContext]:
        """
        Get or create persistent browser context for platform

        Args:
            platform: Platform name

        Returns:
            BrowserContext instance or None
        """
        try:
            if platform in self.contexts:
                return self.contexts[platform]

            platform_handler = self.platforms.get(platform)
            if not platform_handler:
                self.logger.error(f"Unknown platform: {platform}")
                return None

            # Create persistent context
            browser_config = self.config.get('browser', {})

            context = await self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(platform_handler.session_dir),
                headless=browser_config.get('headless', False),
                viewport=browser_config.get('viewport', {'width': 1280, 'height': 720}),
                user_agent=browser_config.get('user_agent')
            )

            self.contexts[platform] = context
            self.logger.info(f"Created persistent context for {platform}")

            return context

        except Exception as e:
            self.logger.error(f"Failed to create context for {platform}: {e}")
            return None

    async def close_browser(self):
        """Close browser contexts and Playwright"""
        try:
            # Close all contexts
            for platform, context in self.contexts.items():
                await context.close()
                self.logger.info(f"Closed context for {platform}")

            self.contexts.clear()

            # Stop playwright
            if self.playwright:
                await self.playwright.stop()

            self.logger.info("Browser contexts closed")

        except Exception as e:
            self.logger.error(f"Error closing browser: {e}")

    def parse_post_file(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """
        Parse markdown file with YAML frontmatter

        Args:
            file_path: Path to markdown file

        Returns:
            Parsed post data or None
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split frontmatter and content
            if not content.startswith('---'):
                self.logger.error(f"Invalid file format: {file_path.name}")
                return None

            parts = content.split('---', 2)
            if len(parts) < 3:
                self.logger.error(f"Invalid frontmatter: {file_path.name}")
                return None

            # Parse YAML frontmatter
            import yaml
            frontmatter = yaml.safe_load(parts[1])

            # Get content (strip leading/trailing whitespace)
            post_content = parts[2].strip()

            return {
                'platform': frontmatter.get('platform', '').lower(),
                'type': frontmatter.get('type', 'post'),
                'content': frontmatter.get('content', post_content),
                'media': frontmatter.get('media', []),
                'scheduled': frontmatter.get('scheduled', False),
                'metadata': frontmatter
            }

        except Exception as e:
            self.logger.error(f"Failed to parse file {file_path.name}: {e}")
            return None

    async def execute_post(self, post_data: Dict[str, Any], file_path: Path) -> Dict[str, Any]:
        """
        Execute a social media post with retry logic

        Args:
            post_data: Parsed post data
            file_path: Path to original file

        Returns:
            Execution result
        """
        platform = post_data.get('platform')
        content = post_data.get('content')
        media = post_data.get('media', [])

        # Validate platform
        if platform not in self.platforms:
            return {
                'success': False,
                'platform': platform,
                'error': f'Unsupported platform: {platform}',
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            }

        # Initialize browser if not already initialized
        if not self.playwright:
            try:
                await self.initialize_browser()
            except Exception as e:
                return {
                    'success': False,
                    'platform': platform,
                    'error': f'Failed to initialize browser: {str(e)}',
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                }

        # Publish start event
        if self.event_bus:
            self.event_bus.publish('social.post.started', {
                'platform': platform,
                'file': file_path.name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Get retry configuration
        retry_config = self.config.get('retry', {})
        max_attempts = retry_config.get('max_attempts', 3)
        initial_delay = retry_config.get('initial_delay', 5000) / 1000  # Convert to seconds
        backoff_multiplier = retry_config.get('backoff_multiplier', 2)

        # Retry loop
        last_error = None
        for attempt in range(1, max_attempts + 1):
            try:
                self.logger.info(f"Attempt {attempt}/{max_attempts} for {platform} post")

                # Get browser context
                context = await self.get_context(platform)
                if not context:
                    raise Exception(f"Failed to create browser context for {platform}")

                # Get or create page
                pages = context.pages
                page = pages[0] if pages else await context.new_page()

                # Execute platform-specific posting
                platform_handler = self.platforms[platform]
                result = await platform_handler.post(page, content, media)

                if result.get('success'):
                    self.logger.info(f"Post successful on {platform}")

                    # Publish success event
                    if self.event_bus:
                        self.event_bus.publish('social.post.completed', {
                            'platform': platform,
                            'file': file_path.name,
                            'success': True,
                            'timestamp': datetime.utcnow().isoformat() + 'Z'
                        })

                    # Log to audit
                    if self.audit_logger:
                        self.audit_logger.log_event(
                            event_type='social_post',
                            actor='social_media_executor',
                            action='post',
                            resource=platform,
                            result='success',
                            metadata={'file': file_path.name}
                        )

                    return result

                else:
                    last_error = result.get('error', 'Unknown error')
                    self.logger.warning(f"Attempt {attempt} failed: {last_error}")

                    if attempt < max_attempts:
                        # Calculate backoff delay
                        delay = initial_delay * (backoff_multiplier ** (attempt - 1))
                        self.logger.info(f"Retrying in {delay} seconds...")
                        await asyncio.sleep(delay)

            except Exception as e:
                last_error = str(e)
                self.logger.error(f"Attempt {attempt} error: {e}")

                if attempt < max_attempts:
                    delay = initial_delay * (backoff_multiplier ** (attempt - 1))
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)

        # All attempts failed
        self.logger.error(f"All {max_attempts} attempts failed for {platform} post")

        # Publish failure event
        if self.event_bus:
            self.event_bus.publish('social.post.failed', {
                'platform': platform,
                'file': file_path.name,
                'error': last_error,
                'attempts': max_attempts,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Log to audit
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type='social_post',
                actor='social_media_executor',
                action='post',
                resource=platform,
                result='failure',
                metadata={
                    'file': file_path.name,
                    'error': last_error,
                    'attempts': max_attempts
                }
            )

        return {
            'success': False,
            'platform': platform,
            'error': last_error,
            'attempts': max_attempts,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    async def process_approved_posts(self) -> Dict[str, Any]:
        """
        Process all approved posts from /Approved folder

        Returns:
            Summary of processing results
        """
        try:
            await self.initialize_browser()

            # Get approved files
            if self.folder_manager:
                approved_files = self.folder_manager.list_approved()
            else:
                approved_files = list(self.approved_dir.glob('POST_*.md'))

            self.logger.info(f"Found {len(approved_files)} approved post(s)")

            results = {
                'total': len(approved_files),
                'successful': 0,
                'failed': 0,
                'details': []
            }

            for file_path in approved_files:
                self.logger.info(f"Processing: {file_path.name}")

                # Parse post file
                post_data = self.parse_post_file(file_path)
                if not post_data:
                    self.logger.error(f"Failed to parse: {file_path.name}")
                    results['failed'] += 1
                    continue

                # Execute post
                result = await self.execute_post(post_data, file_path)

                # Move file based on result
                if result.get('success'):
                    if self.folder_manager:
                        self.folder_manager.move_to_done(file_path.name)
                    results['successful'] += 1
                else:
                    if self.folder_manager:
                        error_msg = result.get('error', 'Unknown error')
                        self.folder_manager.move_to_failed(file_path.name, error_msg)
                    results['failed'] += 1

                results['details'].append({
                    'file': file_path.name,
                    'platform': post_data.get('platform'),
                    'success': result.get('success'),
                    'error': result.get('error')
                })

            await self.close_browser()

            self.logger.info(f"Processing complete: {results['successful']} successful, {results['failed']} failed")

            return results

        except Exception as e:
            self.logger.error(f"Error processing approved posts: {e}")
            await self.close_browser()
            raise


async def main():
    """Main entry point for standalone execution"""
    # Determine base directory
    base_dir = Path(__file__).parent.parent.parent

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='[%(asctime)s] [%(levelname)s] %(message)s'
    )
    logger = logging.getLogger("social_media_executor")

    # Initialize FolderManager for file operations
    folder_manager = None
    try:
        sys.path.insert(0, str(base_dir))
        from Skills.integration_orchestrator.core.folder_manager import FolderManager
        folder_manager = FolderManager(base_dir, logger)
        logger.info("FolderManager initialized")
    except Exception as e:
        logger.warning(f"Could not initialize FolderManager: {e}")
        logger.warning("Files will not be moved automatically")

    # Initialize executor
    executor = SocialMediaExecutorV2(
        base_dir=base_dir,
        folder_manager=folder_manager,
        logger=logger
    )

    # Process approved posts
    results = await executor.process_approved_posts()

    # Print summary
    print("\n" + "=" * 60)
    print("SOCIAL MEDIA EXECUTOR - RESULTS")
    print("=" * 60)
    print(f"Total: {results['total']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
