#!/usr/bin/env python3
"""
Social CLI - Helper Utilities for HITL Workflow
================================================

Simple helper commands for managing the HITL approval workflow.

Commands:
    approve <file>  - Move file from Pending_Approval to Approved
    status          - Show system status and pending items
    list            - List all pending and approved items
    cancel <file>   - Delete a draft file

Usage:
    python social_cli.py approve POST_linkedin_123.md
    python social_cli.py status
    python social_cli.py list
    python social_cli.py cancel MESSAGE_gmail_456.md
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime
import shutil

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from Skills.integration_orchestrator.core import FolderManager, EventBus, AuditLogger
    GOLD_TIER_AVAILABLE = True
except ImportError:
    GOLD_TIER_AVAILABLE = False


def approve_file(filename: str, base_dir: Path):
    """Move file from Pending_Approval to Approved"""
    pending_file = base_dir / "Pending_Approval" / filename
    approved_file = base_dir / "Approved" / filename

    if not pending_file.exists():
        raise FileNotFoundError(f"File not found in Pending_Approval: {filename}")

    # Move file
    shutil.move(str(pending_file), str(approved_file))

    print(f"✅ Approved: {filename}")
    print(f"   Moved to: Approved/{filename}")
    print(f"\n📋 Next steps:")

    # Determine if it's a post or message
    if filename.startswith('POST_'):
        print(f"   Execute: python3 Skills/social_media_executor/executor.py")
    elif filename.startswith('MESSAGE_'):
        print(f"   Execute: python3 Skills/message_sender/sender.py")
    else:
        print(f"   Execute the appropriate executor")


def cancel_file(filename: str, base_dir: Path):
    """Delete a draft file"""
    pending_file = base_dir / "Pending_Approval" / filename

    if not pending_file.exists():
        raise FileNotFoundError(f"File not found in Pending_Approval: {filename}")

    # Confirm deletion
    print(f"⚠️  Are you sure you want to delete: {filename}?")
    response = input("   Type 'yes' to confirm: ")

    if response.lower() != 'yes':
        print("❌ Cancelled")
        return

    # Delete file
    pending_file.unlink()
    print(f"✅ Deleted: {filename}")


def show_status(base_dir: Path):
    """Show system status"""
    pending_dir = base_dir / "Pending_Approval"
    approved_dir = base_dir / "Approved"
    done_dir = base_dir / "Done"
    failed_dir = base_dir / "Failed"

    # Count files
    pending_posts = len(list(pending_dir.glob("POST_*.md"))) if pending_dir.exists() else 0
    pending_messages = len(list(pending_dir.glob("MESSAGE_*.md"))) if pending_dir.exists() else 0
    approved_posts = len(list(approved_dir.glob("POST_*.md"))) if approved_dir.exists() else 0
    approved_messages = len(list(approved_dir.glob("MESSAGE_*.md"))) if approved_dir.exists() else 0
    done_count = len(list(done_dir.glob("*.md"))) if done_dir.exists() else 0
    failed_count = len(list(failed_dir.glob("*.md"))) if failed_dir.exists() else 0

    print("\n" + "=" * 60)
    print("SOCIAL MEDIA AUTOMATION - STATUS")
    print("=" * 60)
    print(f"\n📋 Pending Approval:")
    print(f"   Posts: {pending_posts}")
    print(f"   Messages: {pending_messages}")
    print(f"   Total: {pending_posts + pending_messages}")

    print(f"\n✅ Approved (Ready to Execute):")
    print(f"   Posts: {approved_posts}")
    print(f"   Messages: {approved_messages}")
    print(f"   Total: {approved_posts + approved_messages}")

    print(f"\n📊 History:")
    print(f"   Completed: {done_count}")
    print(f"   Failed: {failed_count}")

    print("\n" + "=" * 60)

    # Show next actions
    if pending_posts + pending_messages > 0:
        print("\n💡 Next actions:")
        print("   Review pending items: python social_cli.py list")
        print("   Approve an item: python social_cli.py approve <filename>")

    if approved_posts + approved_messages > 0:
        print("\n⚡ Ready to execute:")
        if approved_posts > 0:
            print("   Posts: python3 Skills/social_media_executor/executor.py")
        if approved_messages > 0:
            print("   Messages: python3 Skills/message_sender/sender.py")


def list_items(base_dir: Path):
    """List all pending and approved items"""
    pending_dir = base_dir / "Pending_Approval"
    approved_dir = base_dir / "Approved"

    print("\n" + "=" * 60)
    print("PENDING APPROVAL")
    print("=" * 60)

    if pending_dir.exists():
        pending_files = sorted(pending_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)

        if pending_files:
            for file in pending_files:
                # Read first few lines to get platform info
                try:
                    with open(file, 'r') as f:
                        content = f.read(500)
                        if 'platform:' in content:
                            platform = content.split('platform:')[1].split('\n')[0].strip()
                        else:
                            platform = 'unknown'
                except:
                    platform = 'unknown'

                age = datetime.now().timestamp() - file.stat().st_mtime
                age_str = f"{int(age / 3600)}h ago" if age > 3600 else f"{int(age / 60)}m ago"

                print(f"  📄 {file.name}")
                print(f"     Platform: {platform} | Created: {age_str}")
        else:
            print("  (No pending items)")
    else:
        print("  (Pending_Approval folder not found)")

    print("\n" + "=" * 60)
    print("APPROVED (READY TO EXECUTE)")
    print("=" * 60)

    if approved_dir.exists():
        approved_files = sorted(approved_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)

        if approved_files:
            for file in approved_files:
                # Read first few lines to get platform info
                try:
                    with open(file, 'r') as f:
                        content = f.read(500)
                        if 'platform:' in content:
                            platform = content.split('platform:')[1].split('\n')[0].strip()
                        else:
                            platform = 'unknown'
                except:
                    platform = 'unknown'

                age = datetime.now().timestamp() - file.stat().st_mtime
                age_str = f"{int(age / 3600)}h ago" if age > 3600 else f"{int(age / 60)}m ago"

                print(f"  ✅ {file.name}")
                print(f"     Platform: {platform} | Approved: {age_str}")
        else:
            print("  (No approved items)")
    else:
        print("  (Approved folder not found)")

    print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description='Helper utilities for HITL workflow management',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  approve <file>   Move file from Pending_Approval to Approved
  status           Show system status and counts
  list             List all pending and approved items
  cancel <file>    Delete a draft file

Examples:
  python social_cli.py approve POST_linkedin_123456.md
  python social_cli.py status
  python social_cli.py list
  python social_cli.py cancel MESSAGE_gmail_789.md
        """
    )

    parser.add_argument('command',
                       choices=['approve', 'status', 'list', 'cancel'],
                       help='Command to execute')
    parser.add_argument('file', nargs='?',
                       help='Filename (required for approve/cancel)')

    args = parser.parse_args()

    try:
        base_dir = Path(__file__).parent

        if args.command == 'approve':
            if not args.file:
                print("❌ Error: filename required for approve command")
                print("   Usage: python social_cli.py approve <filename>")
                sys.exit(1)
            approve_file(args.file, base_dir)

        elif args.command == 'cancel':
            if not args.file:
                print("❌ Error: filename required for cancel command")
                print("   Usage: python social_cli.py cancel <filename>")
                sys.exit(1)
            cancel_file(args.file, base_dir)

        elif args.command == 'status':
            show_status(base_dir)

        elif args.command == 'list':
            list_items(base_dir)

    except FileNotFoundError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
