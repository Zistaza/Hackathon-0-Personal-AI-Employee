#!/usr/bin/env python3
"""
Test Suite for Accounting Core Skill

Tests all functionality including:
- Transaction management (revenue/expense)
- Idempotency
- Report generation
- Multi-step workflows
- Gold Tier integration (events, audit logs)
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Skills.accounting_core.index import (
    AccountingCore, TransactionType, TransactionStatus
)


class MockEventBus:
    """Mock EventBus for testing"""
    def __init__(self):
        self.events = []

    def publish(self, event_type, data):
        self.events.append({
            'type': event_type,
            'data': data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
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
            'metadata': metadata or {},
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        print(f"  [Audit] {action} on {resource}: {result}")

    def get_logs(self, event_type=None):
        if event_type:
            return [l for l in self.logs if l['event_type'] == event_type]
        return self.logs


def test_basic_transactions():
    """Test basic revenue and expense transactions"""
    print("\n" + "=" * 60)
    print("TEST 1: Basic Transactions")
    print("=" * 60)

    # Create temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Initialize accounting
        accounting = AccountingCore(base_dir)

        # Add revenue
        print("\n1. Adding revenue transaction...")
        txn1 = accounting.add_revenue(
            amount=1000.0,
            category="Consulting",
            description="Project X - Phase 1"
        )
        assert txn1['type'] == 'revenue'
        assert txn1['amount'] == 1000.0
        print("✓ Revenue transaction added")

        # Add expense
        print("\n2. Adding expense transaction...")
        txn2 = accounting.add_expense(
            amount=500.0,
            category="Software",
            description="Adobe License"
        )
        assert txn2['type'] == 'expense'
        assert txn2['amount'] == 500.0
        print("✓ Expense transaction added")

        # Check summary
        print("\n3. Checking summary...")
        summary = accounting.get_summary()
        assert summary['total_revenue'] == 1000.0
        assert summary['total_expenses'] == 500.0
        assert summary['net_profit'] == 500.0
        assert summary['transaction_count'] == 2
        print(f"✓ Summary correct: Net profit ${summary['net_profit']:.2f}")

        # Verify ledger file exists
        print("\n4. Verifying ledger file...")
        assert accounting.ledger_file.exists()
        print(f"✓ Ledger file created: {accounting.ledger_file}")

    print("\n" + "=" * 60)
    print("TEST 1 PASSED")
    print("=" * 60)
    return True


def test_idempotency():
    """Test that duplicate transactions are not created"""
    print("\n" + "=" * 60)
    print("TEST 2: Idempotency")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        accounting = AccountingCore(base_dir)

        # Add transaction
        print("\n1. Adding transaction (first time)...")
        txn1 = accounting.add_revenue(
            amount=1000.0,
            category="Consulting",
            description="Project X",
            date="2026-02-28T12:00:00Z"
        )
        txn1_id = txn1['id']
        print(f"✓ Transaction added: {txn1_id}")

        # Add same transaction again
        print("\n2. Adding same transaction (second time)...")
        txn2 = accounting.add_revenue(
            amount=1000.0,
            category="Consulting",
            description="Project X",
            date="2026-02-28T12:00:00Z"
        )
        txn2_id = txn2['id']
        print(f"✓ Transaction returned: {txn2_id}")

        # Verify same ID
        print("\n3. Verifying idempotency...")
        assert txn1_id == txn2_id
        print("✓ Same transaction ID (idempotent)")

        # Verify only one transaction in ledger
        summary = accounting.get_summary()
        assert summary['transaction_count'] == 1
        print("✓ Only one transaction in ledger")

    print("\n" + "=" * 60)
    print("TEST 2 PASSED")
    print("=" * 60)
    return True


def test_report_generation():
    """Test P&L and cashflow report generation"""
    print("\n" + "=" * 60)
    print("TEST 3: Report Generation")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        accounting = AccountingCore(base_dir)

        # Add multiple transactions
        print("\n1. Adding test transactions...")
        accounting.add_revenue(2000, "Consulting", "Project A")
        accounting.add_revenue(1500, "Product Sales", "Product X")
        accounting.add_expense(800, "Software", "License")
        accounting.add_expense(300, "Marketing", "Ads")
        print("✓ 4 transactions added")

        # Generate reports
        print("\n2. Generating reports...")
        pl_report, cashflow_report = accounting.generate_reports()

        # Verify P&L report
        print("\n3. Verifying P&L report...")
        assert pl_report['report_type'] == 'profit_loss'
        assert pl_report['revenue']['total'] == 3500.0
        assert pl_report['expenses']['total'] == 1100.0
        assert pl_report['summary']['net_profit'] == 2400.0
        print(f"✓ P&L report correct: Net profit ${pl_report['summary']['net_profit']:.2f}")

        # Verify cashflow report
        print("\n4. Verifying cashflow report...")
        assert cashflow_report['report_type'] == 'cashflow'
        assert 'weekly_data' in cashflow_report
        print("✓ Cashflow report generated")

        # Verify report files created
        print("\n5. Verifying report files...")
        report_files = list(accounting.reports_dir.glob("*.json"))
        assert len(report_files) == 2
        print(f"✓ {len(report_files)} report files created")

    print("\n" + "=" * 60)
    print("TEST 3 PASSED")
    print("=" * 60)
    return True


def test_workflow_states():
    """Test multi-step workflow (draft → review → finalized)"""
    print("\n" + "=" * 60)
    print("TEST 4: Workflow States")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        accounting = AccountingCore(base_dir)

        # Add draft transaction
        print("\n1. Adding draft transaction...")
        draft_txn = accounting.add_revenue(
            amount=5000.0,
            category="Consulting",
            description="Large project",
            status=TransactionStatus.DRAFT
        )
        assert draft_txn['status'] == 'draft'
        print("✓ Draft transaction created")

        # Add review transaction
        print("\n2. Adding review transaction...")
        review_txn = accounting.add_revenue(
            amount=3000.0,
            category="Consulting",
            description="Medium project",
            status=TransactionStatus.REVIEW
        )
        assert review_txn['status'] == 'review'
        print("✓ Review transaction created")

        # Add finalized transaction
        print("\n3. Adding finalized transaction...")
        final_txn = accounting.add_revenue(
            amount=1000.0,
            category="Consulting",
            description="Small project",
            status=TransactionStatus.FINALIZED
        )
        assert final_txn['status'] == 'finalized'
        print("✓ Finalized transaction created")

        # Check summary
        print("\n4. Checking summary by status...")
        summary = accounting.get_summary()
        assert summary['transactions_by_status']['draft'] == 1
        assert summary['transactions_by_status']['review'] == 1
        assert summary['transactions_by_status']['finalized'] == 1
        print("✓ Status counts correct")

        # Generate report (should only include finalized)
        print("\n5. Generating P&L report...")
        pl_report = accounting.generate_profit_loss_report()
        # Only finalized transactions should be in report
        assert pl_report['revenue']['total'] == 1000.0
        print("✓ Report only includes finalized transactions")

    print("\n" + "=" * 60)
    print("TEST 4 PASSED")
    print("=" * 60)
    return True


def test_gold_tier_integration():
    """Test Gold Tier integration (EventBus, AuditLogger)"""
    print("\n" + "=" * 60)
    print("TEST 5: Gold Tier Integration")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        accounting = AccountingCore(base_dir)

        # Setup mock Gold Tier components
        print("\n1. Setting up mock Gold Tier components...")
        event_bus = MockEventBus()
        audit_logger = MockAuditLogger()

        accounting.set_event_bus(event_bus)
        accounting.set_audit_logger(audit_logger)
        print("✓ Mock components configured")

        # Add transaction (should emit event and log)
        print("\n2. Adding transaction with Gold Tier integration...")
        accounting.add_revenue(1000, "Consulting", "Project X")

        # Verify event emitted
        print("\n3. Verifying event emission...")
        events = event_bus.get_events('accounting_transaction_added')
        assert len(events) == 1
        assert events[0]['data']['amount'] == 1000
        print(f"✓ Event emitted: accounting_transaction_added")

        # Verify audit log
        print("\n4. Verifying audit logging...")
        logs = audit_logger.get_logs('accounting_transaction')
        assert len(logs) == 1
        assert logs[0]['result'] == 'success'
        print(f"✓ Audit log created")

        # Generate reports (should emit event)
        print("\n5. Generating reports with Gold Tier integration...")
        accounting.generate_reports()

        # Verify report event
        print("\n6. Verifying report event...")
        report_events = event_bus.get_events('accounting_reports_generated')
        assert len(report_events) == 1
        print(f"✓ Report event emitted")

        # Verify report audit log
        print("\n7. Verifying report audit log...")
        report_logs = audit_logger.get_logs('accounting_report')
        assert len(report_logs) == 1
        print(f"✓ Report audit log created")

    print("\n" + "=" * 60)
    print("TEST 5 PASSED")
    print("=" * 60)
    return True


def test_abnormal_cashflow_detection():
    """Test abnormal cashflow detection"""
    print("\n" + "=" * 60)
    print("TEST 6: Abnormal Cashflow Detection")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)
        accounting = AccountingCore(base_dir)

        # Setup event bus
        event_bus = MockEventBus()
        accounting.set_event_bus(event_bus)

        # Create transactions with negative cashflow for 2 weeks
        print("\n1. Creating transactions with negative cashflow...")
        now = datetime.utcnow()

        # Week 1: Negative
        week1 = now - timedelta(weeks=2)
        accounting.add_revenue(1000, "Consulting", "Project A", date=week1.isoformat() + 'Z')
        accounting.add_expense(2000, "Software", "License", date=week1.isoformat() + 'Z')

        # Week 2: Negative
        week2 = now - timedelta(weeks=1)
        accounting.add_revenue(800, "Consulting", "Project B", date=week2.isoformat() + 'Z')
        accounting.add_expense(1500, "Marketing", "Ads", date=week2.isoformat() + 'Z')

        print("✓ Transactions created")

        # Generate cashflow report
        print("\n2. Generating cashflow report...")
        cashflow_report = accounting.generate_cashflow_report(weeks=4)

        # Verify abnormal detection
        print("\n3. Verifying abnormal cashflow detection...")
        assert cashflow_report['abnormal_cashflow_detected'] == True
        print("✓ Abnormal cashflow detected")

        # Verify event emitted
        print("\n4. Verifying abnormal cashflow event...")
        events = event_bus.get_events('accounting_abnormal_cashflow')
        assert len(events) == 1
        print("✓ Abnormal cashflow event emitted")

    print("\n" + "=" * 60)
    print("TEST 6 PASSED")
    print("=" * 60)
    return True


def test_dry_run_mode():
    """Test DRY_RUN mode"""
    print("\n" + "=" * 60)
    print("TEST 7: DRY_RUN Mode")
    print("=" * 60)

    with tempfile.TemporaryDirectory() as tmpdir:
        base_dir = Path(tmpdir)

        # Initialize with dry_run=True
        print("\n1. Initializing with DRY_RUN mode...")
        accounting = AccountingCore(base_dir, dry_run=True)
        print("✓ DRY_RUN mode enabled")

        # Add transaction
        print("\n2. Adding transaction in DRY_RUN mode...")
        accounting.add_revenue(1000, "Consulting", "Project X")

        # Verify ledger file NOT created
        print("\n3. Verifying no files written...")
        assert not accounting.ledger_file.exists()
        print("✓ Ledger file not created (DRY_RUN)")

        # Generate reports
        print("\n4. Generating reports in DRY_RUN mode...")
        accounting.generate_reports()

        # Verify report files NOT created
        print("\n5. Verifying no report files written...")
        report_files = list(accounting.reports_dir.glob("*.json")) if accounting.reports_dir.exists() else []
        assert len(report_files) == 0
        print("✓ Report files not created (DRY_RUN)")

    print("\n" + "=" * 60)
    print("TEST 7 PASSED")
    print("=" * 60)
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("ACCOUNTING CORE TEST SUITE")
    print("=" * 60)

    tests = [
        ("Basic Transactions", test_basic_transactions),
        ("Idempotency", test_idempotency),
        ("Report Generation", test_report_generation),
        ("Workflow States", test_workflow_states),
        ("Gold Tier Integration", test_gold_tier_integration),
        ("Abnormal Cashflow Detection", test_abnormal_cashflow_detection),
        ("DRY_RUN Mode", test_dry_run_mode)
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
