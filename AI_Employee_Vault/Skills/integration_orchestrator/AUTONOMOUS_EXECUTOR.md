# AutonomousExecutor - Autonomous Execution Layer

## Overview

The AutonomousExecutor (nicknamed "Ralph Wiggum Loop") is a continuous monitoring system that detects incomplete work and automatically triggers appropriate actions without manual intervention.

## Key Features

### 1. Continuous Monitoring
- Runs in background thread with configurable check interval (default: 30 seconds)
- Monitors system state, retry queue, pending workflows, and incomplete tasks
- Respects system health - pauses when system is unhealthy

### 2. Automatic Detection
Detects:
- Files in `Needs_Action/` directory
- Files in `Inbox/` directory
- Stale files in `Pending_Approval/` (>1 hour old)
- Items in RetryQueue
- Incomplete multi-step workflows

### 3. Intelligent Action Triggering
- Publishes events to EventBus when unfinished work detected
- Automatically triggers appropriate skills via SkillRegistry
- Prevents duplicate triggers (5-minute cooldown per skill/context)
- Tracks execution results and failure counts

### 4. Failure Escalation
- Tracks failures per task/context
- Escalates to human after threshold exceeded (default: 3 failures)
- Creates detailed escalation file in `Needs_Action/`
- Logs escalation to AuditLogger
- Resets failure count after escalation

### 5. Graceful Shutdown
- Clean thread termination
- Respects stop signals
- No orphaned processes

## Architecture Integration

```
┌─────────────────────────────────────┐
│    IntegrationOrchestrator          │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
┌───▼───┐  ┌──▼───┐  ┌───▼────┐
│Event  │  │Retry │  │Health  │
│Bus    │  │Queue │  │Monitor │
└───┬───┘  └──┬───┘  └───┬────┘
    │         │          │
    └─────────┼──────────┘
              │
      ┌───────▼────────┐
      │  Autonomous    │
      │   Executor     │
      │ (Ralph Wiggum) │
      └────────────────┘
              │
      ┌───────▼────────┐
      │ SkillRegistry  │
      └────────────────┘
```

## Configuration

```python
autonomous_executor = AutonomousExecutor(
    event_bus=event_bus,
    retry_queue=retry_queue,
    state_manager=state_manager,
    health_monitor=health_monitor,
    skill_registry=skill_registry,
    audit_logger=audit_logger,
    base_dir=base_dir,
    logger=logger,
    check_interval=30,      # Seconds between checks
    failure_threshold=3     # Max failures before escalation
)
```

## Usage

### Starting the Orchestrator
The AutonomousExecutor starts automatically when you start the orchestrator:

```python
orchestrator = IntegrationOrchestrator(base_dir)
orchestrator.start()  # AutonomousExecutor starts automatically
```

### Checking Status

```python
# Get autonomous executor status
status = orchestrator.autonomous_executor.get_status()
print(f"Running: {status['running']}")
print(f"Tracked tasks: {status['tracked_tasks']}")
print(f"Last check: {status['last_check']}")

# Get full orchestrator status (includes autonomous executor)
full_status = orchestrator.get_status()
print(full_status['autonomous_executor'])

# Get health report (includes autonomous executor health)
print(orchestrator.get_health_report())
```

### Monitoring Events

Subscribe to events published by AutonomousExecutor:

```python
def on_workflow_detected(data):
    print(f"Unfinished workflow: {data['location']}")
    print(f"File count: {data['file_count']}")

def on_escalation(data):
    print(f"Task escalated: {data['skill_name']}")
    print(f"Failure count: {data['failure_count']}")

orchestrator.event_bus.subscribe('unfinished_workflow_detected', on_workflow_detected)
orchestrator.event_bus.subscribe('task_escalated', on_escalation)
```

## Events Published

