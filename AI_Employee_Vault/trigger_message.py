#!/usr/bin/env python3
"""
Trigger Message - Email and WhatsApp Message Draft Generator
=============================================================

Creates draft messages for Gmail and WhatsApp with HITL workflow.
Always saves to /Pending_Approval - requires human approval before sending.

Usage:
    # Gmail
    python trigger_message.py --platform gmail --to "user@example.com" --subject "Meeting" --body "Let's meet tomorrow"
    python trigger_message.py --platform gmail --to "client@company.com" --subject "Proposal" --body "Attached is the proposal" --attach /path/to/file.pdf

    # WhatsApp
    python trigger_message.py --platform whatsapp --to "John Doe" --body "Hey, can we reschedule?"

Supported Platforms:
    - gmail (requires --subject)
    - whatsapp (--subject ignored)
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from Skills.integration_orchestrator.core import EventBus, AuditLogger
    GOLD_TIER_AVAILABLE = True
except ImportError:
    GOLD_TIER_AVAILABLE = False
    print("Warning: Gold Tier components not available. Running in standalone mode.")


def generate_message_file(platform: str, to: str, subject: str, body: str,
                          attachments: list = None, base_dir: Path = None) -> str:
    """
    Generate markdown message file with YAML frontmatter

    Args:
        platform: Messaging platform (gmail, whatsapp)
        to: Recipient (email address or contact name)
        subject: Message subject (for email)
        body: Message body/content
        attachments: List of attachment file paths (Gmail only)
        base_dir: Base directory (defaults to current directory parent)

    Returns:
        Path to created file
    """
    if base_dir is None:
        base_dir = Path(__file__).parent

    # Validate platform
    valid_platforms = ['gmail', 'whatsapp']
    if platform not in valid_platforms:
        raise ValueError(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")

    # Validate Gmail requires subject
    if platform == 'gmail' and not subject:
        raise ValueError("Gmail messages require a subject (--subject)")

    # Validate recipient
    if not to or not to.strip():
        raise ValueError("Recipient (--to) cannot be empty")

    # Validate body
    if not body or not body.strip():
        raise ValueError("Message body (--body) cannot be empty")

    # Validate attachments exist (Gmail only)
    if attachments:
        if platform == 'whatsapp':
            print("⚠️  Warning: WhatsApp does not support attachments yet. Attachments will be ignored.")
            attachments = []
        else:
            for attachment_path in attachments:
                if not Path(attachment_path).exists():
                    raise ValueError(f"Attachment file not found: {attachment_path}")

    # Generate filename
    timestamp = int(datetime.utcnow().timestamp())
    filename = f"MESSAGE_{platform}_{timestamp}.md"

    # Create pending approval directory
    pending_dir = base_dir / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    filepath = pending_dir / filename

    # Generate YAML frontmatter
    frontmatter = {
        'platform': platform,
        'type': 'message',
        'to': to,
        'subject': subject if platform == 'gmail' else '',
        'content': body,
        'attachments': attachments or [],
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'author': 'trigger_message_cli',
        'status': 'pending_approval'
    }

    # Generate markdown content
    import yaml
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

    markdown_content = f"""---
{yaml_content.strip()}
---

# {platform.title()} Message Draft

**Created:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Recipient
{to}

{f'## Subject{chr(10)}{subject}{chr(10)}' if subject else ''}
## Message

{body}

{'## Attachments' if attachments else ''}
{chr(10).join(f'- {a}' for a in attachments) if attachments else ''}

---

**Next Steps:**
1. Review this draft
2. Edit if needed
3. Move to /Approved folder to send
4. Or delete to cancel
"""

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return str(filepath)


def publish_event(event_bus, platform: str, to: str, filename: str):
    """Publish draft creation event"""
    if event_bus:
        event_bus.publish('message.draft.created', {
            'platform': platform,
            'to': to,
            'filename': filename,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })


def log_audit(audit_logger, platform: str, to: str, filename: str, body_length: int):
    """Log to audit trail"""
    if audit_logger:
        audit_logger.log_event(
            event_type='message_draft_created',
            actor='trigger_message_cli',
            action='create_draft',
            resource=platform,
            result='success',
            metadata={
                'filename': filename,
                'to': to,
                'body_length': body_length
            }
        )


def main():
    parser = argparse.ArgumentParser(
        description='Create email/WhatsApp message drafts for HITL approval workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Gmail
  python trigger_message.py --platform gmail --to "user@example.com" --subject "Meeting" --body "Let's meet at 2pm"
  python trigger_message.py --platform gmail --to "client@company.com" --subject "Proposal" --body "See attached" --attach proposal.pdf

  # WhatsApp
  python trigger_message.py --platform whatsapp --to "John Doe" --body "Hey, can we reschedule our call?"

Note: All messages require human approval before sending.
      Files are saved to /Pending_Approval folder.
        """
    )

    parser.add_argument('--platform', required=True,
                       choices=['gmail', 'whatsapp'],
                       help='Messaging platform')
    parser.add_argument('--to', required=True,
                       help='Recipient (email address or contact name)')
    parser.add_argument('--subject',
                       help='Message subject (required for Gmail)')
    parser.add_argument('--body', required=True,
                       help='Message body/content')
    parser.add_argument('--attach', action='append', dest='attachments',
                       help='Attachment file path (Gmail only, can be used multiple times)')

    args = parser.parse_args()

    try:
        # Determine base directory
        base_dir = Path(__file__).parent

        # Initialize Gold Tier components if available
        event_bus = None
        audit_logger = None

        if GOLD_TIER_AVAILABLE:
            try:
                import logging
                logger = logging.getLogger("trigger_message")
                logger.setLevel(logging.INFO)

                event_bus = EventBus(logger)
                logs_dir = base_dir / "Logs"
                logs_dir.mkdir(parents=True, exist_ok=True)
                audit_logger = AuditLogger(logs_dir, logger)
            except Exception as e:
                print(f"Warning: Could not initialize Gold Tier components: {e}")

        # Generate message file
        print(f"\n📧 Creating {args.platform} message draft...")
        print(f"   To: {args.to}")
        if args.subject:
            print(f"   Subject: {args.subject}")
        print(f"   Body: {args.body[:50]}{'...' if len(args.body) > 50 else ''}")
        if args.attachments:
            print(f"   Attachments: {len(args.attachments)} file(s)")

        filepath = generate_message_file(
            platform=args.platform,
            to=args.to,
            subject=args.subject or '',
            body=args.body,
            attachments=args.attachments,
            base_dir=base_dir
        )

        filename = Path(filepath).name

        # Publish event
        publish_event(event_bus, args.platform, args.to, filename)

        # Log to audit
        log_audit(audit_logger, args.platform, args.to, filename, len(args.body))

        # Success message
        print(f"\n✅ Draft created successfully!")
        print(f"   File: {filepath}")
        print(f"\n📋 Next steps:")
        print(f"   1. Review: cat Pending_Approval/{filename}")
        print(f"   2. Approve: mv Pending_Approval/{filename} Approved/")
        print(f"   3. Execute: python3 Skills/message_sender/sender.py")
        print(f"\n   Or delete the file to cancel.")

    except ValueError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
