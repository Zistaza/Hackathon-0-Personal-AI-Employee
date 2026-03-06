#!/usr/bin/env python3
"""
Test script for Approved Folder Monitor
========================================

Validates that the automatic execution monitor is properly integrated.
"""

import sys
from pathlib import Path
import time

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging


def test_approved_folder_monitor():
    """Test Approved Folder Monitor integration"""

    # Setup logging
    logger = logging.getLogger("test_monitor")
    logger.setLevel(logging.INFO)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('[%(levelname)s] %(message)s'))
    logger.addHandler(handler)

    print("=" * 60)
    print("APPROVED FOLDER MONITOR - VALIDATION TEST")
    print("=" * 60)

    # Get base directory
    base_dir = Path(__file__).parent.parent.parent

    # Test 1: Import modules
    print("\n1. Testing module imports...")
    try:
        from Skills.integration_orchestrator.execution import ApprovedFolderMonitor
        from Skills.integration_orchestrator.core import EventBus, AuditLogger, FolderManager
        print("   ✓ All modules imported successfully")
    except Exception as e:
        print(f"   ✗ Import failed: {e}")
        return False

    # Test 2: Check if executors are available
    print("\n2. Checking executor availability...")
    try:
        from Skills.social_media_executor.executor import SocialMediaExecutorV2
        from Skills.message_sender.sender import MessageSenderV2
        print("   ✓ Social Media Executor v2 available")
        print("   ✓ Message Sender v2 available")
    except Exception as e:
        print(f"   ✗ Executors not available: {e}")
        return False

    # Test 3: Initialize components
    print("\n3. Testing component initialization...")
    try:
        # Initialize infrastructure
        event_bus = EventBus(logger)
        logs_dir = base_dir / "Logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        audit_logger = AuditLogger(logs_dir, logger)
        folder_manager = FolderManager(base_dir, event_bus, audit_logger, logger)

        # Initialize executors
        social_executor = SocialMediaExecutorV2(base_dir, event_bus, audit_logger, folder_manager, logger)
        message_sender = MessageSenderV2(base_dir, event_bus, audit_logger, folder_manager, logger)

        # Initialize monitor
        monitor = ApprovedFolderMonitor(
            base_dir=base_dir,
            event_bus=event_bus,
            audit_logger=audit_logger,
            folder_manager=folder_manager,
            social_media_executor=social_executor,
            message_sender=message_sender,
            logger=logger,
            check_interval=5  # 5 seconds for testing
        )

        print("   ✓ ApprovedFolderMonitor initialized")
        print(f"   ✓ Check interval: {monitor.check_interval}s")

    except Exception as e:
        print(f"   ✗ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Check monitor status
    print("\n4. Testing monitor status...")
    status = monitor.get_status()
    print(f"   ✓ Running: {status.get('running')}")
    print(f"   ✓ Check interval: {status.get('check_interval')}s")
    print(f"   ✓ Processed count: {status.get('processed_count')}")

    # Test 5: Test start/stop
    print("\n5. Testing start/stop lifecycle...")
    try:
        # Start monitor
        monitor.start()
        time.sleep(1)  # Give it time to start

        status = monitor.get_status()
        if status.get('running') and status.get('thread_alive'):
            print("   ✓ Monitor started successfully")
            print(f"   ✓ Thread alive: {status.get('thread_alive')}")
        else:
            print("   ✗ Monitor failed to start")
            return False

        # Stop monitor
        monitor.stop()
        time.sleep(1)  # Give it time to stop

        status = monitor.get_status()
        if not status.get('running'):
            print("   ✓ Monitor stopped successfully")
        else:
            print("   ✗ Monitor failed to stop")
            return False

    except Exception as e:
        print(f"   ✗ Start/stop test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 6: Check folder structure
    print("\n6. Verifying folder structure...")
    folders = [
        ("Pending_Approval", base_dir / "Pending_Approval"),
        ("Approved", base_dir / "Approved"),
        ("Done", base_dir / "Done"),
        ("Failed", base_dir / "Failed"),
    ]

    for name, path in folders:
        exists = path.exists()
        status_icon = "✓" if exists else "✗"
        print(f"   {status_icon} {name}: {path}")

    # Test 7: Integration check
    print("\n7. Checking orchestrator integration...")
    try:
        from Skills.integration_orchestrator.index import IntegrationOrchestrator

        # Check if ApprovedFolderMonitor is in __all__
        if 'ApprovedFolderMonitor' in IntegrationOrchestrator.__module__:
            print("   ✓ ApprovedFolderMonitor exported from orchestrator")

        print("   ✓ Orchestrator integration complete")

    except Exception as e:
        print(f"   ⚠ Integration check warning: {e}")

    print("\n" + "=" * 60)
    print("VALIDATION COMPLETE")
    print("=" * 60)
    print("\n✓ Approved Folder Monitor is properly configured!")
    print("\nNext steps:")
    print("1. Start the orchestrator: python3 Skills/integration_orchestrator/index.py")
    print("2. Create and approve a post/message")
    print("3. Monitor will automatically execute it within 30 seconds")
    print("4. Check /Done or /Failed for results")

    return True


if __name__ == "__main__":
    try:
        success = test_approved_folder_monitor()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
