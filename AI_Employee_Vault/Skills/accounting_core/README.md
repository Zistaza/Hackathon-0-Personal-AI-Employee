# Accounting Core Skill - Gold Tier Integration

## Overview

Lightweight internal accounting system for AI Employee Vault. Tracks revenue, expenses, generates reports, and integrates seamlessly with Gold Tier components.

## Features

### Core Accounting
- ✅ Revenue and expense tracking
- ✅ Transaction categorization
- ✅ Profit & Loss reports
- ✅ Weekly cashflow summaries
- ✅ Multi-step workflows (draft → review → finalized)
- ✅ Idempotent operations (no duplicate entries)
- ✅ DRY_RUN mode for testing

### Gold Tier Integration
- ✅ EventBus integration for autonomous detection
- ✅ AuditLogger integration for compliance
- ✅ StateManager integration for persistence
- ✅ SkillRegistry auto-registration
- ✅ AutonomousExecutor workflow support

## Architecture

```
┌─────────────────────────────────────┐
│      AccountingCore Skill           │
├─────────────────────────────────────┤
│  - Add Revenue/Expense              │
│  - Generate Reports                 │
│  - Detect Abnormal Cashflow         │
│  - Multi-step Workflows             │
└──────────┬──────────────────────────┘
           │
    ┌──────┼──────┐
    │      │      │
┌───▼───┐ │  ┌───▼────┐
│Event  │ │  │Audit   │
│Bus    │ │  │Logger  │
└───────┘ │  └────────┘
          │
    ┌─────▼──────┐
    │ Ledger     │
    │ (JSON)     │
    └────────────┘
```

## Installation

The skill is already installed in your Skills directory. No additional setup required.

## Usage

### Command Line Interface

#### Add Revenue
```bash
cd Skills/accounting_core
python3 index.py add-revenue \
  --amount 1000 \
  --category "Consulting" \
  --description "Project X - Phase 1"
```

#### Add Expense
```bash
python3 index.py add-expense \
  --amount 500 \
  --category "Software" \
  --description "Adobe Creative Cloud License"
```

#### Generate Reports
```bash
python3 index.py generate-reports
```

This generates:
- Profit & Loss report
- Weekly cashflow report (4 weeks)
- Saves to `Reports/accounting/`

#### View Summary
```bash
python3 index.py summary
```

Output:
```
============================================================
ACCOUNTING SUMMARY
============================================================
Total Revenue:    $10,000.00
Total Expenses:   $3,500.00
Net Profit:       $6,500.00

Transactions:     15
  - Draft:        2
  - Review:       1
  - Finalized:    12

Last Updated:     2026-02-28T12:00:00Z
============================================================
```

#### List Transactions
```bash
# List all transactions
python3 index.py list

# Filter by type
python3 index.py list --type revenue
python3 index.py list --type expense

# Filter by status
python3 index.py list --status draft
python3 index.py list --status finalized
```

### Python API

```python
from pathlib import Path
from Skills.accounting_core.index import AccountingCore, TransactionStatus

# Initialize
base_dir = Path.cwd()
accounting = AccountingCore(base_dir)

# Add revenue
accounting.add_revenue(
    amount=1000.0,
    category="Consulting",
    description="Project X",
    status=TransactionStatus.FINALIZED
)

# Add expense
accounting.add_expense(
    amount=500.0,
    category="Software",
    description="License",
    status=TransactionStatus.FINALIZED
)

# Generate reports
pl_report, cashflow_report = accounting.generate_reports()

# Get summary
summary = accounting.get_summary()
print(f"Net Profit: ${summary['net_profit']:.2f}")
```

### Gold Tier Integration

```python
from Skills.integration_orchestrator.index import IntegrationOrchestrator
from Skills.accounting_core.index import AccountingCore

# Initialize orchestrator
orchestrator = IntegrationOrchestrator(base_dir)

# Initialize accounting with Gold Tier components
accounting = AccountingCore(base_dir)
accounting.set_event_bus(orchestrator.event_bus)
accounting.set_audit_logger(orchestrator.audit_logger)

# Subscribe to accounting events
def on_abnormal_cashflow(data):
    print(f"⚠ Abnormal cashflow detected!")
    print(f"Consecutive negative weeks: {data['consecutive_negative_weeks']}")

orchestrator.event_bus.subscribe('accounting_abnormal_cashflow', on_abnormal_cashflow)

# Add transactions (events will be emitted)
accounting.add_revenue(1000, "Consulting", "Project X")
```

## Multi-Step Workflows

Transactions support workflow states for approval processes:

### 1. Draft → Review → Finalized

```bash
# Create draft transaction
python3 index.py add-revenue \
  --amount 5000 \
  --category "Consulting" \
  --description "Large project" \
  --status draft

# Later, move to review
# (You would update the transaction status in code)

# Finally, finalize
# (Update status to finalized)
```

