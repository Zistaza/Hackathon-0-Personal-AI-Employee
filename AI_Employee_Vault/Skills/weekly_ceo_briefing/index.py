#!/usr/bin/env python3
"""
Weekly CEO Briefing Skill - Gold Tier Integration
==================================================

Generates comprehensive executive-level business reports combining:
- Accounting data (revenue, expenses, P&L, cashflow)
- Audit logs (system activity)
- Workflow status (pending, completed)
- RetryQueue statistics
- Escalations and alerts
- System health status
- AI-generated recommendations and risk warnings

Gold Tier Integration:
- Aggregates data from all Gold Tier components
- Registers with SkillRegistry
- Emits events to EventBus
- Logs to AuditLogger
- Supports AutonomousExecutor triggering

Usage:
    # Generate current week's briefing
    python3 index.py generate

    # Generate for specific week
    python3 index.py generate --week 2026-W09

    # Dry run (no file written)
    python3 index.py --dry-run generate
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class WeeklyCEOBriefing:
    """
    Weekly CEO Briefing Generator

    Aggregates data from all Gold Tier components and generates
    executive-level markdown reports.
    """

    def __init__(self, base_dir: Path, dry_run: bool = False):
        """
        Initialize CEO briefing generator

        Args:
            base_dir: Base directory for AI Employee Vault
            dry_run: If True, don't write to disk
        """
        self.base_dir = base_dir
        self.dry_run = dry_run

        # Directories
        self.data_dir = base_dir / "Data"
        self.reports_dir = base_dir / "Reports" / "Weekly"
        self.logs_dir = base_dir / "Logs"
        self.needs_action_dir = base_dir / "Needs_Action"
        self.pending_approval_dir = base_dir / "Pending_Approval"

        # Data files
        self.ledger_file = self.data_dir / "ledger.json"
        self.state_file = base_dir / "Skills" / "integration_orchestrator" / "state.json"
        self.audit_file = self.logs_dir / "audit.jsonl"

        # Create directories
        if not dry_run:
            self.reports_dir.mkdir(parents=True, exist_ok=True)

        # Gold Tier integration (optional)
        self.event_bus = None
        self.audit_logger = None
        self.orchestrator = None

    def set_event_bus(self, event_bus):
        """Set EventBus for Gold Tier integration"""
        self.event_bus = event_bus

    def set_audit_logger(self, audit_logger):
        """Set AuditLogger for Gold Tier integration"""
        self.audit_logger = audit_logger

    def set_orchestrator(self, orchestrator):
        """Set IntegrationOrchestrator for direct component access"""
        self.orchestrator = orchestrator

    def _get_week_identifier(self, date: Optional[datetime] = None) -> str:
        """
        Get week identifier (YYYY-WXX format)

        Args:
            date: Date to get week for (defaults to now)

        Returns:
            Week identifier string
        """
        if date is None:
            date = datetime.utcnow()

        # Use %V for ISO week number (Monday as first day of week)
        # This ensures consistent week numbering
        return date.strftime('%Y-W%V')

    def _get_week_range(self, week_id: str) -> Tuple[datetime, datetime]:
        """
        Get date range for a week identifier (ISO week)

        Args:
            week_id: Week identifier (YYYY-WXX)

        Returns:
            Tuple of (start_date, end_date) - timezone-aware UTC
        """
        from datetime import timezone

        # Parse week identifier
        year, week = week_id.split('-W')
        year = int(year)
        week = int(week)

        # ISO week calculation: Week 1 is the week with the first Thursday
        # Find January 4th (always in week 1)
        jan4 = datetime(year, 1, 4, tzinfo=timezone.utc)

        # Find Monday of week 1
        week1_monday = jan4 - timedelta(days=jan4.weekday())

        # Calculate start of target week (Monday)
        week_start = week1_monday + timedelta(weeks=week - 1)

        # End of week (Sunday)
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)

        return week_start, week_end

    def _check_report_exists(self, week_id: str) -> bool:
        """
        Check if report already exists for this week (idempotency)

        Args:
            week_id: Week identifier

        Returns:
            True if report exists
        """
        # Check for existing report file
        pattern = f"CEO_Briefing_{week_id.replace('-', '_')}_*.md"
        existing = list(self.reports_dir.glob(pattern)) if self.reports_dir.exists() else []

        return len(existing) > 0

    def _load_accounting_data(self) -> Optional[Dict]:
        """Load accounting data from ledger"""
        if not self.ledger_file.exists():
            return None

        try:
            with open(self.ledger_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load accounting data: {e}")
            return None

    def _load_state_data(self) -> Optional[Dict]:
        """Load state data from StateManager"""
        if not self.state_file.exists():
            return None

        try:
            with open(self.state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: Could not load state data: {e}")
            return None

    def _load_audit_logs(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Load audit logs for date range

        Args:
            start_date: Start of range
            end_date: End of range

        Returns:
            List of audit log entries
        """
        if not self.audit_file.exists():
            return []

        logs = []

        try:
            with open(self.audit_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Parse timestamp
                        entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))

                        # Check if in range
                        if start_date <= entry_time <= end_date:
                            logs.append(entry)

                    except (json.JSONDecodeError, KeyError, ValueError):
                        continue

        except Exception as e:
            print(f"Warning: Could not load audit logs: {e}")

        return logs

    def _analyze_accounting_data(self, ledger: Dict, start_date: datetime, end_date: datetime) -> Dict:
        """
        Analyze accounting data for the week

        Args:
            ledger: Ledger data
            start_date: Week start
            end_date: Week end

        Returns:
            Analysis dictionary
        """
        if not ledger:
            return {
                'revenue': 0.0,
                'expenses': 0.0,
                'net_profit': 0.0,
                'revenue_by_category': {},
                'expenses_by_category': {},
                'transaction_count': 0
            }

        # Filter transactions for this week
        transactions = ledger.get('transactions', [])

        revenue_total = 0.0
        expenses_total = 0.0
        revenue_by_cat = defaultdict(float)
        expenses_by_cat = defaultdict(float)
        txn_count = 0

        for txn in transactions:
            # Only include finalized transactions
            if txn.get('status') != 'finalized':
                continue

            # Parse date
            try:
                txn_date = datetime.fromisoformat(txn['date'].replace('Z', '+00:00'))
            except:
                continue

            # Check if in range
            if not (start_date <= txn_date <= end_date):
                continue

            txn_count += 1
            amount = txn['amount']
            category = txn['category']

            if txn['type'] == 'revenue':
                revenue_total += amount
                revenue_by_cat[category] += amount
            else:
                expenses_total += amount
                expenses_by_cat[category] += amount

        return {
            'revenue': revenue_total,
            'expenses': expenses_total,
            'net_profit': revenue_total - expenses_total,
            'revenue_by_category': dict(revenue_by_cat),
            'expenses_by_category': dict(expenses_by_cat),
            'transaction_count': txn_count
        }

    def _analyze_audit_logs(self, logs: List[Dict]) -> Dict:
        """
        Analyze audit logs for the week

        Args:
            logs: List of audit log entries

        Returns:
            Analysis dictionary
        """
        analysis = {
            'total_events': len(logs),
            'events_by_type': defaultdict(int),
            'events_by_actor': defaultdict(int),
            'skill_executions': 0,
            'skill_successes': 0,
            'skill_failures': 0,
            'escalations': 0,
            'email_actions': 0
        }

        for log in logs:
            event_type = log.get('event_type', 'unknown')
            actor = log.get('actor', 'unknown')
            result = log.get('result', 'unknown')

            analysis['events_by_type'][event_type] += 1
            analysis['events_by_actor'][actor] += 1

            if event_type == 'skill_execution':
                analysis['skill_executions'] += 1
                if result == 'success':
                    analysis['skill_successes'] += 1
                else:
                    analysis['skill_failures'] += 1

            elif event_type == 'escalation':
                analysis['escalations'] += 1

            elif event_type == 'email_action':
                analysis['email_actions'] += 1

        # Convert defaultdicts to regular dicts
        analysis['events_by_type'] = dict(analysis['events_by_type'])
        analysis['events_by_actor'] = dict(analysis['events_by_actor'])

        return analysis

    def _get_workflow_status(self) -> Dict:
        """
        Get current workflow status

        Returns:
            Workflow status dictionary
        """
        status = {
            'needs_action_count': 0,
            'pending_approval_count': 0,
            'escalation_count': 0,
            'needs_action_files': [],
            'escalation_files': []
        }

        # Count Needs_Action items
        if self.needs_action_dir.exists():
            needs_action_files = list(self.needs_action_dir.glob("*.md"))
            status['needs_action_count'] = len(needs_action_files)
            status['needs_action_files'] = [f.name for f in needs_action_files[:5]]  # First 5

            # Count escalations
            escalations = [f for f in needs_action_files if f.name.startswith('ESCALATION_')]
            status['escalation_count'] = len(escalations)
            status['escalation_files'] = [f.name for f in escalations[:5]]

        # Count Pending_Approval items
        if self.pending_approval_dir.exists():
            pending_files = list(self.pending_approval_dir.glob("*.md"))
            status['pending_approval_count'] = len(pending_files)

        return status

    def _get_system_health(self) -> Dict:
        """
        Get system health status

        Returns:
            Health status dictionary
        """
        if self.orchestrator and hasattr(self.orchestrator, 'health_monitor'):
            try:
                health = self.orchestrator.health_monitor.get_system_health()
                return {
                    'overall_status': health['overall_status'].value,
                    'components': {
                        name: {
                            'status': comp['status'].value,
                            'message': comp['message']
                        }
                        for name, comp in health['components'].items()
                    }
                }
            except Exception as e:
                print(f"Warning: Could not get health status: {e}")

        return {
            'overall_status': 'unknown',
            'components': {}
        }

    def _get_retry_queue_stats(self) -> Dict:
        """
        Get RetryQueue statistics

        Returns:
            RetryQueue stats dictionary
        """
        if self.orchestrator and hasattr(self.orchestrator, 'retry_queue'):
            try:
                queue_size = self.orchestrator.retry_queue.get_queue_size()
                return {
                    'queue_size': queue_size,
                    'status': 'normal' if queue_size < 10 else 'elevated' if queue_size < 50 else 'critical'
                }
            except Exception as e:
                print(f"Warning: Could not get retry queue stats: {e}")

        return {
            'queue_size': 0,
            'status': 'unknown'
        }

    def _generate_recommendations(self, accounting: Dict, audit: Dict,
                                 workflows: Dict, health: Dict, retry: Dict) -> List[str]:
        """
        Generate AI recommendations based on data

        Args:
            accounting: Accounting analysis
            audit: Audit log analysis
            workflows: Workflow status
            health: Health status
            retry: RetryQueue stats

        Returns:
            List of recommendation strings
        """
        recommendations = []

        # Accounting recommendations
        if accounting['net_profit'] < 0:
            recommendations.append("⚠️ **Negative profit this week.** Review expenses and accelerate revenue collection.")

        if accounting['revenue'] == 0:
            recommendations.append("⚠️ **No revenue recorded this week.** Verify accounting entries are up to date.")

        if accounting['expenses'] > accounting['revenue'] * 0.8:
            recommendations.append("💡 **High expense ratio (>80%).** Consider cost optimization opportunities.")

        # Workflow recommendations
        if workflows['escalation_count'] > 0:
            recommendations.append(f"🚨 **{workflows['escalation_count']} escalations require attention.** Review Needs_Action folder.")

        if workflows['pending_approval_count'] > 5:
            recommendations.append(f"⏳ **{workflows['pending_approval_count']} items pending approval.** Review to prevent workflow delays.")

        # System health recommendations
        if health['overall_status'] in ['degraded', 'unhealthy']:
            recommendations.append(f"🔧 **System health is {health['overall_status']}.** Review component status and resolve issues.")

        # RetryQueue recommendations
        if retry['queue_size'] > 10:
            recommendations.append(f"🔄 **RetryQueue has {retry['queue_size']} items.** Investigate recurring failures.")

        # Audit log recommendations
        if audit['skill_failures'] > audit['skill_successes']:
            recommendations.append("⚠️ **More skill failures than successes.** Review error logs and fix failing skills.")

        # Positive recommendations
        if accounting['net_profit'] > 0 and len(recommendations) == 0:
            recommendations.append("✅ **Strong performance this week.** Continue current operations.")

        if workflows['escalation_count'] == 0 and workflows['needs_action_count'] == 0:
            recommendations.append("✅ **No pending escalations or actions.** System operating smoothly.")

        return recommendations

    def _generate_risk_warnings(self, accounting: Dict, audit: Dict,
                               workflows: Dict, health: Dict, retry: Dict) -> List[str]:
        """
        Generate risk warnings

        Args:
            accounting: Accounting analysis
            audit: Audit log analysis
            workflows: Workflow status
            health: Health status
            retry: RetryQueue stats

        Returns:
            List of risk warning strings
        """
        warnings = []

        # Critical financial risks
        if accounting['net_profit'] < -1000:
            warnings.append("🔴 **CRITICAL: Significant negative profit.** Immediate action required.")

        # System health risks
        if health['overall_status'] == 'unhealthy':
            warnings.append("🔴 **CRITICAL: System unhealthy.** Core functionality may be impaired.")

        # Escalation risks
        if workflows['escalation_count'] > 5:
            warnings.append("🔴 **HIGH: Multiple escalations.** System may require manual intervention.")

        # RetryQueue risks
        if retry['queue_size'] > 50:
            warnings.append("🔴 **CRITICAL: RetryQueue overloaded.** System may be experiencing cascading failures.")

        # Skill failure risks
        failure_rate = audit['skill_failures'] / max(audit['skill_executions'], 1)
        if failure_rate > 0.5:
            warnings.append(f"🟡 **MEDIUM: High skill failure rate ({failure_rate*100:.0f}%).** Review skill implementations.")

        return warnings

    def generate_briefing(self, week_id: Optional[str] = None) -> Dict:
        """
        Generate CEO briefing for specified week

        Args:
            week_id: Week identifier (defaults to current week)

        Returns:
            Briefing data dictionary
        """
        # Get week identifier
        if week_id is None:
            week_id = self._get_week_identifier()

        print(f"\nGenerating CEO Briefing for {week_id}...")

        # Check if report already exists (idempotency)
        if self._check_report_exists(week_id):
            print(f"⚠️ Report already exists for {week_id}")
            if not self.dry_run:
                print("Skipping generation (idempotent)")
                return {'status': 'skipped', 'reason': 'already_exists'}

        # Get week range
        week_start, week_end = self._get_week_range(week_id)

        print(f"Week range: {week_start.date()} to {week_end.date()}")

        # Load data sources
        print("\n1. Loading data sources...")
        ledger = self._load_accounting_data()
        state = self._load_state_data()
        audit_logs = self._load_audit_logs(week_start, week_end)
        print(f"   ✓ Loaded {len(audit_logs)} audit log entries")

        # Analyze data
        print("\n2. Analyzing data...")
        accounting = self._analyze_accounting_data(ledger, week_start, week_end)
        audit = self._analyze_audit_logs(audit_logs)
        workflows = self._get_workflow_status()
        health = self._get_system_health()
        retry = self._get_retry_queue_stats()
        print("   ✓ Analysis complete")

        # Generate insights
        print("\n3. Generating insights...")
        recommendations = self._generate_recommendations(accounting, audit, workflows, health, retry)
        warnings = self._generate_risk_warnings(accounting, audit, workflows, health, retry)
        print(f"   ✓ {len(recommendations)} recommendations")
        print(f"   ✓ {len(warnings)} risk warnings")

        # Build briefing data
        briefing = {
            'week_id': week_id,
            'week_start': week_start.isoformat() + 'Z',
            'week_end': week_end.isoformat() + 'Z',
            'generated_at': datetime.utcnow().isoformat() + 'Z',
            'accounting': accounting,
            'audit': audit,
            'workflows': workflows,
            'health': health,
            'retry_queue': retry,
            'recommendations': recommendations,
            'warnings': warnings
        }

        # Generate markdown report
        print("\n4. Generating markdown report...")
        markdown = self._generate_markdown(briefing)

        # Save report
        if not self.dry_run:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"CEO_Briefing_{week_id.replace('-', '_')}_{timestamp}.md"
            filepath = self.reports_dir / filename

            with open(filepath, 'w') as f:
                f.write(markdown)

            print(f"   ✓ Report saved: {filename}")
            briefing['report_file'] = filename
        else:
            print("   [DRY RUN] Report not saved")
            briefing['report_file'] = None

        # Emit event (Gold Tier integration)
        if self.event_bus:
            self.event_bus.publish('ceo_briefing_generated', {
                'week_id': week_id,
                'net_profit': accounting['net_profit'],
                'warnings_count': len(warnings),
                'recommendations_count': len(recommendations),
                'report_file': briefing['report_file'],
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Audit log (Gold Tier integration)
        if self.audit_logger:
            self.audit_logger.log_event(
                event_type='ceo_briefing',
                actor='weekly_ceo_briefing',
                action='generate_briefing',
                resource=f"briefing_{week_id}",
                result='success',
                metadata={
                    'week_id': week_id,
                    'net_profit': accounting['net_profit'],
                    'warnings_count': len(warnings)
                }
            )

        print("\n✓ CEO Briefing generated successfully")

        return briefing

    def _generate_markdown(self, briefing: Dict) -> str:
        """
        Generate markdown report from briefing data

        Args:
            briefing: Briefing data dictionary

        Returns:
            Markdown string
        """
        md = []

        # Header
        md.append("# Weekly CEO Briefing")
        md.append("")
        md.append(f"**Week:** {briefing['week_id']}")
        md.append(f"**Period:** {briefing['week_start'][:10]} to {briefing['week_end'][:10]}")
        md.append(f"**Generated:** {briefing['generated_at'][:19]}Z")
        md.append("")
        md.append("---")
        md.append("")

        # Executive Summary
        md.append("## Executive Summary")
        md.append("")

        accounting = briefing['accounting']
        md.append(f"- **Revenue:** ${accounting['revenue']:,.2f}")
        md.append(f"- **Expenses:** ${accounting['expenses']:,.2f}")
        md.append(f"- **Net Profit:** ${accounting['net_profit']:,.2f}")
        md.append(f"- **Transactions:** {accounting['transaction_count']}")
        md.append("")

        # Risk Warnings (if any)
        if briefing['warnings']:
            md.append("### ⚠️ Risk Warnings")
            md.append("")
            for warning in briefing['warnings']:
                md.append(f"- {warning}")
            md.append("")

        md.append("---")
        md.append("")

        # Financial Performance
        md.append("## 1. Financial Performance")
        md.append("")

        md.append("### Revenue Summary")
        md.append("")
        if accounting['revenue_by_category']:
            for category, amount in sorted(accounting['revenue_by_category'].items(),
                                          key=lambda x: x[1], reverse=True):
                md.append(f"- **{category}:** ${amount:,.2f}")
        else:
            md.append("- No revenue recorded this week")
        md.append("")
        md.append(f"**Total Revenue:** ${accounting['revenue']:,.2f}")
        md.append("")

        md.append("### Expense Summary")
        md.append("")
        if accounting['expenses_by_category']:
            for category, amount in sorted(accounting['expenses_by_category'].items(),
                                          key=lambda x: x[1], reverse=True):
                md.append(f"- **{category}:** ${amount:,.2f}")
        else:
            md.append("- No expenses recorded this week")
        md.append("")
        md.append(f"**Total Expenses:** ${accounting['expenses']:,.2f}")
        md.append("")

        md.append("### Profit & Loss")
        md.append("")
        md.append(f"- **Net Profit:** ${accounting['net_profit']:,.2f}")
        profit_margin = (accounting['net_profit'] / accounting['revenue'] * 100) if accounting['revenue'] > 0 else 0
        md.append(f"- **Profit Margin:** {profit_margin:.1f}%")
        md.append("")

        md.append("---")
        md.append("")

        # Operational Metrics
        md.append("## 2. Operational Metrics")
        md.append("")

        audit = briefing['audit']
        md.append(f"- **Total System Events:** {audit['total_events']}")
        md.append(f"- **Skill Executions:** {audit['skill_executions']}")
        md.append(f"- **Skill Success Rate:** {(audit['skill_successes'] / max(audit['skill_executions'], 1) * 100):.1f}%")
        md.append(f"- **Escalations:** {audit['escalations']}")
        md.append(f"- **Email Actions:** {audit['email_actions']}")
        md.append("")

        if audit['events_by_type']:
            md.append("### Events by Type")
            md.append("")
            for event_type, count in sorted(audit['events_by_type'].items(),
                                           key=lambda x: x[1], reverse=True)[:5]:
                md.append(f"- **{event_type}:** {count}")
            md.append("")

        md.append("---")
        md.append("")

        # Workflow Status
        md.append("## 3. Workflow Status")
        md.append("")

        workflows = briefing['workflows']
        md.append(f"- **Needs Action:** {workflows['needs_action_count']} items")
        md.append(f"- **Pending Approval:** {workflows['pending_approval_count']} items")
        md.append(f"- **Escalations:** {workflows['escalation_count']} items")
        md.append("")

        if workflows['escalation_files']:
            md.append("### Recent Escalations")
            md.append("")
            for filename in workflows['escalation_files']:
                md.append(f"- `{filename}`")
            md.append("")

        md.append("---")
        md.append("")

        # System Health
        md.append("## 4. System Health")
        md.append("")

        health = briefing['health']
        md.append(f"**Overall Status:** {health['overall_status'].upper()}")
        md.append("")

        if health['components']:
            md.append("### Component Status")
            md.append("")
            for name, comp in health['components'].items():
                status_emoji = "✅" if comp['status'] == 'healthy' else "⚠️" if comp['status'] == 'degraded' else "❌"
                md.append(f"- {status_emoji} **{name}:** {comp['status']} - {comp['message']}")
            md.append("")

        retry = briefing['retry_queue']
        md.append(f"**RetryQueue:** {retry['queue_size']} items ({retry['status']})")
        md.append("")

        md.append("---")
        md.append("")

        # Recommendations
        md.append("## 5. Recommendations")
        md.append("")

        if briefing['recommendations']:
            for rec in briefing['recommendations']:
                md.append(f"- {rec}")
        else:
            md.append("- No specific recommendations at this time")

        md.append("")
        md.append("---")
        md.append("")

        # Footer
        md.append("## Notes")
        md.append("")
        md.append("This report was automatically generated by the weekly_ceo_briefing skill.")
        md.append("Data sources: Accounting ledger, Audit logs, StateManager, HealthMonitor, RetryQueue.")
        md.append("")
        md.append("For detailed information:")
        md.append("- Accounting: `Data/ledger.json`")
        md.append("- Audit logs: `Logs/audit.jsonl`")
        md.append("- System state: `Skills/integration_orchestrator/state.json`")
        md.append("")
        md.append("---")
        md.append("")
        md.append("*Generated by AI Employee Vault - Gold Tier*")

        return "\n".join(md)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Weekly CEO Briefing Skill')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode (no writes)')

    subparsers = parser.add_subparsers(dest='command', help='Command to execute')

    # Generate briefing
    generate_parser = subparsers.add_parser('generate', help='Generate CEO briefing')
    generate_parser.add_argument('--week', help='Week identifier (YYYY-WXX, defaults to current week)')

    args = parser.parse_args()

    # Determine base directory
    base_dir = Path(__file__).parent.parent.parent

    # Create briefing generator
    briefing = WeeklyCEOBriefing(base_dir, dry_run=args.dry_run)

    if args.dry_run:
        print("[DRY RUN MODE - No changes will be saved]")

    # Execute command
    if args.command == 'generate':
        result = briefing.generate_briefing(week_id=args.week)

        if result.get('status') == 'skipped':
            print(f"\nReport already exists for this week")
            sys.exit(0)

        print("\n" + "=" * 60)
        print("BRIEFING SUMMARY")
        print("=" * 60)
        print(f"Week: {result['week_id']}")
        print(f"Net Profit: ${result['accounting']['net_profit']:,.2f}")
        print(f"Warnings: {len(result['warnings'])}")
        print(f"Recommendations: {len(result['recommendations'])}")
        if result['report_file']:
            print(f"Report: Reports/Weekly/{result['report_file']}")
        print("=" * 60)

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
