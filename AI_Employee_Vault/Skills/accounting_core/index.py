#!/usr/bin/env python3
"""
Accounting Core Skill - Gold Tier Integration
==============================================

Lightweight internal accounting system for AI Employee Vault.

Features:
- Revenue and expense tracking
- Transaction categorization
- Profit & Loss reports
- Weekly cashflow summaries
- Multi-step workflows (draft → review → finalize)
- Event-driven integration with Gold Tier
- Idempotent operations (no duplicate entries)

Gold Tier Integration:
- Emits events to EventBus for autonomous detection
- Registers with SkillRegistry automatically
- Uses StateManager for persistence
- Logs to AuditLogger for compliance
- Supports AutonomousExecutor workflows

Usage:
    # Add revenue entry
    python3 index.py add-revenue --amount 1000 --category "Consulting" --description "Project X"

    # Add expense entry
    python3 index.py add-expense --amount 500 --category "Software" --description "License"

    # Generate reports
    python3 index.py generate-reports

    # Get summary
    python3 index.py summary
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from enum import Enum


class TransactionType(Enum):
    """Transaction types"""
    REVENUE = "revenue"
    EXPENSE = "expense"


class TransactionStatus(Enum):
    """Transaction workflow status"""
    DRAFT = "draft"
    REVIEW = "review"
    FINALIZED = "finalized"
    REJECTED = "rejected"


class AccountingCore:
    """
    Core accounting system with Gold Tier integration

    Manages ledger, generates reports, and emits events for autonomous operation.
    """

    def __init__(self, base_dir: Path, dry_run: bool = False):
        """
        Initialize accounting core

        Args:
            base_dir: Base directory for AI Employee Vault
            dry_run: If True, don't write to disk
        """
        self.base_dir = base_dir
        self.dry_run = dry_run

        # Directories
        self.data_dir = base_dir / "Data"
        self.reports_dir = base_dir / "Reports" / "accounting"
        self.ledger_file = self.data_dir / "ledger.json"

        # Create directories
        if not dry_run:
            self.data_dir.mkdir(parents=True, exist_ok=True)
            self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Load ledger
        self.ledger = self._load_ledger()

        # Event bus integration (optional, for Gold Tier)
        self.event_bus = None
        self.audit_logger = None

    def set_event_bus(self, event_bus):
        """Set EventBus for Gold Tier integration"""
        self.event_bus = event_bus

    def set_audit_logger(self, audit_logger):
        """Set AuditLogger for Gold Tier integration"""
        self.audit_logger = audit_logger

    def _load_ledger(self) -> Dict:
        """Load ledger from disk"""
        if self.ledger_file.exists():
            try:
                with open(self.ledger_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load ledger: {e}")
                return self._create_empty_ledger()
        else:
            return self._create_empty_ledger()

    def _create_empty_ledger(self) -> Dict:
        """Create empty ledger structure"""
        return {
            'version': '1.0',
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'transactions': [],
            'metadata': {
                'total_revenue': 0.0,
                'total_expenses': 0.0,
                'transaction_count': 0
            }
        }

    def _save_ledger(self):
        """Save ledger to disk"""
        if self.dry_run:
            print("[DRY RUN] Would save ledger to disk")
            return

        try:
            # Update metadata
            self.ledger['metadata']['last_updated'] = datetime.utcnow().isoformat() + 'Z'

            # Write to disk
            with open(self.ledger_file, 'w') as f:
                json.dump(self.ledger, f, indent=2)

            print(f"✓ Ledger saved to {self.ledger_file}")
        except Exception as e:
            print(f"Error saving ledger: {e}")
            raise

    def _generate_transaction_id(self, transaction_type: str, amount: float,
                                 category: str, description: str, date: str) -> str:
        """
        Generate unique transaction ID for idempotency

        Args:
            transaction_type: Type of transaction
            amount: Transaction amount
            category: Transaction category
            description: Transaction description
            date: Transaction date

        Returns:
            Unique transaction ID (hash)
        """
        content = f"{transaction_type}_{amount}_{category}_{description}_{date}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def _transaction_exists(self, transaction_id: str) -> bool:
        """Check if transaction already exists"""
        for txn in self.ledger['transactions']:
            if txn.get('id') == transaction_id:
                return True
        return False

    def add_transaction(self, transaction_type: TransactionType, amount: float,
                       category: str, description: str, date: Optional[str] = None,
                       status: TransactionStatus = TransactionStatus.FINALIZED,
                       metadata: Optional[Dict] = None) -> Dict:
        """
        Add transaction to ledger (idempotent)

        Args:
            transaction_type: REVENUE or EXPENSE
            amount: Transaction amount (positive)
            category: Transaction category
            description: Transaction description
            date: Transaction date (ISO format, defaults to now)
            status: Transaction status (draft, review, finalized)
            metadata: Additional metadata

        Returns:
            Transaction record
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Default date to now
        if date is None:
            date = datetime.utcnow().isoformat() + 'Z'

        # Generate transaction ID
        txn_id = self._generate_transaction_id(
            transaction_type.value, amount, category, description, date
        )

        # Check for duplicates (idempotency)
        if self._transaction_exists(txn_id):
            print(f"⚠ Transaction already exists: {txn_id}")
            # Return existing transaction
            for txn in self.ledger['transactions']:
                if txn.get('id') == txn_id:
                    return txn

        # Create transaction record
        transaction = {
            'id': txn_id,
            'type': transaction_type.value,
            'amount': amount,
            'category': category,
            'description': description,
            'date': date,
            'status': status.value,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'metadata': metadata or {}
        }

        # Add to ledger
        self.ledger['transactions'].append(transaction)

        # Update metadata
        if transaction_type == TransactionType.REVENUE:
            self.ledger['metadata']['total_revenue'] += amount
        else:
            self.ledger['metadata']['total_expenses'] += amount

        self.ledger['metadata']['transaction_count'] += 1

        # Save ledger
        self._save_ledger()

        # Emit event (Gold Tier integration)
        if self.event_bus:
            self.event_bus.publish('accounting_transaction_added', {
                'transaction_id': txn_id,
                'type': transaction_type.value,
                'amount': amount,
                'category': category,
                'status': status.value,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Audit log (Gold Tier integration)
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type='accounting_transaction',
                actor='accounting_core',
                action='add_transaction',
                resource=f"transaction_{txn_id}",
                result='success',
                metadata={
                    'type': transaction_type.value,
                    'amount': amount,
                    'category': category
                }
            )

        print(f"✓ Transaction added: {txn_id} ({transaction_type.value} ${amount:.2f})")

        return transaction

    def add_revenue(self, amount: float, category: str, description: str,
                   date: Optional[str] = None, status: TransactionStatus = TransactionStatus.FINALIZED,
                   metadata: Optional[Dict] = None) -> Dict:
        """Add revenue transaction"""
        return self.add_transaction(
            TransactionType.REVENUE, amount, category, description, date, status, metadata
        )

    def add_expense(self, amount: float, category: str, description: str,
                   date: Optional[str] = None, status: TransactionStatus = TransactionStatus.FINALIZED,
                   metadata: Optional[Dict] = None) -> Dict:
        """Add expense transaction"""
        return self.add_transaction(
            TransactionType.EXPENSE, amount, category, description, date, status, metadata
        )

    def get_transactions(self, transaction_type: Optional[TransactionType] = None,
                        status: Optional[TransactionStatus] = None,
                        start_date: Optional[str] = None,
                        end_date: Optional[str] = None) -> List[Dict]:
        """
        Get transactions with filters

        Args:
            transaction_type: Filter by type (optional)
            status: Filter by status (optional)
            start_date: Filter by start date (optional)
            end_date: Filter by end date (optional)

        Returns:
            List of matching transactions
        """
        transactions = self.ledger['transactions']

        # Filter by type
        if transaction_type:
            transactions = [t for t in transactions if t['type'] == transaction_type.value]

        # Filter by status
        if status:
            transactions = [t for t in transactions if t['status'] == status.value]

        # Filter by date range
        if start_date:
            transactions = [t for t in transactions if t['date'] >= start_date]

        if end_date:
            transactions = [t for t in transactions if t['date'] <= end_date]

        return transactions

    def generate_profit_loss_report(self, start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> Dict:
        """
        Generate Profit & Loss report

        Args:
            start_date: Report start date (optional)
            end_date: Report end date (optional)

        Returns:
            P&L report dictionary
        """
        # Get transactions in date range
        transactions = self.get_transactions(start_date=start_date, end_date=end_date)

        # Calculate totals by category
        revenue_by_category = {}
        expense_by_category = {}

        total_revenue = 0.0
        total_expenses = 0.0

        for txn in transactions:
            if txn['status'] != TransactionStatus.FINALIZED.value:
                continue  # Only include finalized transactions

            amount = txn['amount']
            category = txn['category']

            if txn['type'] == TransactionType.REVENUE.value:
                revenue_by_category[category] = revenue_by_category.get(category, 0.0) + amount
                total_revenue += amount
            else:
                expense_by_category[category] = expense_by_category.get(category, 0.0) + amount
                total_expenses += amount

        # Calculate profit/loss
        net_profit = total_revenue - total_expenses
        profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0.0

        report = {
            'report_type': 'profit_loss',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'period': {
                'start_date': start_date or 'inception',
                'end_date': end_date or 'now'
            },
            'revenue': {
                'by_category': revenue_by_category,
                'total': total_revenue
            },
            'expenses': {
                'by_category': expense_by_category,
                'total': total_expenses
            },
            'summary': {
                'net_profit': net_profit,
                'profit_margin_percent': profit_margin
            }
        }

        return report

    def generate_cashflow_report(self, weeks: int = 4) -> Dict:
        """
        Generate weekly cashflow report

        Args:
            weeks: Number of weeks to include (default: 4)

        Returns:
            Cashflow report dictionary
        """
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(weeks=weeks)

        # Get transactions in range
        transactions = self.get_transactions(
            start_date=start_date.isoformat() + 'Z',
            end_date=end_date.isoformat() + 'Z'
        )

        # Group by week
        weekly_data = {}

        for txn in transactions:
            if txn['status'] != TransactionStatus.FINALIZED.value:
                continue

            # Parse transaction date
            txn_date = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))

            # Calculate week number
            week_start = txn_date - timedelta(days=txn_date.weekday())
            week_key = week_start.strftime('%Y-W%U')

            if week_key not in weekly_data:
                weekly_data[week_key] = {
                    'week_start': week_start.isoformat() + 'Z',
                    'revenue': 0.0,
                    'expenses': 0.0,
                    'net_cashflow': 0.0
                }

            amount = txn['amount']

            if txn['type'] == TransactionType.REVENUE.value:
                weekly_data[week_key]['revenue'] += amount
                weekly_data[week_key]['net_cashflow'] += amount
            else:
                weekly_data[week_key]['expenses'] += amount
                weekly_data[week_key]['net_cashflow'] -= amount

        # Detect abnormal cashflow (negative for 2+ consecutive weeks)
        weeks_sorted = sorted(weekly_data.keys())
        abnormal_detected = False
        consecutive_negative = 0

        for week in weeks_sorted:
            if weekly_data[week]['net_cashflow'] < 0:
                consecutive_negative += 1
                if consecutive_negative >= 2:
                    abnormal_detected = True
            else:
                consecutive_negative = 0

        report = {
            'report_type': 'cashflow',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'period': {
                'weeks': weeks,
                'start_date': start_date.isoformat() + 'Z',
                'end_date': end_date.isoformat() + 'Z'
            },
            'weekly_data': weekly_data,
            'abnormal_cashflow_detected': abnormal_detected
        }

        # Emit event if abnormal cashflow detected (Gold Tier integration)
        if abnormal_detected and self.event_bus:
            self.event_bus.publish('accounting_abnormal_cashflow', {
                'consecutive_negative_weeks': consecutive_negative,
                'report': report,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })
            print("⚠ Abnormal cashflow detected (2+ consecutive negative weeks)")

        return report

    def generate_reports(self) -> Tuple[Dict, Dict]:
        """
        Generate all reports (P&L and Cashflow)

        Returns:
            Tuple of (profit_loss_report, cashflow_report)
        """
        print("\nGenerating reports...")

        # Generate P&L report
        pl_report = self.generate_profit_loss_report()

        # Generate cashflow report
        cashflow_report = self.generate_cashflow_report()

        # Save reports to disk
        if not self.dry_run:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')

            pl_file = self.reports_dir / f"profit_loss_{timestamp}.json"
            with open(pl_file, 'w') as f:
                json.dump(pl_report, f, indent=2)
            print(f"✓ P&L report saved: {pl_file.name}")

            cashflow_file = self.reports_dir / f"cashflow_{timestamp}.json"
            with open(cashflow_file, 'w') as f:
                json.dump(cashflow_report, f, indent=2)
            print(f"✓ Cashflow report saved: {cashflow_file.name}")

        # Emit event (Gold Tier integration)
        if self.event_bus:
            self.event_bus.publish('accounting_reports_generated', {
                'profit_loss': pl_report['summary'],
                'cashflow_abnormal': cashflow_report['abnormal_cashflow_detected'],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Audit log (Gold Tier integration)
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type='accounting_report',
                actor='accounting_core',
                action='generate_reports',
                resource='reports',
                result='success',
                metadata={
                    'net_profit': pl_report['summary']['net_profit'],
                    'abnormal_cashflow': cashflow_report['abnormal_cashflow_detected']
                }
            )

        return pl_report, cashflow_report

    def get_summary(self) -> Dict:
        """Get accounting summary"""
        metadata = self.ledger['metadata']

        # Count transactions by status
        draft_count = len([t for t in self.ledger['transactions'] if t['status'] == 'draft'])
        review_count = len([t for t in self.ledger['transactions'] if t['status'] == 'review'])
        finalized_count = len([t for t in self.ledger['transactions'] if t['status'] == 'finalized'])

        summary = {
            'total_revenue': metadata.get('total_revenue', 0.0),
            'total_expenses': metadata.get('total_expenses', 0.0),
            'net_profit': metadata.get('total_revenue', 0.0) - metadata.get('total_expenses', 0.0),
            'transaction_count': metadata.get('transaction_count', 0),
            'transactions_by_status': {
                'draft': draft_count,
                'review': review_count,
                'finalized': finalized_count
            },
            'last_updated': metadata.get('last_updated', 'Never')
        }

        return summary

    def print_summary(self):
        """Print formatted summary"""
        summary = self.get_summary()

        print("\n" + "=" * 60)
        print("ACCOUNTING SUMMARY")
        print("=" * 60)
        print(f"Total Revenue:    ${summary['total_revenue']:,.2f}")
        print(f"Total Expenses:   ${summary['total_expenses']:,.2f}")
        print(f"Net Profit:       ${summary['net_profit']:,.2f}")
        print(f"\nTransactions:     {summary['transaction_count']}")
        print(f"  - Draft:        {summary['transactions_by_status']['draft']}")
        print(f"  - Review:       {summary['transactions_by_status']['review']}")
        print(f"  - Finalized:    {summary['transactions_by_status']['finalized']}")
        print(f"\nLast Updated:     {summary['last_updated']}")
        print("=" * 60)

    def print_report(self, report: Dict):
        """Print formatted report"""
        if report['report_type'] == 'profit_loss':
            self._print_pl_report(report)
        elif report['report_type'] == 'cashflow':
            self._print_cashflow_report(report)

    def _print_pl_report(self, report: Dict):
        """Print Profit & Loss report"""
        print("\n" + "=" * 60)
        print("PROFIT & LOSS REPORT")
        print("=" * 60)
        print(f"Period: {report['period']['start_date']} to {report['period']['end_date']}")
        print()

        print("REVENUE:")
        for category, amount in report['revenue']['by_category'].items():
            print(f"  {category:30s} ${amount:>12,.2f}")
        print(f"  {'TOTAL REVENUE':30s} ${report['revenue']['total']:>12,.2f}")
        print()

        print("EXPENSES:")
        for category, amount in report['expenses']['by_category'].items():
            print(f"  {category:30s} ${amount:>12,.2f}")
        print(f"  {'TOTAL EXPENSES':30s} ${report['expenses']['total']:>12,.2f}")
        print()

        print("SUMMARY:")
        print(f"  {'Net Profit':30s} ${report['summary']['net_profit']:>12,.2f}")
        print(f"  {'Profit Margin':30s} {report['summary']['profit_margin_percent']:>12.2f}%")
        print("=" * 60)

    def _print_cashflow_report(self, report: Dict):
        """Print Cashflow report"""
        print("\n" + "=" * 60)
        print("WEEKLY CASHFLOW REPORT")
        print("=" * 60)
        print(f"Period: {report['period']['weeks']} weeks")
        print()

        for week, data in sorted(report['weekly_data'].items()):
            print(f"Week {week}:")
            print(f"  Revenue:      ${data['revenue']:>12,.2f}")
            print(f"  Expenses:     ${data['expenses']:>12,.2f}")
            print(f"  Net Cashflow: ${data['net_cashflow']:>12,.2f}")
            print()

        if report['abnormal_cashflow_detected']:
            print("⚠ WARNING: Abnormal cashflow detected (2+ consecutive negative weeks)")

        print("=" * 60)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Accounting Core Skill')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no writes)')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Add revenue
    revenue_parser = subparsers.add_parser('add-revenue', help='Add revenue transaction')
    revenue_parser.add_argument('--amount', type=float, required=True, help='Amount')
    revenue_parser.add_argument('--category', required=True, help='Category')
    revenue_parser.add_argument('--description', required=True, help='Description')
    revenue_parser.add_argument('--date', help='Date (ISO format)')
    revenue_parser.add_argument('--status', default='finalized',
                               choices=['draft', 'review', 'finalized'], help='Status')

    # Add expense
    expense_parser = subparsers.add_parser('add-expense', help='Add expense transaction')
    expense_parser.add_argument('--amount', type=float, required=True, help='Amount')
    expense_parser.add_argument('--category', required=True, help='Category')
    expense_parser.add_argument('--description', required=True, help='Description')
    expense_parser.add_argument('--date', help='Date (ISO format)')
    expense_parser.add_argument('--status', default='finalized',
                               choices=['draft', 'review', 'finalized'], help='Status')

    # Generate reports
    reports_parser = subparsers.add_parser('generate-reports', help='Generate all reports')

    # Summary
    summary_parser = subparsers.add_parser('summary', help='Show accounting summary')

    # List transactions
    list_parser = subparsers.add_parser('list', help='List transactions')
    list_parser.add_argument('--type', choices=['revenue', 'expense'], help='Filter by type')
    list_parser.add_argument('--status', choices=['draft', 'review', 'finalized'],
                            help='Filter by status')

    args = parser.parse_args()

    # Determine base directory
    base_dir = Path(__file__).parent.parent.parent

    # Create accounting core
    accounting = AccountingCore(base_dir, dry_run=args.dry_run)

    if args.dry_run:
        print("[DRY RUN MODE - No changes will be saved]")

    # Execute command
    if args.command == 'add-revenue':
        status = TransactionStatus[args.status.upper()]
        accounting.add_revenue(
            amount=args.amount,
            category=args.category,
            description=args.description,
            date=args.date,
            status=status
        )
        accounting.print_summary()

    elif args.command == 'add-expense':
        status = TransactionStatus[args.status.upper()]
        accounting.add_expense(
            amount=args.amount,
            category=args.category,
            description=args.description,
            date=args.date,
            status=status
        )
        accounting.print_summary()

    elif args.command == 'generate-reports':
        pl_report, cashflow_report = accounting.generate_reports()
        accounting.print_report(pl_report)
        accounting.print_report(cashflow_report)

    elif args.command == 'summary':
        accounting.print_summary()

    elif args.command == 'list':
        txn_type = TransactionType[args.type.upper()] if args.type else None
        txn_status = TransactionStatus[args.status.upper()] if args.status else None

        transactions = accounting.get_transactions(
            transaction_type=txn_type,
            status=txn_status
        )

        print(f"\nFound {len(transactions)} transactions:")
        for txn in transactions:
            print(f"  [{txn['id'][:8]}] {txn['type']:8s} ${txn['amount']:>10,.2f} - {txn['category']} - {txn['description']}")

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
