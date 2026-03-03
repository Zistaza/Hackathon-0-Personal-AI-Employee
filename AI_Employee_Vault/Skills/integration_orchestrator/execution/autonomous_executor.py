#!/usr/bin/env python3
"""AutonomousExecutor - Autonomous Execution Layer
==================================================

Ralph Wiggum Loop - Continuously monitors system state and triggers actions.
Enhanced with Social Media Automation.
"""

import time
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from threading import Lock, Thread, Event

# Import core components for type hints
from core import (
    EventBus,
    RetryQueue,
    StateManager,
    HealthMonitor,
    AuditLogger,
    ComponentStatus,
)

# Import SocialMediaAutomation if available
try:
    from autonomous_executor_enhanced import SocialMediaAutomation
    SOCIAL_AUTOMATION_AVAILABLE = True
except ImportError:
    SOCIAL_AUTOMATION_AVAILABLE = False
    # Fallback: create empty base class
    class SocialMediaAutomation:
        pass


class AutonomousExecutor(SocialMediaAutomation):
    """
    Autonomous Execution Layer (Ralph Wiggum Loop)

    Continuously monitors system state and automatically triggers actions
    for incomplete workflows, pending tasks, and retry queue items.

    Enhanced with Social Media Automation:
    - Detects content in Posted/, Drafts/, Plans/
    - Automatically triggers social media skills
    - Handles scheduled posts
    - Provides failure recovery for social posts

    This component enables true autonomous operation by:
    - Detecting unfinished work across the system
    - Automatically triggering appropriate skills
    - Escalating repeated failures to human attention
    - Maintaining system momentum without manual intervention
    """

    def __init__(self, event_bus: EventBus, retry_queue: RetryQueue,
                 state_manager: StateManager, health_monitor: HealthMonitor,
                 skill_registry: 'SkillRegistry', audit_logger: AuditLogger,
                 base_dir: Path, logger: logging.Logger,
                 check_interval: int = 30, failure_threshold: int = 3):
        """
        Initialize AutonomousExecutor

        Args:
            event_bus: EventBus for publishing events
            retry_queue: RetryQueue to inspect for pending retries
            state_manager: StateManager for tracking state
            health_monitor: HealthMonitor for system health
            skill_registry: SkillRegistry for triggering skills
            audit_logger: AuditLogger for logging escalations
            base_dir: Base directory for file system checks
            logger: Logger instance
            check_interval: Seconds between checks (default: 30)
            failure_threshold: Max failures before escalation (default: 3)
        """
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.state_manager = state_manager
        self.health_monitor = health_monitor
        self.skill_registry = skill_registry
        self.audit_logger = audit_logger
        self.base_dir = base_dir
        self.logger = logger
        self.check_interval = check_interval
        self.failure_threshold = failure_threshold

        # Tracking state
        self.task_failure_counts: Dict[str, int] = {}
        self.last_check_times: Dict[str, datetime] = {}
        self.lock = Lock()

        # Runtime metrics
        self.metrics = {
            'auto_trigger_success': 0,
            'auto_trigger_failures': 0,
            'escalations': 0,
            'workflows_recovered': 0
        }

        # Thread control
        self.running = False
        self.thread = None
        self.stop_event = Event()

        # Directories to monitor
        self.needs_action_dir = base_dir / "Needs_Action"
        self.pending_approval_dir = base_dir / "Pending_Approval"
        self.inbox_dir = base_dir / "Inbox"

        # Initialize social media automation if available
        if SOCIAL_AUTOMATION_AVAILABLE:
            try:
                SocialMediaAutomation.__init__(self)
                self.logger.info("Social media automation enabled")
            except Exception as e:
                self.logger.warning(f"Failed to initialize social media automation: {e}")
        else:
            self.logger.info("Social media automation not available")

    def start(self):
        """Start the autonomous execution loop"""
        self.running = True
        self.thread = Thread(target=self._execution_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"AutonomousExecutor started (check interval: {self.check_interval}s)")

    def stop(self):
        """Stop the autonomous execution loop gracefully"""
        self.logger.info("Stopping AutonomousExecutor...")
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=10)
        self.logger.info("AutonomousExecutor stopped")

    def _execution_loop(self):
        """Main execution loop - the Ralph Wiggum Loop"""
        self.logger.info("Autonomous execution loop started")

        while self.running:
            try:
                # Check system health first
                health = self.health_monitor.get_system_health()
                if health['overall_status'] == ComponentStatus.UNHEALTHY:
                    self.logger.warning("System unhealthy, skipping autonomous checks")
                    if self.stop_event.wait(timeout=self.check_interval):
                        break
                    continue

                # Perform autonomous checks
                self._check_retry_queue()
                self._check_pending_workflows()
                self._check_incomplete_tasks()
                self._check_stale_files()

                # Social media automation (if available)
                if SOCIAL_AUTOMATION_AVAILABLE and hasattr(self, '_check_social_media_content'):
                    try:
                        self._check_social_media_content()
                    except Exception as e:
                        self.logger.error(f"Error in social media automation: {e}")

                # Update last check time
                self.state_manager.set_system_state(
                    'autonomous_executor_last_check',
                    datetime.utcnow().isoformat() + 'Z'
                )

                # Sleep until next check
                if self.stop_event.wait(timeout=self.check_interval):
                    break

            except Exception as e:
                self.logger.error(f"Error in autonomous execution loop: {e}")
                time.sleep(self.check_interval)

    def _check_retry_queue(self):
        """Check retry queue for items that need attention"""
        try:
            queue_size = self.retry_queue.get_queue_size()

            if queue_size > 0:
                self.logger.debug(f"RetryQueue has {queue_size} pending items")

                # Publish event for monitoring
                self.event_bus.publish('retry_queue_status', {
                    'queue_size': queue_size,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

                # If queue is getting large, log warning
                if queue_size > 10:
                    self.logger.warning(f"RetryQueue is large: {queue_size} items")
                    self.audit_logger.log_event(
                        event_type='autonomous_detection',
                        actor='autonomous_executor',
                        action='retry_queue_alert',
                        resource='retry_queue',
                        result='warning',
                        metadata={'queue_size': queue_size}
                    )
        except Exception as e:
            self.logger.error(f"Error checking retry queue: {e}")

    def _check_pending_workflows(self):
        """Check for pending workflows that need processing"""
        try:
            # Check Needs_Action directory
            if self.needs_action_dir.exists():
                needs_action_files = list(self.needs_action_dir.glob("*.md"))

                if needs_action_files:
                    self.logger.info(f"Found {len(needs_action_files)} files in Needs_Action")

                    # Publish event
                    self.event_bus.publish('unfinished_workflow_detected', {
                        'location': 'Needs_Action',
                        'file_count': len(needs_action_files),
                        'files': [f.name for f in needs_action_files[:5]],  # First 5
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                    # Trigger process_needs_action skill
                    self._trigger_skill_with_tracking(
                        'process_needs_action',
                        context='needs_action_files_detected'
                    )

            # Check Inbox directory
            if self.inbox_dir.exists():
                inbox_files = list(self.inbox_dir.glob("*.md"))

                if inbox_files:
                    self.logger.info(f"Found {len(inbox_files)} files in Inbox")

                    # Publish event
                    self.event_bus.publish('unfinished_workflow_detected', {
                        'location': 'Inbox',
                        'file_count': len(inbox_files),
                        'files': [f.name for f in inbox_files[:5]],
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                    # Files in Inbox should be moved to Needs_Action
                    # This is typically handled by watchers, but we can trigger a check
                    self.logger.debug("Inbox files detected, watchers should handle")

        except Exception as e:
            self.logger.error(f"Error checking pending workflows: {e}")

    def _check_incomplete_tasks(self):
        """Check for incomplete multi-step tasks"""
        try:
            # Check for files stuck in Pending_Approval for too long
            if self.pending_approval_dir.exists():
                pending_files = list(self.pending_approval_dir.glob("*.md"))

                for filepath in pending_files:
                    try:
                        # Check file age
                        stat = filepath.stat()
                        file_age = datetime.utcnow() - datetime.fromtimestamp(stat.st_mtime)

                        # If file is older than 1 hour, log it
                        if file_age > timedelta(hours=1):
                            self.logger.info(f"File stuck in Pending_Approval: {filepath.name} (age: {file_age})")

                            self.event_bus.publish('stale_approval_detected', {
                                'filepath': str(filepath),
                                'filename': filepath.name,
                                'age_hours': file_age.total_seconds() / 3600,
                                'timestamp': datetime.utcnow().isoformat() + 'Z'
                            })
                    except Exception as e:
                        self.logger.error(f"Error checking file {filepath}: {e}")

        except Exception as e:
            self.logger.error(f"Error checking incomplete tasks: {e}")

    def _check_stale_files(self):
        """Check for stale files that might indicate stuck workflows"""
        try:
            # This is a placeholder for more sophisticated stale file detection
            # Could check for files that haven't been modified in a long time
            # or files that are in unexpected states
            pass
        except Exception as e:
            self.logger.error(f"Error checking stale files: {e}")

    def _trigger_skill_with_tracking(self, skill_name: str, context: str, args: List[str] = None):
        """
        Trigger a skill with failure tracking and escalation

        Args:
            skill_name: Name of skill to execute
            context: Context string for tracking
            args: Optional arguments for skill
        """
        try:
            # Check if we should skip due to recent execution
            last_check_key = f"skill_{skill_name}_{context}"

            with self.lock:
                last_check = self.last_check_times.get(last_check_key)

                # Don't trigger same skill more than once per 5 minutes
                if last_check and (datetime.utcnow() - last_check) < timedelta(minutes=5):
                    self.logger.debug(f"Skipping {skill_name}, recently executed")
                    return

                # Update last check time
                self.last_check_times[last_check_key] = datetime.utcnow()

            # Execute skill
            self.logger.info(f"Autonomous trigger: {skill_name} (context: {context})")

            result = self.skill_registry.execute_skill(skill_name, args, retry_on_failure=False)

            # Track result
            if result.get('success'):
                # Reset failure count on success
                with self.lock:
                    # Check if this is a recovery (task previously failed)
                    if last_check_key in self.task_failure_counts:
                        self.metrics['workflows_recovered'] += 1
                        del self.task_failure_counts[last_check_key]

                    # Increment success counter
                    self.metrics['auto_trigger_success'] += 1

                self.logger.info(f"Autonomous execution succeeded: {skill_name}")

                # Audit log
                self.audit_logger.log_event(
                    event_type='autonomous_execution',
                    actor='autonomous_executor',
                    action='trigger_skill',
                    resource=skill_name,
                    result='success',
                    metadata={'context': context}
                )
            else:
                # Increment failure count
                with self.lock:
                    self.task_failure_counts[last_check_key] = \
                        self.task_failure_counts.get(last_check_key, 0) + 1
                    failure_count = self.task_failure_counts[last_check_key]

                    # Increment failure counter
                    self.metrics['auto_trigger_failures'] += 1

                self.logger.warning(f"Autonomous execution failed: {skill_name} (failures: {failure_count})")

                # Check if we need to escalate
                if failure_count >= self.failure_threshold:
                    self._escalate_to_human(skill_name, context, result)
                else:
                    # Add to retry queue for later
                    self.retry_queue.enqueue(
                        operation=self.skill_registry.execute_skill,
                        args=(skill_name, args),
                        kwargs={'retry_on_failure': False},  # Prevent infinite retry loop
                        context={'name': f"autonomous_{skill_name}", 'context': context}
                    )

        except Exception as e:
            self.logger.error(f"Error triggering skill {skill_name}: {e}")

    def _escalate_to_human(self, skill_name: str, context: str, last_result: Dict):
        """
        Escalate repeated failures to human attention

        Creates a file in Needs_Action with details about the failure
        """
        try:
            self.logger.error(f"ESCALATION: {skill_name} failed {self.failure_threshold} times, escalating to human")

            # Increment escalation counter
            with self.lock:
                self.metrics['escalations'] += 1

            # Create escalation file in Needs_Action
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            escalation_file = self.needs_action_dir / f"ESCALATION_{timestamp}_{skill_name}.md"

            escalation_content = f"""# ESCALATION: Autonomous Execution Failure

## Summary
The autonomous executor detected repeated failures and is escalating to human attention.

## Details
- **Skill**: {skill_name}
- **Context**: {context}
- **Failure Count**: {self.failure_threshold}
- **Timestamp**: {datetime.utcnow().isoformat()}Z

## Last Execution Result
```
Success: {last_result.get('success')}
Error: {last_result.get('error', 'N/A')}
Return Code: {last_result.get('returncode', 'N/A')}
```

## Stderr Output
```
{last_result.get('stderr', 'N/A')[:500]}
```

## Recommended Actions
1. Review the error details above
2. Check system logs for more context
3. Manually investigate the {skill_name} skill
4. Fix any underlying issues
5. Delete this file once resolved

## System Status
- Health: Check with get_health_report()
- Retry Queue: Check current size
- Recent Audit Logs: Review for patterns

---
Generated by AutonomousExecutor
"""

            with open(escalation_file, 'w') as f:
                f.write(escalation_content)

            self.logger.info(f"Escalation file created: {escalation_file.name}")

            # Publish escalation event
            self.event_bus.publish('task_escalated', {
                'skill_name': skill_name,
                'context': context,
                'failure_count': self.failure_threshold,
                'escalation_file': str(escalation_file),
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

            # Audit log
            self.audit_logger.log_event(
                event_type='escalation',
                actor='autonomous_executor',
                action='escalate_to_human',
                resource=skill_name,
                result='escalated',
                metadata={
                    'context': context,
                    'failure_count': self.failure_threshold,
                    'escalation_file': escalation_file.name,
                    'error': last_result.get('error', 'Unknown')
                }
            )

            # Reset failure count after escalation
            with self.lock:
                last_check_key = f"skill_{skill_name}_{context}"
                if last_check_key in self.task_failure_counts:
                    del self.task_failure_counts[last_check_key]

        except Exception as e:
            self.logger.error(f"Error escalating to human: {e}")

    def get_status(self) -> Dict:
        """Get current status of autonomous executor"""
        with self.lock:
            return {
                'running': self.running,
                'check_interval': self.check_interval,
                'failure_threshold': self.failure_threshold,
                'tracked_tasks': len(self.task_failure_counts),
                'task_failure_counts': self.task_failure_counts.copy(),
                'last_check': self.state_manager.get_system_state('autonomous_executor_last_check')
            }

    def get_autonomous_metrics(self) -> Dict:
        """
        Get autonomous execution metrics

        Returns:
            Dictionary containing:
            - success_rate: Success rate percentage
            - auto_trigger_success: Count of successful autonomous triggers
            - auto_trigger_failures: Count of failed autonomous triggers
            - escalations: Count of escalations to human
            - workflows_recovered: Count of workflows that recovered after failure
        """
        with self.lock:
            total_triggers = self.metrics['auto_trigger_success'] + self.metrics['auto_trigger_failures']

            # Calculate success rate (handle division by zero)
            if total_triggers > 0:
                success_rate = (self.metrics['auto_trigger_success'] / total_triggers) * 100
            else:
                success_rate = 0.0

            return {
                'success_rate': round(success_rate, 2),
                'auto_trigger_success': self.metrics['auto_trigger_success'],
                'auto_trigger_failures': self.metrics['auto_trigger_failures'],
                'escalations': self.metrics['escalations'],
                'workflows_recovered': self.metrics['workflows_recovered']
            }

