#!/usr/bin/env python3
"""
Test Suite for Weekly CEO Briefing Skill

Tests all functionality including:
- Data aggregation from multiple sources
- Report generation
- Idempotency
- AI recommendations and risk warnings
- Gold Tier integration
"""

import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Skills.weekly_ceo_briefing.index import WeeklyCEOBriefing


class MockEventBus:
    """Mock EventBus for testing"""
    def __init__(self):
        self.events = []

    def publish(self, event_type, data):
        self.events.append({
            'type': event_type,
            'data': data
        })
        print(f"  [Event] {event_type}")

    def get_events(self, event_type=None):
        if event_type:
            return [e for e in self.events if e['type'] == event_type]
        return self.events


class MockAuditLogger:
    """Mock AuditLogger for testing"""
    def __init__(self):
        self.logs = []

    def log_event(self, event_type, actor, action, resource, result, metadata=None):
        self.logs.append({
            'event_type': event_type,
            'actor': actor,
            'action': action,
            'resource': resource,
            'result': result,
            'metadata': metadata or {}
        })
        print(f"  [Audit] {action} on {resource}: {result}")


class MockHealthMonitor:
    """Mock HealthMonitor for testing"""
    def get_system_health(self):
        from Skills.integration_orchestrator.index import ComponentStatus
        return {
            'overall_status': ComponentStatus.HEALTHY,
            'components': {
                'test_component': {
                    'status': ComponentStatus.HEALTHY,
                    'message': 'Test component operational'
                }
            }
        }


class MockRetryQueue:
    """Mock RetryQueue for testing"""
    def __init__(self, size=5):
        self.size = size

    def get_queue_size(self):
        return self.size


class MockOrchestrator:
    """Mock IntegrationOrchestrator for testing"""
    def __init__(self):
        self.health_monitor = MockHealthMonitor()
        self.retry_queue = MockRetryQueue()


def create_test_ledger(tmpdir: Path, transactions: list) -> Path:
    """Create test ledger file"""
    data_dir = tmpdir / "Data"
    data_dir.mkdir(parents=True, exist_ok=True)

    ledger_file = data_dir / "ledger.json"

    ledger = {
        'version': '1.0',
        'created_at': datetime.utcnow().isoformat() + 'Z',
        'transactions': transactions,
        'metadata': {
            'total_revenue': sum(t['amount'] for t in transactions if t['type'] == 'revenue'),
            'total_expenses': sum(t['amount'] for t in transactions if t['type'] == 'expense'),
            'transaction_count': len(transactions)
        }
    }

    with open(ledger_file, 'w') as f:
        json.dump(ledger, f, indent=2)

    return ledger_file


def create_test_audit_logs(tmpdir: Path, entries: list) -> Path:
    """Create test audit log file"""
    logs_dir = tmpdir / "Logs"
    logs_dir.mkdir(parents=True, exist_ok=True)

    audit_file = logs_dir / "audit.jsonl"

    with open(audit_file, 'w') as f:
        for entry in entries:
            f.write(json.dumps(entry) + '\n')

    return audit_file


