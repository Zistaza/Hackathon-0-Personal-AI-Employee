# Weekly CEO Briefing - Quick Start Guide

## 5-Minute Setup

### 1. Verify Installation

```bash
cd Skills/weekly_ceo_briefing
python3 -c "from index import WeeklyCEOBriefing; print('✓ Import successful')"
```

### 2. Generate Your First Briefing

```bash
python3 index.py generate
```

Expected output:
```
Generating CEO Briefing for 2026-W09...
Week range: 2026-02-23 to 2026-03-01

1. Loading data sources...
   ✓ Loaded 145 audit log entries

2. Analyzing data...
   ✓ Analysis complete

3. Generating insights...
   ✓ 3 recommendations
   ✓ 1 risk warnings

4. Generating markdown report...
   ✓ Report saved: CEO_Briefing_2026_W09_20260228_120000.md

✓ CEO Briefing generated successfully
```

### 3. View the Report

```bash
cat Reports/Weekly/CEO_Briefing_*.md | head -50
```

### 4. Test Gold Tier Integration

```bash
python3 gold_tier_integration.py
```

## Common Commands

### Generate Current Week's Briefing
```bash
python3 index.py generate
```

### Generate for Specific Week
```bash
python3 index.py generate --week 2026-W08
```

### Dry Run (Test Without Saving)
```bash
python3 index.py --dry-run generate
```

## Python API Examples

### Basic Usage

```python
from pathlib import Path
from Skills.weekly_ceo_briefing.index import WeeklyCEOBriefing

# Initialize
base_dir = Path.cwd()
briefing = WeeklyCEOBriefing(base_dir)

# Generate briefing
result = briefing.generate_briefing()

# Print summary
print(f"Week: {result['week_id']}")
print(f"Net Profit: ${result['accounting']['net_profit']:,.2f}")
print(f"Warnings: {len(result['warnings'])}")
```

### With Gold Tier Integration

```python
from Skills.integration_orchestrator.index import IntegrationOrchestrator
from Skills.weekly_ceo_briefing.index import WeeklyCEOBriefing

# Initialize orchestrator
orchestrator = IntegrationOrchestrator(base_dir)

# Initialize briefing with Gold Tier
briefing = WeeklyCEOBriefing(base_dir)
briefing.set_event_bus(orchestrator.event_bus)
briefing.set_audit_logger(orchestrator.audit_logger)
briefing.set_orchestrator(orchestrator)

# Subscribe to events
def on_briefing(data):
    print(f"Briefing generated: {data['week_id']}")
    if data['warnings_count'] > 0:
        print(f"⚠️ {data['warnings_count']} warnings!")

orchestrator.event_bus.subscribe('ceo_briefing_generated', on_briefing)

# Generate briefing (event will be emitted)
briefing.generate_briefing()
```

## Report Sections

Every CEO briefing includes:

1. **Executive Summary** - Key metrics at a glance
2. **Financial Performance** - Revenue, expenses, P&L
3. **Operational Metrics** - System events, skill executions
4. **Workflow Status** - Pending items, escalations
5. **System Health** - Component status, retry queue
6. **Recommendations** - AI-generated suggestions
7. **Risk Warnings** - Critical issues requiring attention

## Understanding the Report

### Executive Summary
```markdown
- **Revenue:** $15,000.00
- **Expenses:** $5,500.00
- **Net Profit:** $9,500.00
- **Transactions:** 12
```

Quick snapshot of financial performance.

### Risk Warnings
```markdown
- 🔴 **CRITICAL:** Significant negative profit. Immediate action required.
- 🟡 **MEDIUM:** High skill failure rate (35%). Review skill implementations.
```

Color-coded by severity:
- 🔴 **CRITICAL** - Immediate action required
- 🟡 **MEDIUM** - Address within the week

### Recommendations
```markdown
- 💡 **High expense ratio (>80%).** Consider cost optimization opportunities.
- 🚨 **2 escalations require attention.** Review Needs_Action folder.
```

AI-generated based on data patterns.

## Autonomous Integration

### Weekly Automatic Generation

Add to AutonomousExecutor or PeriodicTrigger:

```python
def check_weekly_briefing():
    """Generate briefing if 7+ days since last one"""
    last_briefing = state_manager.get_system_state('last_ceo_briefing')

    if last_briefing:
        last_date = datetime.fromisoformat(last_briefing)
        days_since = (datetime.utcnow() - last_date).days

        if days_since >= 7:
            # Generate briefing
            briefing = WeeklyCEOBriefing(base_dir)
            briefing.set_event_bus(event_bus)
            briefing.set_audit_logger(audit_logger)
            briefing.set_orchestrator(orchestrator)

            briefing.generate_briefing()

            # Update state
            state_manager.set_system_state('last_ceo_briefing',
                                          datetime.utcnow().isoformat() + 'Z')
```

### Alert on Critical Warnings

```python
def on_briefing_generated(data):
    """Create alert if warnings detected"""
    if data['warnings_count'] > 0:
        alert_file = base_dir / "Needs_Action" / f"CEO_BRIEFING_ALERT_{timestamp}.md"

        with open(alert_file, 'w') as f:
            f.write(f"""# CEO Briefing Alert

Week {data['week_id']} contains {data['warnings_count']} warnings.

Review: Reports/Weekly/{data['report_file']}
""")

event_bus.subscribe('ceo_briefing_generated', on_briefing_generated)
```

