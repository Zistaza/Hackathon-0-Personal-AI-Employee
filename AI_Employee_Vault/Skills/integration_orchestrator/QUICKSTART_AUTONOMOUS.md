# Quick Start: AutonomousExecutor

## 5-Minute Setup

### 1. Verify Installation

The AutonomousExecutor is already integrated into your Gold Tier orchestrator. No additional installation needed!

```bash
cd Skills/integration_orchestrator
python3 -c "from index import IntegrationOrchestrator, AutonomousExecutor; print('✓ Import successful')"
```

### 2. Start the Orchestrator

```bash
cd /path/to/AI_Employee_Vault
python3 Skills/integration_orchestrator/index.py
```

You should see:
```
[2026-02-28 12:00:00] [integration_orchestrator] [INFO] AutonomousExecutor initialized
[2026-02-28 12:00:00] [integration_orchestrator] [INFO] AutonomousExecutor started (check interval: 30s)
```

### 3. Test Autonomous Detection

Create a test file in `Needs_Action/`:

```bash
cat > Needs_Action/test_task.md << 'EOF'
# Test Task

This is a test to verify autonomous detection.

type: test
status: pending
EOF
```

Within 30 seconds, the AutonomousExecutor will:
1. Detect the file
2. Publish an event
3. Trigger the `process_needs_action` skill

Check the logs:
```bash
tail -f Logs/integration_orchestrator.log | grep -i autonomous
```

### 4. Monitor Status

In a Python shell:

```python
from pathlib import Path
from Skills.integration_orchestrator.index import IntegrationOrchestrator

base_dir = Path.cwd()
orchestrator = IntegrationOrchestrator(base_dir)

# Check autonomous executor status
status = orchestrator.autonomous_executor.get_status()
print(f"Running: {status['running']}")
print(f"Check interval: {status['check_interval']}s")
print(f"Tracked tasks: {status['tracked_tasks']}")
```

### 5. View Health Report

```python
print(orchestrator.get_health_report())
```

Look for the `autonomous_executor` section:
```
Component Health:
  - autonomous_executor: healthy - Autonomous executor operational (0 tracked tasks)
```

## Common Use Cases

### Use Case 1: Automatic Task Processing

**Scenario:** Files appear in `Needs_Action/` and need processing

**What happens:**
1. AutonomousExecutor detects files every 30s
2. Publishes `unfinished_workflow_detected` event
3. Triggers `process_needs_action` skill
4. Tracks success/failure

**No manual intervention needed!**

### Use Case 2: Failure Escalation

**Scenario:** A skill fails repeatedly

**What happens:**
1. First failure: Added to RetryQueue
2. Second failure: Retry with backoff
3. Third failure: Escalated to human
4. Creates `ESCALATION_*.md` in `Needs_Action/`

**You only see it when human attention is needed!**

### Use Case 3: Stale Approval Detection

**Scenario:** Approval request sits in `Pending_Approval/` for hours

**What happens:**
1. AutonomousExecutor detects file age >1 hour
2. Publishes `stale_approval_detected` event
3. Logs to audit trail
4. You can subscribe to event for notifications

**Prevents forgotten approvals!**

## Configuration

### Adjust Check Interval

Edit `index.py` line ~1975:

```python
self.autonomous_executor = AutonomousExecutor(
    # ... other params ...
    check_interval=60,  # Change from 30 to 60 seconds
    failure_threshold=3
)
```

### Adjust Failure Threshold

```python
self.autonomous_executor = AutonomousExecutor(
    # ... other params ...
    check_interval=30,
    failure_threshold=5  # Change from 3 to 5 failures
)
```

## Monitoring

### Real-time Event Monitoring

```python
def log_all_events(data):
    print(f"Event: {data}")

# Subscribe to all autonomous events
orchestrator.event_bus.subscribe('unfinished_workflow_detected', log_all_events)
orchestrator.event_bus.subscribe('retry_queue_status', log_all_events)
orchestrator.event_bus.subscribe('stale_approval_detected', log_all_events)
orchestrator.event_bus.subscribe('task_escalated', log_all_events)
```