def test_basic_report_generation():
    """Test basic report generation"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Report Generation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test data
        print("\n1. Creating test data...")

        # Create transactions for current week
        # Use a date that will definitely be in the generated week
        from datetime import timezone
        now = datetime.now(timezone.utc)

        # Get the week that will be generated
        briefing_temp = WeeklyCEOBriefing(base_dir)
        week_id = briefing_temp._get_week_identifier()
        week_start, week_end = briefing_temp._get_week_range(week_id)

        # Use middle of the week for transaction date
        txn_date = week_start + timedelta(days=3)

        transactions = [
            {
                'id': 'txn1',
                'type': 'revenue',
                'amount': 1000.0,
                'category': 'Consulting',
                'description': 'Project A',
                'date': txn_date.isoformat(),
                'status': 'finalized',
                'created_at': now.isoformat(),
                'metadata': {}
            },
            {
                'id': 'txn2',
                'type': 'expense',
                'amount': 500.0,
                'category': 'Software',
                'description': 'License',
                'date': txn_date.isoformat(),
                'status': 'finalized',
                'created_at': now.isoformat(),
                'metadata': {}
            }
        ]

        create_test_ledger(base_dir, transactions)
        print("   ✓ Test ledger created")

        # Create audit logs with timestamp in the same week
        audit_entries = [
            {
                'timestamp': txn_date.isoformat(),
                'event_type': 'skill_execution',
                'actor': 'system',
                'action': 'execute_skill',
                'resource': 'test_skill',
                'result': 'success',
                'metadata': {}
            }
        ]

        create_test_audit_logs(base_dir, audit_entries)
        print("   ✓ Test audit logs created")

        # Initialize briefing
        print("\n2. Initializing briefing generator...")
        briefing = WeeklyCEOBriefing(base_dir)
        briefing.set_orchestrator(MockOrchestrator())
        print("   ✓ Briefing generator initialized")

        # Generate briefing
        print("\n3. Generating briefing...")
        result = briefing.generate_briefing()

        # Verify results
        print("\n4. Verifying results...")
        assert result['accounting']['revenue'] == 1000.0
        assert result['accounting']['expenses'] == 500.0
        assert result['accounting']['net_profit'] == 500.0
        print("   ✓ Accounting data correct")

        assert result['audit']['total_events'] == 1
        print("   ✓ Audit data correct")

        assert result['report_file'] is not None
        print("   ✓ Report file generated")

    print("\n" + "=" * 60)
    print("TEST 1 PASSED")
    print("=" * 60)
    return True


def test_idempotency():
    """Test that duplicate reports are not created"""
    print("\n" + "=" * 60)
    print("TEST 2: Idempotency")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create minimal test data
        create_test_ledger(base_dir, [])
        create_test_audit_logs(base_dir, [])

        # Initialize briefing
        print("\n1. Initializing briefing generator...")
        briefing = WeeklyCEOBriefing(base_dir)
        briefing.set_orchestrator(MockOrchestrator())

        # Generate first briefing
        print("\n2. Generating first briefing...")
        result1 = briefing.generate_briefing()
        assert result1['report_file'] is not None
        print(f"   ✓ First briefing generated: {result1['report_file']}")

        # Try to generate again for same week
        print("\n3. Attempting to generate duplicate...")
        result2 = briefing.generate_briefing()

        # Verify second generation was skipped
        print("\n4. Verifying idempotency...")
        assert result2.get('status') == 'skipped'
        assert result2.get('reason') == 'already_exists'
        print("   ✓ Duplicate generation skipped (idempotent)")

    print("\n" + "=" * 60)
    print("TEST 2 PASSED")
    print("=" * 60)
    return True


def test_recommendations_generation():
    """Test AI recommendations generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Recommendations Generation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test data
        from datetime import timezone
        now = datetime.now(timezone.utc)

        # Get the week that will be generated
        briefing_temp = WeeklyCEOBriefing(base_dir)
        week_id = briefing_temp._get_week_identifier()
        week_start, week_end = briefing_temp._get_week_range(week_id)

        # Use middle of the week for transaction date
        txn_date = week_start + timedelta(days=3)

        # Negative profit scenario
        transactions = [
            {
                'id': 'txn1',
                'type': 'revenue',
                'amount': 100.0,
                'category': 'Consulting',
                'description': 'Small project',
                'date': txn_date.isoformat(),
                'status': 'finalized',
                'created_at': now.isoformat(),
                'metadata': {}
            },
            {
                'id': 'txn2',
                'type': 'expense',
                'amount': 500.0,
                'category': 'Software',
                'description': 'Expensive license',
                'date': txn_date.isoformat(),
                'status': 'finalized',
                'created_at': now.isoformat(),
                'metadata': {}
            }
        ]

        create_test_ledger(base_dir, transactions)
        create_test_audit_logs(base_dir, [])
        print("   ✓ Test data created (negative profit)")

        # Create escalation files
        needs_action_dir = base_dir / "Needs_Action"
        needs_action_dir.mkdir(parents=True, exist_ok=True)

        escalation_file = needs_action_dir / "ESCALATION_test.md"
        escalation_file.write_text("Test escalation")
        print("   ✓ Escalation file created")

        # Initialize briefing
        print("\n2. Generating briefing...")
        briefing = WeeklyCEOBriefing(base_dir)
        briefing.set_orchestrator(MockOrchestrator())

        result = briefing.generate_briefing()

        # Verify recommendations were generated
        print("\n3. Verifying recommendations...")
        assert len(result['recommendations']) > 0
        print(f"   ✓ {len(result['recommendations'])} recommendations generated")

        # Check for specific recommendations
        rec_text = ' '.join(result['recommendations'])
        assert 'Negative profit' in rec_text or 'escalation' in rec_text
        print("   ✓ Relevant recommendations included")

    print("\n" + "=" * 60)
    print("TEST 3 PASSED")
    print("=" * 60)
    return True


