#!/usr/bin/env python3
"""
Integration Orchestrator
Central automation controller for AI Employee Vault
Monitors folders, routes events, and triggers skills automatically
Enhanced with Human-in-the-Loop email approval workflow
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
from typing import Dict, List, Optional, Set
from threading import Thread, Event
import hashlib
import shutil

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except ImportError:
    print("Error: watchdog not installed")
    print("Install with: pip install watchdog")
    sys.exit(1)


class StateManager:
    """Manages processed events state"""

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self.processed_events: Dict[str, Dict] = {}
        self.load_state()

    def load_state(self):
        """Load processed events from file"""
        try:
            if self.state_file.exists():
                with open(self.state_file, 'r') as f:
                    self.processed_events = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load state file: {e}")
            self.processed_events = {}

    def save_state(self):
        """Save processed events to file"""
        try:
            with open(self.state_file, 'w') as f:
                json.dump(self.processed_events, f, indent=2)
        except Exception as e:
            print(f"Error saving state: {e}")

    def is_processed(self, event_id: str) -> bool:
        """Check if event has been processed"""
        return event_id in self.processed_events

    def mark_processed(self, event_id: str, metadata: Dict):
        """Mark event as processed"""
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
    """Routes filesystem events to appropriate handlers"""

    def __init__(self, dispatcher: SkillDispatcher, state_manager: StateManager,
                 approval_manager: ApprovalManager, email_executor: EmailExecutor,
                 base_dir: Path, logger: logging.Logger):
        self.dispatcher = dispatcher
        self.state_manager = state_manager
        self.approval_manager = approval_manager
        self.email_executor = email_executor
        self.base_dir = base_dir
        self.logger = logger

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
        """Handle new file in Needs_Action"""
        self.logger.info(f"Processing Needs_Action file: {filepath.name}")

        # Trigger process_needs_action skill
        result = self.dispatcher.execute_skill("process_needs_action")

        return result['success']

    def _handle_pending_approval(self, filepath: Path) -> bool:
        """Handle modified file in Pending_Approval"""
        try:
            # Read file to check status
            with open(filepath, 'r') as f:
                content = f.read()

            # Check if status is approved
            if 'status: approved' in content or 'status:approved' in content:
                self.logger.info(f"Approved file detected: {filepath.name}")

                # Determine which skill to trigger based on file type
                if 'type: linkedin_post' in content:
                    self.logger.info("Triggering LinkedIn post skill")
                    result = self.dispatcher.execute_skill("linkedin_post_skill", ["process"])
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
        """Handle file moved to Approved - Execute email and move to Done"""
        try:
            # Generate approval ID
            approval_id = self.approval_manager.get_approval_hash(filepath)

            # Check if already processed
            if self.approval_manager.is_processed(approval_id):
                self.logger.warning(f"Approval already processed: {filepath.name}")
                return True

            self.logger.info(f"Processing approved email: {filepath.name}")

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


class IntegrationOrchestrator:
    """Main orchestrator class"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.skills_dir = base_dir / "Skills"
        self.logs_dir = base_dir / "Logs"
        self.state_file = Path(__file__).parent / "processed_events.json"
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

        # Components
        self.logger = None
        self.state_manager = None
        self.approval_manager = None
        self.dispatcher = None
        self.email_executor = None
        self.event_router = None
        self.observer = None
        self.periodic_trigger = None

        # Running state
        self.running = False

        # Setup
        self._setup_directories()
        self._setup_logging()
        self._setup_components()

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
        """Setup orchestrator components"""
        self.state_manager = StateManager(self.state_file)
        self.approval_manager = ApprovalManager(self.approval_state_file)
        self.dispatcher = SkillDispatcher(self.skills_dir, self.logger)
        self.email_executor = EmailExecutor(self.mcp_server_path, self.logs_dir, self.logger)
        self.event_router = EventRouter(
            self.dispatcher,
            self.state_manager,
            self.approval_manager,
            self.email_executor,
            self.base_dir,
            self.logger
        )
        self.periodic_trigger = PeriodicTrigger(self.dispatcher, self.logger)

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
        """Start the orchestrator"""
        self.logger.info("=" * 60)
        self.logger.info("Integration Orchestrator Starting")
        self.logger.info("=" * 60)

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Setup filesystem watchers
        self._setup_watchers()

        # Start observer
        self.observer.start()
        self.logger.info("Filesystem watchers started")

        # Start periodic triggers
        self.periodic_trigger.start()

        self.running = True
        self.logger.info("Orchestrator running - Press Ctrl+C to stop")

        # Main loop
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received")
        finally:
            self.stop()

    def stop(self):
        """Stop the orchestrator"""
        self.logger.info("Stopping orchestrator...")

        # Stop periodic triggers
        if self.periodic_trigger:
            self.periodic_trigger.stop()

        # Stop observer
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)

        self.logger.info("Orchestrator stopped")


def main():
    """Main entry point"""
    # Determine base directory
    base_dir = Path(__file__).parent.parent.parent

    # Create and start orchestrator
    orchestrator = IntegrationOrchestrator(base_dir)
    orchestrator.start()


if __name__ == "__main__":
    main()
