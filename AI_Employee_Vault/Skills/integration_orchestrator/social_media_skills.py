#!/usr/bin/env python3
"""
Social Media Skills Module - Backward Compatibility Wrapper
============================================================

This module maintains backward compatibility after migrating skills to
separate folders.

MIGRATION STATUS:
- ✅ FacebookSkill: Migrated to Skills/facebook_post_skill/
- ✅ InstagramSkill: Migrated to Skills/instagram_post_skill/
- ✅ TwitterXSkill: Migrated to Skills/twitter_post_skill/

ARCHITECTURE:
- All three skills imported from standalone skill folders
- SocialMCPAdapter coordinates all skills (stays here)
- All shared components in social_media_common.py

USAGE (unchanged):
    from social_media_skills import FacebookSkill, InstagramSkill, TwitterXSkill
    from social_media_skills import SocialMCPAdapter

All existing imports continue to work without modification.
"""

import sys
import logging
import hashlib
from pathlib import Path
from datetime import datetime, UTC
from typing import Dict, Any, Optional, List

# Import shared components from social_media_common
from social_media_common import (
    SocialPlatform,
    PostStatus,
    ModerationRisk,
    ContentValidator,
    ContentModerator,
    EngagementTracker,
    SocialAnalytics,
    BaseSocialSkill,
    MODERATION_THRESHOLD
)

# Import all skills from their standalone folders
sys.path.insert(0, str(Path(__file__).parent.parent))
from facebook_post_skill.index import FacebookSkill
from instagram_post_skill.index import InstagramSkill
from twitter_post_skill.index import TwitterXSkill

# All skills are now imported from their standalone folders
# No inline class definitions needed anymore