def test_risk_warnings():
    """Test risk warnings generation"""
    print("\n" + "=" * 60)
    print("TEST 4: Risk Warnings")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create data that should trigger warnings
        print("\n1. Creating test data with critical issues...")

        from datetime import timezone
        now = datetime.now(timezone.utc)

        # Get the week that will be generated
        briefing_temp = WeeklyCEOBriefing(base_dir)
        week_id = briefing_temp._get_week_identifier()
        week_start, week_end = briefing_temp._get_week_range(week_id)

        # Use middle of the week for transaction date
        txn_date = week_start + timedelta(days=3)

        # Large negative profit
        transactions = [
            {
                'id': 'txn1',
                'type': 'expense',
                'amount': 5000.0,
                'category': 'Software',
                'description': 'Major expense',
                'date': txn_date.isoformat(),
                'status': 'finalized',
                'created_at': now.isoformat(),
                'metadata': {}
            }
        ]

        create_test_ledger(base_dir, transactions)
        create_test_audit_logs(base_dir, [])
        print("   ✓ Test data created (large negative profit)")

        # Initialize briefing with high retry queue
        print("\n2. Generating briefing...")
        briefing = WeeklyCEOBriefing(base_dir)

        mock_orchestrator = MockOrchestrator()
        mock_orchestrator.retry_queue = MockRetryQueue(size=60)  # Critical level
        briefing.set_orchestrator(mock_orchestrator)

        result = briefing.generate_briefing()

        # Verify warnings were generated
        print("\n3. Verifying risk warnings...")
        assert len(result['warnings']) > 0
        print(f"   ✓ {len(result['warnings'])} warnings generated")

        # Check for critical warnings
        warnings_text = ' '.join(result['warnings'])
        assert 'CRITICAL' in warnings_text
        print("   ✓ Critical warnings included")

    print("\n" + "=" * 60)
    print("TEST 4 PASSED")
    print("=" * 60)
    return True


def test_gold_tier_integration():
    """Test Gold Tier integration"""
    print("\n" + "=" * 60)
    print("TEST 5: Gold Tier Integration")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create minimal test data
        create_test_ledger(base_dir, [])
        create_test_audit_logs(base_dir, [])

        # Setup mock Gold Tier components
        print("\n1. Setting up mock Gold Tier components...")
        event_bus = MockEventBus()
        audit_logger = MockAuditLogger()

        briefing = WeeklyCEOBriefing(base_dir)
        briefing.set_event_bus(event_bus)
        briefing.set_audit_logger(audit_logger)
        briefing.set_orchestrator(MockOrchestrator())
        print("   ✓ Mock components configured")

        # Generate briefing
        print("\n2. Generating briefing with Gold Tier integration...")
        result = briefing.generate_briefing()

        # Verify event emitted
        print("\n3. Verifying event emission...")
        events = event_bus.get_events('ceo_briefing_generated')
        assert len(events) == 1
        assert events[0]['data']['week_id'] == result['week_id']
        print("   ✓ Event emitted: ceo_briefing_generated")

        # Verify audit log
        print("\n4. Verifying audit logging...")
        logs = [l for l in audit_logger.logs if l['event_type'] == 'ceo_briefing']
        assert len(logs) == 1
        assert logs[0]['result'] == 'success'
        print("   ✓ Audit log created")

    print("\n" + "=" * 60)
    print("TEST 5 PASSED")
    print("=" * 60)
    return True


