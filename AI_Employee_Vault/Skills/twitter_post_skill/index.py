#!/usr/bin/env python3
"""
Twitter/X Post Skill - Enterprise Edition
==========================================

Standalone skill for posting to Twitter/X with enterprise features:
- Content validation (280 character limit)
- Content moderation with risk scoring
- Engagement tracking
- Idempotent execution
- Audit logging
- Report generation

This skill can be used independently or integrated with the orchestrator.
"""

import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List

# Add integration_orchestrator to path for shared components
SKILL_DIR = Path(__file__).parent
INTEGRATION_ORCHESTRATOR_DIR = SKILL_DIR.parent / "integration_orchestrator"
sys.path.insert(0, str(INTEGRATION_ORCHESTRATOR_DIR))

# Import shared components
from social_media_common import (
    BaseSocialSkill,
    SocialPlatform,
    PostStatus
)

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('twitter_post_skill')


class TwitterXSkill(BaseSocialSkill):
    """
    Twitter/X posting skill with simulated API integration - Enterprise Edition

    Features:
    - Character limit validation (280 characters)
    - Media limit validation (4 items max)
    - Simulated API posting with 97% success rate
    - Engagement metrics generation
    - Report generation
    """

    def __init__(self, logger: logging.Logger, event_bus=None, audit_logger=None,
                 retry_queue=None, reports_dir: Path = None, state_manager=None,
                 config: Dict[str, Any] = None):
        """
        Initialize Twitter/X skill.

        Args:
            logger: Logger instance
            event_bus: EventBus for event emission (optional)
            audit_logger: AuditLogger for structured logging (optional)
            retry_queue: RetryQueue for retry logic (optional)
            reports_dir: Directory for report generation (optional)
            state_manager: StateManager for persistence (optional)
            config: Configuration dictionary (optional)
        """
        # Load config
        self.config = config or self._load_config()

        # Set reports directory from config or default
        if reports_dir is None and self.config.get('reports', {}).get('directory'):
            reports_dir = Path(self.config['reports']['directory'])

        super().__init__(
            SocialPlatform.TWITTER_X,
            logger,
            event_bus,
            audit_logger,
            retry_queue,
            reports_dir,
            state_manager
        )

        self.success_rate = self.config.get('api', {}).get('success_rate', 0.97)
        logger.info(f"Twitter/X skill initialized with {self.success_rate*100}% success rate")

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from config.json"""
        config_path = SKILL_DIR / "config.json"
        try:
            if config_path.exists():
                with open(config_path, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load config.json: {e}")

        # Return default config
        return {
            'api': {'success_rate': 0.97},
            'validation': {'max_length': 280, 'max_media': 4},
            'reports': {'directory': 'Reports/Social/Twitter'}
        }

    def _validate_inputs(self, message: str, media: Optional[List[str]]) -> Dict[str, Any]:
        """
        Validate Twitter/X post inputs.

        Args:
            message: Tweet text
            media: Optional list of media paths

        Returns:
            Validation result with 'valid' boolean and optional 'error'
        """
        max_length = self.config.get('validation', {}).get('max_length', 280)
        max_media = self.config.get('validation', {}).get('max_media', 4)

        if not message or len(message.strip()) == 0:
            return {'valid': False, 'error': 'Tweet cannot be empty'}

        if len(message) > max_length:
            return {
                'valid': False,
                'error': f'Tweet exceeds character limit ({max_length})'
            }

        if media and len(media) > max_media:
            return {
                'valid': False,
                'error': f'Twitter allows maximum {max_media} media items per tweet'
            }

        return {'valid': True}

    def _simulate_post(self, message: str, media: Optional[List[str]],
                      metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate Twitter/X API posting.

        In production, this would make actual API calls to Twitter/X API v2.
        Currently simulates posting with configurable success rate.

        Args:
            message: Tweet text
            media: Optional list of media paths
            metadata: Additional metadata

        Returns:
            Post result with success status and details
        """
        import time
        import random

        start_time = time.time()

        # Simulate API call delay (realistic network latency)
        time.sleep(0.08)

        # Generate fake post ID
        post_id = f"tw_{hashlib.sha256(message.encode()).hexdigest()[:12]}_{int(datetime.now(UTC).timestamp())}"

        # Simulate success/failure based on configured success rate
        if random.random() < self.success_rate:
            execution_time = time.time() - start_time

            return {
                'success': True,
                'post_id': post_id,
                'url': f"https://x.com/user/status/{post_id}",
                'timestamp': datetime.now(UTC).isoformat(),
                'execution_time': f"{execution_time:.3f}s",
                'api_response_time': "0.067s",
                'media_count': len(media) if media else 0,
                'engagement': {
                    'likes': 0,
                    'retweets': 0,
                    'replies': 0,
                    'views': 0
                }
            }
        else:
            return {
                'success': False,
                'error': 'Twitter API service temporarily unavailable (simulated)'
            }


def execute(message: str, media: Optional[List[str]] = None,
           metadata: Dict[str, Any] = None,
           event_bus=None, audit_logger=None, retry_queue=None,
           state_manager=None) -> Dict[str, Any]:
    """
    Entry point for skill execution.

    This function can be called directly or by the orchestrator.

    Args:
        message: Tweet text
        media: Optional list of media paths or URLs
        metadata: Optional metadata for the post
        event_bus: EventBus instance (optional)
        audit_logger: AuditLogger instance (optional)
        retry_queue: RetryQueue instance (optional)
        state_manager: StateManager instance (optional)

    Returns:
        Result dictionary with success status and data
    """
    logger.info("Twitter/X skill execute() called")

    # Initialize skill
    skill = TwitterXSkill(
        logger=logger,
        event_bus=event_bus,
        audit_logger=audit_logger,
        retry_queue=retry_queue,
        state_manager=state_manager
    )

    # Execute posting
    result = skill.execute(message, media, metadata)

    return result


def main():
    """
    CLI entry point for testing the skill independently.

    Usage:
        python index.py "Your tweet here"
        python index.py "Tweet with media" --media path/to/image.jpg
        python index.py --test
    """
    import argparse

    parser = argparse.ArgumentParser(description='Twitter/X Post Skill')
    parser.add_argument('message', nargs='?', help='Tweet text (max 280 characters)')
    parser.add_argument('--media', nargs='+', help='Media file paths or URLs (max 4)')
    parser.add_argument('--test', action='store_true', help='Run in test mode')
    parser.add_argument('--dry-run', action='store_true', help='Dry run (no actual posting)')

    args = parser.parse_args()

    if args.test:
        print("Running Twitter/X skill in test mode...")
        test_message = "This is a test tweet from the Twitter/X skill! 🚀 #AI #Automation"
        result = execute(test_message, media=None, metadata={'test': True})
    elif not args.message:
        parser.error("message is required unless --test is specified")
    else:
        result = execute(args.message, media=args.media, metadata={'cli': True})

    # Print result
    print("\n" + "="*60)
    print("TWITTER/X POST RESULT")
    print("="*60)
    print(json.dumps(result, indent=2))
    print("="*60 + "\n")

    # Exit with appropriate code
    sys.exit(0 if result.get('success') else 1)


if __name__ == "__main__":
    main()
