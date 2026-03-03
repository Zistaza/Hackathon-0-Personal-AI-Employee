# Weekly CEO Briefing Skill - Gold Tier Integration

## Overview

Generates comprehensive executive-level business reports by aggregating data from all Gold Tier components. Provides a single weekly snapshot of business performance, system health, and operational metrics.

## Features

### Data Aggregation
- ✅ Accounting data (revenue, expenses, P&L, cashflow)
- ✅ Audit logs (system activity, skill executions)
- ✅ Workflow status (pending items, escalations)
- ✅ RetryQueue statistics
- ✅ System health status (HealthMonitor)
- ✅ StateManager metrics

### Report Sections
- ✅ Executive Summary
- ✅ Financial Performance (revenue, expenses, P&L)
- ✅ Operational Metrics (events, skill executions)
- ✅ Workflow Status (pending, escalations)
- ✅ System Health (component status, retry queue)
- ✅ AI-Generated Recommendations
- ✅ Risk Warnings

### Gold Tier Integration
- ✅ Aggregates from all Gold Tier components
- ✅ EventBus integration (emits events)
- ✅ AuditLogger integration (logs generation)
- ✅ SkillRegistry compatible
- ✅ AutonomousExecutor triggering support
- ✅ Idempotent (no duplicate weekly reports)
- ✅ DRY_RUN mode

## Architecture

```
┌─────────────────────────────────────────┐
│    WeeklyCEOBriefing Skill              │
├─────────────────────────────────────────┤
│  Data Sources:                          │
│  - Accounting (ledger.json)             │
│  - Audit Logs (audit.jsonl)             │
│  - StateManager (state.json)            │
│  - HealthMonitor (via orchestrator)     │
│  - RetryQueue (via orchestrator)        │
│  - Workflow folders (Needs_Action, etc) │
└──────────┬──────────────────────────────┘
           │
    ┌──────┼──────┐
    │      │      │
┌───▼───┐ │  ┌───▼────┐
│Event  │ │  │Audit   │
│Bus    │ │  │Logger  │
└───────┘ │  └────────┘
          │
    ┌─────▼──────┐
    │ Markdown   │
    │ Report     │
    └────────────┘
```

## Installation

The skill is already installed in your Skills directory. No additional setup required.

## Usage

### Command Line Interface

#### Generate Current Week's Briefing
```bash
cd Skills/weekly_ceo_briefing
python3 index.py generate
```

Output:
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

#### Generate for Specific Week
```bash
python3 index.py generate --week 2026-W08
```

#### Dry Run (Test Without Saving)
```bash
python3 index.py --dry-run generate
```

### Python API

```python
from pathlib import Path
from Skills.weekly_ceo_briefing.index import WeeklyCEOBriefing

# Initialize
base_dir = Path.cwd()
briefing = WeeklyCEOBriefing(base_dir)

# Generate current week's briefing
result = briefing.generate_briefing()

print(f"Net Profit: ${result['accounting']['net_profit']:.2f}")
print(f"Warnings: {len(result['warnings'])}")
print(f"Report: {result['report_file']}")
```

### Gold Tier Integration

```python
from Skills.integration_orchestrator.index import IntegrationOrchestrator
from Skills.weekly_ceo_briefing.index import WeeklyCEOBriefing

# Initialize orchestrator
orchestrator = IntegrationOrchestrator(base_dir)

# Initialize briefing with Gold Tier components
briefing = WeeklyCEOBriefing(base_dir)
briefing.set_event_bus(orchestrator.event_bus)
briefing.set_audit_logger(orchestrator.audit_logger)
briefing.set_orchestrator(orchestrator)  # For direct component access

# Subscribe to events
def on_briefing_generated(data):
    print(f"CEO Briefing generated for {data['week_id']}")
    print(f"Net Profit: ${data['net_profit']:.2f}")
    if data['warnings_count'] > 0:
        print(f"⚠️ {data['warnings_count']} warnings!")

orchestrator.event_bus.subscribe('ceo_briefing_generated', on_briefing_generated)

# Generate briefing (event will be emitted)
briefing.generate_briefing()
```

## Report Format

### Example Report Structure