## Data Sources

The briefing aggregates data from:

1. **Accounting** - `Data/ledger.json`
   - Revenue and expense transactions
   - Only finalized transactions included

2. **Audit Logs** - `Logs/audit.jsonl`
   - System events for the week
   - Skill executions and results

3. **StateManager** - `Skills/integration_orchestrator/state.json`
   - System state and metrics

4. **HealthMonitor** - Via orchestrator
   - Component health status

5. **RetryQueue** - Via orchestrator
   - Queue size and status

6. **Workflow Folders**
   - `Needs_Action/` - Pending items
   - `Pending_Approval/` - Awaiting approval
   - Escalation files

## Testing

Run the test suite:

```bash
python3 test_briefing.py
```

Expected output:
```
WEEKLY CEO BRIEFING TEST SUITE
==============================
✓ PASS: Basic Report Generation
✓ PASS: Idempotency
✓ PASS: Recommendations Generation
✓ PASS: Risk Warnings
✓ PASS: Gold Tier Integration
✓ PASS: DRY_RUN Mode
✓ PASS: Markdown Generation

Total: 7/7 tests passed
```

## Troubleshooting

### No Financial Data in Report

**Problem:** Report shows $0.00 for revenue/expenses

**Solutions:**
- Verify `Data/ledger.json` exists
- Check transactions are marked as "finalized"
- Ensure transactions are within the week date range

### No Audit Log Data

**Problem:** Operational metrics show 0 events

**Solutions:**
- Verify `Logs/audit.jsonl` exists
- Check file permissions
- Ensure audit logger is writing logs

### System Health Shows "Unknown"

**Problem:** Health status not available

**Solutions:**
- Pass orchestrator via `set_orchestrator()`
- Verify HealthMonitor is running
- Check components are registered

### Report Already Exists

**Problem:** Cannot generate report for current week

**Solutions:**
- This is expected (idempotency)
- Delete existing report to regenerate
- Use `--dry-run` to test

## Best Practices

1. **Generate Weekly**
   - Set up automatic generation every Monday
   - Review reports consistently

2. **Act on Warnings**
   - Critical warnings need immediate attention
   - Medium warnings should be addressed within the week

3. **Follow Recommendations**
   - AI recommendations are data-driven
   - Implement suggestions to improve performance

4. **Monitor Trends**
   - Compare week-over-week
   - Identify patterns early

5. **Archive Reports**
   - Keep for historical analysis
   - Archive reports older than 3 months

## Integration Examples

### Example 1: Monday Morning Briefing

```python
# Run every Monday at 9 AM
def monday_briefing():
    if datetime.utcnow().weekday() == 0:  # Monday
        briefing = WeeklyCEOBriefing(base_dir)
        briefing.set_event_bus(orchestrator.event_bus)
        briefing.set_audit_logger(orchestrator.audit_logger)
        briefing.set_orchestrator(orchestrator)

        briefing.generate_briefing()
```

### Example 2: Email to CEO

```python
def email_briefing(data):
    """Email report to CEO"""
    report_file = base_dir / "Reports" / "Weekly" / data['report_file']

    with open(report_file, 'r') as f:
        content = f.read()

    email_executor.send_email({
        'to': 'ceo@company.com',
        'subject': f"Weekly Briefing - {data['week_id']}",
        'body': content
    })

event_bus.subscribe('ceo_briefing_generated', email_briefing)
```

### Example 3: Slack Notification

```python
def slack_notification(data):
    """Send Slack notification with summary"""
    message = f"""📊 Weekly CEO Briefing - {data['week_id']}

Net Profit: ${data['net_profit']:,.2f}
Warnings: {data['warnings_count']}
Recommendations: {data['recommendations_count']}

View report: Reports/Weekly/{data['report_file']}
"""

    # Send to Slack (via webhook or API)
    send_slack_message(message)

event_bus.subscribe('ceo_briefing_generated', slack_notification)
```

## Summary

The weekly_ceo_briefing skill provides:

✅ **Comprehensive reporting** - All business metrics in one place
✅ **Gold Tier integration** - Aggregates from all components
✅ **AI insights** - Intelligent recommendations and warnings
✅ **Idempotent** - No duplicate reports
✅ **Autonomous** - Can be triggered automatically
✅ **Executive-ready** - Professional markdown format

Perfect for weekly business reviews and data-driven decision making!

## Next Steps

1. **Generate Your First Report**
   ```bash
   python3 index.py generate
   ```

2. **Review the Report**
   ```bash
   cat Reports/Weekly/CEO_Briefing_*.md
   ```

3. **Set Up Autonomous Generation**
   - Add weekly trigger to AutonomousExecutor
   - Configure event handlers

4. **Configure Notifications**
   - Set up email delivery
   - Add Slack/Teams integration

5. **Act on Insights**
   - Address warnings
   - Implement recommendations
   - Monitor trends

You're ready to generate executive-level business reports automatically!
