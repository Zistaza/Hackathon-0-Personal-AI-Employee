#!/usr/bin/env python3
"""
Integration Orchestrator - Gold Tier Architecture (Refactored)
===============================================================

Central automation controller for AI Employee Vault.
Monitors folders, routes events, and triggers skills automatically.

This file has been refactored to extract components into modular structure:
- core/: EventBus, RetryQueue, HealthMonitor, AuditLogger, StateManager, etc.
- skills/: SkillDispatcher, SkillRegistry
- routing/: EventRouter, FolderWatcherHandler
- execution/: EmailExecutor, PeriodicTrigger, GracefulDegradation, AutonomousExecutor

ARCHITECTURE:
-------------
All components are now in separate modules for better maintainability.
This file contains only the IntegrationOrchestrator class for orchestration.

USAGE:
------
    from Skills.integration_orchestrator.index import IntegrationOrchestrator

    orchestrator = IntegrationOrchestrator(base_dir)
    orchestrator.start()

    # Get system status
    status = orchestrator.get_status()
    print(orchestrator.get_health_report())

BACKWARD COMPATIBILITY:
-----------------------
All components are re-exported from this module for backward compatibility.
Existing code importing from index.py will continue to work.
"""

import os
import sys
import logging
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add parent directory to path for direct execution
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Import core components
try:
    # Try relative imports first (when imported as module)
    from .core import (
        EventBus,
        RetryQueue,
        RetryPolicy,
        HealthMonitor,
        ComponentStatus,
        AuditLogger,
        StateManager,
        ApprovalManager,
        CircuitBreakerManager,
        MCPServerManager,
        FolderManager,
    )
    from .skills import (
        SkillDispatcher,
        SkillRegistry,
    )
    from .routing import (
        EventRouter,
        FolderWatcherHandler,
    )
    from .execution import (
        EmailExecutor,
        PeriodicTrigger,
        GracefulDegradation,
        AutonomousExecutor,
        ApprovedFolderMonitor,
    )
except ImportError:
    # Fall back to absolute imports (when run directly)
    from Skills.integration_orchestrator.core import (
        EventBus,
        RetryQueue,
        RetryPolicy,
        HealthMonitor,
        ComponentStatus,
        AuditLogger,
        StateManager,
        ApprovalManager,
        CircuitBreakerManager,
        MCPServerManager,
        FolderManager,
    )
    from Skills.integration_orchestrator.skills import (
        SkillDispatcher,
        SkillRegistry,
    )
    from Skills.integration_orchestrator.routing import (
        EventRouter,
        FolderWatcherHandler,
    )
    from Skills.integration_orchestrator.execution import (
        EmailExecutor,
        PeriodicTrigger,
        GracefulDegradation,
        AutonomousExecutor,
        ApprovedFolderMonitor,
    )

# Social Media Skills Integration
try:
    try:
        from .social_media_skills import register_social_skills
    except ImportError:
        from Skills.integration_orchestrator.social_media_skills import register_social_skills
    SOCIAL_SKILLS_AVAILABLE = True
except ImportError:
    SOCIAL_SKILLS_AVAILABLE = False

# Enhanced AutonomousExecutor with Social Media Automation
try:
    try:
        from .autonomous_executor_enhanced import SocialMediaAutomation
    except ImportError:
        from Skills.integration_orchestrator.autonomous_executor_enhanced import SocialMediaAutomation
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
    from watchdog.observers.polling import PollingObserver
    from watchdog.events import FileSystemEventHandler, FileSystemEvent
except ImportError:
    print("Error: watchdog not installed")
    print("Install with: pip install watchdog")
    sys.exit(1)


# Re-export components for backward compatibility
__all__ = [
    'IntegrationOrchestrator',
    'EventBus',
    'RetryQueue',
    'RetryPolicy',
    'HealthMonitor',
    'ComponentStatus',
    'AuditLogger',
    'StateManager',
    'ApprovalManager',
    'CircuitBreakerManager',
    'SkillDispatcher',
    'SkillRegistry',
    'EventRouter',
    'FolderWatcherHandler',
    'EmailExecutor',
    'PeriodicTrigger',
    'GracefulDegradation',
    'AutonomousExecutor',
    'FolderManager',
    'ApprovedFolderMonitor',
]


