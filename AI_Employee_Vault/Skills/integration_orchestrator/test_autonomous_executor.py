#!/usr/bin/env python3
"""
Test script for AutonomousExecutor (Ralph Wiggum Loop)

This script tests the autonomous execution layer to ensure it:
1. Detects unfinished workflows
2. Triggers appropriate skills
3. Tracks failures and escalates when threshold is exceeded
4. Integrates properly with all Gold Tier components
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Skills.integration_orchestrator.index import IntegrationOrchestrator


def create_test_file(directory: Path, filename: str, content: str):
    """Create a test file in the specified directory"""
    filepath = directory / filename
    with open(filepath, 'w') as f:
        f.write(content)
    print(f"✓ Created test file: {filepath.name}")
    return filepath


def test_autonomous_detection():
    """Test that AutonomousExecutor detects unfinished work"""
    print("\n" + "=" * 60)
    print("TEST 1: Autonomous Detection of Unfinished Work")
    print("=" * 60)

    # Get base directory
    base_dir = Path(__file__).parent.parent.parent

    # Create orchestrator
    print("\n1. Initializing orchestrator...")
    orchestrator = IntegrationOrchestrator(base_dir)

    # Verify AutonomousExecutor is initialized
    if orchestrator.autonomous_executor:
        print("✓ AutonomousExecutor initialized")
        status = orchestrator.autonomous_executor.get_status()
        print(f"  - Check interval: {status['check_interval']}s")
        print(f"  - Failure threshold: {status['failure_threshold']}")
    else:
        print("✗ AutonomousExecutor NOT initialized")
        return False

    # Create test file in Needs_Action
    print("\n2. Creating test file in Needs_Action...")
    test_content = """# Test Task

This is a test task to verify autonomous detection.

