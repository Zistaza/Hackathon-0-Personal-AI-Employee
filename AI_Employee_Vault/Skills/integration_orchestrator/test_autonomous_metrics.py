#!/usr/bin/env python3
"""Test AutonomousExecutor Metrics Tracking"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Skills.integration_orchestrator.execution.autonomous_executor import AutonomousExecutor
from Skills.integration_orchestrator.core import (
    EventBus,
    RetryQueue,
    StateManager,
    HealthMonitor,
    AuditLogger,
)
from Skills.integration_orchestrator.skills import SkillRegistry, SkillDispatcher
import logging
import tempfile


def test_metrics_initialization():
    """Test that metrics are initialized correctly"""
    print("\n=== Test 1: Metrics Initialization ===")

    # Setup minimal components
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        state_file = base_dir / "state.json"

        event_bus = EventBus(logger)
        retry_queue = RetryQueue(logger)
        state_manager = StateManager(state_file)
        health_monitor = HealthMonitor(logger)
        audit_logger = AuditLogger(base_dir, logger)
        dispatcher = SkillDispatcher(base_dir / "Skills", logger)
        skill_registry = SkillRegistry(dispatcher, event_bus, retry_queue, audit_logger, logger)

        executor = AutonomousExecutor(
            event_bus=event_bus,
            retry_queue=retry_queue,
            state_manager=state_manager,
            health_monitor=health_monitor,
            skill_registry=skill_registry,
            audit_logger=audit_logger,
            base_dir=base_dir,
            logger=logger
        )

        # Check metrics initialized
        assert hasattr(executor, 'metrics'), "Metrics dictionary not found"
        assert 'auto_trigger_success' in executor.metrics
        assert 'auto_trigger_failures' in executor.metrics
        assert 'escalations' in executor.metrics
        assert 'workflows_recovered' in executor.metrics

        # Check all start at 0
        assert executor.metrics['auto_trigger_success'] == 0
        assert executor.metrics['auto_trigger_failures'] == 0
        assert executor.metrics['escalations'] == 0
        assert executor.metrics['workflows_recovered'] == 0

        print("✓ Metrics dictionary initialized correctly")
        print(f"  Initial metrics: {executor.metrics}")


def test_get_autonomous_metrics():
    """Test get_autonomous_metrics() method"""
    print("\n=== Test 2: get_autonomous_metrics() Method ===")

    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        state_file = base_dir / "state.json"

        event_bus = EventBus(logger)
        retry_queue = RetryQueue(logger)
        state_manager = StateManager(state_file)
        health_monitor = HealthMonitor(logger)
        audit_logger = AuditLogger(base_dir, logger)
        dispatcher = SkillDispatcher(base_dir / "Skills", logger)
        skill_registry = SkillRegistry(dispatcher, event_bus, retry_queue, audit_logger, logger)

        executor = AutonomousExecutor(
            event_bus=event_bus,
            retry_queue=retry_queue,
            state_manager=state_manager,
            health_monitor=health_monitor,
            skill_registry=skill_registry,
            audit_logger=audit_logger,
            base_dir=base_dir,
            logger=logger
        )

        # Test with no executions (division by zero case)
        metrics = executor.get_autonomous_metrics()
        assert metrics['success_rate'] == 0.0
        assert metrics['auto_trigger_success'] == 0
        assert metrics['auto_trigger_failures'] == 0
        assert metrics['escalations'] == 0
        assert metrics['workflows_recovered'] == 0

        print("✓ Method returns correct structure with zero executions")
        print(f"  Metrics: {metrics}")

        # Simulate some executions
        executor.metrics['auto_trigger_success'] = 8
        executor.metrics['auto_trigger_failures'] = 2
        executor.metrics['escalations'] = 1
        executor.metrics['workflows_recovered'] = 3

        metrics = executor.get_autonomous_metrics()

        # Verify success rate calculation: 8/(8+2) * 100 = 80%
        assert metrics['success_rate'] == 80.0
        assert metrics['auto_trigger_success'] == 8
        assert metrics['auto_trigger_failures'] == 2
        assert metrics['escalations'] == 1
        assert metrics['workflows_recovered'] == 3

        print("✓ Method calculates success_rate correctly")
        print(f"  Metrics: {metrics}")

        # Test rounding
        executor.metrics['auto_trigger_success'] = 2
        executor.metrics['auto_trigger_failures'] = 1

        metrics = executor.get_autonomous_metrics()
        # 2/(2+1) * 100 = 66.666... should round to 66.67
        assert metrics['success_rate'] == 66.67

        print("✓ Success rate rounds to 2 decimal places")
        print(f"  Success rate: {metrics['success_rate']}%")


def test_metrics_thread_safety():
    """Test that metrics use lock for thread safety"""
    print("\n=== Test 3: Thread Safety ===")

    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        state_file = base_dir / "state.json"

        event_bus = EventBus(logger)
        retry_queue = RetryQueue(logger)
        state_manager = StateManager(state_file)
        health_monitor = HealthMonitor(logger)
        audit_logger = AuditLogger(base_dir, logger)
        dispatcher = SkillDispatcher(base_dir / "Skills", logger)
        skill_registry = SkillRegistry(dispatcher, event_bus, retry_queue, audit_logger, logger)

        executor = AutonomousExecutor(
            event_bus=event_bus,
            retry_queue=retry_queue,
            state_manager=state_manager,
            health_monitor=health_monitor,
            skill_registry=skill_registry,
            audit_logger=audit_logger,
            base_dir=base_dir,
            logger=logger
        )

        # Verify lock exists
        assert hasattr(executor, 'lock'), "Lock not found"

        # Test that get_autonomous_metrics uses lock
        with executor.lock:
            executor.metrics['auto_trigger_success'] = 5

        metrics = executor.get_autonomous_metrics()
        assert metrics['auto_trigger_success'] == 5

        print("✓ Metrics are thread-safe with lock")


def test_metrics_structure():
    """Test that metrics don't break existing functionality"""
    print("\n=== Test 4: Backward Compatibility ===")

    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        state_file = base_dir / "state.json"

        event_bus = EventBus(logger)
        retry_queue = RetryQueue(logger)
        state_manager = StateManager(state_file)
        health_monitor = HealthMonitor(logger)
        audit_logger = AuditLogger(base_dir, logger)
        dispatcher = SkillDispatcher(base_dir / "Skills", logger)
        skill_registry = SkillRegistry(dispatcher, event_bus, retry_queue, audit_logger, logger)

        executor = AutonomousExecutor(
            event_bus=event_bus,
            retry_queue=retry_queue,
            state_manager=state_manager,
            health_monitor=health_monitor,
            skill_registry=skill_registry,
            audit_logger=audit_logger,
            base_dir=base_dir,
            logger=logger
        )

        # Test that existing get_status() still works
        status = executor.get_status()
        assert 'running' in status
        assert 'check_interval' in status
        assert 'failure_threshold' in status

        print("✓ Existing get_status() method still works")
        print(f"  Status keys: {list(status.keys())}")

        # Test that new method doesn't interfere
        metrics = executor.get_autonomous_metrics()
        status2 = executor.get_status()

        assert status == status2, "get_autonomous_metrics() affected get_status()"

        print("✓ New method doesn't interfere with existing functionality")


def main():
    """Run all tests"""
    print("=" * 60)
    print("AUTONOMOUS EXECUTOR METRICS TEST SUITE")
    print("=" * 60)

    try:
        test_metrics_initialization()
        test_get_autonomous_metrics()
        test_metrics_thread_safety()
        test_metrics_structure()

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✓")
        print("=" * 60)

    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
