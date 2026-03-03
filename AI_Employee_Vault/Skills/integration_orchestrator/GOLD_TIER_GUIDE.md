# Gold Tier Architecture - Usage Guide

## Overview

The Integration Orchestrator has been upgraded to Gold Tier architecture with enterprise-grade features while preserving all existing functionality.

## New Components

### 1. EventBus - Central Pub/Sub System

**Purpose**: Decouples components through event-driven communication.

**Events Published**:
- `skill_execution_started` - When a skill begins execution
- `skill_execution_completed` - When a skill finishes (success or failure)
- `needs_action_detected` - When a file appears in Needs_Action
- `approval_detected` - When an approval is detected
- `email_approved` - When an email is approved for sending
- `email_sent` - When an email is successfully sent
- `email_failed` - When email sending fails

**Usage Example**:
```python
# Subscribe to events
def on_email_sent(data):
    print(f"Email sent to: {data['to']}")

orchestrator.event_bus.subscribe('email_sent', on_email_sent)

# Publish custom events
orchestrator.event_bus.publish('custom_event', {
    'key': 'value',
    'timestamp': datetime.utcnow().isoformat()
})
```

### 2. SkillRegistry - Enhanced Skill Management

**Purpose**: Wraps SkillDispatcher with retry, audit, and metadata tracking.

**Features**:
- Automatic retry on failure
- Structured audit logging
- Execution metrics (count, last run)
- Event publishing for skill lifecycle

**Usage Example**:
```python
# Execute skill with automatic retry
result = orchestrator.skill_registry.execute_skill(
    'process_needs_action',
    retry_on_failure=True
)

# Get skill metadata
info = orchestrator.skill_registry.get_skill_info('process_needs_action')
print(f"Executed {info['execution_count']} times")

# List all registered skills
skills = orchestrator.skill_registry.list_skills()
```

### 3. RetryQueue - Intelligent Retry Mechanism

**Purpose**: Handles transient failures with exponential backoff.

**Features**:
- Configurable retry policies (exponential, linear, fixed)
- Max retry limits (default: 5)
- Background processing
- Thread-safe queue

**Usage Example**:
```python
# Manually enqueue an operation for retry
orchestrator.retry_queue.enqueue(
    operation=some_function,
    args=(arg1, arg2),
    kwargs={'key': 'value'},
    policy=RetryPolicy.EXPONENTIAL,
    context={'name': 'my_operation'}
)

# Check queue size
size = orchestrator.retry_queue.get_queue_size()
print(f"Pending retries: {size}")
```

### 4. HealthMonitor - Component Health Tracking

**Purpose**: Continuously monitors health of all system components.

**Monitored Components**:
- State Manager
- Skill Dispatcher
- Email Executor
- Retry Queue
- Filesystem Watcher
- System Resources (CPU, Memory)

**Usage Example**:
```python
# Get overall system health
health = orchestrator.health_monitor.get_system_health()
print(f"Status: {health['overall_status'].value}")

# Get specific component status
status = orchestrator.health_monitor.get_component_status('email_executor')
print(f"Email Executor: {status['status'].value} - {status['message']}")

# Register custom health check
def check_custom_component():
    return {
        'status': ComponentStatus.HEALTHY,
        'message': 'All good'
    }

orchestrator.health_monitor.register_component('my_component', check_custom_component)
```

### 5. AuditLogger - Structured Audit Trail

**Purpose**: Provides queryable audit trail for compliance and debugging.

**Features**:
- JSONL format (one JSON object per line)
- Tracks skills, approvals, emails, system lifecycle
- Queryable with filters
- Separate from operational logs

**Usage Example**:
```python
# Log custom audit event
orchestrator.audit_logger.log_event(
    event_type='custom_action',
    actor='user',
    action='performed_action',
    resource='resource_name',
    result='success',
    metadata={'key': 'value'}
)

# Query audit logs
logs = orchestrator.audit_logger.query_logs(
    event_type='skill_execution',
    start_time=datetime.utcnow() - timedelta(days=1),
    limit=100
)

for log in logs:
    print(f"{log['timestamp']}: {log['action']} on {log['resource']}")
```

### 6. GracefulDegradation - Automatic Failure Handling

**Purpose**: Maintains core functionality during partial outages.

**Features**:
- Monitors system health
- Disables non-critical features when unhealthy
- Automatic recovery
- Feature flags

**Usage Example**:
```python
# Check if feature is enabled
if orchestrator.graceful_degradation.is_feature_enabled('email_sending'):
    send_email()
else:
    print("Email sending disabled due to degraded mode")

# Check degradation status
if orchestrator.graceful_degradation.degraded_mode:
    print("System in degraded mode")
    print(f"Disabled: {orchestrator.graceful_degradation.disabled_features}")
```

### 7. Enhanced StateManager - Expanded State Tracking

**Purpose**: Manages system-wide state beyond event processing.

**New Features**:
- System state key-value store
- Metrics collection
- Counter tracking
- Thread-safe operations

