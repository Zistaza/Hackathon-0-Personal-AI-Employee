#!/usr/bin/env python3
"""
Trigger Post - Social Media Post Draft Generator
================================================

Creates draft posts for social media platforms with HITL workflow.
Always saves to /Pending_Approval - requires human approval before posting.

Usage:
    python trigger_post.py --platform linkedin --content "Your post here"
    python trigger_post.py --platform facebook --content "Post" --media /path/to/image.jpg
    python trigger_post.py --platform instagram --content "Caption" --media /path/to/photo.jpg
    python trigger_post.py --platform twitter --content "Tweet (max 280 chars)"

Supported Platforms:
    - linkedin
    - facebook
    - instagram (requires --media)
    - twitter (280 character limit)
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


def generate_post_file(platform: str, content: str, media: list = None,
                       base_dir: Path = None) -> str:
    """
    Generate markdown post file with YAML frontmatter

    Args:
        platform: Social media platform
        content: Post content
        media: List of media file paths
        base_dir: Base directory (defaults to current directory parent)

    Returns:
        Path to created file
    """
    if base_dir is None:
        base_dir = Path(__file__).parent

    # Validate platform
    valid_platforms = ['linkedin', 'facebook', 'instagram', 'twitter']
    if platform not in valid_platforms:
        raise ValueError(f"Invalid platform. Must be one of: {', '.join(valid_platforms)}")

    # Validate Instagram requires media
    if platform == 'instagram' and (not media or len(media) == 0):
        raise ValueError("Instagram posts require at least one media file (--media)")

    # Validate Twitter character limit
    if platform == 'twitter' and len(content) > 280:
        raise ValueError(f"Twitter posts must be 280 characters or less (current: {len(content)})")

    # Validate media files exist
    if media:
        for media_path in media:
            if not Path(media_path).exists():
                raise ValueError(f"Media file not found: {media_path}")

    # Generate filename
    timestamp = int(datetime.utcnow().timestamp())
    filename = f"POST_{platform}_{timestamp}.md"

    # Create pending approval directory
    pending_dir = base_dir / "Pending_Approval"
    pending_dir.mkdir(parents=True, exist_ok=True)

    filepath = pending_dir / filename

    # Generate YAML frontmatter
    frontmatter = {
        'platform': platform,
        'type': 'post',
        'content': content,
        'media': media or [],
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'author': 'trigger_post_cli',
        'status': 'pending_approval'
    }

    # Generate markdown content
    import yaml
    yaml_content = yaml.dump(frontmatter, default_flow_style=False, allow_unicode=True)

    markdown_content = f"""---
{yaml_content.strip()}
---

# {platform.title()} Post Draft

**Created:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

## Content Preview

{content}

{'## Media' if media else ''}
{chr(10).join(f'- {m}' for m in media) if media else ''}

---

**Next Steps:**
1. Review this draft
2. Edit if needed
3. Move to /Approved folder to post
4. Or delete to cancel
"""

    # Write file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown_content)

    return str(filepath)


def publish_event(event_bus, platform: str, filename: str):
    """Publish draft creation event"""
    if event_bus:
        event_bus.publish('post.draft.created', {
            'platform': platform,
            'filename': filename,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })


def log_audit(audit_logger, platform: str, filename: str, content_length: int):
    """Log to audit trail"""
    if audit_logger:
        audit_logger.log_event(
            event_type='post_draft_created',
            actor='trigger_post_cli',
            action='create_draft',
            resource=platform,
            result='success',
            metadata={
                'filename': filename,
                'content_length': content_length
            }
        )


def main():
    parser = argparse.ArgumentParser(
        description='Create social media post drafts for HITL approval workflow',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python trigger_post.py --platform linkedin --content "Excited to share my new project!"
  python trigger_post.py --platform facebook --content "Check this out" --media photo.jpg
  python trigger_post.py --platform instagram --content "Beautiful sunset" --media sunset.jpg
  python trigger_post.py --platform twitter --content "Quick update for everyone"

Note: All posts require human approval before posting.
      Files are saved to /Pending_Approval folder.
        """
    )

    parser.add_argument('--platform', required=True,
                       choices=['linkedin', 'facebook', 'instagram', 'twitter'],
                       help='Social media platform')
    parser.add_argument('--content', required=True,
                       help='Post content/text')
    parser.add_argument('--media', action='append',
                       help='Media file path (can be used multiple times)')

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
                logger = logging.getLogger("trigger_post")
                logger.setLevel(logging.INFO)

                event_bus = EventBus(logger)
                logs_dir = base_dir / "Logs"
                logs_dir.mkdir(parents=True, exist_ok=True)
                audit_logger = AuditLogger(logs_dir, logger)
            except Exception as e:
                print(f"Warning: Could not initialize Gold Tier components: {e}")

        # Generate post file
        print(f"\n📝 Creating {args.platform} post draft...")
        print(f"   Content: {args.content[:50]}{'...' if len(args.content) > 50 else ''}")
        if args.media:
            print(f"   Media: {len(args.media)} file(s)")

        filepath = generate_post_file(
            platform=args.platform,
            content=args.content,
            media=args.media,
            base_dir=base_dir
        )

        filename = Path(filepath).name

        # Publish event
        publish_event(event_bus, args.platform, filename)

        # Log to audit
        log_audit(audit_logger, args.platform, filename, len(args.content))

        # Success message
        print(f"\n✅ Draft created successfully!")
        print(f"   File: {filepath}")
        print(f"\n📋 Next steps:")
        print(f"   1. Review: cat Pending_Approval/{filename}")
        print(f"   2. Approve: mv Pending_Approval/{filename} Approved/")
        print(f"   3. Execute: python3 Skills/social_media_executor/executor.py")
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
