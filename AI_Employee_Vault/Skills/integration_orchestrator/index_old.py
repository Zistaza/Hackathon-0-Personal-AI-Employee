#!/usr/bin/env python3
"""
Integration Orchestrator - Gold Tier Architecture
==================================================

Central automation controller for AI Employee Vault
Monitors folders, routes events, and triggers skills automatically
Enhanced with Human-in-the-Loop email approval workflow

GOLD TIER ENHANCEMENTS:
-----------------------

1. EventBus: Central pub/sub system for inter-component communication
   - Decouples components through event-driven architecture
   - Enables reactive programming patterns
   - Supports multiple subscribers per event type

2. SkillRegistry: Enhanced skill management with retry and audit
   - Wraps existing SkillDispatcher with additional capabilities
   - Automatic retry on failure with exponential backoff
   - Structured audit logging for all skill executions
   - Skill metadata tracking (execution count, last run, etc.)

3. RetryQueue: Intelligent retry mechanism with exponential backoff
   - Handles transient failures gracefully
   - Configurable retry policies (exponential, linear, fixed)
   - Prevents system overload with max retry limits
   - Background processing with thread-safe queue

4. HealthMonitor: Continuous component health monitoring
   - Tracks health status of all system components
   - Periodic health checks with configurable intervals
   - Provides overall system health assessment
   - Enables proactive issue detection

5. AuditLogger: Structured audit logging for compliance
   - JSONL format for easy parsing and analysis
   - Tracks all critical operations (skills, approvals, emails)
   - Queryable audit trail with filtering
   - Separate from operational logs

6. GracefulDegradation: Automatic feature degradation on failures
   - Monitors system health and disables non-critical features
   - Prevents cascading failures
   - Automatic recovery when health improves
   - Maintains core functionality during partial outages

7. Enhanced StateManager: Expanded state management
   - System-wide state tracking beyond event processing
   - Metrics collection and persistence
   - Thread-safe operations with locking
   - Backward compatible with existing state files

8. AutonomousExecutor: Autonomous execution layer (Ralph Wiggum Loop)
   - Continuous monitoring of system state and workflows
   - Automatic detection of incomplete tasks and pending work
   - Intelligent retry with failure tracking and escalation
   - Escalates repeated failures to human attention
   - Maintains system momentum without manual intervention

ARCHITECTURE:
-------------

    ┌─────────────────────────────────────────────────────────┐
    │         IntegrationOrchestrator (Main Controller)       │
    └─────────────────────────────────────────────────────────┘
                              │
                ┌─────────────┼─────────────┐
                │             │             │
         ┌──────▼──────┐ ┌───▼────┐ ┌─────▼──────┐
         │  EventBus   │ │ Health │ │   Retry    │
         │  (Pub/Sub)  │ │Monitor │ │   Queue    │
         └──────┬──────┘ └───┬────┘ └─────┬──────┘
                │            │             │
         ┌──────▼────────────▼─────────────▼──────┐
         │         SkillRegistry (Enhanced)        │
         │    ┌────────────────────────────┐       │
         │    │   SkillDispatcher (Core)   │       │
         │    └────────────────────────────┘       │
         └──────────────────┬──────────────────────┘
                            │
         ┌──────────────────┼──────────────────┐
         │                  │                  │
    ┌────▼─────┐    ┌──────▼──────┐   ┌──────▼──────┐
    │  Event   │    │   Email     │   │  Approval   │
    │  Router  │    │  Executor   │   │  Manager    │
    └──────────┘    └─────────────┘   └─────────────┘
                            │
                    ┌───────▼────────┐
                    │  Autonomous    │
                    │   Executor     │
                    │ (Ralph Wiggum) │
                    └────────────────┘

PRESERVED COMPONENTS (Unchanged):
----------------------------------
- StateManager (enhanced, not replaced)
- ApprovalManager
- SkillDispatcher (wrapped by SkillRegistry)
- EventRouter (enhanced with Gold Tier integration)
- EmailExecutor
- PeriodicTrigger
- FolderWatcherHandler

USAGE:
------
    orchestrator = IntegrationOrchestrator(base_dir)
    orchestrator.start()  # Starts all components including Gold Tier

    # Get system status
    status = orchestrator.get_status()
    print(orchestrator.get_health_report())

BACKWARD COMPATIBILITY:
-----------------------
All existing functionality is preserved. The system can operate with or without
Gold Tier components. If a Gold Tier component is unavailable, the system falls
back to the original behavior.
"""

import os
import sys
import json
import time
import signal
import logging
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Callable, Any
from threading import Thread, Event, Lock
from collections import deque
from enum import Enum
import hashlib
import shutil

# Social Media Skills Integration
try:
    from social_media_skills import register_social_skills
    SOCIAL_SKILLS_AVAILABLE = True
except ImportError:
    SOCIAL_SKILLS_AVAILABLE = False

# Enhanced AutonomousExecutor with Social Media Automation
try:
    from autonomous_executor_enhanced import SocialMediaAutomation
    SOCIAL_AUTOMATION_AVAILABLE = True
except ImportError:
    SOCIAL_AUTOMATION_AVAILABLE = False
    # Fallback: create empty base class
    class SocialMediaAutomation:
        pass

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("Warning: psutil not installed. System resource monitoring will be limited.")

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except ImportError:
    print("Error: watchdog not installed")
    print("Install with: pip install watchdog")
    sys.exit(1)


