#!/usr/bin/env python3
"""
Gold Tier Integration Test
Tests all Gold Tier components and features
"""

import sys
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Skills.integration_orchestrator.index import (
    IntegrationOrchestrator,
    EventBus,
    RetryQueue,
    HealthMonitor,
    AuditLogger,
    SkillRegistry,
    GracefulDegradation,
    ComponentStatus,
    RetryPolicy
)

def test_event_bus():
    """Test EventBus functionality"""
    print("\n=== Testing EventBus ===")

    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    event_bus = EventBus(logger)

    # Test subscription and publishing
    received_events = []

    def callback(data):
        received_events.append(data)

    event_bus.subscribe('test_event', callback)
    event_bus.publish('test_event', {'message': 'Hello'})

    time.sleep(0.1)  # Give time for event processing

    assert len(received_events) == 1, "Event not received"
    assert received_events[0]['message'] == 'Hello', "Event data incorrect"

    print("✓ EventBus: Subscription and publishing works")

    # Test unsubscribe
    event_bus.unsubscribe('test_event', callback)
    event_bus.publish('test_event', {'message': 'World'})

    time.sleep(0.1)

    assert len(received_events) == 1, "Event received after unsubscribe"

    print("✓ EventBus: Unsubscribe works")
    print("✓ EventBus: All tests passed")


def test_retry_queue():
    """Test RetryQueue functionality"""
    print("\n=== Testing RetryQueue ===")

    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    retry_queue = RetryQueue(logger, max_retries=3)
    retry_queue.start()

    # Test enqueue
    call_count = [0]

    def test_operation():
        call_count[0] += 1
        # Succeed on first try for testing
        return {'success': True}

    retry_queue.enqueue(
        operation=test_operation,
        policy=RetryPolicy.FIXED,
        context={'name': 'test_operation'}
    )

    print("✓ RetryQueue: Operation enqueued")

    # Wait for initial processing (queue checks every 5 seconds)
    time.sleep(6)

    assert call_count[0] >= 1, "Operation not executed"

    print(f"✓ RetryQueue: Operation executed {call_count[0]} time(s)")

    # Test queue size
    size = retry_queue.get_queue_size()
    print(f"✓ RetryQueue: Queue size = {size}")

    retry_queue.stop()
    print("✓ RetryQueue: All tests passed")


def test_health_monitor():
    """Test HealthMonitor functionality"""
    print("\n=== Testing HealthMonitor ===")

    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    health_monitor = HealthMonitor(logger, check_interval=2)

    # Register test component
    def check_test_component():
        return {
            'status': ComponentStatus.HEALTHY,
            'message': 'Test component operational'
        }

    health_monitor.register_component('test_component', check_test_component)
    print("✓ HealthMonitor: Component registered")

    health_monitor.start()
    print("✓ HealthMonitor: Started")

    # Wait for health check
    time.sleep(3)

    # Get system health
    health = health_monitor.get_system_health()
    assert 'test_component' in health['components'], "Component not found"
    assert health['components']['test_component']['status'] == ComponentStatus.HEALTHY

    print(f"✓ HealthMonitor: System health = {health['overall_status'].value}")

    # Get component status
    status = health_monitor.get_component_status('test_component')
    assert status is not None, "Component status not found"

    print(f"✓ HealthMonitor: Component status = {status['status'].value}")

    health_monitor.stop()
    print("✓ HealthMonitor: All tests passed")


def test_audit_logger():
    """Test AuditLogger functionality"""
    print("\n=== Testing AuditLogger ===")

    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    logs_dir = Path(__file__).parent / "test_logs"
    logs_dir.mkdir(exist_ok=True)

    audit_logger = AuditLogger(logs_dir, logger)

    # Log test event
    audit_logger.log_event(
        event_type='test_event',
        actor='test_user',
        action='test_action',
        resource='test_resource',
        result='success',
        metadata={'key': 'value'}
    )

    print("✓ AuditLogger: Event logged")

    # Query logs
    logs = audit_logger.query_logs(event_type='test_event', limit=10)
    assert len(logs) > 0, "No logs found"
    assert logs[0]['event_type'] == 'test_event'

    print(f"✓ AuditLogger: Found {len(logs)} log entries")

    # Test skill execution logging
    audit_logger.log_skill_execution(
        'test_skill',
        ['arg1', 'arg2'],
        {'success': True, 'returncode': 0},
        2.5
    )

    print("✓ AuditLogger: Skill execution logged")

    # Cleanup
    import shutil
    shutil.rmtree(logs_dir)

    print("✓ AuditLogger: All tests passed")