```markdown
# Weekly CEO Briefing

**Week:** 2026-W09
**Period:** 2026-02-23 to 2026-03-01
**Generated:** 2026-02-28T12:00:00Z

---

## Executive Summary

- **Revenue:** $15,000.00
- **Expenses:** $5,500.00
- **Net Profit:** $9,500.00
- **Transactions:** 12

### ⚠️ Risk Warnings

- 🟡 **MEDIUM: High skill failure rate (35%).** Review skill implementations.

---

## 1. Financial Performance

### Revenue Summary

- **Consulting:** $10,000.00
- **Product Sales:** $5,000.00

**Total Revenue:** $15,000.00

### Expense Summary

- **Software:** $2,500.00
- **Marketing:** $2,000.00
- **Office:** $1,000.00

**Total Expenses:** $5,500.00

### Profit & Loss

- **Net Profit:** $9,500.00
- **Profit Margin:** 63.3%

---

## 2. Operational Metrics

- **Total System Events:** 145
- **Skill Executions:** 23
- **Skill Success Rate:** 65.2%
- **Escalations:** 2
- **Email Actions:** 5

### Events by Type

- **skill_execution:** 23
- **accounting_transaction:** 12
- **email_action:** 5
- **escalation:** 2
- **system_lifecycle:** 2

---

## 3. Workflow Status

- **Needs Action:** 3 items
- **Pending Approval:** 1 items
- **Escalations:** 2 items

### Recent Escalations

- `ESCALATION_20260227_143022_process_needs_action.md`
- `CASHFLOW_ALERT_20260226_091500.md`

---

## 4. System Health

**Overall Status:** HEALTHY

### Component Status

- ✅ **state_manager:** healthy - State manager operational
- ✅ **skill_dispatcher:** healthy - Skill dispatcher operational
- ✅ **email_executor:** healthy - Email executor operational
- ⚠️ **retry_queue:** degraded - Retry queue large: 15 items
- ✅ **filesystem_watcher:** healthy - Filesystem watcher operational
- ✅ **autonomous_executor:** healthy - Autonomous executor operational (2 tracked tasks)

**RetryQueue:** 15 items (elevated)

---

## 5. Recommendations

- 💡 **High expense ratio (>80%).** Consider cost optimization opportunities.
- 🚨 **2 escalations require attention.** Review Needs_Action folder.
- 🔄 **RetryQueue has 15 items.** Investigate recurring failures.
- ⚠️ **More skill failures than successes.** Review error logs and fix failing skills.

---

## Notes

This report was automatically generated by the weekly_ceo_briefing skill.
Data sources: Accounting ledger, Audit logs, StateManager, HealthMonitor, RetryQueue.

For detailed information:
- Accounting: `Data/ledger.json`
- Audit logs: `Logs/audit.jsonl`
- System state: `Skills/integration_orchestrator/state.json`

---

*Generated by AI Employee Vault - Gold Tier*
```

## Data Sources

### 1. Accounting Data (`Data/ledger.json`)
- Revenue and expense transactions
- Transaction categories
- Finalized transactions only

### 2. Audit Logs (`Logs/audit.jsonl`)
- System events
- Skill executions
- Escalations
- Email actions

### 3. StateManager (`Skills/integration_orchestrator/state.json`)
- System state
- Metrics
- Last updated timestamps

### 4. HealthMonitor (via orchestrator)
- Component health status
- Overall system health
- Component messages

### 5. RetryQueue (via orchestrator)
- Queue size
- Status (normal/elevated/critical)

### 6. Workflow Folders
- `Needs_Action/` - Pending items
- `Pending_Approval/` - Items awaiting approval
- Escalation files (ESCALATION_*.md)

## Idempotency

Reports are idempotent - generating a report for the same week twice will skip the second generation:

```python
# First call - generates report
briefing.generate_briefing(week_id='2026-W09')

# Second call - skips (report already exists)
briefing.generate_briefing(week_id='2026-W09')
```

Report files are named with week identifier to prevent duplicates:
- `CEO_Briefing_2026_W09_20260228_120000.md`

## AI-Generated Insights

### Recommendations

The skill generates intelligent recommendations based on:
- **Financial performance** - Negative profit, high expenses, no revenue
- **Workflow status** - Escalations, pending approvals
- **System health** - Degraded/unhealthy components
- **RetryQueue** - High queue size
- **Skill performance** - High failure rates

### Risk Warnings

Critical warnings are generated for:
- **🔴 CRITICAL** - Significant negative profit, system unhealthy, retry queue overloaded
- **🟡 MEDIUM** - High skill failure rate, multiple escalations

## Autonomous Integration

### Automatic Weekly Generation

The AutonomousExecutor can automatically trigger weekly briefings:

```python
# In AutonomousExecutor._check_pending_workflows()

def check_weekly_briefing():
    """Check if weekly briefing is due"""
    # Get last briefing date from state
    last_briefing = state_manager.get_system_state('last_ceo_briefing')

    if last_briefing:
        last_date = datetime.fromisoformat(last_briefing)
        days_since = (datetime.utcnow() - last_date).days

        # If 7+ days since last briefing, trigger generation
        if days_since >= 7:
            event_bus.publish('weekly_briefing_due', {
                'days_since_last': days_since,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

            # Trigger skill
            skill_registry.execute_skill('weekly_ceo_briefing', ['generate'])

            # Update state
            state_manager.set_system_state('last_ceo_briefing',
                                          datetime.utcnow().isoformat() + 'Z')
```

### Event-Driven Triggering

Subscribe to trigger events:

```python
def on_week_end(data):
    """Generate briefing at end of week"""
    briefing = WeeklyCEOBriefing(base_dir)
    briefing.set_event_bus(orchestrator.event_bus)
    briefing.set_audit_logger(orchestrator.audit_logger)
    briefing.set_orchestrator(orchestrator)

    briefing.generate_briefing()

# Subscribe to week-end event
orchestrator.event_bus.subscribe('week_end', on_week_end)
```