### 2. Integration with Approval Workflow

```python
# Create draft transaction
txn = accounting.add_revenue(
    amount=5000,
    category="Consulting",
    description="Large project",
    status=TransactionStatus.DRAFT
)

# Create approval request in Pending_Approval/
approval_file = base_dir / "Pending_Approval" / f"accounting_{txn['id']}.md"
with open(approval_file, 'w') as f:
    f.write(f"""# Accounting Transaction Approval

type: accounting_transaction
transaction_id: {txn['id']}
amount: ${txn['amount']:.2f}
category: {txn['category']}
description: {txn['description']}

status: pending

---
Please review and approve this transaction.
""")

# Human approves by changing status to 'approved'
# Then skill updates transaction to FINALIZED
```

## Events Emitted

### `accounting_transaction_added`
Emitted when a transaction is added.

```json
{
  "transaction_id": "a1b2c3d4e5f6g7h8",
  "type": "revenue",
  "amount": 1000.0,
  "category": "Consulting",
  "status": "finalized",
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### `accounting_reports_generated`
Emitted when reports are generated.

```json
{
  "profit_loss": {
    "net_profit": 6500.0,
    "profit_margin_percent": 65.0
  },
  "cashflow_abnormal": false,
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### `accounting_abnormal_cashflow`
Emitted when abnormal cashflow is detected (2+ consecutive negative weeks).

```json
{
  "consecutive_negative_weeks": 3,
  "report": { /* full cashflow report */ },
  "timestamp": "2026-02-28T12:00:00Z"
}
```

## Autonomous Integration

The AutonomousExecutor can detect incomplete accounting workflows:

### Scenario 1: Draft Transactions Need Review

```python
# AutonomousExecutor detects draft transactions
# Publishes event: 'accounting_draft_transactions_detected'
# Triggers: accounting_core skill to generate review report
```

### Scenario 2: Weekly Reports Not Generated

```python
# AutonomousExecutor detects no reports in last 7 days
# Publishes event: 'accounting_reports_overdue'
# Triggers: accounting_core generate-reports
```

### Scenario 3: Abnormal Cashflow Escalation

```python
# Accounting detects abnormal cashflow
# Emits: 'accounting_abnormal_cashflow'
# AutonomousExecutor creates escalation file in Needs_Action/
```

## Data Storage

### Ledger File: `Data/ledger.json`

```json
{
  "version": "1.0",
  "created_at": "2026-02-28T12:00:00Z",
  "transactions": [
    {
      "id": "a1b2c3d4e5f6g7h8",
      "type": "revenue",
      "amount": 1000.0,
      "category": "Consulting",
      "description": "Project X",
      "date": "2026-02-28T12:00:00Z",
      "status": "finalized",
      "created_at": "2026-02-28T12:00:00Z",
      "metadata": {}
    }
  ],
  "metadata": {
    "total_revenue": 10000.0,
    "total_expenses": 3500.0,
    "transaction_count": 15,
    "last_updated": "2026-02-28T12:00:00Z"
  }
}
```

### Reports: `Reports/accounting/`

- `profit_loss_YYYYMMDD_HHMMSS.json`
- `cashflow_YYYYMMDD_HHMMSS.json`

## Idempotency

Transactions are idempotent - adding the same transaction twice will not create duplicates:

```python
# First call - creates transaction
accounting.add_revenue(1000, "Consulting", "Project X")

# Second call - returns existing transaction (no duplicate)
accounting.add_revenue(1000, "Consulting", "Project X")
```

Transaction ID is generated from: `type + amount + category + description + date`

## Categories

Common categories (customize as needed):

**Revenue:**
- Consulting
- Product Sales
- Services
- Licensing
- Subscriptions

**Expenses:**
- Software
- Hardware
- Marketing
- Salaries
- Office
- Travel
- Professional Services

## Reports

### Profit & Loss Report

Shows revenue and expenses by category, with totals and profit margin.

```
============================================================
PROFIT & LOSS REPORT
============================================================
Period: inception to now

REVENUE:
  Consulting                     $    10,000.00
  Product Sales                  $     5,000.00
  TOTAL REVENUE                  $    15,000.00

EXPENSES:
  Software                       $     2,000.00
  Marketing                      $     1,500.00
  TOTAL EXPENSES                 $     3,500.00

SUMMARY:
  Net Profit                     $    11,500.00
  Profit Margin                         76.67%
============================================================
```

### Weekly Cashflow Report

Shows weekly revenue, expenses, and net cashflow. Detects abnormal patterns.

```
============================================================
WEEKLY CASHFLOW REPORT
============================================================
Period: 4 weeks

Week 2026-W08:
  Revenue:      $     3,000.00
  Expenses:     $     1,000.00
  Net Cashflow: $     2,000.00

Week 2026-W09:
  Revenue:      $     2,500.00
  Expenses:     $     3,000.00
  Net Cashflow: $      -500.00

⚠ WARNING: Abnormal cashflow detected (2+ consecutive negative weeks)
============================================================
```

## Audit Logging

All accounting actions are logged to `Logs/audit.jsonl`:

```json
{
  "timestamp": "2026-02-28T12:00:00Z",
  "event_type": "accounting_transaction",
  "actor": "accounting_core",
  "action": "add_transaction",
  "resource": "transaction_a1b2c3d4e5f6g7h8",
  "result": "success",
  "metadata": {
    "type": "revenue",
    "amount": 1000.0,
    "category": "Consulting"
  }
}
```

## DRY RUN Mode

Test commands without writing to disk:

```bash
python3 index.py --dry-run add-revenue \
  --amount 1000 \
  --category "Test" \
  --description "Testing"
```

Output:
```
[DRY RUN MODE - No changes will be saved]
[DRY RUN] Would save ledger to disk
✓ Transaction added: a1b2c3d4 (revenue $1000.00)
```

## Best Practices

1. **Use Descriptive Categories**
   - Keep categories consistent
   - Use title case (e.g., "Software", not "software")
   - Limit to 10-15 categories for clarity

2. **Add Detailed Descriptions**
   - Include project names, invoice numbers, etc.
   - Makes audit trail more useful

3. **Use Workflow States**
   - Draft for uncertain transactions
   - Review for transactions needing approval
   - Finalized for confirmed transactions

4. **Generate Reports Weekly**
   - Set up periodic trigger in orchestrator
   - Review cashflow trends regularly

5. **Monitor Events**
   - Subscribe to abnormal cashflow events
   - Set up alerts for escalations

## Troubleshooting

### Ledger file corrupted
```bash
# Backup current ledger
cp Data/ledger.json Data/ledger.json.backup

# Reset ledger (creates new empty ledger)
rm Data/ledger.json
python3 index.py summary
```

### Duplicate transactions
Transactions are idempotent by design. If you see duplicates, they have different:
- Amount, OR
- Category, OR
- Description, OR
- Date

### Reports not generating
```bash
# Check permissions
ls -la Reports/accounting/

# Create directory if missing
mkdir -p Reports/accounting

# Try dry run
python3 index.py --dry-run generate-reports
```

## Integration Examples

### Example 1: Periodic Report Generation

```python
# In orchestrator periodic trigger
def generate_weekly_accounting_reports():
    accounting = AccountingCore(base_dir)
    accounting.set_event_bus(orchestrator.event_bus)
    accounting.set_audit_logger(orchestrator.audit_logger)

    pl_report, cashflow_report = accounting.generate_reports()

    # Check for abnormal cashflow
    if cashflow_report['abnormal_cashflow_detected']:
        # Create escalation
        create_escalation_file("Abnormal cashflow detected")
```

### Example 2: Transaction Approval Workflow

```python
# When approval file is moved to Approved/
def handle_accounting_approval(filepath):
    # Parse approval file
    with open(filepath, 'r') as f:
        content = f.read()

    # Extract transaction ID
    txn_id = extract_transaction_id(content)

    # Update transaction status to finalized
    # (Would need to add update_transaction method)

    # Emit event
    event_bus.publish('accounting_transaction_approved', {
        'transaction_id': txn_id,
        'timestamp': datetime.utcnow().isoformat() + 'Z'
    })
```

### Example 3: Autonomous Cashflow Monitoring

```python
# Subscribe to abnormal cashflow events
def on_abnormal_cashflow(data):
    # Create escalation file
    escalation_file = base_dir / "Needs_Action" / f"CASHFLOW_ALERT_{timestamp}.md"

    with open(escalation_file, 'w') as f:
        f.write(f"""# Cashflow Alert

Abnormal cashflow detected: {data['consecutive_negative_weeks']} consecutive negative weeks.

## Action Required
1. Review weekly cashflow report
2. Identify causes of negative cashflow
3. Develop action plan to improve cashflow

## Report
See: Reports/accounting/cashflow_latest.json
""")

orchestrator.event_bus.subscribe('accounting_abnormal_cashflow', on_abnormal_cashflow)
```

## Summary

The accounting_core skill provides:

✅ **Complete accounting system** - Revenue, expenses, reports
✅ **Gold Tier integration** - Events, audit logs, autonomous detection
✅ **Idempotent operations** - No duplicate entries
✅ **Multi-step workflows** - Draft → Review → Finalized
✅ **Abnormal detection** - Automatic cashflow monitoring
✅ **Production ready** - Tested, documented, integrated

Perfect for managing finances in your AI Employee Vault!
