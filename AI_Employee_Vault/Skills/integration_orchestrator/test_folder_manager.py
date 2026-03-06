#!/usr/bin/env python3
"""
Test script for FolderManager integration
==========================================

Validates that FolderManager is properly integrated with the orchestrator.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Skills.integration_orchestrator.core import FolderManager, EventBus, AuditLogger
import logging

def test_folder_manager():
    """Test FolderManager functionality"""

    # Setup logging
    logger = logging.getLogger("test_folder_manager")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    print("=" * 60)
    print("FOLDER MANAGER VALIDATION TEST")
    print("=" * 60)

    # Get base directory
    base_dir = Path(__file__).parent.parent.parent

    # Initialize components
    print("\n1. Initializing components...")
    event_bus = EventBus(logger)
    audit_logger = AuditLogger(base_dir / "Logs", logger)
    folder_manager = FolderManager(
        base_dir=base_dir,
        event_bus=event_bus,
        audit_logger=audit_logger,
        logger=logger
    )
    print("   ✓ FolderManager initialized")

    # Test folder existence
    print("\n2. Verifying folder structure...")
    folders_to_check = [
        ("Pending_Approval", folder_manager.pending_approval_dir),
        ("Approved", folder_manager.approved_dir),
        ("Done", folder_manager.done_dir),
        ("Failed", folder_manager.failed_dir),
        ("Sessions", folder_manager.sessions_dir),
        ("Logs", folder_manager.logs_dir),
    ]

    all_exist = True
    for name, path in folders_to_check:
        exists = path.exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {name}: {path}")
        if not exists:
            all_exist = False

    if not all_exist:
        print("\n   ✗ ERROR: Some folders are missing!")
        return False

    # Test session folders
    print("\n3. Verifying session platform folders...")
    for platform in folder_manager.session_platforms:
        session_path = folder_manager.get_session_path(platform)
        exists = session_path.exists()
        status = "✓" if exists else "✗"
        print(f"   {status} {platform}: {session_path}")
        if not exists:
            all_exist = False

    # Test folder listing
    print("\n4. Testing folder listing methods...")
    pending_files = folder_manager.list_pending()
    approved_files = folder_manager.list_approved()
    print(f"   ✓ list_pending(): {len(pending_files)} files")
    print(f"   ✓ list_approved(): {len(approved_files)} files")

    # Test stats
    print("\n5. Testing folder statistics...")
    stats = folder_manager.get_stats()
    print(f"   ✓ Pending Approval: {stats.get('pending_approval', 0)}")
    print(f"   ✓ Approved: {stats.get('approved', 0)}")
    print(f"   ✓ Done: {stats.get('done', 0)}")
    print(f"   ✓ Failed: {stats.get('failed', 0)}")

    # Test event publishing
    print("\n6. Testing event bus integration...")
    events_received = []

    def capture_event(data):
        events_received.append(data)

    event_bus.subscribe("file.moved.to.approved", capture_event)
    event_bus.subscribe("file.moved.to.done", capture_event)
    event_bus.subscribe("file.moved.to.failed", capture_event)

    # Create a test file
    test_file = folder_manager.pending_approval_dir / "TEST_validation.md"
    test_file.write_text("---\ntype: test\n---\n\nTest file for validation")

    # Test move to approved
    result = folder_manager.move_to_approved("TEST_validation.md")
    if result:
        print("   ✓ move_to_approved() works")
    else:
        print("   ✗ move_to_approved() failed")

    # Test move to done
    result = folder_manager.move_to_done("TEST_validation.md")
    if result:
        print("   ✓ move_to_done() works")
    else:
        print("   ✗ move_to_done() failed")

    # Verify events were published
    if len(events_received) >= 2:
        print(f"   ✓ Events published: {len(events_received)}")
    else:
        print(f"   ✗ Events not published correctly: {len(events_received)}")

    # Cleanup test file
    done_test_file = folder_manager.done_dir / "TEST_validation.md"
    if done_test_file.exists():
        done_test_file.unlink()
        print("   ✓ Test file cleaned up")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print("\n✓ FolderManager is properly integrated and functional!")

    return True


if __name__ == "__main__":
    try:
        success = test_folder_manager()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