class StateManager:
    """Manages processed events state - Enhanced for Gold Tier"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.processed_events: Dict[str, Dict] = {}
        # Gold Tier enhancements
        self.system_state: Dict[str, Any] = {}
        self.metrics: Dict[str, Any] = {}
        self.lock = Lock()
        self.load_state()

    def load_state(self):
        """Load processed events from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    data = json.load(f)
                    # Support both old and new format
                    if isinstance(data, dict) and 'processed_events' in data:
                        # New format with enhanced state
                        self.processed_events = data.get('processed_events', {})
                        self.system_state = data.get('system_state', {})
                        self.metrics = data.get('metrics', {})
                    else:
                        # Old format - just processed events
                        self.processed_events = data
                        self.system_state = {}
                        self.metrics = {}
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
            self.processed_events = {}
            self.system_state = {}
            self.metrics = {}

    def save_state(self):
        """Save processed events to file - Enhanced format"""
        try:
            with self.lock:
                state_data = {
                    'processed_events': self.processed_events,
                    'system_state': self.system_state,
                    'metrics': self.metrics,
                    'last_updated': datetime.utcnow().isoformat() + 'Z'
                }
                with open(self.state_file, 'w') as f:
                    json.dump(state_data, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def is_processed(self, event_id: str) -> bool:
        """Check if event has been processed"""
        with self.lock:
            return event_id in self.processed_events

    def mark_processed(self, event_id: str, metadata: Dict):
        """Mark event as processed"""
        with self.lock:
            self.processed_events[event_id] = {
                **metadata,
                'processed_at': datetime.utcnow().isoformat() + 'Z'
            }
        self.save_state()

    def get_event_hash(self, filepath: Path) -> str:
        """Generate unique hash for file event"""
        try:
            stat = filepath.stat()
            content = f"{filepath.name}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return hashlib.md5(str(filepath).encode()).hexdigest()

    # Gold Tier enhancements
    def set_system_state(self, key: str, value: Any):
        """Set system state value"""
        with self.lock:
            self.system_state[key] = value
        self.save_state()

    def get_system_state(self, key: str, default: Any = None) -> Any:
        """Get system state value"""
        with self.lock:
            return self.system_state.get(key, default)

    def update_metric(self, metric_name: str, value: Any):
        """Update a metric"""
        with self.lock:
            self.metrics[metric_name] = {
                'value': value,
                'updated_at': datetime.utcnow().isoformat() + 'Z'
            }
        self.save_state()

    def get_metric(self, metric_name: str) -> Optional[Dict]:
        """Get a metric"""
        with self.lock:
            return self.metrics.get(metric_name)

    def increment_counter(self, counter_name: str, amount: int = 1):
        """Increment a counter metric"""
        with self.lock:
            if counter_name not in self.metrics:
                self.metrics[counter_name] = {'value': 0}
            self.metrics[counter_name]['value'] += amount
            self.metrics[counter_name]['updated_at'] = datetime.utcnow().isoformat() + 'Z'
        self.save_state()


class ApprovalManager:
    """Manages email approval tracking to prevent duplicate execution"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.processed_approvals: Dict[str, Dict] = {}
        self.load_state()

    def load_state(self):
        """Load processed approvals from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    self.processed_approvals = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load approval state file: {e}")
            self.processed_approvals = {}

    def save_state(self):
        """Save processed approvals to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.processed_approvals, f, indent=2)
        except Exception as e:
            print(f"Error saving approval state: {e}")

    def is_processed(self, approval_id: str) -> bool:
        """Check if approval has been processed"""
        return approval_id in self.processed_approvals

    def mark_processed(self, approval_id: str, metadata: Dict):
        """Mark approval as processed"""
        self.processed_approvals[approval_id] = {
            **metadata,
            'processed_at': datetime.utcnow().isoformat() + 'Z'
        }
        self.save_state()

    def get_approval_hash(self, filepath: Path) -> str:
        """Generate unique hash for approval file"""
        try:
            stat = filepath.stat()
            content = f"{filepath.name}_{stat.st_size}_{stat.st_mtime}"
            return hashlib.md5(content.encode()).hexdigest()
        except Exception:
            return hashlib.md5(str(filepath).encode()).hexdigest()


class EmailExecutor:
    """Executes email sending via MCP server"""

    def __init__(self, mcp_server_path: Path, logs_dir: Path, logger: logging.Logger):
        self.mcp_server_path = mcp_server_path
        self.logs_dir = logs_dir
        self.logger = logger

    def send_email(self, email_data: Dict) -> Dict:
        """Send email using nodemailer directly"""
        try:
            # Prepare email command
            to = email_data.get('to', '')
            subject = email_data.get('subject', '')
            body = email_data.get('body', '')

            if not to or not subject or not body:
                return {
                    'success': False,
                    'error': 'Missing required email fields (to, subject, body)'
                }

            self.logger.info(f"Sending email to: {to}")
            self.logger.info(f"Subject: {subject}")

            # Use the test_email.js script with custom parameters
            test_script = self.mcp_server_path / "test_email.js"

            if not test_script.exists():
                return {
                    'success': False,
                    'error': f'Email script not found: {test_script}'
                }

            # Create temporary email data file
            temp_data_file = self.mcp_server_path / "temp_email_data.json"
            with open(temp_data_file, 'w') as f:
                json.dump(email_data, f, indent=2)

            # Execute email sending
            result = subprocess.run(
                ["node", str(test_script), to],
                cwd=str(self.mcp_server_path),
                capture_output=True,
                text=True,
                timeout=30
            )

            # Clean up temp file
            if temp_data_file.exists():
                temp_data_file.unlink()

            success = result.returncode == 0

            if success:
                self.logger.info(f"Email sent successfully to {to}")
                self._log_email_action('email_sent', email_data, result.stdout)
            else:
                self.logger.error(f"Email sending failed: {result.stderr}")
                self._log_email_action('email_failed', email_data, result.stderr)

            return {
                'success': success,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        except subprocess.TimeoutExpired:
            self.logger.error("Email sending timed out")
            return {
                'success': False,
                'error': 'Email sending timeout'
            }
        except Exception as e:
            self.logger.error(f"Error sending email: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def _log_email_action(self, action: str, email_data: Dict, details: str):
        """Log email action to daily log file"""
        try:
            today = datetime.utcnow().strftime('%Y-%m-%d')
            log_file = self.logs_dir / f"{today}.json"

            # Load existing logs
            logs = []
            if log_file.exists():
                try:
                    with open(log_file, 'r') as f:
                        logs = json.load(f)
                except:
                    logs = []

            # Add new log entry
            log_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'action': action,
                'to': email_data.get('to', ''),
                'subject': email_data.get('subject', ''),
                'details': details[:500]  # Limit details length
            }
            logs.append(log_entry)

            # Save logs
            with open(log_file, 'w') as f:
                json.dump(logs, f, indent=2)

        except Exception as e:
            self.logger.error(f"Error logging email action: {e}")


class SkillDispatcher:
    """Executes skills and manages skill processes"""

    def __init__(self, skills_dir: Path, logger: logging.Logger):
        self.skills_dir = skills_dir
        self.logger = logger

    def execute_skill(self, skill_name: str, args: List[str] = None) -> Dict:
        """Execute a skill and return result"""
        skill_path = self.skills_dir / skill_name

        if not skill_path.exists():
            return {
                'success': False,
                'error': f"Skill not found: {skill_name}"
            }

        try:
            # Determine execution method
            if (skill_path / "index.js").exists():
                cmd = ["node", "index.js"] + (args or [])
            elif (skill_path / "index.py").exists():
                cmd = ["python3", "index.py"] + (args or [])
            elif (skill_path / "process_needs_action.py").exists():
                cmd = ["python3", "process_needs_action.py"] + (args or [])
            elif (skill_path / "run.sh").exists():
                cmd = ["./run.sh"] + (args or [])
            else:
                return {
                    'success': False,
                    'error': f"No executable found in {skill_name}"
                }

            self.logger.info(f"Executing skill: {skill_name} with command: {' '.join(cmd)}")

            # Execute skill
            result = subprocess.run(
                cmd,
                cwd=str(skill_path),
                capture_output=True,
                text=True,
                timeout=300  # 5 minute timeout
            )

            success = result.returncode == 0

            if success:
                self.logger.info(f"Skill {skill_name} completed successfully")
            else:
                self.logger.error(f"Skill {skill_name} failed with code {result.returncode}")
                self.logger.error(f"Error output: {result.stderr}")

            return {
                'success': success,
                'returncode': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }

        except subprocess.TimeoutExpired:
            self.logger.error(f"Skill {skill_name} timed out")
            return {
                'success': False,
                'error': 'Execution timeout'
            }
        except Exception as e:
            self.logger.error(f"Error executing skill {skill_name}: {e}")
            return {
                'success': False,
                'error': str(e)
            }


class EventRouter:
    """Routes filesystem events to appropriate handlers - Enhanced for Gold Tier"""

    def __init__(self, dispatcher: SkillDispatcher, state_manager: StateManager,
                 approval_manager: ApprovalManager, email_executor: EmailExecutor,
                 base_dir: Path, logger: logging.Logger,
                 skill_registry: 'SkillRegistry' = None, event_bus: 'EventBus' = None,
                 graceful_degradation: 'GracefulDegradation' = None):
        self.dispatcher = dispatcher
        self.state_manager = state_manager
        self.approval_manager = approval_manager
        self.email_executor = email_executor
        self.base_dir = base_dir
        self.logger = logger
        # Gold Tier components (optional for backward compatibility)
        self.skill_registry = skill_registry
        self.event_bus = event_bus
        self.graceful_degradation = graceful_degradation

    def route_event(self, event_type: str, filepath: Path) -> bool:
        """Route event to appropriate handler"""
        try:
            # Generate event ID
            event_id = f"{event_type}_{self.state_manager.get_event_hash(filepath)}"

            # Check if already processed
            if self.state_manager.is_processed(event_id):
                self.logger.debug(f"Event already processed: {event_id}")
                return True

            self.logger.info(f"Routing event: {event_type} for {filepath.name}")

            # Route based on event type and location
            if event_type == "needs_action_created":
                result = self._handle_needs_action(filepath)
            elif event_type == "pending_approval_modified":
                result = self._handle_pending_approval(filepath)
            elif event_type == "pending_approval_email_created":
                result = self._handle_pending_approval_email(filepath)
            elif event_type == "approved_created":
                result = self._handle_approved(filepath)
            elif event_type == "rejected_created":
                result = self._handle_rejected(filepath)
            elif event_type == "inbox_created":
                result = self._handle_inbox(filepath)
            else:
                self.logger.warning(f"Unknown event type: {event_type}")
                return False

            # Mark as processed if successful
            if result:
                self.state_manager.mark_processed(event_id, {
                    'event_type': event_type,
                    'filepath': str(filepath),
                    'filename': filepath.name
                })

            return result

        except Exception as e:
            self.logger.error(f"Error routing event: {e}")
            return False

    def _handle_needs_action(self, filepath: Path) -> bool:
        """Handle new file in Needs_Action - Enhanced with Gold Tier"""
        self.logger.info(f"Processing Needs_Action file: {filepath.name}")

        # Publish event
        if self.event_bus:
            self.event_bus.publish('needs_action_detected', {
                'filepath': str(filepath),
                'filename': filepath.name,
                'timestamp': datetime.utcnow().isoformat() + 'Z'
            })

        # Trigger process_needs_action skill via SkillRegistry
        result = self.skill_registry.execute_skill("process_needs_action")

        return result['success']

    def _handle_pending_approval(self, filepath: Path) -> bool:
        """Handle modified file in Pending_Approval - Enhanced with Gold Tier"""
        try:
            # Read file to check status
            with open(filepath, 'r') as f:
                content = f.read()

            # Check if status is approved
            if 'status: approved' in content or 'status:approved' in content:
                self.logger.info(f"Approved file detected: {filepath.name}")

                # Publish event
                if self.event_bus:
                    self.event_bus.publish('approval_detected', {
                        'filepath': str(filepath),
                        'filename': filepath.name,
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                # Determine which skill to trigger based on file type
                if 'type: linkedin_post' in content:
                    self.logger.info("Triggering LinkedIn post skill")

                    # Trigger via SkillRegistry
                    result = self.skill_registry.execute_skill("linkedin_post_skill", ["process"])

                    return result['success']
                else:
                    self.logger.info("Approved file but no specific handler")
                    return True
            else:
                self.logger.debug(f"File not approved yet: {filepath.name}")
                return True

        except Exception as e:
            self.logger.error(f"Error handling pending approval: {e}")
            return False

    def _handle_pending_approval_email(self, filepath: Path) -> bool:
        """Handle new file in Pending_Approval/email/ - Wait for human approval"""
        self.logger.info(f"Email approval request created: {filepath.name}")
        self.logger.info("Waiting for human to move file to /Approved/ or /Rejected/")
        # Do nothing - wait for human to move the file
        return True

    def _handle_approved(self, filepath: Path) -> bool:
        """Handle file moved to Approved - Execute email and move to Done - Enhanced with Gold Tier"""
        try:
            # Check if email sending is enabled (graceful degradation)
            if self.graceful_degradation and not self.graceful_degradation.is_feature_enabled('email_sending'):
                self.logger.warning(f"Email sending disabled (degraded mode), skipping: {filepath.name}")
                return False

            # Generate approval ID
            approval_id = self.approval_manager.get_approval_hash(filepath)

            # Check if already processed
            if self.approval_manager.is_processed(approval_id):
                self.logger.warning(f"Approval already processed: {filepath.name}")
                return True

            self.logger.info(f"Processing approved email: {filepath.name}")

            # Publish event
            if self.event_bus:
                self.event_bus.publish('email_approved', {
                    'filepath': str(filepath),
                    'filename': filepath.name,
                    'timestamp': datetime.utcnow().isoformat() + 'Z'
                })

            # Read approval file
            with open(filepath, 'r') as f:
                content = f.read()

            # Parse email data from file
            email_data = self._parse_email_approval(content)

            if not email_data:
                self.logger.error(f"Failed to parse email data from {filepath.name}")
                return False

            # Validate required fields
            if email_data.get('action') != 'send_email':
                self.logger.warning(f"Not an email action: {email_data.get('action')}")
                return False

            # Send email
            self.logger.info(f"Sending email to: {email_data.get('to')}")
            result = self.email_executor.send_email(email_data)

            if result['success']:
                self.logger.info("Email sent successfully")

                # Mark as processed
                self.approval_manager.mark_processed(approval_id, {
                    'filename': filepath.name,
                    'to': email_data.get('to'),
                    'subject': email_data.get('subject'),
                    'status': 'sent'
                })

                # Publish success event
                if self.event_bus:
                    self.event_bus.publish('email_sent', {
                        'to': email_data.get('to'),
                        'subject': email_data.get('subject'),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                # Move to Done
                done_dir = self.base_dir / "Done"
                done_dir.mkdir(parents=True, exist_ok=True)

                timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
                done_path = done_dir / f"sent_{timestamp}_{filepath.name}"

                shutil.move(str(filepath), str(done_path))
                self.logger.info(f"Moved to Done: {done_path.name}")

                return True
            else:
                self.logger.error(f"Email sending failed: {result.get('error', 'Unknown error')}")

                # Publish failure event
                if self.event_bus:
                    self.event_bus.publish('email_failed', {
                        'to': email_data.get('to'),
                        'subject': email_data.get('subject'),
                        'error': result.get('error'),
                        'timestamp': datetime.utcnow().isoformat() + 'Z'
                    })

                return False

        except Exception as e:
            self.logger.error(f"Error handling approved email: {e}")
            return False

    def _handle_rejected(self, filepath: Path) -> bool:
        """Handle file moved to Rejected - Log rejection"""
        try:
            self.logger.info(f"Email approval rejected: {filepath.name}")

            # Read file for logging
            try:
                with open(filepath, 'r') as f:
                    content = f.read()
                email_data = self._parse_email_approval(content)

                if email_data:
                    self.logger.info(f"Rejected email to: {email_data.get('to')}")
                    self.logger.info(f"Subject: {email_data.get('subject')}")
            except:
                pass

            # Log rejection
            self.email_executor._log_email_action('email_rejected',
                                                   email_data if email_data else {},
                                                   f"User rejected approval for {filepath.name}")

            return True

        except Exception as e:
            self.logger.error(f"Error handling rejected email: {e}")
            return False

    def _parse_email_approval(self, content: str) -> Optional[Dict]:
        """Parse email data from approval file"""
        try:
            email_data = {}
            lines = content.split('\n')

            for line in lines:
                line = line.strip()
                if line.startswith('action:'):
                    email_data['action'] = line.split(':', 1)[1].strip()
                elif line.startswith('to:'):
                    email_data['to'] = line.split(':', 1)[1].strip()
                elif line.startswith('subject:'):
                    email_data['subject'] = line.split(':', 1)[1].strip()
                elif line.startswith('body:'):
                    # Body might be multiline, capture everything after 'body:'
                    body_start = content.find('body:')
                    if body_start != -1:
                        body_content = content[body_start + 5:].strip()
                        # Stop at timestamp or status if present
                        for stop_marker in ['timestamp:', 'status:']:
                            if stop_marker in body_content:
                                body_content = body_content.split(stop_marker)[0].strip()
                        email_data['body'] = body_content
                elif line.startswith('timestamp:'):
                    email_data['timestamp'] = line.split(':', 1)[1].strip()
                elif line.startswith('status:'):
                    email_data['status'] = line.split(':', 1)[1].strip()

            return email_data if email_data else None

        except Exception as e:
            self.logger.error(f"Error parsing email approval: {e}")
            return None

    def _handle_inbox(self, filepath: Path) -> bool:
        """Handle new file in Inbox"""
        self.logger.info(f"Processing Inbox file: {filepath.name}")

        # Move to Needs_Action for processing
        try:
            needs_action_dir = filepath.parent.parent / "Needs_Action"
            destination = needs_action_dir / filepath.name

            # Move file
            filepath.rename(destination)
            self.logger.info(f"Moved {filepath.name} to Needs_Action")

            return True

        except Exception as e:
            self.logger.error(f"Error moving inbox file: {e}")
            return False


class FolderWatcherHandler(FileSystemEventHandler):
    """Handles filesystem events"""

    def __init__(self, folder_name: str, event_router: EventRouter, logger: logging.Logger):
        self.folder_name = folder_name
        self.event_router = event_router
        self.logger = logger

    def on_created(self, event: FileSystemEvent):
        """Handle file creation"""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Only process markdown files
        if filepath.suffix != '.md':
            return

        # Route event
        event_type = f"{self.folder_name}_created"
        self.event_router.route_event(event_type, filepath)

    def on_modified(self, event: FileSystemEvent):
        """Handle file modification"""
        if event.is_directory:
            return

        filepath = Path(event.src_path)

        # Only process markdown files
        if filepath.suffix != '.md':
            return

        # Only route modifications for Pending_Approval
        if self.folder_name == "pending_approval":
            event_type = f"{self.folder_name}_modified"
            self.event_router.route_event(event_type, filepath)

    def on_moved(self, event: FileSystemEvent):
        """Handle file moves (for Approved/Rejected workflow)"""
        if event.is_directory:
            return

        dest_path = Path(event.dest_path)

        # Only process markdown files
        if dest_path.suffix != '.md':
            return

        # Treat moves as creation in destination folder
        event_type = f"{self.folder_name}_created"
        self.event_router.route_event(event_type, dest_path)


class PeriodicTrigger:
    """Handles periodic skill triggers"""

    def __init__(self, dispatcher: SkillDispatcher, logger: logging.Logger):
        self.dispatcher = dispatcher
        self.logger = logger
        self.running = False
        self.thread = None
        self.stop_event = Event()

    def start(self):
        """Start periodic triggers"""
        self.running = True
        self.thread = Thread(target=self._run_periodic_tasks, daemon=True)
        self.thread.start()
        self.logger.info("Periodic triggers started")

    def stop(self):
        """Stop periodic triggers"""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("Periodic triggers stopped")

    def _run_periodic_tasks(self):
        """Run periodic tasks"""
        last_watcher_check = datetime.utcnow()

        while self.running:
            try:
                now = datetime.utcnow()

                # Check watchers every 5 minutes
                if (now - last_watcher_check) > timedelta(minutes=5):
                    self.logger.info("Periodic: Checking if watchers are running")
                    # Could check if run_all_watchers.py is running and restart if needed
                    last_watcher_check = now

                # Sleep for 60 seconds
                if self.stop_event.wait(timeout=60):
                    break

            except Exception as e:
                self.logger.error(f"Error in periodic tasks: {e}")
                time.sleep(60)


# ============================================================================
# GOLD TIER COMPONENTS - NEW ADDITIONS
# ============================================================================


class EventBus:
    """Central pub/sub event bus for inter-component communication"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.subscribers: Dict[str, List[Callable]] = {}
        self.lock = Lock()

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event type"""
        with self.lock:
            if event_type not in self.subscribers:
                self.subscribers[event_type] = []
            self.subscribers[event_type].append(callback)
            self.logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event type"""
        with self.lock:
            if event_type in self.subscribers:
                try:
                    self.subscribers[event_type].remove(callback)
                    self.logger.debug(f"Unsubscribed from event: {event_type}")
                except ValueError:
                    pass

    def publish(self, event_type: str, data: Dict[str, Any]):
        """Publish an event to all subscribers"""
        with self.lock:
            subscribers = self.subscribers.get(event_type, []).copy()

        if subscribers:
            self.logger.debug(f"Publishing event: {event_type} to {len(subscribers)} subscribers")
            for callback in subscribers:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Error in event subscriber for {event_type}: {e}")

    def clear(self):
        """Clear all subscriptions"""
        with self.lock:
            self.subscribers.clear()


class RetryPolicy(Enum):
    """Retry policy types"""
    EXPONENTIAL = "exponential"
    LINEAR = "linear"
    FIXED = "fixed"


class RetryQueue:
    """Queue for failed operations with exponential backoff retry"""

    def __init__(self, logger: logging.Logger, max_retries: int = 5):
        self.logger = logger
        self.max_retries = max_retries
        self.queue: deque = deque()
        self.lock = Lock()
        self.running = False
        self.thread = None
        self.stop_event = Event()

    def enqueue(self, operation: Callable, args: tuple = (), kwargs: dict = None,
                policy: RetryPolicy = RetryPolicy.EXPONENTIAL, context: Dict = None):
        """Add operation to retry queue"""
        with self.lock:
            retry_item = {
                'operation': operation,
                'args': args,
                'kwargs': kwargs or {},
                'policy': policy,
                'context': context or {},
                'attempts': 0,
                'next_retry': datetime.utcnow(),
                'created_at': datetime.utcnow()
            }
            self.queue.append(retry_item)
            self.logger.info(f"Enqueued operation for retry: {context.get('name', 'unknown')}")

    def start(self):
        """Start retry queue processor"""
        self.running = True
        self.thread = Thread(target=self._process_queue, daemon=True)
        self.thread.start()
        self.logger.info("RetryQueue started")

    def stop(self):
        """Stop retry queue processor"""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("RetryQueue stopped")

    def _calculate_backoff(self, attempts: int, policy: RetryPolicy) -> int:
        """Calculate backoff delay in seconds"""
        if policy == RetryPolicy.EXPONENTIAL:
            return min(300, 2 ** attempts)  # Max 5 minutes
        elif policy == RetryPolicy.LINEAR:
            return min(300, 30 * attempts)  # 30s, 60s, 90s...
        else:  # FIXED
            return 60

    def _process_queue(self):
        """Process retry queue"""
        while self.running:
            try:
                now = datetime.utcnow()
                items_to_retry = []

                with self.lock:
                    # Find items ready for retry
                    for item in list(self.queue):
                        if item['next_retry'] <= now:
                            items_to_retry.append(item)
                            self.queue.remove(item)

                # Process items outside lock
                for item in items_to_retry:
                    self._retry_operation(item)

                # Sleep for 5 seconds
                if self.stop_event.wait(timeout=5):
                    break

            except Exception as e:
                self.logger.error(f"Error processing retry queue: {e}")
                time.sleep(5)

    def _retry_operation(self, item: Dict):
        """Retry a single operation"""
        item['attempts'] += 1
        context = item['context']
        operation_name = context.get('name', 'unknown')

        self.logger.info(f"Retrying operation: {operation_name} (attempt {item['attempts']}/{self.max_retries})")

        try:
            # Execute operation
            result = item['operation'](*item['args'], **item['kwargs'])

            # Check if successful
            if isinstance(result, dict) and result.get('success'):
                self.logger.info(f"Retry successful for: {operation_name}")
                return True
            else:
                raise Exception(f"Operation returned failure: {result}")

        except Exception as e:
            self.logger.warning(f"Retry failed for {operation_name}: {e}")

            # Re-enqueue if under max retries
            if item['attempts'] < self.max_retries:
                backoff = self._calculate_backoff(item['attempts'], item['policy'])
                item['next_retry'] = datetime.utcnow() + timedelta(seconds=backoff)

                with self.lock:
                    self.queue.append(item)

                self.logger.info(f"Re-enqueued {operation_name}, next retry in {backoff}s")
            else:
                self.logger.error(f"Max retries exceeded for {operation_name}, giving up")
                return False

    def get_queue_size(self) -> int:
        """Get current queue size"""
        with self.lock:
            return len(self.queue)


class ComponentStatus(Enum):
    """Component health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class HealthMonitor:
    """Monitors health of all system components"""

    def __init__(self, logger: logging.Logger, check_interval: int = 60):
        self.logger = logger
        self.check_interval = check_interval
        self.component_status: Dict[str, Dict] = {}
        self.lock = Lock()
        self.running = False
        self.thread = None
        self.stop_event = Event()
        self.health_checks: Dict[str, Callable] = {}

    def register_component(self, name: str, health_check: Callable):
        """Register a component with its health check function"""
        with self.lock:
            self.health_checks[name] = health_check
            self.component_status[name] = {
                'status': ComponentStatus.UNKNOWN,
                'last_check': None,
                'message': 'Not yet checked'
            }
        self.logger.info(f"Registered health check for: {name}")

    def start(self):
        """Start health monitoring"""
        self.running = True
        self.thread = Thread(target=self._monitor_health, daemon=True)
        self.thread.start()
        self.logger.info("HealthMonitor started")

    def stop(self):
        """Stop health monitoring"""
        self.running = False
        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)
        self.logger.info("HealthMonitor stopped")

    def _monitor_health(self):
        """Monitor component health"""
        while self.running:
            try:
                self._check_all_components()

                # Sleep for check interval
                if self.stop_event.wait(timeout=self.check_interval):
                    break

            except Exception as e:
                self.logger.error(f"Error in health monitoring: {e}")
                time.sleep(self.check_interval)

    def _check_all_components(self):
        """Check health of all registered components"""
        with self.lock:
            checks = self.health_checks.copy()

        for name, health_check in checks.items():
            try:
                result = health_check()
                status = result.get('status', ComponentStatus.UNKNOWN)
                message = result.get('message', 'No message')

                with self.lock:
                    self.component_status[name] = {
                        'status': status,
                        'last_check': datetime.utcnow(),
                        'message': message
                    }

                if status != ComponentStatus.HEALTHY:
                    self.logger.warning(f"Component {name} is {status.value}: {message}")

            except Exception as e:
                self.logger.error(f"Health check failed for {name}: {e}")
                with self.lock:
                    self.component_status[name] = {
                        'status': ComponentStatus.UNHEALTHY,
                        'last_check': datetime.utcnow(),
                        'message': f"Health check error: {str(e)}"
                    }

    def get_system_health(self) -> Dict:
        """Get overall system health status"""
        with self.lock:
            status_copy = self.component_status.copy()

        # Determine overall status
        statuses = [comp['status'] for comp in status_copy.values()]

        if all(s == ComponentStatus.HEALTHY for s in statuses):
            overall = ComponentStatus.HEALTHY
        elif any(s == ComponentStatus.UNHEALTHY for s in statuses):
            overall = ComponentStatus.UNHEALTHY
        elif any(s == ComponentStatus.DEGRADED for s in statuses):
            overall = ComponentStatus.DEGRADED
        else:
            overall = ComponentStatus.UNKNOWN

        return {
            'overall_status': overall,
            'components': status_copy,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }

    def get_component_status(self, name: str) -> Optional[Dict]:
        """Get status of specific component"""
        with self.lock:
            return self.component_status.get(name)


class AuditLogger:
    """Structured audit logging for compliance and debugging"""

    def __init__(self, logs_dir: Path, logger: logging.Logger):
        self.logs_dir = logs_dir
        self.logger = logger
        self.audit_file = logs_dir / "audit.jsonl"
        self.lock = Lock()

    def log_event(self, event_type: str, actor: str, action: str,
                  resource: str, result: str, metadata: Dict = None):
        """Log an audit event"""
        try:
            audit_entry = {
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'event_type': event_type,
                'actor': actor,
                'action': action,
                'resource': resource,
                'result': result,
                'metadata': metadata or {}
            }

            with self.lock:
                with open(self.audit_file, 'a') as f:
                    f.write(json.dumps(audit_entry) + '\n')

        except Exception as e:
            self.logger.error(f"Error writing audit log: {e}")

    def log_skill_execution(self, skill_name: str, args: List[str],
                           result: Dict, duration: float):
        """Log skill execution"""
        self.log_event(
            event_type='skill_execution',
            actor='system',
            action='execute_skill',
            resource=skill_name,
            result='success' if result.get('success') else 'failure',
            metadata={
                'args': args,
                'duration_seconds': duration,
                'returncode': result.get('returncode'),
                'error': result.get('error')
            }
        )

    def log_approval_decision(self, approval_id: str, decision: str,
                             resource: str, metadata: Dict = None):
        """Log approval decision"""
        self.log_event(
            event_type='approval_decision',
            actor='human',
            action=decision,
            resource=resource,
            result='recorded',
            metadata=metadata
        )

    def log_email_action(self, action: str, recipient: str, subject: str,
                        result: str, metadata: Dict = None):
        """Log email action"""
        self.log_event(
            event_type='email_action',
            actor='system',
            action=action,
            resource=f"email_to_{recipient}",
            result=result,
            metadata={
                'subject': subject,
                **(metadata or {})
            }
        )

    def query_logs(self, event_type: str = None, start_time: datetime = None,
                   end_time: datetime = None, limit: int = 100) -> List[Dict]:
        """Query audit logs with filters"""
        try:
            results = []

            if not self.audit_file.exists():
                return results

            with open(self.audit_file, 'r') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())

                        # Apply filters
                        if event_type and entry.get('event_type') != event_type:
                            continue

                        entry_time = datetime.fromisoformat(entry['timestamp'].replace('Z', '+00:00'))

                        if start_time and entry_time < start_time:
                            continue

                        if end_time and entry_time > end_time:
                            continue

                        results.append(entry)

                        if len(results) >= limit:
                            break

                    except json.JSONDecodeError:
                        continue

            return results

        except Exception as e:
            self.logger.error(f"Error querying audit logs: {e}")
            return []


class SkillRegistry:
    """Registry wrapper around SkillDispatcher with enhanced capabilities"""

    def __init__(self, dispatcher: SkillDispatcher, event_bus: EventBus,
                 retry_queue: RetryQueue, audit_logger: AuditLogger,
                 logger: logging.Logger):
        self.dispatcher = dispatcher
        self.event_bus = event_bus
        self.retry_queue = retry_queue
        self.audit_logger = audit_logger
        self.logger = logger
        self.skill_metadata: Dict[str, Dict] = {}
        self.lock = Lock()

    def register_skill(self, skill_name: str, metadata: Dict = None):
        """Register a skill with metadata"""
        with self.lock:
            self.skill_metadata[skill_name] = {
                'name': skill_name,
                'registered_at': datetime.utcnow().isoformat() + 'Z',
                'execution_count': 0,
                'last_execution': None,
                'metadata': metadata or {}
            }
        self.logger.info(f"Registered skill: {skill_name}")

    def execute_skill(self, skill_name: str, args: List[str] = None,
                     retry_on_failure: bool = True) -> Dict:
        """Execute skill with enhanced error handling and retry"""
        start_time = time.time()

        # Publish pre-execution event
        self.event_bus.publish('skill_execution_started', {
            'skill_name': skill_name,
            'args': args,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

        # Execute skill
        result = self.dispatcher.execute_skill(skill_name, args)
        duration = time.time() - start_time

        # Update metadata
        with self.lock:
            if skill_name in self.skill_metadata:
                self.skill_metadata[skill_name]['execution_count'] += 1
                self.skill_metadata[skill_name]['last_execution'] = datetime.utcnow().isoformat() + 'Z'

        # Audit log
        self.audit_logger.log_skill_execution(skill_name, args or [], result, duration)

        # Handle failure
        if not result.get('success') and retry_on_failure:
            self.logger.warning(f"Skill {skill_name} failed, enqueueing for retry")
            # Use SkillRegistry.execute_skill (not dispatcher) to ensure audit logging and events
            self.retry_queue.enqueue(
                operation=self.execute_skill,
                args=(skill_name, args),
                kwargs={'retry_on_failure': False},  # Prevent infinite retry loop
                context={'name': f"skill_{skill_name}", 'skill': skill_name}
            )

        # Publish post-execution event
        self.event_bus.publish('skill_execution_completed', {
            'skill_name': skill_name,
            'success': result.get('success'),
            'duration': duration,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })

        return result

    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """Get skill metadata"""
        with self.lock:
            return self.skill_metadata.get(skill_name)

    def list_skills(self) -> List[Dict]:
        """List all registered skills"""
        with self.lock:
            return list(self.skill_metadata.values())


class GracefulDegradation:
    """Handles graceful degradation when components fail"""

    def __init__(self, health_monitor: HealthMonitor, logger: logging.Logger):
        self.health_monitor = health_monitor
        self.logger = logger
        self.degraded_mode = False
        self.disabled_features: Set[str] = set()

    def check_and_degrade(self) -> bool:
        """Check system health and enable degradation if needed"""
        health = self.health_monitor.get_system_health()
        overall_status = health['overall_status']

        if overall_status == ComponentStatus.UNHEALTHY:
            if not self.degraded_mode:
                self.logger.warning("System unhealthy, entering degraded mode")
                self._enter_degraded_mode(health['components'])
            return True
        elif overall_status == ComponentStatus.DEGRADED:
            self.logger.info("System degraded, some features may be limited")
            return True
        else:
            if self.degraded_mode:
                self.logger.info("System recovered, exiting degraded mode")
                self._exit_degraded_mode()
            return False

    def _enter_degraded_mode(self, components: Dict):
        """Enter degraded mode and disable non-critical features"""
        self.degraded_mode = True

        # Disable non-critical features based on component health
        for name, status in components.items():
            if status['status'] == ComponentStatus.UNHEALTHY:
                if 'email' in name.lower():
                    self.disabled_features.add('email_sending')
                    self.logger.warning("Disabled email sending due to unhealthy component")
                elif 'periodic' in name.lower():
                    self.disabled_features.add('periodic_triggers')
                    self.logger.warning("Disabled periodic triggers due to unhealthy component")

    def _exit_degraded_mode(self):
        """Exit degraded mode and re-enable features"""
        self.degraded_mode = False
        self.disabled_features.clear()
        self.logger.info("All features re-enabled")

    def is_feature_enabled(self, feature: str) -> bool:
        """Check if a feature is enabled"""
        return feature not in self.disabled_features


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
                    if last_check_key in self.task_failure_counts:
                        del self.task_failure_counts[last_check_key]

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


class IntegrationOrchestrator:
    """Main orchestrator class - Enhanced with Gold Tier architecture"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.skills_dir = base_dir / "Skills"
        self.logs_dir = base_dir / "Logs"
        self.state_file = Path(__file__).parent / "state.json"  # Enhanced state file
        self.approval_state_file = Path(__file__).parent / "processed_approvals.json"
        self.mcp_server_path = base_dir / "mcp_servers" / "email_mcp"

        # Monitored directories
        self.inbox_dir = base_dir / "Inbox"
        self.needs_action_dir = base_dir / "Needs_Action"
        self.pending_approval_dir = base_dir / "Pending_Approval"
        self.pending_approval_email_dir = base_dir / "Pending_Approval" / "email"
        self.approved_dir = base_dir / "Approved"
        self.rejected_dir = base_dir / "Rejected"
        self.done_dir = base_dir / "Done"

        # Existing components (preserved)
        self.logger = None
        self.state_manager = None
        self.approval_manager = None
        self.dispatcher = None
        self.email_executor = None
        self.event_router = None
        self.observer = None
        self.periodic_trigger = None

        # Gold Tier components (new)
        self.event_bus = None
        self.retry_queue = None
        self.health_monitor = None
        self.audit_logger = None
        self.skill_registry = None
        self.graceful_degradation = None
        self.autonomous_executor = None  # Autonomous Execution Layer
        self.social_adapter = None  # Social Media Skills Adapter

        # Running state
        self.running = False

        # Setup
        self._setup_directories()
        self._setup_logging()
        self._setup_components()
        self._setup_gold_tier_components()
        self._register_health_checks()
        self._setup_event_subscriptions()

    def _setup_directories(self):
        """Ensure all required directories exist"""
        directories = [
            self.inbox_dir,
            self.needs_action_dir,
            self.pending_approval_dir,
            self.pending_approval_email_dir,
            self.approved_dir,
            self.rejected_dir,
            self.done_dir,
            self.logs_dir
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def _setup_logging(self):
        """Setup logging"""
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = self.logs_dir / "integration_orchestrator.log"

        self.logger = logging.getLogger("integration_orchestrator")
        self.logger.setLevel(logging.INFO)
        self.logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '[%(asctime)s] [%(name)s] [%(levelname)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def _setup_components(self):
        """Setup orchestrator components (existing) - Updated to integrate Gold Tier"""
        self.state_manager = StateManager(self.state_file)
        self.approval_manager = ApprovalManager(self.approval_state_file)
        self.dispatcher = SkillDispatcher(self.skills_dir, self.logger)
        self.email_executor = EmailExecutor(self.mcp_server_path, self.logs_dir, self.logger)

        # Note: EventRouter will be re-initialized after Gold Tier components are ready
        # This is a temporary initialization for backward compatibility
        self.event_router = EventRouter(
            self.dispatcher,
            self.state_manager,
            self.approval_manager,
            self.email_executor,
            self.base_dir,
            self.logger
        )
        self.periodic_trigger = PeriodicTrigger(self.dispatcher, self.logger)

    def _reinitialize_event_router(self):
        """Reinitialize EventRouter with Gold Tier components"""
        self.event_router = EventRouter(
            self.dispatcher,
            self.state_manager,
            self.approval_manager,
            self.email_executor,
            self.base_dir,
            self.logger,
            skill_registry=self.skill_registry,
            event_bus=self.event_bus,
            graceful_degradation=self.graceful_degradation
        )
        self.logger.info("EventRouter reinitialized with Gold Tier components")

    def _setup_gold_tier_components(self):
        """Setup Gold Tier components (new)"""
        self.logger.info("Initializing Gold Tier components...")

        # Event Bus
        self.event_bus = EventBus(self.logger)
        self.logger.info("EventBus initialized")

        # Retry Queue
        self.retry_queue = RetryQueue(self.logger, max_retries=5)
        self.logger.info("RetryQueue initialized")

        # Health Monitor
        self.health_monitor = HealthMonitor(self.logger, check_interval=60)
        self.logger.info("HealthMonitor initialized")

        # Audit Logger
        self.audit_logger = AuditLogger(self.logs_dir, self.logger)
        self.logger.info("AuditLogger initialized")

        # Skill Registry (wraps existing dispatcher)
        self.skill_registry = SkillRegistry(
            self.dispatcher,
            self.event_bus,
            self.retry_queue,
            self.audit_logger,
            self.logger
        )
        self.logger.info("SkillRegistry initialized")

        # Graceful Degradation
        self.graceful_degradation = GracefulDegradation(self.health_monitor, self.logger)
        self.logger.info("GracefulDegradation initialized")

        # Circuit Breaker Manager
        from Skills.integration_orchestrator.core import CircuitBreakerManager
        self.circuit_breaker_manager = CircuitBreakerManager(
            logger=self.logger,
            event_bus=self.event_bus,
            state_manager=self.state_manager,
            failure_threshold=5,
            recovery_timeout=300
        )
        self.logger.info("CircuitBreakerManager initialized")

        # Autonomous Executor (Ralph Wiggum Loop)
        self.autonomous_executor = AutonomousExecutor(
            event_bus=self.event_bus,
            retry_queue=self.retry_queue,
            state_manager=self.state_manager,
            health_monitor=self.health_monitor,
            skill_registry=self.skill_registry,
            audit_logger=self.audit_logger,
            base_dir=self.base_dir,
            logger=self.logger,
            check_interval=30,  # Check every 30 seconds
            failure_threshold=3  # Escalate after 3 failures
        )
        # Pass orchestrator reference for social_adapter access
        self.autonomous_executor.orchestrator = self
        self.logger.info("AutonomousExecutor initialized")

        # Reinitialize EventRouter with Gold Tier components
        self._reinitialize_event_router()

        # Auto-discover and register skills
        self._discover_skills()

        # Register social media skills
        self._register_social_media_skills()

        self.logger.info("Gold Tier components initialized successfully")

    def _discover_skills(self):
        """Auto-discover and register skills"""
        try:
            if not self.skills_dir.exists():
                return

            for skill_path in self.skills_dir.iterdir():
                if skill_path.is_dir() and not skill_path.name.startswith('.'):
                    # Check if it has an executable
                    has_executable = any([
                        (skill_path / "index.js").exists(),
                        (skill_path / "index.py").exists(),
                        (skill_path / "process_needs_action.py").exists(),
                        (skill_path / "run.sh").exists()
                    ])

                    if has_executable:
                        self.skill_registry.register_skill(
                            skill_path.name,
                            metadata={'path': str(skill_path)}
                        )

        except Exception as e:
            self.logger.error(f"Error discovering skills: {e}")

    def _register_social_media_skills(self):
        """Register social media skills with SkillRegistry"""
        if not SOCIAL_SKILLS_AVAILABLE:
            self.logger.warning("Social media skills module not available")
            return

        try:
            reports_dir = self.base_dir / "Reports" / "Social"
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Register skills and get adapter
            self.social_adapter = register_social_skills(
                skill_registry=self.skill_registry,
                logger=self.logger,
                event_bus=self.event_bus,
                audit_logger=self.audit_logger,
                retry_queue=self.retry_queue,
                reports_dir=reports_dir,
                mcp_server=None  # Can be added later if MCP integration needed
            )

            self.logger.info("Social media skills registered successfully")
            self.logger.info(f"Available platforms: {self.social_adapter.list_platforms()}")

        except Exception as e:
            self.logger.error(f"Failed to register social media skills: {e}", exc_info=True)

    def _register_health_checks(self):
        """Register health checks for all components"""

        # State Manager health check
        def check_state_manager():
            try:
                # Check if state file is writable
                test_key = '_health_check'
                self.state_manager.set_system_state(test_key, datetime.utcnow().isoformat())
                return {
                    'status': ComponentStatus.HEALTHY,
                    'message': 'State manager operational'
                }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'State manager error: {str(e)}'
                }

        # Dispatcher health check
        def check_dispatcher():
            try:
                if self.skills_dir.exists():
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': 'Skill dispatcher operational'
                    }
                else:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': 'Skills directory not found'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Dispatcher error: {str(e)}'
                }

        # Email executor health check
        def check_email_executor():
            try:
                if self.mcp_server_path.exists():
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': 'Email executor operational'
                    }
                else:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': 'MCP server path not found'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Email executor error: {str(e)}'
                }

        # Retry queue health check
        def check_retry_queue():
            try:
                queue_size = self.retry_queue.get_queue_size()
                if queue_size > 100:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': f'Retry queue large: {queue_size} items'
                    }
                return {
                    'status': ComponentStatus.HEALTHY,
                    'message': f'Retry queue operational ({queue_size} items)'
                }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Retry queue error: {str(e)}'
                }

        # Filesystem watcher health check
        def check_filesystem_watcher():
            try:
                if self.observer and self.observer.is_alive():
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': 'Filesystem watcher operational'
                    }
                else:
                    return {
                        'status': ComponentStatus.UNHEALTHY,
                        'message': 'Filesystem watcher not running'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Watcher error: {str(e)}'
                }

        # System resources health check
        def check_system_resources():
            try:
                if not PSUTIL_AVAILABLE:
                    return {
                        'status': ComponentStatus.UNKNOWN,
                        'message': 'psutil not available, cannot check resources'
                    }

                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()

                if cpu_percent > 90 or memory.percent > 90:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': f'High resource usage: CPU {cpu_percent}%, Memory {memory.percent}%'
                    }
                return {
                    'status': ComponentStatus.HEALTHY,
                    'message': f'Resources normal: CPU {cpu_percent}%, Memory {memory.percent}%'
                }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNKNOWN,
                    'message': f'Cannot check resources: {str(e)}'
                }

        # Autonomous executor health check
        def check_autonomous_executor():
            try:
                if self.autonomous_executor and self.autonomous_executor.running:
                    status_info = self.autonomous_executor.get_status()
                    tracked_tasks = status_info.get('tracked_tasks', 0)

                    if tracked_tasks > 5:
                        return {
                            'status': ComponentStatus.DEGRADED,
                            'message': f'Many tracked failures: {tracked_tasks} tasks'
                        }
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': f'Autonomous executor operational ({tracked_tasks} tracked tasks)'
                    }
                else:
                    return {
                        'status': ComponentStatus.UNHEALTHY,
                        'message': 'Autonomous executor not running'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Autonomous executor error: {str(e)}'
                }

        # Register all health checks
        self.health_monitor.register_component('state_manager', check_state_manager)
        self.health_monitor.register_component('skill_dispatcher', check_dispatcher)
        self.health_monitor.register_component('email_executor', check_email_executor)
        self.health_monitor.register_component('retry_queue', check_retry_queue)
        self.health_monitor.register_component('filesystem_watcher', check_filesystem_watcher)
        self.health_monitor.register_component('system_resources', check_system_resources)
        self.health_monitor.register_component('autonomous_executor', check_autonomous_executor)

        self.logger.info("Health checks registered")

    def _setup_event_subscriptions(self):
        """Setup event bus subscriptions"""

        # Subscribe to skill execution events
        def on_skill_started(data):
            self.logger.debug(f"Skill started: {data.get('skill_name')}")
            self.state_manager.increment_counter('skills_started')

        def on_skill_completed(data):
            skill_name = data.get('skill_name')
            success = data.get('success')
            duration = data.get('duration')

            if success:
                self.logger.info(f"Skill completed successfully: {skill_name} ({duration:.2f}s)")
                self.state_manager.increment_counter('skills_succeeded')
            else:
                self.logger.warning(f"Skill failed: {skill_name}")
                self.state_manager.increment_counter('skills_failed')

        # Subscribe to events
        self.event_bus.subscribe('skill_execution_started', on_skill_started)
        self.event_bus.subscribe('skill_execution_completed', on_skill_completed)

        self.logger.info("Event subscriptions configured")

    def _setup_watchers(self):
        """Setup filesystem watchers"""
        self.observer = Observer()

        # Watch Inbox
        if self.inbox_dir.exists():
            handler = FolderWatcherHandler("inbox", self.event_router, self.logger)
            self.observer.schedule(handler, str(self.inbox_dir), recursive=False)
            self.logger.info(f"Watching: {self.inbox_dir}")

        # Watch Needs_Action
        if self.needs_action_dir.exists():
            handler = FolderWatcherHandler("needs_action", self.event_router, self.logger)
            self.observer.schedule(handler, str(self.needs_action_dir), recursive=False)
            self.logger.info(f"Watching: {self.needs_action_dir}")

        # Watch Pending_Approval
        if self.pending_approval_dir.exists():
            handler = FolderWatcherHandler("pending_approval", self.event_router, self.logger)
            self.observer.schedule(handler, str(self.pending_approval_dir), recursive=False)
            self.logger.info(f"Watching: {self.pending_approval_dir}")

        # Watch Pending_Approval/email (Human-in-the-Loop)
        if self.pending_approval_email_dir.exists():
            handler = FolderWatcherHandler("pending_approval_email", self.event_router, self.logger)
            self.observer.schedule(handler, str(self.pending_approval_email_dir), recursive=False)
            self.logger.info(f"Watching: {self.pending_approval_email_dir}")

        # Watch Approved (Human approved emails)
        if self.approved_dir.exists():
            handler = FolderWatcherHandler("approved", self.event_router, self.logger)
            self.observer.schedule(handler, str(self.approved_dir), recursive=False)
            self.logger.info(f"Watching: {self.approved_dir}")

        # Watch Rejected (Human rejected emails)
        if self.rejected_dir.exists():
            handler = FolderWatcherHandler("rejected", self.event_router, self.logger)
            self.observer.schedule(handler, str(self.rejected_dir), recursive=False)
            self.logger.info(f"Watching: {self.rejected_dir}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False

    def start(self):
        """Start the orchestrator - Enhanced with Gold Tier components"""
        self.logger.info("=" * 60)
        self.logger.info("Integration Orchestrator Starting (Gold Tier)")
        self.logger.info("=" * 60)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Start Gold Tier components first
        self.logger.info("Starting Gold Tier components...")

        # Start retry queue
        self.retry_queue.start()

        # Start health monitor
        self.health_monitor.start()

        # Start autonomous executor
        self.autonomous_executor.start()

        # Setup filesystem watchers
        self._setup_watchers()

        # Start observer
        self.observer.start()
        self.logger.info("Filesystem watchers started")

        # Start periodic triggers
        self.periodic_trigger.start()

        self.running = True

        # Log system health
        health = self.health_monitor.get_system_health()
        self.logger.info(f"System health: {health['overall_status'].value}")

        # Record startup in state
        self.state_manager.set_system_state('last_startup', datetime.utcnow().isoformat() + 'Z')
        self.state_manager.set_system_state('orchestrator_version', 'gold_tier_v1.0')

        # Audit log startup
        self.audit_logger.log_event(
            event_type='system_lifecycle',
            actor='system',
            action='startup',
            resource='orchestrator',
            result='success',
            metadata={'version': 'gold_tier_v1.0'}
        )

        self.logger.info("Orchestrator running - Press Ctrl+C to stop")

        # Main loop with health monitoring
        try:
            last_health_check = datetime.utcnow()

            while self.running:
                time.sleep(1)

                # Periodic health check and degradation handling (every 30 seconds)
                now = datetime.utcnow()
                if (now - last_health_check) > timedelta(seconds=30):
                    self.graceful_degradation.check_and_degrade()
                    last_health_check = now

        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    def post_to_social_media(self, platform: str, message: str,
                            media: List[str] = None, metadata: Dict = None) -> Dict:
        """
        Post to social media platform.

        Args:
            platform: Platform name ('facebook', 'instagram', 'twitter_x')
            message: Post message
            media: Optional media files
            metadata: Optional metadata

        Returns:
            Result dictionary with success status and post details
        """
        if not self.social_adapter:
            return {
                'success': False,
                'error': 'Social media skills not initialized'
            }

        return self.social_adapter.post(platform, message, media, metadata)

    def stop(self):
        """Stop the orchestrator - Enhanced with Gold Tier components"""
        self.logger.info("Stopping orchestrator...")

        # Audit log shutdown
        self.audit_logger.log_event(
            event_type='system_lifecycle',
            actor='system',
            action='shutdown',
            resource='orchestrator',
            result='initiated',
            metadata={}
        )

        # Stop periodic triggers
        if self.periodic_trigger:
            self.periodic_trigger.stop()

        # Stop observer
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)

        # Stop Gold Tier components
        self.logger.info("Stopping Gold Tier components...")

        # Stop autonomous executor first (it depends on other components)
        if self.autonomous_executor:
            self.autonomous_executor.stop()

        # Stop health monitor
        if self.health_monitor:
            self.health_monitor.stop()

        # Stop retry queue (allow pending retries to complete)
        if self.retry_queue:
            queue_size = self.retry_queue.get_queue_size()
            if queue_size > 0:
                self.logger.warning(f"Stopping with {queue_size} items in retry queue")
            self.retry_queue.stop()

        # Clear event bus
        if self.event_bus:
            self.event_bus.clear()

        # Record shutdown in state
        self.state_manager.set_system_state('last_shutdown', datetime.utcnow().isoformat() + 'Z')

        # Final audit log
        self.audit_logger.log_event(
            event_type='system_lifecycle',
            actor='system',
            action='shutdown',
            resource='orchestrator',
            result='success',
            metadata={'pending_retries': queue_size if self.retry_queue else 0}
        )

        self.logger.info("Orchestrator stopped")

    def get_status(self) -> Dict:
        """Get comprehensive orchestrator status - Gold Tier feature"""
        try:
            health = self.health_monitor.get_system_health()
            queue_size = self.retry_queue.get_queue_size()
            registered_skills = len(self.skill_registry.list_skills())

            # Get metrics from state manager
            skills_started = self.state_manager.get_metric('skills_started')
            skills_succeeded = self.state_manager.get_metric('skills_succeeded')
            skills_failed = self.state_manager.get_metric('skills_failed')

            # Get autonomous executor status
            autonomous_status = self.autonomous_executor.get_status() if self.autonomous_executor else {}

            return {
                'running': self.running,
                'health': health,
                'retry_queue_size': queue_size,
                'registered_skills': registered_skills,
                'degraded_mode': self.graceful_degradation.degraded_mode,
                'disabled_features': list(self.graceful_degradation.disabled_features),
                'autonomous_executor': autonomous_status,
                'metrics': {
                    'skills_started': skills_started.get('value', 0) if skills_started else 0,
                    'skills_succeeded': skills_succeeded.get('value', 0) if skills_succeeded else 0,
                    'skills_failed': skills_failed.get('value', 0) if skills_failed else 0
                },
                'last_startup': self.state_manager.get_system_state('last_startup'),
                'version': self.state_manager.get_system_state('orchestrator_version', 'unknown')
            }
        except Exception as e:
            self.logger.error(f"Error getting status: {e}")
            return {'error': str(e)}

    def get_health_report(self) -> str:
        """Get human-readable health report - Gold Tier feature"""
        try:
            status = self.get_status()
            health = status.get('health', {})
            overall = health.get('overall_status', ComponentStatus.UNKNOWN)

            report = []
            report.append("=" * 60)
            report.append("ORCHESTRATOR HEALTH REPORT")
            report.append("=" * 60)
            report.append(f"Overall Status: {overall.value.upper()}")
            report.append(f"Running: {status.get('running')}")
            report.append(f"Version: {status.get('version')}")
            report.append("")

            # Component health
            report.append("Component Health:")
            components = health.get('components', {})
            for name, comp_status in components.items():
                status_str = comp_status['status'].value
                message = comp_status['message']
                report.append(f"  - {name}: {status_str} - {message}")

            report.append("")

            # Metrics
            metrics = status.get('metrics', {})
            report.append("Metrics:")
            report.append(f"  - Skills Started: {metrics.get('skills_started', 0)}")
            report.append(f"  - Skills Succeeded: {metrics.get('skills_succeeded', 0)}")
            report.append(f"  - Skills Failed: {metrics.get('skills_failed', 0)}")
            report.append(f"  - Retry Queue Size: {status.get('retry_queue_size', 0)}")
            report.append(f"  - Registered Skills: {status.get('registered_skills', 0)}")

            report.append("")

            # Autonomous Executor status
            autonomous = status.get('autonomous_executor', {})
            if autonomous:
                report.append("Autonomous Executor:")
                report.append(f"  - Running: {autonomous.get('running', False)}")
                report.append(f"  - Check Interval: {autonomous.get('check_interval', 0)}s")
                report.append(f"  - Tracked Tasks: {autonomous.get('tracked_tasks', 0)}")
                report.append(f"  - Last Check: {autonomous.get('last_check', 'Never')}")

            report.append("")

            # Degradation status
            if status.get('degraded_mode'):
                report.append("⚠️  DEGRADED MODE ACTIVE")
                disabled = status.get('disabled_features', [])
                if disabled:
                    report.append(f"Disabled Features: {', '.join(disabled)}")
            else:
                report.append("✓ All features operational")

            report.append("=" * 60)

            return "\n".join(report)

        except Exception as e:
            return f"Error generating health report: {e}"


def main():
    """Main entry point"""
    # Determine base directory
    base_dir = Path(__file__).parent.parent.parent

    # Create and start orchestrator
    orchestrator = IntegrationOrchestrator(base_dir)
    orchestrator.start()


if __name__ == "__main__":
    main()