### `unfinished_workflow_detected`
```json
{
  "location": "Needs_Action",
  "file_count": 3,
  "files": ["file1.md", "file2.md", "file3.md"],
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### `retry_queue_status`
```json
{
  "queue_size": 5,
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### `stale_approval_detected`
```json
{
  "filepath": "/path/to/file.md",
  "filename": "approval_request.md",
  "age_hours": 2.5,
  "timestamp": "2026-02-28T12:00:00Z"
}
```

### `task_escalated`
```json
{
  "skill_name": "process_needs_action",
  "context": "needs_action_files_detected",
  "failure_count": 3,
  "escalation_file": "/path/to/ESCALATION_file.md",
  "timestamp": "2026-02-28T12:00:00Z"
}
```

## Escalation Files

When a task fails repeatedly, AutonomousExecutor creates an escalation file in `Needs_Action/`:

```
ESCALATION_20260228_120000_process_needs_action.md
```

The file contains:
- Summary of the failure
- Skill name and context
- Failure count
- Last execution result (error, stderr, return code)
- Recommended actions
- System status information

## Health Monitoring

AutonomousExecutor is monitored by HealthMonitor:

- **Healthy**: Running with <5 tracked failures
- **Degraded**: Running with 5+ tracked failures
- **Unhealthy**: Not running or error state

Check health:
```python
health = orchestrator.health_monitor.get_component_status('autonomous_executor')
print(f"Status: {health['status']}")
print(f"Message: {health['message']}")
```

## Audit Logging

All autonomous actions are logged to `Logs/audit.jsonl`:

```json
{
  "timestamp": "2026-02-28T12:00:00Z",
  "event_type": "autonomous_execution",
  "actor": "autonomous_executor",
  "action": "trigger_skill",
  "resource": "process_needs_action",
  "result": "success",
  "metadata": {
    "context": "needs_action_files_detected"
  }
}
```

Escalations are also logged:
```json
{
  "timestamp": "2026-02-28T12:00:00Z",
  "event_type": "escalation",
  "actor": "autonomous_executor",
  "action": "escalate_to_human",
  "resource": "process_needs_action",
  "result": "escalated",
  "metadata": {
    "context": "needs_action_files_detected",
    "failure_count": 3,
    "escalation_file": "ESCALATION_20260228_120000_process_needs_action.md",
    "error": "Execution timeout"
  }
}
```

## Testing

Run the test suite:

```bash
cd Skills/integration_orchestrator
python3 test_autonomous_executor.py
```

Tests include:
1. Autonomous detection of unfinished work
2. Failure escalation mechanism
3. Health monitoring integration
4. EventBus integration

## Best Practices

1. **Monitor Escalations**: Check `Needs_Action/` regularly for escalation files
2. **Review Audit Logs**: Query audit logs to understand autonomous behavior
3. **Tune Check Interval**: Adjust based on your workload (30s default is reasonable)
4. **Set Appropriate Threshold**: 3 failures is a good default, adjust if needed
5. **Subscribe to Events**: Monitor key events for visibility into autonomous actions

## Troubleshooting

### AutonomousExecutor not running
```python
status = orchestrator.autonomous_executor.get_status()
if not status['running']:
    # Check logs for errors
    # Verify orchestrator is started
    # Check health monitor status
```

### Too many escalations
- Check system health
- Review skill implementations for bugs
- Increase failure threshold if transient failures are common
- Check retry queue size

### Not detecting work
- Verify check interval is appropriate
- Check that files are in monitored directories
- Review logs for detection events
- Verify EventBus subscriptions are working

## Integration with Existing Gold Tier

AutonomousExecutor seamlessly integrates with all Gold Tier components:

- **EventBus**: Publishes detection and escalation events
- **RetryQueue**: Monitors queue size and adds failed operations
- **StateManager**: Tracks last check time and metrics
- **HealthMonitor**: Provides health status
- **SkillRegistry**: Triggers skills with retry and audit
- **AuditLogger**: Logs all autonomous actions
- **GracefulDegradation**: Respects system health status

## Summary

The AutonomousExecutor provides true autonomous operation by:
- Continuously monitoring for incomplete work
- Automatically triggering appropriate actions
- Intelligently handling failures with escalation
- Maintaining system momentum without manual intervention
- Integrating seamlessly with all Gold Tier components

This enables your AI Employee Vault to operate autonomously, handling routine tasks and escalating only when human intervention is truly needed.