## Events Emitted

### `ceo_briefing_generated`

Emitted when a briefing is successfully generated.

```json
{
  "week_id": "2026-W09",
  "net_profit": 9500.0,
  "warnings_count": 1,
  "recommendations_count": 4,
  "report_file": "CEO_Briefing_2026_W09_20260228_120000.md",
  "timestamp": "2026-02-28T12:00:00Z"
}
```

## Audit Logging

All briefing generations are logged to `Logs/audit.jsonl`:

```json
{
  "timestamp": "2026-02-28T12:00:00Z",
  "event_type": "ceo_briefing",
  "actor": "weekly_ceo_briefing",
  "action": "generate_briefing",
  "resource": "briefing_2026-W09",
  "result": "success",
  "metadata": {
    "week_id": "2026-W09",
    "net_profit": 9500.0,
    "warnings_count": 1
  }
}
```

## Report Storage

Reports are stored in `Reports/Weekly/`:

```
Reports/Weekly/
├── CEO_Briefing_2026_W08_20260221_090000.md
├── CEO_Briefing_2026_W09_20260228_120000.md
└── CEO_Briefing_2026_W10_20260307_090000.md
```

## Best Practices

1. **Generate Weekly**
   - Set up automatic generation every Monday morning
   - Review reports regularly for trends

2. **Act on Warnings**
   - Critical warnings require immediate attention
   - Medium warnings should be addressed within the week

3. **Follow Recommendations**
   - AI recommendations are based on data patterns
   - Implement suggestions to improve performance

4. **Monitor Trends**
   - Compare week-over-week performance
   - Identify patterns in revenue, expenses, and system health

5. **Archive Old Reports**
   - Keep reports for historical analysis
   - Archive reports older than 3 months

## Troubleshooting

### No Data in Report

**Problem:** Report shows zero revenue/expenses

**Solutions:**
- Verify `Data/ledger.json` exists and has transactions
- Check that transactions are marked as "finalized"
- Ensure transactions are within the week date range

### Missing System Health Data

**Problem:** System health shows "unknown"

**Solutions:**
- Ensure orchestrator is passed via `set_orchestrator()`
- Verify HealthMonitor is running
- Check that components are registered

### Report Already Exists Error

**Problem:** Cannot generate report for current week

**Solutions:**
- This is expected behavior (idempotency)
- Delete existing report if you want to regenerate
- Use `--dry-run` to test without creating files

### Audit Logs Not Loading

**Problem:** Operational metrics show zero events

**Solutions:**
- Verify `Logs/audit.jsonl` exists
- Check file permissions
- Ensure audit logger is writing to correct location

## Integration Examples

### Example 1: Automatic Monday Morning Briefing

```python
# In orchestrator periodic trigger
def monday_morning_briefing():
    """Generate CEO briefing every Monday at 9 AM"""
    now = datetime.utcnow()

    # Check if Monday
    if now.weekday() == 0:  # Monday
        briefing = WeeklyCEOBriefing(base_dir)
        briefing.set_event_bus(orchestrator.event_bus)
        briefing.set_audit_logger(orchestrator.audit_logger)
        briefing.set_orchestrator(orchestrator)

        briefing.generate_briefing()
```

### Example 2: Alert on Critical Warnings

```python
def on_briefing_generated(data):
    """Send alert if critical warnings detected"""
    if data['warnings_count'] > 0:
        # Create alert in Needs_Action
        alert_file = base_dir / "Needs_Action" / f"CEO_BRIEFING_ALERT_{timestamp}.md"

        with open(alert_file, 'w') as f:
            f.write(f"""# CEO Briefing Alert

Week {data['week_id']} briefing contains {data['warnings_count']} warnings.

Review: Reports/Weekly/{data['report_file']}

Action required: Address critical issues identified in the briefing.
""")

orchestrator.event_bus.subscribe('ceo_briefing_generated', on_briefing_generated)
```

### Example 3: Email Briefing to CEO

```python
def email_briefing_to_ceo(data):
    """Email briefing report to CEO"""
    # Read report file
    report_file = base_dir / "Reports" / "Weekly" / data['report_file']

    with open(report_file, 'r') as f:
        report_content = f.read()

    # Send email (via email_executor or MCP)
    email_executor.send_email({
        'to': 'ceo@company.com',
        'subject': f"Weekly CEO Briefing - {data['week_id']}",
        'body': report_content
    })

orchestrator.event_bus.subscribe('ceo_briefing_generated', email_briefing_to_ceo)
```

## Summary

The weekly_ceo_briefing skill provides:

✅ **Comprehensive reporting** - All business and system metrics in one place
✅ **Gold Tier integration** - Aggregates from all components
✅ **AI insights** - Intelligent recommendations and risk warnings
✅ **Idempotent** - No duplicate reports
✅ **Autonomous** - Can be triggered automatically
✅ **Executive-ready** - Professional markdown format
✅ **Production ready** - Tested, documented, integrated

Perfect for weekly business reviews and executive decision-making!