def test_dry_run_mode():
    """Test DRY_RUN mode"""
    print("\n" + "=" * 60)
    print("TEST 6: DRY_RUN Mode")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test data
        create_test_ledger(base_dir, [])
        create_test_audit_logs(base_dir, [])

        # Initialize with dry_run=True
        print("\n1. Initializing with DRY_RUN mode...")
        briefing = WeeklyCEOBriefing(base_dir, dry_run=True)
        briefing.set_orchestrator(MockOrchestrator())
        print("   ✓ DRY_RUN mode enabled")

        # Generate briefing
        print("\n2. Generating briefing in DRY_RUN mode...")
        result = briefing.generate_briefing()

        # Verify no file created
        print("\n3. Verifying no files written...")
        assert result['report_file'] is None
        print("   ✓ Report file not created (DRY_RUN)")

        # Verify reports directory doesn't exist or is empty
        reports_dir = base_dir / "Reports" / "Weekly"
        if reports_dir.exists():
            report_files = list(reports_dir.glob("*.md"))
            assert len(report_files) == 0
            print("   ✓ No report files in directory")

    print("\n" + "=" * 60)
    print("TEST 6 PASSED")
    print("=" * 60)
    return True


def test_markdown_generation():
    """Test markdown report generation"""
    print("\n" + "=" * 60)
    print("TEST 7: Markdown Generation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Create test data
        from datetime import timezone
        now = datetime.now(timezone.utc)

        # Get the week that will be generated
        briefing_temp = WeeklyCEOBriefing(base_dir)
        week_id = briefing_temp._get_week_identifier()
        week_start, week_end = briefing_temp._get_week_range(week_id)

        # Use middle of the week for transaction date
        txn_date = week_start + timedelta(days=3)

        transactions = [
            {
                'id': 'txn1',
                'type': 'revenue',
                'amount': 1000.0,
                'category': 'Consulting',
                'description': 'Project A',
                'date': txn_date.isoformat(),
                'status': 'finalized',
                'created_at': now.isoformat(),
                'metadata': {}
            }
        ]

        create_test_ledger(base_dir, transactions)
        create_test_audit_logs(base_dir, [])

        # Generate briefing
        print("\n1. Generating briefing...")
        briefing = WeeklyCEOBriefing(base_dir)
        briefing.set_orchestrator(MockOrchestrator())

        result = briefing.generate_briefing()

        # Read generated markdown
        print("\n2. Reading generated markdown...")
        report_file = base_dir / "Reports" / "Weekly" / result['report_file']
        assert report_file.exists()

        with open(report_file, 'r') as f:
            markdown = f.read()

        # Verify markdown structure
        print("\n3. Verifying markdown structure...")
        assert '# Weekly CEO Briefing' in markdown
        assert '## Executive Summary' in markdown
        assert '## 1. Financial Performance' in markdown
        assert '## 2. Operational Metrics' in markdown
        assert '## 3. Workflow Status' in markdown
        assert '## 4. System Health' in markdown
        assert '## 5. Recommendations' in markdown
        print("   ✓ All sections present")

        # Verify data in markdown
        assert '$1,000.00' in markdown  # Revenue
        print("   ✓ Financial data included")

    print("\n" + "=" * 60)
    print("TEST 7 PASSED")
    print("=" * 60)
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("WEEKLY CEO BRIEFING TEST SUITE")
    print("=" * 60)

    tests = [
        ("Basic Report Generation", test_basic_report_generation),
        ("Idempotency", test_idempotency),
        ("Recommendations Generation", test_recommendations_generation),
        ("Risk Warnings", test_risk_warnings),
        ("Gold Tier Integration", test_gold_tier_integration),
        ("DRY_RUN Mode", test_dry_run_mode),
        ("Markdown Generation", test_markdown_generation)
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