class SocialMCPAdapter:
    """
    MCP Adapter for social media skills - Enterprise Edition.

    Provides abstraction layer between social media skills and SocialMCPServer.
    Enables unified interface for posting across multiple platforms.

    Enterprise Features:
    - Post scheduling with state persistence
    - Analytics summary generation
    - Centralized engagement tracking
    """

    def __init__(self, logger: logging.Logger, event_bus=None, audit_logger=None,
                 retry_queue=None, reports_dir: Path = None, mcp_server=None,
                 state_manager=None):
        """
        Initialize Social MCP Adapter.

        Args:
            logger: Logger instance
            event_bus: EventBus for event emission
            audit_logger: AuditLogger for structured logging
            retry_queue: RetryQueue for retry logic
            reports_dir: Directory for report generation
            mcp_server: SocialMCPServer instance for MCP integration
            state_manager: StateManager for persistence
        """
        self.logger = logger
        self.event_bus = event_bus
        self.audit_logger = audit_logger
        self.retry_queue = retry_queue
        self.reports_dir = reports_dir or Path("Reports/Social")
        self.mcp_server = mcp_server
        self.state_manager = state_manager

        # Initialize skills with state_manager
        self.skills = {
            'facebook': FacebookSkill(logger, event_bus, audit_logger, retry_queue, reports_dir, state_manager),
            'instagram': InstagramSkill(logger, event_bus, audit_logger, retry_queue, reports_dir, state_manager),
            'twitter_x': TwitterXSkill(logger, event_bus, audit_logger, retry_queue, reports_dir, state_manager)
        }

        # Enterprise: Analytics
        self.analytics = SocialAnalytics(logger, state_manager)

        self.logger.info("SocialMCPAdapter initialized with 3 skills (Enterprise Mode)")

    def post(self, platform: str, message: str, media: Optional[List[str]] = None,
             metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Post to social media platform.

        Args:
            platform: Platform name ('facebook', 'instagram', 'twitter_x')
            message: Post message/content
            media: Optional list of media paths
            metadata: Optional metadata

        Returns:
            Result dictionary
        """
        skill = self.skills.get(platform.lower())
        if not skill:
            return {
                'success': False,
                'error': f"Unknown platform: {platform}. Available: {list(self.skills.keys())}"
            }

        # Add message and media to metadata for retry context
        metadata = metadata or {}
        metadata['message'] = message
        metadata['media'] = media

        # Execute skill
        result = skill.execute(message, media, metadata)

        # If MCP server is available, also execute via MCP
        if self.mcp_server and result['success']:
            try:
                self._sync_with_mcp(platform, message, media, result)
            except Exception as e:
                self.logger.warning(f"Failed to sync with MCP server: {e}")

        return result

    def schedule_post(self, platform: str, message: str, scheduled_time: datetime,
                     media: Optional[List[str]] = None, metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Schedule a post for future execution.

        Enterprise Feature: Integrates with PeriodicTrigger for execution.
        Stores scheduled posts in state.json.

        Args:
            platform: Platform name
            message: Post content
            scheduled_time: When to post
            media: Optional media
            metadata: Optional metadata

        Returns:
            Scheduling result
        """
        if not self.state_manager:
            return {
                'success': False,
                'error': 'StateManager not available for scheduling'
            }

        # Generate schedule ID
        schedule_id = hashlib.sha256(
            f"{platform}_{message}_{scheduled_time.isoformat()}".encode()
        ).hexdigest()[:16]

        # Store in state
        scheduled_posts = self.state_manager.get_system_state('scheduled_posts', {})
        scheduled_posts[schedule_id] = {
            'platform': platform,
            'message': message,
            'media': media,
            'metadata': metadata or {},
            'scheduled_time': scheduled_time.isoformat(),
            'status': PostStatus.SCHEDULED.value,
            'created_at': datetime.now(UTC).isoformat()
        }

        self.state_manager.set_system_state('scheduled_posts', scheduled_posts)

        # Emit event
        if self.event_bus:
            self.event_bus.publish('social_post_scheduled', {
                'schedule_id': schedule_id,
                'platform': platform,
                'scheduled_time': scheduled_time.isoformat()
            })

        self.logger.info(f"Scheduled post {schedule_id} for {platform} at {scheduled_time}")

        return {
            'success': True,
            'schedule_id': schedule_id,
            'scheduled_time': scheduled_time.isoformat(),
            'platform': platform
        }

    def execute_scheduled_posts(self) -> Dict[str, Any]:
        """
        Execute scheduled posts that are due.

        Called by PeriodicTrigger to check and execute scheduled posts.

        Returns:
            Execution summary
        """
        if not self.state_manager:
            return {'error': 'StateManager not available'}

        scheduled_posts = self.state_manager.get_system_state('scheduled_posts', {})
        now = datetime.now(UTC)
        executed = []
        failed = []

        for schedule_id, post_data in list(scheduled_posts.items()):
            if post_data['status'] != PostStatus.SCHEDULED.value:
                continue

            scheduled_time = datetime.fromisoformat(post_data['scheduled_time'])

            # Ensure scheduled_time is timezone-aware for comparison
            if scheduled_time.tzinfo is None:
                scheduled_time = scheduled_time.replace(tzinfo=UTC)

            # Check if post is due
            if scheduled_time <= now:
                self.logger.info(f"Executing scheduled post {schedule_id}")

                # Execute the post
                result = self.post(
                    post_data['platform'],
                    post_data['message'],
                    post_data['media'],
                    post_data['metadata']
                )

                # Update status
                if result['success']:
                    post_data['status'] = PostStatus.POSTED.value
                    post_data['executed_at'] = datetime.now(UTC).isoformat()
                    post_data['post_id'] = result.get('post_id')
                    executed.append(schedule_id)

                    # Emit event
                    if self.event_bus:
                        self.event_bus.publish('scheduled_post_executed', {
                            'schedule_id': schedule_id,
                            'platform': post_data['platform'],
                            'post_id': result.get('post_id')
                        })
                else:
                    post_data['status'] = PostStatus.FAILED.value
                    post_data['error'] = result.get('error')
                    failed.append(schedule_id)

                scheduled_posts[schedule_id] = post_data

        # Save updated state
        self.state_manager.set_system_state('scheduled_posts', scheduled_posts)

        return {
            'executed': executed,
            'failed': failed,
            'total_checked': len(scheduled_posts),
            'checked_at': datetime.now(UTC).isoformat()
        }

    def get_analytics_summary(self) -> Dict[str, Any]:
        """
        Get social analytics summary.

        Enterprise Feature: Generates weekly analytics report.

        Returns:
            Analytics summary
        """
        return self.analytics.generate_weekly_summary()

    def _sync_with_mcp(self, platform: str, message: str, media: Optional[List[str]],
                      skill_result: Dict[str, Any]):
        """Sync skill execution with MCP server"""
        # Map platform to MCP action
        if platform == 'facebook' or platform == 'instagram':
            # Use generic post_linkedin action as placeholder
            # In real implementation, would have platform-specific actions
            self.mcp_server.execute_action('post_linkedin', {
                'content': message,
                'media_url': media[0] if media else None
            })

    def post_to_all(self, message: str, media: Optional[List[str]] = None,
                    metadata: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """
        Post to all platforms.

        Args:
            message: Post message/content
            media: Optional list of media paths
            metadata: Optional metadata

        Returns:
            Dictionary with results for each platform
        """
        results = {}

        for platform_name in self.skills.keys():
            # Adjust message for Twitter if needed
            platform_message = message
            if platform_name == 'twitter_x' and len(message) > 280:
                platform_message = message[:277] + "..."

            # Instagram requires media
            if platform_name == 'instagram' and not media:
                results[platform_name] = {
                    'success': False,
                    'error': 'Instagram requires media',
                    'skipped': True
                }
                continue

            result = self.post(platform_name, platform_message, media, metadata)
            results[platform_name] = result

        return results

    def get_skill(self, platform: str) -> Optional[BaseSocialSkill]:
        """Get skill for specific platform"""
        return self.skills.get(platform.lower())

    def list_platforms(self) -> List[str]:
        """List available platforms"""
        return list(self.skills.keys())


def register_social_skills(skill_registry, logger: logging.Logger,
                          event_bus=None, audit_logger=None, retry_queue=None,
                          reports_dir: Path = None, mcp_server=None, state_manager=None):
    """
    Register all social media skills with SkillRegistry - Enterprise Edition.

    Args:
        skill_registry: SkillRegistry instance
        logger: Logger instance
        event_bus: EventBus instance
        audit_logger: AuditLogger instance
        retry_queue: RetryQueue instance
        reports_dir: Reports directory path
        mcp_server: SocialMCPServer instance
        state_manager: StateManager instance (Enterprise)

    Returns:
        SocialMCPAdapter instance
    """
    # Create adapter with state_manager
    adapter = SocialMCPAdapter(logger, event_bus, audit_logger, retry_queue,
                              reports_dir, mcp_server, state_manager)

    # Register each skill
    for platform_name, skill in adapter.skills.items():
        skill_registry.register_skill(
            f"social_{platform_name}",
            metadata={
                'type': 'social_media',
                'platform': platform_name,
                'description': f'Post to {platform_name.title()}',
                'version': '2.0.0',  # Enterprise version
                'enterprise_features': [
                    'content_validation',
                    'content_moderation',
                    'engagement_tracking',
                    'post_scheduling',
                    'analytics'
                ]
            }
        )

    logger.info("Registered 3 social media skills with SkillRegistry (Enterprise Mode)")

    return adapter


# Re-export for backward compatibility
__all__ = [
    'FacebookSkill',
    'InstagramSkill',
    'TwitterXSkill',
    'SocialMCPAdapter',
    'register_social_skills',
    'SocialPlatform',
    'PostStatus',
    'ModerationRisk',
    'MODERATION_THRESHOLD'
]