class IntegrationOrchestrator:
    """Main orchestrator class - Enhanced with Gold Tier architecture"""

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
        self.skills_dir = base_dir / "Skills"
        self.logs_dir = base_dir / "Logs"
        self.state_file = Path(__file__).parent / "state.json"
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

        # Component references
        self.logger = None
        self.state_manager = None
        self.approval_manager = None
        self.dispatcher = None
        self.email_executor = None
        self.event_router = None
        self.observer = None
        self.periodic_trigger = None

        # Gold Tier components
        self.event_bus = None
        self.retry_queue = None
        self.health_monitor = None
        self.audit_logger = None
        self.skill_registry = None
        self.graceful_degradation = None
        self.circuit_breaker_manager = None
        self.autonomous_executor = None
        self.social_adapter = None
        self.mcp_manager = None
        self.folder_manager = None
        self.social_media_executor = None
        self.message_sender = None
        self.approved_folder_monitor = None

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
        """Setup core components"""
        self.state_manager = StateManager(self.state_file)
        self.approval_manager = ApprovalManager(self.approval_state_file)
        self.dispatcher = SkillDispatcher(self.skills_dir, self.logger)
        self.email_executor = EmailExecutor(self.mcp_server_path, self.logs_dir, self.logger)
        self.periodic_trigger = PeriodicTrigger(self.logger)

        # EventRouter will be initialized after Gold Tier components
        self.logger.info("Core components initialized")

    def _setup_gold_tier_components(self):
        """Setup Gold Tier components"""
        self.logger.info("Initializing Gold Tier components...")

        # Event Bus
        self.event_bus = EventBus(self.logger)
        self.logger.info("EventBus initialized")

        # Folder Manager (initialize early for HITL architecture)
        self.folder_manager = FolderManager(
            base_dir=self.base_dir,
            event_bus=self.event_bus,
            audit_logger=None,  # Will be set after AuditLogger is initialized
            logger=self.logger
        )
        self.logger.info("FolderManager initialized with HITL architecture")

        # Retry Queue
        self.retry_queue = RetryQueue(self.logger, max_retries=5)
        self.logger.info("RetryQueue initialized")

        # Health Monitor
        self.health_monitor = HealthMonitor(self.logger, check_interval=60)
        self.logger.info("HealthMonitor initialized")

        # Audit Logger
        self.audit_logger = AuditLogger(self.logs_dir, self.logger)
        self.logger.info("AuditLogger initialized")

        # Connect AuditLogger to FolderManager
        if self.folder_manager:
            self.folder_manager.audit_logger = self.audit_logger
            self.logger.info("FolderManager connected to AuditLogger")

        # MCP Server Manager (initialize before SkillRegistry)
        self.mcp_manager = MCPServerManager(
            logger=self.logger,
            event_bus=self.event_bus,
            retry_queue=self.retry_queue,
            audit_logger=self.audit_logger,
            base_dir=self.base_dir
        )
        self.mcp_manager.initialize_servers()
        self.logger.info(f"MCPServerManager initialized with {len(self.mcp_manager.list_servers())} servers")

        # Skill Registry (wraps existing dispatcher with MCP support)
        self.skill_registry = SkillRegistry(
            self.dispatcher,
            self.event_bus,
            self.retry_queue,
            self.audit_logger,
            self.logger,
            mcp_manager=self.mcp_manager
        )
        self.logger.info("SkillRegistry initialized with MCP support")

        # Graceful Degradation
        self.graceful_degradation = GracefulDegradation(self.health_monitor, self.logger)
        self.logger.info("GracefulDegradation initialized")

        # Circuit Breaker Manager
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
            check_interval=30,
            failure_threshold=3
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

        # Register Social Media Executor v2
        self._register_social_media_executor()

        # Register Message Sender v2
        self._register_message_sender()

        # Initialize Approved Folder Monitor (Step 5)
        self._initialize_approved_folder_monitor()

        self.logger.info("Gold Tier components initialized successfully")

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
        """Register social media skills with SkillRegistry - Enterprise Mode"""
        if not SOCIAL_SKILLS_AVAILABLE:
            self.logger.warning("Social media skills module not available")
            return

        try:
            reports_dir = self.base_dir / "Reports" / "Social"
            reports_dir.mkdir(parents=True, exist_ok=True)

            # Register skills and get adapter (Enterprise Mode with state_manager)
            self.social_adapter = register_social_skills(
                skill_registry=self.skill_registry,
                logger=self.logger,
                event_bus=self.event_bus,
                audit_logger=self.audit_logger,
                retry_queue=self.retry_queue,
                reports_dir=reports_dir,
                mcp_server=None,
                state_manager=self.state_manager  # Enterprise: Pass state_manager
            )

            # Enterprise: Connect social_adapter to PeriodicTrigger for scheduled posts
            if hasattr(self, 'periodic_trigger') and self.periodic_trigger:
                self.periodic_trigger.social_adapter = self.social_adapter
                self.logger.info("PeriodicTrigger connected to social_adapter for scheduled posts")

            self.logger.info("Social media skills registered successfully (Enterprise Mode)")
            self.logger.info(f"Available platforms: {self.social_adapter.list_platforms()}")

        except Exception as e:
            self.logger.error(f"Failed to register social media skills: {e}", exc_info=True)

    def _register_social_media_executor(self):
        """Register Social Media Executor v2 with SkillRegistry"""
        try:
            from Skills.social_media_executor.register import register_executor

            self.social_media_executor = register_executor(
                skill_registry=self.skill_registry,
                event_bus=self.event_bus,
                audit_logger=self.audit_logger,
                folder_manager=self.folder_manager,
                logger=self.logger,
                base_dir=self.base_dir
            )

            if self.social_media_executor:
                self.logger.info("Social Media Executor v2 registered successfully")
            else:
                self.logger.warning("Social Media Executor v2 registration returned None")

        except Exception as e:
            self.logger.error(f"Failed to register Social Media Executor v2: {e}", exc_info=True)

    def _register_message_sender(self):
        """Register Message Sender v2 with SkillRegistry"""
        try:
            from Skills.message_sender.register import register_sender

            self.message_sender = register_sender(
                skill_registry=self.skill_registry,
                event_bus=self.event_bus,
                audit_logger=self.audit_logger,
                folder_manager=self.folder_manager,
                logger=self.logger,
                base_dir=self.base_dir
            )

            if self.message_sender:
                self.logger.info("Message Sender v2 registered successfully")
            else:
                self.logger.warning("Message Sender v2 registration returned None")

        except Exception as e:
            self.logger.error(f"Failed to register Message Sender v2: {e}", exc_info=True)

    def _initialize_approved_folder_monitor(self):
        """Initialize Approved Folder Monitor for automatic execution"""
        try:
            # Only initialize if we have both executors
            if not self.social_media_executor or not self.message_sender:
                self.logger.warning("Skipping ApprovedFolderMonitor - executors not available")
                return

            self.approved_folder_monitor = ApprovedFolderMonitor(
                base_dir=self.base_dir,
                event_bus=self.event_bus,
                audit_logger=self.audit_logger,
                folder_manager=self.folder_manager,
                social_media_executor=self.social_media_executor,
                message_sender=self.message_sender,
                logger=self.logger,
                check_interval=30  # Check every 30 seconds
            )

            self.logger.info("ApprovedFolderMonitor initialized (will start with orchestrator)")

        except Exception as e:
            self.logger.error(f"Failed to initialize ApprovedFolderMonitor: {e}", exc_info=True)

    def _register_health_checks(self):
        """Register health checks for all components"""

        # State Manager health check
        def check_state_manager():
            try:
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

        # Skill Dispatcher health check
        def check_skill_dispatcher():
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
                    'message': f'Skill dispatcher error: {str(e)}'
                }

        # Email Executor health check
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

        # Retry Queue health check
        def check_retry_queue():
            try:
                queue_size = self.retry_queue.get_queue_size()
                if queue_size < 10:
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': f'Retry queue operational ({queue_size} items)'
                    }
                else:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': f'Retry queue large ({queue_size} items)'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Retry queue error: {str(e)}'
                }

        # Filesystem Watcher health check
        def check_filesystem_watcher():
            try:
                if self.observer and self.observer.is_alive():
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': 'Filesystem watcher operational'
                    }
                else:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': 'Filesystem watcher not running'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Filesystem watcher error: {str(e)}'
                }

        # System Resources health check (if psutil available)
        def check_system_resources():
            if not PSUTIL_AVAILABLE:
                return {
                    'status': ComponentStatus.UNKNOWN,
                    'message': 'psutil not available'
                }

            try:
                cpu_percent = psutil.cpu_percent(interval=0.1)
                memory = psutil.virtual_memory()

                if cpu_percent < 80 and memory.percent < 80:
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': f'CPU: {cpu_percent}%, Memory: {memory.percent}%'
                    }
                elif cpu_percent < 90 and memory.percent < 90:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': f'High usage - CPU: {cpu_percent}%, Memory: {memory.percent}%'
                    }
                else:
                    return {
                        'status': ComponentStatus.UNHEALTHY,
                        'message': f'Critical usage - CPU: {cpu_percent}%, Memory: {memory.percent}%'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNKNOWN,
                    'message': f'Resource check error: {str(e)}'
                }

        # Autonomous Executor health check
        def check_autonomous_executor():
            try:
                if self.autonomous_executor and self.autonomous_executor.running:
                    return {
                        'status': ComponentStatus.HEALTHY,
                        'message': 'Autonomous executor operational'
                    }
                else:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': 'Autonomous executor not running'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Autonomous executor error: {str(e)}'
                }

        # Approved Folder Monitor health check
        def check_approved_folder_monitor():
            try:
                if self.approved_folder_monitor:
                    status = self.approved_folder_monitor.get_status()
                    if status.get('running') and status.get('thread_alive'):
                        return {
                            'status': ComponentStatus.HEALTHY,
                            'message': f'Approved folder monitor operational (interval: {status.get("check_interval")}s)'
                        }
                    else:
                        return {
                            'status': ComponentStatus.DEGRADED,
                            'message': 'Approved folder monitor not running'
                        }
                else:
                    return {
                        'status': ComponentStatus.DEGRADED,
                        'message': 'Approved folder monitor not initialized'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Approved folder monitor error: {str(e)}'
                }

        # Folder Manager health check
        def check_folder_manager():
            try:
                if self.folder_manager:
                    stats = self.folder_manager.get_stats()
                    pending = stats.get('pending_approval', 0)
                    approved = stats.get('approved', 0)

                    if pending + approved < 100:
                        return {
                            'status': ComponentStatus.HEALTHY,
                            'message': f'Folder manager operational (Pending: {pending}, Approved: {approved})'
                        }
                    else:
                        return {
                            'status': ComponentStatus.DEGRADED,
                            'message': f'High queue count (Pending: {pending}, Approved: {approved})'
                        }
                else:
                    return {
                        'status': ComponentStatus.UNHEALTHY,
                        'message': 'Folder manager not initialized'
                    }
            except Exception as e:
                return {
                    'status': ComponentStatus.UNHEALTHY,
                    'message': f'Folder manager error: {str(e)}'
                }

        # Register all health checks
        self.health_monitor.register_health_check('state_manager', check_state_manager)
        self.health_monitor.register_health_check('skill_dispatcher', check_skill_dispatcher)
        self.health_monitor.register_health_check('email_executor', check_email_executor)
        self.health_monitor.register_health_check('retry_queue', check_retry_queue)
        self.health_monitor.register_health_check('filesystem_watcher', check_filesystem_watcher)
        self.health_monitor.register_health_check('system_resources', check_system_resources)
        self.health_monitor.register_health_check('autonomous_executor', check_autonomous_executor)
        self.health_monitor.register_health_check('approved_folder_monitor', check_approved_folder_monitor)
        self.health_monitor.register_health_check('folder_manager', check_folder_manager)

        self.logger.info("Health checks registered")

    def _setup_event_subscriptions(self):
        """Setup event subscriptions for monitoring"""

        def log_skill_execution(data):
            self.logger.debug(f"Skill execution started: {data.get('skill_name')}")

        def log_skill_completed(data):
            skill_name = data.get('skill_name')
            success = data.get('success')
            duration = data.get('duration', 0)
            self.logger.info(f"Skill {skill_name} {'succeeded' if success else 'failed'} ({duration:.2f}s)")

        def check_retry_queue(data):
            queue_size = data.get('queue_size', 0)
            if queue_size > 10:
                self.logger.warning(f"Retry queue is large: {queue_size} items")

        def on_accounting_transaction_added(data):
            """Cross-domain: Accounting → Reporting integration"""
            self.logger.info(f"Ledger updated: {data.get('type')} ${data.get('amount')} - Triggering report generation")

            # Trigger weekly CEO briefing to regenerate with new data
            try:
                result = self.skill_registry.execute_skill('weekly_ceo_briefing', ['generate'])
                if result.get('success'):
                    self.logger.info("Weekly CEO briefing regenerated successfully")
                else:
                    self.logger.warning(f"Failed to regenerate briefing: {result.get('error')}")
            except Exception as e:
                self.logger.error(f"Error triggering report generation: {e}")

        def on_file_moved_to_approved(data):
            """Log when files are moved to Approved folder"""
            filename = data.get('filename', 'unknown')
            self.logger.info(f"File approved for execution: {filename}")

        def on_file_moved_to_done(data):
            """Log when files are successfully executed"""
            filename = data.get('filename', 'unknown')
            self.logger.info(f"File execution completed: {filename}")

        def on_file_moved_to_failed(data):
            """Log when files fail execution"""
            filename = data.get('filename', 'unknown')
            error = data.get('error', 'unknown error')
            self.logger.warning(f"File execution failed: {filename} - {error}")

        # Subscribe to events
        self.event_bus.subscribe('skill_execution_started', log_skill_execution)
        self.event_bus.subscribe('skill_execution_completed', log_skill_completed)
        self.event_bus.subscribe('retry_queue_status', check_retry_queue)

        # Cross-domain integration: Accounting → Reporting
        self.event_bus.subscribe('accounting_transaction_added', on_accounting_transaction_added)

        # Folder Manager events
        self.event_bus.subscribe('file.moved.to.approved', on_file_moved_to_approved)
        self.event_bus.subscribe('file.moved.to.done', on_file_moved_to_done)
        self.event_bus.subscribe('file.moved.to.failed', on_file_moved_to_failed)

        self.logger.info("Event subscriptions configured")

    def _print_gold_startup_banner(self):
        """Print Gold Tier startup banner"""
        # Get skill count
        skill_count = len(self.skill_registry.list_skills()) if self.skill_registry else 0

        # Check autonomous executor status
        autonomous_active = self.autonomous_executor and self.autonomous_executor.running

        # Get MCP server count
        mcp_servers = len(self.mcp_manager.list_servers()) if self.mcp_manager else 0

        # Build banner
        banner = []
        banner.append("=" * 60)
        banner.append("GOLD TIER RUNTIME INITIALIZED")
        banner.append("=" * 60)
        banner.append(f"Autonomous Execution: {'ACTIVE' if autonomous_active else 'INACTIVE'}")
        banner.append("RetryQueue: CENTRALIZED")
        banner.append("Circuit Breaker: CENTRALIZED")
        banner.append("EventBus: ACTIVE")
        banner.append(f"MCP Servers: {mcp_servers} ACTIVE")
        banner.append(f"Skills Registered: {skill_count}")
        banner.append("=" * 60)

        # Print banner
        for line in banner:
            self.logger.info(line)

    def start(self):
        """Start the orchestrator"""
        if self.running:
            self.logger.warning("Orchestrator already running")
            return

        self.logger.info("=" * 60)
        self.logger.info("Starting Integration Orchestrator (Gold Tier)")
        self.logger.info("=" * 60)

        # Start Gold Tier components
        self.retry_queue.start()
        self.health_monitor.start()
        self.periodic_trigger.start()
        self.autonomous_executor.start()

        # Start Approved Folder Monitor (Step 5)
        if self.approved_folder_monitor:
            self.approved_folder_monitor.start()
            self.logger.info("ApprovedFolderMonitor started - automatic execution enabled")

        # Setup filesystem watchers (using PollingObserver for WSL2 compatibility)
        self.observer = PollingObserver()

        # Watch monitored directories
        folders_to_watch = [
            ("inbox", self.inbox_dir),
            ("needs_action", self.needs_action_dir),
            ("pending_approval", self.pending_approval_dir),
            ("pending_approval_email", self.pending_approval_email_dir),
            ("approved", self.approved_dir),
            ("rejected", self.rejected_dir),
        ]

        for folder_name, folder_path in folders_to_watch:
            if folder_path.exists():
                handler = FolderWatcherHandler(folder_name, self.event_router, self.logger)
                self.observer.schedule(handler, str(folder_path), recursive=False)
                self.logger.info(f"Watching: {folder_path}")

        self.observer.start()

        # Record startup
        self.state_manager.set_system_state('last_startup', datetime.utcnow().isoformat() + 'Z')
        self.state_manager.set_system_state('orchestrator_version', 'gold_tier_v1.0_refactored')
        self.state_manager.increment_counter('total_startups')

        self.running = True

        # Print Gold Tier startup banner
        self._print_gold_startup_banner()

        self.logger.info("Integration Orchestrator started successfully")
        self.logger.info("=" * 60)

        # Keep running
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.logger.info("Received shutdown signal")
            self.stop()

    def stop(self):
        """Stop the orchestrator"""
        if not self.running:
            return

        self.logger.info("=" * 60)
        self.logger.info("Stopping Integration Orchestrator")
        self.logger.info("=" * 60)

        self.running = False

        # Stop components
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)

        if self.approved_folder_monitor:
            self.approved_folder_monitor.stop()

        if self.periodic_trigger:
            self.periodic_trigger.stop()

        if self.autonomous_executor:
            self.autonomous_executor.stop()

        if self.health_monitor:
            self.health_monitor.stop()

        if self.retry_queue:
            self.retry_queue.stop()

        # Record shutdown
        self.state_manager.set_system_state('last_shutdown', datetime.utcnow().isoformat() + 'Z')

        self.logger.info("Integration Orchestrator stopped")
        self.logger.info("=" * 60)

    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        try:
            # Get health status
            health = self.health_monitor.get_system_health()

            # Get retry queue size
            queue_size = self.retry_queue.get_queue_size()

            # Get registered skills
            registered_skills = self.skill_registry.list_skills()

            # Get metrics
            skills_started = self.state_manager.get_metric('skills_started')
            skills_succeeded = self.state_manager.get_metric('skills_succeeded')
            skills_failed = self.state_manager.get_metric('skills_failed')

            # Get autonomous executor status
            autonomous_status = self.autonomous_executor.get_status() if self.autonomous_executor else {}

            return {
                'running': self.running,
                'health': health,
                'retry_queue_size': queue_size,
                'registered_skills': len(registered_skills),
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
        """Get human-readable health report"""
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
            report.append("Metrics:")
            metrics = status.get('metrics', {})
            report.append(f"  - Skills Started: {metrics.get('skills_started', 0)}")
            report.append(f"  - Skills Succeeded: {metrics.get('skills_succeeded', 0)}")
            report.append(f"  - Skills Failed: {metrics.get('skills_failed', 0)}")
            report.append(f"  - Retry Queue Size: {status.get('retry_queue_size', 0)}")
            report.append(f"  - Registered Skills: {status.get('registered_skills', 0)}")

            report.append("")
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