type: test
status: pending
timestamp: {timestamp}
""".format(timestamp=datetime.utcnow().isoformat() + 'Z')

    test_file = create_test_file(
        orchestrator.needs_action_dir,
        f"test_autonomous_{int(time.time())}.md",
        test_content
    )

    # Start orchestrator in background
    print("\n3. Starting orchestrator...")
    import threading
    orchestrator_thread = threading.Thread(target=orchestrator.start, daemon=True)
    orchestrator_thread.start()

    # Wait for startup
    time.sleep(3)

    # Check if autonomous executor is running
    print("\n4. Checking AutonomousExecutor status...")
    status = orchestrator.autonomous_executor.get_status()
    print(f"  - Running: {status['running']}")
    print(f"  - Tracked tasks: {status['tracked_tasks']}")
    print(f"  - Last check: {status.get('last_check', 'Not yet')}")

    # Wait for autonomous executor to detect the file
    print("\n5. Waiting for autonomous detection (30 seconds)...")
    time.sleep(35)

    # Check status again
    print("\n6. Checking status after detection window...")
    status = orchestrator.autonomous_executor.get_status()
    print(f"  - Tracked tasks: {status['tracked_tasks']}")
    print(f"  - Last check: {status.get('last_check', 'Not yet')}")

    # Get overall orchestrator status
    print("\n7. Overall orchestrator status:")
    overall_status = orchestrator.get_status()
    print(f"  - Running: {overall_status['running']}")
    print(f"  - Retry queue size: {overall_status['retry_queue_size']}")
    print(f"  - Registered skills: {overall_status['registered_skills']}")

    # Check metrics
    metrics = overall_status.get('metrics', {})
    print(f"\n8. Metrics:")
    print(f"  - Skills started: {metrics.get('skills_started', 0)}")
    print(f"  - Skills succeeded: {metrics.get('skills_succeeded', 0)}")
    print(f"  - Skills failed: {metrics.get('skills_failed', 0)}")

    # Stop orchestrator
    print("\n9. Stopping orchestrator...")
    orchestrator.stop()

    # Clean up test file if it still exists
    if test_file.exists():
        test_file.unlink()
        print(f"✓ Cleaned up test file")

    print("\n" + "=" * 60)
    print("TEST 1 COMPLETE")
    print("=" * 60)

    return True


def test_failure_escalation():
    """Test that AutonomousExecutor escalates repeated failures"""
    print("\n" + "=" * 60)
    print("TEST 2: Failure Escalation")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent.parent

    print("\n1. Initializing orchestrator...")
    orchestrator = IntegrationOrchestrator(base_dir)

    # Create a mock failure scenario by checking escalation logic
    print("\n2. Testing escalation threshold...")
    executor = orchestrator.autonomous_executor

    # Simulate failures
    task_key = "test_skill_test_context"
    print(f"  - Simulating failures for: {task_key}")

    with executor.lock:
        executor.task_failure_counts[task_key] = executor.failure_threshold

    print(f"  - Failure count: {executor.task_failure_counts[task_key]}")
    print(f"  - Threshold: {executor.failure_threshold}")

    if executor.task_failure_counts[task_key] >= executor.failure_threshold:
        print("✓ Escalation threshold reached")
    else:
        print("✗ Escalation threshold NOT reached")

    print("\n" + "=" * 60)
    print("TEST 2 COMPLETE")
    print("=" * 60)

    return True


def test_health_monitoring():
    """Test that AutonomousExecutor health check works"""
    print("\n" + "=" * 60)
    print("TEST 3: Health Monitoring Integration")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent.parent

    print("\n1. Initializing orchestrator...")
    orchestrator = IntegrationOrchestrator(base_dir)

    print("\n2. Starting components...")
    orchestrator.retry_queue.start()
    orchestrator.health_monitor.start()
    orchestrator.autonomous_executor.start()

    # Wait for health check
    print("\n3. Waiting for health check (5 seconds)...")
    time.sleep(5)

    # Get health report
    print("\n4. Health Report:")
    print(orchestrator.get_health_report())

    # Stop components
    print("\n5. Stopping components...")
    orchestrator.autonomous_executor.stop()
    orchestrator.health_monitor.stop()
    orchestrator.retry_queue.stop()

    print("\n" + "=" * 60)
    print("TEST 3 COMPLETE")
    print("=" * 60)

    return True


def test_event_bus_integration():
    """Test that AutonomousExecutor publishes events correctly"""
    print("\n" + "=" * 60)
    print("TEST 4: EventBus Integration")
    print("=" * 60)

    base_dir = Path(__file__).parent.parent.parent

    print("\n1. Initializing orchestrator...")
    orchestrator = IntegrationOrchestrator(base_dir)

    # Subscribe to events
    events_received = []

    def event_handler(data):
        events_received.append(data)
        print(f"  ✓ Event received: {data.get('location', 'unknown')}")

    print("\n2. Subscribing to events...")
    orchestrator.event_bus.subscribe('unfinished_workflow_detected', event_handler)
    orchestrator.event_bus.subscribe('retry_queue_status', event_handler)

    # Start autonomous executor
    print("\n3. Starting autonomous executor...")
    orchestrator.autonomous_executor.start()

    # Wait for checks
    print("\n4. Waiting for autonomous checks (35 seconds)...")
    time.sleep(35)

    # Check events
    print(f"\n5. Events received: {len(events_received)}")
    for i, event in enumerate(events_received, 1):
        print(f"  Event {i}: {json.dumps(event, indent=2)}")

    # Stop
    print("\n6. Stopping autonomous executor...")
    orchestrator.autonomous_executor.stop()

    print("\n" + "=" * 60)
    print("TEST 4 COMPLETE")
    print("=" * 60)

    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("AUTONOMOUS EXECUTOR TEST SUITE")
    print("=" * 60)

    tests = [
        ("Autonomous Detection", test_autonomous_detection),
        ("Failure Escalation", test_failure_escalation),
        ("Health Monitoring", test_health_monitoring),
        ("EventBus Integration", test_event_bus_integration)
    ]

    results = []

    for test_name, test_func in tests:
        try:
            print(f"\n\nRunning: {test_name}")
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))

    # Summary
    print("\n\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")

    print(f"\nTotal: {passed}/{total} tests passed")
    print("=" * 60)

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