def test_graceful_degradation():
    """Test GracefulDegradation functionality"""
    print("\n=== Testing GracefulDegradation ===")

    import logging
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    health_monitor = HealthMonitor(logger, check_interval=2)

    # Register unhealthy component
    def check_unhealthy_component():
        return {
            'status': ComponentStatus.UNHEALTHY,
            'message': 'Component failed'
        }

    health_monitor.register_component('email_executor', check_unhealthy_component)

    degradation = GracefulDegradation(health_monitor, logger)

    # Check and degrade
    health_monitor.start()
    time.sleep(3)

    is_degraded = degradation.check_and_degrade()

    print(f"✓ GracefulDegradation: Degraded mode = {degradation.degraded_mode}")
    print(f"✓ GracefulDegradation: Disabled features = {degradation.disabled_features}")

    # Test feature check
    email_enabled = degradation.is_feature_enabled('email_sending')
    print(f"✓ GracefulDegradation: Email sending enabled = {email_enabled}")

    health_monitor.stop()
    print("✓ GracefulDegradation: All tests passed")


def test_orchestrator_integration():
    """Test full orchestrator integration"""
    print("\n=== Testing Orchestrator Integration ===")

    base_dir = Path(__file__).parent.parent.parent

    # Create orchestrator (don't start it)
    orchestrator = IntegrationOrchestrator(base_dir)

    print("✓ Orchestrator: Initialized")

    # Check Gold Tier components exist
    assert orchestrator.event_bus is not None, "EventBus not initialized"
    assert orchestrator.retry_queue is not None, "RetryQueue not initialized"
    assert orchestrator.health_monitor is not None, "HealthMonitor not initialized"
    assert orchestrator.audit_logger is not None, "AuditLogger not initialized"
    assert orchestrator.skill_registry is not None, "SkillRegistry not initialized"
    assert orchestrator.graceful_degradation is not None, "GracefulDegradation not initialized"

    print("✓ Orchestrator: All Gold Tier components initialized")

    # Test status method
    status = orchestrator.get_status()
    assert 'health' in status, "Health not in status"
    assert 'retry_queue_size' in status, "Retry queue size not in status"
    assert 'version' in status, "Version not in status"

    print(f"✓ Orchestrator: Status retrieved (version: {status['version']})")

    # Test health report
    report = orchestrator.get_health_report()
    assert 'ORCHESTRATOR HEALTH REPORT' in report, "Health report format incorrect"

    print("✓ Orchestrator: Health report generated")

    # Test state manager enhancements
    orchestrator.state_manager.set_system_state('test_key', 'test_value')
    value = orchestrator.state_manager.get_system_state('test_key')
    assert value == 'test_value', "State manager set/get failed"

    print("✓ Orchestrator: StateManager enhancements work")

    # Test metrics
    # Use unique counter name to avoid conflicts with previous test runs
    test_counter_name = f'test_counter_{int(time.time())}'
    orchestrator.state_manager.increment_counter(test_counter_name)
    metric = orchestrator.state_manager.get_metric(test_counter_name)
    assert metric is not None, "Counter not found"
    assert metric['value'] == 1, "Counter increment failed"

    print("✓ Orchestrator: Metrics tracking works")

    print("✓ Orchestrator: All integration tests passed")


def main():
    """Run all tests"""
    print("=" * 60)
    print("Gold Tier Integration Tests")
    print("=" * 60)

    try:
        test_event_bus()
        test_retry_queue()
        test_health_monitor()
        test_audit_logger()
        test_graceful_degradation()
        test_orchestrator_integration()

        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
        print("\nGold Tier upgrade is working correctly!")

        return 0

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