**Usage Example**:
```python
# Set system state
orchestrator.state_manager.set_system_state('maintenance_mode', False)

# Get system state
mode = orchestrator.state_manager.get_system_state('maintenance_mode', default=False)

# Update metrics
orchestrator.state_manager.update_metric('api_calls', 1234)

# Increment counters
orchestrator.state_manager.increment_counter('emails_sent')

# Get metrics
metric = orchestrator.state_manager.get_metric('emails_sent')
print(f"Emails sent: {metric['value']}")
```

## System Status and Monitoring

### Get Comprehensive Status

```python
status = orchestrator.get_status()

print(f"Running: {status['running']}")
print(f"Health: {status['health']['overall_status'].value}")
print(f"Retry Queue: {status['retry_queue_size']} items")
print(f"Registered Skills: {status['registered_skills']}")
print(f"Degraded Mode: {status['degraded_mode']}")

# Metrics
metrics = status['metrics']
print(f"Skills Started: {metrics['skills_started']}")
print(f"Skills Succeeded: {metrics['skills_succeeded']}")
print(f"Skills Failed: {metrics['skills_failed']}")
```

### Get Human-Readable Health Report

```python
report = orchestrator.get_health_report()
print(report)
```

Output:
```
============================================================
ORCHESTRATOR HEALTH REPORT
============================================================
Overall Status: HEALTHY
Running: True
Version: gold_tier_v1.0

Component Health:
  - state_manager: healthy - State manager operational
  - skill_dispatcher: healthy - Skill dispatcher operational
  - email_executor: healthy - Email executor operational
  - retry_queue: healthy - Retry queue operational (0 items)
  - filesystem_watcher: healthy - Filesystem watcher operational
  - system_resources: healthy - Resources normal: CPU 15%, Memory 45%

Metrics:
  - Skills Started: 42
  - Skills Succeeded: 40
  - Skills Failed: 2
  - Retry Queue Size: 0
  - Registered Skills: 5

✓ All features operational
============================================================
```

## State File Format

The enhanced state file (`state.json`) now includes:

```json
{
  "processed_events": {
    "event_id": {
      "event_type": "needs_action_created",
      "filepath": "/path/to/file.md",
      "processed_at": "2026-02-27T10:30:00Z"
    }
  },
  "system_state": {
    "last_startup": "2026-02-27T10:00:00Z",
    "orchestrator_version": "gold_tier_v1.0",
    "maintenance_mode": false
  },
  "metrics": {
    "skills_started": {
      "value": 42,
      "updated_at": "2026-02-27T10:30:00Z"
    },
    "skills_succeeded": {
      "value": 40,
      "updated_at": "2026-02-27T10:30:00Z"
    }
  },
  "last_updated": "2026-02-27T10:30:00Z"
}
```

## Audit Log Format

Audit logs are stored in `Logs/audit.jsonl` (JSONL format):

```json
{"timestamp": "2026-02-27T10:30:00Z", "event_type": "skill_execution", "actor": "system", "action": "execute_skill", "resource": "process_needs_action", "result": "success", "metadata": {"duration_seconds": 2.5}}
{"timestamp": "2026-02-27T10:31:00Z", "event_type": "email_action", "actor": "system", "action": "send_email", "resource": "email_to_user@example.com", "result": "success", "metadata": {"subject": "Test Email"}}
{"timestamp": "2026-02-27T10:32:00Z", "event_type": "approval_decision", "actor": "human", "action": "approved", "resource": "email_approval_123.md", "result": "recorded", "metadata": {}}
```

## Backward Compatibility

All existing functionality is preserved:
- Old state files are automatically migrated
- EventRouter works with or without Gold Tier components
- Existing skills continue to work unchanged
- All original APIs remain functional

## Dependencies

Optional dependency for enhanced monitoring:
```bash
pip install psutil
```

If `psutil` is not installed, system resource monitoring will be limited but all other features work normally.

## Best Practices

1. **Monitor Health Regularly**: Check `get_health_report()` periodically
2. **Review Audit Logs**: Query audit logs for compliance and debugging
3. **Handle Degraded Mode**: Check feature flags before critical operations
4. **Subscribe to Events**: Use EventBus for reactive programming
5. **Track Metrics**: Use StateManager metrics for operational insights
6. **Let Retry Queue Work**: Don't manually retry operations that will auto-retry

## Troubleshooting

### High Retry Queue Size
```python
size = orchestrator.retry_queue.get_queue_size()
if size > 50:
    print("Warning: High retry queue size, investigate failures")
```

### Component Unhealthy
```python
health = orchestrator.health_monitor.get_system_health()
for name, status in health['components'].items():
    if status['status'] == ComponentStatus.UNHEALTHY:
        print(f"Component {name} is unhealthy: {status['message']}")
```

### Query Recent Failures
```python
logs = orchestrator.audit_logger.query_logs(
    event_type='skill_execution',
    start_time=datetime.utcnow() - timedelta(hours=1)
)

failures = [log for log in logs if log['result'] == 'failure']
print(f"Recent failures: {len(failures)}")
```

## Migration from Silver Tier

No migration needed! The Gold Tier upgrade is fully backward compatible. Simply restart the orchestrator and all Gold Tier features will be automatically enabled.

Existing state files will be automatically upgraded to the new format on first save.