### Check Audit Logs

```bash
# View recent autonomous actions
tail -20 Logs/audit.jsonl | grep autonomous_executor
```

### Check for Escalations

```bash
# List escalation files
ls -lh Needs_Action/ESCALATION_*.md
```

## Troubleshooting

### AutonomousExecutor Not Running

```python
status = orchestrator.autonomous_executor.get_status()
if not status['running']:
    print("Not running! Check logs for errors")
    # Restart orchestrator
```

### Too Many Escalations

```bash
# Check how many escalations
ls Needs_Action/ESCALATION_*.md | wc -l

# Review recent escalations
cat Needs_Action/ESCALATION_*.md | head -50
```

**Solutions:**
- Increase `failure_threshold`
- Fix underlying skill issues
- Check system health

### Not Detecting Files

**Check:**
1. Files are in monitored directories (`Needs_Action/`, `Inbox/`)
2. Files have `.md` extension
3. Check interval hasn't been set too high
4. Orchestrator is running

```bash
# Verify orchestrator is running
ps aux | grep integration_orchestrator
```

## Advanced Usage

### Custom Event Handlers

```python
def handle_escalation(data):
    """Send notification when task escalates"""
    skill_name = data['skill_name']
    failure_count = data['failure_count']

    # Send email, Slack message, etc.
    print(f"ALERT: {skill_name} failed {failure_count} times!")

orchestrator.event_bus.subscribe('task_escalated', handle_escalation)
```

### Query Autonomous Actions

```python
from datetime import datetime, timedelta

# Get autonomous actions from last hour
start_time = datetime.utcnow() - timedelta(hours=1)
actions = orchestrator.audit_logger.query_logs(
    event_type='autonomous_execution',
    start_time=start_time,
    limit=100
)

for action in actions:
    print(f"{action['timestamp']}: {action['resource']} - {action['result']}")
```

### Programmatic Control

```python
# Stop autonomous executor temporarily
orchestrator.autonomous_executor.stop()

# Do manual work...

# Restart
orchestrator.autonomous_executor.start()
```

## Best Practices

1. **Monitor Escalations Daily**
   - Check `Needs_Action/ESCALATION_*.md` files
   - Resolve underlying issues
   - Delete escalation files after resolution

2. **Review Audit Logs Weekly**
   - Look for patterns in failures
   - Identify skills that need improvement
   - Verify autonomous actions are appropriate

3. **Tune Configuration**
   - Start with defaults (30s interval, 3 failure threshold)
   - Adjust based on your workload
   - Lower interval = more responsive, higher CPU
   - Higher threshold = fewer escalations, longer to detect issues

4. **Subscribe to Key Events**
   - `task_escalated` - Critical, needs attention
   - `stale_approval_detected` - Important, prevents delays
   - `unfinished_workflow_detected` - Informational

5. **Health Monitoring**
   - Check health report regularly
   - Watch for degraded status
   - Investigate unhealthy components immediately

## Testing

Run the test suite to verify everything works:

```bash
cd Skills/integration_orchestrator
python3 test_autonomous_executor.py
```

Expected output:
```
AUTONOMOUS EXECUTOR TEST SUITE
==============================
✓ PASS: Autonomous Detection
✓ PASS: Failure Escalation
✓ PASS: Health Monitoring
✓ PASS: EventBus Integration

Total: 4/4 tests passed
```

## Summary

The AutonomousExecutor provides:

✓ **Automatic detection** of incomplete work
✓ **Intelligent retry** with failure tracking
✓ **Human escalation** when needed
✓ **Zero configuration** - works out of the box
✓ **Full observability** - events, logs, health checks

Just start the orchestrator and let it run autonomously!

## Need Help?

- Check `AUTONOMOUS_EXECUTOR.md` for detailed documentation
- Review `IMPLEMENTATION_COMPLETE.md` for technical details
- Run `test_autonomous_executor.py` to verify functionality
- Check logs in `Logs/integration_orchestrator.log`
- Review audit trail in `Logs/audit.jsonl`
