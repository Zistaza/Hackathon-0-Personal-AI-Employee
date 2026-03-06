"""
Message Sender v2 - SkillRegistry Integration
==============================================

Registers the message sender with the Gold Tier SkillRegistry.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


def register_sender(skill_registry, event_bus, audit_logger, folder_manager, logger, base_dir):
    """
    Register message sender with SkillRegistry

    Args:
        skill_registry: SkillRegistry instance
        event_bus: EventBus instance
        audit_logger: AuditLogger instance
        folder_manager: FolderManager instance
        logger: Logger instance
        base_dir: Base directory path

    Returns:
        MessageSenderV2 instance
    """
    try:
        from Skills.message_sender.sender import MessageSenderV2

        # Create sender instance
        sender = MessageSenderV2(
            base_dir=base_dir,
            event_bus=event_bus,
            audit_logger=audit_logger,
            folder_manager=folder_manager,
            logger=logger
        )

        # Register with SkillRegistry
        skill_registry.register_skill(
            skill_name='message_sender',
            metadata={
                'version': '2.0.0',
                'description': 'Unified message sending for Gmail and WhatsApp with HITL workflow',
                'platforms': ['gmail', 'whatsapp'],
                'type': 'automation',
                'tier': 'gold',
                'sender_instance': sender
            }
        )

        logger.info("Message Sender v2 registered with SkillRegistry")

        return sender

    except Exception as e:
        logger.error(f"Failed to register message sender: {e}")
        return None


def send_message(sender, file_path):
    """
    Send a message (wrapper for synchronous calls)

    Args:
        sender: MessageSenderV2 instance
        file_path: Path to message file

    Returns:
        Execution result
    """
    import asyncio

    # Parse message file
    message_data = sender.parse_message_file(Path(file_path))
    if not message_data:
        return {
            'success': False,
            'error': 'Failed to parse message file'
        }

    # Send message
    try:
        result = asyncio.run(sender.send_message(message_data, Path(file_path)))
        return result
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }
