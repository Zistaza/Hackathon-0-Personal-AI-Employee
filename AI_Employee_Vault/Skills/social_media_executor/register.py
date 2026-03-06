"""
Social Media Executor v2 - SkillRegistry Integration
====================================================

Registers the social media executor with the Gold Tier SkillRegistry.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def register_executor(skill_registry, event_bus, audit_logger, folder_manager, logger, base_dir):
    """
    Register social media executor with SkillRegistry

    Args:
        skill_registry: SkillRegistry instance
        event_bus: EventBus instance
        audit_logger: AuditLogger instance
        folder_manager: FolderManager instance
        logger: Logger instance
        base_dir: Base directory path

    Returns:
        SocialMediaExecutorV2 instance
    """
    try:
        from Skills.social_media_executor.executor import SocialMediaExecutorV2

        # Create executor instance
        executor = SocialMediaExecutorV2(
            base_dir=base_dir,
            event_bus=event_bus,
            audit_logger=audit_logger,
            folder_manager=folder_manager,
            logger=logger
        )

        # Register with SkillRegistry
        skill_registry.register_skill(
            skill_name='social_media_executor',
            metadata={
                'version': '2.0.0',
                'description': 'Unified social media posting executor with HITL workflow',
                'platforms': ['linkedin', 'facebook', 'instagram', 'twitter'],
                'type': 'automation',
                'tier': 'gold',
                'executor_instance': executor
            }
        )

        logger.info("Social Media Executor v2 registered with SkillRegistry")

        return executor

    except Exception as e:
        logger.error(f"Failed to register social media executor: {e}")
        return None


def execute_social_post(executor, file_path):
    """
    Execute a social media post (wrapper for synchronous calls)

    Args:
        executor: SocialMediaExecutorV2 instance
        file_path: Path to post file

    Returns:
        Execution result
    """
    import asyncio

    # Parse post file
    post_data = executor.parse_post_file(Path(file_path))
    if not post_data:
        return {
            'success': False,
            'error': 'Failed to parse post file'
        }

    # Execute post
    try:
        result = asyncio.run(executor.execute_post(post_data, Path(file_path)))
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
